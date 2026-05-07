import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import urllib.parse
import qrcode
from io import BytesIO
import base64
import re

# 1. Configuración de pantalla
st.set_page_config(page_title="Red Nacional TVS - Postventa", layout="wide")

# --- CABECERA ESTILIZADA ---
st.markdown(
    """
    <div style="background: linear-gradient(90deg, #d32f2f 0%, #1976d2 100%); padding:20px; border-radius:10px; text-align:center; margin-bottom:20px;">
        <h1 style="color:white; margin:0; font-family:sans-serif; letter-spacing: 2px;">TVS ECUADOR</h1>
        <p style="color:white; margin:0; opacity:0.9; font-size:16px;">Directorio Nacional de Servicios Técnicos - Gestión de Postventa</p>
    </div>
    """, 
    unsafe_allow_html=True
)

@st.cache_data
def load_data():
    # Carga y limpieza de columnas
    df = pd.read_csv('data_red_nacional_final.csv')
    df.columns = df.columns.str.strip()
    df = df.replace(r'\r\n|\r|\n', ' ', regex=True)
    return df

# --- FUNCIONES DE CONTACTO Y QR ---

def extraer_primer_numero(texto):
    """Extrae solo el primer número telefónico válido para el QR"""
    if pd.isna(texto): return None
    numeros = re.findall(r'\d{7,10}', str(texto))
    if numeros:
        tel = numeros[0]
        if not tel.startswith('593'):
            tel = '593' + tel.lstrip('0')
        return tel
    return None

def generar_qr_base64(url):
    """Genera el código QR para mostrarlo en el mapa y tabla"""
    if not url: return ""
    qr = qrcode.QRCode(version=1, box_size=2, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"

def crear_enlace_wa(telefono_crudo):
    """Crea el link de WhatsApp con el primer número detectado"""
    numero_unico = extraer_primer_numero(telefono_crudo)
    if not numero_unico: return None
    mensaje = urllib.parse.quote("Hola, contacto desde la Red Nacional TVS. Necesito soporte técnico.")
    return f"https://wa.me/{numero_unico}?text={mensaje}"

try:
    df = load_data()

    # --- BARRA LATERAL: BUSCADOR ---
    st.sidebar.header("🔍 Buscador")
    ciudades_lista = sorted(df['CIUDAD BASE'].unique())
    seleccion_ciudad = st.sidebar.multiselect("📍 Ciudad Base:", ciudades_lista)
    busqueda_cobertura = st.sidebar.text_input("❄️ Zona de Cobertura:", placeholder="Ej: Daule, Pastaza...")

    # Aplicar filtros
    df_filt = df.copy()
    if seleccion_ciudad:
        df_filt = df_filt[df_filt['CIUDAD BASE'].isin(seleccion_ciudad)]
    if busqueda_cobertura:
        df_filt = df_filt[df_filt['COBERTURA INST AA Y LINEA BLANCA'].str.contains(busqueda_cobertura, case=False, na=False)]

    # Procesar WhatsApp y QRs
    df_filt['WA_Link'] = df_filt['NUMEROS DE CONTACTO'].apply(crear_enlace_wa)
    df_filt['QR_Img'] = df_filt['WA_Link'].apply(generar_qr_base64)

    # --- MAPA INTERACTIVO ---
    limites_ecuador = [[-5.2, -81.5], [2.5, -75.0]] 
    centro_lat = df_filt['LAT_VIZ'].mean() if not df_filt.empty else -1.45
    centro_lon = df_filt['LON_VIZ'].mean() if not df_filt.empty else -78.5
    zoom_level = 13 if (seleccion_ciudad or busqueda_cobertura) else 7

    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=zoom_level, tiles="CartoDB positron", max_bounds=True)
    marker_cluster = MarkerCluster(options={'maxClusterRadius': 30}).add_to(m)

    for _, row in df_filt.iterrows():
        popup_html = f"""
        <div style='font-family:sans-serif; width:220px;'>
            <div style='text-align:center;'>
                <b style='color:#d32f2f; font-size:14px;'>{row['NOMBRE DEL TALLER']}</b><br>
                <img src='{row['QR_Img']}' width='90' style='margin:10px 0;'><br>
                <a href='{row['WA_Link']}' target='_blank' style='background:#25D366; color:white; padding:5px 10px; border-radius:5px; text-decoration:none; font-weight:bold; font-size:10px;'>WHATSAPP DIRECTO</a>
            </div>
            <hr style='margin:10px 0;'>
            <div style='font-size:11px;'>
                <b>📍 Dirección:</b> {row['DIRECCION']}<br><br>
                <b>📞 Contacto:</b> {row['NUMEROS DE CONTACTO']}<br><br>
                <b>❄️ Cobertura:</b>
                <div style='max-height:60px; overflow-y:auto; background:#f9f9f9; padding:5px; border:1px solid #eee;'>
                    {row['COBERTURA INST AA Y LINEA BLANCA']}
                </div>
            </div>
        </div>
        """
        folium.Marker(
            location=[row['LAT_VIZ'], row['LON_VIZ']], 
            popup=folium.Popup(popup_html, max_width=250), 
            icon=folium.Icon(color="red", icon="wrench", prefix="fa")
        ).add_to(marker_cluster)

    st_folium(m, width="100%", height=500, key="mapa_final_tvs")

    # --- TABLA INFERIOR COMPLETA ---
    st.markdown("### 📋 Directorio Detallado de la Red")
    
    # Columnas organizadas para el usuario
    cols_tabla = ['QR_Img', 'NOMBRE DEL TALLER', 'NUMEROS DE CONTACTO', 'DIRECCION', 'COBERTURA INST AA Y LINEA BLANCA']
    
    st.dataframe(
        df_filt[cols_tabla],
        use_container_width=True,
        hide_index=True,
        column_config={
            "QR_Img": st.column_config.ImageColumn("QR", help="Escanea para abrir WhatsApp"),
            "NOMBRE DEL TALLER": "Taller Autorizado",
            "NUMEROS DE CONTACTO": "Teléfonos",
            "DIRECCION": "Ubicación",
            "COBERTURA INST AA Y LINEA BLANCA": "Zona de Cobertura"
        }
    )

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
