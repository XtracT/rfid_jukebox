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
        self._attr_name = "Map Last Tag"
        self._attr_unique_id = f"{jukebox.entry.entry_id}_map_last_tag"
        self._attr_icon = "mdi:tag-plus"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._jukebox.entry.entry_id)},
            "name": "RFID Jukebox",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._jukebox.async_map_tag_from_ui()