"""Data coordinator for Menjin integration."""

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MenjinApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MenjinDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for Menjin."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: MenjinApiClient,
        divide_code: str,
    ) -> None:
        """Initialize the coordinator."""
        self.api_client = api_client
        self.divide_code = divide_code
        self._last_response: dict[str, Any] | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),  # 每小时自动刷新
        )

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch data from API."""
        devices = await self.api_client.get_equip_list(self.divide_code)
        if not devices:
            raise UpdateFailed("Failed to fetch device list")
        return devices

    async def async_refresh_devices(self) -> tuple[int, int]:
        """Manually refresh device list.

        Returns: (added_count, removed_count)
        """
        await self.async_request_refresh()
        # The actual entity management is handled by the button platform
        # based on the coordinator data
        return 0, 0

    def set_last_response(self, response: dict[str, Any]) -> None:
        """Store the last API response."""
        self._last_response = response
        _LOGGER.debug("Last response updated: %s", response)

    @property
    def last_response(self) -> dict[str, Any] | None:
        """Get the last API response."""
        return self._last_response
