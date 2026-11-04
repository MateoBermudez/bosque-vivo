#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
api_port="${API_PORT:-8000}"
web_port="${WEB_PORT:-3000}"
panel_port="${PANEL_PORT:-8501}"

(cd "$root/backend" && uv sync --quiet --all-extras && uv run bosquevivo setup --api-port "$api_port")

if [ ! -d "$root/web/node_modules" ]; then
    echo "Instalando dependencias de web (npm ci)..."
    (cd "$root/web" && npm ci)
fi

pids=()
cleanup() { kill "${pids[@]}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

(cd "$root/backend" && uv run uvicorn bosquevivo.api.app:app --port "$api_port") &
pids+=($!)
(cd "$root/web" && npm run dev -- --port "$web_port") &
pids+=($!)

if [ "${STREAMLIT:-0}" = "1" ]; then
    (cd "$root/panel" && uv run streamlit run app.py --server.port "$panel_port") &
    pids+=($!)
    echo "Panel Streamlit (en desuso): http://127.0.0.1:$panel_port"
fi

echo "API: http://127.0.0.1:$api_port  Sitio: http://localhost:$web_port"
wait
