"""API client for Menjin integration."""

import logging
from datetime import datetime
from typing import Any, Callable

import aiohttp

from .const import API_GET_EQUIP_LIST, API_GET_ORG_LIST, API_OPEN_DOOR

_LOGGER = logging.getLogger(__name__)


class MenjinApiClient:
    """API client for Menjin."""

    def __init__(self, token: str, phone: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._token = token
        self._phone = phone
        self._session = session
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._response_callback: Callable[[dict[str, Any]], None] | None = None

    def set_response_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Set a callback to be called after each API response."""
        self._response_callback = callback

    def _notify_response(self, response: dict[str, Any]) -> None:
        """Notify the callback with the response data."""
        if self._response_callback:
            self._response_callback(response)

    async def get_org_list(self) -> list[dict[str, Any]]:
        """Get list of organizations/communities."""
        try:
            async with self._session.get(
                API_GET_ORG_LIST, headers=self._headers
            ) as response:
                status_code = response.status
                data = await response.json()
                _LOGGER.debug("get_org_list response type: %s, data: %s", type(data), data)
                
                # Record the response
                self._notify_response({
                    "action": "get_org_list",
                    "device_name": None,
                    "timestamp": datetime.now().isoformat(),
                    "success": response.status == 200 and (isinstance(data, list) or data.get("code") in (200, 0)),
                    "status_code": status_code,
                    "response_code": data.get("code") if isinstance(data, dict) else None,
                    "message": data.get("msg", "Success") if isinstance(data, dict) else "Success",
                })
                
                if status_code != 200:
                    _LOGGER.error("Failed to get org list: %s", status_code)
                    return []
                if isinstance(data, list):
                    return data
                if not isinstance(data, dict):
                    _LOGGER.error("Unexpected response type: %s", type(data))
                    return []
                if data.get("code") not in (200, 0):
                    _LOGGER.error("API error: %s", data)
                    return []
                return data.get("data", [])
        except Exception as err:
            _LOGGER.error("Error getting org list: %s", err)
            self._notify_response({
                "action": "get_org_list",
                "device_name": None,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "status_code": None,
                "response_code": None,
                "message": str(err),
            })
            return []

    async def get_equip_list(self, divide_code: str) -> list[dict[str, Any]]:
        """Get list of equipment for a community."""
        try:
            payload = {
                "phone": self._phone,
                "divideCode": divide_code,
            }
            async with self._session.post(
                API_GET_EQUIP_LIST, headers=self._headers, json=payload
            ) as response:
                status_code = response.status
                data = await response.json()
                
                # Record the response
                self._notify_response({
                    "action": "get_equip_list",
                    "device_name": None,
                    "timestamp": datetime.now().isoformat(),
                    "success": response.status == 200 and data.get("code") in (200, 0),
                    "status_code": status_code,
                    "response_code": data.get("code"),
                    "message": data.get("msg", "Success"),
                })
                
                if status_code != 200:
                    _LOGGER.error("Failed to get equip list: %s", status_code)
                    return []
                if data.get("code") not in (200, 0):
                    _LOGGER.error("API error: %s", data)
                    return []
                return data.get("data", [])
        except Exception as err:
            _LOGGER.error("Error getting equip list: %s", err)
            self._notify_response({
                "action": "get_equip_list",
                "device_name": None,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "status_code": None,
                "response_code": None,
                "message": str(err),
            })
            return []

    async def open_door(self, equip_id: str, device_name: str | None = None) -> dict[str, Any]:
        """Open a door."""
        try:
            payload = {
                "equipId": equip_id,
                "phoneNo": self._phone,
            }
            async with self._session.post(
                API_OPEN_DOOR, headers=self._headers, json=payload
            ) as response:
                status_code = response.status
                data = await response.json()
                success = data.get("code") in (200, 0)
                
                # Record the response
                self._notify_response({
                    "action": "open_door",
                    "device_name": device_name,
                    "timestamp": datetime.now().isoformat(),
                    "success": success and status_code == 200,
                    "status_code": status_code,
                    "response_code": data.get("code"),
                    "message": data.get("msg", "Unknown"),
                })
                
                if status_code != 200:
                    _LOGGER.error("Failed to open door: %s", status_code)
                    return {"success": False, "msg": f"HTTP {status_code}"}
                return {
                    "success": success,
                    "msg": data.get("msg", "Unknown"),
                }
        except Exception as err:
            _LOGGER.error("Error opening door: %s", err)
            self._notify_response({
                "action": "open_door",
                "device_name": device_name,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "status_code": None,
                "response_code": None,
                "message": str(err),
            })
            return {"success": False, "msg": str(err)}
