"""Helper functions for the RFID Jukebox integration."""
import logging
import os
import tempfile
from typing import Dict

import yaml
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


def load_mappings(hass: HomeAssistant, file_path: str) -> Dict[str, Dict[str, str]]:
    """Load tag mappings from a YAML file."""
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


def save_mappings(hass: HomeAssistant, file_path: str, mappings: Dict[str, Dict[str, str]]) -> None:
    """Save tag mappings to a YAML file atomically."""
    try:
        dir_name = os.path.dirname(file_path) or "."
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=dir_name, delete=False, suffix=".tmp"
        ) as tmp_file:
            yaml.dump(mappings, tmp_file, default_flow_style=False)
            tmp_path = tmp_file.name
        os.replace(tmp_path, file_path)
        _LOGGER.info("Saved %d mappings to %s", len(mappings), file_path)
    except (OSError, yaml.YAMLError) as e:
        _LOGGER.error("Error saving mapping file %s: %s", file_path, e)