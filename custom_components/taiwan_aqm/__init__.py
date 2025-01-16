from __future__ import annotations

import asyncio
import logging

from copy import deepcopy

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .coordinator import AQMCoordinator
from .const import DOMAIN, PLATFORM, UPDATE_INTERVAL

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
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][entry.entry_id] = coordinator
        # 初始化感測器平台
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORM)

        entry.async_on_unload(entry.add_update_listener(update_listener))

        return True
    except Exception as e:
        _LOGGER.error(f"async_setup_entry error {e}")
        return False


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    try:
        await hass.config_entries.async_reload(entry.entry_id)
    except Exception as e:
        _LOGGER.error(f"update_listener error {e}")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORM)
        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id)
            return True
        else:
            return False
    except Exception as e:
        _LOGGER.error(f"async_unload_entry error {e}")
        return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_unload_platforms(entry, PLATFORM)

        if DOMAIN in hass.data and not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    except Exception as e:
        _LOGGER.error(f"async_remove_entry error {e}")


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
