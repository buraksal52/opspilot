#!/bin/sh
# Basic frontend/API connectivity verification for Phase 1 (BACKLOG.md 1.8).
# Assumes `docker compose up` (or `make up`) is already running.
set -e

API_URL="${API_URL:-http://localhost:8000}"
WEB_URL="${WEB_URL:-http://localhost:3000}"

echo "Checking API health at ${API_URL}/api/v1/health ..."
health_body=$(curl -sS -f "${API_URL}/api/v1/health")
case "$health_body" in
  *'"status":"ok"'*) echo "  OK: ${health_body}" ;;
  *) echo "  FAILED: unexpected response: ${health_body}" >&2; exit 1 ;;
esac

echo "Checking API responds with CORS headers for the web origin ..."
cors_header=$(curl -sS -D - -o /dev/null -H "Origin: ${WEB_URL}" "${API_URL}/api/v1/health" | grep -i "access-control-allow-origin" || true)
if [ -z "$cors_header" ]; then
  echo "  FAILED: no access-control-allow-origin header for Origin: ${WEB_URL}" >&2
  exit 1
fi
echo "  OK: ${cors_header}"

echo "Checking frontend dashboard at ${WEB_URL}/dashboard ..."
dashboard_body=$(curl -sS -f "${WEB_URL}/dashboard")
case "$dashboard_body" in
  *"Backend Connectivity"*) echo "  OK: dashboard route renders" ;;
  *) echo "  FAILED: dashboard did not render expected content" >&2; exit 1 ;;
esac

echo "Stack verification passed."
