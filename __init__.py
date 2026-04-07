"""The Menjin integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MenjinApiClient
from .const import (
    CONF_DIVIDE_CODE,
    CONF_PHONE,
    DATA_COORDINATOR,
    DOMAIN,
)
from .coordinator import MenjinDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["button", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Menjin from a config entry."""
    token = entry.data[CONF_TOKEN]
    phone = entry.data[CONF_PHONE]
    divide_code = entry.data[CONF_DIVIDE_CODE]

    session = async_get_clientsession(hass)
    api_client = MenjinApiClient(token, phone, session)

    coordinator = MenjinDataUpdateCoordinator(hass, api_client, divide_code)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
