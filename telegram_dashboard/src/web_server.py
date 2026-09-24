"""Ingress Web UI and REST API server using aiohttp."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from aiohttp import web
from .config_manager import ConfigManager
from .renderer import MessageRenderer
from .access_controller import AccessController


class WebApp:
    def __init__(self, config_manager: ConfigManager, renderer: MessageRenderer) -> None:
        self.cm = config_manager
        self.renderer = renderer
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
        if ui_path.exists():
            self.app.router.add_static("/ui", ui_path)

    async def index_handler(self, request: web.Request) -> web.Response:
        ui_file = Path(__file__).parent / "ui" / "index.html"
        if ui_file.exists():
            return web.FileResponse(ui_file)
        return web.Response(text="Telegram Dashboard UI Loaded", content_type="text/html")

    async def get_config(self, request: web.Request) -> web.Response:
        return web.json_response(self.cm.config)

    async def save_config(self, request: web.Request) -> web.Response:
        data = await request.json()
        try:
            self.cm.save(data)
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
        state = data.get("state", {
            "outside_temp": 18.5,
            "people_home": "2 людей",
            "climate": {"Зал": {"temperature": 22.4, "humidity": 45, "ac_on": False, "window_open": True}},
            "water_valve": {"open": True},
            "leaks": {"Кухня": {"on": False}, "Ванна": {"on": False}},
            "batteries": {"Зал (клімат)": {"level": 85}, "Кухня (протічка)": {"level": 18}},
            "updated_at": "17:45:00"
        })
        text = self.renderer.render_section(section, state)
        return web.json_response({"html": text})
