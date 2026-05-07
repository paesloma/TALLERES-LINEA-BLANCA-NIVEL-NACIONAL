import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# Configuración de pantalla completa
st.set_page_config(page_title="Red Nacional TVS - Postventa", layout="wide")

st.markdown("## 🛠️ Red Nacional de Servicios Técnicos")

@st.cache_data
def load_data():
    # Cargamos el archivo que acabas de subir
    df = pd.read_csv('data_red_nacional_final.csv')
    return df

try:
    df = load_data()

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.header("Filtros de Búsqueda")
    ciudades_lista = sorted(df['CIUDAD BASE'].unique())
    seleccion = st.sidebar.multiselect("📍 Seleccionar Ciudad Base:", ciudades_lista)

    # Lógica de Filtrado y Zoom
    if seleccion:
        df_display = df[df['CIUDAD BASE'].isin(seleccion)]
        # Calculamos el centro para el zoom dinámico
        centro_lat = df_display['LAT_VIZ'].mean()
        centro_lon = df_display['LON_VIZ'].mean()
        # Si es una sola ciudad, hacemos zoom cercano (13), si son varias, zoom medio (9)
        zoom_level = 13 if len(seleccion) == 1 else 9
    else:
        df_display = df
        centro_lat = -1.45  # Centro de Ecuador
        centro_lon = -78.5
        zoom_level = 7

    st.info(f"Mostrando **{len(df_display)}** talleres registrados.")

    # --- MAPA INTERACTIVO ---
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=zoom_level, tiles="CartoDB positron")
    
    # Agrupación de marcadores (Cluster)
    marker_cluster = MarkerCluster(options={'maxClusterRadius': 30}).add_to(m)

    for _, row in df_display.iterrows():
        # Diseño del Popup
        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 12px; width: 220px;">
            <b style="color: #E74C3C; font-size: 14px;">{row['NOMBRE DEL TALLER']}</b><br>
            <hr style="margin: 5px 0;">
            <b>🏠 Dirección:</b> {row['DIRECCION']}<br>
            <b>📞 Contacto:</b> {row['NUMEROS DE CONTACTO']}<br>
            <hr style="margin: 5px 0;">
            <b>❄️ Cobertura:</b><br>{row['COBERTURA INST AA Y LINEA BLANCA']}
        </div>
        """
        
        folium.Marker(
            location=[row['LAT_VIZ'], row['LON_VIZ']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{row['NOMBRE DEL TALLER']} - {row['CIUDAD BASE']}",
            icon=folium.Icon(color="red", icon="wrench", prefix="fa")
        ).add_to(marker_cluster)

    # Mostrar el mapa
    st_folium(m, width="100%", height=550, key="mapa_principal")

    # --- TABLA DE INFORMACIÓN BÁSICA (SIEMPRE VISIBLE) ---
    st.markdown("### 📋 Directorio de Contactos")
    
    # Seleccionamos solo las columnas clave para la lista rápida
    cols_basicas = ['NOMBRE DEL TALLER', 'CIUDAD BASE', 'DIRECCION', 'NUMEROS DE CONTACTO']
    
    st.dataframe(
        df_display[cols_basicas], 
        use_container_width=True, 
        hide_index=True
    )

except Exception as e:
    st.error(f"Error al cargar la aplicación: {e}")
    st.info("Asegúrate de que el archivo 'data_red_nacional_final.csv' esté en la carpeta principal del repositorio.")
