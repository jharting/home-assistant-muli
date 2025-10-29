"""Device tracker platform for Muli integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MuliConfigEntry
from .entity import MuliEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuliConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up muli device tracker platform."""
    coordinator = entry.runtime_data.data_coordinator
    async_add_entities([MuliDeviceTracker(coordinator, entry)])


class MuliDeviceTracker(MuliEntity, TrackerEntity):
    """Representation of a muli device tracker."""

    _attr_icon = "mdi:bicycle-cargo"
    _attr_entity_picture = "https://openclipart.org/image/128px/svg_to_png/345917"

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_location"
        self._attr_translation_key = "location"

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the device tracker."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        bike_position_data = self.coordinator.data.get("bikePositionData", {})
        return bike_position_data.get("latitude")

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        bike_position_data = self.coordinator.data.get("bikePositionData", {})
        return bike_position_data.get("longitude")

    @property
    def location_accuracy(self) -> int:
        """Return the location accuracy of the device in meters."""
        # Default GPS accuracy estimate
        return 10

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        bike_position_data = self.coordinator.data.get("bikePositionData", {})
        return {
            "gps_signal_lost": bike_position_data.get("gpsSignalLost", False),
            "last_position_time": bike_position_data.get("lastDatePosition"),
            "last_signal_time": bike_position_data.get("dateLastSignal"),
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and "bikePositionData" in self.coordinator.data
            and self.latitude is not None
            and self.longitude is not None
        )
