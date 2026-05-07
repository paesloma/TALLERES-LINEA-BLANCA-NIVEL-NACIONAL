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

# --- CABECERA PERSONALIZADA ---
st.markdown(
    """
    <div style="background: linear-gradient(90deg, #d32f2f 0%, #1976d2 100%); padding:20px; border-radius:10px; text-align:center; margin-bottom:20px;">
        <h1 style="color:white; margin:0; font-family:sans-serif; letter-spacing: 2px;">TVS ECUADOR</h1>
        <p style="color:white; margin:0; opacity:0.9; font-size:16px;">Red Nacional de Servicios Técnicos - Información Completa por Taller</p>
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

    # --- BARRA LATERAL: BUSCADOR ---
    st.sidebar.header("🔍 Buscador")
    ciudades_lista = sorted(df['CIUDAD BASE'].unique())
    seleccion_ciudad = st.sidebar.multiselect("📍 Ciudad Base:", ciudades_lista)
    busqueda_cobertura = st.sidebar.text_input("❄️ Zona de Cobertura:", placeholder="Ej: Daule...")

    df_filt = df.copy()
    if seleccion_ciudad:
        df_filt = df_filt[df_filt['CIUDAD BASE'].isin(seleccion_ciudad)]
    if busqueda_cobertura:
        df_filt = df_filt[df_filt['COBERTURA INST AA Y LINEA BLANCA'].str.contains(busqueda_cobertura, case=False, na=False)]

    # Procesamiento de enlaces y QRs
    df_filt['WhatsApp_Link'] = df_filt['NUMEROS DE CONTACTO'].apply(crear_enlace_wa)
    df_filt['QR_Code'] = df_filt['WhatsApp_Link'].apply(generar_qr_base64)

    # --- MAPA ---
    limites_ecuador = [[-5.2, -81.5], [2.5, -75.0]] 
    centro_lat = df_filt['LAT_VIZ'].mean() if not df_filt.empty else -1.45
    centro_lon = df_filt['LON_VIZ'].mean() if not df_filt.empty else -78.5
    
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=7, tiles="CartoDB positron", max_bounds=True)
    marker_cluster = MarkerCluster(options={'maxClusterRadius': 30}).add_to(m)

    for _, row in df_filt.iterrows():
        # HTML detallado para el globo del mapa
        popup_html = f"""
        <div style='font-family:sans-serif; width:220px; line-height:1.2;'>
            <div style='text-align:center;'>
                <b style='color:#d32f2f; font-size:14px;'>{row['NOMBRE DEL TALLER']}</b><br>
                <img src='{row['QR_Code']}' width='90' style='margin:10px 0;'><br>
                <a href='{row['WhatsApp_Link']}' target='_blank' style='background-color:#25D366; color:white; padding:5px 10px; border-radius:5px; text-decoration:none; font-weight:bold;'>CHAT WHATSAPP</a>
            </div>
            <hr style='margin:10px 0;'>
            <b>📍 Dirección:</b><br><span style='font-size:11px;'>{row['DIRECCION']}</span><br>
            <hr style='margin:10px 0;'>
            <b>📞 Contacto:</b><br><span style='font-size:11px;'>{row['NUMEROS DE CONTACTO']}</span><br>
            <hr style='margin:10px 0;'>
            <b>❄️ Cobertura:</b><br>
            <div style='max-height:60px; overflow-y:auto; font-size:10px; background:#f0f0f0; padding:5px;'>
                {row['COBERTURA INST AA Y LINEA BLANCA']}
            </div>
        </div>
        """
        folium.Marker(
            location=[row['LAT_VIZ'], row['LON_VIZ']], 
            popup=folium.Popup(popup_html, max_width=250), 
            icon=folium.Icon(color="red", icon="wrench", prefix="fa")
        ).add_to(marker_cluster)

    st_folium(m, width="100%", height=500, key="mapa_final_tvs")

    # --- TABLA INFERIOR ---
    st.markdown("### 📋 Listado Detallado de Talleres")
    
    # Columnas a mostrar en la tabla
    columnas_tabla = [
        'QR_Code', 
        'NOMBRE DEL TALLER', 
        'CIUDAD BASE', 
        'DIRECCION', 
        'NUMEROS DE CONTACTO', 
        'COBERTURA INST AA Y LINEA BLANCA'
    ]
    
    st.dataframe(
        df_filt[columnas_tabla],
        use_container_width=True,
        hide_index=True,
        column_config={
            "QR_Code": st.column_config.ImageColumn("QR", help="Escanea para contacto"),
            "NOMBRE DEL TALLER": "Taller",
            "CIUDAD BASE": "Ciudad",
            "DIRECCION": "Ubicación Exacta",
            "NUMEROS DE CONTACTO": "Teléfonos",
            "COBERTURA INST AA Y LINEA BLANCA": "Zonas Cubiertas"
        }
    )

except Exception as e:
    st.error(f"Se ha producido un error: {e}")
