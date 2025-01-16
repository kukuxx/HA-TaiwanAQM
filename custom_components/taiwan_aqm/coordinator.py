import logging
import asyncio

from aiohttp import ClientError

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, API_URL, CONF_API_KEY, CONF_SITEID

_LOGGER = logging.getLogger(__name__)


class AQMCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, entry, interval):
        """Initialize the AQM coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=interval,  # 定義自動更新的間隔時間
        )
        self.hass = hass
        self.entry = entry
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self):
        """Fetch data from API."""
        api_key = self.entry.data[CONF_API_KEY]
        id = self.entry.data[CONF_SITEID]
        data = await self._get_data(api_key, id)
        if data:
            return data
        else:
            raise UpdateFailed

    async def _get_data(self, api_key, id):
        """Fetch the AQI data from the API."""

        params = {"language": "zh", "api_key": api_key}

        for attempt in range(3):
            try:
                async with self.session.get(
                    API_URL, params=params, ssl=False, timeout=20
                ) as response:
                    if response.ok:
                        try:
                            data = await response.json()
                            records = data.get("records", [])
                            if records:
                                aq_data = {
                                    str(data["siteid"]): data
                                    for data in records if str(data["siteid"]) in id
                                }
                                return aq_data
                            else:
                                _LOGGER.error("No records found in the API response.")
                                return None
                        except Exception as e:
                            msg = await response.text()
                            _LOGGER.error(f"Failed to parse JSON response: {e}")
                            await self.hass.services.async_call(
                                "notify", "persistent_notification", {
                                    "message": f"{msg}",
                                    "title": f"Taiwan Air Quality Monitor Error"
                                }
                            )
                            return None
                    else:
                        _LOGGER.error(
                            f"API returned unexpected status code: {response.status}"
                        )
                        return None

            except asyncio.TimeoutError:
                _LOGGER.warning(f"Request timed out. Retrying... ({attempt + 1}/3)")
            except ClientError as e:
                _LOGGER.warning(f"HTTP client error: {e}. Retrying... ({attempt + 1}/3)")
            except Exception as e:
                _LOGGER.error(f"Unexpected error occurred: {e}")
                return None
            if attempt < 2:
                await asyncio.sleep(3)
        _LOGGER.error(f"Failed to fetch data after 3 attempts.")
        return None
