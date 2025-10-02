from app.config import get_settings
from app.events import OrderCreatedEvent, parse_order_event
from app.redis_client import create_redis_client


def process_event(event: OrderCreatedEvent) -> None:
    if event.event_type != "order.created":
        print(f"Skipping unsupported event_type={event.event_type}")
        return

    # Placeholder for notification dispatch and persistence logic.
    print(
        "Processed order.created "
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
