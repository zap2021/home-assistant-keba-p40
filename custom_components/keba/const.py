"""Constants for the KEBA integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL

DOMAIN = "keba"
DEFAULT_NAME = "KEBA Wallbox"
DEFAULT_HOST = "192.168.0.10"
DEFAULT_PORT = 8443
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)
DEFAULT_USERNAME = "admin"
DEFAULT_VERIFY_SSL = False

CONF_SCAN_INTERVAL = "scan_interval"
CONF_SERIAL_NUMBER = "serial_number"

ATTR_FIRMWARE = "firmware"
ATTR_SERIAL = "serial"
ATTR_API_VERSION = "api_version"

SUPPORTED_PLATFORMS = ("sensor", "binary_sensor", "switch")

API_TIMEOUT = 10
LOGIN_PATH = "/v2/jwt/login"
REFRESH_PATH = "/v2/jwt/refresh"
VERSION_PATH = "/version"
SERIAL_NUMBER_PATH = "/serialnumber"
WALLBOXES_PATH = "/v2/wallboxes"

CONFIG_ENTRY_DEFAULTS = {
    CONF_USERNAME: DEFAULT_USERNAME,
    CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL.seconds,
}
