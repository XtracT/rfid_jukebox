"""The RFID Jukebox integration."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import event

from .const import (
    DOMAIN,
    CONF_TAG_SENSOR,
    CONF_MEDIA_PLAYER,
    CONF_UNMAPPED_TAG_TTS_MESSAGE,
    CONF_TTS_SERVICE,
    DEFAULT_MAPPING_FILE_PATH,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RFID Jukebox from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    jukebox = RFIDJukebox(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = jukebox

    await jukebox.async_setup()

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "text", "button"])

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "text", "button"]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class RFIDJukebox:
    """The main class for the RFID Jukebox integration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the RFID Jukebox."""
        self.hass = hass
        self.entry = entry
        self.config = entry.data
        self.mappings = {}
        self.last_tag = None
        self.current_tag = None
        self.sensor = None
        self.text_entity = None
        self.playlist_to_map = ""
        self.last_played_playlist_name = None

    async def async_setup(self):
        """Set up the jukebox."""
        from .helpers import load_mappings

        # Load mappings
        mapping_file = self.hass.config.path(DEFAULT_MAPPING_FILE_PATH)
        self.mappings = await self.hass.async_add_executor_job(
            load_mappings, self.hass, mapping_file
        )

        # Register state listener
        self.entry.async_on_unload(
            event.async_track_state_change_event(
                self.hass, self.config[CONF_TAG_SENSOR], self.async_tag_changed_handler
            )
        )

        # Register services
        self.hass.services.async_register(
            DOMAIN, "map_tag", self.async_map_tag_service
        )
        self.hass.services.async_register(
            DOMAIN, "reload_mappings", self.async_reload_mappings_service
        )

    async def async_tag_changed_handler(self, event_data):
        """Handle state changes for the RFID tag sensor."""
        new_state = event_data.data.get("new_state")
        if not new_state:
            return

        new_tag = new_state.state
        _LOGGER.debug("Tag sensor changed to: %s", new_tag)

        # Tag is presented
        if new_tag and new_tag.lower() not in ["none", "unknown", ""]:
            # Update the 'last_tag' sensor for the UI
            if self.last_tag != new_tag:
                self.last_tag = new_tag
                if self.sensor:
                    self.sensor.async_schedule_update_ha_state(True)

            # If it's the same tag that was just playing, resume.
            if self.current_tag == new_tag:
                await self.async_resume_playback()
            # Otherwise, it's a new playlist.
            else:
                self.current_tag = new_tag
                if new_tag in self.mappings:
                    await self.async_start_new_playlist(self.mappings[new_tag])
                else:
                    await self.async_announce_unmapped_tag()
        # Tag is removed
        else:
            if self.current_tag:
                await self.async_pause_player()
                # We don't clear current_tag here, so we can resume it later

    async def async_start_new_playlist(self, playlist_name: str):
        """Start a new playlist from the beginning."""
        _LOGGER.info("Starting new playlist '%s'", playlist_name)
        from homeassistant.exceptions import HomeAssistantError

        try:
            await self.hass.services.async_call(
                "music_assistant",
                "play_media",
                {
                    "entity_id": self.config[CONF_MEDIA_PLAYER],
                    "media_id": playlist_name,
                    "media_type": "playlist",
                },
                blocking=True,
            )
        except HomeAssistantError as err:
            _LOGGER.error(
                "Error playing playlist '%s': %s. Please ensure the playlist name is spelled correctly and exists in Music Assistant.",
                playlist_name,
                err,
            )

    async def async_resume_playback(self):
        """Resume the currently paused media player."""
        _LOGGER.info("Resuming playback")
        await self.hass.services.async_call(
            "media_player",
            "media_play",
            {"entity_id": self.config[CONF_MEDIA_PLAYER]},
            blocking=True,
        )

    async def async_pause_player(self):
        """Pause the media player."""
        _LOGGER.info("Pausing player")
        await self.hass.services.async_call(
            "media_player",
            "media_pause",
            {"entity_id": self.config[CONF_MEDIA_PLAYER]},
            blocking=True,
        )

    async def async_announce_unmapped_tag(self):
        """Announce that the scanned tag is not mapped."""
        message = self.config.get(
            CONF_UNMAPPED_TAG_TTS_MESSAGE, "This tag is not mapped."
        )
        tts_service = self.config.get(CONF_TTS_SERVICE)

        if not tts_service:
            _LOGGER.warning(
                "Unmapped tag scanned: %s. No TTS service configured.", self.last_tag
            )
            return

        _LOGGER.warning(
            "Unmapped tag scanned: %s. Announcing via %s: %s",
            self.last_tag,
            tts_service,
            message,
        )
        domain, service = tts_service.split(".")
        await self.hass.services.async_call(
            domain,
            service,
            {
                "entity_id": self.config[CONF_MEDIA_PLAYER],
                "message": message,
            },
            blocking=True,
        )

    async def async_map_tag(self, tag_id: str, playlist_name: str):
        """Map a tag to a playlist and save it."""
        from .helpers import save_mappings

        if not tag_id or not playlist_name:
            _LOGGER.error(
                "Cannot map tag. Tag ID or Playlist Name is missing. Tag: '%s', Playlist: '%s'",
                tag_id,
                playlist_name,
            )
            return

        _LOGGER.info("Mapping tag '%s' to playlist '%s'", tag_id, playlist_name)
        self.mappings[tag_id] = playlist_name

        mapping_file = self.hass.config.path(DEFAULT_MAPPING_FILE_PATH)
        await self.hass.async_add_executor_job(
            save_mappings, self.hass, mapping_file, self.mappings
        )

    async def async_map_tag_service(self, service_call):
        """Handle the map_tag service call."""
        tag_id = service_call.data.get("tag_id")
        playlist_name = service_call.data.get("playlist_name")
        await self.async_map_tag(tag_id, playlist_name)

    async def async_reload_mappings_service(self, service_call):
        """Handle the reload_mappings service call."""
        from .helpers import load_mappings

        _LOGGER.info("Reloading mappings from file")
        mapping_file = self.hass.config.path(DEFAULT_MAPPING_FILE_PATH)
        self.mappings = await self.hass.async_add_executor_job(
            load_mappings, self.hass, mapping_file
        )

    async def async_map_tag_from_ui(self):
        """Map the last scanned tag to the playlist name from the text input."""
        last_tag_entity_id = f"sensor.{DOMAIN}_last_tag"
        playlist_text_entity_id = f"text.{DOMAIN}_playlist_to_map"

        last_tag_state = self.hass.states.get(last_tag_entity_id)
        playlist_text_state = self.hass.states.get(playlist_text_entity_id)

        tag_id = last_tag_state.state if last_tag_state else None
        playlist_name = playlist_text_state.state if playlist_text_state else None

        await self.async_map_tag(tag_id, playlist_name)