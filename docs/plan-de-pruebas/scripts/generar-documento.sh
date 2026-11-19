#!/usr/bin/env bash
set -euo pipefail

dir="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
fecha="${1:-$(date +%d/%m/%Y)}"

uv run --no-project --with python-docx==1.2.0 python "$dir/scripts/generar_documento.py" "$work" "$fecha"
echo "Generados Formato_ieee829.docx y Formato_ieee829.pdf con la plantilla plantilla/Formato_ieee829.docx"
