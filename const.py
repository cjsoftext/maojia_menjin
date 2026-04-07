"""Constants for the Menjin integration."""

DOMAIN = "maojia_menjin"

# API Endpoints
API_BASE_URL = "https://znmenjin.shimaowy.com"
API_GET_ORG_LIST = f"{API_BASE_URL}/customer/app/house/getUcOrgList"
API_GET_EQUIP_LIST = f"{API_BASE_URL}/customer/api/customer/v1/acUserEquip/getEquiqList"
API_OPEN_DOOR = f"{API_BASE_URL}/customer/api/customer/v1/acUserEquip/openDoor"

# Config keys
CONF_TOKEN = "token"
CONF_PHONE = "phone"
CONF_DIVIDE_CODE = "divide_code"
CONF_DIVIDE_NAME = "divide_name"

# Data keys
DATA_COORDINATOR = "coordinator"

# Entity naming
ENTITY_PREFIX = "gate"

# Last response data key
DATA_LAST_RESPONSE = "last_response"
