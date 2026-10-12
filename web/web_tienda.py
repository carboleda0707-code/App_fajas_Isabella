import streamlit as st
import requests
import os

st.set_page_config(
    page_title="Fajas Isabella - Tienda Online",
    page_icon="🛍️",
    layout="wide"
)

# Detectar URL de la API dinámicamente para entornos Local y Nube (Railway)
API_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.markdown("""
    <div style="text-align: center; padding: 20px; background-color: #f8fafc; border-bottom: 2px solid #e2e8f0; margin-bottom: 25px;">
        <h1 style="color: #1e293b; margin: 0; font-family: sans-serif;">🛍️ Fajas Isabella</h1>
        <p style="color: #64748b; font-size: 1.1rem; margin-top: 5px;">Moldea tu figura con comodidad y elegancia. Catálogo disponible en tiempo real.</p>
    </div>
""", unsafe_allow_html=True)

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
    col_f1, col_f2 = st.columns(2)
    
    # Extraer colores y tallas de las variantes
    todos_colores = set()
    todas_tallas = set()
    for p in productos:
        for v in p.get('variantes', []):
            todos_colores.add(v['color'])
            todas_tallas.add(v['talla'])

    with col_f1:
        filtro_color = st.selectbox("Filtrar por Color", ["Todos"] + list(todos_colores))
    with col_f2:
        filtro_talla = st.selectbox("Filtrar por Talla", ["Todos"] + list(todas_tallas))

    cols_por_fila = 3
    for i in range(0, len(productos), cols_por_fila):
        fila = productos[i:i + cols_por_fila]
        cols = st.columns(cols_por_fila)
        
        for idx, prod in enumerate(fila):
            with cols[idx]:
                with st.container(border=True):
                    st.markdown(f"### {prod['nombre']}")
                    st.markdown(f"🏷️ **Categoría:** {prod['categoria']}")
                    
                    # Mostrar rango de precios
                    precios = [v['precio'] for v in prod['variantes']]
                    min_p, max_p = min(precios), max(precios)
                    precio_str = f"${min_p:.2f}" if min_p == max_p else f"${min_p:.2f} - ${max_p:.2f}"
                    
                    st.markdown(f"💰 **Precio:** <span style='color: #16a34a; font-size: 1.2rem; font-weight: bold;'>{precio_str}</span>", unsafe_allow_html=True)
                    st.markdown(f"📦 **Opciones disponibles:** {len(prod['variantes'])} variantes")
                    
                    if st.button("🛒 Consultar / Comprar", key=f"btn_{prod['id']}"):
                        st.success(f"¡Excelente elección! Comunícate con nosotros para procesar tu pedido de {prod['nombre']}")