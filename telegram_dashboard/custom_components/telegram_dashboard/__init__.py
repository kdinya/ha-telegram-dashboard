"""Telegram Dashboard integration.

Exposes every bot action as a Home Assistant service so it can be used
from Automations and Scripts ("Add action" picker) without YAML.
"""
from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from .const import CONF_BOT_TOKEN, DOMAIN

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Optional(CONF_BOT_TOKEN): cv.string})},
    extra=vol.ALLOW_EXTRA,
)

SEND_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required("message"): cv.string,
        vol.Optional("chat_id"): vol.Any(cv.string, cv.positive_int),
        vol.Optional("parse_mode", default="HTML"): vol.In(["HTML", "Markdown", "MarkdownV2"]),
        vol.Optional("disable_notification", default=False): cv.boolean,
        vol.Optional("inline_keyboard"): list,
    },
    extra=vol.ALLOW_EXTRA,
)
EDIT_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required("message"): cv.string,
        vol.Optional("chat_id"): vol.Any(cv.string, cv.positive_int),
        vol.Required("message_id"): cv.positive_int,
        vol.Optional("parse_mode", default="HTML"): vol.In(["HTML", "Markdown", "MarkdownV2"]),
        vol.Optional("inline_keyboard"): list,
    },
    extra=vol.ALLOW_EXTRA,
)
DELETE_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required("message_id"): cv.positive_int,
        vol.Optional("chat_id"): vol.Any(cv.string, cv.positive_int),
    },
    extra=vol.ALLOW_EXTRA,
)
ANSWER_CALLBACK_SCHEMA = vol.Schema(
    {
        vol.Required("callback_query_id"): cv.string,
        vol.Optional("message"): cv.string,
        vol.Optional("show_alert", default=False): cv.boolean,
    },
    extra=vol.ALLOW_EXTRA,
)
SEND_PHOTO_SCHEMA = vol.Schema(
    {
        vol.Required("photo"): cv.string,
        vol.Optional("chat_id"): vol.Any(cv.string, cv.positive_int),
        vol.Optional("caption"): cv.string,
        vol.Optional("parse_mode", default="HTML"): vol.In(["HTML", "Markdown", "MarkdownV2"]),
        vol.Optional("inline_keyboard"): list,
    },
    extra=vol.ALLOW_EXTRA,
)
SEND_DOCUMENT_SCHEMA = vol.Schema(
    {
        vol.Required("document"): cv.string,
        vol.Optional("chat_id"): vol.Any(cv.string, cv.positive_int),
        vol.Optional("caption"): cv.string,
        vol.Optional("parse_mode", default="HTML"): vol.In(["HTML", "Markdown", "MarkdownV2"]),
        vol.Optional("inline_keyboard"): list,
    },
    extra=vol.ALLOW_EXTRA,
)
SPEAK_SCHEMA = vol.Schema(
    {
        vol.Required("message"): cv.string,
        vol.Required("entity_id"): cv.string,
        vol.Optional("tts_service", default="tts.google_translate_say"): cv.string,
    },
    extra=vol.ALLOW_EXTRA,
)


