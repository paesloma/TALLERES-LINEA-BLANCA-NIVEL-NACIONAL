import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

st.set_page_config(page_title="Red Nacional TVS", layout="wide")

st.markdown("## 🛠️ Red Nacional de Servicios Técnicos")

@st.cache_data
def load_data():
    # Carga el archivo final con jitter que generamos anteriormente
    return pd.read_csv('data_red_nacional_final.csv')

try:
    df = load_data()

    # --- SECCIÓN DE FILTROS ---
    st.sidebar.header("Filtros")
    ciudades_disponibles = sorted(df['CIUDAD BASE'].unique())
    seleccion = st.sidebar.multiselect("Seleccionar Ciudad:", ciudades_disponibles)

    # Lógica de filtrado y Zoom Dinámico
    if seleccion:
        df_filt = df[df['CIUDAD BASE'].isin(seleccion)]
        # Calculamos el centro promedio de los talleres seleccionados para hacer el ZOOM
        centro_lat = df_filt['LAT_VIZ'].mean()
        centro_lon = df_filt['LON_VIZ'].mean()
        zoom_inicial = 12 if len(seleccion) == 1 else 8 # Zoom más cercano si es solo una ciudad
    else:
        df_filt = df
        centro_lat = -1.45
        centro_lon = -78.5
        zoom_inicial = 7

    # --- MAPA INTERACTIVO ---
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=zoom_inicial, tiles="CartoDB positron")
    marker_cluster = MarkerCluster(options={'maxClusterRadius': 30}).add_to(m)

    for _, row in df_filt.iterrows():
        html_info = f"""
        <div style="font-family: sans-serif; font-size: 12px; width: 220px;">
            <b style="color: #d32f2f;">{row['NOMBRE DEL TALLER']}</b><br>
            <hr style="margin: 5px 0;">
            <b>📍 Ciudad:</b> {row['CIUDAD BASE']}<br>
            <b>📞 Contacto:</b> {row['NUMEROS DE CONTACTO']}<br>
            <b>❄️ Cobertura:</b> {row['COBERTURA INST AA Y LINEA BLANCA']}
        </div>
        """
        folium.Marker(
            location=[row['LAT_VIZ'], row['LON_VIZ']],
            popup=folium.Popup(html_info, max_width=250),
            tooltip=row['NOMBRE DEL TALLER'],
            icon=folium.Icon(color="red", icon="wrench", prefix="fa")
        ).add_to(marker_cluster)

    st_folium(m, width="100%", height=500, key="mapa_red")

    # --- LISTA DE INFORMACIÓN BÁSICA (Siempre visible abajo) ---
    st.markdown("### 📋 Directorio de Talleres Seleccionados")
    
    # Seleccionamos solo las columnas básicas para la lista
    columnas_basicas = ['NOMBRE DEL TALLER', 'CIUDAD BASE', 'DIRECCION ', 'NUMEROS DE CONTACTO']
    
    # Mostramos la tabla (siempre visible)
    st.dataframe(
        df_filt[columnas_basicas], 
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error(f"Error: {e}")
