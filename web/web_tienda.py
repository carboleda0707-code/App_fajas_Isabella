import streamlit as st
import requests

# Configuración de la página web pública para clientes
st.set_page_config(
    page_title="Fajas Isabella - Tienda Online",
    page_icon="🛍️",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000/api"

# --- CABECERA DE LA TIENDA ---
st.markdown("""
    <div style="text-align: center; padding: 20px; background-color: #f8fafc; border-bottom: 2px solid #e2e8f0; margin-bottom: 25px;">
        <h1 style="color: #1e293b; margin: 0; font-family: sans-serif;">🛍️ Fajas Isabella</h1>
        <p style="color: #64748b; font-size: 1.1rem; margin-top: 5px;">Moldea tu figura con comodidad y elegancia. Catálogo disponible en tiempo real.</p>
    </div>
""", unsafe_allow_html=True)

# --- CARGAR INVENTARIO PÚBLICO DESDE LA API ---
try:
    response = requests.get(f"{API_URL}/web/inventario", timeout=5)
    if response.status_code == 200:
        productos = response.json()
    else:
        productos = []
except Exception as e:
    productos = []
    st.error(f"⚠️ No se pudo conectar con el servidor de la tienda: {e}")

if not productos:
    st.info("No hay productos disponibles con stock en este momento. ¡Vuelve pronto!")
else:
    # --- FILTROS DE BÚSQUEDA ---
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_color = st.selectbox("Filtrar por Color", ["Todos"] + list(set(p['color'] for p in productos)))
    with col_f2:
        filtro_talla = st.selectbox("Filtrar por Talla", ["Todos"] + list(set(p['talla'] for p in productos)))

    # Aplicar filtros
    productos_filtrados = productos
    if filtro_color != "Todos":
        productos_filtrados = [p for p in productos_filtrados if p['color'] == filtro_color]
    if filtro_talla != "Todos":
        productos_filtrados = [p for p in productos_filtrados if p['talla'] == filtro_talla]

    st.markdown("---")
    
    # --- MOSTRAR PRODUCTOS EN TARJETAS (GRID) ---
    cols_por_fila = 3
    for i in range(0, len(productos_filtrados), cols_por_fila):
        fila = productos_filtrados[i:i + cols_por_fila]
        cols = st.columns(cols_por_fila)
        
        for idx, prod in enumerate(fila):
            with cols[idx]:
                with st.container(border=True):
                    st.markdown(f"### 📦 Faja / Moldeador")
                    st.markdown(f"**SKU:** `{prod['sku']}`")
                    st.markdown(f"🎨 **Color:** {prod['color']}")
                    st.markdown(f"📏 **Talla:** {prod['talla']}")
                    st.markdown(f"💰 **Precio:** <span style='color: #16a34a; font-size: 1.2rem; font-weight: bold;'>${prod['precio']:.2f}</span>", unsafe_allow_html=True)
                    st.markdown(f"🟢 **Stock disponible:** {prod['stock_disponible']} unidades")
                    
                    if st.button("🛒 Consultar / Comprar", key=f"btn_{prod['sku']}"):
                        st.success(f"¡Excelente elección! Comunícate con nosotros para procesar tu pedido del SKU: {prod['sku']}")