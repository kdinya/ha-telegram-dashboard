import json
from pathlib import Path
import pytest
from telegram_dashboard.src.web_server import WebApp
from telegram_dashboard.src.config_manager import ConfigManager
from telegram_dashboard.src.renderer import MessageRenderer


@pytest.mark.asyncio
async def test_preview_render_keyboard_parity(tmp_path: Path):
    cfg_file = tmp_path / "config.json"
    cm = ConfigManager(cfg_file)
    cm.load()
    renderer = MessageRenderer()
    app = WebApp(cm, renderer)

    # Mock request with custom menu sections checked
    payload = {
        "menu": {
            "main": {
                "title": "Головна",
                "type": "menu",
                "icon": "🏠",
                "roles": ["admin", "member", "guest"],
                "sections": ["climate", "water"],
            },
            "climate": {
                "title": "Клімат",
                "type": "section",
                "icon": "🌡",
                "roles": ["admin"],
            },
            "water": {
                "title": "Вода",
                "type": "section",
                "icon": "🚰",
                "roles": ["admin", "member"],
            },
        },
        "section_key": "main",
        "role": "admin",
    }

    class MockRequest:
        async def json(self):
            return payload

    response = await app.preview_render(MockRequest())
    data = json.loads(response.text)

    # As admin, both climate and water navigation buttons should appear
    flat_buttons = [btn["text"] for row in data["keyboard"] for btn in row]
    assert any("Клімат" in text for text in flat_buttons), f"Missing Climate button in {flat_buttons}"
    assert any("Вода" in text for text in flat_buttons), f"Missing Water button in {flat_buttons}"

    # As member, only water should appear since climate requires admin
    payload["role"] = "member"
    response_member = await app.preview_render(MockRequest())
    data_member = json.loads(response_member.text)
    flat_buttons_member = [btn["text"] for row in data_member["keyboard"] for btn in row]
    assert not any("Клімат" in text for text in flat_buttons_member), "Climate should not be visible to member"
    assert any("Вода" in text for text in flat_buttons_member), "Water should be visible to member"


@pytest.mark.asyncio
async def test_bot_info_returns_only_name_and_handles_missing_ha_client(tmp_path: Path):
    cfg_file = tmp_path / "config.json"
    cm = ConfigManager(cfg_file)
    cm.load()
    renderer = MessageRenderer()

    class MockHAClient:
        async def get_telegram_bot_name(self):
            return "House Bot"

    class MockRequest:
        pass

    app = WebApp(cm, renderer, ha_client=MockHAClient())
    assert any(route.resource.canonical == "/api/bot/info" for route in app.app.router.routes())
    response = await app.get_bot_info(MockRequest())
    assert json.loads(response.text) == {"name": "House Bot"}

    app_without_ha = WebApp(cm, renderer)
    response_without_ha = await app_without_ha.get_bot_info(MockRequest())
    assert json.loads(response_without_ha.text) == {"name": None}

    class FailingHAClient:
        async def get_telegram_bot_name(self):
            raise RuntimeError("Home Assistant unavailable")

    app_with_unavailable_ha = WebApp(cm, renderer, ha_client=FailingHAClient())
    response_with_unavailable_ha = await app_with_unavailable_ha.get_bot_info(MockRequest())
    assert json.loads(response_with_unavailable_ha.text) == {"name": None}
