"""Media player platform for RFID Jukebox."""
import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_MEDIA_PLAYER

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media player platform."""
    jukebox = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([JukeboxMediaPlayer(jukebox)])


class JukeboxMediaPlayer(MediaPlayerEntity):
    """The virtual media player for the RFID Jukebox."""

    def __init__(self, jukebox):
        """Initialize the media player."""
        self._jukebox = jukebox
        self._jukebox.media_player = self  # Register with the main jukebox instance
        self._attr_name = "RFID Jukebox"
        self._attr_unique_id = f"{jukebox.entry.entry_id}_media_player"
        self._attr_icon = "mdi:music-box"

        self._attr_state = MediaPlayerState.IDLE
        self._attr_media_title = None
        self._attr_media_artist = None
        self._attr_media_album_name = None
        self._attr_media_playlist = None
        self._attr_queue_position = None
        self._attr_volume_level = None
        self._attr_is_volume_muted = None
        self._attr_media_image_url = None

        self._attr_supported_features = (
            MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.VOLUME_STEP
        )

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._jukebox.entry.entry_id)},
            "name": "RFID Jukebox",
        }

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        physical_player_entity_id = self._jukebox.config[CONF_MEDIA_PLAYER]
        if physical_player_state := self.hass.states.get(physical_player_entity_id):
            self._attr_volume_level = physical_player_state.attributes.get("volume_level")
            self._attr_is_volume_muted = physical_player_state.attributes.get(
                "is_volume_muted"
            )

    async def async_play_media(self, media_type, media_id, **kwargs):
        """Send play command."""
        await self._jukebox.async_play_folder(media_id)

    async def async_media_play(self):
        """Send play command."""
        await self._jukebox.async_play()

    async def async_media_pause(self):
        """Send pause command."""
        await self._jukebox.async_pause()

    async def async_media_stop(self):
        """Send stop command."""
        await self._jukebox.async_stop()

    async def async_media_next_track(self):
        """Send next track command."""
        await self._jukebox.async_next_track()

    async def async_media_previous_track(self):
        """Send previous track command."""
        await self._jukebox.async_previous_track()

    async def async_set_volume_level(self, volume):
        """Set volume level."""
        await self._jukebox.async_set_volume_level(volume)

    async def async_mute_volume(self, mute):
        """Mute the volume."""
        await self._jukebox.async_mute_volume(mute)

    async def async_volume_up(self):
        """Step volume up."""
        await self._jukebox.async_volume_up()

    async def async_volume_down(self):
        """Step volume down."""
        await self._jukebox.async_volume_down()