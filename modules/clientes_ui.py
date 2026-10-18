import streamlit as st
import requests
import os
import pandas as pd

# Conexión estricta de Producción en Nube
API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

def render_clientes():
    st.subheader("👥 Mantenimiento de Clientes")
    st.markdown("Datos fiscales, comerciales, ubicación - descuentos.")
    
    accion = st.radio(
        "Acción:",
        ("Registrar Nuevo Cliente", "Consultar y Modificar Clientes"),
        horizontal=True
    )
    
    st.divider()

    if accion == "Registrar Nuevo Cliente":
        st.subheader("➕ Registro de Nuevo Cliente")
        
        with st.form("form_crear_cliente", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                m_ruc = st.text_input("RUC / Cédula *", placeholder="Ej: 0914592936001").strip()
                m_nom = st.text_input("Nombre / Razón Social *", placeholder="Ej: Carlos Arboleda").strip()
            with col2:
                m_ciudad = st.text_input("Ciudad *", placeholder="Ej: Guayaquil, Quito, Cuenca").strip()
                m_telf = st.text_input("Teléfono", placeholder="Ej: 0983870398").strip()
            with col3:
                m_correo = st.text_input("Correo Electrónico", placeholder="Ej: correo@dominio.com").strip()
                m_dir = st.text_input("Dirección Fiscal / Entrega", placeholder="Ej: Mucho Lote 2").strip()

            st.markdown("##### 🏷️ Configuración Comercial de Tarifa")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                m_tipo_precio = st.selectbox("Categoría de Tarifa", ["REGULAR", "MAYORISTA", "VIP"])
            with col_c2:
                m_descuento = st.number_input("Descuento Fijo (%)", min_value=0.0, max_value=50.0, value=0.0, step=0.5)

            btn_guardar = st.form_submit_button("💾 Guardar Cliente", type="primary", use_container_width=True)
            
            if btn_guardar:
                if m_ruc and m_nom and m_ciudad:
                    payload = {
                        "ruc_cedula": m_ruc, 
                        "nombre": m_nom, 
                        "ciudad": m_ciudad,
                        "telefono": m_telf if m_telf else "", 
                        "correo": m_correo if m_correo else "",
                        "direccion": m_dir if m_dir else "",
                        "tipo_precio": m_tipo_precio,
                        "descuento_porcentaje": float(m_descuento)
                    }
                    res_post = requests.post(f"{API_URL}/clientes", json=payload)
                    if res_post.status_code in (200, 201):
                        st.success("✅ Cliente registrado correctamente.")
                    else:
                        st.error(f"Error al registrar: {res_post.text}")
                else:
                    st.warning("Debe completar al menos el RUC/Cédula, el Nombre y la Ciudad.")

    elif accion == "Consultar y Modificar Clientes":
        st.subheader("📋 Consulta y Actualización de Clientes")
        
        try:
            res = requests.get(f"{API_URL}/clientes")
            if res.status_code == 200:
                clientes_data = res.json()
                if clientes_data:
                    mapa_clientes = {c["id"]: c for c in clientes_data}
                    
                    data_tabla = []
                    for c in clientes_data:
                        data_tabla.append({
                            "ID": c["id"],
                            "RUC / Cédula": c.get("ruc_cedula", ""),
                            "Nombre": c.get("nombre", ""),
                            "Correo": c.get("correo", "") or "",
                            "Ciudad": c.get("ciudad", "") or "",
                            "Teléfono": c.get("telefono", "") or "",
                            "Tarifa": c.get("tipo_precio", "REGULAR"),
                            "Desc. (%)": f"{c.get('descuento_porcentaje', 0.0)}%",
                            "Dirección": c.get("direccion", "") or ""
                        })
                    
                    df_clientes = pd.DataFrame(data_tabla)
                    
                    filtro_busqueda = st.text_input("🔍 Buscar por RUC o Nombre:", placeholder="Escribe para filtrar...")
                    if filtro_busqueda:
                        mask = df_clientes["RUC / Cédula"].str.contains(filtro_busqueda, case=False, na=False) | \
                               df_clientes["Nombre"].str.contains(filtro_busqueda, case=False, na=False)
                        df_filtrado = df_clientes[mask]
                    else:
                        df_filtrado = df_clientes
                        
                    st.dataframe(df_filtrado, use_container_width=True)
                    
                    st.divider()
                    st.markdown("##### 🛠️ Modificar o Eliminar Cliente por ID")
                    
                    c_id_input = st.number_input("ID del Cliente a Editar", min_value=1, step=1, key="select_cliente_id")
                    cli_encontrado = mapa_clientes.get(c_id_input)
                    
                    val_ruc = str(cli_encontrado.get("ruc_cedula", "")) if cli_encontrado and cli_encontrado.get("ruc_cedula") else ""
                    val_nom = str(cli_encontrado.get("nombre", "")) if cli_encontrado and cli_encontrado.get("nombre") else ""
                    val_ciudad = str(cli_encontrado.get("ciudad", "")) if cli_encontrado and cli_encontrado.get("ciudad") else ""
                    val_telf = str(cli_encontrado.get("telefono", "")) if cli_encontrado and cli_encontrado.get("telefono") else ""
                    val_correo = str(cli_encontrado.get("correo", "")) if cli_encontrado and cli_encontrado.get("correo") else ""
                    val_dir = str(cli_encontrado.get("direccion", "")) if cli_encontrado and cli_encontrado.get("direccion") else ""
                    val_tipo_p = str(cli_encontrado.get("tipo_precio", "REGULAR")) if cli_encontrado else "REGULAR"
                    val_desc = float(cli_encontrado.get("descuento_porcentaje", 0.0)) if cli_encontrado else 0.0

                    with st.form("form_modificar_cliente"):
                        col_m_1, col_m_2 = st.columns(2)
                        with col_m_1:
                            mod_ruc = st.text_input("RUC / Cédula *", value=val_ruc).strip()
                            mod_nom = st.text_input("Nombre / Razón Social *", value=val_nom).strip()
                            mod_ciudad = st.text_input("Ciudad *", value=val_ciudad).strip()
                            mod_telf = st.text_input("Teléfono", value=val_telf).strip()
                        with col_m_2:
                            mod_correo = st.text_input("Correo Electrónico", value=val_correo).strip()
                            mod_dir = st.text_input("Dirección Fiscal", value=val_dir).strip()
                            mod_tipo_p = st.selectbox("Categoría de Tarifa", ["REGULAR", "MAYORISTA", "VIP"], index=["REGULAR", "MAYORISTA", "VIP"].index(val_tipo_p) if val_tipo_p in ["REGULAR", "MAYORISTA", "VIP"] else 0)
                            mod_desc = st.number_input("Descuento Fijo (%)", min_value=0.0, max_value=50.0, value=val_desc, step=0.5)
                        
                        col_b1, col_b2 = st.columns(2)
                        btn_actualizar = col_b1.form_submit_button("🔄 Actualizar Datos", type="primary", use_container_width=True)
                        btn_eliminar = col_b2.form_submit_button("🗑️ Eliminar Cliente", type="secondary", use_container_width=True)
                        
                        if btn_actualizar:
                            if cli_encontrado and mod_ruc and mod_nom and mod_ciudad:
                                payload = {
                                    "ruc_cedula": mod_ruc,
                                    "nombre": mod_nom,
                                    "ciudad": mod_ciudad,
                                    "telefono": mod_telf,
                                    "correo": mod_correo,
                                    "direccion": mod_dir,
                                    "tipo_precio": mod_tipo_p,
                                    "descuento_porcentaje": float(mod_desc)
                                }
                                res_upd = requests.put(f"{API_URL}/clientes/{c_id_input}", json=payload)
                                if res_upd.status_code == 200:
                                    st.success(f"✅ Cliente ID {c_id_input} actualizado con éxito.")
                                    st.rerun()
                                else:
                                    st.error(f"Error al actualizar: {res_upd.text}")
                            else:
                                st.warning("Selecciona un ID válido y completa los campos obligatorios (*).")
                                
                        if btn_eliminar:
                            if cli_encontrado:
                                res_del = requests.delete(f"{API_URL}/clientes/{c_id_input}")
                                if res_del.status_code == 200:
                                    st.success(f"🗑️ Cliente ID {c_id_input} eliminado correctamente.")
                                    st.rerun()
                                else:
                                    st.error("No se pudo eliminar el cliente.")
                            else:
                                st.warning("El ID ingresado no existe en los registros.")
                else:
                    st.info("No hay clientes registrados en el sistema todavía.")
            else:
                st.error("Error al conectar con el servidor para consultar clientes.")
        except Exception as e:
            st.warning(f"Error de conexión: {e}")