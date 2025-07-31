"""Helper functions for the RFID Jukebox integration."""
import logging
from typing import Dict

import yaml
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


def load_mappings(hass: HomeAssistant, file_path: str) -> Dict[str, str]:
    """Load tag-to-playlist mappings from a YAML file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            mappings = yaml.safe_load(f)
            if isinstance(mappings, dict):
                _LOGGER.info("Loaded %d mappings from %s", len(mappings), file_path)
                return mappings
            _LOGGER.warning("Mapping file %s is not a valid dictionary.", file_path)
            return {}
    except FileNotFoundError:
        _LOGGER.debug("Mapping file not found at %s, starting with empty map.", file_path)
        return {}
    except yaml.YAMLError as e:
        _LOGGER.error("Error reading mapping file %s: %s", file_path, e)
        return {}


def save_mappings(hass: HomeAssistant, file_path: str, mappings: Dict[str, str]) -> None:
    """Save tag-to-playlist mappings to a YAML file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(mappings, f)
            _LOGGER.info("Saved %d mappings to %s", len(mappings), file_path)
    except Exception as e:
        _LOGGER.error("Error saving mapping file %s: %s", file_path, e)