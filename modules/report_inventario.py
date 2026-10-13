import streamlit as st
import requests
import os
import pandas as pd

# Conexión estricta de Producción en Nube
API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

def render_reporte_inventario():
    st.markdown("### 📦 Reportes de Inventario y Stock")
    st.markdown("---")
    
    tipo_vista = st.selectbox(
        "Tipo de Vista", 
        ["General (Stock por Variante)", "Consolidado (Valoración de Stock)"]
    )
    st.markdown("---")
    
    col_b1, col_b2 = st.columns([2, 2])
    with col_b1:
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.rerun()
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
        
    st.markdown("---")

    try:
        res = requests.get(f"{API_URL}/inventario", timeout=5)
        if res.status_code == 200:
            inventario = res.json()
            if not inventario:
                st.info("No hay productos registrados en el inventario.")
                return
                
            df_inv = pd.DataFrame(inventario)

            if tipo_vista == "General (Stock por Variante)":
                st.markdown("#### 📋 Inventario General Actual por Variante")
                st.dataframe(df_inv, use_container_width=True, hide_index=True)
            else:
                st.markdown("#### 💰 Consolidado y Valoración Total de Inventario")
                
                # Función segura para extraer stock y precio considerando diferentes formatos de claves
                total_items = 0
                valor_total = 0.0
                
                for item in inventario:
                    # Búsqueda flexible de claves de stock y precio
                    stock = int(item.get('Stock') or item.get('stock_actual') or item.get('stock') or 0)
                    precio = float(item.get('Precio ($') or item.get('precio') or 0.0)
                    
                    total_items += stock
                    valor_total += (stock * precio)
                
                m1, m2 = st.columns(2)
                m1.metric("📦 Unidades Totales en Stock", f"{total_items:,} unidades")
                m2.metric("💵 Valor Estimado del Inventario", f"${valor_total:,.2f}")
                
                st.markdown("---")
                st.dataframe(df_inv, use_container_width=True, hide_index=True)
        else:
            st.error("Error al obtener la información del inventario desde el servidor.")
    except Exception as e:
        st.error(f"Error de conexión con el servidor: {e}")