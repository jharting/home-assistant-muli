"""Config flow for Muli integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import MuliAuthenticationError, MuliClient, MuliConnectionError
from .const import CONF_REFRESH_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    websession = async_get_clientsession(hass)
    client = MuliClient(websession)

    try:
        tokens = await client.login(data[CONF_EMAIL], data[CONF_PASSWORD])
    except MuliAuthenticationError as err:
        raise InvalidAuth from err
    except MuliConnectionError as err:
        raise CannotConnect from err

    # Return data to store in the config entry
    return {
        "title": f"Muli ({data[CONF_EMAIL]})",
        CONF_EMAIL: data[CONF_EMAIL],
        CONF_ACCESS_TOKEN: tokens["access_token"],
        CONF_REFRESH_TOKEN: tokens["refresh_token"],
    }


class MuliConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for muli."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Set unique_id based on email to prevent duplicates
                await self.async_set_unique_id(info[CONF_EMAIL])
                self._abort_if_unique_id_configured()

                # Store email and tokens, but not the password
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_EMAIL: info[CONF_EMAIL],
                        CONF_ACCESS_TOKEN: info[CONF_ACCESS_TOKEN],
                        CONF_REFRESH_TOKEN: info[CONF_REFRESH_TOKEN],
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication when refresh token expires."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth and collect new credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                # Set unique_id based on email
                await self.async_set_unique_id(info[CONF_EMAIL])

                # Verify it's the same account
                self._abort_if_unique_id_mismatch(reason="wrong_account")

                # Update config entry with new tokens
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={
                        CONF_ACCESS_TOKEN: info[CONF_ACCESS_TOKEN],
                        CONF_REFRESH_TOKEN: info[CONF_REFRESH_TOKEN],
                    },
                )
            except AbortFlow:
                raise
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "email": self._get_reauth_entry().data[CONF_EMAIL]
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
