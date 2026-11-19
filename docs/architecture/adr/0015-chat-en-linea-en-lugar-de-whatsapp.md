# ADR 0015: Chat en línea en lugar de WhatsApp

- Estado: aceptada (reemplaza a ADR 0007)

## Contexto
El ERS preveía WhatsApp Business API como canal del asistente. Ponerlo en marcha exige un número de teléfono dedicado al servicio y la verificación de una cuenta empresarial en Meta, algo que el equipo no puede asumir durante el semestre. El sitio ya tenía un chat en línea con el mismo asistente.

## Decisión
- El canal del asistente es el chat en línea del sitio (`/asistente`), con todo lo que iba a ofrecer WhatsApp: texto, ubicación del navegador, fotos y notas de voz, con el mismo consentimiento (ACEPTO y ACEPTO FOTOS) y el mismo borrado (BORRAR MIS DATOS).
- La conversación se identifica con un código aleatorio guardado en el navegador; en la base solo queda su HMAC.
- El navegador reduce las fotos a 1280 px en JPEG y graba las notas de voz como WAV de 16 kHz (hasta 60 s), para que cada mensaje quede por debajo de 3 MB y el modelo lo entienda sin conversiones.
- El servidor de Next (`/api/asistente`) valida el mensaje, aplica un límite por IP y llama a `POST /api/v1/community/messages` con `ADMIN_TOKEN`, que nunca llega al navegador.
- El código del webhook de WhatsApp se conserva sin anunciarse, como base de la ampliación de la sección 2.6 del ERS.

## Consecuencias
- No hace falta número, verificación ni costo de mensajería; el enlace o el código QR de `/asistente` se comparte por cualquier medio.
- Quien no tenga datos móviles o navegador no puede usar el asistente; es el mismo supuesto de conectividad de WhatsApp.
- El sitio declara `Permissions-Policy` con micrófono y ubicación solo para el propio sitio.
