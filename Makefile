.PHONY: up down logs migrate test-api test-infra-up test-infra-down test-web lint-web verify-stack

TEST_PG_CONTAINER := opspilot-test-pg
TEST_REDIS_CONTAINER := opspilot-test-redis
TEST_DB_PORT := 55432
TEST_REDIS_PORT := 63790

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	cd apps/api && . .venv/bin/activate && alembic upgrade head

# Backend tests run against disposable containers (never the docker-compose
# dev database), so a test run can never wipe local dev data.
test-infra-up:
	docker rm -f $(TEST_PG_CONTAINER) $(TEST_REDIS_CONTAINER) >/dev/null 2>&1 || true
	docker run -d --name $(TEST_PG_CONTAINER) \
		-e POSTGRES_USER=opspilot -e POSTGRES_PASSWORD=opspilot -e POSTGRES_DB=opspilot \
		-p $(TEST_DB_PORT):5432 postgres:16-alpine >/dev/null
	docker run -d --name $(TEST_REDIS_CONTAINER) -p $(TEST_REDIS_PORT):6379 redis:7-alpine >/dev/null
	until docker exec $(TEST_PG_CONTAINER) pg_isready -U opspilot >/dev/null 2>&1; do sleep 1; done

test-infra-down:
	docker rm -f $(TEST_PG_CONTAINER) $(TEST_REDIS_CONTAINER) >/dev/null 2>&1 || true

test-api: test-infra-up
	cd apps/api && . .venv/bin/activate && cd ../.. && pytest tests/; \
	status=$$?; $(MAKE) test-infra-down; exit $$status

test-web:
	cd apps/web && npm run build

lint-web:
	cd apps/web && npm run lint

# Requires `make up` (or `docker compose up`) to already be running.
verify-stack:
	./scripts/verify_stack.sh
