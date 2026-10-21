import pydeck as pdk
import streamlit as st

import client
from view import centroid

st.title("Mapa del polígono")
project_id = st.session_state.get("project_id")
if project_id is None:
    st.info("Elija un proyecto en la página principal.")
    st.stop()

feature = client.geometry(project_id)
if not feature:
    st.warning("No se encontró la geometría del proyecto.")
    st.stop()

lat, lon = centroid(feature)
layer = pdk.Layer(
    "GeoJsonLayer",
    data=feature,
    get_fill_color=[47, 125, 70, 90],
    get_line_color=[47, 125, 70, 255],
    line_width_min_pixels=2,
)
view = pdk.ViewState(latitude=lat, longitude=lon, zoom=10)
st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, map_style=None))
