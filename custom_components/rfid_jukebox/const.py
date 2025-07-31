"""Constants for the RFID Jukebox integration."""

DOMAIN = "rfid_jukebox"

# Configuration keys
CONF_TAG_SENSOR = "tag_sensor"
CONF_MEDIA_PLAYER = "media_player"
CONF_MAPPING_FILE_PATH = "mapping_file_path"
CONF_UNMAPPED_TAG_TTS_MESSAGE = "unmapped_tag_tts_message"
CONF_TTS_SERVICE = "tts_service"

# Default values
DEFAULT_MAPPING_FILE_PATH = "rfid_mappings.yaml"
DEFAULT_UNMAPPED_TAG_TTS_MESSAGE = "This tag is not yet mapped to a playlist."