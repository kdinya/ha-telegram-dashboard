import pytest
from unittest.mock import AsyncMock
from telegram_dashboard.src.ha_client import HAClient


def test_ha_client_init_without_running_loop():
    """Verify HAClient can be instantiated synchronously without a running event loop."""
    client = HAClient("http://supervisor/core/api", "test-token")
    assert client._session is None
    assert client._token == "test-token"
    assert client._base == "http://supervisor/core/api"


@pytest.mark.asyncio
async def test_ha_client_lazy_session_and_close():
    """Verify session is created lazily in loop and closes properly."""
    client = HAClient("http://supervisor/core/api", "test-token")
    session = await client._ensure_session()
    assert session is not None
    assert not session.closed
    await client.close()
    assert session.closed


@pytest.mark.asyncio
async def test_call_service_requests_service_response_when_requested():
    client = HAClient("http://supervisor/core/api", "test-token")
    client._post = AsyncMock(return_value={"service_response": {"chats": []}})

    response = await client.call_service(
        "telegram_bot", "send_message", service_data={"chat_id": [123]}, return_response=True
    )

    assert response == {"service_response": {"chats": []}}
    client._post.assert_awaited_once_with(
        "/api/services/telegram_bot/send_message?return_response", {"chat_id": [123]}
    )


@pytest.mark.asyncio
async def test_get_telegram_bot_name_uses_loaded_entry_title_only():
    client = HAClient("http://supervisor/core", "test-token")
    client._get = AsyncMock(return_value=[
        {"title": "Unavailable bot", "state": "setup_error"},
        {"title": "House Bot", "state": "loaded", "data": {"api_key": "must-not-be-read"}},
    ])

    assert await client.get_telegram_bot_name() == "House Bot"
    client._get.assert_awaited_once_with(
        "/api/config/config_entries/entry?domain=telegram_bot"
    )


@pytest.mark.asyncio
async def test_get_telegram_bot_name_returns_none_without_loaded_entry():
    client = HAClient("http://supervisor/core", "test-token")
    client._get = AsyncMock(return_value=[
        {"title": "Unavailable bot", "state": "setup_error"},
        {"state": "loaded", "title": "   "},
    ])

    assert await client.get_telegram_bot_name() is None
