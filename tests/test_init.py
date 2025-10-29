"""Test the Muli integration init."""

from unittest.mock import MagicMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mulibikes.api import MuliAuthenticationError, MuliConnectionError


async def test_setup_unload(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_muli_client: MagicMock,
) -> None:
    """Test successful setup and unload."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_muli_client.get_device_data.call_count >= 1
    assert mock_muli_client.get_bike_details.call_count >= 1

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_connection_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_muli_client: MagicMock,
) -> None:
    """Test setup failure due to connection error."""
    mock_config_entry.add_to_hass(hass)

    mock_muli_client.get_device_data.side_effect = MuliConnectionError(
        "Connection failed"
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_auth_error_triggers_reauth(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_muli_client: MagicMock,
) -> None:
    """Test setup failure due to authentication error triggers reauth."""
    mock_config_entry.add_to_hass(hass)

    # First call fails with auth error, refresh also fails
    mock_muli_client.get_device_data.side_effect = MuliAuthenticationError(
        "Token expired"
    )
    mock_muli_client.refresh_access_token.side_effect = MuliAuthenticationError(
        "Refresh token expired"
    )

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    # Check that reauth flow was triggered
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"


async def test_coordinator_refresh_token_on_auth_error(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_muli_client: MagicMock,
) -> None:
    """Test coordinator refreshes token on authentication error."""
    # Reset the mock to track new calls
    mock_muli_client.get_device_data.reset_mock()
    mock_muli_client.refresh_access_token.reset_mock()

    # First call fails with auth, then succeeds after refresh
    mock_muli_client.get_device_data.side_effect = [
        MuliAuthenticationError("Token expired"),
        {
            "vehicleData": {"batteryLevel": 90},
            "bikePositionData": {},
            "securityData": {},
        },
    ]

    # Trigger a coordinator refresh
    runtime_data = init_integration.runtime_data
    await runtime_data.data_coordinator.async_refresh()
    await hass.async_block_till_done()

    # Verify token refresh was called
    assert mock_muli_client.refresh_access_token.call_count == 1
    # Verify data fetch was retried after refresh
    assert mock_muli_client.get_device_data.call_count == 2
