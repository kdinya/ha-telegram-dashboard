import pytest
import asyncio
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
    await runner.stop()


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


@pytest.mark.asyncio
async def test_command_message_is_auto_deleted_after_configured_timeout():
    config = {
        "auto_delete_timeout": 1,
        "menu": {
            "main": {"title": "Main", "type": "menu", "sections": [], "roles": ["admin"]}
        },
        "users": [{"telegram_id": 100, "role": "admin"}],
    }
    access = AccessController(config["users"])
    engine = BotEngine(config, access, MessageRenderer())
    deleted = asyncio.Event()

    async def mock_call_service(domain, service, service_data=None, **kwargs):
        if service == "send_message":
            return {"service_response": {"chats": [{"chat_id": 100, "message_id": 55}]}}
        if service == "delete_message":
            assert service_data == {"chat_id": 100, "message_id": 55}
            deleted.set()
            return {"ok": True}
        return {"ok": True}

    ha_client = MagicMock()
    ha_client.call_service = AsyncMock(side_effect=mock_call_service)
    runner = TelegramBotRunner(ha_client, engine)

    await runner.handle_ha_command({
        "command": "/dashboard",
        "chat_id": 100,
        "user_id": 100,
        "from_first_name": "Admin",
    })

    assert (100, 55) in runner._auto_delete_tasks
    send_call = ha_client.call_service.call_args_list[0]
    assert send_call.kwargs["return_response"] is True
    await asyncio.sleep(0.6)
    await runner.handle_ha_callback({
        "data": f"{TD_CALLBACK_PREFIX}/sec_main",
        "id": "12345",
        "chat_id": 100,
        "message": {"message_id": 55},
        "user_id": 100,
    })
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(deleted.wait(), timeout=0.5)
    await asyncio.wait_for(deleted.wait(), timeout=2)
    await runner.stop()
