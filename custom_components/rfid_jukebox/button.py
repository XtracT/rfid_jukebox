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

        # Get values from UI entities directly (avoid hard-coded entity IDs)
        if self._jukebox.media_type_entity is None:
            _LOGGER.warning("Media type entity not ready, cannot map tag")
            return
        if self._jukebox.text_entity is None:
            _LOGGER.warning("Media name entity not ready, cannot map tag")
            return

        media_type = self._jukebox.media_type_entity.current_option
        media_name = self._jukebox.text_entity.native_value
        alias = (
            self._jukebox.alias_entity.native_value
            if self._jukebox.alias_entity else None
        )
        tag_id = self._jukebox.last_tag

        if not tag_id:
            _LOGGER.warning("No tag has been scanned yet, cannot map")
            return
        if not media_name:
            _LOGGER.warning("Media name is empty, cannot map tag %s", tag_id)
            return

        await self._jukebox.async_map_tag(tag_id, media_type, media_name, alias)