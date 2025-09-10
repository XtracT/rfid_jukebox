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
    async_add_entities([
        MediaNameText(jukebox),
        AliasText(jukebox),
    ])


class MediaNameText(TextEntity):
    """Representation of a Text entity for entering a media name."""

    def __init__(self, jukebox):
        """Initialize the text entity."""
        self._jukebox = jukebox
        self._jukebox.text_entity = self
        self._attr_name = "RFID Jukebox Media Name to Map"
        self._attr_unique_id = f"{DOMAIN}_media_name_to_map"
        self._attr_icon = "mdi:music-box"
        self._attr_native_value = ""

    async def async_set_value(self, value: str) -> None:
        """Change the value of the text entity."""
        self._attr_native_value = value
        self.async_write_ha_state()

    def update_value(self, value: str):
        """Update the value of the text entity from the jukebox."""
        self._attr_native_value = value
        self.async_write_ha_state()


class AliasText(TextEntity):
    """Representation of a Text entity for entering a media alias."""

    def __init__(self, jukebox):
        """Initialize the text entity."""
        self._jukebox = jukebox
        self._jukebox.alias_entity = self
        self._attr_name = "RFID Jukebox Alias"
        self._attr_unique_id = f"{DOMAIN}_alias"
        self._attr_icon = "mdi:label"
        self._attr_native_value = ""

    async def async_set_value(self, value: str) -> None:
        """Change the value of the text entity."""
        self._attr_native_value = value
        self.async_write_ha_state()

    def update_value(self, value: str):
        """Update the value of the text entity from the jukebox."""
        self._attr_native_value = value
        self.async_write_ha_state()