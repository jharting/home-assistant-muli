"""Sensor platform for Muli integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfLength, UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MuliConfigEntry
from .entity import MuliEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuliConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up muli sensor platform."""
    data_coordinator = entry.runtime_data.data_coordinator
    bike_details_coordinator = entry.runtime_data.bike_details_coordinator

    async_add_entities(
        [
            MuliBatterySensor(data_coordinator, entry),
            MuliTotalMileageSensor(data_coordinator, entry),
            MuliRemainingDistanceSensor(data_coordinator, entry),
            MuliBatteryCyclesSensor(data_coordinator, entry),
            MuliAssistanceLevelSensor(data_coordinator, entry),
            MuliSpeedSensor(data_coordinator, entry),
            MuliStatusSensor(data_coordinator, entry),
            MuliFirmwareVersionSensor(bike_details_coordinator, entry),
            MuliHardwareVersionSensor(bike_details_coordinator, entry),
            MuliGpsTrackerBatterySensor(bike_details_coordinator, entry),
        ]
    )


class MuliBatterySensor(MuliEntity, SensorEntity):
    """Representation of a muli battery sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_battery"
        self._attr_translation_key = "battery"

    @property
    def native_value(self) -> int | None:
        """Return the battery level from coordinator data."""
        vehicle_data = self.coordinator.data.get("vehicleData", {})
        return vehicle_data.get("batteryLevel")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and "vehicleData" in self.coordinator.data
            and "batteryLevel" in self.coordinator.data.get("vehicleData", {})
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        vehicle_data = self.coordinator.data.get("vehicleData", {})
        return {
            "last_update_time": vehicle_data.get("lastUpdateDateTime"),
        }


class MuliTotalMileageSensor(MuliEntity, SensorEntity):
    """Representation of total mileage (odometer)."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the total mileage sensor."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_total_mileage"
        self._attr_translation_key = "total_mileage"

    @property
    def native_value(self) -> int | None:
        """Return the total mileage from coordinator data."""
        vehicle_data = self.coordinator.data.get("vehicleData", {})
        return vehicle_data.get("totalMileage")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and "vehicleData" in self.coordinator.data
            and "totalMileage" in self.coordinator.data.get("vehicleData", {})
        )


class MuliRemainingDistanceSensor(MuliEntity, SensorEntity):
    """Representation of remaining distance (range)."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the remaining distance sensor."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_remaining_distance"
        self._attr_translation_key = "remaining_distance"

    @property
    def native_value(self) -> int | None:
        """Return the remaining distance from coordinator data."""
        vehicle_data = self.coordinator.data.get("vehicleData", {})
        return vehicle_data.get("remainDistance")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and "vehicleData" in self.coordinator.data
            and "remainDistance" in self.coordinator.data.get("vehicleData", {})
        )


class MuliBatteryCyclesSensor(MuliEntity, SensorEntity):
    """Representation of battery charge cycles."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:battery-sync"

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the battery cycles sensor."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_battery_cycles"
        self._attr_translation_key = "battery_cycles"

    @property
    def native_value(self) -> int | None:
        """Return the battery cycles from coordinator data."""
        vehicle_data = self.coordinator.data.get("vehicleData", {})
        battery_health = vehicle_data.get("batteryHealth", {})
        return battery_health.get("batteryCycles")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and "vehicleData" in self.coordinator.data
            and "batteryHealth" in self.coordinator.data.get("vehicleData", {})
            and "batteryCycles"
            in self.coordinator.data.get("vehicleData", {}).get("batteryHealth", {})
        )


class MuliAssistanceLevelSensor(MuliEntity, SensorEntity):
    """Representation of electric assistance level."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:electric-switch"

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the assistance level sensor."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_assistance_level"
        self._attr_translation_key = "assistance_level"

    @property
    def native_value(self) -> int | None:
        """Return the assistance level from coordinator data."""
        vehicle_data = self.coordinator.data.get("vehicleData", {})
        return vehicle_data.get("assistanceLevel")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and "vehicleData" in self.coordinator.data
            and "assistanceLevel" in self.coordinator.data.get("vehicleData", {})
        )


class MuliSpeedSensor(MuliEntity, SensorEntity):
    """Representation of current speed."""

    _attr_device_class = SensorDeviceClass.SPEED
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the speed sensor."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_speed"
        self._attr_translation_key = "speed"

    @property
    def native_value(self) -> float | None:
        """Return the speed from coordinator data."""
        bike_position_data = self.coordinator.data.get("bikePositionData", {})
        speed_raw = bike_position_data.get("speed")
        return round(speed_raw / 10, 1) if speed_raw is not None else None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and "bikePositionData" in self.coordinator.data


class MuliStatusSensor(MuliEntity, SensorEntity):
    """Representation of product status."""

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the status sensor."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_translation_key = "status"

    @property
    def native_value(self) -> str | None:
        """Return the product status from coordinator data."""
        bike_position_data = self.coordinator.data.get("bikePositionData", {})
        return bike_position_data.get("productStatus")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and "bikePositionData" in self.coordinator.data


class MuliFirmwareVersionSensor(MuliEntity, SensorEntity):
    """Representation of firmware version."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:chip"

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the firmware version sensor."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_firmware_version"
        self._attr_translation_key = "firmware_version"

    @property
    def native_value(self) -> str | None:
        """Return the firmware version from coordinator data."""
        return self.coordinator.data.get("productFirmwareVersion")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available


class MuliHardwareVersionSensor(MuliEntity, SensorEntity):
    """Representation of hardware version."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:memory"

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the hardware version sensor."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_hardware_version"
        self._attr_translation_key = "hardware_version"

    @property
    def native_value(self) -> str | None:
        """Return the hardware version from coordinator data."""
        return self.coordinator.data.get("productHardwareVersion")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available


class MuliGpsTrackerBatterySensor(MuliEntity, SensorEntity):
    """Representation of GPS tracker battery level."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the GPS tracker battery sensor."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_gps_tracker_battery"
        self._attr_translation_key = "gps_tracker_battery"

    @property
    def native_value(self) -> int | None:
        """Return the GPS tracker battery level from coordinator data."""
        return self.coordinator.data.get("iotBatteryLevel")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available
