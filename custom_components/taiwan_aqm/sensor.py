from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SITENAME_DICT,
    SENSOR_INFO,
    SITEID,
    COORDINATOR,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Taiwan AQM sensors from a config entry."""
    try:
        siteid = hass.data[DOMAIN][entry.entry_id].get(SITEID, [])
        coordinator = hass.data[DOMAIN][entry.entry_id].get(COORDINATOR)

        entities = [
            AQMSensor(
                coordinator, id, SITENAME_DICT[id], aq_type, value["dc"],
                value["unit"], value["sc"], value["dp"], value["icon"]
            ) for aq_type, value in SENSOR_INFO.items() for id in siteid
        ]
        async_add_entities(entities)
    except Exception as e:
        _LOGGER.error(f"setup sensor error: {e}")


class AQMSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Taiwan AQM sensor."""

    def __init__(
        self,
        coordinator,
        siteid,
        sitename,
        aq_type,
        device_class,
        unit_of_measurement=None,
        state_class=None,
        display_precision=None,
        icon=None,
    ):
        """Initialize the AQI sensor."""
        super().__init__(coordinator)
        self.siteid = siteid
        self._sitename = sitename
        self._type = aq_type
        self._device_class = device_class
        self._unit_of_measurement = unit_of_measurement
        self._state_class = state_class
        self._display_precision = display_precision
        self._icon = icon
        _LOGGER.debug(
            f"Initialized TaiwanAQMEntity for siteid: {self.siteid}, type: {self._type}"
        )

    @property
    def _data(self):
        return self.coordinator.data

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.siteid)},
            "name": f"TWAQ Monitor - {self._sitename}({self.siteid})",
            "manufacturer": "台灣環境部環境資料開放平台",
            "model": "TaiwanAQM",
        }

    @property
    def native_value(self):
        if self._is_valid_data():
            return self._data[self.siteid].get(self._type)

        if self._device_class is None:
            return "unknown"
        return 0

    @property
    def device_class(self):
        return self._device_class  # 設備類型

    @property
    def native_unit_of_measurement(self):
        return self._unit_of_measurement  # 預設單位

    @property
    def state_class(self):
        return self._state_class  # 圖表類型

    @property
    def suggested_display_precision(self):
        return self._display_precision

    @property
    def extra_state_attributes(self):
        if self._data and self.siteid in self._data:
            lon = self._data[self.siteid].get("longitude", "unknown")
            lat = self._data[self.siteid].get("latitude", "unknown")
        else:
            lon = "unknown"
            lat = "unknown"

        return {
            "sitename": self._sitename,
            "siteid": self.siteid,
            "longitude": lon,
            "latitude": lat,
        }

    @property
    def available(self):
        return self.coordinator.last_update_success and self.siteid in self._data

    @property
    def name(self):
        _entity_name = f"TWAQM-{self._sitename}_{self._type}"
        return _entity_name

    @property
    def has_entity_name(self):
        return False

    @property
    def unique_id(self):
        sanitized_name = self._type.replace(
            " ", "_"
        ) if self._type else "unknown"
        return f"{DOMAIN}_{self.siteid}_{sanitized_name}"

    @property
    def icon(self):
        return self._icon

    def _is_valid_data(self) -> bool:
        """Validate the integrity of the data."""
        if not self._data:
            return False

        if self.siteid not in self._data:
            _LOGGER.warning(
                f"The site ID '{self.siteid}' is not in the data: {self._data.keys()}"
            )
            return False

        value = self._data[self.siteid].get(self._type)
        if value is None:
            _LOGGER.warning(
                f"The value for '{self._type}' in siteID '{self.siteid}' is missing or None."
            )
            return False
        if value == "" and self._type not in ["pollutant", "status"]:
            _LOGGER.warning(
                f"The value for '{self._type}' in siteID '{self.siteid}' is empy"
            )
            return False

        _LOGGER.debug(
            f"Valid data found for site '{self.siteid}' and type '{self._type}': {value}"
        )
        return True
