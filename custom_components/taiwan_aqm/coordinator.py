from __future__ import annotations

import csv
import logging
import asyncio
import random

from io import StringIO

from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
        self.api_key = self.hass.data[DOMAIN][entry.entry_id][API_KEY]
        self.siteid = self.hass.data[DOMAIN][entry.entry_id][SITEID]
        self.client = get_async_client(hass, False)

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            data = await self._get_data()
            if data:
                return data
            else:
                raise UpdateFailed("No data received from API")
        except Exception as e:
            raise UpdateFailed(f"Unexpected error during data update: {e}")

    async def _get_data(self):
        """Fetch the AQI data from the API."""

        params = {"language": "zh", "api_key": self.api_key, "format": "CSV"}
        headers = {
            "Accept": "text/csv",
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
                        self._parse_csv_response, response
                    )

                    if records:
                        aq_data = {
                            site_id: data
                            for data in records
                            if (site_id := str(data.get("siteid"))) in self.siteid
                        }
                        if aq_data:
                            _LOGGER.debug(f"Successfully fetched data for {len(aq_data)} sites")
                            return aq_data
                        else:
                            _LOGGER.warning("No matching site data found in records")

                    _LOGGER.warning(
                        f"No records found in the API response. Retrying... ({attempt + 1}/5)"
                    )
                else:
                    _LOGGER.warning(
                        f"API returned unexpected status code: {response.status_code}, Retrying... ({attempt + 1}/5)"
                    )

            except asyncio.TimeoutError as e:
                _LOGGER.warning(
                    f"Request timed out: {e}. Retrying... ({attempt + 1}/5)"
                )
            except Exception as e:
                _LOGGER.warning(
                    f"Request failed: {e}. Retrying... ({attempt + 1}/5)"
                )
            
            if attempt < 4:
                await asyncio.sleep(random.uniform(5, 15))
        
        await self.hass.services.async_call(
            "notify", "persistent_notification", {
                "message": "Failed to fetch data after 5 attempts.",
                "title": "Taiwan Air Quality Monitor Error"
            }
        )
        return None

    def _parse_csv_response(self, response):
        """Parse CSV response content and return list of record dicts."""
        try:
            if hasattr(response, 'text'):
                raw_text = response.text
            else:
                raw_data = response.read()
                # 嘗試不同的編碼方式
                for encoding in ['utf-8', 'big5', 'gb2312']:
                    try:
                        raw_text = raw_data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # 如果所有編碼都失敗，使用 utf-8 並替換錯誤字符
                    raw_text = raw_data.decode("utf-8", errors="replace")
                    _LOGGER.warning("Used fallback encoding with character replacement")
            
            _LOGGER.debug(f"Raw CSV API Response length: {len(raw_text)} characters")
            
            # 檢查是否為空響應
            if not raw_text.strip():
                _LOGGER.warning("Received empty CSV response")
                return []
            
            csv_reader = csv.DictReader(StringIO(raw_text))
            records = list(csv_reader)
            
            _LOGGER.debug(f"Parsed {len(records)} records from CSV")
            
            return records
            
        except csv.Error as e:
            _LOGGER.error(f"CSV parsing error: {e}")
            return []
        except Exception as e:
            _LOGGER.error(f"Unexpected error parsing CSV data: {e}")
            return []
