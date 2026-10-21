# Bosque Vivo — Agente de IA con Gemini (v3: local + Google AI Studio)

> Complementa [`PLAN_IMPLEMENTACION.md`](PLAN_IMPLEMENTACION.md), que contiene las decisiones vigentes, el stack, el equipo, el cronograma y los riesgos.

## 0. Decisiones que rigen este documento

| Tema | Decisión |
|---|---|
| **Modelo de IA** | **Gemini de Google AI Studio, capa gratuita, por API** (SDK oficial `google-genai`). **No se usa Ollama ni modelos locales.** |
| **Dónde corre** | El código del agente corre **en este computador**. Solo la inferencia ocurre en el servicio de Google. |
| **Escala** | Proyecto universitario, no tesis: un agente bien acotado, evaluado y demostrable, no un producto de producción. |
| **Nombre del modelo** | Va en variables de entorno (`GEMINI_MODEL` para razonar y ver imágenes, `GEMINI_MODEL_LIGHT` para clasificar/enrutar). Los modelos gratuitos y sus cuotas cambian: **verificar en AI Studio** cuál usar y qué límites tiene. |
| **Código abierto (OE2)** | Todo el código es propio y abierto. Gemini es un servicio gratuito de terceros, igual que GEE y WhatsApp. Queda como ADR. Una interfaz `LLMProvider` delgada documenta cómo se cambiaría de proveedor, sin construir soporte para varios. |

## 1. Qué es el agente

Un **asistente-analista con IA** que:

- **Razona en varios pasos:** decide qué datos necesita, los consulta con herramientas, verifica y responde.
- **Analiza imágenes:** miniaturas satelitales antes/después y, si el nivel lo permite, fotos del usuario.
- **Concluye con evidencia:** cada afirmación apunta a una corrida de auditoría, una imagen o un dato.
- **Responde preguntas abiertas** en texto libre ("¿están talando cerca de mi finca?", "¿por qué el índice de este proyecto es bajo?"), no solo comandos de un menú.
- **Sirve a dos públicos:** la comunidad rural por WhatsApp (lenguaje sencillo) y el auditor en el panel (detalle técnico).

### 1.1 Principio rector: la IA interpreta, el sistema mide

Los números (índice, hectáreas, porcentajes, fechas) los producen **pipelines deterministas** (GEE, Hansen, NDVI, índice). Gemini **no inventa cifras**: orquesta herramientas, interpreta imágenes y explica. Un **validador** comprueba que todo número de la respuesta exista en la evidencia; si no, se usa una respuesta de respaldo basada en plantilla. Esto es lo que hace defendible un agente en un tema donde una cifra errónea puede leerse como acusación.

---

## 2. Qué aporta Gemini (y qué ya no hace falta)

Un solo servicio cubre varias piezas que antes eran componentes separados:

| Necesidad | Con Gemini | Antes se pensaba en |
|---|---|---|
| Razonar y planificar | Modelo con razonamiento activable | LLM local |
| Llamar herramientas | *Function calling* | Framework de agentes |
| Respuestas estructuradas | Salida JSON con esquema | Parsers a medida |
| Ver imágenes | Entrada multimodal | VLM aparte |
| Entender notas de voz | Entrada de audio | Whisper |
| Leer PDD en PDF | Entrada de PDF | OCR + extractor |
| Búsqueda en conocimiento | Contexto largo y/o embeddings por API | pgvector + modelo de embeddings |

Verificar en la documentación vigente de la API qué combinaciones de funciones están soportadas por el modelo elegido (por ejemplo, llamar herramientas y pedir salida estructurada a la vez).

**Lo que se descarta por escala y por no usar modelos locales:** Ollama/vLLM, LiteLLM, Whisper, pgvector, Langfuse, MCP y el entrenamiento propio de un modelo de visión (queda como evolución futura).

---

## 3. Requisitos de la ampliación

Se agregan como revisión del ERS (control de cambios del OE1) **si el docente lo aprueba**.

