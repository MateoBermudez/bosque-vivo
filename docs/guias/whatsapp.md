# Guía: conectar el asistente a WhatsApp

El código del asistente ya está terminado y probado (RF07, RF08). Solo falta conectar una cuenta de Meta, algo que debe hacer el dueño del proyecto con sus credenciales.

## ¿Cuesta dinero?

Para el piloto, **no**:

- El **número de prueba** que Meta crea con la app de desarrollador es gratuito y permite escribir a hasta 5 números verificados.
- El asistente solo **responde** a quien le escribe (mensajes de servicio dentro de la ventana de 24 horas); no envía plantillas de marketing.
- Desde el 1 de octubre de 2026, Meta cobra los mensajes de servicio por encima de **1.000 gratuitos al mes por número**. Un piloto académico queda muy por debajo de ese límite. Verifique la tabla vigente en la [página de precios de Meta](https://developers.facebook.com/docs/whatsapp/pricing) antes de un uso mayor.

Si en algún momento WhatsApp no está disponible o deja de ser gratuito, el sitio tiene el **chat en línea** (`/asistente`), que usa exactamente el mismo flujo (aviso, ACEPTO, ESTADO, ALERTAS, AYUDA, BORRAR MIS DATOS) sin depender de Meta.

## Pasos

1. Entre a [developers.facebook.com](https://developers.facebook.com/), cree una app de tipo **Empresa** y agregue el producto **WhatsApp**.
2. En **WhatsApp → Configuración de la API** copie:
   - el **token de acceso** → `WHATSAPP_TOKEN` (el temporal dura 24 h; para el piloto cree un token permanente de un *usuario del sistema* en el Business Manager),
   - el **identificador del número de teléfono** → `WHATSAPP_PHONE_NUMBER_ID`.
3. Agregue en esa misma pantalla los números de prueba (hasta 5) y verifíquelos con el código que llega por WhatsApp.
4. En **Configuración de la app → Básica** copie la **clave secreta de la app** → `WHATSAPP_APP_SECRET` (con ella se valida la firma `X-Hub-Signature-256`).
5. Invente una cadena larga para `WHATSAPP_VERIFY_TOKEN`.
6. Complete `backend/.env`:

   ```
   WHATSAPP_TOKEN=...
   WHATSAPP_PHONE_NUMBER_ID=...
   WHATSAPP_APP_SECRET=...
   WHATSAPP_VERIFY_TOKEN=...
   PHONE_HMAC_KEY=<openssl rand -hex 32>
   WHATSAPP_ALLOWED_PHONES=573001234567,573009876543
   ```

   `WHATSAPP_ALLOWED_PHONES` es la lista de números autorizados del piloto (RF07). Si se deja vacía, atiende a cualquiera.
7. Levante la API (`scripts/dev.sh` o `scripts\dev.ps1`) y abra un túnel HTTPS gratuito:

   ```
   cloudflared tunnel --url http://127.0.0.1:8000
   ```

   (o `ngrok http 8000`). Copie la URL `https://...trycloudflare.com`.
8. En **WhatsApp → Configuración → Webhook** ponga `https://<túnel>/webhook/whatsapp` y el mismo `WHATSAPP_VERIFY_TOKEN`. Pulse **Verificar y guardar** y suscríbase al campo **messages**.
9. Escriba «Hola» desde un número de prueba. Debe llegar el saludo y el aviso de privacidad; responda ACEPTO, luego PROYECTO 1, ESTADO, ALERTAS y AYUDA.
10. Para mostrar el número en el sitio, ponga `WHATSAPP_PUBLIC_NUMBER` en `web/.env.local` (aparece un código QR en `/whatsapp`).

## Comprobación

- `GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token=<token>&hub.challenge=123` debe devolver `123`.
- Un POST sin firma válida debe devolver `401`.
- `uv run bosquevivo incidents` muestra los fallos de envío (origen «externo»).

## Sin clave de IA

El asistente funciona sin Gemini para las intenciones del ERS (estado, alertas, ayuda, registro del proyecto, consentimiento y borrado): esas respuestas son deterministas. Las preguntas libres, las fotos y las notas de voz requieren `GEMINI_API_KEY` (ver [guía de Gemini](gemini.md)); sin ella el asistente responde con el mensaje de respaldo y la ayuda.
