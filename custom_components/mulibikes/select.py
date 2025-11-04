"""Select platform for Muli integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MuliConfigEntry
from .entity import MuliEntity

ALARM_MODE_SILENT = "silent"
ALARM_MODE_AUDIBLE = "audible"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuliConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Muli select platform."""
    coordinator = entry.runtime_data.data_coordinator
    async_add_entities([MuliAlarmModeSelect(coordinator, entry)])


class MuliAlarmModeSelect(MuliEntity, SelectEntity):
    """Representation of Muli alarm mode select."""

    _attr_icon = "mdi:bell"
    _attr_options = [ALARM_MODE_SILENT, ALARM_MODE_AUDIBLE]

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the select."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_alarm_mode"
        self._attr_translation_key = "alarm_mode"

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if "securityData" not in self.coordinator.data:
            return None
        if "movementAlarm" not in self.coordinator.data["securityData"]:
            return None

        is_audible = self.coordinator.data["securityData"]["movementAlarm"]
        return ALARM_MODE_AUDIBLE if is_audible else ALARM_MODE_SILENT

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        is_audible = option == ALARM_MODE_AUDIBLE
        await self.coordinator.async_set_movement_alarm(is_audible)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and "securityData" in self.coordinator.data
            and "movementAlarm" in self.coordinator.data["securityData"]
        )
