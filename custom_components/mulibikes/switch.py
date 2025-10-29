"""Switch platform for muli integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import UpdateFailed

from . import MuliConfigEntry
from .entity import MuliEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuliConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up muli switch platform."""
    coordinator = entry.runtime_data.data_coordinator
    async_add_entities(
        [
            MuliSwitch(coordinator, entry),
            MuliMovementAlarmSwitch(coordinator, entry),
        ]
    )


class MuliSwitch(MuliEntity, SwitchEntity):
    """Representation of a muli alarm armed switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_armed"
        self._attr_translation_key = "armed"

    @property
    def is_on(self) -> bool | None:
        """Return if alarm is armed."""
        security_data = self.coordinator.data.get("securityData", {})
        return security_data.get("monitored")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and "securityData" in self.coordinator.data
            and "monitored" in self.coordinator.data.get("securityData", {})
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Arm the alarm."""
        try:
            await self.coordinator.async_set_monitored(True)
        except UpdateFailed as err:
            raise HomeAssistantError(f"Failed to arm alarm: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disarm the alarm."""
        try:
            await self.coordinator.async_set_monitored(False)
        except UpdateFailed as err:
            raise HomeAssistantError(f"Failed to disarm alarm: {err}") from err


class MuliMovementAlarmSwitch(MuliEntity, SwitchEntity):
    """Representation of movement alarm switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the movement alarm switch."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_movement_alarm"
        self._attr_translation_key = "movement_alarm"

    @property
    def is_on(self) -> bool | None:
        """Return if movement alarm is enabled."""
        security_data = self.coordinator.data.get("securityData", {})
        return security_data.get("movementAlarm")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and "securityData" in self.coordinator.data
            and "movementAlarm" in self.coordinator.data.get("securityData", {})
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable movement alarm."""
        try:
            await self.coordinator.async_set_movement_alarm(True)
        except UpdateFailed as err:
            raise HomeAssistantError(f"Failed to enable movement alarm: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable movement alarm."""
        try:
            await self.coordinator.async_set_movement_alarm(False)
        except UpdateFailed as err:
            raise HomeAssistantError(
                f"Failed to disable movement alarm: {err}"
            ) from err
