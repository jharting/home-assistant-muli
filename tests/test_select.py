"""Test the Muli select platform."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from syrupy.assertion import SnapshotAssertion


@pytest.fixture
def platforms() -> list[Platform]:
    """Fixture to specify platforms to test."""
    return [Platform.SELECT]


@pytest.mark.usefixtures("init_integration")
async def test_select(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test select entity."""
    # Verify entity is created
    entity_entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    assert len(entity_entries) == 1

    # Verify state matches snapshot
    entity_entry = entity_entries[0]
    assert (state := hass.states.get(entity_entry.entity_id))
    assert state == snapshot(name=f"{entity_entry.entity_id}-state")

    # Verify entity is assigned to correct device
    device_entry = device_registry.async_get_device(
        identifiers={("mulibikes", mock_config_entry.entry_id)}
    )
    assert entity_entry.device_id == device_entry.id


@pytest.mark.usefixtures("init_integration")
async def test_select_option(
    hass: HomeAssistant,
    mock_muli_client,
) -> None:
    """Test changing select option."""
    # Test selecting audible
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.muli_bike_alarm_mode", "option": "audible"},
        blocking=True,
    )
    mock_muli_client.set_movement_alarm.assert_called_with(True)

    # Test selecting silent
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.muli_bike_alarm_mode", "option": "silent"},
        blocking=True,
    )
    mock_muli_client.set_movement_alarm.assert_called_with(False)
