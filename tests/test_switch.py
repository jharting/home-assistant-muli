"""Test the Muli switch platform."""

from unittest.mock import MagicMock

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from syrupy.assertion import SnapshotAssertion


@pytest.fixture
def platforms() -> list[Platform]:
    """Fixture to specify platforms to test."""
    return [Platform.SWITCH]


@pytest.mark.usefixtures("init_integration")
async def test_switches(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test all switch entities."""
    # Verify entities are created
    entity_entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    assert len(entity_entries) == 1

    # Verify states match snapshot
    for entity_entry in entity_entries:
        assert (state := hass.states.get(entity_entry.entity_id))
        assert state == snapshot(name=f"{entity_entry.entity_id}-state")

    # Verify entities are assigned to correct device
    device_entry = device_registry.async_get_device(
        identifiers={("mulibikes", mock_config_entry.entry_id)}
    )
    assert device_entry

    for entity_entry in entity_entries:
        assert entity_entry.device_id == device_entry.id


@pytest.mark.usefixtures("init_integration")
async def test_switch_turn_on_armed(
    hass: HomeAssistant,
    mock_muli_client: MagicMock,
) -> None:
    """Test turning on the armed switch."""
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.muli_bike_armed"},
        blocking=True,
    )

    mock_muli_client.set_monitored.assert_called_once_with(True)


@pytest.mark.usefixtures("init_integration")
async def test_switch_turn_off_armed(
    hass: HomeAssistant,
    mock_muli_client: MagicMock,
) -> None:
    """Test turning off the armed switch."""
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.muli_bike_armed"},
        blocking=True,
    )

    mock_muli_client.set_monitored.assert_called_once_with(False)
