"""Unit tests for authentication attempt tracker and lockout."""

import time
from Core.authentication.attempt_tracker import AttemptTracker


def test_initial_state():
    tracker = AttemptTracker(max_attempts=3, lockout_seconds=60)
    assert tracker.is_locked("user1") is False
    assert tracker.get_remaining_attempts("user1") == 3


def test_record_failures_and_lockout():
    tracker = AttemptTracker(max_attempts=3, lockout_seconds=60)
    assert tracker.record_failure("user1") is False  # 1st fail
    assert tracker.record_failure("user1") is False  # 2nd fail
    assert tracker.record_failure("user1") is True   # 3rd fail -> locked
    assert tracker.is_locked("user1") is True
    assert tracker.get_remaining_attempts("user1") == 0


def test_success_resets_counter():
    tracker = AttemptTracker(max_attempts=3, lockout_seconds=60)
    tracker.record_failure("user1")
    tracker.record_failure("user1")
    tracker.record_success("user1")
    assert tracker.get_remaining_attempts("user1") == 3
    assert tracker.is_locked("user1") is False


def test_lockout_expires():
    tracker = AttemptTracker(max_attempts=2, lockout_seconds=1)
    tracker.record_failure("user1")
    tracker.record_failure("user1")
    assert tracker.is_locked("user1") is True
    time.sleep(1.1)
    assert tracker.is_locked("user1") is False
    assert tracker.get_remaining_attempts("user1") == 2


def test_independent_users():
    tracker = AttemptTracker(max_attempts=2, lockout_seconds=60)
    tracker.record_failure("user_a")
    tracker.record_failure("user_a")
    assert tracker.is_locked("user_a") is True
    assert tracker.is_locked("user_b") is False
