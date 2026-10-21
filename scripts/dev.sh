#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
api_port="${API_PORT:-8000}"
panel_port="${PANEL_PORT:-8501}"

if [ ! -f "$root/backend/.env" ]; then
    cp "$root/.env.example" "$root/backend/.env"
    echo "Se creó backend/.env. Complete las claves y vuelva a ejecutar."
    exit 1
fi

pids=()
cleanup() { kill "${pids[@]}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

(cd "$root/backend" && uv run uvicorn bosquevivo.api.app:app --port "$api_port") &
pids+=($!)
(cd "$root/panel" && uv run streamlit run app.py --server.port "$panel_port") &
pids+=($!)

echo "API: http://127.0.0.1:$api_port  Panel: http://127.0.0.1:$panel_port"
wait
