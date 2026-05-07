import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from PIL import Image # Librería para manejo de imágenes

# 1. Configuración de pantalla ancha y título de pestaña
st.set_page_config(page_title="Red Nacional TVS - Postventa", layout="wide")

# --- CABECERA CON IMAGEN (NUEVO) ---
# Intenta cargar la imagen desde el repositorio. Asegúrate de subir 'banner_header.png' a GitHub.
try:
    # Cambia 'banner_header.png' por el nombre EXACTO de tu archivo de imagen subido
    imagen_cabecera = Image.open('banner_header.png')
    
    # Muestra la imagen. use_container_width=True la hace responsiva al ancho de la pantalla.
    st.image(imagen_cabecera, use_container_width=True)
    
except FileNotFoundError:
    # Mensaje de error amigable si no encuentra la imagen
    st.error("🚨 No se encontró el archivo de imagen para la cabecera.")
    st.info("Por favor, asegúrate de subir la imagen a tu repositorio de GitHub con el nombre 'banner_header.png' o actualiza este nombre en el código.")
    
# Separador visual opcional
st.markdown("---")

# --- CARGA DE DATOS ---
@st.cache_data
def load_data():
    df = pd.read_csv('data_red_nacional_final.csv')
    # Limpieza básica de columnas y datos
    df.columns = df.columns.str.strip()
    df = df.replace(r'\r\n|\r|\n', ' ', regex=True)
    return df

try:
    df = load_data()

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.header("🔍 Buscador y Filtros")
    
    # Filtro por Ciudad Base
    ciudades_lista = sorted(df['CIUDAD BASE'].unique())
    seleccion_ciudad = st.sidebar.multiselect("📍 Ciudad Base del Taller:", ciudades_lista)

    # Filtro por Zona de Cobertura (Búsqueda de texto)
    busqueda_cobertura = st.sidebar.text_input("❄️ Buscar Zona de Cobertura (ej: Daule):", 
                                             placeholder="Escribe para filtrar...")

    # Aplicación de filtros combinados
    df_filt = df.copy()
    
    if seleccion_ciudad:
        df_filt = df_filt[df_filt['CIUDAD BASE'].isin(seleccion_ciudad)]
    
    if busqueda_cobertura:
        df_filt = df_filt[df_filt['COBERTURA INST AA Y LINEA BLANCA'].str.contains(busqueda_cobertura, case=False, na=False)]

    # Métrica rápida de resultados
    st.info(f"Se encontraron **{len(df_filt)}** talleres registrados.")

    # --- CONFIGURACIÓN DE LÍMITES Y ZOOM DEL MAPA (ECUADOR) ---
    limites_ecuador = [[-5.2, -81.5], [2.5, -75.0]] 

    if not df_filt.empty:
        centro_lat = df_filt['LAT_VIZ'].mean()
        centro_lon = df_filt['LON_VIZ'].mean()
        zoom_level = 12 if (seleccion_ciudad or busqueda_cobertura) else 7
    else:
        centro_lat, centro_lon, zoom_level = -1.45, -78.5, 7

    # --- MAPA INTERACTIVO (CON RESTRICCIÓN) ---
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
        <div style="font-family: sans-serif; font-size: 12px; width: 230px; line-height: 1.5;">
            <b style="color: #E74C3C; font-size: 14px;">{row['NOMBRE DEL TALLER']}</b><br>
            <hr style="margin: 5px 0; border-top: 1px solid #eee;">
            <b>📞 Contacto:</b> {row['NUMEROS DE CONTACTO']}<br>
            <hr style="margin: 5px 0; border-top: 1px solid #eee;">
            <b style="color: #2E86C1;">❄️ Cobertura Detallada:</b><br>
            <div style="max-height: 80px; overflow-y: auto; font-size: 11px; background: #f9f9f9; padding: 3px;">
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

    # Renderizado del mapa
    st_folium(m, width="100%", height=500, key="mapa_restringido_final")

    # --- LISTA BÁSICA SIEMPRE VISIBLE ---
    st.markdown("### 📋 Directorio de Contactos y Coberturas")
    
    # Seleccionamos las columnas clave para la lista
    cols_tabla = ['NOMBRE DEL TALLER', 'CIUDAD BASE', 'DIRECCION', 'NUMEROS DE CONTACTO', 'COBERTURA INST AA Y LINEA BLANCA']
    
    st.dataframe(
        df_filt[cols_tabla], 
        use_container_width=True, 
        hide_index=True
    )

except Exception as e:
    st.error(f"Se produjo un error crítico en la aplicación: {e}")
