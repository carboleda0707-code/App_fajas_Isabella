import streamlit as st
import requests
import os
from datetime import date, datetime
import pandas as pd

API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

def render_reporte_compras():
    st.markdown("### 🛒 Reportes de Compras a Proveedores")
    st.markdown("---")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        tipo_vista = st.selectbox("Tipo de Vista", ["General (Detallado)", "Consolidado (Resumen)"], key="vista_comp")
    with col_f2:
        fecha_inicio = st.date_input("Desde", value=date(date.today().year, date.today().month, 1), key="ini_comp")
    with col_f3:
        fecha_fin = st.date_input("Hasta", value=date.today(), key="fin_comp")
        
    st.markdown("---")
    
    try:
        res = requests.get(f"{API_URL}/compras-factura", timeout=5)
        if res.status_code == 200:
            compras = res.json()
            
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
                df_compras = pd.DataFrame(compras_filtradas)
                st.dataframe(df_compras, use_container_width=True, hide_index=True)
            else:
                st.markdown("#### 📊 Vista Consolidada de Inversión en Compras")
                total_inversion = sum(float(c.get('total_factura', 0)) for c in compras_filtradas)
                total_ordenes = len(compras_filtradas)
                
                m1, m2 = st.columns(2)
                m1.metric("💸 Inversión Total en Compras", f"${total_inversion:,.2f}")
                m2.metric("📄 Órdenes de Compra Registradas", total_ordenes)
        else:
            st.error("Error al conectar con el servidor.")
    except Exception as e:
        st.error(f"Error de conexión: {e}")