| ID | Requisito | Nivel |
|---|---|---|
| **RF09** | Agente con razonamiento multi-paso y uso de herramientas sobre los datos del sistema | **Núcleo** |
| **RF15** | Base de conocimiento consultable (metodología, glosario, normativa, FAQ) con citas | **Núcleo** |
| **RF17** | Chat técnico del auditor en el panel (explicar el índice, comparar proyectos, pedir un reporte) | **Núcleo** |
| **RF10** | Análisis visual de escenas antes/después, con evaluación de calidad (nubes, humo, brumas) | Alta |
| **RF12** | Fotos y ubicación enviadas por el usuario, tratadas como evidencia no verificada | Media |
| **RF13** | Notas de voz entendidas por el agente | Media |
| **RF16** | Extracción asistida de declaraciones desde documentos de diseño (PDD), con revisión humana | Media |
| **RF14** | Alertas tempranas opt-in (cambios con Sentinel-2 y focos de calor de NASA FIRMS) | Opcional |
| **RF11** | Modelo propio de visión por computadora, entrenado y evaluado | Opcional / evolución futura |
| **RNF-IA1** | **Fidelidad numérica:** 100 % de las cifras citadas coinciden con la evidencia; si no, respaldo | Núcleo |
| **RNF-IA2** | **Incertidumbre explícita:** toda conclusión incluye confianza y limitaciones; "no hay datos suficientes" es respuesta válida | Núcleo |
| **RNF-IA3** | **Trazabilidad:** cada respuesta guarda herramientas usadas, evidencias, modelo y versión de prompt | Núcleo |
| **RNF-IA4** | **Lenguaje neutro:** nunca atribuir fraude o dolo; solo describir correspondencia observada | Núcleo |
| **RNF-IA5** | **Legibilidad:** respuestas a la comunidad en español sencillo, ≤ 300 caracteres por mensaje | Alta |
| **RNF-IA6** | **Seguridad del agente:** resistencia a inyección de instrucciones y límites de costo y de tasa | Alta |

### 3.1 Dos clases de consulta (ajuste del NFR de 10 s)

El ERS pide que el 90 % de las consultas se respondan en menos de 10 s. Un análisis con imágenes puede tardar más. Propuesta para acordar con el docente:

| Clase | Ejemplo | Meta |
|---|---|---|
| **Rápida** | "¿Cómo está el bosque de X?" (datos ya calculados) | p90 < 10 s, con indicador de "escribiendo" inmediato |
| **Profunda** | "Analiza si hubo tala cerca de mi finca" (genera imágenes, las analiza) | Acuse en < 10 s y resultado en pocos minutos |

---

## 4. Arquitectura del agente

```
                 ┌───────────────────────────────────────────────────────┐
 WhatsApp  ────▶ │  Entrada ─▶ Router ─▶ Bucle del agente (Gemini)       │ ──▶ Respuesta
 (texto/voz/foto)│  (texto,     (rol,     │  planifica ─▶ llama           │     + evidencias
 Panel (chat) ──▶│   audio,     clase,    │  herramientas ─▶ lee          │     + traza
                 │   imagen)    límites)  │  resultados ─▶ responde       │
                 │                        ▼                               │
                 │              Validador de fidelidad ◀── Evidencia      │
                 │              (si falla: respaldo con plantilla)        │
                 └──────┬─────────────────────────────┬──────────────────┘
                        │ herramientas                │ conocimiento
          ┌─────────────┼───────────────┐             ▼
          ▼             ▼               ▼        Base de conocimiento
   audit.queries   satellite       jobs (cálculo   (documentos del
   (índice, series (miniaturas,     profundo)       proyecto, glosario,
    pérdida)        Hansen, FIRMS)                  normativa)
```

### 4.1 Bucle (planificar, actuar, verificar)

1. **Router:** con el modelo ligero (o reglas) identifica rol (comunidad / auditor), clase (rápida / profunda), tipo de entrada (texto / audio / imagen) y si hay cuota disponible.
2. **Bucle del agente:** Gemini decide qué herramientas llamar. Cada herramienta valida su entrada con un esquema (Pydantic) y devuelve una **evidencia** con identificador.
3. **Tope de pasos:** máximo ~4–5 llamadas de herramientas por consulta (cada paso consume cuota de la capa gratuita).
4. **Validador de fidelidad:** comprueba que cifras, fechas y nombres de la respuesta estén en las evidencias. Si falla: un reintento y luego respaldo con plantilla.
5. **Respuesta:** adaptada al rol, con confianza y limitaciones. Se guarda la traza completa (`agent_run` / `agent_step`).

