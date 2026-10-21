# ADR 0007: WhatsApp Cloud API con túnel

- Estado: aceptada

## Decisión
El webhook valida la firma `X-Hub-Signature-256`, responde `200` de inmediato y encola el mensaje en la tabla `job`. Un trabajador lo procesa en segundo plano. La idempotencia se garantiza por `message_id`. El HTTPS lo aporta el túnel (cloudflared o ngrok).

## Consecuencias
- El procesamiento largo (modelo, imágenes) no bloquea el webhook.
- Plan B: el chat del panel funciona sin WhatsApp.
