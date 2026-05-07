import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Red Nacional de Servicios", layout="wide")

st.title("📍 Red Nacional de Servicios Técnicos")
st.markdown("Visualización completa de todos los talleres y su cobertura a nivel nacional.")

# Cargar datos
@st.cache_data
def load_data():
    # Asegúrate de que el nombre coincida con el CSV que subiste a GitHub
    return pd.read_csv('data_red_nacional.csv')

df = load_data()

# Filtros en la barra lateral
st.sidebar.header("Opciones de Visualización")
todas_las_ciudades = sorted(df['CIUDAD BASE'].unique())
ciudad_filtro = st.sidebar.multiselect("Filtrar por Ciudad Base (opcional)", options=todas_las_ciudades)

# Lógica: Si no hay filtro seleccionado, mostrar TODOS. Si hay, mostrar filtrados.
if ciudad_filtro:
    df_display = df[df['CIUDAD BASE'].isin(ciudad_filtro)]
else:
    df_display = df

# Estadísticas rápidas
st.write(f"Mostrando **{len(df_display)}** talleres en el mapa.")

# Configuración del mapa centrado en Ecuador
m = folium.Map(location=[-1.45, -78.5], zoom_start=7, tiles="OpenStreetMap")

# Añadir todos los talleres correspondientes a la vista
for _, row in df_display.iterrows():
    if pd.notnull(row['LATITUD_BASE']) and pd.notnull(row['LONGITUD_BASE']):
        # Contenido del globo de información (Popup)
        popup_content = f"""
        <div style='font-family: Arial; font-size: 12px; width: 220px;'>
            <h4 style='color:#2E86C1; margin-bottom:5px;'>{row['NOMBRE DEL TALLER']}</h4>
            <b>📍 Ciudad:</b> {row['CIUDAD BASE']}<br>
            <b>🏠 Dirección:</b> {row['DIRECCION']}<br>
            <hr style='margin:5px 0;'>
            <b>❄️ Cobertura AA/LB:</b><br>{row['COBERTURA INST AA Y LINEA BLANCA']}<br>
            <hr style='margin:5px 0;'>
            <b>📞 Contacto:</b> {row['NUMEROS DE CONTACTO']}
        </div>
        """
        
        folium.Marker(
            location=[row['LATITUD_BASE'], row['LONGITUD_BASE']],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=f"{row['NOMBRE DEL TALLER']} - {row['CIUDAD BASE']}",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

# Renderizar mapa
st_folium(m, width="100%", height=600)

# Tabla de datos debajo del mapa
with st.expander("Ver lista completa de talleres"):
    st.dataframe(df_display, use_container_width=True)
