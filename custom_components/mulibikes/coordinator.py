"""Data update coordinator for Muli integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MuliAuthenticationError, MuliClient, MuliConnectionError
from .const import (
    BIKE_DETAILS_UPDATE_INTERVAL,
    CONF_REFRESH_TOKEN,
    DOMAIN,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# Forward reference - actual definition is in __init__.py to avoid circular import
type MuliConfigEntry = ConfigEntry[Any]


class MuliDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Muli data from the API."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: MuliClient
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            config_entry=entry,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint.

        This is the only method that should fetch data.
        """
        try:
            data = await self.client.get_device_data()
        except MuliAuthenticationError:
            # Try to refresh the token first
            _LOGGER.debug("Access token expired, attempting refresh")
            try:
                assert self.config_entry is not None
                refresh_token = self.config_entry.data[CONF_REFRESH_TOKEN]
                new_token_data = await self.client.refresh_access_token(refresh_token)

                # Update the access token in the client
                self.client.access_token = new_token_data["access_token"]

                # Update config entry with new access token
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={
                        **self.config_entry.data,
                        CONF_ACCESS_TOKEN: new_token_data["access_token"],
                    },
                )

                _LOGGER.info("Successfully refreshed access token")

                # Retry the data fetch with new token
                data = await self.client.get_device_data()

            except MuliAuthenticationError as refresh_err:
                # Refresh token also expired, trigger reauth
                _LOGGER.warning("Refresh token expired, reauth flow will be triggered")
                raise ConfigEntryAuthFailed(
                    "Refresh token expired, please re-authenticate"
                ) from refresh_err
            except MuliConnectionError as conn_err:
                # Network error during refresh
                raise UpdateFailed(f"Failed to refresh token: {conn_err}") from conn_err

        except MuliConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        _LOGGER.debug("Coordinator fetched data: %s", data)
        return data

    async def async_set_monitored(self, monitored: bool) -> None:
        """Set monitored state with automatic token refresh.

        Args:
            monitored: True to arm alarm, False to disarm

        Raises:
            ConfigEntryAuthFailed: If refresh token expired
            UpdateFailed: If connection fails
        """
        try:
            await self.client.set_monitored(monitored)
        except MuliAuthenticationError:
            # Try to refresh the token first
            _LOGGER.debug("Access token expired, attempting refresh")
            try:
                assert self.config_entry is not None
                refresh_token = self.config_entry.data[CONF_REFRESH_TOKEN]
                new_token_data = await self.client.refresh_access_token(refresh_token)

                # Update the access token in the client
                self.client.access_token = new_token_data["access_token"]

                # Update config entry with new access token
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={
                        **self.config_entry.data,
                        CONF_ACCESS_TOKEN: new_token_data["access_token"],
                    },
                )

                _LOGGER.info("Successfully refreshed access token")

                # Retry the API call with new token
                await self.client.set_monitored(monitored)

            except MuliAuthenticationError as refresh_err:
                # Refresh token also expired, trigger reauth
                _LOGGER.warning("Refresh token expired, reauth flow will be triggered")
                raise ConfigEntryAuthFailed(
                    "Refresh token expired, please re-authenticate"
                ) from refresh_err
            except MuliConnectionError as conn_err:
                # Network error during refresh
                raise UpdateFailed(f"Failed to refresh token: {conn_err}") from conn_err

        except MuliConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        # Refresh coordinator data to reflect new state
        await self.async_request_refresh()

    async def async_set_movement_alarm(self, enabled: bool) -> None:
        """Set movement alarm state with automatic token refresh.

        Args:
            enabled: True to enable movement alarm, False to disable

        Raises:
            ConfigEntryAuthFailed: If refresh token expired
            UpdateFailed: If connection fails
        """
        try:
            await self.client.set_movement_alarm(enabled)
        except MuliAuthenticationError:
            # Try to refresh the token first
            _LOGGER.debug("Access token expired, attempting refresh")
            try:
                assert self.config_entry is not None
                refresh_token = self.config_entry.data[CONF_REFRESH_TOKEN]
                new_token_data = await self.client.refresh_access_token(refresh_token)

                # Update the access token in the client
                self.client.access_token = new_token_data["access_token"]

                # Update config entry with new access token
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={
                        **self.config_entry.data,
                        CONF_ACCESS_TOKEN: new_token_data["access_token"],
                    },
                )

                _LOGGER.info("Successfully refreshed access token")

                # Retry the API call with new token
                await self.client.set_movement_alarm(enabled)

            except MuliAuthenticationError as refresh_err:
                # Refresh token also expired, trigger reauth
                _LOGGER.warning("Refresh token expired, reauth flow will be triggered")
                raise ConfigEntryAuthFailed(
                    "Refresh token expired, please re-authenticate"
                ) from refresh_err
            except MuliConnectionError as conn_err:
                # Network error during refresh
                raise UpdateFailed(f"Failed to refresh token: {conn_err}") from conn_err

        except MuliConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        # Refresh coordinator data to reflect new state
        await self.async_request_refresh()


class MuliBikeDetailsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Muli bike details from the API."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: MuliClient
    ) -> None:
        """Initialize the bike details coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_bike_details",
            update_interval=BIKE_DETAILS_UPDATE_INTERVAL,
            config_entry=entry,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch bike details from API endpoint.

        This is the only method that should fetch bike details.
        """
        try:
            data = await self.client.get_bike_details()
        except MuliAuthenticationError:
            # Try to refresh the token first
            _LOGGER.debug("Access token expired, attempting refresh")
            try:
                assert self.config_entry is not None
                refresh_token = self.config_entry.data[CONF_REFRESH_TOKEN]
                new_token_data = await self.client.refresh_access_token(refresh_token)

                # Update the access token in the client
                self.client.access_token = new_token_data["access_token"]

                # Update config entry with new access token
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={
                        **self.config_entry.data,
                        CONF_ACCESS_TOKEN: new_token_data["access_token"],
                    },
                )

                _LOGGER.info("Successfully refreshed access token")

                # Retry the data fetch with new token
                data = await self.client.get_bike_details()

            except MuliAuthenticationError as refresh_err:
                # Refresh token also expired, trigger reauth
                _LOGGER.warning("Refresh token expired, reauth flow will be triggered")
                raise ConfigEntryAuthFailed(
                    "Refresh token expired, please re-authenticate"
                ) from refresh_err
            except MuliConnectionError as conn_err:
                # Network error during refresh
                raise UpdateFailed(f"Failed to refresh token: {conn_err}") from conn_err

        except MuliConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        _LOGGER.debug("Bike details coordinator fetched data: %s", data)
        return data
