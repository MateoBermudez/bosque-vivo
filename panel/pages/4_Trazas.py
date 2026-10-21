import pandas as pd
import streamlit as st

import client

st.title("Trazas del agente")
rows = client.traces(100)
if not rows:
    st.info("Todavía no hay consultas registradas.")
    st.stop()

frame = pd.DataFrame(rows)
frame["herramientas"] = frame["tools"].apply(lambda t: ", ".join(t))
frame = frame.drop(columns=["tools"])
st.dataframe(frame, hide_index=True, use_container_width=True)
fallback_rate = frame["used_fallback"].mean()
st.metric("Respuestas de respaldo", f"{fallback_rate:.0%}")
st.caption("p50 y p90 de latencia por consulta (ms)")
st.write(frame["latency_ms"].describe(percentiles=[0.5, 0.9]).to_frame().T)
