"""Unit tests for PAM helper module functionality."""

from unittest.mock import patch, MagicMock
from Linux.pam.pam_facelock import _get_pam_user


def test_get_pam_user_from_env():
    """PAM user should be read from PAM_USER environment variable."""
    with patch.dict("os.environ", {"PAM_USER": "test_user"}):
        assert _get_pam_user() == "test_user"


def test_get_pam_user_fallback():
    """When PAM_USER is not set, fallback to getpass.getuser()."""
    with patch.dict("os.environ", {}, clear=True):
        with patch("getpass.getuser", return_value="fallback_user"):
            result = _get_pam_user()
            assert result == "fallback_user"
