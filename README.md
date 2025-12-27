[![CI](https://github.com/rudikcloud/notifications-worker/actions/workflows/ci.yml/badge.svg)](https://github.com/rudikcloud/notifications-worker/actions/workflows/ci.yml)

# notifications-worker

`notifications-worker` is the asynchronous reliability component in RudikCloud. It consumes order events, attempts notification delivery, updates order status, retries with backoff, and dead-letters exhausted events.

## Queue and Retry Model

- Input stream: `orders.events` (Redis Stream)
- Retry queue: `orders.retry` (Redis ZSET, score = next retry epoch)
- Dead letter queue: `orders.dlq` (Redis Stream)

## What It Updates on Orders

For each processed order, worker updates:

- `notification_status` in `{pending, retrying, sent, failed}`
- `notification_attempts`
- `notification_last_error` (nullable)
- `notification_last_attempt_at` (nullable)

Idempotency: if an order is already `sent`, it is not sent again.

## Retry Policy and Failure Modes

- Exponential backoff between attempts.
- Max attempts controlled by `MAX_ATTEMPTS`.
- When attempts exceed max, payload is pushed to DLQ and order is marked `failed`.

Failure simulation (`FAIL_MODE`):

- `off`: normal behavior
- `always`: every send attempt fails
- `random`: approximately 30% attempts fail

## Environment Variables

Copy `.env.example` to `.env` for local runs.

- `DATABASE_URL`: Postgres connection string.
- `REDIS_URL`: Redis connection string.
- `ORDERS_EVENTS_STREAM`: Input stream name (default `orders.events`).
- `ORDERS_RETRY_ZSET`: Retry queue name (default `orders.retry`).
- `ORDERS_DLQ_STREAM`: DLQ stream name (default `orders.dlq`).
- `MAX_ATTEMPTS`: Max delivery attempts (default `5`).
- `WORKER_POLL_INTERVAL_MS`: Poll interval in ms (default `500`).
- `FAIL_MODE`: `off|always|random`.
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OTLP endpoint.
- `OTEL_SERVICE_NAME`: Telemetry service name.
- `OTEL_SERVICE_VERSION`: Telemetry service version.
- `OTEL_ENVIRONMENT`: Telemetry environment label.

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.worker
```

## Run in Docker

```bash
docker build -t notifications-worker .
docker run --rm --env-file .env.example notifications-worker
```

## Tests

```bash
pytest -q
```

## Demo: Force Failures to DLQ

1. In `infra/.env`, set:

```bash
NOTIFICATIONS_FAIL_MODE=always
```

2. Restart worker:

```bash
docker compose -f ../infra/docker-compose.yml up -d --build notifications-worker
```

3. Create order via dashboard or orders API.
4. Watch retries and terminal failure:

```bash
docker compose -f ../infra/docker-compose.yml logs -f notifications-worker
```

5. Confirm failed payload in DLQ:

```bash
docker compose -f ../infra/docker-compose.yml exec -T redis redis-cli XRANGE orders.dlq - +
```

6. Inspect `/orders` and verify status progression to `failed`.
