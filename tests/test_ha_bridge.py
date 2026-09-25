import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_dashboard.src.telegram_bot import TelegramBotRunner, TD_CALLBACK_PREFIX
from telegram_dashboard.src.bot_engine import BotEngine
from telegram_dashboard.src.access_controller import AccessController
from telegram_dashboard.src.renderer import MessageRenderer


@pytest.mark.asyncio
async def test_bridge_routes_multi_menu_commands():
    config = {
        "menu": {
            "main": {
                "title": "Main Dashboard",
                "command": "/dashboard",
                "type": "menu",
                "sections": ["lights"],
                "roles": ["admin"],
            },
            "security": {
                "title": "Security System",
                "command": "/security",
                "type": "menu",
                "sections": [],
                "roles": ["admin"],
            },
        }
    }
    ac = AccessController([{"telegram_id": 100, "role": "admin"}])
    engine = BotEngine(config, ac, MessageRenderer())

    ha_client = MagicMock()
    ha_client.call_service = AsyncMock(return_value={"ok": True})

    runner = TelegramBotRunner(ha_client, engine)

    # 1. Test /dashboard command
    await runner.handle_ha_command({
        "command": "/dashboard",
        "chat_id": 100,
        "user_id": 100,
        "from_first_name": "Admin",
    })
    assert ha_client.call_service.call_count == 1
    call_args = ha_client.call_service.call_args[1]
    assert call_args["service_data"]["chat_id"] == [100]
    assert "Main Dashboard" in call_args["service_data"]["message"]

    # 2. Test /security command
    ha_client.call_service.reset_mock()
    await runner.handle_ha_command({
        "command": "/security",
        "chat_id": 100,
        "user_id": 100,
        "from_first_name": "Admin",
    })
    assert ha_client.call_service.call_count == 1
    call_args = ha_client.call_service.call_args[1]
    assert "Security System" in call_args["service_data"]["message"]

    # 3. Test unknown command (should be ignored for user automations)
    ha_client.call_service.reset_mock()
    await runner.handle_ha_command({
        "command": "/unknown_bot_cmd",
        "chat_id": 100,
        "user_id": 100,
        "from_first_name": "Admin",
    })
    assert ha_client.call_service.call_count == 0


@pytest.mark.asyncio
async def test_bridge_callback_isolation():
    config = {
        "menu": {
            "main": {"title": "Main", "type": "menu", "sections": [], "roles": ["admin"]}
        }
    }
    ac = AccessController([{"telegram_id": 100, "role": "admin"}])
    engine = BotEngine(config, ac, MessageRenderer())
    ha_client = MagicMock()
    ha_client.call_service = AsyncMock(return_value={"ok": True})
    runner = TelegramBotRunner(ha_client, engine)

    # External callback without prefix - MUST be ignored
    await runner.handle_ha_callback({
        "data": "some_ha_automation_callback",
        "id": "12345",
        "chat_id": 100,
        "message": {"message_id": 50},
        "user_id": 100,
    })
    assert ha_client.call_service.call_count == 0

    # Dashboard callback WITH td: prefix - MUST be handled and answered
    await runner.handle_ha_callback({
        "data": f"{TD_CALLBACK_PREFIX}/sec_main",
        "id": "12345",
        "chat_id": 100,
        "message": {"message_id": 50},
        "user_id": 100,
    })
    # edit_message + answer_callback_query
    assert ha_client.call_service.call_count == 2


@pytest.mark.asyncio
async def test_bridge_formats_inline_keyboard_for_ha():
    from telegram_dashboard.src.telegram_bot import format_inline_keyboard_for_ha
    raw_keyboard = [
        [{"text": "🏠 Smart Home", "callback_data": "td:/sec_main"}],
        [{"text": "🔄 Refresh", "callback_data": "td:/sec_main"}, {"text": "Web Link", "url": "https://example.com"}]
    ]
    ha_kb = format_inline_keyboard_for_ha(raw_keyboard)
    assert ha_kb == [
        [["🏠 Smart Home", "td:/sec_main"]],
        [["🔄 Refresh", "td:/sec_main"], ["Web Link", "https://example.com"]]
    ]
