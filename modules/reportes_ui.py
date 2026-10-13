import streamlit as st
import requests
import os
from datetime import date

# Conexión estricta de Producción en Nube
API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

# Importar los submódulos de reportes existentes
from modules.report_ventas import render_reporte_ventas
from modules.report_compras import render_reporte_compras
from modules.report_inventario import render_reporte_inventario

def render_reportes():
    st.markdown("### 📊 Reportes y Auditoría del Sistema")
    st.markdown("---")
    
    # Submenú principal dividido en dos bloques de trabajo principales: Ventas y Compras
    submodulo = st.radio(
        "Seleccione la categoría de reporte a consultar:",
        ["📈 Reportes de Ventas y Facturación", "🛒 Reportes de Compras y Proveedores"],
        horizontal=True
    )
    st.markdown("---")
    
    if submodulo == "📈 Reportes de Ventas y Facturación":
        # Subpestañas para profundizar en la gestión de ventas
        tab_v1, tab_v2, tab_v3 = st.tabs([
            "📊 Reporte de Ventas", 
            "📦 Inventario y Stock Activo", 
            "📋 Auditoría de Movimientos"
        ])
        
        with tab_v1:
            render_reporte_ventas()
            
        with tab_v2:
            render_reporte_inventario()
            
        with tab_v3:
            st.markdown("#### 📋 Auditoría de Movimientos de Inventario (Kardex Venta)")
            if st.button("🔄 Actualizar Movimientos", key="btn_act_mov_v"):
                st.rerun()
            try:
                res = requests.get(f"{API_URL}/movimientos", timeout=5)
                if res.status_code == 200 and res.json():
                    st.dataframe(res.json(), use_container_width=True)
                else:
                    st.info("No hay movimientos registrados en el sistema.")
            except Exception as e:
                st.error(f"Error al conectar con el servidor: {e}")

    elif submodulo == "🛒 Reportes de Compras y Proveedores":
        # Subpestañas enfocadas en la gestión de adquisiciones y proveedores
        tab_c1, tab_c2 = st.tabs([
            "🛒 Reporte de Compras", 
            "💰 Financiero de Facturas de Compra"
        ])
        
        with tab_c1:
            render_reporte_compras()
            
        with tab_c2:
            st.markdown("#### 💰 Reporte Financiero de Facturas de Compra")
            if st.button("🔄 Actualizar Registro de Facturas", key="btn_act_fact_c"):
                st.rerun()
            try:
                res = requests.get(f"{API_URL}/facturas", timeout=5)
                if res.status_code == 200 and res.json():
                    facturas = res.json()
                    compras_facturas = [f for f in facturas if f.get('tipo_factura') == 'COMPRA']
                    if compras_facturas:
                        st.dataframe(compras_facturas, use_container_width=True)
                    else:
                        st.info("No hay facturas de compra registradas.")
                else:
                    st.info("No hay registros de facturas disponibles.")
            except Exception as e:
                st.error(f"Error al conectar con el servidor: {e}")