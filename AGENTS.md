# AGENTS.md

This file provides guidance to AI coding assistants when working with this Home Assistant custom integration.

## Repository Overview

This is a custom Home Assistant integration for **Muli electric cargo bikes** (powered by Velco API). It provides real-time monitoring and control of bike status, location, and security features through Home Assistant.

**Key Features:**

- Real-time battery level and range monitoring
- GPS location tracking with device tracker
- Security system control (arm/disarm, movement alarm)
- Bike status sensors (speed, assistance level, mileage)
- Diagnostic sensors (firmware, hardware, GPS tracker battery)
- Automatic token refresh and reauthentication flow

**Platforms:** sensor (10), switch (2), binary_sensor (1), device_tracker (1)

## Development Commands

### Environment Setup

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Install development tools (includes pre-commit, ruff, mypy, codespell)
pip install -r requirements_dev.txt

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=custom_components.mulibikes --cov-report=term-missing

# Run tests in parallel (faster)
pytest tests/ --numprocesses=auto

# Run specific test file
pytest tests/test_config_flow.py -v

# Run specific test
pytest tests/test_config_flow.py::test_user_flow_success -v

# Update snapshots (use with caution)
pytest tests/ --snapshot-update
# Always run again without --snapshot-update to verify
```

### Code Quality

```bash
# Run all pre-commit hooks on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Linting with ruff
ruff check custom_components/mulibikes

# Auto-fix with ruff
ruff check --fix custom_components/mulibikes

# Format code with ruff
ruff format custom_components/mulibikes

# Type checking with mypy
mypy custom_components/mulibikes

# Spell checking
codespell custom_components/ tests/
```

## Architecture

### Dual Coordinator Pattern

This integration uses **two separate DataUpdateCoordinator instances** with different update intervals to optimize API usage:

**MuliDataUpdateCoordinator:**

- Update interval: **30 seconds** (`SCAN_INTERVAL`)
- Fetches frequently-changing data: vehicle data, position data, security data
- Methods: `async_set_monitored()`, `async_set_movement_alarm()` for user actions
- Includes automatic token refresh before retry on auth failures

**MuliBikeDetailsCoordinator:**

- Update interval: **30 minutes** (`BIKE_DETAILS_UPDATE_INTERVAL`)
- Fetches static/slowly-changing data: firmware version, hardware version, GPS battery
- Same token refresh mechanism as data coordinator

**Why dual coordinators?**

- Separates frequently-changing telemetry from rarely-changing metadata
- Prevents unnecessary API calls for static data
- Allows independent refresh schedules

### Token Refresh Mechanism

Both coordinators implement **identical automatic token refresh logic**:

1. Catch `MuliAuthenticationError` (401 response from API)
2. Attempt refresh using `refresh_token` from `config_entry.data`
3. Update `client.access_token` in-memory
4. Call `hass.config_entries.async_update_entry()` to persist new token
5. Retry the original operation with new token
6. If refresh fails, raise `ConfigEntryAuthFailed` → triggers reauth flow in UI

This pattern is implemented in:

- `_async_update_data()` - automatic data fetch
- `async_set_monitored()` - manual action
- `async_set_movement_alarm()` - manual action

**Token persistence strategy:** Refresh tokens never expire and are stored in `config_entry.data`. Access tokens are refreshed on-demand when they expire (401 response).

### Runtime Data Pattern

```python
@dataclass
class MuliRuntimeData:
    """Runtime data for Muli integration."""
    data_coordinator: MuliDataUpdateCoordinator
    bike_details_coordinator: MuliBikeDetailsCoordinator

type MuliConfigEntry = ConfigEntry[MuliRuntimeData]
```

This provides:

- Type safety across the codebase
- Clean access to coordinators: `entry.runtime_data.data_coordinator`
- IDE support and type checking

### Entity Organization

**Base entity class** (`entity.py`):

```python
class MuliEntity(CoordinatorEntity[MuliDataUpdateCoordinator]):
    _attr_has_entity_name = True  # Entity names from translation keys
