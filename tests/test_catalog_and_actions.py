import pytest
from telegram_dashboard.src.access_controller import AccessController
from telegram_dashboard.src.bot_engine import BotEngine
from telegram_dashboard.src.renderer import MessageRenderer


def test_entity_level_rbac():
    users = [
        {
            "telegram_id": 100,
            "role": "member",
            "allowed_domains": ["light", "media_player"],
            "allowed_areas": ["living_room"],
            "blocked_entities": ["light.secret"],
        },
        {"telegram_id": 200, "role": "admin"},
    ]
    ac = AccessController(users)

    # Admin always passes
    assert ac.check_entity(200, "light.secret", area="living_room", domain="light").allowed is True

    # Blocked entity rejected
    assert ac.check_entity(100, "light.secret", area="living_room", domain="light").allowed is False

    # Allowed domain & area
    assert ac.check_entity(100, "light.main", area="living_room", domain="light").allowed is True

    # Disallowed domain
    assert ac.check_entity(100, "switch.boiler", area="living_room", domain="switch").allowed is False

    # Disallowed area
    assert ac.check_entity(100, "light.bedroom", area="bedroom", domain="light").allowed is False


@pytest.mark.asyncio
async def test_bot_engine_tts_action():
    called = []

    async def fake_call(domain, service, payload):
        called.append((domain, service, payload))

    config = {
        "menu": {
            "main": {"type": "menu", "sections": ["tts_sec"], "roles": ["admin", "member"]},
            "tts_sec": {
                "title": "Озвучка",
                "roles": ["admin", "member"],
                "actions": [
                    {
                        "id": "say_hi",
                        "label": "Привіт",
                        "type": "speak",
                        "entity_id": "media_player.kolonka",
                        "message": "Привіт з розумного дому!",
                        "tts_service": "tts.google_translate_say",
                    }
                ],
            },
        }
    }
    ac = AccessController([{"telegram_id": 1, "role": "member"}])
    engine = BotEngine(config, ac, MessageRenderer(), ha_call_service=fake_call)

    res = await engine.handle_action(1, "say_hi", {})
    assert res["ok"] is True
    assert called == [("tts", "google_translate_say", {
        "entity_id": ["media_player.kolonka"],
        "message": "Привіт з розумного дому!",
    })]


@pytest.mark.asyncio
async def test_bot_engine_entities_browser():
    config = {
        "menu": {
            "main": {"type": "menu", "sections": ["lights"], "roles": ["admin"]},
            "lights": {
                "title": "Освітлення",
                "type": "entities",
                "roles": ["admin"],
                "source": {"mode": "domain", "value": "light"},
            },
        }
    }
    ac = AccessController([{"telegram_id": 1, "role": "admin"}])
    engine = BotEngine(config, ac, MessageRenderer())
    engine.set_catalog({
        "domains": {"light": ["light.hall", "light.kitchen"]},
        "areas": {"living_room": ["light.hall"]},
        "labels": {},
    })

    res = await engine.handle_navigation(1, "lights", {}, page=0)
    assert res["keyboard"]
    # Verify button callbacks
    callbacks = [btn["callback_data"] for row in res["keyboard"] for btn in row]
    assert "td:/tog_lights_0" in callbacks or "/tog_lights_0" in callbacks
    assert "td:/tog_lights_1" in callbacks or "/tog_lights_1" in callbacks
