import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import urllib.parse
import qrcode
from io import BytesIO

# 1. Configuración de pantalla
st.set_page_config(page_title="Red Nacional TVS - Postventa", layout="wide")

# --- CABECERA DE TEXTO ESTILIZADA ---
st.markdown(
    """
    <div style="background: linear-gradient(90deg, #d32f2f 0%, #1976d2 100%); padding:20px; border-radius:10px; text-align:center; margin-bottom:20px;">
        <h1 style="color:white; margin:0; font-family:sans-serif; letter-spacing: 2px;">TVS ECUADOR</h1>
        <p style="color:white; margin:0; opacity:0.9; font-size:16px;">Gestión de Postventa - Red Nacional de Servicios Técnicos</p>
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

def crear_enlace_wa(telefono):
    tel_limpio = "".join(filter(str.isdigit, str(telefono)))
    if not tel_limpio: return None
    if not tel_limpio.startswith('593'):
        tel_limpio = '593' + tel_limpio.lstrip('0')
    mensaje = urllib.parse.quote("Hola, contacto desde la Red Nacional TVS. Necesito soporte técnico.")
    return f"https://wa.me/{tel_limpio}?text={mensaje}"

# --- SECCIÓN LATERAL DE UNIÓN (QR) ---
st.sidebar.markdown("---")
st.sidebar.subheader("📢 Únete a la Red")
enlace_registro = "https://tu-enlace-de-registro.com" # CAMBIA ESTE ENLACE

# Generar QR dinámico
qr = qrcode.QRCode(version=1, box_size=10, border=2)
qr.add_data(enlace_registro)
qr.make(fit=True)
img_qr = qr.make_image(fill_color="black", back_color="white")

# Convertir imagen para mostrar en Streamlit
buf = BytesIO()
img_qr.save(buf, format="PNG")
st.sidebar.image(buf.getvalue(), caption="Escanea para unirte", width=150)
st.sidebar.markdown(f"[Enlace directo aquí]({enlace_registro})")

try:
    df = load_data()

    # --- FILTROS ---
    st.sidebar.header("🔍 Buscador")
    ciudades_lista = sorted(df['CIUDAD BASE'].unique())
    seleccion_ciudad = st.sidebar.multiselect("📍 Ciudad Base:", ciudades_lista)
    busqueda_cobertura = st.sidebar.text_input("❄️ Zona de Cobertura:", placeholder="Ej: Daule, Salitre...")

    df_filt = df.copy()
    if seleccion_ciudad:
        df_filt = df_filt[df_filt['CIUDAD BASE'].isin(seleccion_ciudad)]
    if busqueda_cobertura:
        df_filt = df_filt[df_filt['COBERTURA INST AA Y LINEA BLANCA'].str.contains(busqueda_cobertura, case=False, na=False)]

    df_filt['WhatsApp'] = df_filt['NUMEROS DE CONTACTO'].apply(crear_enlace_wa)

    # --- MAPA ---
    limites_ecuador = [[-5.2, -81.5], [2.5, -75.0]] 
    centro_lat = df_filt['LAT_VIZ'].mean() if not df_filt.empty else -1.45
    centro_lon = df_filt['LON_VIZ'].mean() if not df_filt.empty else -78.5
    zoom_level = 13 if (seleccion_ciudad or busqueda_cobertura) else 7

    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=zoom_level, tiles="CartoDB positron", max_bounds=True)
    marker_cluster = MarkerCluster(options={'maxClusterRadius': 30}).add_to(m)

    for _, row in df_filt.iterrows():
        wa_url = row['WhatsApp']
        btn_wa = f"<br><a href='{wa_url}' target='_blank' style='color:green; font-weight:bold; text-decoration:none;'>📲 Contactar WhatsApp</a>" if wa_url else ""
        popup_html = f"<div style='font-family:sans-serif; font-size:12px;'><b>{row['NOMBRE DEL TALLER']}</b><br>📞 {row['NUMEROS DE CONTACTO']}{btn_wa}</div>"
        folium.Marker(location=[row['LAT_VIZ'], row['LON_VIZ']], popup=folium.Popup(popup_html, max_width=250), icon=folium.Icon(color="red", icon="wrench", prefix="fa")).add_to(marker_cluster)

    st_folium(m, width="100%", height=500, key="mapa_final")

    # --- INFORMACIÓN ADICIONAL Y TABLA ---
    col_info, col_tabla = st.columns([1, 3])
    
    with col_info:
        st.info("💡 **Información de Red**\n\nNuestra red cuenta con técnicos certificados en todo el país. Para reportar anomalías en el servicio, usa el canal oficial.")
        st.warning("⚠️ **Recordatorio**\n\nVerifica siempre la cobertura específica antes de asignar una orden.")

    with col_tabla:
        st.dataframe(
            df_filt[['NOMBRE DEL TALLER', 'CIUDAD BASE', 'NUMEROS DE CONTACTO', 'WhatsApp', 'COBERTURA INST AA Y LINEA BLANCA']], 
            use_container_width=True, hide_index=True,
            column_config={"WhatsApp": st.column_config.LinkColumn("Chat", display_text="📲 WA")}
        )

except Exception as e:
    st.error(f"Error: {e}")
