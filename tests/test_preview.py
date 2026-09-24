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
