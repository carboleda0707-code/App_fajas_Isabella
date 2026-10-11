import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/api"

def render_proveedores():
    st.header("🏭 Mantenimiento de Proveedores")
    
    # 1. Cargar y mostrar listado de proveedores registrados
    try:
        res = requests.get(f"{API_URL}/proveedores", timeout=3)
        if res.status_code == 200:
            proveedores = res.json()
            if proveedores:
                st.subheader("📋 Proveedores Registrados")
                for p in proveedores:
                    cols = st.columns([2, 3, 2, 2, 1])
                    cols[0].write(f"**RUC:** {p['ruc_cedula']}")
                    cols[1].write(f"**Empresa:** {p['nombre_empresa']}")
                    cols[2].write(f"**Telf:** {p.get('telefono', '-')}")
                    cols[3].write(f"**Contacto:** {p.get('contacto', '-')}")
                    if cols[4].button("🗑️", key=f"del_prov_{p['id']}"):
                        requests.delete(f"{API_URL}/proveedores/{p['id']}", timeout=3)
                        st.rerun()
            else:
                st.info("No hay proveedores registrados todavía.")
        else:
            st.error("No se pudo obtener el listado de proveedores.")
    except Exception as e:
        st.warning("⚠️ No hay conexión con el servidor API o está tardando en responder.")
        
    st.markdown("---")
    
    # 2. Formulario para agregar / actualizar proveedor
    st.subheader("➕ Agregar / Actualizar Proveedor")
    with st.form("form_mant_proveedor"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            p_ruc = st.text_input("RUC del Proveedor").strip()
            p_empresa = st.text_input("Nombre / Razón Social de la Empresa").strip()
        with col_p2:
            p_telf = st.text_input("Teléfono").strip()
            p_dir = st.text_input("Dirección").strip()
            
        btn_guardar = st.form_submit_button("Guardar Proveedor")
        
        if btn_guardar:
            if not p_ruc or not p_empresa:
                st.warning("⚠️ Por favor complete el RUC y el Nombre de la Empresa.")
            else:
                try:
                    payload = {
                        "ruc_cedula": p_ruc,
                        "nombre_empresa": p_empresa,
                        "telefono": p_telf,
                        "direccion": p_dir
                    }
                    res_post = requests.post(f"{API_URL}/proveedores", json=payload, timeout=5)
                    if res_post.status_code == 200:
                        st.success("✅ Proveedor guardado con éxito.")
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar el proveedor.")
                except Exception as ex:
                    st.error(f"❌ Error de conexión: {ex}")