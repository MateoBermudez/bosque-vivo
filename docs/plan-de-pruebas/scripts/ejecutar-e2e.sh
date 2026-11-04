#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/../../.." && pwd)"
work="$(mktemp -d)"
evidence="$root/docs/plan-de-pruebas/evidencias"
mkdir -p "$evidence/capturas"
api_port=8100
web_port=3100

for port in "$api_port" "$web_port"; do
  if curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$port/"; then
    echo "El puerto $port está ocupado: detenga el proceso que lo usa y vuelva a ejecutar." >&2
    exit 1
  fi
done

export DATABASE_URL="sqlite:///$work/bv.db" DATA_DIR="$work/data" ADMIN_TOKEN="token-e2e"
export SATELLITE_PROVIDER=fake WEB_BASE_URL="http://localhost:$web_port" AUTH_TWO_FACTOR=on

cd "$root/backend"
uv run bosquevivo seed-demo
uv run bosquevivo user-invite auditora@elpoli.edu.co --name "Auditora Prueba"
setsid uv run uvicorn bosquevivo.api.app:app --port "$api_port" > "$work/api.log" 2>&1 &
api_pid=$!

cd "$root/web"
[ -d .next ] || npm run build
BV_DATA_SOURCE=live BACKEND_URL="http://127.0.0.1:$api_port" ADMIN_TOKEN="$ADMIN_TOKEN" \
  SESSION_SECRET="$(openssl rand -hex 32)" setsid npx next start --port "$web_port" > "$work/web.log" 2>&1 &
web_pid=$!
trap 'kill -- -$api_pid -$web_pid 2>/dev/null || true' EXIT

for _ in $(seq 1 60); do
  curl -sf "http://localhost:$web_port/acceso" > /dev/null && curl -sf "http://127.0.0.1:$api_port/health" > /dev/null && break
  sleep 1
done

E2E_BASE="http://localhost:$web_port" E2E_OUTBOX="$work/data/outbox" E2E_SHOTS="$evidence/capturas" \
  E2E_REPORT="$evidence/e2e-resultados.json" node "$root/docs/plan-de-pruebas/scripts/e2e.cjs" | tee "$evidence/e2e-salida.txt"
