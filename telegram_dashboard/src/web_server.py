"""Ingress Web UI and REST API server using aiohttp."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from aiohttp import web
from .config_manager import ConfigManager
from .renderer import MessageRenderer

logger = logging.getLogger("telegram_dashboard.web")


class WebApp:
    def __init__(
        self,
        config_manager: ConfigManager,
        renderer: MessageRenderer,
        ha_client: Any | None = None,
        bot_engine: Any | None = None,
    ) -> None:
        self.cm = config_manager
        self.renderer = renderer
        self.ha_client = ha_client
        self.bot_engine = bot_engine
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self) -> None:
        ui_path = Path(__file__).parent / "ui"
        self.app.router.add_get("/", self.index_handler)
        self.app.router.add_get("/api/config", self.get_config)
        self.app.router.add_post("/api/config", self.save_config)
        self.app.router.add_get("/api/users", self.get_users)
        self.app.router.add_post("/api/users", self.upsert_user)
        self.app.router.add_delete("/api/users/{id}", self.delete_user)
        self.app.router.add_post("/api/users/sync", self.sync_users)
        self.app.router.add_post("/api/preview", self.preview_render)
        self.app.router.add_get("/api/catalog", self.get_catalog)
        self.app.router.add_get("/api/entities", self.get_entities)
        if ui_path.exists():
            self.app.router.add_static("/ui", ui_path)

    async def index_handler(self, request: web.Request) -> web.Response:
        ui_file = Path(__file__).parent / "ui" / "index.html"
        if ui_file.exists():
            content = ui_file.read_text(encoding="utf-8")
            ingress_path = request.headers.get("X-Ingress-Path", "")
            if ingress_path:
                base_href = ingress_path.rstrip("/") + "/"
                content = content.replace('<base href="./">', f'<base href="{base_href}">')
            return web.Response(text=content, content_type="text/html")
        return web.Response(text="Telegram Dashboard UI Loaded", content_type="text/html")

    async def get_config(self, request: web.Request) -> web.Response:
        return web.json_response(self.cm.config)

    async def save_config(self, request: web.Request) -> web.Response:
        data = await request.json()
        try:
            self.cm.save(data)
            if self.bot_engine:
                self.bot_engine.config = self.cm.config
            return web.json_response({"ok": True, "config": self.cm.config})
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)}, status=400)

    async def get_users(self, request: web.Request) -> web.Response:
        return web.json_response(self.cm.config.get("users", []))

    async def upsert_user(self, request: web.Request) -> web.Response:
        data = await request.json()
        try:
            user = self.cm.upsert_user(
                int(data["telegram_id"]), str(data.get("name", "")), str(data.get("role", "member"))
            )
            return web.json_response({"ok": True, "user": user})
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)}, status=400)

    async def delete_user(self, request: web.Request) -> web.Response:
        uid = int(request.match_info["id"])
        deleted = self.cm.remove_user(uid)
        return web.json_response({"ok": deleted})

    async def sync_users(self, request: web.Request) -> web.Response:
        """Sync users from Home Assistant Telegram Bot integration and notify services."""
        discovered = []
        default_role = self.cm.config.get("default_role", "guest")

        if self.ha_client:
            try:
                # Query HA template for notify.telegram and allowed_chat_ids
                template = """
                {% set found = [] %}
                {% for s in states.notify %}
                  {% if 'telegram' in s.entity_id %}
                    {% set _ = found.append({'entity_id': s.entity_id, 'name': s.name}) %}
                  {% endif %}
                {% endfor %}
                {% for p in states.person %}
                  {% set _ = found.append({'entity_id': p.entity_id, 'name': p.name}) %}
                {% endfor %}
                {{ found | to_json }}
                """
                res = await self.ha_client.render_template(template)
                if isinstance(res, str):
                    import json
                    try:
                        items = json.loads(res)
                        for item in items:
                            name = item.get("name", "Telegram User")
                            # If person or notify entity has custom chat_id or name
                            eid = item.get("entity_id", "")
                            state = await self.ha_client.get_state(eid)
                            if state and state.get("attributes"):
                                attrs = state["attributes"]
                                cid = attrs.get("chat_id") or attrs.get("user_id")
                                if cid and str(cid).isdigit():
                                    user = self.cm.auto_discover_user(int(cid), name, default_role)
                                    discovered.append(user)
                    except Exception as err:
                        logger.warning("Error parsing HA telegram template: %s", err)
            except Exception as e:
                logger.warning("HA Telegram sync error: %s", e)

        return web.json_response({"ok": True, "users": self.cm.config.get("users", []), "discovered": len(discovered)})

    async def preview_render(self, request: web.Request) -> web.Response:
        data = await request.json()
        section = data.get("section", {})
        section_key = data.get("section_key", "main")
        user_role = data.get("role", "admin")
        state = data.get("state", {
            "outside_temp": 18.5,
            "people_home": "2 людей",
            "climate": {"Зал": {"temperature": 22.4, "humidity": 45, "ac_on": False, "window_open": True}},
            "water_valve": {"open": True},
            "leaks": {"Кухня": {"on": False}, "Ванна": {"on": False}},
            "batteries": {"Зал (клімат)": {"level": 85}, "Кухня (протічка)": {"level": 18}},
            "updated_at": "17:45:00",
        })

        if self.bot_engine:
            simulated_uid = 1 if user_role == "admin" else (2 if user_role == "member" else 3)
            res = await self.bot_engine.handle_navigation(simulated_uid, section_key, state)
            return web.json_response({
                "html": res.get("text", ""),
                "keyboard": res.get("keyboard", []),
            })

        text = self.renderer.render_section(section, state)
        return web.json_response({"html": text, "keyboard": []})

    async def get_catalog(self, request: web.Request) -> web.Response:
        """Full HA catalog: entities grouped by area, domain and label."""
        if self.ha_client is None:
            return web.json_response(
                {"ok": False, "error": "Home Assistant client is not configured"},
                status=503,
            )
        try:
            catalog = await self.ha_client.collect_catalog()
            return web.json_response({"ok": True, "catalog": catalog})
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)}, status=502)

    async def get_entities(self, request: web.Request) -> web.Response:
        """List of individual entities for UI autocompletion and selection."""
        if self.ha_client is None:
            # Return sample entities for rich offline development/preview
            sample_entities = [
                {"entity_id": "light.living_room", "friendly_name": "Світло у вітальні", "domain": "light"},
                {"entity_id": "light.kitchen", "friendly_name": "Світло на кухні", "domain": "light"},
                {"entity_id": "switch.boiler", "friendly_name": "Бойлер", "domain": "switch"},
                {"entity_id": "climate.hall", "friendly_name": "Кондиціонер", "domain": "climate"},
                {
                    "entity_id": "sensor.living_room_temperature",
                    "friendly_name": "Температура у залі",
                    "domain": "sensor",
                },
                {
                    "entity_id": "sensor.living_room_humidity",
                    "friendly_name": "Вологість у залі",
                    "domain": "sensor",
                },
                {
                    "entity_id": "binary_sensor.kitchen_leak",
                    "friendly_name": "Датчик протікання кухня",
                    "domain": "binary_sensor",
                },
                {
                    "entity_id": "sensor.battery_hall_climate",
                    "friendly_name": "Батарея датчика залу",
                    "domain": "sensor",
                },
                {
                    "entity_id": "media_player.living_room_speaker",
                    "friendly_name": "Колонка",
                    "domain": "media_player",
                },
            ]
            return web.json_response({"ok": True, "entities": sample_entities})
        try:
            states = await self.ha_client.get_states()
            entities = []
            for s in states:
                eid = s.get("entity_id", "")
                attrs = s.get("attributes", {})
                fn = attrs.get("friendly_name", eid)
                domain = eid.split(".", 1)[0]
                entities.append({
                    "entity_id": eid,
                    "friendly_name": fn,
                    "domain": domain,
                    "state": s.get("state", ""),
                })
            return web.json_response({"ok": True, "entities": entities})
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)}, status=502)
