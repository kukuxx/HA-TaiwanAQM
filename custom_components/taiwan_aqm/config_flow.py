import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_API_KEY,
    CONF_SITEID,
    CONF_STATION_ID,
    CONF_THING_ID,
    DOMAIN,
    HA_USER_AGENT,
    MICRO_ID_API_URL,
    SITEID_DICT,
    SITENAME_DICT,
)

_LOGGER = logging.getLogger(__name__)
TEXT_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))
SITE_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[
            SelectOptionDict(value=str(v), label=k)
            for k, v in SITEID_DICT.items()
        ],
        mode=SelectSelectorMode.DROPDOWN,
        custom_value=False,
        multiple=False,
    )
)

class TaiwanAQMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Taiwan AQM."""

    VERSION = 2

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth configuration."""
        return await self.async_step_reauth_confirm()
    
    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauthentication dialog."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input[CONF_API_KEY]:
                errors["base"] = "no_api"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates=user_input,
                )

        schema = vol.Schema(
            {vol.Required(CONF_API_KEY): TEXT_SELECTOR}
        )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the initial configuration step."""
        errors: dict[str, str] = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            if not user_input[CONF_API_KEY]:
                errors["base"] = "no_api"
            else:
                return self.async_create_entry(
                    title="TWAQ Monitor",
                    data=user_input,
                )

        schema = vol.Schema(
            {vol.Required(CONF_API_KEY): TEXT_SELECTOR}
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls,
        config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {
            "site": SiteSubentryFlowHandler,
            "micro_sensor": MicroSensorSubentryFlowHandler,
        }


class SiteSubentryFlowHandler(ConfigSubentryFlow):
    """Handle subentry flow for adding and modifying monitoring sites."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle the initial step."""
        return await self.async_step_site()

    async def async_step_site(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Site flow to add a new monitoring site."""
        errors: dict[str, str] = {}

        # 取得已存在的站點 ID
        config_entry = self._get_entry()
        existing_site_ids = []
        if hasattr(config_entry, 'subentries') and config_entry.subentries:
            existing_site_ids = [
                subentry.data.get(CONF_SITEID)
                for subentry in config_entry.subentries
                if (hasattr(subentry, 'subentry_type')
                and subentry.subentry_type == "site")
            ]

        if user_input is not None:
            if not user_input.get(CONF_SITEID):
                errors["base"] = "no_id"
            elif user_input[CONF_SITEID] in existing_site_ids:
                errors["base"] = "site_already_configured"
            else:
                site_id = user_input[CONF_SITEID]
                site_name = SITENAME_DICT.get(site_id, f"Site {site_id}")

                return self.async_create_entry(
                    title=site_name,
                    data=user_input,
                )

        schema = vol.Schema(
            {vol.Required(CONF_SITEID): SITE_SELECTOR}
        )

        return self.async_show_form(
            step_id="site",
            data_schema=schema,
            errors=errors,
        )


class MicroSensorSubentryFlowHandler(ConfigSubentryFlow):
    """Handle subentry flow for adding micro sensors."""

    @callback
    async def _query_thing_id(
        self, station_id: str
    ) -> tuple[int | None, str | None, str]:
        """Query Thing ID from API. Returns (thing_id,error)."""
        try:
            client = get_async_client(self.hass, False)
            url = MICRO_ID_API_URL.format(station_id)
            headers = {
                "Accept": "application/json",
                "User-Agent": HA_USER_AGENT,
            }

            response = await client.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("@iot.count", 0) > 0:
                    thing_id = data["value"][0]["@iot.id"]
                    return thing_id, ""
                else:
                    return None, "station_not_found"
            else:
                return None, "cannot_connect"
        except Exception as e:
            _LOGGER.error("Error querying micro sensor API: %s", e)
            return None, "unknown"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle the initial step."""
        return await self.async_step_micro_sensor()

    async def async_step_micro_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Micro sensor flow to add a new micro sensor."""
        errors: dict[str, str] = {}

        # 取得已存在的 station ID
        config_entry = self._get_entry()
        existing_station_ids = []
        if hasattr(config_entry, 'subentries') and config_entry.subentries:
            existing_station_ids = [
                subentry.data.get(CONF_STATION_ID)
                for subentry in config_entry.subentries
                if (hasattr(subentry, 'subentry_type')
                and subentry.subentry_type == "micro_sensor")
            ]

        if user_input is not None:
            station_id = user_input.get(CONF_STATION_ID)
            if not station_id:
                errors["base"] = "no_station_id"
            elif station_id in existing_station_ids:
                errors["base"] = "micro_sensor_already_configured"
            else:
                thing_id, error = await self._query_thing_id(station_id)
                if error:
                    errors["base"] = error
                else:
                    return self.async_create_entry(
                        title=f"Micro Sensor-{station_id}",
                        data={
                            CONF_STATION_ID: station_id,
                            CONF_THING_ID: thing_id,
                        },
                    )

        schema = vol.Schema(
            {vol.Required(CONF_STATION_ID): TEXT_SELECTOR}
        )

        return self.async_show_form(
            step_id="micro_sensor",
            data_schema=schema,
            errors=errors,
        )
