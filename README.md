# Bosque Vivo

Proyecto Integrador · Ingeniería Informática · ODS 15 (Vida de ecosistemas terrestres)
Politécnico Colombiano Jaime Isaza Cadavid · Segundo semestre de 2026

Sistema de información que contrasta lo que declaran los proyectos de carbono forestal con lo que se observa desde el satélite, y lo explica en lenguaje sencillo mediante un **asistente con IA** por WhatsApp y un panel web para auditores.

> **Estado:** planificación. Aún no hay código.

## Decisiones del equipo (leer primero)

| Tema | Decisión |
|---|---|
| **Dónde corre** | **Todo en un computador local (Windows 11).** Sin máquinas virtuales, sin servidores, sin nube propia. |
| **Docker** | **No se usa.** En Windows corre sobre WSL2/Hyper-V (una VM). |
| **IA** | **Gemini de Google AI Studio, capa gratuita, por API** (SDK `google-genai`). **No se usa Ollama ni modelos locales.** |
| **Nivel del proyecto** | **Proyecto universitario, no tesis.** Se prioriza que funcione, se pueda demostrar, esté probado y documentado. |
| **Código abierto** | Todo el código propio es abierto. Gemini, Google Earth Engine y WhatsApp Cloud API son servicios gratuitos de terceros (el ERS contempla "servicios gratuitos de terceros"). |
| **Base de datos** | SQLite + shapely (sin PostgreSQL/PostGIS). |
| **Panel** | Streamlit. |
| **Alcance** | ERS (RF01–RF08) + agente de IA que razona, analiza imágenes y concluye con evidencia (RF09–RF17, pendiente de aprobación del docente). |

Los nombres de modelo y las cuotas de Gemini cambian: verificar en AI Studio y configurar `GEMINI_MODEL` en el `.env`.

## Documentos

| Documento | Contenido |
|---|---|
| [`docs/planning/PLAN_IMPLEMENTACION.md`](docs/planning/PLAN_IMPLEMENTACION.md) | Plan maestro: arquitectura local, stack, estructura del repo, datos, índice, equipo, pruebas, cronograma, riesgos, primeros pasos |
| [`docs/planning/PLAN_AGENTE_IA.md`](docs/planning/PLAN_AGENTE_IA.md) | Diseño del agente con Gemini: herramientas, análisis de imágenes, conocimiento, voz, cuotas, seguridad, evaluación |

## Ejecución local (cuando exista el código)

Requisitos previstos en cada PC: Python 3.12, `uv`, Git, una clave de Google AI Studio, acceso a Google Earth Engine y (solo para WhatsApp) ngrok o cloudflared.

1. Copiar `.env.example` a `.env` y completar `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEE_PROJECT` y las variables de WhatsApp.
2. Instalar dependencias con `uv sync`.
3. Arrancar todo con `scripts\dev.ps1` (API, panel y, si se pide, túnel).

Para la demo y el piloto, el computador debe estar encendido, sin suspensión y con Internet estable.

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
