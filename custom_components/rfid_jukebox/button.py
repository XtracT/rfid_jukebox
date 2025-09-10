"""Button platform for RFID Jukebox."""
import logging

from homeassistant.components.button import ButtonEntity
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
    """Set up the button platform from a config entry."""
    jukebox = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MapTagButton(jukebox)])


class MapTagButton(ButtonEntity):
    """Representation of a Button entity for mapping tags."""

    def __init__(self, jukebox):
        """Initialize the button entity."""
        self._jukebox = jukebox
        self._attr_name = "Map Scanned Tag to Media"
        self._attr_unique_id = f"{DOMAIN}_map_tag_button"
        self._attr_icon = "mdi:tag-plus"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Map tag button pressed")

        # Get values from UI entities
        media_type = self.hass.states.get(f"select.{DOMAIN}_media_type").state
        media_name = self.hass.states.get(f"text.{DOMAIN}_media_name_to_map").state
        alias = self.hass.states.get(f"text.{DOMAIN}_alias").state
        tag_id = self._jukebox.last_tag

        await self._jukebox.async_map_tag(tag_id, media_type, media_name, alias)