"""Locate (and if needed download) the ONNX models FaceLock depends on."""

import hashlib
import os
import urllib.request
from pathlib import Path
from typing import Dict

from Core.utils.logger import get_logger

logger = get_logger("Models")

_ZOO = "https://github.com/opencv/opencv_zoo/raw/main/models"

MODELS: Dict[str, Dict[str, str]] = {
    "yunet": {
        "file": "detection/face_detection_yunet_2023mar.onnx",
        "url": f"{_ZOO}/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
    },
    "sface": {
        "file": "recognition/face_recognition_sface_2021dec.onnx",
        "url": f"{_ZOO}/face_recognition_sface/face_recognition_sface_2021dec.onnx",
        "sha256": "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
    },
}


class ModelUnavailableError(RuntimeError):
    """Raised when a required model file is missing and cannot be downloaded."""


def models_dir() -> Path:
    override = os.environ.get("FACELOCK_MODELS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "Models"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def model_path(name: str, download: bool = True) -> Path:
    """Return the path of a model, downloading and verifying it when absent."""
    spec = MODELS[name]
    path = models_dir() / spec["file"]
    if path.is_file():
        return path
    if not download:
        raise ModelUnavailableError(f"Model '{name}' not found at {path}")
    return fetch_model(name)


def fetch_model(name: str) -> Path:
    """Download a model into the models directory and verify its checksum."""
    spec = MODELS[name]
    path = models_dir() / spec["file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    logger.info(f"Downloading model '{name}' from {spec['url']}")
    try:
        urllib.request.urlretrieve(spec["url"], tmp)
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        raise ModelUnavailableError(
            f"Could not download model '{name}': {exc}. "
            f"Run `python Scripts/fetch_models.py` while online, or copy the file to {path}."
        ) from exc
    digest = _sha256(tmp)
    if digest != spec["sha256"]:
        tmp.unlink(missing_ok=True)
        raise ModelUnavailableError(f"Checksum mismatch for model '{name}' ({digest}).")
    tmp.replace(path)
    return path
