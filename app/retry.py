import json
import time

from app.events import OrderCreatedEvent, parse_order_event

BASE_RETRY_SECONDS = 5
RETRY_MULTIPLIER = 3


def compute_backoff_seconds(attempt_number: int) -> int:
    normalized_attempt = max(1, attempt_number)
    return BASE_RETRY_SECONDS * (RETRY_MULTIPLIER ** (normalized_attempt - 1))


def compute_next_retry_epoch(attempt_number: int, *, now_epoch: float | None = None) -> float:
    now = time.time() if now_epoch is None else now_epoch
    return now + float(compute_backoff_seconds(attempt_number))


def status_for_attempt(attempt_number: int, max_attempts: int) -> str:
    if attempt_number >= max_attempts:
        return "failed"
    return "retrying"


def encode_retry_member(event: OrderCreatedEvent) -> str:
    return json.dumps(event.to_payload(), sort_keys=True)


def decode_retry_member(member: str) -> OrderCreatedEvent:
    payload = json.loads(member)
    if not isinstance(payload, dict):
        raise ValueError("Retry member payload must be an object")
    normalized: dict[str, str] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise ValueError("Retry member key must be string")
        if not isinstance(value, str):
            raise ValueError("Retry member value must be string")
        normalized[key] = value
    return parse_order_event(normalized)
