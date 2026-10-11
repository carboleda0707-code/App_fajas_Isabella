import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/api"

def render_reportes():
    st.header("📊 Reportes y Auditoría del Sistema")
    tab1, tab2, tab3 = st.tabs(["📋 Movimientos de Inventario", "💰 Reporte de Pagos", "📑 Facturas Emitidas"])
    
    with tab1:
        if st.button("🔄 Actualizar Movimientos"):
            st.rerun()
        try:
            res = requests.get(f"{API_URL}/movimientos")
            if res.status_code == 200 and res.json():
                st.dataframe(res.json(), use_container_width=True)
            else:
                st.info("No hay movimientos registrados.")
        except:
            pass

    with tab2:
        if st.button("🔄 Actualizar Pagos"):
            st.rerun()
        try:
            res = requests.get(f"{API_URL}/pagos")
            if res.status_code == 200 and res.json():
                st.dataframe(res.json(), use_container_width=True)
            else:
                st.info("No hay pagos registrados.")
        except:
            pass

    with tab3:
        if st.button("🔄 Actualizar Facturas"):
            st.rerun()
        try:
            res = requests.get(f"{API_URL}/facturas")
            if res.status_code == 200 and res.json():
                st.dataframe(res.json(), use_container_width=True)
            else:
                st.info("No hay facturas registradas.")
        except:
            pass