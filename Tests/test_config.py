"""Unit tests for configuration system."""

from pathlib import Path
from Core.config.settings import SystemSettings, CameraSettings, SecuritySettings
from Core.config.loader import ConfigLoader


def test_default_settings():
    settings = SystemSettings()
    assert settings.db_name == "facelock.db"
    assert settings.camera.frame_width == 1280
    assert settings.security.matching_threshold == 0.40


def test_config_loader_save_load(tmp_path: Path):
    config_file = tmp_path / "config.json"
    loader = ConfigLoader(config_file)

    settings = SystemSettings(
        data_dir=tmp_path,
        camera=CameraSettings(frame_width=1280, frame_height=720),
        security=SecuritySettings(matching_threshold=0.75),
    )

    saved = loader.save(settings)
    assert saved is True
    assert config_file.exists()

    loaded_settings = loader.load()
    assert loaded_settings.camera.frame_width == 1280
    assert loaded_settings.security.matching_threshold == 0.75