```

All entities:

- Inherit from `MuliEntity`
- Use translation keys for naming (e.g., `_attr_translation_key = "battery"`)
- Unique IDs follow pattern: `f"{entry.entry_id}_{sensor_name}"`
- Custom `available` property checks for required data in coordinator.data dict
- Support extra state attributes (e.g., `last_update_time` for battery sensor)

**Data structure contract:** Entities know the exact path into coordinator.data dict. No data transformation layer - entities expect specific API response structure:

```python
vehicle_data = self.coordinator.data.get("vehicleData", {})
return vehicle_data.get("batteryLevel")
```

### API Client Structure

**Custom exceptions:**

- `MuliAuthenticationError` - 401/403 responses, triggers token refresh
- `MuliConnectionError` - Network errors, connection failures

**Auth flow:** JWT tokens (access + refresh)

**Error handling pattern:**

- Specific 401 status checks for auth errors
- Uses `raise ... from err` for exception chaining
- All methods raise either `MuliAuthenticationError` or `MuliConnectionError`

### Config Flow with Reauth

- **Initial setup:** `async_step_user()` collects email/password, calls `client.login()`
- **Reauth flow:** `async_step_reauth()` → `async_step_reauth_confirm()`
  - Triggered when `ConfigEntryAuthFailed` is raised in coordinators
  - Validates new credentials match the same account using unique_id
  - Updates config_entry with new tokens (not password)
- **Unique ID:** Set to user's email address to prevent duplicates

## Home Assistant Standards

### Python Requirements

- **Compatibility:** Python 3.12+
- **Language Features:** Use modern Python features:
  - Type hints on all functions
  - f-strings (preferred over `%` or `.format()`)
  - Dataclasses
  - Pattern matching where appropriate

### Async Programming

All external I/O operations must be async.

**Best practices:**

- Never use blocking calls (`time.sleep`, `requests.get`, file I/O)
- Use `asyncio.sleep()` instead of `time.sleep()`
- For blocking operations, use executor: `await hass.async_add_executor_job(blocking_func, args)`
- Avoid awaiting in loops - use `gather` instead
- Group executor jobs when possible

**Data Update Coordinator pattern:**

```python
class MyCoordinator(DataUpdateCoordinator[MyData]):
    def __init__(self, hass: HomeAssistant, client: MyClient, config_entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
            config_entry=config_entry,  # Pass config_entry - it's recommended
        )
        self.client = client

    async def _async_update_data(self):
        try:
            return await self.client.fetch_data()
        except ApiError as err:
            raise UpdateFailed(f"API communication error: {err}") from err
```

**Error types:**

- `UpdateFailed` - for API errors during updates
- `ConfigEntryAuthFailed` - for authentication issues (triggers reauth)
- `ConfigEntryNotReady` - device offline or temporary failure

### Entity Development

**Unique IDs (required):**

- Every entity must have a unique ID
- Must be unique per platform (not per integration)
- Don't include integration domain or platform in ID
- Acceptable sources: device serial numbers, MAC addresses, physical identifiers
- Last resort: `f"{entry.entry_id}_battery"`
- **Never use:** IP addresses, hostnames, device names, email addresses

**Entity naming:**

- Set `_attr_has_entity_name = True`
- Use `_attr_translation_key` for all entity names (e.g., `"battery"`)
- Create translations in `strings.json`:

```json
{
  "entity": {
    "sensor": {
      "battery": {
        "name": "Battery"
      }
    }
  }
}
```

**Availability:**

```python
@property
def available(self) -> bool:
    """Return if entity is available."""
    return super().available and self.identifier in self.coordinator.data
```

**State handling:**

- Unknown values: Use `None` (not "unknown" or "unavailable")
- Availability: Implement `available()` property instead of using "unavailable" state

### Error Handling

**Exception types (choose most specific):**

- `ServiceValidationError` - User input errors (preferred over `ValueError`)
- `HomeAssistantError` - Device communication failures
- `ConfigEntryNotReady` - Temporary setup issues (device offline)
- `ConfigEntryAuthFailed` - Authentication problems
- `ConfigEntryError` - Permanent setup issues

**Try/Catch best practices:**

- Only wrap code that can throw exceptions
- Keep try blocks minimal - process data after the try/catch
- **Avoid bare exceptions** except in specific cases:
  - ❌ Generally not allowed: `except:` or `except Exception:`
  - ✅ Allowed in config flows to ensure robustness
  - ✅ Allowed in functions/methods that run in background tasks

**Good pattern:**

```python
try:
    data = await device.get_data()  # Can throw