### 4.2 Herramientas

| Herramienta | Qué hace | Fuente |
|---|---|---|
| `buscar_proyecto(texto \| lat,lon)` | Resuelve el proyecto por nombre aproximado o por punto dentro de un polígono | SQLite + shapely + rapidfuzz |
| `obtener_auditoria(proyecto)` | Índice, componentes, confianza y fecha de cálculo | `audit.queries` |
| `obtener_serie_ndvi(proyecto, rango)` | Serie y tendencia | BD |
| `obtener_perdida_anual(proyecto)` | Hectáreas perdidas por año | Hansen GFC |
| `comparar_periodos(proyecto, t1, t2)` | Cambio entre dos fechas | Pipeline |
| `ver_imagenes(proyecto, t1, t2)` | Genera miniaturas antes/después (color natural, falso color, NDVI) y las entrega al modelo | GEE |
| `evaluar_calidad_escena(imagen)` | Nubes, humo, sombras, artefactos | Gemini (visión) |
| `analizar_foto_usuario(imagen, ubicacion?)` | Describe y clasifica una foto cruzándola con el polígono y la imagen satelital | Gemini (visión) |
| `focos_de_calor(proyecto, rango)` | Hotspots cercanos (opcional) | NASA FIRMS |
| `buscar_conocimiento(consulta)` | Metodología, glosario, normativa, FAQ, con cita | Base de conocimiento |
| `solicitar_calculo(proyecto)` | Encola un cálculo completo (asíncrono) | Trabajador en segundo plano |
| `generar_reporte(run_id)` | Reporte HTML/PDF | `reports` |
| `explicar_indice(run_id)` | Desglose de componentes y sensibilidad (rol auditor) | `audit` |

### 4.3 Ejemplo de traza

> **Usuaria (WhatsApp):** "Don Pedro dice que están talando cerca de mi finca, ¿es cierto?" + ubicación.
>
> 1. `buscar_proyecto(lat,lon)` → proyecto *X*.
> 2. `obtener_auditoria` → índice 61/100 (media), confianza media.
> 3. `obtener_perdida_anual` → pérdida de 14 ha en el último año.
> 4. `ver_imagenes(t1,t2)` + `evaluar_calidad_escena` → la escena posterior tiene 40 % de nubes.
> 5. Gemini compara las imágenes y describe un área despejada al noreste.
> 6. Validador: todas las cifras están en evidencias.
>
> **Respuesta:** "Hay señales de pérdida de árboles en el proyecto, unas 14 hectáreas en el último año, sobre todo al noreste. La confianza es media porque había nubes en una de las fotos. No es una acusación a nadie, solo lo que se ve desde el satélite. ¿Quiere que le envíe las imágenes de antes y después?"

---

## 5. Análisis de imágenes

**Regla:** Gemini **describe, compara y evalúa calidad**; **nunca cuantifica**. Las hectáreas y porcentajes salen del pipeline (NDVI, Hansen).

1. **Generación de imágenes (P2):** `SatelliteProvider.get_thumbnail(geom, fecha, tipo)` con GEE. Color natural, falso color (vegetación) y NDVI; antes y después, con la misma escala y orientación.
2. **Calidad de la escena (RF10):** Gemini devuelve JSON estructurado `{nubes: bajo|medio|alto, humo: si|no, sombras: si|no, utilizable: si|no, motivo}`. **Refuerza, no reemplaza**, la máscara de nubes (Cloud Score+ / SCL) y alimenta la confianza.
3. **Comparación antes/después:** Gemini describe diferencias visibles (claros, cambios de textura, quemas) y las **anota como interpretación**, citando las dos imágenes como evidencia.
4. **Fotos del usuario (RF12):**
   - El usuario manda foto y, opcionalmente, ubicación.
   - Gemini describe qué se ve y se cruza con la imagen satelital y el polígono.
   - **Es evidencia comunitaria no verificada** y la respuesta lo dice.
   - Privacidad: quitar EXIF, consentimiento específico, retención corta, borrado a petición, sin fotos de personas identificables. Recordar que las imágenes se procesan en un servicio externo.
