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
        coordinator = hass.data[DOMAIN][entry.entry_id].get(COORDINATOR, None)

        entities = [
            AQMSensor(
                coordinator, id, SITENAME_DICT[id], aq_type, value["dc"], value["unit"],
                value["sc"], value["dp"], value["icon"]
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
            "Initialized TaiwanAQMEntity for siteid: %s, type: %s", siteid, aq_type
        )

    @property
    def _data(self):
        if not self.coordinator.data:
            data = {}
            _LOGGER.warning("Coordinator data is empty for siteid: %s", self.siteid)
        else:
            data = self.coordinator.data

        return data

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
            return self._data[self.siteid].get(self._type, None)
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
        sanitized_name = self._type.replace(" ", "_") if self._type else "unknown"
        return f"{DOMAIN}_{self.siteid}_{sanitized_name}"

    @property
    def icon(self):
        return self._icon

    def _is_valid_data(self):
        if (
            self._data and self.siteid in self._data
            and self._type in self._data.get(self.siteid, {})
        ):
            return True
        return False
