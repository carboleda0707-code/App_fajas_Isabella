import streamlit as st
import requests
import os
from datetime import date, datetime

API_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

def render_reporte_compras():
    st.markdown("### 🛒 Reportes de Compras y Proveedores")
    st.markdown("---")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        tipo_vista = st.selectbox("Tipo de Vista", ["General (Detallado)", "Consolidado (Resumen)"], key="vista_comp")
    with col_f2:
        fecha_inicio = st.date_input("Desde", value=date(date.today().year, date.today().month, 1), key="ini_comp")
    with col_f3:
        fecha_fin = st.date_input("Hasta", value=date.today(), key="fin_comp")
        
    st.markdown("---")
    
    col_b1, col_b2 = st.columns([2, 2])
    with col_b1:
        consultar = st.button("🔍 Generar Reporte Compras", type="primary", use_container_width=True)
    with col_b2:
        excel_url = f"{API_URL}/reportes/compras/excel?inicio={fecha_inicio}&fin={fecha_fin}&tipo={tipo_vista}"
        st.markdown(
            f"""
            <a href="{excel_url}" target="_blank">
                <button style="width:100%; background-color:#2e7d32; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer;">
                    📥 Descargar Excel de Compras
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )
        
    try:
        res = requests.get(f"{API_URL}/facturas", timeout=4)
        if res.status_code == 200:
            facturas = res.json()
            compras = [f for f in facturas if f.get('tipo_factura') == 'COMPRA']
            
            if not compras:
                st.info("No hay registros de compras a proveedores en el sistema.")
                return
                
            compras_filtradas = []
            for c in compras:
                f_str = c.get('fecha_factura')
                if f_str:
                    f_date = datetime.strptime(str(f_str)[:10], "%Y-%m-%d").date()
                    if fecha_inicio <= f_date <= fecha_fin:
                        compras_filtradas.append(c)
                        
            if not compras_filtradas:
                st.warning("⚠️ No se encontraron compras en el rango de fechas seleccionado.")
                return

            if tipo_vista == "General (Detallado)":
                st.markdown("#### 📋 Listado General de Compras a Proveedores")
                st.dataframe(compras_filtradas, use_container_width=True)
            else:
                st.markdown("#### 📊 Vista Consolidada de Compras")
                total_inversion = sum(float(c.get('total_factura', 0)) for c in compras_filtradas)
                total_ordenes = len(compras_filtradas)
                
                m1, m2 = st.columns(2)
                m1.metric("💸 Inversión Total en Compras", f"${total_inversion:,.2f}")
                m2.metric("📄 Órdenes de Compra Registradas", total_ordenes)
        else:
            st.error("Error al conectar con el servidor.")
    except Exception as e:
        st.error(f"Error de conexión: {e}")