#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
api_port="${API_PORT:-8000}"
web_port="${WEB_PORT:-3000}"

(cd "$root/backend" && uv sync --quiet && uv run bosquevivo setup --api-port "$api_port")

cd "$root/web"
[ -d node_modules ] || npm ci
npm run build

pids=()
cleanup() { kill -- "${pids[@]/#/-}" 2>/dev/null || kill "${pids[@]}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

(cd "$root/backend" && exec setsid uv run uvicorn bosquevivo.api.app:app --host 127.0.0.1 --port "$api_port") &
pids+=($!)
(cd "$root/web" && exec setsid npm run start -- --port "$web_port") &
pids+=($!)

if [ "${TUNNEL:-0}" = "1" ]; then
    (exec setsid cloudflared tunnel --url "http://127.0.0.1:$web_port") &
    pids+=($!)
    (exec setsid cloudflared tunnel --url "http://127.0.0.1:$api_port") &
    pids+=($!)
    echo "Túneles HTTPS: copie las URL https://...trycloudflare.com que imprime cloudflared."
    echo "Sitio: ponga su URL en WEB_BASE_URL (backend/.env). API: úsela para el webhook de WhatsApp."
fi

echo "Modo producción. API: http://127.0.0.1:$api_port  Sitio: http://localhost:$web_port"
wait
