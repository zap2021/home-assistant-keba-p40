"""Config flow for the KEBA integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_HOST,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)


class KebaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KEBA."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            entry_data = dict(user_input)
            entry_data[CONF_HOST] = entry_data[CONF_HOST].strip()

            await self.async_set_unique_id(_entry_unique_id(entry_data))
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=entry_data[CONF_NAME],
                data=entry_data,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
                vol.Optional(CONF_SCAN_INTERVAL, default=30): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=5, max=3600),
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors={})


def _entry_unique_id(user_input: dict[str, Any]) -> str:
    """Return the stable unique ID available before the connection test."""
    return f"{user_input[CONF_HOST].lower()}:{user_input[CONF_PORT]}"
