import streamlit as st
import requests
import os
import pandas as pd

# Conexión estricta de Producción en Nube
API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

def render_proveedores():
    st.markdown("<p style='color: black; font-weight: bold;'>🏭 Gestión de Datos de Proveedores</p>", unsafe_allow_html=True)
    
    accion = st.radio(
        "Acción:",
        ("Registrar Nuevo Proveedor", "Consultar y Modificar Proveedores"),
        horizontal=True
    )
    
    st.divider()

    if accion == "Registrar Nuevo Proveedor":
        st.markdown("<p style='color: black; font-weight: bold;'>➕ Registro de Nuevo Proveedor</p>", unsafe_allow_html=True)
        
        with st.form("form_crear_proveedor", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                p_ruc = st.text_input("RUC del Proveedor *", placeholder="Ej: 0991234567001").strip()
                p_nom = st.text_input("Nombre / Razón Social de la Empresa *", placeholder="Ej: Textiles S.A.").strip()
                p_ciudad = st.text_input("Ciudad *", placeholder="Ej: Guayaquil, Quito, Ambato").strip()
            with col2:
                p_telf = st.text_input("Teléfono", placeholder="Ej: 042123456").strip()
                p_correo = st.text_input("Correo Electrónico", placeholder="Ej: ventas@proveedor.com").strip()
                p_dir = st.text_input("Dirección", placeholder="Ej: Parque Industrial PIADI").strip()
                
            btn_guardar = st.form_submit_button("💾 Guardar Proveedor", type="primary", use_container_width=True)
            
            if btn_guardar:
                if p_ruc and p_nom and p_ciudad:
                    payload = {
                        "ruc_cedula": p_ruc, 
                        "nombre": p_nom, 
                        "ciudad": p_ciudad,
                        "telefono": p_telf if p_telf else "", 
                        "correo": p_correo if p_correo else "",
                        "direccion": p_dir if p_dir else ""
                    }
                    res_post = requests.post(f"{API_URL}/proveedores", json=payload)
                    if res_post.status_code in (200, 201):
                        st.success("✅ Proveedor registrado correctamente.")
                    else:
                        # Muestra el detalle exacto que devuelve FastAPI
                        st.error(f"Error al registrar ({res_post.status_code}): {res_post.text}")
                else:
                    st.warning("Debe completar al menos el RUC, el Nombre/Razón Social y la Ciudad.")

    elif accion == "Consultar y Modificar Proveedores":
        st.markdown("<p style='color: black; font-weight: bold;'>📋 Consulta, Modificación de Proveedores</p>", unsafe_allow_html=True)
                
        try:
            res = requests.get(f"{API_URL}/proveedores")
            if res.status_code == 200:
                provs_data = res.json()
                if provs_data:
                    mapa_provs = {p["id"]: p for p in provs_data}
                    
                    data_tabla = []
                    for p in provs_data:
                        data_tabla.append({
                            "ID": p["id"],
                            "RUC": p.get("ruc_cedula", ""),
                            "Nombre / Empresa": p.get("nombre", ""),
                            "Ciudad": p.get("ciudad", "") or "",
                            "Teléfono": p.get("telefono", "") or "",
                            "Correo": p.get("correo", "") or "",
                            "Dirección": p.get("direccion", "") or ""
                        })
                    
                    df_proveedores = pd.DataFrame(data_tabla)
                    
                    filtro_busqueda = st.text_input("🔍 Buscar por RUC o Empresa:", placeholder="Escribe para filtrar...")
                    if filtro_busqueda:
                        mask = df_proveedores["RUC"].str.contains(filtro_busqueda, case=False, na=False) | \
                               df_proveedores["Nombre / Empresa"].str.contains(filtro_busqueda, case=False, na=False)
                        df_filtrado = df_proveedores[mask]
                    else:
                        df_filtrado = df_proveedores
                        
                    st.dataframe(df_filtrado, use_container_width=True)
                    
                    st.divider()
                    st.markdown("##### 🛠️ Modificar o Eliminar Proveedor por ID")
                    
                    p_id_input = st.number_input("ID del Proveedor a Editar", min_value=1, step=1, key="select_prov_id")
                    prov_encontrado = mapa_provs.get(p_id_input)
                    
                    val_ruc = str(prov_encontrado.get("ruc_cedula", "")) if prov_encontrado and prov_encontrado.get("ruc_cedula") else ""
                    val_nom = str(prov_encontrado.get("nombre", "")) if prov_encontrado and prov_encontrado.get("nombre") else ""
                    val_ciudad = str(prov_encontrado.get("ciudad", "")) if prov_encontrado and prov_encontrado.get("ciudad") else ""
                    val_telf = str(prov_encontrado.get("telefono", "")) if prov_encontrado and prov_encontrado.get("telefono") else ""
                    val_correo = str(prov_encontrado.get("correo", "")) if prov_encontrado and prov_encontrado.get("correo") else ""
                    val_dir = str(prov_encontrado.get("direccion", "")) if prov_encontrado and prov_encontrado.get("direccion") else ""

                    with st.form("form_modificar_proveedor"):
                        col_m_1, col_m_2 = st.columns(2)
                        with col_m_1:
                            mod_ruc = st.text_input("RUC del Proveedor *", value=val_ruc).strip()
                            mod_nom = st.text_input("Nombre / Razón Social *", value=val_nom).strip()
                            mod_ciudad = st.text_input("Ciudad *", value=val_ciudad).strip()
                        with col_m_2:
                            mod_telf = st.text_input("Teléfono", value=val_telf).strip()
                            mod_correo = st.text_input("Correo Electrónico", value=val_correo).strip()
                            mod_dir = st.text_input("Dirección", value=val_dir).strip()
                        
                        col_b1, col_b2 = st.columns(2)
                        btn_actualizar = col_b1.form_submit_button("🔄 Actualizar Datos", type="primary", use_container_width=True)
                        btn_eliminar = col_b2.form_submit_button("🗑️ Eliminar Proveedor", type="secondary", use_container_width=True)
                        
                        if btn_actualizar:
                            if prov_encontrado and mod_ruc and mod_nom and mod_ciudad:
                                payload = {
                                    "ruc_cedula": mod_ruc,
                                    "nombre": mod_nom,
                                    "ciudad": mod_ciudad,
                                    "telefono": mod_telf,
                                    "correo": mod_correo,
                                    "direccion": mod_dir
                                }
                                res_upd = requests.put(f"{API_URL}/proveedores/{p_id_input}", json=payload)
                                if res_upd.status_code == 200:
                                    st.success(f"✅ Proveedor ID {p_id_input} actualizado con éxito.")
                                    st.rerun()
                                else:
                                    st.error(f"Error al actualizar: {res_upd.text}")
                            else:
                                st.warning("Selecciona un ID válido y completa los campos obligatorios (*).")
                                
                        if btn_eliminar:
                            if prov_encontrado:
                                res_del = requests.delete(f"{API_URL}/proveedores/{p_id_input}")
                                if res_del.status_code == 200:
                                    st.success(f"🗑️ Proveedor ID {p_id_input} eliminado correctamente.")
                                    st.rerun()
                                else:
                                    st.error("No se pudo eliminar el proveedor.")
                            else:
                                st.warning("El ID ingresado no existe en los registros.")
                else:
                    st.info("No hay proveedores registrados en el sistema todavía.")
            else:
                st.error("Error al conectar con el servidor para consultar proveedores.")
        except Exception as e:
            st.warning(f"Error de conexión: {e}")