# Guía: activar la IA (Gemini, capa gratuita)

El agente de IA (RA01–RA09) usa la API de Gemini de Google AI Studio. La capa gratuita no requiere tarjeta y basta para el piloto.

## Pasos

1. Entre a [aistudio.google.com/apikey](https://aistudio.google.com/apikey) con una cuenta de Google y pulse **Crear clave de API**.
2. En `backend/.env`:

   ```
   GEMINI_API_KEY=<la clave>
   GEMINI_MODEL=<modelo principal>
   GEMINI_MODEL_LIGHT=<modelo liviano, opcional>
   ```

3. Liste los modelos disponibles con su clave y pruebe los elegidos:

   ```
   cd backend
   uv run bosquevivo gemini-check
   ```

   Elija de la lista un modelo **Flash** para `GEMINI_MODEL` y un **Flash-Lite** para `GEMINI_MODEL_LIGHT`; son los que tienen capa gratuita. Los nombres cambian con frecuencia: use los que muestre el comando.

4. Ejecute la evaluación del agente (20 casos) y guarde el resultado como evidencia del plan de pruebas (CP-50):

   ```
   uv run bosquevivo eval --output data/eval/report.json
   ```

## Límites y privacidad

- Los límites de la capa gratuita (solicitudes por minuto y por día) se consultan en [aistudio.google.com/rate-limit](https://aistudio.google.com/rate-limit). El backend además limita a 10 solicitudes por minuto, 400 por día y `AGENT_DAILY_LIMIT_PER_USER` por usuario.
- En la capa gratuita Google puede usar el contenido para mejorar sus productos. Por eso el aviso de privacidad lo advierte y el sistema nunca envía teléfonos ni nombres.
- Si la cuota se agota o la clave falla, el agente usa la respuesta de respaldo determinista y queda registrado un incidente de origen «externo» (`uv run bosquevivo incidents`).
