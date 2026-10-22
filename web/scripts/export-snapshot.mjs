// Guarda en web/snapshot una copia de solo lectura de lo que responde la API (proyectos, polígonos,
// auditorías, series, datos del registro y reportes). Con ella el sitio se publica sin servidor
// (BV_DATA_SOURCE=snapshot). Uso: node scripts/export-snapshot.mjs  (con la API encendida)
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "snapshot");
const base = (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "") + "/api/v1";
// Mismos aligeramientos que usa el sitio: mapa del explorador y mapa de la ficha.
const GEOMETRY = { map: "simplify=0.005&max_parts=200", detail: "simplify=0.0005&max_parts=1000" };

async function get(url, { optional = false, text = false } = {}) {
  const response = await fetch(url, { signal: AbortSignal.timeout(120_000) });
  if (response.status === 404 && optional) return null;
  if (!response.ok) throw new Error(`${response.status} en ${url}`);
  return text ? response.text() : response.json();
}

function save(relative, content) {
  const file = path.join(root, relative);
  mkdirSync(path.dirname(file), { recursive: true });
  writeFileSync(file, typeof content === "string" ? content : JSON.stringify(content));
}

rmSync(root, { recursive: true, force: true });
const projects = await get(`${base}/projects?limit=200`);
save("projects.json", projects);

let reports = 0;
for (const project of projects) {
  const id = project.id;
  for (const [name, query] of Object.entries(GEOMETRY)) {
    const geometry = await get(`${base}/projects/${id}/geometry?${query}`, { optional: true });
    if (geometry) save(`geometry/${id}.${name}.json`, geometry);
  }
  const series = await get(`${base}/projects/${id}/series`, { optional: true });
  if (series) save(`series/${id}.json`, series);
  save(`declarations/${id}.json`, (await get(`${base}/projects/${id}/declarations`, { optional: true })) ?? []);
  const audit = await get(`${base}/projects/${id}/audit`, { optional: true });
  if (audit) {
    save(`audit/${id}.json`, audit);
    const report = await get(`${base}/audits/${audit.id}/report?format=html`, { optional: true, text: true });
    if (report) {
      save(`reports/${audit.id}.html`, report);
      reports += 1;
    }
  }
  console.log(`#${id} ${project.name.slice(0, 50)}`);
}
console.log(`listo: ${projects.length} proyectos, ${reports} reportes en ${root}`);
