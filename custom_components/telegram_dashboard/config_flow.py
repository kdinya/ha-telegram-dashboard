"""Config flow for Telegram Dashboard integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from .const import CONF_BOT_TOKEN, DOMAIN


class TelegramDashboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            token = user_input.get(CONF_BOT_TOKEN, "").strip()
            if not token:
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(
                    title="Telegram Dashboard",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_BOT_TOKEN): str,
                vol.Optional("default_chat_id"): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
