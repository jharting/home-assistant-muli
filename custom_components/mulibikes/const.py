"""Constants for the mulibikes integration."""

from datetime import timedelta

DOMAIN = "mulibikes"

# API Configuration
API_BASE_URL = "https://vr-api.velco.bike"
API_LOGIN_ENDPOINT = "/api/auth/rest/v1/login"
API_REFRESH_ENDPOINT = "/api/auth/rest/v1/refresh"
API_HOME_ENDPOINT = "/api/socle-350/rest/v2/home"
API_BIKE_ENDPOINT = "/api/socle-350/rest/v1/bike"
API_MONITORED_ENDPOINT = "/api/socle-350/rest/v1/bike/monitored"
API_SETTINGS_ENDPOINT = "/api/socle-350/rest/v1/settings"
API_KEY = "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJNVUxJIn0.wjHUUOvtuR4JO_LDu1qRGPjWBZqqjbT0EJ-sgf_g0kVUyvkM7ltXXx5ssQxPZ9O6GapMink5WOJ4XFTo1REi_A"

# Update intervals
SCAN_INTERVAL = timedelta(seconds=30)
BIKE_DETAILS_UPDATE_INTERVAL = timedelta(minutes=30)

# Application Configuration
APPLICATION_NAME = "MULI"

# HTTP Headers for API requests
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

# Config Entry Keys
CONF_REFRESH_TOKEN = "refresh_token"
