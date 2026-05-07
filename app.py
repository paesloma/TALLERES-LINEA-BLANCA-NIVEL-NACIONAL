import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from PIL import Image
import os

# 1. Configuración de pantalla ancha
st.set_page_config(page_title="Red Nacional TVS - Postventa", layout="wide")

# --- CABECERA CON IMAGEN ---
# Nombre del archivo que debe estar en GitHub
nombre_img = 'banner_header.png'

if os.path.exists(nombre_img):
    try:
        img = Image.open(nombre_img)
        st.image(img, use_container_width=True)
    except Exception as e:
        st.error(f"Error al abrir la imagen: {e}")
else:
    # Banner de respaldo elegante si la imagen no se encuentra
    st.markdown(
        """
        <div style="background: linear-gradient(90deg, #d32f2f 0%, #1976d2 100%); padding:30px; border-radius:15px; text-align:center; margin-bottom:20px;">
            <h1 style="color:white; margin:0; font-family:sans-serif; letter-spacing: 2px;">TVS ECUADOR</h1>
            <p style="color:white; margin:0; opacity:0.8; font-size:18px;">Red Nacional de Servicios Técnicos - Postventa</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

@st.cache_data
def load_data():
    # Carga y limpieza automática de nombres de columnas
    df = pd.read_csv('data_red_nacional_final.csv')
    df.columns = df.columns.str.strip()
    # Limpiar saltos de línea para que la tabla sea legible
    df = df.replace(r'\r\n|\r|\n', ' ', regex=True)
    return df

try:
    df = load_data()

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.header("🔍 Buscador y Filtros")
    
    ciudades_lista = sorted(df['CIUDAD BASE'].unique())
    seleccion_ciudad = st.sidebar.multiselect("📍 Ciudad Base del Taller:", ciudades_lista)

    busqueda_cobertura = st.sidebar.text_input("❄️ Buscar Zona de Cobertura (ej: Daule, Salitre):", 
                                             placeholder="Escribe aquí para filtrar...")

    # Aplicación de filtros
    df_filt = df.copy()
    if seleccion_ciudad:
        df_filt = df_filt[df_filt['CIUDAD BASE'].isin(seleccion_ciudad)]
    if busqueda_cobertura:
        df_filt = df_filt[df_filt['COBERTURA INST AA Y LINEA BLANCA'].str.contains(busqueda_cobertura, case=False, na=False)]

    # --- CONFIGURACIÓN DE LÍMITES (ECUADOR) ---
    limites_ecuador = [[-5.2, -81.5], [2.5, -75.0]] 

    if not df_filt.empty:
        centro_lat = df_filt['LAT_VIZ'].mean()
        centro_lon = df_filt['LON_VIZ'].mean()
        # Zoom 13 si hay filtro (ciudad), zoom 7 para general
        zoom_level = 13 if (seleccion_ciudad or busqueda_cobertura) else 7
    else:
        centro_lat, centro_lon, zoom_level = -1.45, -78.5, 7

    # --- MAPA CON RESTRICCIÓN ---
    m = folium.Map(
        location=[centro_lat, centro_lon], 
        zoom_start=zoom_level, 
        tiles="CartoDB positron",
        max_bounds=True,
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
            <b>📍 Ciudad:</b> {row['CIUDAD BASE']}<br>
            <b>📞 Contacto:</b> {row['NUMEROS DE CONTACTO']}<br>
            <hr style="margin: 5px 0;">
            <b style="color: #2E86C1;">Cobertura Detallada:</b><br>
            <div style="max-height: 80px; overflow-y: auto; background: #f9f9f9; padding: 5px; border-radius:5px;">
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

    st_folium(m, width="100%", height=550, key="mapa_final_tvs")

    # --- TABLA INFERIOR DINÁMICA ---
    st.markdown("### 📋 Directorio y Coberturas")
    cols_vista = ['NOMBRE DEL TALLER', 'CIUDAD BASE', 'NUMEROS DE CONTACTO', 'COBERTURA INST AA Y LINEA BLANCA', 'DIRECCION']
    
    st.dataframe(df_filt[cols_vista], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Se produjo un error: {e}")
