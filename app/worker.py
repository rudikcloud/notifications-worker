from dataclasses import replace
from datetime import datetime, timezone
import time

from redis import Redis
from sqlalchemy import select

from app.config import Settings, get_settings
from app.database import SessionLocal
from app.events import OrderCreatedEvent, parse_order_event
from app.models import Order
from app.notifications import mark_notification_error, mark_notification_sent
from app.redis_client import create_redis_client
from app.retry import (
    compute_next_retry_epoch,
    decode_retry_member,
    encode_retry_member,
)
from app.sender import send_notification


def schedule_retry(redis_client: Redis, settings: Settings, event: OrderCreatedEvent) -> None:
    next_retry_epoch = compute_next_retry_epoch(event.attempts)
    member = encode_retry_member(event)
    redis_client.zadd(settings.orders_retry_zset, {member: next_retry_epoch})


def push_to_dlq(
    redis_client: Redis,
    settings: Settings,
    event: OrderCreatedEvent,
    *,
    attempts: int,
    error_message: str,
) -> None:
    payload = event.to_payload()
    payload["attempts"] = str(attempts)
    payload["error"] = error_message[:255]
    payload["failed_at"] = datetime.now(timezone.utc).isoformat()
    redis_client.xadd(settings.orders_dlq_stream, payload)


def process_event(event: OrderCreatedEvent, redis_client: Redis, settings: Settings) -> None:
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

        try:
            send_notification(event, settings)
            mark_notification_sent(db, order)
            db.commit()
        except Exception as exc:
            attempt_number = max(order.notification_attempts, event.attempts) + 1
            if attempt_number >= settings.max_attempts:
                mark_notification_error(
                    db,
                    order,
                    status="failed",
                    attempts=attempt_number,
                    error_message=str(exc),
                )
                db.commit()
                push_to_dlq(
                    redis_client,
                    settings,
                    event,
                    attempts=attempt_number,
                    error_message=str(exc),
                )
                print(
                    f"Notification permanently failed order_id={event.order_id} "
                    f"attempt={attempt_number}"
                )
                return

            retry_event = replace(event, attempts=attempt_number)
            mark_notification_error(
                db,
                order,
                status="retrying",
                attempts=attempt_number,
                error_message=str(exc),
            )
            db.commit()
            schedule_retry(redis_client, settings, retry_event)
            print(
                f"Notification failed; scheduled retry order_id={event.order_id} "
                f"attempt={attempt_number}"
            )
            return

    print(
        "Notification sent "
        f"order_id={event.order_id} user_id={event.user_id} created_at={event.created_at}"
    )


def process_due_retries(redis_client: Redis, settings: Settings) -> None:
    due_members = redis_client.zrangebyscore(
        settings.orders_retry_zset,
        min="-inf",
        max=time.time(),
        start=0,
        num=50,
    )
    for member in due_members:
        removed = redis_client.zrem(settings.orders_retry_zset, member)
        if removed == 0:
            continue
        try:
            retry_event = decode_retry_member(member)
        except ValueError as exc:
            print(f"Dropping invalid retry payload: {exc}")
            continue
        process_event(retry_event, redis_client, settings)


def run() -> None:
    settings = get_settings()
    redis_client = create_redis_client(settings)
    last_id = "$"

    print(
        "notifications-worker started "
        f"(stream={settings.orders_events_stream}, retry_zset={settings.orders_retry_zset}, dlq={settings.orders_dlq_stream})"
    )

    while True:
        process_due_retries(redis_client, settings)

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
                process_event(event, redis_client, settings)


if __name__ == "__main__":
    run()
