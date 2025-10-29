"""Common fixtures for the mulibikes tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_ACCESS_TOKEN, CONF_EMAIL
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mulibikes.const import CONF_REFRESH_TOKEN, DOMAIN

# Automatically enable custom integration loading
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    return


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Muli (test@example.com)",
        data={
            CONF_EMAIL: "test@example.com",
            CONF_ACCESS_TOKEN: "test_access_token",
            CONF_REFRESH_TOKEN: "test_refresh_token",
        },
        unique_id="test@example.com",
    )


@pytest.fixture
def mock_muli_client() -> Generator[MagicMock]:
    """Return a mocked Muli API client."""
    with (
        patch(
            "custom_components.mulibikes.MuliClient",
            autospec=True,
        ) as mock_client_class,
        patch(
            "custom_components.mulibikes.config_flow.MuliClient",
            new=mock_client_class,
        ),
    ):
        mock_client = mock_client_class.return_value
        mock_client.access_token = "test_access_token"

        # Mock login method
        mock_client.login = AsyncMock(
            return_value={
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
            }
        )

        # Mock refresh_access_token method
        mock_client.refresh_access_token = AsyncMock(
            return_value={
                "access_token": "new_access_token",
                "refresh_token": "test_refresh_token",
            }
        )

        # Mock get_device_data method with realistic data
        mock_client.get_device_data = AsyncMock(
            return_value={
                "vehicleData": {
                    "batteryLevel": 85,
                    "totalMileage": 1234,
                    "remainDistance": 45,
                    "assistanceLevel": 3,
                    "lastUpdateDateTime": "2024-01-15T10:30:00Z",
                    "batteryHealth": {
                        "batteryCycles": 42,
                    },
                },
                "bikePositionData": {
                    "latitude": 52.5200,
                    "longitude": 13.4050,
                    "speed": 15,
                    "productStatus": "RUNNING",
                    "gpsSignalLost": False,
                    "lastDatePosition": "2024-01-15T10:29:00Z",
                    "dateLastSignal": "2024-01-15T10:30:00Z",
                },
                "securityData": {
                    "monitored": True,
                    "movementAlarm": False,
                    "alarm": False,
                },
            }
        )

        # Mock get_bike_details method
        mock_client.get_bike_details = AsyncMock(
            return_value={
                "productFirmwareVersion": "1.2.3",
                "productHardwareVersion": "HW-2.0",
                "iotBatteryLevel": 95,
            }
        )

        # Mock control methods
        mock_client.set_monitored = AsyncMock()
        mock_client.set_movement_alarm = AsyncMock()

        yield mock_client


@pytest.fixture
def platforms() -> list[str]:
    """Fixture to specify platforms to test."""
    return []


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_muli_client: MagicMock,
    platforms: list[str],
) -> MockConfigEntry:
    """Set up the Muli integration for testing."""
    mock_config_entry.add_to_hass(hass)

    with patch("custom_components.mulibikes._PLATFORMS", platforms):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    return mock_config_entry
