# Muli Integration - Developer Documentation

Technical documentation for developers and contributors working on the Muli Home Assistant integration.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Code Structure](#code-structure)
- [API Documentation](#api-documentation)
- [Authentication System](#authentication-system)
- [Adding New Features](#adding-new-features)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Future Roadmap](#future-roadmap)

## Architecture Overview

### Dual Coordinator Pattern

The integration uses two separate `DataUpdateCoordinator` instances with different update intervals:

#### 1. MuliDataUpdateCoordinator

- **Update Interval**: 30 seconds
- **Endpoint**: `/api/socle-350/rest/v2/home`
- **Purpose**: Frequently changing data
- **Data Includes**:
  - Battery level and status
  - GPS location and speed
  - Security status (armed, alarm)
  - Assistance level
  - Movement alarm state

#### 2. MuliBikeDetailsCoordinator

- **Update Interval**: 30 minutes
- **Endpoint**: `/api/socle-350/rest/v1/bike`
- **Purpose**: Rarely changing data
- **Data Includes**:
  - Firmware version
  - Hardware version
  - GPS tracker battery level

### Runtime Data Structure

The integration uses a dataclass to store both coordinators:

```python
@dataclass
class MuliRuntimeData:
    """Runtime data for Muli integration."""
    data_coordinator: MuliDataUpdateCoordinator
    bike_details_coordinator: MuliBikeDetailsCoordinator

type MuliConfigEntry = ConfigEntry[MuliRuntimeData]
```

This allows platforms to access the appropriate coordinator for their data needs.

## Code Structure

### File Organization

```
custom_components/mulibikes/
├── __init__.py              # Entry point, coordinator setup
├── api.py                   # API client implementation
├── binary_sensor.py         # Alarm binary sensor
├── config_flow.py           # UI configuration flow
├── const.py                 # Constants and configuration
├── coordinator.py           # Data update coordinators
├── device_tracker.py        # GPS location tracking
├── entity.py                # Base entity class
├── manifest.json            # Integration metadata
├── select.py                # Alarm mode select
├── sensor.py                # 10 sensor entities
├── strings.json             # User-facing text
├── switch.py                # Armed switch
├── translations/            # Generated translations
│   └── en.json
├── README.md                # User documentation
└── DEVELOPERS.md            # This file
```

### Platform Implementations

#### Base Entity (`entity.py`)

All entities inherit from `MuliEntity`:

```python
class MuliEntity(CoordinatorEntity[MuliDataUpdateCoordinator]):
    """Base class for Muli entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MuliDataUpdateCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Muli Bike",
            manufacturer="Muli",
            model="Cargo bike",
        )
```

Key features:

- Uses `has_entity_name = True` for proper entity naming
- Provides consistent device info across all entities
- Inherits from `CoordinatorEntity` for automatic updates

#### Translation System

All entities use `_attr_translation_key` instead of hardcoded names:

```python
self._attr_translation_key = "battery"  # References strings.json
```

Translations are defined in `strings.json` and auto-generated to `translations/en.json`.

## API Documentation

### Base URL

```
https://vr-api.velco.bike
```

### Authentication

The API uses JWT bearer tokens with refresh token support.

#### Headers

```python
API_HEADERS = {
    "Accept": "application/json",
    "Accept-Charset": "UTF-8",
    "Accept-Encoding": "gzip",
    "Accept-Language": "en",
    "company": "MULI",
    "Connection": "Keep-Alive",
    "Content-Type": "application/json",
    "Host": "vr-api.velco.bike",
    "User-Agent": "Ktor client",
    "x-api-key": API_KEY,
}
```

### Endpoints

#### 1. Login

```
POST /api/auth/rest/v1/login
```

**Request:**

```json
{
  "email": "user@example.com",
  "password": "password",
  "application": "MULI",
  "successUrl": ""
}
```

**Response:**

```json
{
  "jwtToken": "access_token_here",
  "jwtRefreshToken": "refresh_token_here"
}
```

#### 2. Refresh Token

```
POST /api/auth/rest/v1/refresh
```

**Request:**

```json
{
  "refreshToken": "refresh_token_here"
}
```

**Response:**

```json
{
  "jwtToken": "new_access_token_here"
}
```

#### 3. Get Device Data

```
GET /api/socle-350/rest/v2/home
Authorization: Bearer {access_token}
```

**Response:** Contains `vehicleData`, `bikePositionData`, and `securityData` objects.

#### 4. Get Bike Details

```
GET /api/socle-350/rest/v1/bike
Authorization: Bearer {access_token}
```

**Response:** Contains `productFirmwareVersion`, `productHardwareVersion`, and `iotBatteryLevel`.

#### 5. Set Monitored (Arm/Disarm)

```
POST /api/socle-350/rest/v1/bike/monitored
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Body:** `true` or `false`

#### 6. Set Movement Alarm

```
PUT /api/socle-350/rest/v1/settings
Authorization: Bearer {access_token}
```

**Request:**

```json
{
  "display": null,
  "security": {
    "movementLockControl": null,
    "movementAlarm": true,
    "autoLock": null
  },
  "notifications": null
}
```

### Error Handling

The API client (`MuliClient`) raises two custom exceptions:

- **`MuliAuthenticationError`**: 401/403 responses, triggers reauthentication flow
- **`MuliConnectionError`**: Network errors, connection failures

The coordinators handle these exceptions:

- `MuliAuthenticationError` → Attempt token refresh → `ConfigEntryAuthFailed` if refresh fails
- `MuliConnectionError` → `UpdateFailed`

## Authentication System

### Token Management Flow

```
1. User enters credentials
   ↓
2. Login API call → Receive access_token + refresh_token
   ↓
3. Store both tokens in config_entry.data
   ↓
4. Use access_token for API calls
   ↓
5. On 401 error:
   - Try refresh_token
   - Update access_token in config_entry.data
   - Retry API call
   ↓
6. If refresh fails:
   - Raise ConfigEntryAuthFailed
   - Trigger reauth flow in UI
```

### Automatic Token Refresh

Both coordinators implement automatic token refresh:

```python
except MuliAuthenticationError as err:
    _LOGGER.debug("Access token expired, attempting refresh")
    try:
        refresh_token = self.config_entry.data[CONF_REFRESH_TOKEN]
        new_token_data = await self.client.refresh_access_token(refresh_token)

        self.client.access_token = new_token_data["access_token"]

        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data={**self.config_entry.data, CONF_ACCESS_TOKEN: new_token_data["access_token"]},
        )

        _LOGGER.info("Successfully refreshed access token")

        # Retry the API call with new token
        data = await self.client.get_device_data()
        return data

    except MuliAuthenticationError as refresh_err:
        raise ConfigEntryAuthFailed("Refresh token expired") from refresh_err
```

### Reauthentication Flow

Implemented in `config_flow.py`:

```python
async def async_step_reauth(self, entry_data):
    """Handle reauthentication."""
    return await self.async_step_reauth_confirm()

async def async_step_reauth_confirm(self, user_input=None):
    """Confirm reauthentication."""
    if user_input:
        # Validate new credentials
        # Get user ID from API
        # Verify same account
        # Update config entry with new tokens
```

## Adding New Features

### Adding a New Sensor

1. **Identify the data source**
   - Check if data is in `/home` endpoint (use `data_coordinator`)
   - Check if data is in `/bike` endpoint (use `bike_details_coordinator`)

2. **Create the sensor class in `sensor.py`**:

```python
class MuliNewSensor(MuliEntity, SensorEntity):
    """Representation of new sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE  # If applicable
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry: MuliConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry.entry_id)
        self._attr_unique_id = f"{entry.entry_id}_new_sensor"
        self._attr_translation_key = "new_sensor"

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        return self.coordinator.data.get("newField")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and "newField" in self.coordinator.data
```

3. **Add to entity list in `async_setup_entry`**:

```python
async_add_entities([
    # ... existing sensors ...
    MuliNewSensor(data_coordinator, entry),
])
```

4. **Add translation in `strings.json`**:

```json
{
  "entity": {
    "sensor": {
      "new_sensor": {
        "name": "New sensor"
      }
    }
  }
}
```

5. **Update translations manually** or regenerate `translations/en.json` from `strings.json`

### Adding a New API Endpoint

1. **Add endpoint constant to `const.py`**:

```python
API_NEW_ENDPOINT = "/api/socle-350/rest/v1/new-endpoint"
```

2. **Implement method in `api.py`**:

```python
async def new_api_method(self, parameter: str) -> dict[str, Any]:
    """Call new API endpoint."""
    if not self.access_token:
        raise MuliAuthenticationError("No access token available")

    url = f"{self.base_url}{API_NEW_ENDPOINT}"
    headers = {**API_HEADERS, "Authorization": f"Bearer {self.access_token}"}

    try:
        async with self.session.get(url, headers=headers) as response:
            if response.status == 401:
                raise MuliAuthenticationError("Access token expired")
            response.raise_for_status()
            return await response.json()
    except ClientResponseError as err:
        if err.status == 401:
            raise MuliAuthenticationError("Token expired") from err
        raise MuliConnectionError(f"HTTP error: {err.status}") from err
    except ClientError as err:
        raise MuliConnectionError(f"Connection error: {err}") from err
```

3. **Add coordinator method with token refresh**:

```python
async def async_new_action(self, parameter: str) -> None:
    """Perform new action with automatic token refresh."""
    try:
        await self.client.new_api_method(parameter)
    except MuliAuthenticationError:
        # Implement token refresh logic (see existing methods)
        pass
    except MuliConnectionError as err:
        raise UpdateFailed(f"Error: {err}") from err

    await self.async_request_refresh()
```

## Testing

### Test Environment Setup

This integration can be tested standalone without a full Home Assistant installation.

#### Prerequisites

1. **Install test dependencies:**

   ```bash
   pip install -r requirements_test.txt
   ```

2. **Required files:**
   - `requirements_test.txt` - Contains pytest and Home Assistant test framework
   - `pytest.ini` - Configures pytest for async tests
   - `tests/conftest.py` - Enables custom integration loading

#### Key Test Dependencies

- **pytest** - Test framework
- **pytest-homeassistant-custom-component** - Provides Home Assistant fixtures and mocks
- **pytest-cov** - Code coverage reporting
- **pytest-xdist** - Parallel test execution

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=custom_components.mulibikes --cov-report=term-missing

# Run tests in parallel (faster)
pytest tests/ --numprocesses=auto

# Run a specific test file
pytest tests/test_config_flow.py -v

# Run a specific test
pytest tests/test_config_flow.py::test_user_flow_success -v
```

### Test Configuration

The `pytest.ini` file configures automatic async test detection:

```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
testpaths = tests
```

The `conftest.py` file enables custom integration loading:

```python
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield
```

### Test Coverage Requirements

- Aim for 95%+ code coverage
- All config flow paths must be tested
- Mock all external API calls
- Use snapshot testing for entity states

Current coverage: **74%** (20 tests passing)

### Example Test Structure

```python
@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_ACCESS_TOKEN: "test_token",
            CONF_REFRESH_TOKEN: "refresh_token",
        },
        unique_id="test_user_id",
    )

@pytest.fixture
def mock_muli_client():
    """Return mocked Muli client."""
    with patch("custom_components.mulibikes.MuliClient") as mock:
        client = mock.return_value
        client.get_device_data.return_value = {...}
        yield client
```

### Writing New Tests

When adding new tests:

1. Import from `pytest_homeassistant_custom_component.common` (not `tests.common`)
2. Async test functions are automatically detected (no decorator needed)
3. Use the `hass` fixture for Home Assistant instance
4. Use `mock_config_entry` and `mock_muli_client` fixtures from conftest.py
5. Use snapshot testing with `syrupy` for entity state verification

## Code Quality

### Pre-commit Hooks

This project uses pre-commit hooks to automatically check and format code before commits. The hooks are based on the Home Assistant Core setup.

#### Setup

1. **Install dev dependencies:**

   ```bash
   pip install -r requirements_dev.txt
   ```

2. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

#### What the hooks do

The pre-commit hooks automatically:

- **ruff-check** - Lints code and auto-fixes issues
- **ruff-format** - Formats code according to style guidelines
- **codespell** - Checks for spelling errors
- **check-json** - Validates JSON files
- **end-of-file-fixer** - Ensures files end with a newline
- **trailing-whitespace** - Removes trailing whitespace
- **prettier** - Formats JSON, Markdown, and YAML files

#### Running manually

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

### Manual Validation Commands

```bash
# Linting with ruff
ruff check custom_components/mulibikes

# Format code with ruff
ruff format custom_components/mulibikes

# Type checking with mypy
mypy custom_components/mulibikes

# Spell checking
codespell custom_components/ tests/
```

## Contributing Guidelines

1. **Follow Home Assistant coding standards**
2. **Add tests** for all new features
3. **Update strings.json** when adding entities
4. **Run quality checks** before submitting
5. **Document API changes** in this file
6. **Update README.md** for user-facing changes
