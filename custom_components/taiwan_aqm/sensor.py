from __future__ import annotations

import logging

from homeassistant.components.sensor import RestoreSensor
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_STATION_ID,
    CONF_SITEID,
    CONF_THING_ID,
    DOMAIN,
    MICRO_COORDINATORS,
    SENSOR_INFO,
    SITE_COORDINATOR,
    SITENAME_DICT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Taiwan AQM sensors from a config entry."""
    try:
        entry_data = hass.data[DOMAIN][entry.entry_id]

        for subentry_id, subentry in entry.subentries.items():
            if not hasattr(subentry, 'subentry_type'):
                continue

            subentry_entities = []

            # 處理標準監測站 subentry
            if subentry.subentry_type == "site":
                site_id = subentry.data.get(CONF_SITEID)
                coordinator = entry_data.get(SITE_COORDINATOR)
                site_name = SITENAME_DICT.get(site_id, f"Site {site_id}")
                
                subentry_entities.extend([
                    SiteSensor(
                        coordinator=coordinator,
                        siteid=site_id,
                        sitename=site_name,
                        aq_type=aq_type,
                        device_class=config["device_class"],
                        unit_of_measurement=config["unit"],
                        state_class=config["state_class"],
                        display_precision=config["display_precision"],
                        icon=config["icon"]
                    ) for aq_type, config in SENSOR_INFO.items()
                    if aq_type not in ["temperature", "humidity"]
                ])

            # 處理微型感測器 subentry
            elif subentry.subentry_type == "micro_sensor":
                station_id = subentry.data.get(CONF_STATION_ID)
                thing_id = subentry.data.get(CONF_THING_ID)
                coordinator = entry_data[MICRO_COORDINATORS].get(station_id)
                if not coordinator:
                    _LOGGER.warning("Micro sensor coordinator not found for station %s", station_id)
                    continue

                subentry_entities.extend([
                    MicroSensor(
                        coordinator=coordinator,
                        station_id=station_id,
                        thing_id=thing_id,
                        aq_type=aq_type,
                        device_class=config["device_class"],
                        unit_of_measurement=config["unit"],
                        state_class=config["state_class"],
                        display_precision=config["display_precision"],
                        icon=config["icon"]
                    ) for aq_type, config in SENSOR_INFO.items()
                    if aq_type in ["pm2.5", "temperature", "humidity"]
                ])

            # 為這個 subentry 添加實體
            if subentry_entities:
                async_add_entities(subentry_entities, config_subentry_id=subentry_id)
                _LOGGER.debug(
                    "Added %d entities for subentry %s (type: %s)",
                    len(subentry_entities),
                    subentry_id,
                    subentry.subentry_type
                )

    except Exception as e:
        _LOGGER.error("setup sensor error: %s", e, exc_info=True)



class AQMbaseSensor(CoordinatorEntity, RestoreSensor):
    """Representation of a Taiwan AQM base sensor."""

    def __init__(
        self,
        coordinator,
        station_or_site_id,
        station_or_site_name,
        aq_type,
        device_class,
        unit_of_measurement,
        state_class,
        display_precision,
        icon,
    ):
        """Initialize the AQI sensor."""
        super().__init__(coordinator)
        self._station_or_site_id = station_or_site_id
        self._station_or_site_name = station_or_site_name
        self._aq_type = aq_type
        self._device_class = device_class
        self._unit_of_measurement = unit_of_measurement
        self._state_class = state_class
        self._display_precision = display_precision
        self._icon = icon
        self._last_value = None

    async def async_added_to_hass(self):
        """Get the old value"""
        await super().async_added_to_hass()

        if (
            (last_sensor_data := await self.async_get_last_sensor_data())
            and last_sensor_data.native_value is not None
            and self._device_class is not None
        ):
            self._last_value = last_sensor_data.native_value
            _LOGGER.debug(
                "Restored last value: %s for %s", self._last_value, self.name
            )

    @property
    def coordinator_data(self) -> dict:
        return self.coordinator.data
    
    @property
    def _get_value(self):
        return self.coordinator_data[self._station_or_site_id][self._aq_type]

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._station_or_site_id)},
            "name": (
                f"TWAQ Monitor - {self._station_or_site_name}"
                f"({self._station_or_site_id})"
            ),
            "manufacturer": "Taiwan Ministry of Environment Data Open Platform",
            "model": "TaiwanAQM",
        }

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
    def icon(self):
        return self._icon

    @property
    def has_entity_name(self):
        return False

    @property
    def available(self):
        return self._station_or_site_id in self.coordinator_data

    @property
    def name(self):
        sensor_type = (
            self._aq_type.replace("_", " ") if self._aq_type else "unknown"
        )

        if "Micro Sensor" in self._station_or_site_name:
            return (
                f"{self._station_or_site_name}"
                f"({self._station_or_site_id}) {sensor_type}"
            )
        else:
            return f"{self._station_or_site_name} {sensor_type}"

    @property
    def unique_id(self):
        sanitized_name = (
            self._aq_type.replace(" ", "_") if self._aq_type else "unknown"
        )
        return f"{DOMAIN}_{self._station_or_site_id}_{sanitized_name}"

    @property
    def native_value(self):
        if self._is_valid_data() and self.coordinator.last_update_success:
            return self._get_value
        else:
            return "unknown" if self._device_class is None else 0

    def _is_valid_data(self) -> bool:
        """Validate the integrity of the data."""
        _type = (
            "site"
            if "Micro Sensor" not in self._station_or_site_name
            else "micro sensor station"
        )

        if not self.coordinator_data:
            if _type == "site":
                _LOGGER.error("No %s data available", _type)
            else:
                _LOGGER.error(
                    "No %s data available for station %s",
                    _type,
                    self._station_or_site_id,
                )
            return False

        if self._station_or_site_id not in self.coordinator_data:
            _LOGGER.warning(
                "The %s ID '%s' is not in the data: %s",
                _type,
                self._station_or_site_id,
                list(self.coordinator_data.keys()),
            )
            return False

        if (value := self._get_value) in [None, ""]:
            if value is None:
                _LOGGER.debug(
                    "The value for '%s' in %s ID '%s' is missing or None.",
                    self._aq_type,
                    _type,
                    self._station_or_site_id,
                )
            elif value == "":
                _LOGGER.debug(
                    "The value for '%s' in %s ID '%s' is empty",
                    self._aq_type,
                    _type,
                    self._station_or_site_id,
                )
            return False

        _LOGGER.debug(
            "Valid data found for %s ID'%s' and type '%s': %s",
            _type,
            self._station_or_site_id,
            self._aq_type,
            value,
        )
        return True


class SiteSensor(AQMbaseSensor):
    """Representation of a Taiwan AQM Site Sensor."""

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
        """Initialize the site sensor."""
        super().__init__(
            coordinator,
            siteid,
            sitename,
            aq_type,
            device_class,
            unit_of_measurement,
            state_class,
            display_precision,
            icon,
        )

        self._siteid = siteid
        _LOGGER.debug(
            "Initialized TaiwanAQMEntity for siteid: %s, type: %s",
            self._siteid,
            self._aq_type,
        )

    @property
    def extra_state_attributes(self):
        if self.coordinator_data and self._siteid in self.coordinator_data:
            lon = self.coordinator_data[self._siteid].get("longitude", "unknown")
            lat = self.coordinator_data[self._siteid].get("latitude", "unknown")
        else:
            lon = "unknown"
            lat = "unknown"

        return {
            "site_id": self._siteid,
            "longitude": lon,
            "latitude": lat,
        }


class MicroSensor(AQMbaseSensor):
    """Representation of a Taiwan AQM Micro Sensor."""

    def __init__(
        self,
        coordinator,
        station_id,
        thing_id,
        aq_type,
        device_class,
        unit_of_measurement=None,
        state_class=None,
        display_precision=None,
        icon=None,
    ):
        """Initialize the Micro sensor."""
        super().__init__(
            coordinator,
            station_id,
            "Micro Sensor",
            aq_type,
            device_class,
            unit_of_measurement,
            state_class,
            display_precision,
            icon,
        )

        self._station_id = station_id
        self._thing_id = thing_id
        _LOGGER.debug(
            "Initialized MicroSensor for station_id: %s, type: %s",
            self._station_id,
            self._aq_type,
        )


    @property
    def extra_state_attributes(self):
        if self.coordinator_data and self._station_id in self.coordinator_data:
            thing_data = self.coordinator_data[self._station_id]

            attrs = {
                "city": thing_data.get("city", "unknown"),
                "area": thing_data.get("area", "unknown"),
                "station_id": self._station_id,
                "thing_id": self._thing_id,
                "longitude": thing_data.get("longitude", "unknown"),
                "latitude": thing_data.get("latitude", "unknown"),
                "last_update": thing_data.get(
                    f"{self._aq_type}_time", "unknown"
                ),
            }

            return attrs
        else:
            return {
                "station_id": self._station_id,
                "thing_id": self._thing_id,
            }
