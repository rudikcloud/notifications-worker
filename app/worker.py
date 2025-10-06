from datetime import datetime, timezone

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.events import OrderCreatedEvent, parse_order_event
from app.models import Order
from app.notifications import mark_notification_sent
from app.redis_client import create_redis_client


def process_event(event: OrderCreatedEvent) -> None:
    if event.event_type != "order.created":
        print(f"Skipping unsupported event_type={event.event_type}")
        return

    with SessionLocal() as db:
        statement = select(Order).where(Order.id == event.order_id)
        order = db.scalar(statement)
        if order is None:
            print(f"Order not found for event order_id={event.order_id}")
            return

        # Idempotency: if already sent, treat as success and skip re-send.
        if order.notification_status == "sent":
            print(f"Order already marked sent order_id={event.order_id}")
            return

        # Mock dispatch for now. Retry and failure simulation are added in later checkpoints.
        _ = datetime.now(timezone.utc)
        mark_notification_sent(db, order)
        db.commit()

    print(
        "Notification sent "
        f"order_id={event.order_id} user_id={event.user_id} created_at={event.created_at}"
    )


def run() -> None:
    settings = get_settings()
    redis_client = create_redis_client(settings)
    last_id = "$"

    print(
        "notifications-worker started "
        f"(stream={settings.orders_events_stream}, retry_zset={settings.orders_retry_zset}, dlq={settings.orders_dlq_stream})"
    )

    while True:
        records = redis_client.xread(
            streams={settings.orders_events_stream: last_id},
            count=10,
            block=settings.worker_poll_interval_ms,
        )
        if not records:
            continue

        for _, entries in records:
            for event_id, raw_payload in entries:
                last_id = event_id
                try:
                    event = parse_order_event(raw_payload)
                except ValueError as exc:
                    print(f"Skipping invalid event id={event_id}: {exc}")
                    continue
                process_event(event)


if __name__ == "__main__":
    run()
