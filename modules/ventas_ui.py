import streamlit as st
import requests
import os
import pandas as pd
from datetime import date, datetime

# Conexión estricta de Producción en Nube
API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

def render_ventas():
            
    accion = st.radio("Acción a realizar en : 💳 Ventas y Facturación", ["Registrar Nueva Venta", "Consultar Facturas Emitidas"], horizontal=True)
    #st.markdown("---")
    
    if accion == "Consultar Facturas Emitidas":
        col_btn1, col_btn2 = st.columns([0.15, 0.85])
        with col_btn1:
            if st.button("🔄 Actualizar"):
                st.rerun()
                
        st.subheader("📋 Consulta y Control General de Facturas Emitidas")
        
        try:
            # Intentar obtener el reporte completo optimizado de despachos/ventas
            res = requests.get(f"{API_URL}/despachos/reporte", timeout=3)
            if res.status_code != 200:
                res = requests.get(f"{API_URL}/facturas", timeout=3)
                
            if res.status_code == 200:
                facturas_data = res.json()
                if not facturas_data:
                    st.info("No hay facturas de venta registradas en el sistema.")
                    return
                
                # Filtrar solo ventas si viene del endpoint general de facturas
                if isinstance(facturas_data, list) and len(facturas_data) > 0 and "tipo_factura" in facturas_data[0]:
                    facturas_data = [f for f in facturas_data if f.get('tipo_factura') == 'VENTA']

                df_raw = pd.DataFrame(facturas_data)
                
                # Normalizar columna de totales y fechas
                col_total_key = "total" if "total" in df_raw.columns else ("total_factura" if "total_factura" in df_raw.columns else None)
                df_raw["total_norm"] = pd.to_numeric(df_raw[col_total_key], errors="coerce").fillna(0.0) if col_total_key else 0.0
                
                # --- SECCIÓN DE FILTROS Y BÚSQUEDA ---
                st.markdown("##### 🔍 Filtros de Búsqueda y Rango")
                col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.5, 1.5, 1.5])
                
                with col_f1:
                    busqueda = st.text_input("Buscador Rápido:", placeholder="Buscar por Nº Factura, Cliente o RUC...").strip()
                
                with col_f2:
                    f_estado = st.selectbox(
                        "Estado Despacho:",
                        ["TODOS", "PENDIENTE", "EMPACADO", "EN TRÁNSITO", "ENTREGADO"]
                    )
                
                with col_f3:
                    fecha_inicio = st.date_input("Fecha Desde:", value=date(2026, 1, 1))
                
                with col_f4:
                    fecha_fin = st.date_input("Fecha Hasta:", value=date.today())
                    
                st.divider()

                # --- APLICAR FILTROS ---
                df_filtrado = df_raw.copy()

                # Filtro por texto
                if busqueda:
                    mask = (
                        df_filtrado.get("numero_factura", "").astype(str).str.contains(busqueda, case=False, na=False) |
                        df_filtrado.get("cliente", df_filtrado.get("entidad_nombre", "")).astype(str).str.contains(busqueda, case=False, na=False) |
                        df_filtrado.get("ruc_cedula", df_filtrado.get("entidad_ruc", "")).astype(str).str.contains(busqueda, case=False, na=False)
                    )
                    df_filtrado = df_filtrado[mask]

                # Filtro por estado
                if f_estado != "TODOS":
                    col_estado = "estado_despacho" if "estado_despacho" in df_filtrado.columns else "estado"
                    if col_estado in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado[col_estado].astype(str).str.upper() == f_estado]

                # Filtro por fecha
                col_fecha_name = "fecha" if "fecha" in df_filtrado.columns else ("fecha_factura" if "fecha_factura" in df_filtrado.columns else None)
                if col_fecha_name:
                    df_filtrado["fecha_dt"] = pd.to_datetime(df_filtrado[col_fecha_name], errors="coerce").dt.date
                    df_filtrado = df_filtrado[(df_filtrado["fecha_dt"] >= fecha_inicio) & (df_filtrado["fecha_dt"] <= fecha_fin)]

                # --- TARJETAS DE MÉTRICAS (KPIs) ---
                total_monto = df_filtrado["total_norm"].sum()
                cant_facturas = len(df_filtrado)
                
                col_est_estado = "estado_despacho" if "estado_despacho" in df_filtrado.columns else "estado"
                pendientes = len(df_filtrado[df_filtrado[col_est_estado].astype(str).str.upper() == "PENDIENTE"]) if col_est_estado in df_filtrado.columns else 0

                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric("💰 Total Ventas ($)", f"${total_monto:,.2f}")
                kpi2.metric("📄 Facturas Encontradas", f"{cant_facturas}")
                kpi3.metric("⏳ Pendientes de Entrega", f"{pendientes}")

                st.markdown("---")

                # --- TABLA PRESENTABLE Y PROFESIONAL ---
                data_tabla = []
                for _, r in df_filtrado.iterrows():
                    data_tabla.append({
                        "Nº Factura": r.get("numero_factura", "N/A"),
                        "Fecha": r.get("fecha", r.get("fecha_factura", "N/A")),
                        "RUC / Cédula": r.get("ruc_cedula", r.get("entidad_ruc", "N/A")),
                        "Cliente": r.get("cliente", r.get("entidad_nombre", "Consumidor Final")),
                        "Total ($)": f"${r.get('total_norm', 0.0):,.2f}",
                        "Ciudad": r.get("ciudad", "N/A"),
                        "Dirección Entrega": r.get("direccion", r.get("direccion_entrega", "N/A")),
                        "Courier": r.get("courier", r.get("courier_nombre", "Servientrega")),
                        "Nº Guía": r.get("numero_guia", "SIN GUÍA"),
                        "Estado Despacho": r.get("estado_despacho", "PENDIENTE")
                    })

                df_pantalla = pd.DataFrame(data_tabla)
                st.dataframe(df_pantalla, use_container_width=True, hide_index=True)

                # --- DETALLE INDIVIDUAL DE FACTURA ---
                st.divider()
                st.markdown("#### 🔎 Inspeccionar Detalle de Factura / Orden")
                
                lista_facturas = df_filtrado["numero_factura"].dropna().unique().tolist() if "numero_factura" in df_filtrado.columns else []
                if lista_facturas:
                    factura_sel = st.selectbox("Seleccione una Factura para ver su información detallada:", lista_facturas)
                    
                    fact_info = df_filtrado[df_filtrado["numero_factura"] == factura_sel].iloc[0]
                    
                    with st.expander(f"📦 Ver información completa y productos de la Factura Nº {factura_sel}", expanded=True):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.write(f"**Cliente:** {fact_info.get('cliente', fact_info.get('entidad_nombre', 'N/A'))}")
                            st.write(f"**RUC/Cédula:** {fact_info.get('ruc_cedula', fact_info.get('entidad_ruc', 'N/A'))}")
                            st.write(f"**Fecha:** {fact_info.get('fecha', fact_info.get('fecha_factura', 'N/A'))}")
                        with c2:
                            st.write(f"**Provincia / Ciudad:** {fact_info.get('provincia', 'Guayas')} / {fact_info.get('ciudad', 'Guayaquil')}")
                            st.write(f"**Dirección:** {fact_info.get('direccion', fact_info.get('direccion_entrega', 'N/A'))}")
                            st.write(f"**Referencia:** {fact_info.get('referencia', fact_info.get('referencia_direccion', 'Sin referencia'))}")
                        with c3:
                            st.write(f"**Courier:** {fact_info.get('courier', fact_info.get('courier_nombre', 'Servientrega'))}")
                            st.write(f"**Nº Guía:** {fact_info.get('numero_guia', 'SIN GUÍA')}")
                            st.write(f"**Estado Despacho:** `{fact_info.get('estado_despacho', 'PENDIENTE')}`")

                        st.markdown("---")
                        st.markdown("##### 🛍️ Detalle de Ítems / Fajas Vendidas")

                        # 1. Intentar tomar los items directamente del objeto factura
                        items_factura = fact_info.get("items", [])
                        if isinstance(items_factura, str):
                            import json
                            try:
                                items_factura = json.loads(items_factura)
                            except Exception:
                                items_factura = []

                        # 2. Si viene vacío, consultar al endpoint específico de la factura
                        num_fact_str = str(factura_sel).strip()
                        if not items_factura:
                            try:
                                res_single = requests.get(f"{API_URL}/facturas/{num_fact_str}", timeout=3)
                                if res_single.status_code == 200:
                                    fact_single = res_single.json()
                                    items_factura = fact_single.get("items", [])
                            except Exception:
                                pass

                        # 3. Si sigue vacío, buscar en movimientos por coincidencia flexible (numérico)
                        if not items_factura:
                            try:
                                res_mov = requests.get(f"{API_URL}/movimientos", timeout=3)
                                if res_mov.status_code == 200:
                                    movs = res_mov.json()
                                    for m in movs:
                                        ref_f = str(m.get('referencia_factura', '')).strip()
                                        num_m = str(m.get('numero_factura', '')).strip()
                                        if num_fact_str in ref_f or num_fact_str in num_m or (ref_f and ref_f.lstrip('0') == num_fact_str.lstrip('0')):
                                            items_factura.append(m)
                            except Exception:
                                items_factura = []

                        # Renderizado de la tabla de ítems
                        if items_factura:
                            tabla_items = []
                            for idx, it in enumerate(items_factura, 1):
                                sku = it.get("sku", it.get("sku_producto", it.get("codigo_producto", "N/A")))
                                cant = abs(int(it.get("cantidad", it.get("cant", 1))))
                                prec = float(it.get("precio_unitario", it.get("precio", it.get("precio_venta", 0.0))))
                                subtotal = cant * prec
                                
                                tabla_items.append({
                                    "Item #": idx,
                                    "SKU": sku,
                                    "Cantidad": cant,
                                    "Precio Unit. ($)": f"${prec:,.2f}",
                                    "Subtotal ($)": f"${subtotal:,.2f}"
                                })
                            
                            st.dataframe(pd.DataFrame(tabla_items), use_container_width=True, hide_index=True)
                        else:
                            st.info(f"⚠️ No se encontraron ítems desglosados en el Kardex para la Factura Nº {factura_sel}.")
            else:
                st.error("No se pudo obtener el historial de ventas desde el servidor.")
        except Exception as e:
            st.error(f"Error al conectar con el servidor: {e}")
            
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
        st.markdown("##### 👤 Búsqueda y Selección de Cliente")
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