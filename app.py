import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

st.set_page_config(page_title="Red Nacional TVS - Postventa", layout="wide")

st.markdown("## 🛠️ Red Nacional de Servicios Técnicos")

@st.cache_data
def load_data():
    df = pd.read_csv('data_red_nacional_final.csv')
    df.columns = df.columns.str.strip()
    df = df.replace(r'\r\n|\r|\n', ' ', regex=True)
    return df

try:
    df = load_data()

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.header("🔍 Buscador y Filtros")
    ciudades_lista = sorted(df['CIUDAD BASE'].unique())
    seleccion_ciudad = st.sidebar.multiselect("📍 Ciudad Base del Taller:", ciudades_lista)
    busqueda_cobertura = st.sidebar.text_input("❄️ Buscar Zona de Cobertura:", placeholder="Ej: Daule...")

    # Aplicación de filtros
    df_filt = df.copy()
    if seleccion_ciudad:
        df_filt = df_filt[df_filt['CIUDAD BASE'].isin(seleccion_ciudad)]
    if busqueda_cobertura:
        df_filt = df_filt[df_filt['COBERTURA INST AA Y LINEA BLANCA'].str.contains(busqueda_cobertura, case=False, na=False)]

    # --- CONFIGURACIÓN DE LÍMITES (ECUADOR) ---
    # Definimos el recuadro que el usuario no puede saltar
    # [lat_min, lon_min], [lat_max, lon_max]
    limites_ecuador = [[-5.2, -81.5], [2.5, -75.0]] 

    if not df_filt.empty:
        centro_lat = df_filt['LAT_VIZ'].mean()
        centro_lon = df_filt['LON_VIZ'].mean()
        zoom_level = 12 if (seleccion_ciudad or busqueda_cobertura) else 7
    else:
        centro_lat, centro_lon, zoom_level = -1.45, -78.5, 7

    # --- MAPA CON RESTRICCIÓN ---
    m = folium.Map(
        location=[centro_lat, centro_lon], 
        zoom_start=zoom_level, 
        tiles="CartoDB positron",
        max_bounds=True,           # ACTIVAR RESTRICCIÓN
        min_lat=limites_ecuador[0][0],
        max_lat=limites_ecuador[1][0],
        min_lon=limites_ecuador[0][1],
        max_lon=limites_ecuador[1][1]
    )

    marker_cluster = MarkerCluster(options={'maxClusterRadius': 30}).add_to(m)

    for _, row in df_filt.iterrows():
        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 12px; width: 230px;">
            <b style="color: #E74C3C; font-size: 14px;">{row['NOMBRE DEL TALLER']}</b><br>
            <hr style="margin: 5px 0;">
            <b>📞 Contacto:</b> {row['NUMEROS DE CONTACTO']}<br>
            <hr style="margin: 5px 0;">
            <b style="color: #2E86C1;">Cobertura:</b><br>
            <div style="max-height: 80px; overflow-y: auto; font-size: 11px;">
                {row['COBERTURA INST AA Y LINEA BLANCA']}
            </div>
        </div>
        """
        folium.Marker(
            location=[row['LAT_VIZ'], row['LON_VIZ']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=row['NOMBRE DEL TALLER'],
            icon=folium.Icon(color="red", icon="wrench", prefix="fa")
        ).add_to(marker_cluster)

    # Renderizado
    st_folium(m, width="100%", height=500, key="mapa_restringido")

    # --- TABLA INFERIOR ---
    st.markdown("### 📋 Directorio Detallado")
    st.dataframe(df_filt[['NOMBRE DEL TALLER', 'CIUDAD BASE', 'NUMEROS DE CONTACTO', 'COBERTURA INST AA Y LINEA BLANCA', 'DIRECCION']], 
                 use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
