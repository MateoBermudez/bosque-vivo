#!/usr/bin/env bash
set -euo pipefail

dir="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"
sources=(plan-de-pruebas.md casos-de-prueba.md informe-de-resultados.md incidencias.md)
cd "$dir"

pandoc "${sources[@]}" --toc --toc-depth=2 -M toc-title="Tabla de contenido" -o Plan_de_Pruebas_Bosque_Vivo.docx
mkdir -p "$work/docx"
(cd "$work/docx" && unzip -q "$dir/Plan_de_Pruebas_Bosque_Vivo.docx" \
  && sed -i 's|<w:settings\([^>]*\)>|<w:settings\1><w:updateFields w:val="true"/>|' word/settings.xml \
  && rm "$dir/Plan_de_Pruebas_Bosque_Vivo.docx" && zip -q -X -r "$dir/Plan_de_Pruebas_Bosque_Vivo.docx" '[Content_Types].xml' _rels docProps word)

pandoc "${sources[@]}" --standalone --toc --toc-depth=2 -M toc-title="Tabla de contenido" \
  --metadata title="Plan de Pruebas de Software" --css "$dir/scripts/estilo-pdf.css" --embed-resources \
  -o "$work/plan.html"
node "$dir/scripts/html-a-pdf.cjs" "$work/plan.html" "$dir/Plan_de_Pruebas_Bosque_Vivo.pdf"
echo "Generados Plan_de_Pruebas_Bosque_Vivo.docx y Plan_de_Pruebas_Bosque_Vivo.pdf"
