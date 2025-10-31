from __future__ import annotations

import asyncio
import csv
import functools
import logging
import random
from abc import ABC, abstractmethod
from datetime import timedelta
from io import StringIO
from typing import (
    Any,
    Callable,
    TypeVar,
)

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.dt import as_local, parse_datetime

from .const import (
    DOMAIN,
    HA_USER_AGENT,
    SITE_API_URL,
    MICRO_API_FILTER_PARAMS,
    MICRO_DATA_API_URL,
)
from .exceptions import (
    ApiAuthError,
    DataNotFoundError,
    RecordNotFoundError,
    RequestFailedError,
    RequestTimeoutError,
    UnexpectedStatusError,
)

_LOGGER = logging.getLogger(__name__)
F = TypeVar("F", bound=Callable[..., Any])


def retry_on_failure(max_retries: int = 5):
    """Retry decorator for coroutine functions."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_error = {"name": "Unknown"}

            for attempt in range(max_retries):
                try:
                    return await func(self, *args, **kwargs)
                except ApiAuthError:
                    raise
                except DataNotFoundError as e:
                    last_error = e
                    _LOGGER.warning(
                        "No valid data found in the %s API response. "
                        "Retrying... (%d/5)",
                        e["name"],
                        attempt + 1,
                    )
                except RecordNotFoundError as e:
                    last_error = e
                    _LOGGER.warning(
                        "No records found in the Site API response. "
                        "Retrying... (%d/5)",
                        attempt + 1,
                    )
                except UnexpectedStatusError as e:
                    last_error = e
                    _LOGGER.warning(
                        "%s API returned unexpected status code: %s. "
                        "Retrying... (%d/5)",
                        e["name"],
                        e["code"],
                        attempt + 1,
                    )
                except RequestTimeoutError as e:
                    last_error = e
                    _LOGGER.warning(
                        "%s API Request timed out: %s. Retrying... (%d/5)",
                        e["name"],
                        e["exception"],
                        attempt + 1,
                    )
                except RequestFailedError as e:
                    last_error = e
                    _LOGGER.warning(
                        "%s API Request failed: %s. Retrying... (%d/5)",
                        e["name"],
                        e["exception"],
                        attempt + 1,
                    )

                if attempt < (max_retries - 1):
                    await asyncio.sleep(random.uniform(5, 15))

            await self.hass.services.async_call(
                "notify",
                "persistent_notification",
                {
                    "message": (
                        f"Failed to fetch data after 5 attempts "
                        f"in the {last_error['name']} API."
                    ),
                    "title": "Taiwan Air Quality Monitor Error",
                },
            )
            return None
        return wrapper
    return decorator


class baseCoordinator(DataUpdateCoordinator, ABC):
    """Base class to manage fetching data from the API."""

    def __init__(self, hass, name, update_interval):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )
        self.hass = hass
        self.client = get_async_client(hass, False)

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            data = await self._get_data_with_retry()
            if data:
                return data
            else:
                raise UpdateFailed("No data received from API")
        except ApiAuthError:
            raise ConfigEntryAuthFailed("API key expired or invalid")
        except Exception as e:
            raise UpdateFailed(f"Unexpected error during data update: {e}") from e
    
    @retry_on_failure(max_retries=5)
    async def _get_data_with_retry(self, *args, **kwargs):
        """Fetch data from API with retry."""
        return await self._get_data(*args, **kwargs)
    
    @abstractmethod
    async def _get_data(self, *args, **kwargs):
        """Fetch the data from the API."""


class SiteCoordinator(baseCoordinator):
    """Class to manage fetching data from the Site API."""

    def __init__(self, hass, api_key, site_ids):
        """Initialize the Site coordinator."""
        super().__init__(
            hass,
            name=f"{DOMAIN}_site",
            update_interval=timedelta(minutes=11),
        )

        self.api_key = api_key
        self.siteids = site_ids

    async def _get_data(self):
        """Fetch the AQI data from the API."""

        params = {"language": "zh", "api_key": self.api_key, "format": "CSV"}
        headers = {
            "Accept": "text/csv",
            "User-Agent": HA_USER_AGENT,
        }

        err = {"name": "Site",}

        try:
            response = await self.client.get(
                SITE_API_URL, headers=headers, params=params, timeout=15
            )

            if response.is_success:
                records = await self.hass.async_add_executor_job(
                    self._parse_csv_response, response
                )

                if records:
                    aq_data = {
                        site_id: data
                        for data in records
                        if (site_id := str(data.get("siteid"))) in self.siteids
                    }
                    if aq_data:
                        _LOGGER.debug(
                            "Successfully fetched data for %d sites", len(aq_data)
                        )
                        return aq_data
                    else:
                        raise DataNotFoundError(err)
                else:
                    raise RecordNotFoundError(err)
            else:
                err["code"] = response.status_code
                raise UnexpectedStatusError(err)

        except DataNotFoundError as e:
            raise
        except RecordNotFoundError as e:
            raise
        except UnexpectedStatusError as e:
            raise
        except ApiAuthError:
            raise 
        except asyncio.TimeoutError as e:
            err["exception"] = str(e)
            raise RequestTimeoutError(err) from e
        except Exception as e:
            err["exception"] = str(e)
            raise RequestFailedError(err) from e

    def _parse_csv_response(self, response):
        """Parse CSV response content and return list of record dicts."""
        try:
            if hasattr(response, "text"):
                raw_text = response.text
            else:
                raw_data = response.read()
                # 嘗試不同的編碼方式
                for encoding in ["utf-8", "big5", "gb2312"]:
                    try:
                        raw_text = raw_data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # 如果所有編碼都失敗, 使用 utf-8 並替換錯誤字符
                    raw_text = raw_data.decode("utf-8", errors="replace")
                    _LOGGER.warning("Used fallback encoding with character replacement")

            _LOGGER.debug(
                "Raw CSV API Response length: %d characters", len(raw_text)
            )

            # 檢查是否為空響應
            if not raw_text.strip():
                _LOGGER.warning("Received empty CSV in Site API response")
                return None
            
            # 檢查是否包含錯誤訊息
            if any(keyword in raw_text.lower() for keyword in ["不存在", "過期", "失效", "無效", "expired", "invalid"]):
                _LOGGER.error("Detected possible auth issue in Site API response: %s", raw_text[:100])
                raise ApiAuthError

            csv_reader = csv.DictReader(StringIO(raw_text))
            records = list(csv_reader)

            _LOGGER.debug("Parsed %d records from CSV", len(records))

            return records

        except csv.Error as e:
            _LOGGER.error("CSV parsing error: %s", e)
            return None
        except ApiAuthError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error parsing CSV data: %s", e)
            return None


class MicroSensorCoordinator(baseCoordinator):
    """Class to manage fetching data from the Micro Sensor API."""

    def __init__(self, hass, station_ids):
        """Initialize the Micro Sensor coordinator."""
        super().__init__(
            hass,
            name=f"{DOMAIN}_micro_sensors",
            update_interval=timedelta(minutes=2),
        )

        self.station_ids = station_ids

    async def _get_data(self):
        """Fetch the micro sensor data from the API."""
        filter_params = " or ".join(
            MICRO_API_FILTER_PARAMS.format(stationID=stationID) 
            for stationID in self.station_ids
        )
        url = MICRO_DATA_API_URL.format(filter_params=filter_params)
        headers = {
            "Accept": "application/json",
            "User-Agent": HA_USER_AGENT,
        }

        err = {"name": f"Micro_Sensor",}

        try:
            response = await self.client.get(
                url,
                headers=headers,
                timeout=15
            )

            if response.is_success:
                res_data = response.json()

                parsed_data = self._parse_thing_data(res_data)
                if parsed_data:
                    _LOGGER.debug(
                        "Successfully fetched data for Micro Sensor %s",
                        self.station_ids,
                    )
                    return parsed_data
                else:
                    raise DataNotFoundError(err)
            else:
                err["code"] = response.status_code
                raise UnexpectedStatusError(err)

        except DataNotFoundError as e:
            raise
        except UnexpectedStatusError as e:
            raise
        except asyncio.TimeoutError as e:
            err["exception"] = str(e)
            raise RequestTimeoutError(err) from e
        except Exception as e:
            err["exception"] = str(e)
            raise RequestFailedError(err) from e

    def _parse_thing_data(self, res_data):
        """Parse Thing data and extract sensor values."""
        # 感測器名稱映射表
        sensor_mapping = {
            "pm2.5": ["pm2.5", "pm25", "PM2.5", "PM25"],
            "pm10": ["pm10", "PM10"],
            "pm1": ["pm1", "PM1"],
            "temperature": ["temperature", "Temperature"],
            "humidity": ["humidity", "Humidity"],
            "co": ["co", "CO"],
            "o3": ["o3", "O3"],
            "no2": ["no2", "NO2"],
            "voc": ["voc", "tvoc", "TVOC"],
        }

        try:
            if (
                res_data.get("@iot.count", 0) == 0 
                or not (value := res_data.get("value"))
            ):
                raise DataNotFoundError({"name": "Micro_Sensor"})
            
            result = {}
            for data in value:
                if (
                    not (properties := data.get("properties"))
                    or not (station_id := properties.get("stationID"))
                    or station_id not in self.station_ids
                ):
                    continue

                result[station_id] = {
                    "thing_id": data.get("@iot.id"),
                    "stationID": properties.get("stationID"),
                    "Description": properties.get("Description"),
                    "areaType": properties.get("areaType"),
                    "areaDescription": properties.get("areaDescription"),
                    "authority": properties.get("authority"),
                }
                
                coords = self._parse_coordinates(data.get("Locations"))
                result[station_id]["longitude"] = coords["lon"]
                result[station_id]["latitude"] = coords["lat"]

                # 解析 Datastreams
                if not (datastreams := data.get("Datastreams")):
                    continue

                for datastream in datastreams:
                    if not (observations := datastream.get("Observations")):
                        continue

                    name = datastream.get("name", "").lower()
                    latest_obs = observations[0]
                    value = latest_obs.get("result")
                    fresh_time = self._parse_datetime(
                        latest_obs.get("phenomenonTime")
                    )

                    # 根據映射表匹配感測器類型
                    for sensor_type, keywords in sensor_mapping.items():
                        if any(keyword in name for keyword in keywords):
                            # 排除特殊情況
                            if sensor_type == "temperature" and "main" in name:
                                continue
                            if sensor_type == "humidity" and "main" in name:
                                continue
                            if sensor_type == "co" and "voc" in name:
                                continue

                            result[station_id][sensor_type] = value
                            result[station_id][f"{sensor_type}_time"] = fresh_time
                            break

            return result
        except Exception as e:
            _LOGGER.error("Error parsing thing data: %s", e)
            return None

    def _parse_coordinates(self, locations):
        """Parse coordinates and determine latitude and longitude."""
        if (
            not locations 
            or not (coords := locations[0].get("location", {}).get("coordinates"))
            or len(coords) < 2
        ):
            return {"lat": "unknown", "lon": "unknown"}

        lat_range = (10.36, 26.40)  # 緯度範圍
        lon_range = (114.35, 122.11)  # 經度範圍

        a, b = coords[0], coords[1]

        if lat_range[0] <= a <= lat_range[1] and lon_range[0] <= b <= lon_range[1]:
            return {"lat": a, "lon": b}
        elif lat_range[0] <= b <= lat_range[1] and lon_range[0] <= a <= lon_range[1]:
            return {"lat": b, "lon": a}
        else:
            return {"lat": "unknown", "lon": "unknown"}

    def _parse_datetime(self, datetime_str):
        """Parse datetime string and return local datetime string."""
        if not datetime_str:
            return "unknown"

        try:
            utc_dt = parse_datetime(datetime_str)
            local_dt = as_local(utc_dt)
            return local_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            _LOGGER.error("Error parsing datetime: %s", e)
            return "unknown"

