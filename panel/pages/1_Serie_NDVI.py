import altair as alt
import pandas as pd
import streamlit as st

import client
from view import ndvi_frame

st.title("Serie de NDVI")
project_id = st.session_state.get("project_id")
if project_id is None:
    st.info("Elija un proyecto en la página principal.")
    st.stop()

st.caption(st.session_state.get("project_name", ""))
data = client.series(project_id)
if not data or not data["ndvi"]:
    st.warning("No hay serie disponible para este proyecto.")
    st.stop()

frame = ndvi_frame(data)
line = (
    alt.Chart(frame)
    .mark_line(color="#2f7d46")
    .encode(
        x=alt.X("period:T", title="Fecha"),
        y=alt.Y("ndvi_mean:Q", title="NDVI", scale=alt.Scale(domain=[0, 1])),
        tooltip=["period:T", "ndvi_mean:Q", "valid_fraction:Q", "scene_count:Q"],
    )
)
layers = [line]
if data["t0"]:
    rule = (
        alt.Chart(pd.DataFrame({"t0": [pd.to_datetime(data["t0"])]}))
        .mark_rule(color="#b5651d", strokeDash=[6, 4])
        .encode(x="t0:T")
    )
    layers.append(rule)
st.altair_chart(alt.layer(*layers), use_container_width=True)
st.caption("Línea punteada: fecha de acreditación (T0). Los huecos indican nubes o falta de datos.")

st.subheader("Declarado y observado por año")
comparison = pd.DataFrame(data["comparison"])
if not comparison.empty:
    comparison = comparison.rename(
        columns={
            "year": "Año",
            "after_t0": "Posterior a T0",
            "ndvi_mean": "NDVI medio",
            "loss_ha": "Pérdida (ha)",
            "declared_note": "Periodo",
        }
    )
    st.dataframe(comparison, hide_index=True, use_container_width=True)
