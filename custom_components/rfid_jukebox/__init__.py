"""The RFID Jukebox integration."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import event
from homeassistant.const import STATE_PLAYING, STATE_PAUSED, Platform

from .const import (
    DOMAIN,
    CONF_TAG_SENSOR,
    CONF_MEDIA_PLAYER,
    CONF_MA_FILESYSTEM,
    DEFAULT_MAPPING_FILE_PATH,
)
from .helpers import load_mappings, save_mappings

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.TEXT, Platform.BUTTON, Platform.SELECT]


def _resolve_mapping(mapping):
    """Normalise a mapping entry to (media_type, media_name).

    Handles both the modern dict format::

        {"type": "playlist", "name": "Kids Party Time", "alias": "..."}

    and the legacy plain-string format.
    """
    if isinstance(mapping, dict):
        return (
            mapping.get("type", "playlist"),
            mapping.get("name"),
            mapping.get("alias"),
        )
    # legacy plain string mapping
    return ("playlist", mapping, None)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RFID Jukebox from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    jukebox = RFIDJukebox(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = jukebox

    await jukebox.async_setup()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    _maybe_register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _maybe_remove_services(hass)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


# ---------------------------------------------------------------------------
# Service helpers – register once globally and clean up when the last entry
# is removed so reloads don't leak duplicate handlers.
# ---------------------------------------------------------------------------
_SERVICE_REGISTERED = f"{DOMAIN}_service_registered"


def _maybe_register_services(hass: HomeAssistant) -> None:
    """Register domain-wide services if not already done."""
    if hass.data[DOMAIN].get(_SERVICE_REGISTERED):
        return

    async def _map_tag_service(call):
        tag_id = call.data.get("tag_id")
        media_type = call.data.get("media_type", "playlist")
        media_name = call.data.get("media_name")
        alias = call.data.get("alias")
        # Dispatch to the first available jukebox instance (typical single-instance setup)
        for jukebox in hass.data[DOMAIN].values():
            if isinstance(jukebox, RFIDJukebox):
                await jukebox.async_map_tag(tag_id, media_type, media_name, alias)
                return
        _LOGGER.error("No RFIDJukebox instance found to handle map_tag service")

    hass.services.async_register(DOMAIN, "map_tag", _map_tag_service)
    hass.data[DOMAIN][_SERVICE_REGISTERED] = True


def _maybe_remove_services(hass: HomeAssistant) -> None:
    """Remove domain-wide services when the last config entry is gone."""
    if len(hass.data[DOMAIN]) <= 1:  # 1 because _SERVICE_REGISTERED key remains
        hass.services.async_remove(DOMAIN, "map_tag")
        hass.data[DOMAIN].pop(_SERVICE_REGISTERED, None)


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

    async def async_setup(self):
        """Set up the jukebox."""
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
                        media_type = mapping.get("type", "playlist")
                        media_name = mapping.get("name", "")
                        alias = mapping.get("alias", new_tag)
                    else:  # Handle old, simple mapping format
                        media_type = "playlist"
                        media_name = mapping
                        alias = new_tag
                    if self.text_entity:
                        self.text_entity.update_value(media_name)
                    if self.alias_entity:
                        self.alias_entity.update_value(alias)
                    if self.media_type_entity:
                        self.media_type_entity.update_option(media_type)
                else:  # Unmapped tag, clear the fields
                    if self.text_entity:
                        self.text_entity.update_value("")
                    if self.alias_entity:
                        self.alias_entity.update_value("")
                    if self.media_type_entity:
                        self.media_type_entity.update_option("folder")

            # If it's the same tag, decide whether to resume or restart.
            if self.current_tag == new_tag:
                media_player_entity_id = self.config[CONF_MEDIA_PLAYER]
                media_player_state = self.hass.states.get(media_player_entity_id)

                if media_player_state and media_player_state.state == STATE_PAUSED:
                    await self.async_resume_playback()
                else:
                    # If the player is idle, off, or in any other state,
                    # treat it as a new request to play from the beginning.
                    _LOGGER.info(
                        "Player is not paused, restarting media for tag %s", new_tag
                    )
                    if new_tag in self.mappings:
                        media_type, media_name, _ = _resolve_mapping(
                            self.mappings[new_tag]
                        )
                        if media_name:
                            if media_type == "folder":
                                await self.async_start_new_folder(media_name)
                            else:
                                await self.async_start_new_playlist(media_name)
            # Otherwise, it's a new media.
            else:
                self.current_tag = new_tag
                if new_tag in self.mappings:
                    media_type, media_name, _ = _resolve_mapping(
                        self.mappings[new_tag]
                    )

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
                media_player_entity_id = self.config[CONF_MEDIA_PLAYER]
                media_player_state = self.hass.states.get(media_player_entity_id)

                # Only pause if the player is currently playing
                if media_player_state and media_player_state.state == STATE_PLAYING:
                    await self.async_pause_player()
                # We don't clear current_tag here, so we can resume it later

    async def async_start_new_playlist(self, playlist_name: str):
        """Start a new playlist from the beginning."""
        _LOGGER.info("Starting new playlist '%s'", playlist_name)

        try:
            service_data = {
                "entity_id": self.config[CONF_MEDIA_PLAYER],
                "media_id": playlist_name,
                "media_type": "playlist",
            }
            _LOGGER.debug(
                "Calling music_assistant.play_media with data: %s", service_data
            )
            await self.hass.services.async_call(
                "music_assistant",
                "play_media",
                service_data,
                blocking=True,
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error(
                "Error playing playlist '%s': %s. "
                "Please ensure the playlist name is spelled correctly and exists in Music Assistant.",
                playlist_name,
                err,
            )

    async def async_start_new_folder(self, folder_name: str):
        """Play a Music Assistant folder now (hardcoded filesystem + device)."""
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
            _LOGGER.debug(
                "Calling music_assistant.play_media with data: %s", service_data
            )
            await self.hass.services.async_call(
                "music_assistant",
                "play_media",
                service_data,
                blocking=True,
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("MA folder play failed (%s): %s", media_id, err)

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
