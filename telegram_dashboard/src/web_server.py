"""Ingress Web UI and REST API server using aiohttp."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
import aiohttp
from aiohttp import web
from .config_manager import ConfigManager
from .renderer import MessageRenderer
from .access_controller import AccessController

logger = logging.getLogger("telegram_dashboard.web")


def _sample_entities() -> list[dict[str, Any]]:
    """Demo entities used when HA is unreachable or no supervisor token."""
    return [
        {
            "entity_id": "light.living_room",
            "friendly_name": "Світло у вітальні",
            "domain": "light",
            "area": "Вітальня",
            "state": "on",
        },
        {
            "entity_id": "light.kitchen",
            "friendly_name": "Світло на кухні",
            "domain": "light",
            "area": "Кухня",
            "state": "off",
        },
        {
            "entity_id": "switch.boiler",
            "friendly_name": "Бойлер",
            "domain": "switch",
            "area": "Ванна",
            "state": "on",
        },
        {
            "entity_id": "climate.hall",
            "friendly_name": "Кондиціонер",
            "domain": "climate",
            "area": "Вітальня",
            "state": "cool",
        },
        {
            "entity_id": "sensor.living_room_temperature",
            "friendly_name": "Температура у вітальні",
            "domain": "sensor",
            "area": "Вітальня",
            "state": "22.5 °C",
        },
        {
            "entity_id": "binary_sensor.kitchen_leak",
            "friendly_name": "Датчик протікання кухня",
            "domain": "binary_sensor",
            "area": "Кухня",
            "state": "off",
        },
        {
            "entity_id": "automation.night_mode",
            "friendly_name": "Нічний режим",
            "domain": "automation",
            "area": "Дім",
            "state": "on",
        },
        {
            "entity_id": "script.turn_off_all_lights",
            "friendly_name": "Вимкнути все світло",
            "domain": "script",
            "area": "Дім",
            "state": "off",
        },
        {
            "entity_id": "cover.living_room_curtains",
            "friendly_name": "Штори у вітальні",
            "domain": "cover",
            "area": "Вітальня",
            "state": "open",
        },
    ]


class WebApp:
    def __init__(
        self,
        config_manager: ConfigManager,
        renderer: MessageRenderer,
        ha_client: Any | None = None,
        bot_engine: Any | None = None,
        telegram_token: str | None = None,
    ) -> None:
        self.cm = config_manager
        self.renderer = renderer
        self.ha_client = ha_client
        self.bot_engine = bot_engine
        self.telegram_token = telegram_token or ""
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
        """Sync users from Telegram API getUpdates and Home Assistant integration."""
        discovered = 0
        default_role = self.cm.config.get("default_role", "guest")
        token = self.telegram_token or self.cm.config.get("telegram_token", "")

        # 1. Direct Telegram Bot API getUpdates
        if token:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"https://api.telegram.org/bot{token}/getUpdates"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for upd in data.get("result", []):
                                user_info = None
                                if "message" in upd and "from" in upd["message"]:
                                    user_info = upd["message"]["from"]
                                elif "callback_query" in upd and "from" in upd["callback_query"]:
                                    user_info = upd["callback_query"]["from"]
                                elif "my_chat_member" in upd and "from" in upd["my_chat_member"]:
                                    user_info = upd["my_chat_member"]["from"]

                                if user_info and "id" in user_info:
                                    tid = int(user_info["id"])
                                    parts = [user_info.get("first_name", ""), user_info.get("last_name", "")]
                                    name = " ".join(p for p in parts if p).strip()
                                    if not name and user_info.get("username"):
                                        name = f"@{user_info['username']}"
                                    if not name:
                                        name = f"User {tid}"

                                    existing = any(u.get("telegram_id") == tid for u in self.cm.config.get("users", []))
                                    self.cm.auto_discover_user(tid, name, default_role)
                                    if not existing:
                                        discovered += 1
            except Exception as e:
                logger.warning("Telegram getUpdates sync failed: %s", e)

        # User auto-discovery happens directly through Telegram chat interactions and getUpdates

        return web.json_response({
            "ok": True,
            "users": self.cm.config.get("users", []),
            "discovered": discovered,
        })

    async def preview_render(self, request: web.Request) -> web.Response:
        data = await request.json()
        menu = data.get("menu") or self.cm.config.get("menu", {})
        section_key = data.get("section_key", "main")
        user_role = data.get("role", "admin")
        section = data.get("section") or menu.get(section_key, {})

        # Build mock state with sample entities + legacy keys
        state = {
            "outside_temp": 19.2,
            "people_home": "2 вдома",
            "climate": {"Зал": {"temperature": 22.0, "humidity": 48, "ac_on": False, "window_open": False}},
            "water_valve": {"open": True},
            "leaks": {"Кухня": {"on": False}, "Ванна": {"on": False}},
            "batteries": {"Зал": {"level": 88}, "Кухня": {"level": 64}},
            "updated_at": "12:00:00",
            # Sample entity states for realistic preview
            "light.living_room": {"state": "on", "attributes": {"friendly_name": "Світло у вітальні"}},
            "light.kitchen": {"state": "off", "attributes": {"friendly_name": "Світло на кухні"}},
            "switch.boiler": {"state": "on", "attributes": {"friendly_name": "Бойлер"}},
            "switch.water_tap": {"state": "on", "attributes": {"friendly_name": "Ввідний кран"}},
            "switch.valve": {"state": "open", "attributes": {"friendly_name": "Кран"}},
            "climate.hall": {
                "state": "cool", "attributes": {"friendly_name": "Кондиціонер", "temperature": 22.0}
            },
            "sensor.living_room_temperature": {
                "state": "22.5", "attributes": {"unit_of_measurement": "°C", "friendly_name": "Температура"}
            },
            "sensor.humidity": {
                "state": "45", "attributes": {"unit_of_measurement": "%", "friendly_name": "Вологість"}
            },
            "sensor.phone_battery": {
                "state": "85", "attributes": {"unit_of_measurement": "%", "friendly_name": "Заряд"}
            },
            "binary_sensor.kitchen_leak": {
                "state": "off", "attributes": {"device_class": "moisture", "friendly_name": "Датчик"}
            },
        }

        # Check access
        allowed_roles = section.get("roles", ["admin", "member", "guest"])
        if user_role not in allowed_roles:
            return web.json_response({
                "html": "⛔ <i>У вас немає доступу до цього розділу.</i>",
                "keyboard": [[{"text": "⬅️ Назад", "callback_data": "/sec_main"}]],
            })

        # Render HTML using unified renderer
        text = self.renderer.render_section(section, state)

        # Build preview keyboard
        if self.bot_engine:
            self.bot_engine.config = {"menu": menu, "users": self.cm.config.get("users", [])}
            keyboard = self.bot_engine.build_keyboard(section_key, 0, state=state)
        else:
            keyboard = []

        return web.json_response({"html": text, "keyboard": keyboard})

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
            return web.json_response({
                "ok": True,
                "entities": _sample_entities(),
                "warning": "SUPERVISOR_TOKEN відсутній: показано демонстраційні сутності",
            })
        try:
            states = await self.ha_client.get_states()
            entities = []
            for s in states:
                eid = s.get("entity_id", "")
                attrs = s.get("attributes", {})
                fn = attrs.get("friendly_name", eid)
                domain = eid.split(".", 1)[0]
                area = attrs.get("area_id") or ""
                entities.append({
                    "entity_id": eid,
                    "friendly_name": fn,
                    "domain": domain,
                    "area": area,
                    "state": s.get("state", ""),
                })
            return web.json_response({"ok": True, "entities": entities})
        except Exception as e:
            logger.warning("get_states failed, falling back to sample entities: %s", e)
            return web.json_response({
                "ok": True,
                "entities": _sample_entities(),
                "warning": f"Home Assistant недоступний: {e}",
            })
