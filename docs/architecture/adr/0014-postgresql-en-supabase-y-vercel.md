# ADR 0014: PostgreSQL en Supabase y despliegue en Vercel

- Estado: aceptada (reemplaza en producción a ADR 0002 y ADR 0003)

## Contexto
El equipo quiere el sistema en línea sin depender de un computador encendido. SQLite necesita un disco persistente, que Vercel no ofrece, y las librerías de cálculo satelital superan el límite de 500 MB de una función de Python en Vercel.

## Decisión
- Base de datos de producción: PostgreSQL administrado en Supabase, por el *Transaction pooler* (IPv4, puerto 6543), con `NullPool` en funciones sin estado y sin sentencias preparadas. SQLite se mantiene para desarrollo local y pruebas; la suite completa también corre contra PostgreSQL en la CI.
- Sitio y API en dos proyectos de Vercel (`web/` y `backend/`). La API instala solo el núcleo de dependencias; el cálculo satelital (extra `procesamiento`) se ejecuta desde un computador con la CLI contra la misma base.
- En Vercel las tareas se procesan en la misma petición (`JOBS_MODE=auto`), los reportes se generan al vuelo y los archivos temporales van a `/tmp`.
- `bosquevivo migrate-db` copia una base SQLite existente a PostgreSQL.

## Consecuencias
- URL estable y sin servidor propio; copias de seguridad a cargo de Supabase.
- El cálculo de auditorías nuevas sigue requiriendo un computador del equipo.
- La capa gratuita de Supabase pausa el proyecto tras una semana sin uso.
