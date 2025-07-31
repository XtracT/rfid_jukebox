"""Text platform for RFID Jukebox."""
import logging

from homeassistant.components.text import TextEntity
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
    """Set up the text platform from a config entry."""
    jukebox = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PlaylistNameText(jukebox)])


class PlaylistNameText(TextEntity):
    """Representation of a Text entity for entering a playlist name."""

    def __init__(self, jukebox):
        """Initialize the text entity."""
        self._jukebox = jukebox
        self._jukebox.text_entity = self  # Register entity with the jukebox instance
        self._attr_name = "RFID Jukebox Playlist to Map"
        self._attr_unique_id = f"{DOMAIN}_playlist_to_map"
        self._attr_icon = "mdi:playlist-edit"
        self._attr_native_value = self._jukebox.playlist_to_map

    async def async_set_value(self, value: str) -> None:
        """Change the value."""
        self._jukebox.playlist_to_map = value
        self._attr_native_value = value
        self.async_write_ha_state()