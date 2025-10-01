# notifications-worker

Python worker service for RudikCloud Milestone 4.

## Scope (stub)

- Read order events from Redis (`orders.events` by default)
- Process notifications for orders
- Update order notification status in Postgres
- Handle retries and dead-letter queue (DLQ)

## Environment variables

- `DATABASE_URL`
- `REDIS_URL`
- `ORDERS_EVENTS_STREAM`
- `ORDERS_RETRY_ZSET`
- `ORDERS_DLQ_STREAM`
- `MAX_ATTEMPTS`
- `WORKER_POLL_INTERVAL_MS`
- `FAIL_MODE`

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.worker
```
