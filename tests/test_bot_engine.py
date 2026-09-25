import pytest
from telegram_dashboard.src.bot_engine import BotEngine
from telegram_dashboard.src.access_controller import AccessController
from telegram_dashboard.src.renderer import MessageRenderer


@pytest.mark.asyncio
async def test_bot_engine_navigation():
    config = {
        "menu": {
            "main": {"type": "menu", "sections": ["climate", "system"], "roles": ["admin", "member", "guest"]},
            "climate": {"title": "Клімат", "roles": ["admin", "member", "guest"], "widgets": []},
            "system": {"title": "Система", "roles": ["admin"], "widgets": []},
        }
    }
    users = [{"telegram_id": 10, "role": "guest"}]
    ac = AccessController(users, default_role="guest")
    renderer = MessageRenderer()
    engine = BotEngine(config, ac, renderer)

    # Guest cannot access system section
    res_sys = await engine.handle_navigation(10, "system", {})
    assert "Доступ обмежено" in res_sys["text"]

    # Guest can access climate section
    res_clim = await engine.handle_navigation(10, "climate", {})
    assert "📁 Клімат" in res_clim["text"]
    keyboard_text = [button["text"] for row in res_clim["keyboard"] for button in row]
    assert "❌ Закрити" in keyboard_text
    assert any("↩️ Назад" in text for text in keyboard_text)


@pytest.mark.asyncio
async def test_bot_engine_underscore_section_keys():
    """Verify that section keys with underscores (e.g. living_room) work properly in bot engine."""
    config = {
        "menu": {
            "main": {"title": "Main", "sections": ["living_room"]},
            "living_room": {
                "title": "Living Room",
                "type": "entities",
                "entities": ["switch.fan", "light.ceiling"],
                "buttons": [{"entity_id": "switch.fan", "label": "Вентилятор"}]
            }
        },
        "users": [{"telegram_id": 111, "name": "Admin", "role": "admin"}]
    }
    access = AccessController(config["users"], default_role="guest")
    renderer = MessageRenderer()
    engine = BotEngine(config=config, access_controller=access, renderer=renderer)

    # 1. Navigation to underscore key
    nav = await engine.handle_navigation(111, "living_room", {"switch.fan": "off", "light.ceiling": "on"}, page=0)
    assert nav["keyboard"] is not None

    # 2. Toggle entity with underscore section key
    toggled = []

    async def mock_call_service(domain, service, target=None):
        toggled.append((domain, service, target))

    engine.ha_call_service = mock_call_service
    res = await engine.handle_entity_toggle(111, "living_room", 0)
    assert res["ok"] is True
    assert len(toggled) == 1
    assert toggled[0][2] == {"entity_id": ["switch.fan"]}

    # 3. Button click with underscore section key
    btn_res = await engine.handle_button_click(111, "living_room", "0", {"switch.fan": "off"})
    assert btn_res["ok"] is True
    assert len(toggled) == 2


@pytest.mark.asyncio
async def test_callbacks_cannot_bypass_section_rbac():
    config = {
        "menu": {
            "main": {"type": "menu", "roles": ["guest"], "sections": ["admin_only"]},
            "admin_only": {
                "type": "entities",
                "roles": ["admin"],
                "entities": ["switch.secret"],
                "actions": [{
                    "id": "danger", "min_role": "admin", "domain": "switch",
                    "service": "turn_off", "entity_id": "switch.secret"
                }],
            },
        }
    }
    called = []

    async def mock_call_service(domain, service, target=None):
        called.append((domain, service, target))

    engine = BotEngine(
        config, AccessController([{"telegram_id": 9, "role": "guest"}]),
        MessageRenderer(), mock_call_service
    )
    toggle = await engine.handle_entity_toggle(9, "admin_only", 0)
    action = await engine.handle_action(9, "danger", {})
    assert toggle["ok"] is False
    assert action["ok"] is False
    assert called == []
