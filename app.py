import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# Configuración de la página
st.set_page_config(page_title="Red Nacional TVS", layout="wide")

st.markdown("## 🛠️ Red Nacional de Servicios Técnicos")
st.markdown("Consulta la ubicación y cobertura de todos los talleres a nivel nacional.")

# Función para cargar la data
@st.cache_data
def load_data():
    # Asegúrate de que el archivo CSV generado anteriormente esté en tu repositorio
    return pd.read_csv('data_red_nacional_final.csv')

try:
    df = load_data()

    # Barra lateral: Filtros
    st.sidebar.header("Filtros de Búsqueda")
    ciudades_disponibles = sorted(df['CIUDAD BASE'].unique())
    seleccion = st.sidebar.multiselect("Seleccionar Ciudad Base:", ciudades_disponibles)

    # Lógica de filtrado: Si no hay selección, muestra TODOS los talleres
    df_filt = df[df['CIUDAD BASE'].isin(seleccion)] if seleccion else df

    # Indicador de cantidad de talleres encontrados
    st.info(f"Se han encontrado **{len(df_filt)}** talleres en la selección actual.")

    # Creación del Mapa centrado en Ecuador
    # Coordenadas aproximadas del centro del país
    m = folium.Map(location=[-1.45, -78.5], zoom_start=7, tiles="OpenStreetMap")

    # Implementación de MarkerCluster para evitar solapamiento de puntos en la misma ciudad
    marker_cluster = MarkerCluster(options={'maxClusterRadius': 30}).add_to(m)

    for _, row in df_filt.iterrows():
        # Crear el diseño del Popup (Globo de información)
        html_info = f"""
        <div style="font-family: sans-serif; font-size: 12px; width: 240px; line-height: 1.5;">
            <b style="color: #d32f2f; font-size: 14px;">{row['NOMBRE DEL TALLER']}</b><br>
            <hr style="margin: 5px 0; border: 0; border-top: 1px solid #eee;">
            <b>📍 Ciudad Base:</b> {row['CIUDAD BASE']}<br>
            <b>🏠 Dirección:</b> {row['DIRECCION']}<br>
            <b>📞 Contacto:</b> {row['NUMEROS DE CONTACTO']}<br>
            <hr style="margin: 5px 0; border: 0; border-top: 1px solid #eee;">
            <b style="color: #2E86C1;">❄️ Cobertura AA y Línea Blanca:</b><br>
            <small>{row['COBERTURA INST AA Y LINEA BLANCA']}</small>
        </div>
        """
        
        # Añadir marcador al cluster
        folium.Marker(
            location=[row['LAT_VIZ'], row['LON_VIZ']],
            popup=folium.Popup(html_info, max_width=300),
            tooltip=f"{row['NOMBRE DEL TALLER']} ({row['CIUDAD BASE']})",
            icon=folium.Icon(color="red", icon="wrench", prefix="fa")
        ).add_to(marker_cluster)

    # Renderizar el mapa en Streamlit
    st_folium(m, width="100%", height=600, returned_objects=[])

    # Tabla de datos detallada en la parte inferior
    with st.expander("📂 Ver lista detallada de talleres y coberturas"):
        st.dataframe(
            df_filt[['NOMBRE DEL TALLER', 'CIUDAD BASE', 'DIRECCION', 'NUMEROS DE CONTACTO', 'COBERTURA INST AA Y LINEA BLANCA']], 
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Error al cargar el archivo de datos: {e}")
    st.warning("Asegúrate de que el archivo 'data_red_nacional_final.csv' esté presente en el repositorio de GitHub.")
