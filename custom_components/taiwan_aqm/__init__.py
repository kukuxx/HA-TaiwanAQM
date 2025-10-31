import logging

from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_change

from .coordinator import SiteCoordinator, MicroSensorCoordinator
from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_SITEID,
    CONF_STATION_ID,
    CONF_THING_ID,
    SITENAME_DICT,
    SITE_COORDINATOR,
    MICRO_COORDINATOR,
    MICRO_SENSOR_IDS,
    SITE_UPDATE_TASK,
    PLATFORM,
)

CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=True)
_LOGGER = logging.getLogger(__name__)


@callback
def _get_site_ids_from_entry(entry: ConfigEntry) -> list[str]:
    """Get list of site IDs from config entry subentries."""
    # 確保 subentries 存在且可用
    if not hasattr(entry, 'subentries') or not entry.subentries:
        return []

    return [
        str(subentry.data.get(CONF_SITEID))
        for subentry in entry.subentries.values()
        if (
            subentry.subentry_type == "site"
            and subentry.data
        )
    ]


@callback
def _get_micro_sensor_ids_from_entry(entry: ConfigEntry) -> list[str]:
    """Get list of thing IDs from config entry subentries."""
    # 確保 subentries 存在且可用
    if not hasattr(entry, 'subentries') or not entry.subentries:
        return []

    return [
        str(subentry.data.get(CONF_STATION_ID))
        for subentry in entry.subentries.values()
        if (
            subentry.subentry_type == "micro_sensor"
            and subentry.data
        )
    ]


