#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
api_port="${API_PORT:-8000}"
web_port="${WEB_PORT:-3000}"
panel_port="${PANEL_PORT:-8501}"

if [ ! -f "$root/backend/.env" ]; then
    cp "$root/.env.example" "$root/backend/.env"
    echo "Se creó backend/.env. Complete las claves y vuelva a ejecutar."
    exit 1
fi

# El sitio (web/) se conecta a la API con el mismo ADMIN_TOKEN del backend.
if [ ! -f "$root/web/.env.local" ]; then
    admin_token="$(grep -E '^[[:space:]]*ADMIN_TOKEN[[:space:]]*=' "$root/backend/.env" | head -1 | cut -d= -f2- | tr -d '[:space:]' || true)"
    {
        echo "BV_DATA_SOURCE=live"
        echo "BACKEND_URL=http://127.0.0.1:$api_port"
        echo "ADMIN_TOKEN=$admin_token"
        echo "BV_SAMPLE_NOTICE=1"
    } > "$root/web/.env.local"
    echo "Se creó web/.env.local (modo live). Defina AUDITOR_ACCESS_CODE y SESSION_SECRET para proteger el área de auditores."
fi

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
