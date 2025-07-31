"""DataUpdateCoordinator for the RFID Jukebox integration."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class RFIDJukeboxCoordinator(DataUpdateCoordinator):
    """Manages fetching data for the RFID Jukebox integration."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        # We will add logic here to periodically fetch data if needed,
        # for example, to check the status of Music Assistant playlists.