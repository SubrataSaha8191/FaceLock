"""Unit tests for structured audit logger."""

import json
from pathlib import Path
from Core.utils.audit_logger import AuditLogger


def test_audit_log_event(tmp_path: Path):
    log_file = tmp_path / "test_audit.log"
    audit = AuditLogger(log_file)

    audit.log_event("TEST_EVENT", user_id="usr_1", success=True, details={"key": "value"})
    assert log_file.exists()

    content = log_file.read_text().strip()
    record = json.loads(content)
    assert record["event"] == "TEST_EVENT"
    assert record["user_id"] == "usr_1"
    assert record["success"] is True
    assert record["details"]["key"] == "value"


def test_audit_enrollment_log(tmp_path: Path):
    audit = AuditLogger(tmp_path / "audit.log")
    audit.log_enrollment("usr_2", success=True)
    content = (tmp_path / "audit.log").read_text().strip()
    record = json.loads(content)
    assert record["event"] == "ENROLLMENT"


def test_audit_auth_attempt_log(tmp_path: Path):
    audit = AuditLogger(tmp_path / "audit.log")
    audit.log_auth_attempt("usr_3", success=False, similarity=0.45)
    content = (tmp_path / "audit.log").read_text().strip()
    record = json.loads(content)
    assert record["event"] == "AUTH_ATTEMPT"
    assert record["details"]["similarity"] == 0.45


def test_audit_lockout_log(tmp_path: Path):
    audit = AuditLogger(tmp_path / "audit.log")
    audit.log_lockout("usr_4")
    content = (tmp_path / "audit.log").read_text().strip()
    record = json.loads(content)
    assert record["event"] == "LOCKOUT"
    assert record["success"] is False
