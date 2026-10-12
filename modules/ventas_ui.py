import streamlit as st
import requests
import os
from datetime import date

API_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

def render_ventas():
    st.markdown("### 💳 Ventas y Facturación")
    st.markdown("---")
    
    accion = st.radio("Acción:", ["Registrar Nueva Venta", "Consultar Facturas Emitidas"], horizontal=True)
    st.markdown("---")
    
    if accion == "Consultar Facturas Emitidas":
        if st.button("🔄 Actualizar Facturas"):
            st.rerun()
        try:
            res = requests.get(f"{API_URL}/facturas", timeout=3)
            if res.status_code == 200 and res.json():
                facturas_venta = [f for f in res.json() if f.get('tipo_factura') == 'VENTA']
                if facturas_venta:
                    st.dataframe(facturas_venta, use_container_width=True)
                else:
                    st.info("No hay facturas de venta registradas.")
            else:
                st.info("No hay registros en el sistema.")
        except:
            st.error("Error al conectar con el servidor.")
            
    elif accion == "Registrar Nueva Venta":
        dict_skus = {}
        try:
            res = requests.get(f"{API_URL}/inventario", timeout=3)
            if res.status_code == 200:
                items_inv = res.json()
                for item in items_inv:
                    prod_info = item.get("producto", {})
                    nombre_prod = prod_info.get("nombre", "Producto")
                    sku_val = item.get("SKU", "")
                    talla_val = item.get("Talla", "")
                    color_val = item.get("Color", "")
                    stock_val = item.get("Stock", 0)
                    precio_val = item.get("Precio ($)", 0.0)
                    
                    label = f"{nombre_prod} | SKU: {sku_val} | Talla: {talla_val} | Color: {color_val} (Stock: {stock_val} | ${precio_val})"
                    dict_skus[label] = item
        except Exception as e:
            st.error(f"Error al conectar con inventario: {e}")
            
        lista_desc = list(dict_skus.keys())
        
        todos_clientes = []
        try:
            res_c = requests.get(f"{API_URL}/clientes", timeout=3)
            if res_c.status_code == 200:
                todos_clientes = res_c.json()
        except:
            todos_clientes = []
            
        st.markdown('<div id="top-cliente-section"></div>', unsafe_allow_html=True)
        st.markdown("#### 👤 Búsqueda y Selección de Cliente")
        col_b_izq, col_b_der = st.columns([1.5, 2.5])
        
        cliente_sel = st.session_state.get("cliente_venta_sel", None)
        
        with col_b_izq:
            filtro = st.text_input("🔍 RUC o Nombre (Mín. 3 caracteres):", placeholder="Ej: 091 o Carlos", key="input_filtro_cliente").strip().lower()
            if len(filtro) >= 3:
                filtrados = [
                    c for c in todos_clientes 
                    if filtro in str(c.get('ruc_cedula', '')).lower() or filtro in str(c.get('nombre', '')).lower()
                ]
                if filtrados:
                    opts = {f"{c.get('ruc_cedula', '')} - {c.get('nombre', '')}": c for c in filtrados}
                    sel_key = st.selectbox("Coincidencias encontradas:", list(opts.keys()), key="select_coincidencia_cliente")
                    if sel_key:
                        nuevo_sel = opts[sel_key]
                        if cliente_sel != nuevo_sel:
                            # Limpiar mensajes antiguos de éxito o alerta al cambiar de cliente
                            st.session_state.pop("mensaje_exito_venta", None)
                            st.session_state.pop("mensaje_alerta_venta", None)
                        cliente_sel = nuevo_sel
                        st.session_state.cliente_venta_sel = cliente_sel
                else:
                    st.warning("⚠️ No hay clientes coincidentes.")
            elif len(filtro) > 0:
                st.info("💡 Digite al menos 3 caracteres...")
            else:
                if not cliente_sel:
                    st.caption("Escriba en la caja para buscar...")

        ruc_c = str(cliente_sel.get('ruc_cedula', '')) if cliente_sel and cliente_sel.get('ruc_cedula') else ""
        nom_c = str(cliente_sel.get('nombre', '')) if cliente_sel and cliente_sel.get('nombre') else ""
        telf_c = str(cliente_sel.get('telefono', '')) if cliente_sel and cliente_sel.get('telefono') else ""
        dir_c = str(cliente_sel.get('direccion', '')) if cliente_sel and cliente_sel.get('direccion') else ""
        ciudad_c = str(cliente_sel.get('ciudad', '')) if cliente_sel and cliente_sel.get('ciudad') else ""
        tipo_precio_c = str(cliente_sel.get('tipo_precio', 'REGULAR')) if cliente_sel else "REGULAR"
        desc_porcentaje_c = float(cliente_sel.get('descuento_porcentaje', 0.0)) if cliente_sel else 0.0

        def_prov, def_ciudad, def_courier, def_dir, def_ref = "Guayas", ciudad_c or "Guayaquil", "Servientrega", dir_c, ""
        if cliente_sel and ruc_c:
            try:
                res_hist = requests.get(f"{API_URL}/facturas", timeout=3)
                if res_hist.status_code == 200:
                    facturas_cli = [f for f in res_hist.json() if f.get('entidad_ruc') == ruc_c and f.get('tipo_factura') == 'VENTA']
                    if facturas_cli:
                        ult_f = facturas_cli[-1]
                        def_prov = ult_f.get('provincia') or def_prov
                        def_ciudad = ult_f.get('ciudad') or def_ciudad
                        def_courier = ult_f.get('courier_nombre') or def_courier
                        def_dir = ult_f.get('direccion_entrega') or def_dir
                        def_ref = ult_f.get('referencia_direccion') or def_ref
            except:
                pass

        with col_b_der:
            st.markdown("**Datos del Cliente Seleccionado:**")
            if cliente_sel:
                st.success(f"**RUC/CI:** {ruc_c} | **Nombre:** {nom_c}  \n**Tarifa:** {tipo_precio_c} ({desc_porcentaje_c}% Desc.) | **Telf:** {telf_c or 'N/D'}  \n**Ciudad:** {ciudad_c or 'N/D'} | **Dirección Fiscal:** {dir_c or 'N/D'}")
                
                with st.expander("📦 Ver Tallas y Fajas Frecuentes Compradas por este Cliente"):
                    try:
                        res_movs = requests.get(f"{API_URL}/movimientos", timeout=3)
                        if res_movs.status_code == 200:
                            movs_cli = [m for m in res_movs.json() if ruc_c in str(m.get('referencia_factura', '')) or nom_c.lower() in str(m.get('entidad_asociada', '')).lower()]
                            if movs_cli:
                                skus_frec = {}
                                for m in movs_cli:
                                    s = m.get('sku')
                                    skus_frec[s] = skus_frec.get(s, 0) + abs(int(m.get('cantidad', 0)))
                                
                                tabla_frec = []
                                for sku, cant_tot in skus_frec.items():
                                    tabla_frec.append({"SKU": sku, "Unidades Compradas": cant_tot})
                                st.dataframe(tabla_frec, use_container_width=True, hide_index=True)
                            else:
                                st.caption("No registra compras previas en el historial de kardex.")
                    except:
                        st.caption("No se pudo obtener el historial de productos.")
            else:
                st.warning("⚠️ Ningún cliente seleccionado aún.")

        st.markdown("---")
        
        # Mostrar alertas o éxitos y ofrecer un botón rápido para descartarlos
        if "mensaje_alerta_venta" in st.session_state:
            st.warning(st.session_state.mensaje_alerta_venta)
        if "mensaje_exito_venta" in st.session_state:
            col_m1, col_m2 = st.columns([0.85, 0.15])
            with col_m1:
                st.success(st.session_state.mensaje_exito_venta)
            with col_m2:
                if st.button("❌ Cerrar"):
                    del st.session_state.mensaje_exito_venta
                    st.rerun()

        st.markdown("#### 🛍️ Configuración de Ítems")
        col_ci1, col_ci2 = st.columns([1, 3])
        with col_ci1:
            n_items = st.number_input("Cantidad de Ítems", min_value=1, max_value=20, value=1, key="num_items_input")

        if "form_reset_counter" not in st.session_state:
            st.session_state.form_reset_counter = 0
        rc = st.session_state.form_reset_counter

        with st.form(f"form_venta_mod_{rc}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                num_f = st.text_input("Nº de Factura", key=f"input_num_fact_{rc}").strip()
            with c2:
                num_aut = st.text_input("Nº de Autorización", key=f"input_num_aut_{rc}").strip()
            with c3:
                metodo = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Tarjeta de Crédito"], key=f"sel_metodo_{rc}")
                
            r1, r2 = st.columns(2)
            with r1:
                f_fact = st.date_input("Fecha de Factura", value=date.today(), key=f"date_fact_{rc}")
            with r2:
                cod_t = st.text_input("Código Transferencia (Si aplica)", key=f"input_cod_t_{rc}").strip()

            st.markdown("---")
            st.markdown("#### 📦 Datos de Envío y Despacho (Autocompletados según Historial)")
            
            e1, e2, e3 = st.columns(3)
            with e1:
                provincia_env = st.text_input("Provincia", value=def_prov, key=f"input_prov_{rc}").strip()
            with e2:
                ciudad_env = st.text_input("Ciudad de Destino", value=def_ciudad, key=f"input_ciudad_{rc}").strip()
            with e3:
                couriers_opt = ["Servientrega", "Tame Cargo", "Cooperativa", "Uber/Moto", "Retiro en Local", "Otro"]
                c_idx = couriers_opt.index(def_courier) if def_courier in couriers_opt else 0
                courier_env = st.selectbox("Courier / Empresa de Envío", couriers_opt, index=c_idx, key=f"sel_courier_{rc}")

            e4, e5 = st.columns(2)
            with e4:
                dir_env = st.text_input("Dirección Exacta de Entrega", value=def_dir, key=f"input_dir_{rc}").strip()
            with e5:
                ref_env = st.text_input("Referencia de Dirección", value=def_ref, key=f"input_ref_{rc}").strip()

            st.markdown("---")
            st.markdown("#### 📋 Detalle de Productos a Vender")
            items_lista = []
            if lista_desc:
                for i in range(int(n_items)):
                    ic1, ic2, ic3 = st.columns([3, 1, 1])
                    with ic1:
                        p_sel = st.selectbox(f"Faja #{i+1}", lista_desc, key=f"mv_sku_{rc}_{i}")
                        info = dict_skus[p_sel]
                    
                    precio_base = float(info.get('Precio ($)', 0.0))
                    precio_sugerido = precio_base * (1.0 - (desc_porcentaje_c / 100.0)) if desc_porcentaje_c > 0 else precio_base

                    with ic2:
                        cant = st.number_input(f"Cant #{i+1}", min_value=1, value=1, key=f"mv_cant_{rc}_{i}")
                    with ic3:
                        prec = st.number_input(f"Precio ($) #{i+1}", min_value=0.0, value=float(precio_sugerido), key=f"mv_prec_{rc}_{i}")
                    
                    items_lista.append({
                        "sku": str(info.get('SKU', '')),
                        "cantidad": int(cant),
                        "precio_unitario": float(prec)
                    })
            else:
                st.warning("⚠️ No se encontraron productos en el inventario.")
                    
            submitted = st.form_submit_button("💾 Confirmar Venta", type="primary", use_container_width=True)

        if submitted:
            # Limpieza previa de estados
            st.session_state.pop("mensaje_alerta_venta", None)
            st.session_state.pop("mensaje_exito_venta", None)

            if not cliente_sel:
                st.session_state.mensaje_alerta_venta = "❌ Por favor seleccione un cliente."
                st.rerun()
            elif not num_f or not ruc_c:
                st.session_state.mensaje_alerta_venta = "⚠️ Complete los campos obligatorios de factura y cliente."
                st.rerun()
            elif not lista_desc:
                st.session_state.mensaje_alerta_venta = "❌ No hay productos disponibles en el inventario para facturar."
                st.rerun()
            else:
                payload = {
                    "numero_factura": num_f, 
                    "numero_autorizacion": num_aut or "",
                    "fecha_factura": str(f_fact), 
                    "metodo_pago": metodo,
                    "codigo_transferencia": cod_t or "", 
                    "ruc_cliente": ruc_c,
                    "nombre_cliente": nom_c, 
                    "direccion_cliente": dir_c or "",
                    "telefono_cliente": telf_c or "", 
                    "provincia": provincia_env or "Guayas", 
                    "ciudad": ciudad_env or "Guayaquil",
                    "direccion_entrega": dir_env or "", 
                    "referencia_direccion": ref_env or "",
                    "courier_nombre": courier_env or "Servientrega",
                    "items": items_lista
                }
                
                try:
                    res = requests.post(f"{API_URL}/ventas-factura", json=payload, timeout=5)
                        
                    if res.status_code == 200:
                        st.session_state.mensaje_exito_venta = f"✅ ¡Factura Nº {num_f} y datos de envío registrados exitosamente!"
                        st.session_state.pop("cliente_venta_sel", None)
                        st.session_state.form_reset_counter += 1
                        st.rerun()
                    elif res.status_code == 400:
                        try:
                            error_detalle = res.json().get("detail", res.text)
                        except:
                            error_detalle = res.text
                        st.session_state.mensaje_alerta_venta = f"⚠️ {error_detalle}"
                        st.rerun()
                    else:
                        st.error(f"❌ Error HTTP {res.status_code} del Servidor:")
                        st.code(res.text)
                except Exception as e:
                    st.error(f"❌ Error de conexión: {e}")