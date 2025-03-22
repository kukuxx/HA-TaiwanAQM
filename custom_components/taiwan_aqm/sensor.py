from __future__ import annotations

import logging

from homeassistant.components.sensor import RestoreSensor
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
        siteid = hass.data[DOMAIN][entry.entry_id].get(SITEID)
        coordinator = hass.data[DOMAIN][entry.entry_id].get(COORDINATOR)

        entities = [
            AQMSensor(
                coordinator=coordinator,
                siteid=s_id,
                sitename=SITENAME_DICT[s_id],
                aq_type=aq_type,
                device_class=config["dc"],
                unit_of_measurement=config["unit"],
                state_class=config["sc"],
                display_precision=config["dp"],
                icon=config["icon"]
            ) for s_id in siteid for aq_type, config in SENSOR_INFO.items()
        ]
        async_add_entities(entities)
    except Exception as e:
        _LOGGER.error(f"setup sensor error: {e}")


class AQMSensor(CoordinatorEntity, RestoreSensor):
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
        self._last_value = None
        _LOGGER.debug(f"Initialized TaiwanAQMEntity for siteid: {self.siteid}, type: {self._type}")

    async def async_added_to_hass(self):
        """Get the old value"""
        await super().async_added_to_hass()

        if (last_sensor_data := await self.async_get_last_sensor_data()) \
            and last_sensor_data.native_value is not None \
            and self._device_class is not None:

            self._last_value = last_sensor_data.native_value

    @property
    def _data(self):
        return self.coordinator.data

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.siteid)},
            "name": f"TWAQ Monitor - {self._sitename}({self.siteid})",
            "manufacturer": "Taiwan Ministry of Environment Data Open Platform",
            "model": "TaiwanAQM",
        }

    @property
    def native_value(self):
        if self._is_valid_data() and self.coordinator.last_update_success:
            self._last_value = self._data[self.siteid].get(self._type)
            return self._last_value
        else:
            return "unknown" if self._device_class is None else 0

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
        return self.siteid in self._data

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

    def _is_valid_data(self) -> bool:
        """Validate the integrity of the data."""
        if not self._data:
            _LOGGER.error("No data available")
            return False

        if self.siteid not in self._data:
            _LOGGER.warning(f"The site ID '{self.siteid}' is not in the data: {self._data.keys()}")
            return False

        if (value := self._data[self.siteid].get(self._type)) in [None, ""]:
            if value is None:
                _LOGGER.debug(f"The value for '{self._type}' in siteID '{self.siteid}' is missing or None.")
            elif value == "":
                _LOGGER.debug(f"The value for '{self._type}' in siteID '{self.siteid}' is empy")
            return False

        _LOGGER.debug(f"Valid data found for site '{self.siteid}' and type '{self._type}': {value}")
        return True
