# Guía: puesta en marcha y despliegue

## ¿Está desplegado?

No hay un servidor público en funcionamiento. Por decisión del equipo ([ADR 0002](../architecture/adr/0002-ejecucion-local-sin-docker.md)) Bosque Vivo corre en un computador del equipo (Windows 11 o Linux), sin servidores ni nube propia. Para el piloto se publica desde ese computador con un túnel HTTPS gratuito.

## Primera vez

Requisitos: Python 3.12, [uv](https://docs.astral.sh/uv/), Node 22 o superior, Git.

```
git clone https://github.com/MateoBermudez/bosque-vivo
cd bosque-vivo
```

Linux o macOS:

```
scripts/dev.sh
```

Windows (PowerShell):

```
scripts\dev.ps1
```

`dev` ejecuta `bosquevivo setup`, que:

- crea `backend/.env` y `web/.env.local`;
- genera todos los secretos (`ADMIN_TOKEN`, `PHONE_HMAC_KEY`, `WHATSAPP_VERIFY_TOKEN`, `SESSION_SECRET`);
- usa datos satelitales abiertos (`SATELLITE_PROVIDER=open`) si no hay cuenta de Earth Engine;
- crea la base y carga 3 proyectos de demostración;
- muestra qué claves externas faltan.

Cree la primera cuenta de auditor:

```
cd backend
uv run bosquevivo user-invite su-correo@elpoli.edu.co --name "Su nombre"
```

Abra http://localhost:3000. Todo funciona sin claves externas, salvo lo que depende de ellas:

| Falta | Qué no funciona hasta completarlo | Guía |
|---|---|---|
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Preguntas libres, fotos y voz del asistente; chat del auditor | [gemini.md](gemini.md) |
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_APP_SECRET` | Canal de WhatsApp (el chat en línea `/asistente` funciona igual) | [whatsapp.md](whatsapp.md) |
| `SMTP_USER`, `SMTP_PASSWORD` | Envío real de correos y verificación en dos pasos (sin ellos los correos quedan en `backend/data/outbox`) | [correo.md](correo.md) |
| `GEE_PROJECT` (opcional) | NDVI de Sentinel-2/Landsat con Earth Engine (sin él se usa MODIS + Hansen) | [datos-abiertos.md](../fuentes-de-datos/datos-abiertos.md) |

## Modo producción (piloto)

`start` compila el sitio y lo sirve optimizado:

```
scripts/start.sh
```

```
scripts\start.ps1
```

Para publicarlo en Internet con HTTPS, instale [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) y use:

```
TUNNEL=1 scripts/start.sh
```

```
scripts\start.ps1 -Tunnel
```

Se abren dos túneles `https://…trycloudflare.com`: el del sitio (póngalo en `WEB_BASE_URL` de `backend/.env` y en `SITE_URL` de `web/.env.local`) y el de la API (úselo en el webhook de WhatsApp: `https://<túnel-api>/webhook/whatsapp`). Las URL de los túneles rápidos cambian en cada arranque; para una URL fija use un túnel con nombre de Cloudflare (gratis, requiere una cuenta y un dominio).

El computador debe quedar encendido, sin suspensión y con Internet estable durante el piloto. La disponibilidad se mide con `docs/plan-de-pruebas/scripts/disponibilidad.sh`.

## Copia estática para mostrar sin servidor

`web/snapshot` contiene una copia de solo lectura de los proyectos. Con `BV_DATA_SOURCE=snapshot` el sitio se puede publicar gratis en Vercel o Netlify sin la API (sin chat ni área de auditores). Ver `web/README.md`.
