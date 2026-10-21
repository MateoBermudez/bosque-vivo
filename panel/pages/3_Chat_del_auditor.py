import uuid

import streamlit as st

import client

st.title("Chat del auditor")
st.caption(
    "Asistente de IA con acceso de solo lectura a los datos del sistema. "
    "Sus respuestas citan evidencias y pueden contener errores."
)

if "chat_ref" not in st.session_state:
    st.session_state["chat_ref"] = uuid.uuid4().hex[:12]
    st.session_state["chat_history"] = []

for entry in st.session_state["chat_history"]:
    with st.chat_message(entry["role"]):
        st.write(entry["text"])
        if entry.get("meta"):
            st.caption(entry["meta"])

prompt = st.chat_input("Pregunte por un proyecto, el índice o la metodología")
if prompt:
    st.session_state["chat_history"].append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Consultando los datos..."):
            try:
                reply = client.chat(prompt, st.session_state["chat_ref"])
            except client.ApiError as exc:
                reply = {
                    "answer": str(exc),
                    "tools_called": [],
                    "evidence_ids": [],
                    "used_fallback": True,
                }
        st.write(reply["answer"])
        meta = f"Herramientas: {', '.join(reply['tools_called']) or 'ninguna'} · Evidencias: {len(reply['evidence_ids'])}"
        if reply["used_fallback"]:
            meta += " · respuesta de respaldo"
        st.caption(meta)
    st.session_state["chat_history"].append(
        {"role": "assistant", "text": reply["answer"], "meta": meta}
    )
