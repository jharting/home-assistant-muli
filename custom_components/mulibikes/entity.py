"""Base entity for Muli integration."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MuliDataUpdateCoordinator


class MuliEntity(CoordinatorEntity[MuliDataUpdateCoordinator]):
    """Base class for Muli entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MuliDataUpdateCoordinator, entry_id: str) -> None:
        """Initialize the Muli entity."""
        super().__init__(coordinator)
        self._entry_id = entry_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Muli Bike",
            manufacturer="Muli",
            model="Cargo bike",
        )
