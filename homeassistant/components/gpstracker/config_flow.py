"""Config flow for GPS Tracker integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import gps_tracker
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EXTERNAL_URL, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_EXTERNAL_URL, default=gps_tracker.Config.default_api_url()
        ): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    cfg = gps_tracker.Config(
        api_url=data[CONF_EXTERNAL_URL],
        password=data[CONF_PASSWORD],
        username=data[CONF_USERNAME],
    )

    async with gps_tracker.AsyncClient(cfg) as client:
        try:
            await client.get_devices()
        except gps_tracker.client.exceptions.UnauthorizedQuery:
            raise InvalidAuth
        except (
            gps_tracker.client.exceptions.HttpException,
            aiohttp.ClientResponseError,
        ):
            raise CannotConnect


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GPS Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            await validate_input(self.hass, user_input)
            await self.async_set_unique_id(
                f"{user_input[CONF_USERNAME]}@{user_input[CONF_EXTERNAL_URL]}"
            )
            self._abort_if_unique_id_configured()
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(
                title=user_input[CONF_USERNAME], data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
