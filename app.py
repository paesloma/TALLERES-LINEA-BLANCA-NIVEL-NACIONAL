import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import urllib.parse
import qrcode
from io import BytesIO
import base64

st.set_page_config(page_title="Red Nacional TVS - Postventa", layout="wide")

# --- CABECERA ESTILIZADA ---
st.markdown(
    """
    <div style="background: linear-gradient(90deg, #d32f2f 0%, #1976d2 100%); padding:20px; border-radius:10px; text-align:center; margin-bottom:20px;">
        <h1 style="color:white; margin:0; font-family:sans-serif; letter-spacing: 2px;">TVS ECUADOR</h1>
        <p style="color:white; margin:0; opacity:0.9; font-size:16px;">Red Nacional de Servicios Técnicos - Códigos QR de Contacto Directo</p>
    </div>
    """, 
    unsafe_allow_html=True
)

@st.cache_data
def load_data():
    df = pd.read_csv('data_red_nacional_final.csv')
    df.columns = df.columns.str.strip()
    df = df.replace(r'\r\n|\r|\n', ' ', regex=True)
    return df

# Función para generar imagen QR en Base64 para mostrar en tablas/HTML
def generar_qr_base64(url):
    if not url: return ""
    qr = qrcode.QRCode(version=1, box_size=2, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"

def crear_enlace_wa(telefono):
    tel_limpio = "".join(filter(str.isdigit, str(telefono)))
    if not tel_limpio: return None
    if not tel_limpio.startswith('593'):
        tel_limpio = '593' + tel_limpio.lstrip('0')
    mensaje = urllib.parse.quote("Hola, contacto desde la Red Nacional TVS. Necesito soporte técnico.")
    return f"https://wa.me/{tel_limpio}?text={mensaje}"

try:
    df = load_data()

    # --- FILTROS ---
    st.sidebar.header("🔍 Buscador")
    ciudades_lista = sorted(df['CIUDAD BASE'].unique())
    seleccion_ciudad = st.sidebar.multiselect("📍 Ciudad Base:", ciudades_lista)
    busqueda_cobertura = st.sidebar.text_input("❄️ Zona de Cobertura:", placeholder="Ej: Daule...")

    df_filt = df.copy()
    if seleccion_ciudad:
        df_filt = df_filt[df_filt['CIUDAD BASE'].isin(seleccion_ciudad)]
    if busqueda_cobertura:
        df_filt = df_filt[df_filt['COBERTURA INST AA Y LINEA BLANCA'].str.contains(busqueda_cobertura, case=False, na=False)]

    # Generar Enlaces y QRs
    df_filt['WhatsApp_Link'] = df_filt['NUMEROS DE CONTACTO'].apply(crear_enlace_wa)
    df_filt['QR_Code'] = df_filt['WhatsApp_Link'].apply(generar_qr_base64)

    # --- MAPA ---
    limites_ecuador = [[-5.2, -81.5], [2.5, -75.0]] 
    centro_lat = df_filt['LAT_VIZ'].mean() if not df_filt.empty else -1.45
    centro_lon = df_filt['LON_VIZ'].mean() if not df_filt.empty else -78.5
    
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=7, tiles="CartoDB positron", max_bounds=True)
    marker_cluster = MarkerCluster(options={'maxClusterRadius': 30}).add_to(m)

    for _, row in df_filt.iterrows():
        popup_html = f"""
        <div style='text-align:center; font-family:sans-serif;'>
            <b>{row['NOMBRE DEL TALLER']}</b><br>
            <img src='{row['QR_Code']}' width='80'><br>
            <a href='{row['WhatsApp_Link']}' target='_blank' style='color:green;'>Abrir Chat</a>
        </div>
        """
        folium.Marker(
            location=[row['LAT_VIZ'], row['LON_VIZ']], 
            popup=folium.Popup(popup_html, max_width=150), 
            icon=folium.Icon(color="red", icon="wrench", prefix="fa")
        ).add_to(marker_cluster)

    st_folium(m, width="100%", height=450, key="mapa_qr")

    # --- LISTA CON QR VISIBLE ---
    st.markdown("### 📋 Directorio de Talleres con QR Individual")
    
    # Usamos st.column_config para mostrar la imagen del QR en la tabla
    st.dataframe(
        df_filt[['QR_Code', 'NOMBRE DEL TALLER', 'CIUDAD BASE', 'NUMEROS DE CONTACTO', 'COBERTURA INST AA Y LINEA BLANCA']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "QR_Code": st.column_config.ImageColumn("Escanear QR", help="Apunta tu cámara aquí para chatear"),
            "NOMBRE DEL TALLER": st.column_config.TextColumn("Taller", width="medium"),
        }
    )

except Exception as e:
    st.error(f"Error: {e}")
