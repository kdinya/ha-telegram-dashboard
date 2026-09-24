import pytest
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
