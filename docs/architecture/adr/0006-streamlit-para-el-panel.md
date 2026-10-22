# ADR 0006: Streamlit para el panel

- Estado: reemplazada por la [0013](0013-nextjs-para-el-frontend.md) (en revisión; `panel/` se conserva hasta aprobarla)

## Decisión
El panel es Streamlit, Python puro, que consume la API REST por HTTP. Incluye chat (`st.chat_message`), mapa (pydeck) y gráficos (Altair).

## Consecuencias
- Un solo lenguaje para el equipo y desarrollo rápido.
- El panel no accede a la base de datos: todo pasa por la API y su token de administración.