5. **Validación:** comparar las salidas de calidad de imagen contra etiquetas humanas de ~30–50 pares de miniaturas (la evaluación de visión del OE4).

**Evolución futura (no obligatoria):** un modelo propio de detección de cambio entrenado con Kaggle/Colab (que no es local, pero sí gratuito), usando Hansen y Dynamic World como etiquetas, y comparado contra el umbral simple de ΔNDVI. Si el tiempo no alcanza, se documenta como trabajo futuro.

---

## 6. Conocimiento y documentos

### 6.1 Base de conocimiento (RF15)

- **Qué entra:** metodología del índice, glosario en lenguaje sencillo, preguntas frecuentes, normativa citada en el ERS (Leyes 1931/2018, 2169/2021, 1581/2012; Decreto 926/2017; Res. 1447/2018) y notas sobre Verra y Gold Standard.
- **Cómo (de menos a más):**
  1. **Empezar simple:** el corpus es pequeño (decenas de páginas). Los fragmentos relevantes se seleccionan por palabras clave y se incluyen en el contexto.
  2. **Si hace falta:** embeddings por la API de Gemini guardados en SQLite y similitud coseno con numpy.
- **Regla:** las respuestas de conocimiento **siempre citan la fuente**.

### 6.2 Extracción de declaraciones desde PDD (RF16, nivel medio)

1. Descargar los PDD públicos de los proyectos de validación.
2. Gemini lee el PDF y extrae, con salida estructurada: fecha de inicio de acreditación, línea base de deforestación, área, periodo de acreditación y metodología.
3. Cada campo guarda **cita textual y página**.
4. **Un humano valida** antes de pasar a `project_declaration`. Nada extraído por el modelo entra a un cálculo sin revisión.
5. Medir la exactitud contra campos etiquetados a mano.

---

## 7. Voz (RF13, nivel medio)

- Las notas de voz de WhatsApp (OGG/Opus) se envían a Gemini como entrada de audio, que las transcribe y las entiende en el mismo paso. No hace falta Whisper.
- La respuesta es en texto. Audio sintético solo si sobra tiempo.
- Medir la comprensión con acentos regionales y ruido (5–10 audios reales de voluntarios).
- Los audios también se procesan en un servicio externo: aplica el mismo consentimiento específico que las fotos.

---

## 8. Alertas tempranas (RF14, opcional)

- Un job periódico (`APScheduler`) revisa escenas nuevas de Sentinel-2 sobre proyectos suscritos y consulta NASA FIRMS (API gratuita con clave).
- Solo avisa si supera un umbral y el usuario aceptó las alertas (opt-in).
- Los avisos proactivos fuera de la ventana de 24 h de WhatsApp requieren **plantillas aprobadas por Meta**: iniciar el trámite temprano si se decide hacerlo.
- Se aborda **solo si el núcleo ya está cerrado**.

---

## 9. Gestión de la capa gratuita

La capa gratuita de Gemini tiene límites de peticiones por minuto y por día, y el contenido puede usarse para mejorar productos de Google (**verificar los términos vigentes**). El diseño lo asume:

| Medida | Detalle |
|---|---|
| **Modelo ligero para el router** | Clasificar y enrutar con el modelo más barato; el modelo principal solo para razonar y ver imágenes |
| **Tope de pasos** | Máx. ~4–5 llamadas por consulta, y un tope diario por usuario |
| **Caché** | Cachear respuestas de herramientas y resultados de evaluación para no repetir peticiones; las pruebas de evaluación usan caché |
| **Reintentos con espera** | Ante errores de límite de tasa (429) y errores transitorios |
| **Escalera de degradación** | Si no hay cuota: respuesta de respaldo con plantilla a partir de los datos ya calculados, y aviso al usuario ("el análisis profundo no está disponible ahora") |
| **Una clave por persona en desarrollo** | Cada integrante usa su clave para no agotar la cuota compartida; la instancia de demo usa una clave aparte |
| **Evaluación por lotes** | La evaluación completa se corre antes de cada hito, no en cada commit |
| **Bloqueos de seguridad del modelo** | Manejar respuestas bloqueadas o vacías como un error recuperable |
| **Privacidad** | No enviar teléfonos ni nombres (solo contenido mínimo); aviso al usuario de que un servicio externo procesa el mensaje; retención corta de trazas |

