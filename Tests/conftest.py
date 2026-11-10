"""Keep the test suite away from the real ~/.facelock data directory."""

import pytest


@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path_factory, monkeypatch):
    monkeypatch.setenv("FACELOCK_DATA_DIR", str(tmp_path_factory.mktemp("facelock-data")))
