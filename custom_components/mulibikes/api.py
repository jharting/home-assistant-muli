"""API client for Muli integration."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession
from homeassistant.exceptions import HomeAssistantError

from .const import (
    API_BASE_URL,
    API_BIKE_ENDPOINT,
    API_HEADERS,
    API_HOME_ENDPOINT,
    API_LOGIN_ENDPOINT,
    API_MONITORED_ENDPOINT,
    API_REFRESH_ENDPOINT,
    API_SETTINGS_ENDPOINT,
    APPLICATION_NAME,
)

_LOGGER = logging.getLogger(__name__)


class MuliAuthenticationError(HomeAssistantError):
    """Exception raised for authentication errors."""


class MuliConnectionError(HomeAssistantError):
    """Exception raised for connection errors."""


class MuliClient:
    """Client for Muli API."""

    def __init__(self, session: ClientSession, access_token: str | None = None) -> None:
        """Initialize the client."""
        self.session = session
        self.access_token = access_token
        self.base_url = API_BASE_URL

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Login and get tokens.

        Args:
            email: The email address for authentication
            password: The password for authentication

        Returns:
            Dictionary containing access_token and refresh_token

        Raises:
            MuliAuthenticationError: If credentials are invalid
            MuliConnectionError: If connection fails
        """
        url = f"{self.base_url}{API_LOGIN_ENDPOINT}"
        payload = {
            "email": email,
            "password": password,
            "application": APPLICATION_NAME,
            "successUrl": "",
        }

        try:
            async with self.session.post(
                url, json=payload, headers=API_HEADERS
            ) as response:
                if response.status in (401, 403):
                    raise MuliAuthenticationError("Invalid credentials")
                response.raise_for_status()
                data = await response.json()

                return {
                    "access_token": data["jwtToken"],
                    "refresh_token": data["jwtRefreshToken"],
                }
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise MuliAuthenticationError("Invalid credentials") from err
            raise MuliConnectionError(f"HTTP error: {err.status}") from err
        except ClientError as err:
            raise MuliConnectionError(f"Connection error: {err}") from err

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh access token using refresh token.

        Args:
            refresh_token: The refresh token

        Returns:
            Dictionary containing new access_token

        Raises:
            MuliAuthenticationError: If refresh token is invalid
            MuliConnectionError: If connection fails
        """
        url = f"{self.base_url}{API_REFRESH_ENDPOINT}"
        payload = {"refreshToken": refresh_token}

        try:
            async with self.session.post(
                url, json=payload, headers=API_HEADERS
            ) as response:
                if response.status in (401, 403):
                    raise MuliAuthenticationError("Refresh token expired or invalid")
                response.raise_for_status()
                data = await response.json()

                return {
                    "access_token": data["jwtToken"],
                }
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise MuliAuthenticationError("Refresh token expired") from err
            raise MuliConnectionError(f"HTTP error: {err.status}") from err
        except ClientError as err:
            raise MuliConnectionError(f"Connection error: {err}") from err

    async def get_device_data(self) -> dict[str, Any]:
        """Get device data using access token.

        Returns:
            Dictionary containing device data

        Raises:
            MuliAuthenticationError: If access token is invalid (401)
            MuliConnectionError: If connection fails
        """
        if not self.access_token:
            raise MuliAuthenticationError("No access token available")

        url = f"{self.base_url}{API_HOME_ENDPOINT}"
        headers = {**API_HEADERS, "Authorization": f"Bearer {self.access_token}"}

        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 401:
                    raise MuliAuthenticationError("Access token expired or invalid")
                response.raise_for_status()
                return await response.json()
        except ClientResponseError as err:
            if err.status == 401:
                raise MuliAuthenticationError(
                    "Access token expired or invalid"
                ) from err
            raise MuliConnectionError(f"HTTP error: {err.status}") from err
        except ClientError as err:
            raise MuliConnectionError(f"Connection error: {err}") from err

    async def get_bike_details(self) -> dict[str, Any]:
        """Get bike details using access token.

        Returns:
            Dictionary containing bike details (firmware, hardware, etc.)

        Raises:
            MuliAuthenticationError: If access token is invalid (401)
            MuliConnectionError: If connection fails
        """
        if not self.access_token:
            raise MuliAuthenticationError("No access token available")

        url = f"{self.base_url}{API_BIKE_ENDPOINT}"
        headers = {**API_HEADERS, "Authorization": f"Bearer {self.access_token}"}

        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 401:
                    raise MuliAuthenticationError("Access token expired or invalid")
                response.raise_for_status()
                return await response.json()
        except ClientResponseError as err:
            if err.status == 401:
                raise MuliAuthenticationError(
                    "Access token expired or invalid"
                ) from err
            raise MuliConnectionError(f"HTTP error: {err.status}") from err
        except ClientError as err:
            raise MuliConnectionError(f"Connection error: {err}") from err

    async def set_monitored(self, monitored: bool) -> None:
        """Set monitored state (alarm armed/disarmed).

        Args:
            monitored: True to arm alarm, False to disarm

        Raises:
            MuliAuthenticationError: If access token is invalid (401)
            MuliConnectionError: If connection fails
        """
        if not self.access_token:
            raise MuliAuthenticationError("No access token available")

        url = f"{self.base_url}{API_MONITORED_ENDPOINT}"
        headers = {**API_HEADERS, "Authorization": f"Bearer {self.access_token}"}

        try:
            async with self.session.post(
                url, json=monitored, headers=headers
            ) as response:
                if response.status == 401:
                    raise MuliAuthenticationError("Access token expired or invalid")
                response.raise_for_status()
        except ClientResponseError as err:
            if err.status == 401:
                raise MuliAuthenticationError(
                    "Access token expired or invalid"
                ) from err
            raise MuliConnectionError(f"HTTP error: {err.status}") from err
        except ClientError as err:
            raise MuliConnectionError(f"Connection error: {err}") from err

    async def set_movement_alarm(self, enabled: bool) -> None:
        """Set movement alarm state.

        Args:
            enabled: True to enable movement alarm, False to disable

        Raises:
            MuliAuthenticationError: If access token is invalid (401)
            MuliConnectionError: If connection fails
        """
        if not self.access_token:
            raise MuliAuthenticationError("No access token available")

        url = f"{self.base_url}{API_SETTINGS_ENDPOINT}"
        headers = {**API_HEADERS, "Authorization": f"Bearer {self.access_token}"}
        payload = {
            "display": None,
            "security": {
                "movementLockControl": None,
                "movementAlarm": enabled,
                "autoLock": None,
            },
            "notifications": None,
        }

        try:
            async with self.session.put(url, json=payload, headers=headers) as response:
                if response.status == 401:
                    raise MuliAuthenticationError("Access token expired or invalid")
                response.raise_for_status()
        except ClientResponseError as err:
            if err.status == 401:
                raise MuliAuthenticationError(
                    "Access token expired or invalid"
                ) from err
            raise MuliConnectionError(f"HTTP error: {err.status}") from err
        except ClientError as err:
            raise MuliConnectionError(f"Connection error: {err}") from err
