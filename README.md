# Bosque Vivo

Proyecto Integrador · Ingeniería Informática · ODS 15 (Vida de ecosistemas terrestres)
Politécnico Colombiano Jaime Isaza Cadavid · Segundo semestre de 2026

Sistema de información que contrasta lo que declaran los proyectos de carbono forestal con lo que se observa desde el satélite, y lo explica en lenguaje sencillo mediante un **asistente con IA** por WhatsApp y un panel web para auditores.

> **Estado:** ERS IEEE 830 completo (RF01–RF09) y ampliación de IA RA01, RA02, RA04, RA05, RA07 y RA09. Plan de pruebas IEEE 829 ejecutado en [`docs/plan-de-pruebas`](docs/plan-de-pruebas/README.md). Pendiente del dueño: claves de Gemini y WhatsApp, piloto con usuarios reales; RA03, RA06 y RA08 quedan como evolución.

> **Numeración de requisitos.** RF01–RF09 son los del ERS (IEEE 830); RF09 es la recuperación de contraseña del panel web. La ampliación con IA, antes numerada RF09–RF17, pasa a **RA01–RA09** para no chocar con el ERS (RA01 = antes RF09 … RA09 = antes RF17).

## Decisiones del equipo (leer primero)

| Tema | Decisión |
|---|---|
| **Dónde corre** | **Todo en un computador local (Windows 11).** Sin máquinas virtuales, sin servidores, sin nube propia. |
| **Docker** | **No se usa.** En Windows corre sobre WSL2/Hyper-V (una VM). |
| **IA** | **Gemini de Google AI Studio, capa gratuita, por API** (SDK `google-genai`). **No se usa Ollama ni modelos locales.** |
| **Nivel del proyecto** | **Proyecto universitario, no tesis.** Se prioriza que funcione, se pueda demostrar, esté probado y documentado. |
| **Código abierto** | Todo el código propio es abierto. Gemini, Google Earth Engine y WhatsApp Cloud API son servicios gratuitos de terceros (el ERS contempla "servicios gratuitos de terceros"). |
| **Base de datos** | SQLite + shapely (sin PostgreSQL/PostGIS). |
| **Frontend** | Next.js en `web/` ([ADR 0013](docs/architecture/adr/0013-nextjs-para-el-frontend.md), propuesta). El panel Streamlit (`panel/`) queda en desuso hasta que se apruebe. |
| **Alcance** | ERS (RF01–RF09) + agente de IA que razona, analiza imágenes y concluye con evidencia (RA01–RA09, pendiente de aprobación del docente). |

Los nombres de modelo y las cuotas de Gemini cambian: verificar en AI Studio y configurar `GEMINI_MODEL` en el `.env`.

## Documentos

| Documento | Contenido |
|---|---|
| [`docs/planning/PLAN_IMPLEMENTACION.md`](docs/planning/PLAN_IMPLEMENTACION.md) | Plan maestro: arquitectura local, stack, estructura del repo, datos, índice, equipo, pruebas, cronograma, riesgos, primeros pasos |
| [`docs/planning/PLAN_AGENTE_IA.md`](docs/planning/PLAN_AGENTE_IA.md) | Diseño del agente con Gemini: herramientas, análisis de imágenes, conocimiento, voz, cuotas, seguridad, evaluación |
| [`docs/architecture`](docs/architecture/arquitectura.md) | Arquitectura y [ADRs](docs/architecture/adr/README.md) |
| [`docs/methodology/indice-v0.md`](docs/methodology/indice-v0.md) | Definición del índice, confianza y limitaciones |
| [`docs/fuentes-de-datos/datos-abiertos.md`](docs/fuentes-de-datos/datos-abiertos.md) | Pérdida de bosque con datos abiertos de Hansen, sin Earth Engine |
| [`docs/fuentes-de-datos/karnik.md`](docs/fuentes-de-datos/karnik.md) | Fuente de los polígonos (Karnik et al., 2025): licencia, reglas de importación, resultado para Colombia |
| [`docs/testing`](docs/testing/plan-de-pruebas.md) | Plan de pruebas anterior (reemplazado por `docs/plan-de-pruebas`) |
| [`docs/privacy`](docs/privacy/aviso-de-privacidad.md) | Aviso de privacidad (Ley 1581) |
| [`docs/plan-de-pruebas`](docs/plan-de-pruebas/README.md) | **Plan de pruebas IEEE 829**: plan, casos, ejecución, incidencias, evidencias y mediciones |
| [`docs/guias`](docs/guias) | Guías: [despliegue](docs/guias/despliegue.md), [WhatsApp](docs/guias/whatsapp.md), [Gemini](docs/guias/gemini.md), [correo y 2FA](docs/guias/correo.md) |