except DeviceError:
    _LOGGER.error("Failed to get data")
    return

# ✅ Process data outside try block
processed = data.get("value", 0) * 100
self._attr_native_value = processed
```

**Bad pattern:**

```python
try:
    data = await device.get_data()
    # ❌ Don't process data inside try block
    processed = data.get("value", 0) * 100
    self._attr_native_value = processed
except DeviceError:
    _LOGGER.error("Failed to get data")
```

### Logging

**Format guidelines:**

- No periods at end of messages
- No integration names/domains (added automatically)
- No sensitive data (keys, tokens, passwords)
- Use lazy logging: `_LOGGER.debug("Message with %s", variable)`

**Unavailability logging:**
Log once when device/service becomes unavailable (info level), and once when it recovers:

```python
_unavailable_logged: bool = False

if not self._unavailable_logged:
    _LOGGER.info("The sensor is unavailable: %s", ex)
    self._unavailable_logged = True

# On recovery:
if self._unavailable_logged:
    _LOGGER.info("The sensor is back online")
    self._unavailable_logged = False
```

## Testing Patterns

### Test Environment

This integration uses **pytest-homeassistant-custom-component** which provides:

- Mock Home Assistant core without full installation
- Test fixtures (`hass`, `MockConfigEntry`, etc.)
- Test harness to run integration tests standalone

**Key difference from HA Core:** Custom integrations don't use `tests.common` - they use `pytest_homeassistant_custom_component.common`.

### Test Configuration

**pytest.ini:**

```ini
[pytest]
asyncio_mode = auto  # Automatic async test detection
asyncio_default_fixture_loop_scope = function
testpaths = tests
```

**conftest.py must include:**

```python
from pytest_homeassistant_custom_component.common import MockConfigEntry

pytest_plugins = "pytest_homeassistant_custom_component"

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield
```

### Test Fixtures

**mock_config_entry:**

```python
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
```

**mock_muli_client:**

```python
@pytest.fixture
def mock_muli_client() -> Generator[MagicMock]:
    """Return a mocked Muli API client."""
    with (
        patch("custom_components.mulibikes.MuliClient", autospec=True) as mock_client_class,
        patch("custom_components.mulibikes.config_flow.MuliClient", new=mock_client_class),
    ):
        mock_client = mock_client_class.return_value
        mock_client.access_token = "test_access_token"
        mock_client.login = AsyncMock(return_value={"access_token": "...", "refresh_token": "..."})
        mock_client.get_device_data = AsyncMock(return_value={...})  # Realistic API response
        yield mock_client
