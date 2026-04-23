import hashlib
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

def _sha256(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest().lower()

async def async_get_token(session: aiohttp.ClientSession, username, password, app_id, app_secret, base_url):
    url = f"{base_url}/account/token?appId={app_id}"
    payload = {
        "appSecret": app_secret,
        "username": username,
        "password": _sha256(password),
    }
    _LOGGER.debug("Requesting token for user %s at %s", username, url)
    async with session.post(url, json=payload, timeout=10) as resp:
        if resp.status != 200:
            text = await resp.text()
            _LOGGER.error("HTTP error %s from Deye API: %s", resp.status, text)
            resp.raise_for_status()
            
        j = await resp.json()
        if not j.get("success"):
            error_msg = j.get("msg", "Unknown error")
            _LOGGER.error("Deye API authentication failed: %s (Payload: %s)", error_msg, {k: v for k, v in payload.items() if k != "password"})
            raise Exception(f"Token request failed: {error_msg}")
            
        _LOGGER.debug("Token request successful")
        return j["accessToken"]

async def async_control_solar_sell(session: aiohttp.ClientSession, token, base_url, device_sn, is_enable):
    """Send Solar Sell control command."""
    url = f"{base_url}/order/sys/solarSell/control"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    action = "on" if is_enable else "off"
    
    payload = {
        "action": action,
        "deviceSn": device_sn
    }
    
    async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
        resp.raise_for_status()
        return await resp.json()