from dataclasses import dataclass


@dataclass(frozen=True)
class OrderCreatedEvent:
    event_type: str
    order_id: str
    user_id: str
    created_at: str
    checkout_variant: str | None = None
    attempts: int = 0

    def to_payload(self) -> dict[str, str]:
        payload: dict[str, str] = {
            "event_type": self.event_type,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "attempts": str(self.attempts),
        }
        if self.checkout_variant is not None:
            payload["checkout_variant"] = self.checkout_variant
        return payload


def parse_order_event(payload: dict[str, str]) -> OrderCreatedEvent:
    event_type = payload.get("event_type")
    order_id = payload.get("order_id")
    user_id = payload.get("user_id")
    created_at = payload.get("created_at")

    if not event_type or not order_id or not user_id or not created_at:
        raise ValueError("Event payload missing required fields")

    attempts_raw = payload.get("attempts", "0")
    try:
        attempts = int(attempts_raw)
    except ValueError as exc:
        raise ValueError("Invalid attempts in payload") from exc

    return OrderCreatedEvent(
        event_type=event_type,
        order_id=order_id,
        user_id=user_id,
        created_at=created_at,
        checkout_variant=payload.get("checkout_variant"),
        attempts=max(0, attempts),
    )
