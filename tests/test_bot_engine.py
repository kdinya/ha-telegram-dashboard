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
    assert "blockquote" in res_clim["text"]
