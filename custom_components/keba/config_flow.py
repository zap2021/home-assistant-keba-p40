"""Config flow for the KEBA integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KebaApiClient, KebaApiConfig, KebaApiError, KebaAuthenticationError
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_NUMBER,
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
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _async_validate_input(self.hass, user_input)
            except KebaAuthenticationError:
                errors["base"] = "invalid_auth"
            except KebaApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info[CONF_SERIAL_NUMBER])
                self._abort_if_unique_id_configured()
                user_input[CONF_SERIAL_NUMBER] = info[CONF_SERIAL_NUMBER]
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
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

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


async def _async_validate_input(hass, user_input: dict[str, Any]) -> dict[str, str]:
    """Validate the user input by talking to the wallbox."""
    session = async_get_clientsession(hass, verify_ssl=user_input.get(CONF_VERIFY_SSL, False))
    client = KebaApiClient(
        session,
        KebaApiConfig(
            host=user_input[CONF_HOST],
            port=user_input[CONF_PORT],
            username=user_input[CONF_USERNAME],
            password=user_input[CONF_PASSWORD],
            verify_ssl=user_input.get(CONF_VERIFY_SSL, False),
        ),
    )

    summary = await client.async_get_device_summary()
    wallbox = summary["wallbox"]
    serial_number = summary["serial_number"]
    title = wallbox.get("alias") or user_input[CONF_NAME]

    return {
        CONF_SERIAL_NUMBER: serial_number,
        "title": title,
    }
