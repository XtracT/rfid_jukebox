"""Sensor platform for RFID Jukebox."""
import logging

from homeassistant.components.sensor import SensorEntity
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
    """Set up the sensor platform from a config entry."""
    # This will be used for UI-based configuration in the future.
    pass


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the sensor platform from YAML."""
    if DOMAIN in hass.data:
        jukebox = hass.data[DOMAIN]
        async_add_entities([LastTagSensor(jukebox)], False)


class LastTagSensor(SensorEntity):
    """Representation of a sensor that shows the last scanned RFID tag."""

    def __init__(self, jukebox):
        """Initialize the sensor."""
        self._jukebox = jukebox
        self._jukebox.sensor = self  # Register sensor with the jukebox instance
        self._attr_name = "RFID Jukebox Last Tag"
        self._attr_unique_id = f"{DOMAIN}_last_tag"
        self._attr_icon = "mdi:credit-card-scan-outline"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._jukebox.last_tag

    def update(self):
        """Fetch new state data for the sensor.
        
        This is the only method that should fetch new data for Home Assistant.
        """
        # State is pushed from the jukebox instance, so this is not needed.
        pass