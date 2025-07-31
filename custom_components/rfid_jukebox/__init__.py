"""The RFID Jukebox integration."""
import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery, event

from .const import (
    DOMAIN,
    CONF_TAG_SENSOR,
    CONF_MEDIA_PLAYER,
    CONF_MAPPING_FILE_PATH,
    CONF_UNMAPPED_TAG_TTS_MESSAGE,
    CONF_TTS_SERVICE,
    DEFAULT_MAPPING_FILE_PATH,
    DEFAULT_UNMAPPED_TAG_TTS_MESSAGE,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_TAG_SENSOR): cv.entity_id,
                vol.Required(CONF_MEDIA_PLAYER): cv.entity_id,
                vol.Optional(
                    CONF_MAPPING_FILE_PATH, default=DEFAULT_MAPPING_FILE_PATH
                ): cv.string,
                vol.Optional(
                    CONF_UNMAPPED_TAG_TTS_MESSAGE,
                    default=DEFAULT_UNMAPPED_TAG_TTS_MESSAGE,
                ): cv.string,
                vol.Optional(CONF_TTS_SERVICE): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the RFID Jukebox component from YAML configuration."""
    _LOGGER.info("Setting up RFID Jukebox from configuration.yaml")
    hass.data.setdefault(DOMAIN, {})

    if DOMAIN not in config:
        _LOGGER.debug("No configuration found for %s", DOMAIN)
        return True

    conf = config[DOMAIN]

    jukebox = RFIDJukebox(hass, conf)
    hass.data[DOMAIN] = jukebox

    await jukebox.async_setup()

    return True


class RFIDJukebox:
    """The main class for the RFID Jukebox integration."""

    def __init__(self, hass: HomeAssistant, config: dict):
        """Initialize the RFID Jukebox."""
        self.hass = hass
        self.config = config
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
        mapping_file = self.hass.config.path(self.config[CONF_MAPPING_FILE_PATH])
        self.mappings = await self.hass.async_add_executor_job(
            load_mappings, self.hass, mapping_file
        )

        # Set up platforms
        for platform in ["sensor", "text", "button"]:
            self.hass.async_create_task(
                discovery.async_load_platform(
                    self.hass, platform, DOMAIN, {}, self.config
                )
            )

        # Register state listener
        event.async_track_state_change_event(
            self.hass, self.config[CONF_TAG_SENSOR], self.async_tag_changed_handler
        )

        # Register services
        self.hass.services.async_register(
            DOMAIN, "map_tag", self.async_map_tag_service
        )
        self.hass.services.async_register(
            DOMAIN, "reload_mappings", self.async_reload_mappings_service
        )

    async def async_tag_changed_handler(self, event):
        """Handle state changes for the RFID tag sensor."""
        new_state = event.data.get("new_state")
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
        message = self.config[CONF_UNMAPPED_TAG_TTS_MESSAGE]
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

        mapping_file = self.hass.config.path(self.config[CONF_MAPPING_FILE_PATH])
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
        mapping_file = self.hass.config.path(self.config[CONF_MAPPING_FILE_PATH])
        self.mappings = await self.hass.async_add_executor_job(
            load_mappings, self.hass, mapping_file
        )

    async def async_map_tag_from_ui(self):
        """Map the last scanned tag to the playlist name from the text input."""
        # Fetch the current state directly from Home Assistant to avoid state sync issues
        last_tag_entity_id = f"sensor.{DOMAIN}_last_tag"
        playlist_text_entity_id = f"text.{DOMAIN}_playlist_to_map"

        last_tag_state = self.hass.states.get(last_tag_entity_id)
        playlist_text_state = self.hass.states.get(playlist_text_entity_id)

        tag_id = last_tag_state.state if last_tag_state else None
        playlist_name = playlist_text_state.state if playlist_text_state else None

        await self.async_map_tag(tag_id, playlist_name)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RFID Jukebox from a config entry."""
    # This will be used for UI-based configuration in the future.
    _LOGGER.info("Setting up RFID Jukebox from Config Entry")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This will be used for UI-based configuration in the future.
    _LOGGER.info("Unloading RFID Jukebox Config Entry")
    return True