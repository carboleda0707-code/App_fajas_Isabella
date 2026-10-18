import streamlit as st
import requests
import os
import pandas as pd
import io
from datetime import date, datetime

# Conexión estricta de Producción en Nube
API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

def render_despachos():
    st.subheader("📦 Control de Despachos y Envíos por Courier")
    st.markdown("Gestiona estados de paquetes, asigna guías, repartidores, números de control y genera etiquetas imprimibles 'De / Para'.")

    col_btn1, col_btn2 = st.columns([0.15, 0.85])
    with col_btn1:
        if st.button("🔄 Actualizar", key="btn_refresh_desp"):
            st.rerun()

    try:
        response = requests.get(f"{API_URL}/despachos/reporte", timeout=5)
        if response.status_code != 200:
            response = requests.get(f"{API_URL}/facturas", timeout=5)

        if response.status_code == 200:
            data_despachos = response.json()
            
            if not data_despachos:
                st.info("No se encontraron despachos registrados en el sistema.")
                return

            # Filtrar solo ventas
            if isinstance(data_despachos, list) and len(data_despachos) > 0 and "tipo_factura" in data_despachos[0]:
                data_despachos = [f for f in data_despachos if f.get('tipo_factura') == 'VENTA']

            df_raw = pd.DataFrame(data_despachos)

            # Normalizar totales
            col_total_key = "total" if "total" in df_raw.columns else ("total_factura" if "total_factura" in df_raw.columns else None)
            df_raw["total_norm"] = pd.to_numeric(df_raw[col_total_key], errors="coerce").fillna(0.0) if col_total_key else 0.0

            # --- SECCIÓN DE FILTROS Y BÚSQUEDA ---
            st.markdown("##### 🔍 Filtros de Búsqueda y Rango")
            col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.5, 1.5, 1.5])
            
            with col_f1:
                busqueda = st.text_input("Buscador Rápido:", placeholder="Buscar por Nº Orden, Cliente, Repartidor, Guía o Nº Control...").strip()
            
            with col_f2:
                filtro_estado = st.selectbox(
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

            if busqueda:
                mask = (
                    df_filtrado.get("numero_factura", "").astype(str).str.contains(busqueda, case=False, na=False) |
                    df_filtrado.get("cliente", df_filtrado.get("entidad_nombre", "")).astype(str).str.contains(busqueda, case=False, na=False) |
                    df_filtrado.get("repartidor", df_filtrado.get("chofer", "")).astype(str).str.contains(busqueda, case=False, na=False) |
                    df_filtrado.get("numero_guia", "").astype(str).str.contains(busqueda, case=False, na=False) |
                    df_filtrado.get("numero_control", "").astype(str).str.contains(busqueda, case=False, na=False)
                )
                df_filtrado = df_filtrado[mask]

            if filtro_estado != "TODOS":
                col_est = "estado_despacho" if "estado_despacho" in df_filtrado.columns else "estado"
                if col_est in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado[col_est].astype(str).str.upper() == filtro_estado]

            col_fecha_name = "fecha" if "fecha" in df_filtrado.columns else ("fecha_factura" if "fecha_factura" in df_filtrado.columns else None)
            if col_fecha_name:
                df_filtrado["fecha_dt"] = pd.to_datetime(df_filtrado[col_fecha_name], errors="coerce").dt.date
                df_filtrado = df_filtrado[(df_filtrado["fecha_dt"] >= fecha_inicio) & (df_filtrado["fecha_dt"] <= fecha_fin)]

            # --- TARJETAS DE MÉTRICAS (KPIs) CORREGIDAS Y COHERENTES ---
            total_pedidos = len(df_filtrado)
            col_est = "estado_despacho" if "estado_despacho" in df_filtrado.columns else "estado"
            
            if col_est in df_filtrado.columns:
                estados_upper = df_filtrado[col_est].astype(str).str.upper().str.strip()
                pendientes_empacados = len(df_filtrado[estados_upper.isin(["PENDIENTE", "EMPACADO"])])
                en_transito = len(df_filtrado[estados_upper.isin(["EN TRÁNSITO", "EN TRANSITO"])])
                entregados = len(df_filtrado[estados_upper == "ENTREGADO"])
            else:
                pendientes_empacados, en_transito, entregados = 0, 0, 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📦 Total Pedidos", total_pedidos)
            m2.metric("⏳ Pend. / Empacados", pendientes_empacados)
            m3.metric("🚚 En Tránsito", en_transito)
            m4.metric("✅ Entregados", entregados)

            st.divider()

            # --- SECCIÓN: TABLA COMPACTA Y EXCEL ---
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                st.markdown("#### 📋 Listado Consolidado de Órdenes")
            with col_t2:
                try:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_filtrado.to_excel(writer, index=False, sheet_name='Despachos')
                    excel_data = output.getvalue()
                    
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=excel_data,
                        file_name="Listado_Despachos.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except Exception as ex:
                    st.caption("⚠️ Instale openpyxl para exportar Excel")

            # Tabla limpia con Repartidor y término Orden de Venta
            data_tabla = []
            for _, r in df_filtrado.iterrows():
                data_tabla.append({
                    "Nº Orden Venta": r.get("numero_factura", "N/A"),
                    "Fecha": r.get("fecha", r.get("fecha_factura", "N/A")),
                    "Cliente": r.get("cliente", r.get("entidad_nombre", "Consumidor Final")),
                    "Provincia": r.get("provincia", "Guayas"),
                    "Ciudad": r.get("ciudad", "Guayaquil"),
                    "Courier": r.get("courier", r.get("courier_nombre", "Servientrega")),
                    "Repartidor/Chofer": r.get("repartidor", r.get("chofer", "N/D")),
                    "Nº Guía": r.get("numero_guia", "SIN GUÍA"),
                    "Nº Control": r.get("numero_control", r.get("codigo_control", "SIN CONTROL")),
                    "Total ($)": f"${r.get('total_norm', 0.0):,.2f}",
                    "Estado Despacho": r.get("estado_despacho", r.get("estado", "PENDIENTE"))
                })

            st.dataframe(pd.DataFrame(data_tabla), use_container_width=True, hide_index=True)

            # --- DETALLE DE INSPECCIÓN CON ÍTEMS VENDIDOS ---
            st.divider()
            st.markdown("#### 🔎 Inspeccionar Detalle de Despacho e Ítems Vendidos")
            
            lista_facturas = df_filtrado["numero_factura"].dropna().unique().tolist() if "numero_factura" in df_filtrado.columns else []
            if lista_facturas:
                factura_sel = st.selectbox("Seleccione una Orden de Venta para ver su información detallada:", lista_facturas, key="sel_fact_det_log")
                
                fact_info = df_filtrado[df_filtrado["numero_factura"] == factura_sel].iloc[0]
                monto_factura_tot = float(fact_info.get("total_norm", 0.0))
                
                with st.expander(f"📦 Ver información completa y productos de la Orden Nº {factura_sel}", expanded=True):
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
                        st.write(f"**Courier / Repartidor:** {fact_info.get('courier', 'Servientrega')} ({fact_info.get('repartidor', 'N/D')})")
                        st.write(f"**Nº Guía:** {fact_info.get('numero_guia', 'SIN GUÍA')}")
                        st.write(f"**Nº Control:** {fact_info.get('numero_control', fact_info.get('codigo_control', 'SIN CONTROL'))}")
                        st.write(f"**Estado Despacho:** `{fact_info.get('estado_despacho', 'PENDIENTE')}`")

                    st.markdown("---")
                    st.markdown("##### 🛍️ Detalle de Ítems / Fajas Vendidas")

                    items_factura = fact_info.get("items", [])
                    num_fact_str = str(factura_sel).strip()

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

                    if items_factura:
                        tabla_items = []
                        for idx, it in enumerate(items_factura, 1):
                            sku = it.get("sku", it.get("sku_producto", it.get("codigo_producto", "N/A")))
                            cant = abs(int(it.get("cantidad", it.get("cant", 1))))
                            
                            prec_bruto = (
                                it.get("precio_unitario") or 
                                it.get("precio") or 
                                it.get("precio_venta") or 
                                it.get("costo_unitario") or 
                                0.0
                            )
                            prec = float(prec_bruto)
                            
                            if prec == 0.0 and monto_factura_tot > 0 and len(items_factura) > 0:
                                prec = monto_factura_tot / len(items_factura) / cant
                            
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
                        st.info(f"⚠️ No se encontraron ítems desglosados para la Orden Nº {factura_sel}.")

            st.divider()

            # --- SECCIÓN OPERATIVA: ACTUALIZACIÓN DE GUÍA, CONTROL Y REPARTIDOR ---
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("#### 🚚 Actualizar Guía, Repartidor, Control y Estado")
                
                opts_pedidos = {
                    f"Orden #{r.get('numero_factura')} - {r.get('cliente', r.get('entidad_nombre', 'N/A'))} ({r.get('ciudad', 'Guayaquil')})": r
                    for _, r in df_filtrado.iterrows()
                }

                if opts_pedidos:
                    ped_sel_label = st.selectbox("Seleccione Orden de Venta", list(opts_pedidos.keys()), key="sel_pedido_act_log")
                    pedido_sel = opts_pedidos[ped_sel_label]
                    
                    f_id_sel = pedido_sel.get("factura_id", pedido_sel.get("id"))
                    num_fact = pedido_sel.get("numero_factura")
                    
                    val_courier_def = pedido_sel.get("courier", pedido_sel.get("courier_nombre", "Servientrega"))
                    val_repartidor_def = pedido_sel.get("repartidor", pedido_sel.get("chofer", ""))
                    val_guia_def = pedido_sel.get("numero_guia", "")
                    val_control_def = pedido_sel.get("numero_control", pedido_sel.get("codigo_control", ""))

                    with st.form("form_actualizar_guia_control_auto"):
                        st.write(f"**Modificando:** Orden de Venta Nº `{num_fact}`")
                        
                        # FILA 1: COURIER Y NOMBRE DEL REPARTIDOR AL LADO
                        c_col1, c_col2 = st.columns(2)
                        with c_col1:
                            couriers_opt = ["Servientrega", "Tame Cargo", "Cooperativa", "Uber/Moto", "Retiro en Local", "Otro"]
                            c_idx = couriers_opt.index(val_courier_def) if val_courier_def in couriers_opt else 0
                            nuevo_courier = st.selectbox("Courier / Transporte", couriers_opt, index=c_idx)
                        with c_col2:
                            nuevo_repartidor = st.text_input("Nombre Repartidor / Chofer", value=str(val_repartidor_def or ""), placeholder="Ej: Juan Pérez / Placa HJA-123").strip()

                        # FILA 2: GUÍA Y NÚMERO DE CONTROL
                        g1, g2 = st.columns(2)
                        with g1:
                            guia_val = str(val_guia_def)
                            nueva_guia = st.text_input("Número de Guía", value="" if guia_val == "SIN GUÍA" else guia_val).strip()
                        with g2:
                            ctrl_val = str(val_control_def)
                            nuevo_control = st.text_input("Número de Control", value="" if ctrl_val == "SIN CONTROL" else ctrl_val).strip()

                        # LÓGICA AUTOMÁTICA DE ESTADO
                        if nueva_guia and nueva_guia != "SIN GUÍA":
                            auto_estado = "EN TRÁNSITO"
                        elif nuevo_control and nuevo_control != "SIN CONTROL":
                            auto_estado = "EMPACADO"
                        else:
                            auto_estado = "PENDIENTE"

                        st.info(f"💡 Estado calculado automáticamente: **{auto_estado}**")

                        estados_opt = ["PENDIENTE", "EMPACADO", "EN TRÁNSITO", "ENTREGADO"]
                        e_idx = estados_opt.index(auto_estado) if auto_estado in estados_opt else 0
                        nuevo_estado = st.selectbox("Estado de Despacho (Automático / Manual)", estados_opt, index=e_idx)

                        submit_guia = st.form_submit_button("💾 Guardar Cambios de Despacho", type="primary", use_container_width=True)

                        if submit_guia:
                            payload = {
                                "factura_id": f_id_sel,
                                "numero_factura": str(num_fact),
                                "courier": nuevo_courier,
                                "repartidor": nuevo_repartidor or "N/D",
                                "numero_guia": nueva_guia or "SIN GUÍA",
                                "numero_control": nuevo_control or "SIN CONTROL",
                                "estado_despacho": nuevo_estado
                            }
                            try:
                                res_put = requests.post(f"{API_URL}/despachos/actualizar", json=payload, timeout=5)
                                if res_put.status_code in [200, 201]:
                                    st.success(f"¡Despacho guardado con éxito! Repartidor: {nuevo_repartidor or 'N/D'}")
                                    st.rerun()
                                else:
                                    res_put2 = requests.put(
                                        f"{API_URL}/pedidos/{f_id_sel}/guia", 
                                        params={
                                            "numero_guia": nueva_guia or "SIN GUÍA",
                                            "courier_nombre": nuevo_courier,
                                            "repartidor": nuevo_repartidor or "N/D",
                                            "estado_despacho": nuevo_estado
                                        },
                                        timeout=5
                                    )
                                    if res_put2.status_code == 200:
                                        st.success("¡Actualizado correctamente!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error al actualizar: {res_put.text}")
                            except Exception as ex:
                                st.error(f"Error de conexión: {str(ex)}")

            with col_b:
                st.markdown("#### 🏷️ Generar Membrete de Envío (De / Para)")
                
                if opts_pedidos:
                    ped_label_etq = st.selectbox("Seleccione Orden para Etiqueta", list(opts_pedidos.keys()), key="sel_etiqueta_log_2")
                    ped_lbl = opts_pedidos[ped_label_etq]

                    nom_dest = ped_lbl.get('cliente', ped_lbl.get('entidad_nombre', 'Consumidor Final'))
                    ruc_dest = ped_lbl.get('ruc_cedula', ped_lbl.get('entidad_ruc', 'N/D'))
                    telf_dest = ped_lbl.get('telefono', 'N/D')
                    prov_dest = ped_lbl.get('provincia', 'Guayas')
                    ciud_dest = ped_lbl.get('ciudad', 'Guayaquil')
                    dir_dest = ped_lbl.get('direccion_entrega', ped_lbl.get('direccion', 'Dirección no especificada'))
                    ref_dest = ped_lbl.get('referencia_direccion', ped_lbl.get('referencia', 'Sin referencia'))
                    cour_etq = ped_lbl.get('courier', ped_lbl.get('courier_nombre', 'Servientrega'))
                    rep_etq = ped_lbl.get('repartidor', ped_lbl.get('chofer', 'N/D'))
                    guia_etq = ped_lbl.get('numero_guia', 'SIN GUÍA')
                    ctrl_etq = ped_lbl.get('numero_control', ped_lbl.get('codigo_control', 'SIN CONTROL'))
                    num_fact_etq = ped_lbl.get('numero_factura', 'N/A')

                    html_label = f"""
                    <div style="border: 2px dashed #1e293b; padding: 20px; border-radius: 10px; background-color: #ffffff; color: #000000; font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 12px;">
                            <span style="font-weight: bold; font-size: 1.2rem;">🛍️ FAJAS ISABELLA</span>
                            <span style="font-size: 0.85rem; font-weight: bold;">ENVÍO: {str(cour_etq).upper()}</span>
                        </div>
                        
                        <!-- REMITENTE (DE) -->
                        <div style="background-color: #f1f5f9; padding: 8px; border-radius: 5px; margin-bottom: 12px; font-size: 0.85rem;">
                            <strong>DE (REMITENTE):</strong> FAJAS ISABELLA<br>
                            <strong>Ciudad:</strong> Guayaquil, Ecuador<br>
                            <strong>Atención al cliente:</strong> +593 99 999 9999
                        </div>
                        
                        <!-- DESTINATARIO (PARA) -->
                        <div style="border: 1px solid #cbd5e1; padding: 12px; border-radius: 5px; font-size: 0.95rem;">
                            <span style="font-size: 1.1rem; font-weight: bold; color: #2563eb;">PARA (DESTINATARIO):</span><br>
                            <strong>Cliente:</strong> {nom_dest}<br>
                            <strong>CI/RUC:</strong> {ruc_dest} | <strong>Teléfono:</strong> {telf_dest}<br>
                            <strong>Destino:</strong> {prov_dest} - {ciud_dest}<br>
                            <strong>Dirección:</strong> {dir_dest}<br>
                            <strong>Referencia:</strong> {ref_dest}<br>
                        </div>
                        
                        <div style="margin-top: 12px; font-size: 0.85rem; display: flex; justify-content: space-between;">
                            <span><strong>Orden #:</strong> {num_fact_etq}</span>
                            <span><strong>Guía #:</strong> {guia_etq}</span>
                            <span><strong>Control #:</strong> {ctrl_etq}</span>
                        </div>
                        <div style="margin-top: 5px; font-size: 0.8rem; color: #555;">
                            <strong>Repartidor / Chofer:</strong> {rep_etq}
                        </div>
                    </div>
                    """
                    
                    st.components.v1.html(html_label, height=350, scrolling=True)

                    st.download_button(
                        label="💾 Guardar Membrete (HTML)",
                        data=html_label,
                        file_name=f"Membrete_Orden_{num_fact_etq}.html",
                        mime="text/html",
                        use_container_width=True
                    )

        else:
            st.error(f"Error al conectar con la API: {response.text}")

    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")