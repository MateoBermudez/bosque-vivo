# Guía: despliegue en Vercel con Supabase (PostgreSQL)

## Arquitectura

| Parte | Dónde corre | Qué hace |
|---|---|---|
| Sitio (Next.js, `web/`) | Vercel, proyecto `bosque-vivo-web` | Páginas, chat en línea, área de auditores |
| API (FastAPI, `backend/`) | Vercel, proyecto `bosque-vivo-api` (función de Python) | Proyectos, índice, reportes, chat, WhatsApp, cuentas y correo |
| Base de datos | Supabase (PostgreSQL) | Todos los datos |
| Cálculo satelital | Un computador del equipo, con la CLI | Importa polígonos y calcula auditorías escribiendo en la misma base de Supabase |

El cálculo satelital no va en Vercel porque sus librerías (GDAL, rasterio, Earth Engine, SciPy) pesan cerca de 900 MB y una función de Python en Vercel admite 500 MB. La API instala solo el núcleo (unos 275 MB); las librerías de cálculo son el extra `procesamiento` que se instala en los computadores (`uv sync --all-extras`, lo hacen `scripts/dev` y `scripts/start`). Si alguien pide un cálculo desde la API desplegada, la tarea queda «failed» con el mensaje de usar la CLI.

En Vercel las tareas (mensajes de WhatsApp, reportes) se procesan dentro de la misma petición (`JOBS_MODE=auto` lo detecta con la variable `VERCEL`), los reportes se generan al vuelo y los archivos temporales van a `/tmp`.

## 1. Supabase

1. En el panel del proyecto: **Connect → Transaction pooler**. Copie la cadena; tiene esta forma:

   ```
   postgresql://postgres.<ref>:[YOUR-PASSWORD]@aws-0-<región>.pooler.supabase.com:6543/postgres
   ```

   Use el **pooler** y no la conexión directa (`db.<ref>.supabase.co`): la directa solo funciona por IPv6 y Vercel no la alcanza.
2. En `backend/.env`:

   ```
   DATABASE_URL=postgresql://postgres.<ref>:[YOUR-PASSWORD]@aws-0-<región>.pooler.supabase.com:6543/postgres
   DATABASE_PASSWORD=<contraseña de la base>
   ```

   El sistema reemplaza `[YOUR-PASSWORD]` por `DATABASE_PASSWORD` (codificada) y añade `sslmode=require`. También se puede hacer con `uv run bosquevivo setup --database-url "<cadena>"`.
3. Las tablas se crean solas la primera vez que arranca la API o cualquier comando.

## 2. Pasar los datos existentes de SQLite a Supabase

Desde el computador que tiene la base local (`backend/data/bosquevivo.db`, con los 55 polígonos de Karnik y las auditorías):

```
cd backend
uv run bosquevivo migrate-db
```

Copia las 21 tablas en orden, valida que ningún texto supere el largo de su columna, reinicia las secuencias de identificadores y compara los conteos. Si el destino ya tiene datos se detiene; `--replace` los borra y copia de nuevo. Origen y destino se pueden indicar con `--from` y `--to`.

## 3. Vercel

### Opción A (recomendada, sin token): Vercel conectado a GitHub

Así nadie maneja tokens y cada cambio que llega a `main` se despliega solo.

1. Prepare las variables (en el computador con `backend/.env` ya apuntando a Supabase):

   ```
   cd backend
   uv run bosquevivo vercel-env
   ```

   Crea `backend/data/vercel-api.env` y `backend/data/vercel-web.env` (contienen secretos; `data/` no se sube a git).
2. En [vercel.com/new](https://vercel.com/new) inicie sesión con GitHub e importe `MateoBermudez/bosque-vivo`:
   - **Proyecto de la API:** nombre `bosque-vivo-api`, *Root Directory* `backend` (Vercel detecta FastAPI). En *Environment Variables* pegue el contenido de `vercel-api.env`. Deploy.
   - **Proyecto del sitio:** importe el mismo repositorio otra vez, nombre `bosque-vivo-web`, *Root Directory* `web` (Next.js). Pegue `vercel-web.env`. Deploy.
3. Si Vercel asignó otras direcciones que `bosque-vivo-api.vercel.app` y `bosque-vivo-web.vercel.app`, vuelva a ejecutar `vercel-env --api-url <url-api> --web-url <url-sitio>`, actualice `BACKEND_URL` (sitio) y `WEB_BASE_URL` (API) y use **Redeploy**.

### Opción B: script con token

```
VERCEL_TOKEN=<token> scripts/deploy-vercel.sh
```

El script (requiere Node para `npx vercel`):

1. crea o enlaza el proyecto `bosque-vivo-api` con la carpeta `backend/`, copia las variables de `backend/.env` (base, secretos, Gemini, WhatsApp, SMTP) y lo despliega;
2. crea o enlaza `bosque-vivo-web` con la carpeta `web/`, configura `BV_DATA_SOURCE=live`, `BACKEND_URL`, `ADMIN_TOKEN` y `SESSION_SECRET`, y lo despliega;
3. pone la URL del sitio en `WEB_BASE_URL` de la API (enlaces de los correos) y vuelve a desplegarla.

`VERCEL_SCOPE` elige un equipo de Vercel; `VERCEL_API_PROJECT` y `VERCEL_WEB_PROJECT` cambian los nombres.

## 4. Después de desplegar

- Cuenta de auditor (desde un computador, con `DATABASE_URL` apuntando a Supabase):

  ```
  uv run bosquevivo user-invite su-correo@elpoli.edu.co --name "Su nombre"
  ```

- Webhook de WhatsApp en Meta: `https://bosque-vivo-api.vercel.app/webhook/whatsapp` ([guía](whatsapp.md)).
- Cálculo de auditorías nuevas: `uv run bosquevivo audit-batch` desde un computador con `DATABASE_URL` de Supabase.

## Alternativa local (sin Vercel)

`scripts/dev.sh` (desarrollo) o `scripts/start.sh` (producción, con `TUNNEL=1` para publicar con cloudflared) siguen funcionando con SQLite o con Supabase, según `DATABASE_URL`. En Windows: `scripts\dev.ps1` y `scripts\start.ps1 [-Tunnel]`.

## SQLite y PostgreSQL

| | SQLite (local) | PostgreSQL en Supabase |
|---|---|---|
| Instalación | Ninguna: un archivo | Servicio administrado gratuito |
| Escrituras simultáneas | Una a la vez | Muchas |
| Vercel | No sirve (sin disco persistente) | Sí |
| Copias de seguridad | Copiar `backend/data/` | Automáticas en Supabase |
| Pruebas | Suite completa en memoria | Suite completa con `TEST_DATABASE_URL` (también en la CI) |

La capa gratuita de Supabase pausa el proyecto tras una semana sin actividad; se reactiva desde el panel.
