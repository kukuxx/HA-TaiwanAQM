from __future__ import annotations

import re
import json
import logging
import asyncio
import random

from httpx import HTTPError, TimeoutException

from homeassistant.helpers.httpx_client import get_async_client
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
        self.client = get_async_client(hass, False)

    async def _async_update_data(self):
        """Fetch data from API."""
        api_key = self.hass.data[DOMAIN][self.entry.entry_id][API_KEY]
        siteid = self.hass.data[DOMAIN][self.entry.entry_id][SITEID]
        data = await self._get_data(api_key, siteid)
        if data:
            return data
        else:
            raise UpdateFailed

    async def _get_data(self, api_key, siteid):
        """Fetch the AQI data from the API."""

        params = {"language": "zh", "api_key": api_key, "format": "JSON"}
        headers = {
            "Accept": CONTENT_TYPE_JSON,
            "Content-Type": CONTENT_TYPE_JSON,
            "User-Agent": HA_USER_AGENT,
        }

        for attempt in range(5):
            try:
                response = await self.client.get(
                    API_URL,
                    headers=headers,
                    params=params,
                    timeout=15
                )
                
                if response.is_success:
                    records = await self.hass.async_add_executor_job(
                        self.verify_data, response
                    )

                    if records:
                        aq_data = {
                            str(data["siteid"]): data
                            for data in records
                            if str(data["siteid"]) in siteid
                        }
                        return aq_data

                    _LOGGER.warning(
                        f"No records found in the API response. Retrying... ({attempt + 1}/5)"
                    )
                else:
                    _LOGGER.warning(
                        f"API returned unexpected status code: {response.status_code}, Retrying... ({attempt + 1}/5)"
                    )

            except TimeoutException as e:
                _LOGGER.warning(
                    f"Request timed out: {e}. Retrying... ({attempt + 1}/5)"
                )
            except HTTPError as e:
                _LOGGER.warning(
                    f"HTTP client error: {e}. Retrying... ({attempt + 1}/5)"
                )
            except Exception as e:
                _LOGGER.error(
                    f"Get data error: {e}. Retrying... ({attempt + 1}/5)"
                )
            if attempt < 4:
                await asyncio.sleep(random.uniform(5, 15))
            else:
                await self.hass.services.async_call(
                    "notify", "persistent_notification", {
                        "message": "Failed to fetch data after 5 attempts.",
                        "title": "Taiwan Air Quality Monitor Error"
                    }
                )
                return None

    def verify_data(self, response):
        """Verify the data obtained"""

        raw_data = response.read()
        raw_text = raw_data.decode("utf-8", errors="ignore")
        _LOGGER.debug(f"Raw API Response: {raw_text}")
        try:
            # 嘗試解析完整 JSON
            return json.loads(raw_text).get("records", [])
        except json.JSONDecodeError:
            return self.extract_records(raw_text)

    def extract_records(self, data_string):
        """
        Extract only the records portion from a string

        parameter:
        data_string (str): the original string
        
        Return:
        list: records array contents
        """
        try:
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
