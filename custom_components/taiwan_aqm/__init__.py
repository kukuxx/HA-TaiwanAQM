import logging

from copy import deepcopy

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_time_change

from .coordinator import AQMCoordinator
from .const import (
    DOMAIN,
    CONF_SITEID,
    COORDINATOR,
    SITEID,
    TASK,
    PLATFORM,
    UPDATE_INTERVAL,
)

CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=True)
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up global services for Taiwan AQM  ."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Taiwan AQM from a config entry."""
    try:
        hass.data.setdefault(DOMAIN, {})
        coordinator = AQMCoordinator(hass, entry, UPDATE_INTERVAL)

        async def refresh_task(*args):
            await coordinator.async_refresh()
            _LOGGER.debug(
                f"Refresh Success at: {args[0].strftime('%Y-%m-%d %H:%M:%S %Z')}"
            )

        task = async_track_time_change(hass, refresh_task, minute=10, second=0)
        hass.data[DOMAIN][entry.entry_id] = {
            COORDINATOR: coordinator,
            SITEID: entry.data.get(CONF_SITEID),
            TASK: task,
        }
        await coordinator.async_config_entry_first_refresh()
        # 初始化感測器平台
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORM)

        entry.async_on_unload(entry.add_update_listener(update_listener))

        return True
    except Exception as e:
        _LOGGER.error(f"async_setup_entry error: {e}")
        return False


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    try:
        await hass.config_entries.async_reload(entry.entry_id)
    except Exception as e:
        _LOGGER.error(f"update_listener error: {e}")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        task = hass.data[DOMAIN][entry.entry_id].get(TASK)
        task()
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, PLATFORM
        )

        if unload_ok:
            old_siteid = hass.data[DOMAIN][entry.entry_id].get(SITEID, [])
            new_siteid = entry.data.get(CONF_SITEID, [])
            del_dev_identifiers = {
                (DOMAIN, id)
                for id in old_siteid if id not in new_siteid
            }
            _LOGGER.debug(f"remove dev_identifiers: {del_dev_identifiers}")
            if del_dev_identifiers:
                dev_reg = dr.async_get(hass)
                devices = [
                    device for device in
                    dr.async_entries_for_config_entry(dev_reg, entry.entry_id)
                    if device.identifiers & del_dev_identifiers
                ]
                for dev in devices:
                    dev_reg.async_remove_device(dev.id)
                    _LOGGER.debug(f"removed device: {dev.id}")

            hass.data[DOMAIN].pop(entry.entry_id)
            if DOMAIN in hass.data and not hass.data[DOMAIN]:
                hass.data.pop(DOMAIN)

            return True
        else:
            return False
    except Exception as e:
        _LOGGER.error(f"async_unload_entry error: {e}")
        return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


# async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """Migrate config entry."""
#     if entry.version > 2:
#         # 未來版本無法處理
#         return False

#     if entry.version < 2:
#         # 舊版本更新資料
#         data = deepcopy(dict(entry.data))

#         hass.config_entries.async_update_entry(entry, version=2, data=data)
#     return True
