import streamlit as st
import requests
import os
from datetime import date

API_URL = st.session_state.get("API_URL", "http://127.0.0.1:8000/api")

# Importar los submódulos de reportes que creamos
from modules.report_ventas import render_reporte_ventas
from modules.report_compras import render_reporte_compras
from modules.report_inventario import render_reporte_inventario

def render_reportes():
    st.markdown("### 📊 Reportes y Auditoría del Sistema")
    st.markdown("---")
    
    # Pestañas principales organizadas para auditoría y reportes gerenciales
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Reporte de Ventas", 
        "🛒 Reporte de Compras", 
        "📦 Reporte de Inventario", 
        "📋 Auditoría de Movimientos", 
        "💰 Reporte de Pagos / Facturas"
    ])
    
    with tab1:
        render_reporte_ventas()
        
    with tab2:
        render_reporte_compras()
        
    with tab3:
        render_reporte_inventario()
        
    with tab4:
        st.markdown("#### 📋 Auditoría de Movimientos de Inventario")
        if st.button("🔄 Actualizar Movimientos", key="btn_act_mov"):
            st.rerun()
        try:
            res = requests.get(f"{API_URL}/movimientos", timeout=3)
            if res.status_code == 200 and res.json():
                st.dataframe(res.json(), use_container_width=True)
            else:
                st.info("No hay movimientos registrados.")
        except:
            st.error("Error al conectar con el servidor.")
            
    with tab5:
        st.markdown("#### 💰 Reporte Financiero de Facturas y Pagos")
        if st.button("🔄 Actualizar Facturas", key="btn_act_fact"):
            st.rerun()
        try:
            res = requests.get(f"{API_URL}/facturas", timeout=3)
            if res.status_code == 200 and res.json():
                st.dataframe(res.json(), use_container_width=True)
            else:
                st.info("No hay facturas registradas en el sistema.")
        except:
            st.error("Error al conectar con el servidor.")