"""Select platform for RFID Jukebox."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform from a config entry."""
    jukebox = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MediaTypeSelect(jukebox)])

class MediaTypeSelect(SelectEntity):
    """Representation of a Select entity for choosing media type."""

    def __init__(self, jukebox):
        """Initialize the select entity."""
        self._jukebox = jukebox
        self._jukebox.media_type_entity = self
        self._attr_name = "RFID Jukebox Media Type"
        self._attr_unique_id = f"{DOMAIN}_media_type"
        self._attr_icon = "mdi:music-box-outline"
        self._attr_options = ["playlist", "folder"]
        self._attr_current_option = "playlist"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._attr_current_option = option
        self.async_write_ha_state()

    def update_option(self, option: str):
        """Update the selected option from the jukebox."""
        self._attr_current_option = option
        self.async_write_ha_state()