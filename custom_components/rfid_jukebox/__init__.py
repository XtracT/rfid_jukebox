"""The RFID Jukebox integration."""
import logging
import os
from typing import Optional
from urllib.parse import quote

from homeassistant.components import media_source
from homeassistant.components.media_player import (
    async_process_play_media_url,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import event
from homeassistant.helpers.network import get_url

from .const import (
    DOMAIN,
    CONF_TAG_SENSOR,
    CONF_MEDIA_PLAYER,
    CONF_MUSIC_DIR,
    DEFAULT_MAPPING_FILE_PATH,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RFID Jukebox from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    jukebox = RFIDJukebox(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = jukebox

    await jukebox.async_setup()

    await hass.config_entries.async_forward_entry_setups(entry, ["text", "button"])

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["text", "button"]
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
        self.text_entity = None
        self.playlist_to_map = ""
        self.last_played_playlist_name = None
        self.track_queue = []
        self.current_track_index = -1

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
        self.entry.async_on_unload(
            event.async_track_state_change_event(
                self.hass,
                self.config[CONF_MEDIA_PLAYER],
                self.async_player_changed_handler,
            )
        )

        # Register services
        self.hass.services.async_register(
            DOMAIN, "map_tag", self.async_map_tag_service
        )
        self.hass.services.async_register(
            DOMAIN, "next_track", self.async_next_track_service
        )
        self.hass.services.async_register(
            DOMAIN, "previous_track", self.async_previous_track_service
        )
        self.hass.services.async_register(
            DOMAIN, "stop", self.async_stop_service
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
                if self.text_entity:
                    if new_tag in self.mappings:
                        self.text_entity.update_value(self.mappings[new_tag])
                    else:
                        self.text_entity.update_value(new_tag)

            # If it's the same tag that was just playing, resume.
            if self.current_tag == new_tag:
                await self.async_play()
            # Otherwise, it's a new playlist.
            else:
                self.current_tag = new_tag
                if new_tag in self.mappings:
                    await self.async_play_folder(self.mappings[new_tag])
                else:
                    _LOGGER.warning("Unmapped tag scanned: %s", new_tag)
        # Tag is removed
        else:
            if self.current_tag:
                await self.async_pause()
                # We don't clear current_tag here, so we can resume it later

    async def async_play_folder(self, folder_name: str):
        """Play a folder of music asynchronously."""
        _LOGGER.info("Playing folder '%s'", folder_name)
        music_dir = self.config[CONF_MUSIC_DIR]
        folder_path = os.path.join(music_dir, folder_name)

        try:
            self.track_queue = await self.hass.async_add_executor_job(
                self._scan_folder_sync, folder_path
            )
        except Exception as e:
            _LOGGER.error("Error scanning folder '%s': %s", folder_path, e)
            self.track_queue = None

        if self.track_queue is None:
            _LOGGER.error("Folder '%s' not found in '%s'", folder_name, music_dir)
            return

        if not self.track_queue:
            _LOGGER.warning("No playable media found in folder '%s'", folder_name)
            return

        # Start playback from the first track
        self.current_track_index = 0
        await self.async_play_current_track()

    def _scan_folder_sync(self, folder_path: str) -> Optional[list[str]]:
        """Scan a folder for playable media (synchronous)."""
        if not os.path.isdir(folder_path):
            return None

        # Scan the folder for playable media files
        return sorted([
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.endswith((".mp3", ".wav", ".flac"))
        ])

    async def async_play_current_track(self):
        """Play the current track in the queue."""
        media_url = self._get_media_source_url(self.track_queue[self.current_track_index])
        if media_url:
            # Call the media_player.play_media service to play the track
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": self.config[CONF_MEDIA_PLAYER],
                    "media_content_id": media_url,
                    "media_content_type": "music",
                },
                blocking=True,
            )

    def _get_media_source_url(self, media_path: str) -> Optional[str]:
        """Get the media source URL for a given media path."""
        try:
            base_url = get_url(self.hass)
            if "/www/" in media_path:
                relative_path = media_path.split("/www/", 1)[1]

                # URL encode each part of the path to handle special characters
                encoded_path_parts = [quote(part) for part in relative_path.split("/")]
                encoded_relative_path = "/".join(encoded_path_parts)

                url = f"{base_url}/local/{encoded_relative_path}"
                _LOGGER.debug("Constructed media URL: %s", url)
                return url
            else:
                _LOGGER.error(
                    "Media path is not in the 'www' directory: %s", media_path
                )
                return None
        except Exception as e:
            _LOGGER.error("Error getting media source URL for '%s': %s", media_path, e)
            return None

    async def async_play(self):
        """Resume playback on the media player."""
        _LOGGER.info("Resuming playback")
        await self.hass.services.async_call(
            "media_player",
            "media_play",
            {"entity_id": self.config[CONF_MEDIA_PLAYER]},
            blocking=True,
        )

    async def async_pause(self):
        """Pause the media player."""
        _LOGGER.info("Pausing player")
        await self.hass.services.async_call(
            "media_player",
            "media_pause",
            {"entity_id": self.config[CONF_MEDIA_PLAYER]},
            blocking=True,
        )

    async def async_next_track(self):
        """Play the next track in the queue."""
        if self.current_track_index < len(self.track_queue) - 1:
            self.current_track_index += 1
            await self.async_play_current_track()

    async def async_previous_track(self):
        """Play the previous track in the queue."""
        if self.current_track_index > 0:
            self.current_track_index -= 1
            await self.async_play_current_track()

    async def async_stop(self):
        """Stop the media player."""
        _LOGGER.info("Stopping player")
        await self.hass.services.async_call(
            "media_player",
            "media_stop",
            {"entity_id": self.config[CONF_MEDIA_PLAYER]},
            blocking=True,
        )

    async def async_map_tag(self, tag_id: str, folder_name: str):
        """Map a tag to a folder and save it."""
        from .helpers import save_mappings

        if not tag_id or not folder_name:
            _LOGGER.error(
                "Cannot map tag. Tag ID or Folder Name is missing. Tag: '%s', Folder: '%s'",
                tag_id,
                folder_name,
            )
            return

        _LOGGER.info("Mapping tag '%s' to folder '%s'", tag_id, folder_name)
        self.mappings[tag_id] = folder_name

        mapping_file = self.hass.config.path(DEFAULT_MAPPING_FILE_PATH)
        await self.hass.async_add_executor_job(
            save_mappings, self.hass, mapping_file, self.mappings
        )

    async def async_map_tag_service(self, service_call):
        """Handle the map_tag service call."""
        tag_id = service_call.data.get("tag_id")
        folder_name = service_call.data.get("folder_name")
        await self.async_map_tag(tag_id, folder_name)

    async def async_player_changed_handler(self, event_data):
        """Handle media player state changes for track advancement."""
        old_state = event_data.data.get("old_state")
        new_state = event_data.data.get("new_state")

        if not old_state or not new_state:
            return

        # If player state changes from 'playing' to 'idle', play next track
        if (
            old_state.state == "playing"
            and new_state.state == "idle"
            and self.track_queue
            and self.current_track_index < len(self.track_queue) - 1
        ):
            _LOGGER.debug("Track finished, playing next one.")
            await self.async_next_track()
        elif new_state.state == "idle" and self.track_queue and self.current_track_index >= len(self.track_queue) - 1:
            _LOGGER.info("Last track in folder finished.")
            self.current_tag = None
            self.track_queue = []
            self.current_track_index = -1


    async def async_next_track_service(self, service_call):
        """Handle the next_track service call."""
        await self.async_next_track()

    async def async_previous_track_service(self, service_call):
        """Handle the previous_track service call."""
        await self.async_previous_track()

    async def async_stop_service(self, service_call):
        """Handle the stop service call."""
        await self.async_stop()


    async def async_map_tag_from_ui(self):
        """Map the last scanned tag to the folder name from the text input."""
        folder_text_entity_id = f"text.{DOMAIN}_folder_to_map"
        folder_text_state = self.hass.states.get(folder_text_entity_id)

        tag_id = self.last_tag
        folder_name = folder_text_state.state if folder_text_state else None

        await self.async_map_tag(tag_id, folder_name)