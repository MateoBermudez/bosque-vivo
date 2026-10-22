// MapLibre GL 6 carga su "worker" desde una URL. Con Turbopack esa URL calculada no existe y el mapa
// falla con «Worker failed to load». Se copia el worker a /public y el mapa lo pide desde ahí
// (ver src/components/projects/project-map.tsx). Corre en postinstall, predev y prebuild para que
// siempre coincida con la versión instalada.
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const source = path.join(root, "node_modules", "maplibre-gl", "dist", "maplibre-gl-worker.mjs");
const targetDir = path.join(root, "public", "vendor", "maplibre");

if (!existsSync(source)) {
  console.warn("[copy-maplibre-worker] no se encontró maplibre-gl; se omite (¿falta npm install?)");
  process.exit(0);
}
mkdirSync(targetDir, { recursive: true });
copyFileSync(source, path.join(targetDir, "maplibre-gl-worker.mjs"));
console.log("[copy-maplibre-worker] worker copiado a public/vendor/maplibre/");
