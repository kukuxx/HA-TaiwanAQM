from __future__ import annotations

import re
import json
import logging
import asyncio
import random

from aiohttp import ClientError
from aiohttp.hdrs import ACCEPT, CONTENT_TYPE, USER_AGENT

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONTENT_TYPE_JSON

from .const import DOMAIN, API_URL, API_KEY, SITEID, HA_USER_AGENT

_LOGGER = logging.getLogger(__name__)


class AQMCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, entry, interval):
        """Initialize the AQM coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=interval,
        )
        self.hass = hass
        self.entry = entry
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self):
        """Fetch data from API."""
        api_key = self.hass.data[DOMAIN][self.entry.entry_id].get(API_KEY, "")
        id = self.hass.data[DOMAIN][self.entry.entry_id].get(SITEID, [])
        data = await self._get_data(api_key, id)
        if data:
            return data
        else:
            _LOGGER.error(f"Coordinator data is empty")
            raise UpdateFailed

    async def _get_data(self, api_key, id):
        """Fetch the AQI data from the API."""

        params = {"language": "zh", "api_key": api_key, "format": "JSON"}
        headers = {
            ACCEPT: CONTENT_TYPE_JSON,
            CONTENT_TYPE: CONTENT_TYPE_JSON,
            USER_AGENT: HA_USER_AGENT,
        }

        for attempt in range(3):
            try:
                async with self.session.get(
                    API_URL,
                    headers=headers,
                    params=params,
                    ssl=False,
                    timeout=15
                ) as response:
                    if response.ok:
                        records = await self.verify_data(response)

                        if records:
                            aq_data = {
                                str(data["siteid"]): data
                                for data in records
                                if str(data["siteid"]) in id
                            }
                            return aq_data

                        _LOGGER.warning(
                            f"No records found in the API response. Retrying... ({attempt + 1}/3)"
                        )
                    else:
                        _LOGGER.warning(
                            f"API returned unexpected status code: {response.status}, Retrying... ({attempt + 1}/3)"
                        )

            except asyncio.TimeoutError:
                _LOGGER.warning(
                    f"Request timed out. Retrying... ({attempt + 1}/3)"
                )
            except ClientError as e:
                _LOGGER.warning(
                    f"HTTP client error: {e}. Retrying... ({attempt + 1}/3)"
                )
            except Exception as e:
                _LOGGER.error(
                    f"Get data error: {e}. Retrying... ({attempt + 1}/3)"
                )
            if attempt < 2:
                await asyncio.sleep(random.uniform(1, 3))
            else:
                await self.hass.services.async_call(
                    "notify", "persistent_notification", {
                        "message": "Failed to fetch data after 3 attempts.",
                        "title": "Taiwan Air Quality Monitor Error"
                    }
                )
                _LOGGER.error(f"Failed to fetch data after 3 attempts.")
                return None

    async def verify_data(self, response):
        """Verify the data obtained"""

        try:
            # 嘗試解析完整 JSON
            data = await response.json()
            _LOGGER.debug(f"reponse: {data}")
            if isinstance(data, dict) and "records" in data:
                return data["records"]
            return []
        except json.JSONDecodeError:
            r_data = await response.text()
            return await self.hass.async_add_executor_job(
                self.extract_records, r_data
            )

    def extract_records(self, data_string):
        """
        Extract only the records portion from a string

        parameter:
        data_string (str): the original string
        
        Return:
        list: records array contents
        """
        try:
            _LOGGER.debug(f"reponse: {data_string}")
            pattern = r'"records"\s*:\s*\[(.*?)\]'
            match = re.search(pattern, data_string, re.DOTALL)
            if match:
                records_content = '[' + match.group(1) + ']'
                return json.loads(records_content)

            else:
                _LOGGER.warning(
                    f"Parse failed, no match records found, reponse: {data_string}"
                )

        except (json.JSONDecodeError, AttributeError) as e:
            _LOGGER.warning(
                f"Failed to parse records: {e}, reponse: {data_string}"
            )

        return []
