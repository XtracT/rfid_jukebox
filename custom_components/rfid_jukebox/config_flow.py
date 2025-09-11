"""Config flow for RFID Jukebox."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_TAG_SENSOR,
    CONF_MEDIA_PLAYER,
    CONF_MA_FILESYSTEM,
)

_LOGGER = logging.getLogger(__name__)

class RFIDJukeboxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RFID Jukebox."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle the initial step."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            # TODO: Validate user input
            return self.async_create_entry(title="RFID Jukebox", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TAG_SENSOR): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=["sensor", "input_text"]),
                    ),
                    vol.Required(CONF_MEDIA_PLAYER): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="media_player"),
                    ),
                    vol.Optional(CONF_MA_FILESYSTEM): str,
                }
            ),
            errors=errors,
            description_placeholders=None,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return RFIDJukeboxOptionsFlowHandler(config_entry)


class RFIDJukeboxOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for RFID Jukebox."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manage the options."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TAG_SENSOR,
                        default=self.config_entry.data.get(CONF_TAG_SENSOR),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=["sensor", "input_text"]),
                    ),
                    vol.Required(
                        CONF_MEDIA_PLAYER,
                        default=self.config_entry.data.get(CONF_MEDIA_PLAYER),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="media_player"),
                    ),
                    vol.Optional(
                        CONF_MA_FILESYSTEM,
                        default=self.config_entry.data.get(CONF_MA_FILESYSTEM),
                    ): str,
                }
            ),
            errors=errors,
            description_placeholders=None,
        )