async def _call_telegram(hass: HomeAssistant, token: str, method: str, payload: dict) -> dict:
    """Delegate Telegram action to Home Assistant's standard telegram_bot integration."""
    try:
        res = await hass.services.async_call("telegram_bot", method, payload, blocking=True, return_response=True)
        return res or {}
    except Exception as err:
        raise HomeAssistantError(f"Telegram action telegram_bot.{method} failed: {err}") from err


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Telegram Dashboard integration from config flow or YAML."""
    conf = config.get(DOMAIN) or {}
    token = conf.get(CONF_BOT_TOKEN) or hass.data.get(DOMAIN, {}).get(CONF_BOT_TOKEN, "")
    hass.data.setdefault(DOMAIN, {})
    if token:
        hass.data[DOMAIN][CONF_BOT_TOKEN] = token

    def _require_token() -> str:
        token = hass.data.get(DOMAIN, {}).get(CONF_BOT_TOKEN, "")
        if not token:
            raise HomeAssistantError(
                "Telegram bot token is not configured. Configure the Telegram Dashboard integration first."
            )
        return token

    async def handle_send_message(call: ServiceCall) -> None:
        token = _require_token()
        payload: dict = {"text": call.data["message"], "parse_mode": call.data.get("parse_mode", "HTML")}
        chat_id = call.data.get("chat_id") or hass.data[DOMAIN].get("default_chat_id")
        if not chat_id:
            raise HomeAssistantError("chat_id is required (or set a default chat in the integration options)")
        payload["chat_id"] = chat_id
        if call.data.get("disable_notification"):
            payload["disable_notification"] = True
        kb = call.data.get("inline_keyboard")
        if kb:
            payload["reply_markup"] = {"inline_keyboard": kb}
        await _call_telegram(hass, token, "sendMessage", payload)

    async def handle_edit_message(call: ServiceCall) -> None:
        token = _require_token()
        payload: dict = {
            "text": call.data["message"],
            "message_id": call.data["message_id"],
            "parse_mode": call.data.get("parse_mode", "HTML"),
        }
        chat_id = call.data.get("chat_id") or hass.data[DOMAIN].get("default_chat_id")
        if not chat_id:
            raise HomeAssistantError("chat_id is required (or set a default chat in the integration options)")
        payload["chat_id"] = chat_id
        kb = call.data.get("inline_keyboard")
        if kb:
            payload["reply_markup"] = {"inline_keyboard": kb}
        await _call_telegram(hass, token, "editMessageText", payload)

    async def handle_delete_message(call: ServiceCall) -> None:
        token = _require_token()
        payload: dict = {"message_id": call.data["message_id"]}
        chat_id = call.data.get("chat_id") or hass.data[DOMAIN].get("default_chat_id")
        if not chat_id:
            raise HomeAssistantError("chat_id is required (or set a default chat in the integration options)")
        payload["chat_id"] = chat_id
        await _call_telegram(hass, token, "deleteMessage", payload)

    async def handle_answer_callback(call: ServiceCall) -> None:
        token = _require_token()
        payload: dict = {"callback_query_id": call.data["callback_query_id"]}
        if call.data.get("message"):
            payload["text"] = call.data["message"]
        if call.data.get("show_alert"):
            payload["show_alert"] = True
        await _call_telegram(hass, token, "answerCallbackQuery", payload)

    async def handle_send_photo(call: ServiceCall) -> None:
        token = _require_token()
        payload: dict = {"photo": call.data["photo"]}
        chat_id = call.data.get("chat_id") or hass.data[DOMAIN].get("default_chat_id")
        if not chat_id:
            raise HomeAssistantError("chat_id is required (or set a default chat in the integration options)")
        payload["chat_id"] = chat_id
        if call.data.get("caption"):
            payload["caption"] = call.data["caption"]
        kb = call.data.get("inline_keyboard")
        if kb:
            payload["reply_markup"] = {"inline_keyboard": kb}
        await _call_telegram(hass, token, "sendPhoto", payload)

    async def handle_send_document(call: ServiceCall) -> None:
        token = _require_token()
        payload: dict = {"document": call.data["document"]}
        chat_id = call.data.get("chat_id") or hass.data[DOMAIN].get("default_chat_id")
        if not chat_id:
            raise HomeAssistantError("chat_id is required (or set a default chat in the integration options)")
        payload["chat_id"] = chat_id
        if call.data.get("caption"):
            payload["caption"] = call.data["caption"]
        kb = call.data.get("inline_keyboard")
        if kb:
            payload["reply_markup"] = {"inline_keyboard": kb}
        await _call_telegram(hass, token, "sendDocument", payload)

    async def handle_speak(call: ServiceCall) -> None:
        """Speak a message through a smart speaker via a TTS service."""
        target_entity = str(call.data["entity_id"]).strip()
        if not target_entity.startswith("media_player."):
            raise HomeAssistantError(f"Entity '{target_entity}' must be in the media_player domain")
        svc_name = str(call.data.get("tts_service", "tts.google_translate_say")).strip().lower()
        if "." in svc_name:
            domain, service = svc_name.split(".", 1)
        else:
            domain, service = "tts", svc_name
        if domain != "tts":
            raise HomeAssistantError(f"Invalid TTS service '{svc_name}': domain must be 'tts'")
        await hass.services.async_call(
            domain,
            service,
            {
                "entity_id": target_entity,
                "message": call.data["message"],
            },
            blocking=False,
        )

    hass.services.async_register(DOMAIN, "send_message", handle_send_message, schema=SEND_MESSAGE_SCHEMA)
    hass.services.async_register(DOMAIN, "edit_message", handle_edit_message, schema=EDIT_MESSAGE_SCHEMA)
    hass.services.async_register(DOMAIN, "delete_message", handle_delete_message, schema=DELETE_MESSAGE_SCHEMA)
    hass.services.async_register(DOMAIN, "answer_callback", handle_answer_callback, schema=ANSWER_CALLBACK_SCHEMA)
    hass.services.async_register(DOMAIN, "send_photo", handle_send_photo, schema=SEND_PHOTO_SCHEMA)
    hass.services.async_register(DOMAIN, "send_document", handle_send_document, schema=SEND_DOCUMENT_SCHEMA)
    hass.services.async_register(DOMAIN, "speak", handle_speak, schema=SPEAK_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Store the token from the config entry and reload services."""
    token = entry.data.get(CONF_BOT_TOKEN, "")
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][CONF_BOT_TOKEN] = token
    hass.data[DOMAIN]["default_chat_id"] = entry.data.get("default_chat_id", "")
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    hass.data.get(DOMAIN, {}).pop(CONF_BOT_TOKEN, None)
    return True