---

## 10. Módulos nuevos

Dentro de `backend/src/bosquevivo/` (ver estructura completa en `PLAN_IMPLEMENTACION.md`):

```
ai/
├─ llm/          cliente Gemini (google-genai), límites, caché, reintentos, contador de uso
├─ agent/        router, bucle, registro de herramientas, memoria de conversación, respaldo
│  └─ tools/     una función por herramienta, con esquema Pydantic y evidencia tipada
├─ guardrails/   validador de fidelidad numérica, política de lenguaje neutro, antiinyección
├─ prompts/      versionados (prompt_version), uno por rol (comunidad / auditor)
├─ knowledge/    carga de documentos, selección de fragmentos, citas
├─ vision/       generación de miniaturas, calidad de escena, fotos de usuario
└─ eval/         conjuntos de evaluación, métricas, ejecutor con caché
```

**Reglas de frontera:**
- El agente solo invoca herramientas registradas.
- Las herramientas solo leen (`audit.queries`, `satellite`).
- Nada en `ai/` escribe resultados de auditoría. Las acciones que escriben o consumen recursos (`solicitar_calculo`, `generar_reporte`) tienen límites de tasa y de rol.

---

## 11. Seguridad y ética del agente

- **Lenguaje neutro como política del sistema:** prohibido "fraude", "estafa" o atribuir intención. Se habla de "correspondencia observada" y de "señales". Se prueba en la evaluación.
- **Antiinyección:** el contenido de mensajes, imágenes, documentos y resultados de herramientas se trata como **datos, nunca como instrucciones**. El agente no tiene acceso a secretos ni a acciones administrativas.
- **Privacidad (Ley 1581):** teléfono solo como HMAC, consentimiento específico para fotos, audio y alertas, retención corta, borrado por comando ("borrar mis datos") que limpia también trazas y fotos. El aviso debe decir que la IA y el procesamiento los hace un tercero.
- **Sesgo y equidad:** probar con lenguaje regional y baja alfabetización; no asumir buena conectividad.
- **Transparencia:** el asistente se presenta como IA, advierte que sus conclusiones pueden ser imprecisas y ofrece contacto humano cuando la confianza es baja.

---

## 12. Evaluación de la IA (parte del OE4)

Un agente sin evaluación no es defendible. Se arma un **conjunto de evaluación** desde la semana 2 (20 casos al inicio, 40–60 al final) y se ejecuta con caché.

| Qué se mide | Cómo | Meta orientativa |
|---|---|---|
| **Fidelidad numérica** | Cada cifra de la respuesta debe estar en la evidencia | 100 % (RNF-IA1) |
| **Elección de herramientas** | Casos guionizados con la secuencia esperada | ≥ 85–90 % |
| **Neutralidad** | Preguntas que invitan a acusar o fuera de alcance | 100 % neutras o con aclaración |
| **Incertidumbre** | Casos sin datos o con nubes: debe decir que no puede concluir | 100 % |
| **Legibilidad** | Prueba con 5 personas no técnicas (comprensión) y límite de longitud | Comprensión ≥ 80 % |
| **Calidad de imagen (visión)** | Concordancia con etiquetas humanas en 30–50 pares | Reportar |
| **Voz** | Tasa de error con 5–10 audios reales | Reportar |
| **Extracción PDD** | Exactitud por campo contra etiquetado manual | Reportar |
| **Latencia** | p50/p90 por clase de consulta | Rápida p90 < 10 s |
| **Cuota** | Comportamiento al agotar la cuota (respaldo) | Sin errores visibles al usuario |
| **Seguridad** | Pruebas de inyección (texto, imagen con texto incrustado, PDD con instrucciones) | 0 fugas, 0 acciones no autorizadas |

Herramientas: casos parametrizados en `pytest`; las trazas viven en SQLite y se revisan en la página `/admin/trazas` del panel. Guardar cada versión de prompt y modelo con sus métricas: mostrar la evolución es evidencia de trabajo de ingeniería.

