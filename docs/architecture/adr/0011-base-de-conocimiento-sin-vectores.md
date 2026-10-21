# ADR 0011: Base de conocimiento sin vectores al inicio

- Estado: aceptada

## Decisión
El corpus (metodología, glosario, normativa, preguntas frecuentes) son unas decenas de fragmentos. Se busca con TF-IDF sobre texto sin acentos y cada resultado devuelve su cita. Si el corpus crece, la tabla `kb_chunk` ya tiene la columna `embedding` para pasar a similitud coseno.
