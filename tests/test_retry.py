from app.retry import (
    compute_backoff_seconds,
    compute_next_retry_epoch,
    status_for_attempt,
)


def test_compute_backoff_seconds_exponential() -> None:
    assert compute_backoff_seconds(1) == 5
    assert compute_backoff_seconds(2) == 15
    assert compute_backoff_seconds(3) == 45
    assert compute_backoff_seconds(4) == 135


def test_compute_next_retry_epoch_uses_backoff() -> None:
    base_epoch = 1_700_000_000.0
    assert compute_next_retry_epoch(1, now_epoch=base_epoch) == base_epoch + 5.0
    assert compute_next_retry_epoch(3, now_epoch=base_epoch) == base_epoch + 45.0


def test_status_for_attempt_transitions() -> None:
    assert status_for_attempt(1, 5) == "retrying"
    assert status_for_attempt(4, 5) == "retrying"
    assert status_for_attempt(5, 5) == "failed"
    assert status_for_attempt(7, 5) == "failed"
