"""Configuration file loader and saver."""

import json
from pathlib import Path
from typing import Optional

from Core.config.settings import CONFIG_VERSION, SecuritySettings, SystemSettings, get_default_data_dir


class ConfigLoader:
    """Handles loading and persisting SystemSettings to disk."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = get_default_data_dir() / "config.json"
        self.config_path = config_path

    def load(self) -> SystemSettings:
        """Load settings from JSON file or return defaults if missing."""
        if not self.config_path.exists():
            settings = SystemSettings()
            self.save(settings)
            return settings

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            migrated = int(data.get("config_version", 1)) < CONFIG_VERSION
            settings = SystemSettings.model_validate(data)
            if migrated:
                # Version-1 configs tuned the threshold for the old thumbnail matcher
                # (~0.6). That scale is meaningless for SFace embeddings and would
                # reject nearly everyone, so reset it to the new default.
                settings.security.matching_threshold = SecuritySettings().matching_threshold
                settings.camera.frame_width = max(settings.camera.frame_width, 1280)
                settings.camera.frame_height = max(settings.camera.frame_height, 720)
                settings.config_version = CONFIG_VERSION
                self.save(settings)
            return settings
        except Exception:
            return SystemSettings()

    def save(self, settings: SystemSettings) -> bool:
        """Save SystemSettings instance to JSON file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(settings.model_dump_json(indent=2))
            return True
        except Exception:
            return False