---

## 13. Equipo y cronograma

Equipo y cronograma completos en `PLAN_IMPLEMENTACION.md` (secciones 6 y 8). Lo específico del agente:

- **P4** es dueño del bucle, herramientas, prompts, validador y base de conocimiento. **P1** aporta el cliente Gemini (cuotas, caché, reintentos), el webhook y el consentimiento. **P2** entrega las miniaturas y las herramientas de datos con interfaces ya tipadas. **P3** entrega el índice, el conjunto de validación y la evaluación de la visión.
- **Niveles de entrega:**
  - **Núcleo:** RF09, RF15, RF17, RNF-IA1–4 y el pipeline RF01–RF08.
  - **Alta:** RF10 (visión), RNF-IA5–6.
  - **Media:** RF12, RF13, RF16 (elegir 1–2 según el tiempo).
  - **Opcional:** RF14, RF11.
- **Recorte si falta tiempo:** RF14 → RF11 → RF16 → RF13 → RF12 → RF10. **No se recorta** el agente con validador de fidelidad, la Ley 1581 ni la evaluación.

### 13.1 Semana 0 específica del agente

1. P1 y P4: crear la clave de AI Studio, probar una llamada simple con *function calling* y con una imagen, y medir la latencia.
2. P4: definir el esquema de herramientas, el formato de evidencia y el de traza; primer prompt con herramientas simuladas.
3. P3: listar 20 preguntas reales que haría una comunidad y un auditor (son el primer conjunto de evaluación).
4. Todos: confirmar con el docente las dos clases de consulta y la ampliación del ERS.

---

## 14. Riesgos específicos de la IA

| Riesgo | Mitigación |
|---|---|
| Alucina cifras o acusa | Validador de fidelidad, política de lenguaje neutro, respaldo con plantilla, evaluación |
| Cuota gratuita agotada en la demo | Caché, tope de pasos, escalera de degradación, modo demo con respuestas precalculadas, clave de demo separada |
| Cambio o retiro del modelo gratuito | Modelo en variable de entorno, prompts versionados, interfaz `LLMProvider` delgada, evaluación para detectar regresiones |
| Latencia > 10 s | Dos clases de consulta, precálculo, indicador de escritura, modelo ligero para el router |
| Gemini interpreta mal imágenes satelitales | No cuantifica nunca; salidas estructuradas; validación contra etiquetas humanas; confianza explícita |
| Nubes dejan las imágenes inútiles | Evaluar calidad antes de comparar; "no puedo concluir" como respuesta válida |
| Inyección de instrucciones (mensajes, fotos, PDD) | Datos ≠ instrucciones, mínimo privilegio, pruebas específicas |
| Datos sensibles enviados a un tercero | Minimización, consentimiento específico, aviso claro, sin teléfonos ni nombres, consulta con el docente |
| Respuestas bloqueadas por filtros del modelo | Manejo como error recuperable y respaldo |

---

## 15. ADRs adicionales

1. Gemini (AI Studio, capa gratuita) como único proveedor de IA, y su justificación frente al OE2.
2. Bucle del agente propio y mínimo (sin framework).
3. "La IA interpreta, el sistema mide": validador de fidelidad y respaldo con plantilla.
4. Dos clases de consulta (rápida / profunda).
5. Gestión de la capa gratuita: caché, topes y degradación.
6. Base de conocimiento sin vectores al inicio.
7. Modelo propio de visión como evolución futura.

---

## 16. Preguntas abiertas

**Resueltas:** GPU/servidor (no hay: este PC + API de Gemini) · modelo abierto o no (Gemini, documentado) · nivel (universitario).

**Pendientes:**
1. ¿Qué modelo de Gemini está disponible gratis en AI Studio y con qué límites? (Verificar el primer día.)
2. ¿El docente aprueba ampliar el ERS con RF09–RF17 y las dos clases de consulta?
3. ¿Se acepta procesar mensajes de voluntarios con un servicio externo (Gemini) con aviso y consentimiento?
4. ¿Fecha real de entrega? Define cuántas funciones medias caben.
5. ¿Hay 5 voluntarios para las pruebas de comprensión y el piloto?
