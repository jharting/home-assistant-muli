"""Binary sensor platform for Muli integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MuliConfigEntry
from .entity import MuliEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuliConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up muli binary sensor platform."""
    coordinator = entry.runtime_data.data_coordinator
    async_add_entities(
        [
            MuliAlarmSensor(coordinator, entry),
        ]
    )


class MuliAlarmSensor(MuliEntity, BinarySensorEntity):
    """Representation of alarm state."""

    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the alarm sensor."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_alarm"
        self._attr_translation_key = "alarm"

    @property
    def is_on(self) -> bool | None:
        """Return true if alarm is triggered."""
        security_data = self.coordinator.data.get("securityData", {})
        return security_data.get("alarm")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and "securityData" in self.coordinator.data
