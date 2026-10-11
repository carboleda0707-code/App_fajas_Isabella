import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/api"

def render_clientes():
    st.header("👥 Mantenimiento de Clientes")
    
    try:
        res = requests.get(f"{API_URL}/clientes")
        if res.status_code == 200 and res.json():
            st.write("### Listado de Clientes")
            for c in res.json():
                cols = st.columns([2, 3, 2, 2, 1])
                cols[0].write(f"**RUC:** {c['ruc_cedula']}")
                cols[1].write(f"**Nombre:** {c['nombre']}")
                cols[2].write(f"**Telf:** {c.get('telefono', '-')}")
                cols[3].write(f"**Dir:** {c.get('direccion', '-')}")
                if cols[4].button("🗑️", key=f"del_cli_{c['id']}"):
                    requests.delete(f"{API_URL}/clientes/{c['id']}")
                    st.rerun()
    except:
        pass
        
    st.markdown("---")
    st.subheader("Agregar / Actualizar Cliente")
    with st.form("form_mant_cliente"):
        mc1, mc2 = st.columns(2)
        with mc1:
            m_ruc = st.text_input("RUC / Cédula").strip()
            m_nom = st.text_input("Nombre / Razón Social").strip()
        with mc2:
            m_telf = st.text_input("Teléfono").strip()
            m_dir = st.text_input("Dirección").strip()
            
        if st.form_submit_button("Guardar Cliente"):
            if m_ruc and m_nom:
                requests.post(f"{API_URL}/clientes", json={
                    "ruc_cedula": m_ruc, "nombre": m_nom, 
                    "telefono": m_telf, "direccion": m_dir
                })
                st.success("✅ Cliente guardado correctamente.")
                st.rerun()
            else:
                st.warning("Complete RUC y Nombre.")