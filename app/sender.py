import random

from app.config import Settings
from app.events import OrderCreatedEvent


def send_notification(event: OrderCreatedEvent, settings: Settings) -> None:
    fail_mode = settings.fail_mode
    if fail_mode == "off":
        return
    if fail_mode == "always":
        raise RuntimeError("Simulated notification failure (always mode)")
    if fail_mode == "random":
        if random.random() < 0.3:
            raise RuntimeError("Simulated notification failure (random mode)")
        return

    print(f"Unknown FAIL_MODE={fail_mode}; defaulting to off")
    _ = event
