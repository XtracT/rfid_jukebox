"""Button platform for RFID Jukebox."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the button platform from YAML."""
    if DOMAIN in hass.data:
        jukebox = hass.data[DOMAIN]
        async_add_entities([MapTagButton(jukebox)], False)


class MapTagButton(ButtonEntity):
    """Representation of a Button entity for mapping tags."""

    def __init__(self, jukebox):
        """Initialize the button entity."""
        self._jukebox = jukebox
        self._attr_name = "Map Scanned Tag to Selected Playlist"
        self._attr_unique_id = f"{DOMAIN}_map_tag_button"
        self._attr_icon = "mdi:tag-plus"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Map tag button pressed")
        await self._jukebox.async_map_tag_from_ui()