import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from PIL import Image
import os

# 1. Configuración de pantalla ancha
st.set_page_config(page_title="Red Nacional TVS - Postventa", layout="wide")

# --- CABECERA POSICIONADA A LA DERECHA ---
nombre_img = 'banner_header.png'

# Creamos dos columnas: la primera más ancha (vacia o para título) y la segunda para el logo
col_titulo, col_logo = st.columns([3, 1]) 

with col_titulo:
    st.markdown("<h1 style='margin-top: 10px;'>Gestión de Postventa</h1>", unsafe_allow_html=True)
    st.caption("Red Nacional de Servicios Técnicos - TVS Ecuador")

with col_logo:
    if os.path.exists(nombre_img):
        try:
            img = Image.open(nombre_img)
            # Mostramos la imagen pequeña en la columna de la derecha
            st.image(img, use_container_width=True)
        except Exception as e:
            st.error(f"Error imagen: {e}")
    else:
        # Mini banner de respaldo si no hay imagen
        st.markdown(
            """
            <div style="background: #d32f2f; padding:10px; border-radius:5px; text-align:center;">
                <b style="color:white; font-size:12px;">TVS ECUADOR</b>
            </div>
            """, 
            unsafe_allow_html=True
        )

st.markdown("---")

@st.cache_data
def load_data():
    df = pd.read_csv('data_red_nacional_final.csv')
    df.columns = df.columns.str.strip()
    df = df.replace(r'\r\n|\r|\n', ' ', regex=True)
    return df

try:
    df = load_data()

    # --- FILTROS ---
    st.sidebar.header("🔍 Buscador")
    ciudades_lista = sorted(df['CIUDAD BASE'].unique())
    seleccion_ciudad = st.sidebar.multiselect("📍 Ciudad Base:", ciudades_lista)
    busqueda_cobertura = st.sidebar.text_input("❄️ Zona de Cobertura:", placeholder="Ej: Daule...")

    # Lógica de filtros
    df_filt = df.copy()
    if seleccion_ciudad:
        df_filt = df_filt[df_filt['CIUDAD BASE'].isin(seleccion_ciudad)]
    if busqueda_cobertura:
        df_filt = df_filt[df_filt['COBERTURA INST AA Y LINEA BLANCA'].str.contains(busqueda_cobertura, case=False, na=False)]

    # --- MAPA ---
    limites_ecuador = [[-5.2, -81.5], [2.5, -75.0]] 
    if not df_filt.empty:
        centro_lat, centro_lon = df_filt['LAT_VIZ'].mean(), df_filt['LON_VIZ'].mean()
        zoom_level = 13 if (seleccion_ciudad or busqueda_cobertura) else 7
    else:
        centro_lat, centro_lon, zoom_level = -1.45, -78.5, 7

    m = folium.Map(
        location=[centro_lat, centro_lon], zoom_start=zoom_level, 
        tiles="CartoDB positron", max_bounds=True,
        min_lat=limites_ecuador[0][0], max_lat=limites_ecuador[1][0],
        min_lon=limites_ecuador[0][1], max_lon=limites_ecuador[1][1]
    )

    marker_cluster = MarkerCluster(options={'maxClusterRadius': 30}).add_to(m)

    for _, row in df_filt.iterrows():
        popup_html = f"<b>{row['NOMBRE DEL TALLER']}</b><br>📞 {row['NUMEROS DE CONTACTO']}"
        folium.Marker(
            location=[row['LAT_VIZ'], row['LON_VIZ']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color="red", icon="wrench", prefix="fa")
        ).add_to(marker_cluster)

    st_folium(m, width="100%", height=500, key="mapa_tvs")

    # --- TABLA INFERIOR ---
    st.markdown("### 📋 Directorio Detallado")
    st.dataframe(df_filt[['NOMBRE DEL TALLER', 'CIUDAD BASE', 'NUMEROS DE CONTACTO', 'COBERTURA INST AA Y LINEA BLANCA', 'DIRECCION']], 
                 use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
