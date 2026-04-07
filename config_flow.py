"""Config flow for Menjin integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_TOKEN
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MenjinApiClient
from .const import CONF_DIVIDE_CODE, CONF_DIVIDE_NAME, CONF_PHONE, DATA_COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOKEN): str,
        vol.Required(CONF_PHONE): str,
    }
)


class MenjinConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Menjin."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._token: str | None = None
        self._phone: str | None = None
        self._org_list: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._token = user_input[CONF_TOKEN]
            self._phone = user_input[CONF_PHONE]

            # Validate token by fetching org list
            session = async_get_clientsession(self.hass)
            api_client = MenjinApiClient(self._token, self._phone, session)

            self._org_list = await api_client.get_org_list()

            if not self._org_list:
                errors["base"] = "cannot_connect"
            else:
                # If only one org, skip to creating entry
                if len(self._org_list) == 1:
                    return await self._create_entry(self._org_list[0])
                # Otherwise, show org selection step
                return await self.async_step_select_org()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_select_org(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle org selection step."""
        if user_input is not None:
            divide_code = user_input[CONF_DIVIDE_CODE]
            selected_org = next(
                (org for org in self._org_list if org["divideCode"] == divide_code),
                None,
            )
            if selected_org:
                return await self._create_entry(selected_org)

        # Build org selection schema
        org_options = {
            org["divideCode"]: org["divideName"] for org in self._org_list
        }

        data_schema = vol.Schema(
            {
                vol.Required(CONF_DIVIDE_CODE): vol.In(org_options),
            }
        )

        return self.async_show_form(
            step_id="select_org",
            data_schema=data_schema,
        )

    async def _create_entry(self, org: dict[str, Any]) -> FlowResult:
        """Create the config entry."""
        divide_code = org["divideCode"]
        divide_name = org["divideName"]

        # Check if already configured
        await self.async_set_unique_id(divide_code)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=divide_name,
            data={
                CONF_TOKEN: self._token,
                CONF_PHONE: self._phone,
                CONF_DIVIDE_CODE: divide_code,
                CONF_DIVIDE_NAME: divide_name,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return MenjinOptionsFlow(config_entry)


class MenjinOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Menjin."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__(config_entry)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            if user_input.get("refresh_devices"):
                # Trigger device refresh
                entry_data = self.hass.data[DOMAIN].get(self.config_entry.entry_id)
                if entry_data:
                    coordinator = entry_data.get(DATA_COORDINATOR)
                    if coordinator:
                        await coordinator.async_refresh_devices()
                        return self.async_show_form(
                            step_id="init",
                            data_schema=self._get_schema(),
                            description_placeholders={
                                "message": "设备列表已刷新"
                            },
                        )

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_schema(),
        )

    def _get_schema(self) -> vol.Schema:
        """Get the options schema."""
        return vol.Schema(
            {
                vol.Optional("refresh_devices", default=False): bool,
            }
        )
