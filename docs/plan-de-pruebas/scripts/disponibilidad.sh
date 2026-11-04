#!/usr/bin/env bash
set -uo pipefail

url="${1:-http://127.0.0.1:8000/health}"
minutes="${2:-240}"
log="${3:-disponibilidad.csv}"

echo "fecha,estado,segundos" > "$log"
ok=0
for ((i = 1; i <= minutes; i++)); do
  result="$(curl -s -o /dev/null -w '%{http_code},%{time_total}' --max-time 10 "$url" || echo '000,10')"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),$result" >> "$log"
  [[ "$result" == 200,* ]] && ok=$((ok + 1))
  [ "$i" -lt "$minutes" ] && sleep 60
done
awk -v ok="$ok" -v total="$minutes" 'BEGIN { printf "Disponibilidad: %.2f %% (%d de %d minutos)\n", ok * 100 / total, ok, total }'
