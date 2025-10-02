from dataclasses import dataclass


@dataclass(frozen=True)
class OrderCreatedEvent:
    event_type: str
    order_id: str
    user_id: str
    created_at: str
    checkout_variant: str | None = None


def parse_order_event(payload: dict[str, str]) -> OrderCreatedEvent:
    event_type = payload.get("event_type")
    order_id = payload.get("order_id")
    user_id = payload.get("user_id")
    created_at = payload.get("created_at")

    if not event_type or not order_id or not user_id or not created_at:
        raise ValueError("Event payload missing required fields")

    return OrderCreatedEvent(
        event_type=event_type,
        order_id=order_id,
        user_id=user_id,
        created_at=created_at,
        checkout_variant=payload.get("checkout_variant"),
    )
