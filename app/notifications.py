from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Order

NOTIFICATION_STATUS_PENDING = "pending"
NOTIFICATION_STATUS_RETRYING = "retrying"
NOTIFICATION_STATUS_SENT = "sent"
NOTIFICATION_STATUS_FAILED = "failed"
MAX_ERROR_LENGTH = 255


def mark_notification_sent(db: Session, order: Order) -> None:
    if order.notification_status == NOTIFICATION_STATUS_SENT:
        return

    order.notification_status = NOTIFICATION_STATUS_SENT
    order.notification_attempts = max(0, order.notification_attempts) + 1
    order.notification_last_error = None
    order.notification_last_attempt_at = datetime.now(timezone.utc)
    db.add(order)


def mark_notification_error(
    db: Session,
    order: Order,
    *,
    status: str,
    attempts: int,
    error_message: str,
) -> None:
    order.notification_status = status
    order.notification_attempts = attempts
    order.notification_last_error = error_message[:MAX_ERROR_LENGTH]
    order.notification_last_attempt_at = datetime.now(timezone.utc)
    db.add(order)
