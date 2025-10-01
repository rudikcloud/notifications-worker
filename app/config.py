from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    orders_events_stream: str
    orders_retry_zset: str
    orders_dlq_stream: str
    max_attempts: int
    worker_poll_interval_ms: int
    fail_mode: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql://rudik:rudik@localhost:5432/rudikcloud",
        ),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        orders_events_stream=os.getenv("ORDERS_EVENTS_STREAM", "orders.events"),
        orders_retry_zset=os.getenv("ORDERS_RETRY_ZSET", "orders.retry"),
        orders_dlq_stream=os.getenv("ORDERS_DLQ_STREAM", "orders.dlq"),
        max_attempts=int(os.getenv("MAX_ATTEMPTS", "5")),
        worker_poll_interval_ms=int(os.getenv("WORKER_POLL_INTERVAL_MS", "500")),
        fail_mode=os.getenv("FAIL_MODE", "off").strip().lower() or "off",
    )
