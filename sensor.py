"""Sensor platform for Menjin integration."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DIVIDE_NAME,
    DATA_COORDINATOR,
    DOMAIN,
)
from .coordinator import MenjinDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Menjin sensor from a config entry."""
    coordinator: MenjinDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        DATA_COORDINATOR
    ]

    divide_name = config_entry.data[CONF_DIVIDE_NAME]

    async_add_entities([MenjinLastResponseSensor(coordinator, divide_name)])


class MenjinLastResponseSensor(CoordinatorEntity, SensorEntity):
    """Representation of the last API response."""

    def __init__(
        self,
        coordinator: MenjinDataUpdateCoordinator,
        divide_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._divide_name = divide_name
        self._attr_unique_id = f"{DOMAIN}_last_response"
        self.entity_id = f"sensor.{DOMAIN}_last_response"
        self._attr_name = f"{divide_name} 最后响应"

        # Device info - attach to the same device as buttons
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.divide_code)},
            name=f"{divide_name} 门禁",
            manufacturer="Menjin",
            model="Cloud API",
        )

        # Initial state
        self._attr_native_value = "未初始化"
        self._attr_extra_state_attributes = {}

        # Register callback for API responses
        coordinator.api_client.set_response_callback(self._on_api_response)

    @callback
    def _on_api_response(self, response: dict[str, Any]) -> None:
        """Handle API response callback."""
        device_name = response.get("device_name") or "系统"
        success = response.get("success", False)
        
        # State format: "设备名: 成功/失败"
        self._attr_native_value = f"{device_name}: {'成功' if success else '失败'}"
        
        # Store all response data in attributes
        self._attr_extra_state_attributes = {
            "device_name": device_name,
            "action": response.get("action"),
            "timestamp": response.get("timestamp"),
            "success": success,
            "status_code": response.get("status_code"),
            "response_code": response.get("response_code"),
            "message": response.get("message"),
        }
        
        self.async_write_ha_state()

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        return self._attr_native_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the extra state attributes."""
        return self._attr_extra_state_attributes
