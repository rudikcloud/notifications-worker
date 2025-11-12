# notifications-worker

Background worker for RudikCloud Milestone 4 notifications reliability.

## What it does

- Consumes `order.created` events from Redis stream `orders.events`
- Updates notification fields on `orders` rows in Postgres
- Retries failures using exponential backoff in Redis sorted set `orders.retry`
- Moves permanently failing events to dead-letter stream `orders.dlq`
- Supports failure simulation with `FAIL_MODE=off|always|random`

## Notification lifecycle

- Initial order state: `pending`
- Success: `sent`
- Failed but retryable: `retrying`
- Max attempts exceeded: `failed` + event moved to DLQ

Idempotency rule: if an order is already `sent`, the worker skips re-sending and treats it as success.

## Environment variables

Copy `.env.example` to `.env` when running locally.

- `DATABASE_URL`: Postgres connection string for orders table updates.
- `REDIS_URL`: Redis connection string used for streams and retry zset.
- `ORDERS_EVENTS_STREAM`: Incoming order event stream name (default `orders.events`).
- `ORDERS_RETRY_ZSET`: Retry queue zset name (default `orders.retry`).
- `ORDERS_DLQ_STREAM`: Dead-letter stream name (default `orders.dlq`).
- `MAX_ATTEMPTS`: Maximum delivery attempts before DLQ (default `5`).
- `WORKER_POLL_INTERVAL_MS`: Poll interval for stream + retry checks (default `500`).
- `FAIL_MODE`: Failure simulator: `off`, `always`, `random` (~30% fail).
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OTLP collector endpoint for trace export.
  - Local host example: `http://localhost:4317`
  - Docker Compose example: `http://otel-collector:4317`
- `OTEL_SERVICE_NAME`: OpenTelemetry service name (default `notifications-worker`).
- `OTEL_SERVICE_VERSION`: service version attribute (default `0.1.0`).
- `OTEL_ENVIRONMENT`: deployment environment attribute (default `local`).

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
set -a; source .env; set +a
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

## Milestone 4 demo steps (with infra compose)

1. Start stack from `infra/`:

```bash
docker compose up --build
```

2. Login through auth-service and keep cookie:

```bash
curl -i -c cookies.txt -X POST http://127.0.0.1:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"password123"}'
```

3. Create an order:

```bash
curl -i -b cookies.txt -X POST http://127.0.0.1:8002/orders \
  -H 'Content-Type: application/json' \
  -d '{"item_name":"Keyboard","quantity":1}'
```

4. Confirm worker effect in orders response:

```bash
curl -i -b cookies.txt http://127.0.0.1:8002/orders
```

### Demo retries + DLQ

1. Set worker `FAIL_MODE=always` in `infra/.env`.
2. Restart worker (`docker compose up -d --build notifications-worker`).
3. Create a new order.
4. Watch worker logs and confirm retries then failure:

```bash
docker compose logs -f notifications-worker
```

5. Inspect DLQ stream entries:

```bash
docker compose exec -T redis redis-cli XRANGE orders.dlq - +
```

## Observability quick check

Worker processing creates a `notifications.process_event` span and sets `order.id` as a span attribute.

To verify:

1. Start infra observability stack and worker.
2. Create an order through `orders-service`.
3. In Grafana Explore (Tempo datasource), search traces with `service.name=notifications-worker`.
4. Open a trace and confirm the processing span contains `order.id`.
