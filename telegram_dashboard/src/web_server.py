"""Ingress Web UI and REST API server using aiohttp."""
from __future__ import annotations
from datetime import datetime

import logging
from pathlib import Path
from typing import Any
import aiohttp
from aiohttp import web
from .config_manager import ConfigManager
from .renderer import MessageRenderer
from .access_controller import AccessController
from .bot_engine import BotEngine

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
            "entity_id": "sensor.climate_living_room_temperature",
            "friendly_name": "Клімат в кімнаті Температура",
            "domain": "sensor",
            "area": "Кімната",
            "state": "21.5 °C",
            "attributes": {"unit_of_measurement": "°C", "device_class": "temperature"},
        },
        {
            "entity_id": "sensor.living_room_temperature",
            "friendly_name": "Температура у вітальні",
            "domain": "sensor",
            "area": "Вітальня",
            "state": "22.5 °C",
            "attributes": {"unit_of_measurement": "°C", "device_class": "temperature"},
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
        bot_runner: Any | None = None,
    ) -> None:
        self.cm = config_manager
        self.renderer = renderer
        self.ha_client = ha_client
        self.bot_engine = bot_engine
        self.telegram_token = telegram_token or ""
        self.bot_runner = bot_runner
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
        self.app.router.add_post("/api/bot/send_message", self.bot_send_message)
        self.app.router.add_post("/api/bot/edit_message", self.bot_edit_message)
        self.app.router.add_post("/api/bot/delete_message", self.bot_delete_message)
        self.app.router.add_post("/api/bot/answer_callback", self.bot_answer_callback)
        self.app.router.add_post("/api/bot/send_photo", self.bot_send_photo)
        self.app.router.add_post("/api/bot/send_document", self.bot_send_document)
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
        data = dict(self.cm.config)
        if not data.get("telegram_token"):
            data["telegram_token"] = self.telegram_token or ""
        return web.json_response(data)

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
            "updated_at": datetime.now().strftime("%H:%M:%S"),
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

        # Enrich preview state with live HA states if connected
        if self.ha_client is not None:
            try:
                live_states = await self.ha_client.get_states()
                for s in live_states:
                    eid = s.get("entity_id")
                    if eid:
                        state[eid] = s
            except Exception as exc:
                logger.warning("Could not fetch HA states for preview: %s", exc)

        # Fallback realistic states for requested entities not yet in state
        all_eids = []
        for it in section.get("items", []):
            if isinstance(it, dict) and it.get("type") == "entity" and it.get("entity_id"):
                all_eids.append(it["entity_id"])
        for e in section.get("entities", []):
            if isinstance(e, dict) and e.get("entity_id"):
                all_eids.append(e["entity_id"])

        for eid in all_eids:
            if eid not in state:
                dom = eid.split(".")[0]
                if dom in ("light", "switch", "input_boolean"):
                    state[eid] = {"state": "on", "attributes": {"friendly_name": eid}}
                elif dom == "climate":
                    state[eid] = {"state": "21.5", "attributes": {"temperature": 21.5, "unit_of_measurement": "°C"}}
                elif dom == "binary_sensor":
                    state[eid] = {"state": "off", "attributes": {"device_class": "moisture"}}
                elif "temp" in eid:
                    state[eid] = {"state": "22.0", "attributes": {"unit_of_measurement": "°C"}}
                elif "hum" in eid:
                    state[eid] = {"state": "45", "attributes": {"unit_of_measurement": "%"}}
                elif "batt" in eid:
                    state[eid] = {"state": "85", "attributes": {"device_class": "battery"}}
                else:
                    state[eid] = {"state": "online", "attributes": {"friendly_name": eid}}

        # Check access
        allowed_roles = section.get("roles", ["admin", "member", "guest"])
        if user_role not in allowed_roles:
            return web.json_response({
                "html": "⛔ <i>У вас немає доступу до цього розділу.</i>",
                "keyboard": [[{"text": "⬅️ Назад", "callback_data": "/sec_main"}]],
            })

        # Render HTML using unified renderer
        text = self.renderer.render_section(section, state)

        # Build preview keyboard respecting simulated role and sections parity
        simulated_users = [{"telegram_id": 0, "role": user_role, "name": f"Preview ({user_role})"}]
        preview_access = AccessController(simulated_users)
        preview_engine = BotEngine(
            config={"menu": menu, "users": simulated_users},
            access_controller=preview_access,
            renderer=self.renderer,
        )
        if self.bot_engine and hasattr(self.bot_engine, "catalog"):
            preview_engine.catalog = getattr(self.bot_engine, "catalog", {})
        keyboard = preview_engine.build_keyboard(section_key, 0, state=state)

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
                    "attributes": attrs,
                })
            return web.json_response({"ok": True, "entities": entities})
        except Exception as e:
            logger.warning("get_states failed, falling back to sample entities: %s", e)
            return web.json_response({
                "ok": True,
                "entities": _sample_entities(),
                "warning": f"Home Assistant недоступний: {e}",
            })

    async def bot_send_message(self, request: web.Request) -> web.Response:
        if not self.bot_runner:
            return web.json_response({"ok": False, "error": "Bot runner is not active"}, status=503)
        data = await request.json()
        chat_id = data.get("chat_id") or data.get("target")
        text = data.get("message") or data.get("text", "")
        if not chat_id or not text:
            return web.json_response({"ok": False, "error": "chat_id and message are required"}, status=400)
        parse_mode = data.get("parse_mode", "HTML")
        disable_notification = bool(data.get("disable_notification", False))
        reply_markup = data.get("reply_markup") or data.get("inline_keyboard")
        if reply_markup and "inline_keyboard" not in reply_markup and isinstance(reply_markup, list):
            reply_markup = {"inline_keyboard": reply_markup}

        targets = chat_id if isinstance(chat_id, list) else [chat_id]
        results = []
        all_ok = True
        for cid in targets:
            res = await self.bot_runner.send_message(
                cid, text, reply_markup=reply_markup,
                parse_mode=parse_mode, disable_notification=disable_notification
            )
            results.append(res)
            if not res or not res.get("ok"):
                all_ok = False
        return web.json_response({"ok": all_ok, "results": results}, status=200 if all_ok else 400)

    async def bot_edit_message(self, request: web.Request) -> web.Response:
        if not self.bot_runner:
            return web.json_response({"ok": False, "error": "Bot runner is not active"}, status=503)
        data = await request.json()
        chat_id = data.get("chat_id")
        msg_id = data.get("message_id")
        text = data.get("message") or data.get("text", "")
        if not chat_id or not msg_id or not text:
            return web.json_response({"ok": False, "error": "chat_id, message_id and message are required"}, status=400)
        parse_mode = data.get("parse_mode", "HTML")
        reply_markup = data.get("reply_markup") or data.get("inline_keyboard")
        if reply_markup and "inline_keyboard" not in reply_markup and isinstance(reply_markup, list):
            reply_markup = {"inline_keyboard": reply_markup}

        res = await self.bot_runner.edit_message_text(
            chat_id, int(msg_id), text, reply_markup=reply_markup, parse_mode=parse_mode
        )
        return web.json_response({"ok": True, "result": res})

    async def bot_delete_message(self, request: web.Request) -> web.Response:
        if not self.bot_runner:
            return web.json_response({"ok": False, "error": "Bot runner is not active"}, status=503)
        data = await request.json()
        chat_id = data.get("chat_id")
        msg_id = data.get("message_id")
        if not chat_id or not msg_id:
            return web.json_response({"ok": False, "error": "chat_id and message_id are required"}, status=400)
        res = await self.bot_runner.delete_message(chat_id, int(msg_id))
        return web.json_response({"ok": True, "result": res})

    async def bot_answer_callback(self, request: web.Request) -> web.Response:
        if not self.bot_runner:
            return web.json_response({"ok": False, "error": "Bot runner is not active"}, status=503)
        data = await request.json()
        cb_id = data.get("callback_query_id")
        if not cb_id:
            return web.json_response({"ok": False, "error": "callback_query_id is required"}, status=400)
        text = data.get("message") or data.get("text")
        show_alert = bool(data.get("show_alert", False))
        res = await self.bot_runner.answer_callback_query(cb_id, text=text, show_alert=show_alert)
        return web.json_response({"ok": True, "result": res})

    async def bot_send_photo(self, request: web.Request) -> web.Response:
        if not self.bot_runner:
            return web.json_response({"ok": False, "error": "Bot runner is not active"}, status=503)
        data = await request.json()
        chat_id = data.get("chat_id") or data.get("target")
        photo = data.get("photo") or data.get("url")
        if not chat_id or not photo:
            return web.json_response({"ok": False, "error": "chat_id and photo are required"}, status=400)
        caption = data.get("caption") or data.get("message")
        parse_mode = data.get("parse_mode", "HTML")
        reply_markup = data.get("reply_markup") or data.get("inline_keyboard")
        if reply_markup and "inline_keyboard" not in reply_markup and isinstance(reply_markup, list):
            reply_markup = {"inline_keyboard": reply_markup}

        targets = chat_id if isinstance(chat_id, list) else [chat_id]
        results = []
        for cid in targets:
            res = await self.bot_runner.send_photo(
                cid, photo, caption=caption, reply_markup=reply_markup, parse_mode=parse_mode
            )
            results.append(res)
        return web.json_response({"ok": True, "results": results})

    async def bot_send_document(self, request: web.Request) -> web.Response:
        if not self.bot_runner:
            return web.json_response({"ok": False, "error": "Bot runner is not active"}, status=503)
        data = await request.json()
        chat_id = data.get("chat_id") or data.get("target")
        doc = data.get("document") or data.get("url")
        if not chat_id or not doc:
            return web.json_response({"ok": False, "error": "chat_id and document are required"}, status=400)
        caption = data.get("caption") or data.get("message")
        parse_mode = data.get("parse_mode", "HTML")
        reply_markup = data.get("reply_markup") or data.get("inline_keyboard")
        if reply_markup and "inline_keyboard" not in reply_markup and isinstance(reply_markup, list):
            reply_markup = {"inline_keyboard": reply_markup}

        targets = chat_id if isinstance(chat_id, list) else [chat_id]
        results = []
        for cid in targets:
            res = await self.bot_runner.send_document(
                cid, doc, caption=caption, reply_markup=reply_markup, parse_mode=parse_mode
            )
            results.append(res)
        return web.json_response({"ok": True, "results": results})
