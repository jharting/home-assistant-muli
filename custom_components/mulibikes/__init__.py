"""Integration for Muli electric cargo bikes."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MuliClient
from .coordinator import MuliBikeDetailsCoordinator, MuliDataUpdateCoordinator


@dataclass
class MuliRuntimeData:
    """Runtime data for Muli integration."""

    data_coordinator: MuliDataUpdateCoordinator
    bike_details_coordinator: MuliBikeDetailsCoordinator


type MuliConfigEntry = ConfigEntry[MuliRuntimeData]

_PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: MuliConfigEntry) -> bool:
    """Set up muli from a config entry."""
    # Create API client with stored access token
    websession = async_get_clientsession(hass)
    access_token = entry.data[CONF_ACCESS_TOKEN]
    client = MuliClient(websession, access_token)

    # Create coordinators
    data_coordinator = MuliDataUpdateCoordinator(hass, entry, client)
    bike_details_coordinator = MuliBikeDetailsCoordinator(hass, entry, client)

    # Fetch initial data from both coordinators
    await data_coordinator.async_config_entry_first_refresh()
    await bike_details_coordinator.async_config_entry_first_refresh()

    # Store coordinators for platforms to access
    entry.runtime_data = MuliRuntimeData(
        data_coordinator=data_coordinator,
        bike_details_coordinator=bike_details_coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: MuliConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
