"""The RFID Jukebox integration."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import event

from .const import (
    DOMAIN,
    CONF_TAG_SENSOR,
    CONF_MEDIA_PLAYER,
    CONF_MA_FILESYSTEM,
    DEFAULT_MAPPING_FILE_PATH,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RFID Jukebox from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    jukebox = RFIDJukebox(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = jukebox

    await jukebox.async_setup()

    await hass.config_entries.async_forward_entry_setups(entry, ["text", "button", "select"])

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["text", "button", "select"]
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
        self.alias_entity = None
        self.media_type_entity = None
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
                if new_tag in self.mappings:
                    mapping = self.mappings[new_tag]
                    if isinstance(mapping, dict):
                        alias = mapping.get("alias", new_tag)
                        media_type = mapping.get("type", "playlist")
                        media_name = mapping.get("name", "")
                        if self.text_entity:
                            self.text_entity.update_value(media_name)
                        if self.alias_entity:
                            self.alias_entity.update_value(alias)
                        if self.media_type_entity:
                            self.media_type_entity.update_option(media_type)
                    else:  # Handle old, simple mapping format
                        if self.text_entity:
                            self.text_entity.update_value(mapping)
                        if self.alias_entity:
                            self.alias_entity.update_value(new_tag)
                        if self.media_type_entity:
                            self.media_type_entity.update_option("playlist")
                else:  # Unmapped tag, clear the fields
                    if self.text_entity:
                        self.text_entity.update_value("")
                    if self.alias_entity:
                        self.alias_entity.update_value("")
                    if self.media_type_entity:
                        self.media_type_entity.update_option("playlist")

            # If it's the same tag that was just playing, resume.
            if self.current_tag == new_tag:
                await self.async_resume_playback()
            # Otherwise, it's a new media.
            else:
                self.current_tag = new_tag
                if new_tag in self.mappings:
                    mapping = self.mappings[new_tag]
                    if isinstance(mapping, dict):
                        media_type = mapping.get("type", "playlist")
                        media_name = mapping.get("name")
                    else:
                        media_type = "playlist"
                        media_name = mapping

                    if media_name:
                        if media_type == "folder":
                            await self.async_start_new_folder(media_name)
                        else:
                            await self.async_start_new_playlist(media_name)
                    else:
                        _LOGGER.warning("No media name found for tag: %s", new_tag)
                else:
                    _LOGGER.warning("Unmapped tag scanned: %s", new_tag)
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
            service_data = {
                "entity_id": self.config[CONF_MEDIA_PLAYER],
                "media_id": playlist_name,
                "media_type": "playlist",
            }
            _LOGGER.debug("Calling music_assistant.play_media with data: %s", service_data)
            await self.hass.services.async_call(
                "music_assistant",
                "play_media",
                service_data,
                blocking=True,
            )
        except HomeAssistantError as err:
            _LOGGER.error(
                "Error playing playlist '%s': %s. Please ensure the playlist name is spelled correctly and exists in Music Assistant.",
                playlist_name,
                err,
            )

    async def async_start_new_folder(self, folder_name: str):
        """HACK: play a Music Assistant folder now (hardcoded filesystem + device)."""
        from homeassistant.exceptions import HomeAssistantError

        filesystem = self.config.get(CONF_MA_FILESYSTEM)
        if not filesystem:
            _LOGGER.error("Music Assistant filesystem ID is not configured.")
            return

        # Build "<filesystem>://folder/<path>"
        path = str(folder_name).strip().lstrip("/\\").replace("\\", "/")
        media_id = f"{filesystem}://folder/{path}"
        _LOGGER.info("Starting new folder '%s'", media_id)
        try:
            service_data = {
                "entity_id": self.config[CONF_MEDIA_PLAYER],
                "media_id": media_id,
                "media_type": "folder",
            }
            _LOGGER.debug("Calling music_assistant.play_media with data: %s", service_data)
            await self.hass.services.async_call(
                "music_assistant",
                "play_media",
                service_data,
                blocking=True,
            )
        except HomeAssistantError as err:
            _logger = globals().get("_LOGGER")  # keep it simple for now
            if _logger:
                _logger.error("MA folder play failed (%s): %s", media_id, err)
            else:
                raise

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

    async def async_map_tag(self, tag_id: str, media_type: str, media_name: str, alias: str = None):
        """Map a tag to a media item and save it."""
        from .helpers import save_mappings

        if not tag_id or not media_name:
            _LOGGER.error(
                "Cannot map tag. Tag ID or Media Name is missing. Tag: '%s', Media: '%s'",
                tag_id,
                media_name,
            )
            return

        _LOGGER.info("Mapping tag '%s' to %s '%s'", tag_id, media_type, media_name)
        self.mappings[tag_id] = {
            "type": media_type,
            "name": media_name,
            "alias": alias or tag_id,
        }

        mapping_file = self.hass.config.path(DEFAULT_MAPPING_FILE_PATH)
        await self.hass.async_add_executor_job(
            save_mappings, self.hass, mapping_file, self.mappings
        )

    async def async_map_tag_service(self, service_call):
        """Handle the map_tag service call."""
        tag_id = service_call.data.get("tag_id")
        media_type = service_call.data.get("media_type", "playlist")
        media_name = service_call.data.get("media_name")
        alias = service_call.data.get("alias")
        await self.async_map_tag(tag_id, media_type, media_name, alias)


    async def async_map_tag_from_ui(self):
        """Map the last scanned tag from the UI."""
        # This will be updated in a future step to handle the new UI elements.
        pass