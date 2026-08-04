"""Configuration file loader and saver."""

import json
from pathlib import Path
from typing import Optional

from Core.config.settings import SystemSettings


class ConfigLoader:
    """Handles loading and persisting SystemSettings to disk."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path.home() / ".facelock" / "config.json"
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
            return SystemSettings.model_validate(data)
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