async def _async_setup_subentries(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up subentries for the config entry.

    Returns True if platforms were loaded, False otherwise.
    """
    config_data = hass.data[DOMAIN][entry.entry_id]

    # 從 subentries 獲取站點和微型感測器列表
    site_ids = _get_site_ids_from_entry(entry)
    micro_sensor_ids = _get_micro_sensor_ids_from_entry(entry)

    # 創建 coordinators
    if site_ids:
        api_key = entry.data.get(CONF_API_KEY)
        site_coordinator = SiteCoordinator(hass, api_key, site_ids)
        # 設置定時刷新任務 (僅標準站點)
        async def site_force_refresh_task(*args):
            await site_coordinator.async_refresh()
            timestamp = args[0].strftime("%Y-%m-%d %H:%M:%S %Z")
            _LOGGER.debug("Force Refresh Success at: %s", timestamp)

        site_update_task = async_track_time_change(
            hass, site_force_refresh_task, minute=10, second=0
        )
        config_data.update(
            {
                SITE_COORDINATOR: site_coordinator,
                SITE_UPDATE_TASK: site_update_task,
            }
        )
        # 初始刷新
        await site_coordinator.async_config_entry_first_refresh()

    if micro_sensor_ids:
        micro_coordinator = MicroSensorCoordinator(hass, micro_sensor_ids)
        config_data.update(
            {
                MICRO_COORDINATOR: micro_coordinator,
                MICRO_SENSOR_IDS: micro_sensor_ids,
            }
        )
        # 初始刷新
        await micro_coordinator.async_config_entry_first_refresh()

    # 初始化感測器平台
    platforms_loaded = False
    if site_ids or micro_sensor_ids:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORM)
        platforms_loaded = True

    _LOGGER.debug(
            "Setting up Taiwan AQM with sites: %s, micro sensors: %s",
            site_ids,
            micro_sensor_ids,
        )

    return platforms_loaded
    

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up global services for Taiwan AQM."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Taiwan AQM from a config entry."""
    try:
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
            "platforms_loaded": False,
        }
        platforms_loaded = await _async_setup_subentries(hass, entry)
        hass.data[DOMAIN][entry.entry_id]["platforms_loaded"] = platforms_loaded
        # 註冊更新監聽器
        entry.async_on_unload(entry.add_update_listener(update_listener))
        return True
    except ConfigEntryAuthFailed as e:
        _LOGGER.error("API key authentication failed: %s", e)
        raise
    except Exception as e:
        _LOGGER.error("async_setup_entry error: %s", e)
        return False


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    try:
        await hass.config_entries.async_reload(entry.entry_id)
    except Exception as e:
        _LOGGER.error("update_listener error: %s", e)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        aqm_data = hass.data.get(DOMAIN, {})
        entry_data = aqm_data.get(entry.entry_id, {})
        platforms_loaded = entry_data.get("platforms_loaded", False)

        if platforms_loaded:
            unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORM)
            
            if not unload_ok:
                return False
            # 取消定時刷新任務
            if (unload_task := entry_data.get(SITE_UPDATE_TASK)):
                unload_task()

        # 從 hass.data 中移除 entry 相關數據
        if entry.entry_id in aqm_data:
            aqm_data.pop(entry.entry_id)

        # 如果沒有其他 entry,移除整個 DOMAIN
        if DOMAIN in hass.data and not aqm_data:
            hass.data.pop(DOMAIN)
            _LOGGER.debug("Removed %s from hass.data", DOMAIN)

        return True
    except Exception as e:
        _LOGGER.error("async_unload_entry error: %s", e)
        return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entry."""
    _LOGGER.debug(
        "Migrating configuration from version %s, minor version %s",
        entry.version,
        entry.minor_version,
    )

    # 未來版本無法處理
    if entry.version > 2:
        _LOGGER.error("Cannot migrate from future version")
        return False

    try:
        from copy import deepcopy

        # 從版本 1 遷移到版本 2
        if entry.version < 2:
            data = deepcopy(dict(entry.data))
            # 將舊的 CONF_SITEID 列表轉換為 subentries
            old_site_ids = data.pop(CONF_SITEID, [])
            del_device_identifiers = {
                    (DOMAIN, s_id)
                    for s_id in old_site_ids
                }
            _LOGGER.debug(f"remove dev_identifiers: {del_device_identifiers}")
            if del_device_identifiers:
                device_reg = dr.async_get(hass)
                devices = [
                    device for device in
                    dr.async_entries_for_config_entry(device_reg, entry.entry_id)
                    if device.identifiers & del_device_identifiers
                ]
                for d in devices:
                        device_reg.async_remove_device(d.id)
                        _LOGGER.debug(f"removed device: {d.id}")

            # 為每個站點創建 subentry
            for site_id in old_site_ids:
                site_name = SITENAME_DICT.get(str(site_id), f"Site {site_id}")
                hass.config_entries.async_add_subentry(
                    entry,
                    ConfigSubentry(
                        subentry_type="site",
                        data={CONF_SITEID: str(site_id)},
                        title=site_name,
                        unique_id=None,
                    ),
                )

            hass.config_entries.async_update_entry(
                entry,
                data=data,
                version=2,
                minor_version=1,
            )
        
        elif entry.version == 2 and entry.minor_version < 2:
            # 為每個 subentry 更新 unique_id
            for subentry in entry.subentries.values():
                if subentry.subentry_type == "site":
                    site_data = deepcopy(dict(subentry.data))
                    site_id = site_data.get(CONF_SITEID)
                    site_name = SITENAME_DICT.get(str(site_id), f"Site {site_id}")
                    hass.config_entries.async_update_subentry(
                        entry,
                        subentry, 
                        data=site_data,
                        title=subentry.title,
                        unique_id=f"{site_name}_{site_id}",
                    )
                elif subentry.subentry_type == "micro_sensor":
                    micro_data = deepcopy(dict(subentry.data))
                    micro_data.pop(CONF_THING_ID, None)
                    hass.config_entries.async_update_subentry(
                        entry,
                        subentry, 
                        data=micro_data,
                        title=subentry.title,
                        unique_id=str(micro_data[CONF_STATION_ID]),
                    )
                
                _LOGGER.debug(
                    "Migrated subentry %s to version %s, minor version 2",
                    subentry.subentry_id,
                    entry.version,
                )
            
            entry_data = deepcopy(dict(entry.data))
            hass.config_entries.async_update_entry(
                entry,
                data=entry_data,
                version=entry.version,
                minor_version=2,
            )

            _LOGGER.debug(
                "Migrated entry %s to version %s, minor version 2",
                entry.entry_id,
                entry.version,
            )

        return True

    except Exception as e:
        _LOGGER.error("async_migrate_entry error: %s", e)
        return False
