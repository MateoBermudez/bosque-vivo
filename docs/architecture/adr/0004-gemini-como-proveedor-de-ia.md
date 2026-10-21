# ADR 0004: Gemini (AI Studio, capa gratuita) como único proveedor de IA

- Estado: aceptada

## Contexto
El objetivo específico 2 pide herramientas de código abierto. El ERS contempla "servicios gratuitos de terceros" (Google Earth Engine, WhatsApp).

## Decisión
Todo el código propio es abierto. Gemini se usa por API (`google-genai`) como servicio gratuito de terceros. El modelo se configura con `GEMINI_MODEL` y `GEMINI_MODEL_LIGHT`. Una interfaz `LLMProvider` delgada documenta cómo cambiar de proveedor sin construir soporte para varios.

## Consecuencias
- Un solo servicio cubre razonamiento, llamado a funciones, visión, audio y PDF.
- La capa gratuita puede usar el contenido para mejorar productos de Google: se informa en el aviso de privacidad, no se envían teléfonos ni nombres y se pide consentimiento.
- Las cuotas cambian: caché, topes de pasos y respaldo determinista (ADR 0010).
