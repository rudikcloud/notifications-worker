from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    notification_status: Mapped[str] = mapped_column(String(16), nullable=False)
    notification_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notification_last_error: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notification_last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
