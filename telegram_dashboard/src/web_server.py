"""Ingress Web UI and REST API server using aiohttp."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from aiohttp import web
from .config_manager import ConfigManager
from .renderer import MessageRenderer


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
        self.app.router.add_post("/api/preview", self.preview_render)
        self.app.router.add_get("/api/catalog", self.get_catalog)
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
            # Temporary mock user role in access controller if needed
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
