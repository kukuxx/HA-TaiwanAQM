import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    SelectOptionDict,
)

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_SITEID,
    SITEID_DICT,
)

_LOGGER = logging.getLogger(__name__)
TEXT_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))
SITE_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[SelectOptionDict(value=str(v), label=k) for k, v in SITEID_DICT.items()],
        mode=SelectSelectorMode.DROPDOWN,
        custom_value=False,
        multiple=True
    )
)


class TaiwanAQMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Taiwan AQM."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return TaiwanAQMOptionsFlow()

    async def async_step_user(self, user_input=None):
        """Handle the initial configuration step."""
        errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            if not user_input[CONF_API_KEY]:
                errors["base"] = "no_api"
            elif not user_input[CONF_SITEID]:
                errors["base"] = "no_id"
            else:
                return self.async_create_entry(
                    title="TWAQ Monitor",
                    data=user_input,
                )

        # 顯示縣市-測站選項和 API Key 輸入框
        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): TEXT_SELECTOR,
                vol.Required(CONF_SITEID): SITE_SELECTOR
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )


class TaiwanAQMOptionsFlow(config_entries.OptionsFlow):
    """Handle Taiwan AQM options."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}

        if user_input is not None:
            if not user_input[CONF_API_KEY]:
                errors["base"] = "no_api"
            elif not user_input[CONF_SITEID]:
                errors["base"] = "no_id"
            else:
                # 更新選項
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=user_input
                )
                return self.async_create_entry(title=None, data=None)

        old_apikey = self.config_entry.data.get(CONF_API_KEY)
        old_siteid = self.config_entry.data.get(CONF_SITEID, [])

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY, default=old_apikey): TEXT_SELECTOR,
                vol.Required(CONF_SITEID, default=old_siteid): SITE_SELECTOR
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
