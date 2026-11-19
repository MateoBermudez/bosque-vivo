# ADR 0016: Agente guía con identificación de proyecto y rutas deterministas

- Estado: aceptada (complementa ADR 0008, 0009 y 0010)

## Contexto
Con los proyectos reales cargados, el chat respondía «no hay información» aunque los datos existieran. Probado contra los 55 proyectos de Karnik:

- El modelo recibía la frase completa en `buscar_proyecto` y la comparaba contra los nombres (`WRatio`): «bosque de Carmen del Darién» empataba con proyectos que no eran.
- Cada respuesta necesitaba dos o tres vueltas con Gemini. En la capa gratuita, con 8 s de límite por respuesta, una saturación bastaba para caer en el mensaje genérico de «no tengo datos suficientes», que además era falso.
- No existía una forma de preguntar «¿cuántos proyectos hay?» o «¿cuál tiene el peor índice?», y el modelo llegó a afirmar el departamento de un proyecto sin ninguna evidencia.
- El chat conservaba el formato de WhatsApp: 300 caracteres y elegir proyecto con `PROYECTO 7`.

## Decisión
1. **El sistema identifica el proyecto antes que el modelo.** `ai/agent/resolver.py` indexa los nombres de la base, pondera cada palabra por su rareza (IDF), ignora palabras de dominio y nombres de departamentos, tolera tildes y errores de tipeo y distingue una coincidencia segura de una ambigua. Si hay dos candidatos («Pazcifico» y «Pazcifico Sur») el agente pregunta cuál sin llamar al modelo.
2. **Los datos se consultan antes de llamar al modelo.** Con el proyecto identificado, el agente ejecuta `obtener_auditoria` (y `obtener_perdida_anual` si la pregunta es de pérdida) y se los entrega al modelo en el mismo mensaje. Una sola llamada a Gemini basta, las evidencias quedan registradas y el validador de fidelidad sigue aplicando.
3. **Las preguntas frecuentes se responden sin modelo.** Saludo, gracias, «quién eres», y estado, alertas o índice de un proyecto salen de la base con plantillas (`assistant/community.py`): instantáneas, sin cuota de Gemini y sin posibilidad de inventar cifras.
4. **Si el modelo falla se responde con lo ya calculado**, no con un mensaje genérico. Sin proyecto, se dice que no se pudo consultar a la IA, no que faltan datos.
5. **Herramienta `resumen_portafolio`**: totales, conteo por categoría, orden por índice, tamaño o nombre y filtro por texto. Excluye los proyectos de demostración y avisa que no se registra departamento ni municipio.
6. **Chat web**: el límite de respuesta pasa a `COMMUNITY_MAX_CHARS` (700 por defecto); la API devuelve la ficha del proyecto y sugerencias según la etapa de la conversación (consentimiento, sin proyecto, con proyecto); la web ofrece botones, buscador de proyecto y tarjeta con enlace a su ficha.
7. **Evaluación con proyectos reales**: `bosquevivo eval --cases v2` (o `todos`) ejecuta 25 casos sobre proyectos reales y los revisa con las mismas reglas del conjunto original más `must_contain` y `must_contain_any`.

## Consecuencias
- Prompt `v3`: alcance cerrado a Bosque Vivo, no inventar ubicaciones, usar los datos ya consultados, nombres del índice v1.
- El mensaje «Proyecto identificado por el sistema» y los datos consultados viajan en el mensaje del usuario, marcados como datos y no como instrucciones.
- Un nombre que coincide con una palabra rara de un solo proyecto se toma como mención; el modelo recibe el nombre identificado y la pregunta original, y la ficha del chat muestra qué proyecto se usó.
- Quedan fuera de alcance: filtrar proyectos por departamento (no se registra) y preguntas sobre proyectos de reforestación, para los que el índice v1 aún no calcula resultado.
