from app.config import get_settings


def run() -> None:
    settings = get_settings()
    print(
        "notifications-worker started "
        f"(stream={settings.orders_events_stream}, retry_zset={settings.orders_retry_zset}, dlq={settings.orders_dlq_stream})"
    )


if __name__ == "__main__":
    run()
