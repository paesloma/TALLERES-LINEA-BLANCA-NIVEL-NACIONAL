import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# Configuración de página ancha
st.set_page_config(page_title="Red Nacional TVS - Postventa", layout="wide")

st.markdown("## 🛠️ Red Nacional de Servicios Técnicos")

@st.cache_data
def load_data():
    # Carga el archivo CSV final que ya verificamos
    return pd.read_csv('data_red_nacional_final.csv')

try:
    df = load_data()

    # --- BARRA LATERAL: FILTROS DINÁMICOS ---
    st.sidebar.header("🔍 Buscador y Filtros")
    
    # 1. Filtro Multiselect por Ciudad Base
    ciudades_lista = sorted(df['CIUDAD BASE'].unique())
    seleccion_ciudad = st.sidebar.multiselect("📍 Ciudad Base del Taller:", ciudades_lista)

    # 2. Filtro Buscable por Zona de Cobertura
    # Esto busca dentro del texto de la columna de cobertura
    busqueda_cobertura = st.sidebar.text_input("❄️ Buscar Zona de Cobertura (ej: Daule, Pastaza, Quito):", 
                                             placeholder="Escribe aquí para filtrar...")

    # Aplicación de la lógica de filtros
    df_filt = df.copy()
    
    if seleccion_ciudad:
        df_filt = df_filt[df_filt['CIUDAD BASE'].isin(seleccion_ciudad)]
    
    if busqueda_cobertura:
        # Busca el texto ignorando mayúsculas/minúsculas
        df_filt = df_filt[df_filt['COBERTURA INST AA Y LINEA BLANCA'].str.contains(busqueda_cobertura, case=False, na=False)]

    # Cálculo de Zoom e Indicador
    if not df_filt.empty:
        centro_lat = df_filt['LAT_VIZ'].mean()
        centro_lon = df_filt['LON_VIZ'].mean()
        zoom_level = 12 if (seleccion_ciudad or busqueda_cobertura) else 7
        st.success(f"✅ Se encontraron **{len(df_filt)}** talleres disponibles.")
    else:
        centro_lat, centro_lon, zoom_level = -1.45, -78.5, 7
        st.error("❌ No se encontraron resultados para tu búsqueda.")

    # --- MAPA INTERACTIVO ---
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=zoom_level, tiles="CartoDB positron")
    marker_cluster = MarkerCluster(options={'maxClusterRadius': 30}).add_to(m)

    for _, row in df_filt.iterrows():
        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 12px; width: 230px;">
            <b style="color: #E74C3C; font-size: 14px;">{row['NOMBRE DEL TALLER']}</b><br>
            <hr style="margin: 5px 0;">
            <b>📍 Ciudad:</b> {row['CIUDAD BASE']}<br>
            <b>📞 Teléfono:</b> {row['NUMEROS DE CONTACTO']}<br>
            <hr style="margin: 5px 0;">
            <b style="color: #2E86C1;">Cobertura Detallada:</b><br>
            <div style="max-height: 80px; overflow-y: auto; border: 1px solid #eee; padding: 3px;">
                {row['COBERTURA INST AA Y LINEA BLANCA']}
            </div>
        </div>
        """
        folium.Marker(
            location=[row['LAT_VIZ'], row['LON_VIZ']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{row['NOMBRE DEL TALLER']}",
            icon=folium.Icon(color="red", icon="wrench", prefix="fa")
        ).add_to(marker_cluster)

    st_folium(m, width="100%", height=550, key="mapa_dinamico")

    # --- TABLA DESPLAZABLE Y BUSCABLE ---
    st.markdown("### 📋 Directorio y Coberturas (Desplazable)")
    
    # Seleccionamos las columnas clave
    cols_vista = ['NOMBRE DEL TALLER', 'CIUDAD BASE', 'DIRECCION', 'NUMEROS DE CONTACTO', 'COBERTURA INST AA Y LINEA BLANCA']
    
    # st.dataframe permite de forma nativa desplazar (scroll) y buscar (CTRL+F)
    st.dataframe(
        df_filt[cols_vista], 
        use_container_width=True, 
        hide_index=True
    )

except Exception as e:
    st.error(f"Error en la carga: {e}")
