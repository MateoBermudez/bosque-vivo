# ADR 0010: Dos clases de consulta y gestión de la capa gratuita

- Estado: aceptada

## Decisión
- Consulta rápida (datos ya calculados): meta p90 < 10 s.
- Consulta profunda (genera y analiza imágenes): acuse inmediato y resultado en minutos. El router lo decide por reglas, sin gastar cuota.
- Gestión de cuota: `RateLimiter` por minuto y por día, reintentos con espera exponencial ante 429/5xx, caché de respuestas sin herramientas, límite diario por usuario y respaldo determinista cuando no hay cuota.

## Consecuencias
- El NFR de 10 s se mide por clase. Requiere acordarlo con el docente.
