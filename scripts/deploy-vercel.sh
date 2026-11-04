#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
api_project="${VERCEL_API_PROJECT:-bosque-vivo-api}"
web_project="${VERCEL_WEB_PROJECT:-bosque-vivo-web}"
: "${VERCEL_TOKEN:?Defina VERCEL_TOKEN (Vercel > Account Settings > Tokens)}"
scope=()
[ -n "${VERCEL_SCOPE:-}" ] && scope=(--scope "$VERCEL_SCOPE")
vc() { npx --yes vercel@65.11.0 "$@" --token "$VERCEL_TOKEN" "${scope[@]}"; }

backend_env="$root/backend/.env"
web_env="$root/web/.env.local"
[ -f "$backend_env" ] || { echo "Falta backend/.env: ejecute primero scripts/dev.sh o bosquevivo setup" >&2; exit 1; }

value() { grep -E "^$1=" "$2" 2>/dev/null | tail -1 | cut -d= -f2- || true; }

database_url="$(value DATABASE_URL "$backend_env")"
case "$database_url" in
  postgres*) ;;
  *) echo "DATABASE_URL de backend/.env debe ser la cadena de Supabase (Transaction pooler)" >&2; exit 1 ;;
esac

push_env() {
  local key="$1" val="$2"
  [ -n "$val" ] || return 0
  vc env add "$key" production --value "$val" --force --yes > /dev/null
  echo "  $key"
}

deploy() {
  vc deploy --prod --yes 2>/dev/null | grep -Eo 'https://[^ ]+\.vercel\.app' | tail -1
}

wait_ok() {
  for _ in $(seq 1 30); do
    curl -sf "$1" > /dev/null && return 0
    sleep 5
  done
  return 1
}

api_keys=(DATABASE_URL DATABASE_PASSWORD ADMIN_TOKEN PHONE_HMAC_KEY INDEX_VERSION
  GEMINI_API_KEY GEMINI_MODEL GEMINI_MODEL_LIGHT
  WHATSAPP_TOKEN WHATSAPP_PHONE_NUMBER_ID WHATSAPP_VERIFY_TOKEN WHATSAPP_APP_SECRET
  WHATSAPP_ALLOWED_PHONES WHATSAPP_API_VERSION
  MAIL_BACKEND MAIL_FROM SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASSWORD SMTP_STARTTLS SMTP_SSL
  AUTH_TWO_FACTOR AUTH_CODE_TTL_MINUTES AUTH_LOGIN_ALERTS PASSWORD_RESET_TTL_MINUTES
  INVITATION_TTL_HOURS AGENT_DAILY_LIMIT_PER_USER)

echo "== API ($api_project)"
cd "$root/backend"
vc link --yes --project "$api_project" > /dev/null
for key in "${api_keys[@]}"; do push_env "$key" "$(value "$key" "$backend_env")"; done
api_url="$(deploy)"
api_public="https://$api_project.vercel.app"
wait_ok "$api_public/health" || api_public="$api_url"
echo "API: $api_public"

echo "== Sitio ($web_project)"
cd "$root/web"
vc link --yes --project "$web_project" > /dev/null
session_secret="$(value SESSION_SECRET "$web_env")"
[ -n "$session_secret" ] || session_secret="$(openssl rand -hex 32)"
push_env BV_DATA_SOURCE live
push_env BACKEND_URL "$api_public"
push_env ADMIN_TOKEN "$(value ADMIN_TOKEN "$backend_env")"
push_env SESSION_SECRET "$session_secret"
push_env PRIVACY_CONTACT_EMAIL "$(value PRIVACY_CONTACT_EMAIL "$web_env")"
push_env WHATSAPP_PUBLIC_NUMBER "$(value WHATSAPP_PUBLIC_NUMBER "$web_env")"
web_url="$(deploy)"
web_public="https://$web_project.vercel.app"
wait_ok "$web_public" || web_public="$web_url"
echo "Sitio: $web_public"

echo "== Enlaces de los correos apuntan al sitio"
cd "$root/backend"
push_env WEB_BASE_URL "$web_public"
deploy > /dev/null
wait_ok "$api_public/health"

echo
echo "Listo."
echo "  Sitio: $web_public"
echo "  API:   $api_public  (webhook de WhatsApp: $api_public/webhook/whatsapp)"