```

**init_integration:**

```python
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
```

### Snapshot Testing

Use `syrupy` for verifying entity states:

```python
@pytest.mark.usefixtures("entity_registry_enabled_by_default", "init_integration")
async def test_sensors(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the sensor entities."""
    entity_entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert len(entity_entries) == 10  # Expected number of sensors

    for entity_entry in entity_entries:
        assert hass.states.get(entity_entry.entity_id) == snapshot(name=f"{entity_entry.entity_id}-state")
```

### Coverage Requirements

- **Target:** 95%+ code coverage
- **Config flow:** 100% coverage required - test all paths
- **Mock all external dependencies:** Never make real API calls in tests
- Run with: `pytest tests/ --cov=custom_components.mulibikes --cov-report=term-missing`

## Code Quality

### Ruff Configuration

This integration uses the **full Home Assistant Core ruff configuration** (100+ rules) from `pyproject.toml`:

- All Home Assistant linting rules enabled
- Google-style docstrings required (`convention = "google"`)
- Max complexity: 25
- Comprehensive rule set including: ASYNC, BLE, DTZ, PERF, PL, PT, RUF, SIM, SLF, SLOT, T20, TC, TID, TRY, UP

**Key ignored rules:**

- `E501` - line too long (handled by formatter)
- `PLR0911-PLR0915` - complexity rules (too strict)
- `TC001-TC003` - type-checking imports (conflicts with pytest.patch)
- Formatter conflicts: `W191`, `E111`, `E114`, `E117`, `D206`, `D300`, `Q`, `COM812`, `COM819`

### Pre-commit Hooks

Hooks automatically run before each commit:

1. **ruff-check** - Lints code and auto-fixes issues
2. **ruff-format** - Formats code according to style guidelines
3. **codespell** - Checks for spelling errors
4. **check-json** - Validates JSON files
5. **end-of-file-fixer** - Ensures files end with a newline
6. **trailing-whitespace** - Removes trailing whitespace
7. **prettier** - Formats JSON, Markdown, and YAML files

## Common Patterns & Anti-Patterns

### ✅ Good Patterns

```python
# Async operations
data = await hass.async_add_executor_job(requests.get, url)
await asyncio.sleep(5)

# Translatable entity names
_attr_translation_key = "temperature_sensor"

# Proper error handling
try:
    data = await self.api.get_data()
except ApiException as err:
    raise UpdateFailed(f"API error: {err}") from err

# Minimal try blocks
try:
    data = await device.get_data()
except DeviceError:
    _LOGGER.error("Failed")
    return

# Process outside try block
processed = data.get("value", 0) * 100
self._attr_native_value = processed

# Coordinator action methods trigger refresh
async def async_set_setting(self, value: bool) -> None:
    """Set setting with automatic token refresh."""
    try:
        await self.client.set_setting(value)
    except MuliAuthenticationError:
        # Token refresh logic here
        pass

    await self.async_request_refresh()  # Update all entities immediately
```

### ❌ Anti-Patterns

```python
# Blocking operations in event loop
data = requests.get(url)  # ❌ Blocks event loop
time.sleep(5)  # ❌ Blocks event loop

# Hardcoded strings in code
self._attr_name = "Temperature Sensor"  # ❌ Not translatable

# Missing error handling
data = await self.api.get_data()  # ❌ No exception handling

# Too much code in try block
try:
    response = await client.get_data()
    # ❌ Data processing should be outside try block
    temperature = response["temperature"] / 10
    self._attr_native_value = temperature
except ClientError:
    _LOGGER.error("Failed")

# Bare exceptions in regular code
try:
    value = await sensor.read_value()
except Exception:  # ❌ Too broad - catch specific exceptions
    _LOGGER.error("Failed")

# Accessing wrong import path
from tests.common import MockConfigEntry  # ❌ Wrong for custom integrations
# Should be:
from pytest_homeassistant_custom_component.common import MockConfigEntry  # ✅
```

## File Structure

```
custom_components/mulibikes/
├── __init__.py              # Entry point, runtime data setup
├── api.py                   # API client with custom exceptions
├── binary_sensor.py         # Alarm binary sensor
├── config_flow.py           # UI configuration + reauth flow
├── const.py                 # Constants (DOMAIN, intervals, etc.)
├── coordinator.py           # Dual coordinators (30s + 30min)
├── device_tracker.py        # GPS location tracking
├── entity.py                # Base entity class
├── manifest.json            # Integration metadata
├── sensor.py                # 10 sensor entities
├── strings.json             # User-facing text (config flow, entities)
├── switch.py                # Armed and movement alarm switches
└── translations/en.json     # Generated from strings.json

tests/
├── __init__.py
├── conftest.py              # Fixtures (mock_config_entry, mock_muli_client, init_integration)
├── snapshots/               # Snapshot test data
│   ├── test_binary_sensor.ambr
│   ├── test_device_tracker.ambr
│   ├── test_sensor.ambr
│   └── test_switch.ambr
├── test_binary_sensor.py
├── test_config_flow.py      # Config flow tests (user flow, reauth flow, errors)
├── test_device_tracker.py
├── test_init.py             # Setup/unload, coordinator refresh
├── test_sensor.py
└── test_switch.py
```

## Integration-Specific Notes

### Coordinator Action Methods

When coordinator methods succeed (e.g., `async_set_monitored()`), they call `await self.async_request_refresh()` to immediately update all entities with the new state.

### API Response Structure

The integration expects specific JSON structure from the Muli API:

```python
{
    "vehicleData": {"batteryLevel": 85, "totalMileage": 1234, ...},
    "bikePositionData": {"latitude": 52.52, "longitude": 13.40, ...},
    "securityData": {"monitored": True, "movementAlarm": False, ...}
}
```

Entities access data directly from coordinator.data with no transformation layer.

### Testing Custom Integration Loading

The key to testing custom integrations is the autouse fixture in conftest.py:

```python
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield
```

Without this, Home Assistant won't find the custom_components directory and tests will fail with "Integration not found".
