import streamlit as st
import requests
import os

# Conexión estricta de Producción en Nube
API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

def render_reporte_inventario():
    st.markdown("### 📦 Reportes de Inventario y Stock")
    st.markdown("---")
    
    tipo_vista = st.selectbox("Tipo de Vista", ["General (Stock por Variante)", "Consolidado (Valoración de Stock)"])
    st.markdown("---")
    
    col_b1, col_b2 = st.columns([2, 2])
    with col_b1:
        st.button("🔄 Actualizar Datos", use_container_width=True)
    with col_b2:
        excel_url = f"{API_URL}/reportes/inventario/excel"
        st.markdown(
            f"""
            <a href="{excel_url}" target="_blank">
                <button style="width:100%; background-color:#2e7d32; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer;">
                    📥 Descargar Excel de Inventario
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )
        
    try:
        res = requests.get(f"{API_URL}/inventario", timeout=4)
        if res.status_code == 200:
            inventario = res.json()
            if not inventario:
                st.info("No hay productos registrados en el inventario.")
                return
                
            if tipo_vista == "General (Stock por Variante)":
                st.markdown("#### 📋 Inventario General Actual")
                st.dataframe(inventario, use_container_width=True)
            else:
                st.markdown("#### 💰 Consolidado y Valoración de Inventario")
                
                total_items = sum(int(item.get('Stock', 0)) for item in inventario)
                valor_total = sum(int(item.get('Stock', 0)) * float(item.get('Precio ($', 0.0)) for item in inventario)
                
                m1, m2 = st.columns(2)
                m1.metric("📦 Unidades Totales en Stock", total_items)
                m2.metric("💵 Valor Estimado del Inventario", f"${valor_total:,.2f}")
                
                st.dataframe(inventario, use_container_width=True)
        else:
            st.error("Error al obtener el inventario.")
    except Exception as e:
        st.error(f"Error de conexión: {e}")