#!/usr/bin/env python3
"""Download and verify the FaceLock ONNX models (YuNet detector, SFace recognizer)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Core.models import MODELS, ModelUnavailableError, fetch_model, model_path  # noqa: E402


def main() -> int:
    status = 0
    for name in MODELS:
        try:
            path = model_path(name, download=False)
            print(f"ok       {name}: {path}")
        except ModelUnavailableError:
            try:
                print(f"fetched  {name}: {fetch_model(name)}")
            except ModelUnavailableError as exc:
                print(f"FAILED   {name}: {exc}")
                status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
