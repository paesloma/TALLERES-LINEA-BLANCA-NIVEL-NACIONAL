import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Red Nacional de Servicios", layout="wide")

st.title("📍 Red Nacional de Servicios Técnicos")
st.markdown("Consulta la cobertura de Instalación de AA y Línea Blanca en todo el país.")

# Cargar datos desde el CSV en GitHub (reemplaza con tu URL RAW si es necesario)
@st.cache_data
def load_data():
    # Para pruebas locales usa 'data_red_nacional.csv'. 
    # En producción usa la URL RAW de GitHub.
    return pd.read_csv('data_red_nacional.csv')

df = load_data()

# Filtros en la barra lateral
st.sidebar.header("Filtros")
ciudad_filtro = st.sidebar.multiselect("Seleccionar Ciudad Base", options=df['CIUDAD BASE'].unique())

if ciudad_filtro:
    df_filtered = df[df['CIUDAD BASE'].isin(ciudad_filtro)]
else:
    df_filtered = df

# Mapa de Folium
st.subheader("Mapa de Cobertura")
m = folium.Map(location=[-1.8312, -78.1834], zoom_start=7)

for _, row in df_filtered.iterrows():
    if pd.notnull(row['LATITUD_BASE']):
        popup_content = f"""
        <div style='font-family: sans-serif; font-size: 12px; width: 200px;'>
            <b style='color:#E74C3C;'>{row['NOMBRE DEL TALLER']}</b><br>
            <b>📍 Ciudad:</b> {row['CIUDAD BASE']}<br>
            <b>❄️ Cobertura AA/LB:</b> {row['COBERTURA INST AA Y LINEA BLANCA']}<br>
            <b>📞 Contacto:</b> {row['NUMEROS DE CONTACTO']}
        </div>
        """
        folium.Marker(
            location=[row['LATITUD_BASE'], row['LONGITUD_BASE']],
            popup=folium.Popup(popup_content, max_width=250),
            tooltip=row['NOMBRE DEL TALLER']
        ).add_to(m)

st_folium(m, width=1200, height=500)

# Mostrar Tabla de Datos
st.subheader("Detalles de Cobertura")
st.dataframe(df_filtered[['NOMBRE DEL TALLER', 'CIUDAD BASE', 'COBERTURA INST AA Y LINEA BLANCA', 'NUMEROS DE CONTACTO']], use_container_width=True)
