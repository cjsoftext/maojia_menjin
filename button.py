"""Button platform for Menjin integration."""

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity


from .const import (
    CONF_DIVIDE_NAME,
    DATA_COORDINATOR,
    DOMAIN,
    ENTITY_PREFIX,
)
from .coordinator import MenjinDataUpdateCoordinator
from .util import generate_entity_id

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Menjin button from a config entry."""
    coordinator: MenjinDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        DATA_COORDINATOR
    ]

    divide_name = config_entry.data[CONF_DIVIDE_NAME]

    # Create button entities from coordinator data
    entities = []
    for device in coordinator.data:
        entities.append(
            MenjinButton(
                coordinator,
                device,
                divide_name,
            )
        )

    async_add_entities(entities)


class MenjinButton(CoordinatorEntity, ButtonEntity):
    """Representation of a Menjin button."""

    def __init__(
        self,
        coordinator: MenjinDataUpdateCoordinator,
        device: dict[str, Any],
        divide_name: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._device = device
        self._divide_name = divide_name
        self._attr_unique_id = f"{DOMAIN}_{device['id']}"

        # Entity ID: button.gate_{divide_initials}_{device_pinyin}
        device_name = device.get("equipName", "Unknown")
        entity_id_suffix = generate_entity_id(device_name, divide_name)
        self.entity_id = f"button.{entity_id_suffix}"
        self._attr_name = f"{divide_name} {device_name}"

        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device["id"])},
            name=device_name,
            manufacturer="Menjin",
            model=device.get("equipTypeCode", "Unknown"),
        )

        # Extra state attributes
        self._attr_extra_state_attributes = {
            "device_id": device["id"],
            "device_type": device.get("equipTypeCode"),
            "position_type": device.get("positionTypeCode"),
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        device_id = self._device["id"]
        device_name = self._device.get("equipName", "Unknown")
        _LOGGER.debug("Opening door: %s (%s)", device_id, device_name)

        result = await self.coordinator.api_client.open_door(device_id, device_name)

        if result["success"]:
            _LOGGER.info("Door opened successfully: %s", result["msg"])
        else:
            _LOGGER.error("Failed to open door: %s", result["msg"])
