"""Test the Muli binary sensor platform."""

from unittest.mock import MagicMock

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from syrupy.assertion import SnapshotAssertion


@pytest.fixture
def platforms() -> list[Platform]:
    """Fixture to specify platforms to test."""
    return [Platform.BINARY_SENSOR]


@pytest.mark.usefixtures("init_integration")
async def test_binary_sensor(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test binary sensor entity."""
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
    assert device_entry
    assert entity_entry.device_id == device_entry.id


@pytest.mark.usefixtures("init_integration")
async def test_alarm_sensor_triggered(
    hass: HomeAssistant,
    mock_muli_client: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test alarm sensor shows triggered state."""
    # Get initial state (alarm not triggered)
    state = hass.states.get("binary_sensor.muli_bike_alarm")
    assert state.state == "off"

    # Simulate alarm triggered
    mock_muli_client.get_device_data.return_value["securityData"]["alarm"] = True

    # Trigger coordinator update
    coordinator = mock_config_entry.runtime_data.data_coordinator
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Verify alarm sensor is now ON
    state = hass.states.get("binary_sensor.muli_bike_alarm")
    assert state.state == "on"


@pytest.mark.usefixtures("init_integration")
async def test_alarm_sensor_independent_of_mode(
    hass: HomeAssistant,
    mock_muli_client: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that alarm sensor state is independent of alarm mode setting."""
    coordinator = mock_config_entry.runtime_data.data_coordinator

    # Test alarm triggered with SILENT mode
    mock_muli_client.get_device_data.return_value["securityData"] = {
        "monitored": True,
        "movementAlarm": False,  # Silent mode
        "alarm": True,  # Alarm triggered
    }

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.muli_bike_alarm")
    assert state.state == "on"

    # Test alarm triggered with AUDIBLE mode
    mock_muli_client.get_device_data.return_value["securityData"]["movementAlarm"] = (
        True  # Audible mode
    )

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.muli_bike_alarm")
    # Alarm sensor should still be ON regardless of mode
    assert state.state == "on"

    # Test alarm cleared with AUDIBLE mode still enabled
    mock_muli_client.get_device_data.return_value["securityData"]["alarm"] = False

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.muli_bike_alarm")
    # Alarm sensor should be OFF when alarm is cleared
    assert state.state == "off"


@pytest.mark.usefixtures("init_integration")
async def test_alarm_sensor_silent_mode_triggered(
    hass: HomeAssistant,
    mock_muli_client: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test alarm sensor detects silent mode alarm via suspiciousMovementSince."""
    coordinator = mock_config_entry.runtime_data.data_coordinator

    # Silent mode with suspicious movement detected
    mock_muli_client.get_device_data.return_value["securityData"] = {
        "monitored": True,
        "movementAlarm": False,  # Silent mode
        "alarm": False,  # Not audible alarm
        "suspiciousMovementSince": "2024-01-15T10:25:00.000Z",
    }

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.muli_bike_alarm")
    # Alarm should be ON due to suspiciousMovementSince presence
    assert state.state == "on"


@pytest.mark.usefixtures("init_integration")
async def test_alarm_sensor_silent_mode_cleared(
    hass: HomeAssistant,
    mock_muli_client: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test alarm sensor shows OFF when suspiciousMovementSince is absent."""
    coordinator = mock_config_entry.runtime_data.data_coordinator

    # Silent mode enabled but no suspicious movement
    mock_muli_client.get_device_data.return_value["securityData"] = {
        "monitored": True,
        "movementAlarm": False,  # Silent mode
        "alarm": False,
    }
    # Note: no "suspiciousMovementSince" field

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.muli_bike_alarm")
    assert state.state == "off"