## Ejecución local

Requisitos en cada PC: Python 3.12, [`uv`](https://docs.astral.sh/uv/), Node 22 o superior y Git.

```
scripts/dev.sh                       # en Windows: scripts\dev.ps1
```

La primera vez, `bosquevivo setup` crea `backend/.env` y `web/.env.local` con todos los secretos generados, la base de datos y tres proyectos de demostración, y lista las claves externas que faltan (Gemini, WhatsApp, SMTP). Crear la primera cuenta de auditor:

```
cd backend && uv run bosquevivo user-invite correo@elpoli.edu.co --name "Nombre"
```

- API: http://127.0.0.1:8000 (documentación en `/docs`)
- Sitio: http://localhost:3000
- Modo producción para el piloto: `scripts/start.sh` (o `scripts\start.ps1`), con `TUNNEL=1` / `-Tunnel` para publicarlo con HTTPS. Ver [guía de despliegue](docs/guias/despliegue.md).
- Panel Streamlit (en desuso, opcional): `scripts\dev.ps1 -Streamlit` o `STREAMLIT=1 scripts/dev.sh` → http://127.0.0.1:8501

Sin claves externas funciona todo salvo lo que depende de ellas: el asistente (WhatsApp y el chat en línea `/asistente`) responde ESTADO, ALERTAS, AYUDA y PROYECTO <número> sin IA; las preguntas libres, fotos y voz requieren Gemini ([guía](docs/guias/gemini.md)). El área de auditores usa cuentas con correo y contraseña; con SMTP configurado ([guía](docs/guias/correo.md)) se activan la verificación en dos pasos por correo, los avisos de inicio de sesión y el envío real de la recuperación de contraseña (RF09). Más detalle en [`web/README.md`](web/README.md).

Importar los polígonos reales de Colombia (base de Karnik et al., ver [`docs/fuentes-de-datos/karnik.md`](docs/fuentes-de-datos/karnik.md)) y calcular una auditoría:

```
uv run bosquevivo import-karnik ../data/raw/karnik_south_america/south_america.gpkg --country Colombia
uv run bosquevivo audit 7        # las series empiezan 3 años antes del T0 del proyecto
```

Para calcular **todos** los proyectos de una vez, con datos abiertos y sin cuenta de Google (solo pérdida de bosque y permanencia; ver [`docs/fuentes-de-datos/datos-abiertos.md`](docs/fuentes-de-datos/datos-abiertos.md)):

```
SATELLITE_PROVIDER=hansen uv run bosquevivo audit-batch --country Colombia
```

`audit` con `SATELLITE_PROVIDER=gee` (NDVI completo y miniaturas) necesita `GEE_PROJECT` y haber ejecutado `earthengine authenticate`. Para un tipo de archivo distinto use `bosquevivo import <archivo> --source <nombre>` (GeoJSON, KML, GeoPackage o Shapefile). Por defecto la importación es estricta, como pide RF01: cada polígono debe ser válido y traer identificador y fecha de registro (en KML, como `<ExtendedData><Data name="project_id">` y `<Data name="start_year">`), y un identificador repetido se rechaza con su motivo. `--lenient` repara geometrías y actualiza los existentes.

Calidad:

```
cd backend && uv run ruff check . && uv run pyright && uv run pytest
cd web && npm run lint && npm run typecheck && npm test && npm run build
```

Para la demo y el piloto, el computador debe estar encendido, sin suspensión y con Internet estable.

## Estructura

```
backend/   API, módulos de dominio, agente de IA y pruebas
web/       sitio Next.js (inicio, explorador, detalle, chat del auditor, trazas, metodología)
panel/     panel Streamlit de solo lectura (en desuso, ver ADR 0013)
docs/      ERS, planes, arquitectura y ADRs, metodología, pruebas y privacidad
scripts/   arranque local
```

## Reglas del repositorio

- `.env` y `data/` **nunca** se suben a git.
- No se envían a Gemini teléfonos ni nombres; el teléfono solo se guarda como HMAC.
- Lenguaje neutro en todo el producto: "correspondencia observada", nunca "fraude".
- Ramas cortas, PR con revisión de otra persona, commits convencionales.

## Equipo

| Persona | Rol |
|---|---|
| P1 | Plataforma e integración (tech lead) |
| P2 | Datos geoespaciales |
| P3 | Analítica y reportes |
| P4 | Agente y experiencia |

Detalle de responsabilidades por requisito en `docs/planning/PLAN_IMPLEMENTACION.md`.
