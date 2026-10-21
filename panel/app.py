import streamlit as st

import client
from view import category_color, components_frame

st.set_page_config(page_title="Bosque Vivo", page_icon="🌳", layout="wide")
st.title("Bosque Vivo")
st.caption(
    "Correspondencia entre lo declarado por proyectos de carbono forestal y lo observado "
    "desde el satélite. Panel de solo lectura."
)

if not client.health():
    st.error("La API no responde. Inicie el backend e intente de nuevo.")
    st.stop()

try:
    items = client.projects()
except client.ApiError as exc:
    st.error(str(exc))
    st.stop()

if not items:
    st.info("Aún no hay proyectos cargados.")
    st.stop()

countries = sorted({p["country"] for p in items if p["country"]})
selected_country = st.sidebar.selectbox("País", ["Todos", *countries])
visible = [p for p in items if selected_country in ("Todos", p["country"])]
names = {f"{p['name']} ({p['source_registry']} {p['registry_id']})": p for p in visible}
choice = st.sidebar.selectbox("Proyecto", list(names))
project = names[choice]

audit = client.audit(project["id"])
col1, col2, col3 = st.columns(3)
if audit and audit.get("result"):
    result = audit["result"]
    score = "—" if result["score"] is None else f"{result['score']:.0f} / 100"
    col1.metric("Índice de correspondencia", score)
    col2.markdown(
        f'**Categoría**<br><span style="color:{category_color(result["category"])};'
        f'font-size:1.6rem">{result["category"]}</span>',
        unsafe_allow_html=True,
    )
    col3.metric("Confianza", result["confidence_label"].capitalize())
    st.info(result["narrative"])
    frame = components_frame(result["components"])
    if not frame.empty:
        st.subheader("Componentes")
        st.dataframe(frame, hide_index=True, use_container_width=True)
    st.caption(
        f"Corrida {audit['id']} · índice {audit['index_version']} · "
        f"código {audit['git_sha'] or 'n/d'} · {audit['created_at'][:10]}"
    )
else:
    st.warning("Este proyecto todavía no tiene una auditoría calculada.")

st.subheader("Navegación")
st.page_link("pages/1_Serie_NDVI.py", label="Serie de NDVI y comparación por año")
st.page_link("pages/2_Mapa.py", label="Mapa del polígono")
st.page_link("pages/3_Chat_del_auditor.py", label="Chat del auditor")
st.page_link("pages/4_Trazas.py", label="Trazas del agente")

st.session_state["project_id"] = project["id"]
st.session_state["project_name"] = project["name"]
