import streamlit as st
import requests
import os
import pandas as pd
import io
from datetime import date, datetime

# Conexión estricta de Producción en Nube
API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

def obtener_semaforo_estado(estado):
    est = str(estado).upper().strip()
    if est == "PENDIENTE":
        return "🔴 PENDIENTE"
    elif est == "EMPACADO":
        return "🟡 EMPACADO"
    elif est in ["EN TRÁNSITO", "EN TRANSITO"]:
        return "🟢 EN TRÁNSITO"
    elif est == "ENTREGADO":
        return "🔵 ENTREGADO"
    return f"⚪ {est}"

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

            # --- TARJETAS DE MÉTRICAS (KPIs) ---
            total_pedidos = len(df_filtrado)
            col_est = "estado_despacho" if "estado_despacho" in df_filtrado.columns else "estado"
            
            if col_est in df_filtrado.columns:
                estados_upper = df_filtrado[col_est].astype(str).str.upper().str.strip()
                pendientes = len(df_filtrado[estados_upper == "PENDIENTE"])
                empacados = len(df_filtrado[estados_upper == "EMPACADO"])
                en_transito = len(df_filtrado[estados_upper.isin(["EN TRÁNSITO", "EN TRANSITO"])])
                entregados = len(df_filtrado[estados_upper == "ENTREGADO"])
            else:
                pendientes, empacados, en_transito, entregados = 0, 0, 0, 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📦 Total Pedidos", total_pedidos)
            m2.metric("⏳ Pendientes", pendientes)
            m3.metric("🟡 Empacados", empacados)
            m4.metric("🚚 En Tránsito", en_transito)

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

            data_tabla = []
            for _, r in df_filtrado.iterrows():
                estado_bruto = r.get("estado_despacho", r.get("estado", "PENDIENTE"))
                
                data_tabla.append({
                    "Nº Orden Venta": r.get("numero_factura", "N/A"),
                    "Fecha": r.get("fecha", r.get("fecha_factura", "N/A")),
                    "Cliente": r.get("cliente", r.get("entidad_nombre", "Consumidor Final")),
                    "Provincia": r.get("provincia", "Guayas"),
                    "Ciudad": r.get("ciudad", "Guayaquil"),
                    "Courier": r.get("courier", r.get("courier_nombre", "Servientrega")),
                    "Repartidor/Chofer": r.get("repartidor", r.get("chofer", "N/D")),
                    "Nº Guía": r.get("numero_guia", "SIN GUÍA"),
                    "Nº Control": r.get("numero_control", r.get("control_numero", r.get("codigo_control", "SIN CONTROL"))),
                    "Total ($)": f"${r.get('total_norm', 0.0):,.2f}",
                    "Estado Despacho": obtener_semaforo_estado(estado_bruto)
                })

            st.dataframe(pd.DataFrame(data_tabla), use_container_width=True, hide_index=True)

            st.divider()

            # --- SECCIÓN OPERATIVA ÚNICA (SELECTOR MAESTRO) ---
            opts_pedidos = {
                f"Orden #{r.get('numero_factura')} - {r.get('cliente', r.get('entidad_nombre', 'N/A'))} ({r.get('ciudad', 'Guayaquil')})": r
                for _, r in df_filtrado.iterrows()
            }

            if opts_pedidos:
                st.markdown("#### 🎛️ Gestión y Detalle de Orden Seleccionada")
                ped_sel_label = st.selectbox("Seleccione Orden de Venta", list(opts_pedidos.keys()), key="sel_pedido_act_log")
                pedido_sel = opts_pedidos[ped_sel_label]
                
                # --- 🕵️‍♂️ AQUÍ ESTÁ EL CHIVATO ---
                st.info(f"🕵️‍♂️ **CHIVATO DE DATOS DE LA ORDEN:** `{pedido_sel}`")
                # --------------------------------

                f_id_sel = pedido_sel.get("factura_id", pedido_sel.get("id"))
                num_fact = pedido_sel.get("numero_factura")
                monto_factura_tot = float(pedido_sel.get("total_norm", 0.0))
                
                with st.expander(f"📦 Ver información completa y productos de la Orden Nº {num_fact}", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write(f"**Cliente:** {pedido_sel.get('cliente', pedido_sel.get('entidad_nombre', 'N/A'))}")
                        st.write(f"**RUC/Cédula:** {pedido_sel.get('ruc_cedula', pedido_sel.get('entidad_ruc', 'N/A'))}")
                        st.write(f"**Fecha:** {pedido_sel.get('fecha', pedido_sel.get('fecha_factura', 'N/A'))}")
                    with c2:
                        st.write(f"**Provincia / Ciudad:** {pedido_sel.get('provincia', 'Guayas')} / {pedido_sel.get('ciudad', 'Guayaquil')}")
                        st.write(f"**Dirección:** {pedido_sel.get('direccion', pedido_sel.get('direccion_entrega', 'N/A'))}")
                        st.write(f"**Referencia:** {pedido_sel.get('referencia', pedido_sel.get('referencia_direccion', 'Sin referencia'))}")
                    with c3:
                        st.write(f"**Courier / Repartidor:** {pedido_sel.get('courier', 'Servientrega')} ({pedido_sel.get('repartidor', 'N/D')})")
                        st.write(f"**Nº Guía:** {pedido_sel.get('numero_guia', 'SIN GUÍA')}")
                        st.write(f"**Nº Control:** {pedido_sel.get('numero_control', pedido_sel.get('control_numero', 'SIN CONTROL'))}")
                        st.write(f"**Estado Despacho:** `{pedido_sel.get('estado_despacho', 'PENDIENTE')}`")

                    st.markdown("---")
                    st.markdown("##### 🛍️ Detalle de Ítems / Fajas Vendidas")

                    items_factura = pedido_sel.get("items", [])
                    num_fact_str = str(num_fact).strip()

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
                        st.info(f"⚠️ No se encontraron ítems desglosados para la Orden Nº {num_fact}.")

                st.markdown("---")

                val_courier_def = pedido_sel.get("courier", pedido_sel.get("courier_nombre", "Servientrega"))
                val_repartidor_def = pedido_sel.get("repartidor", pedido_sel.get("chofer", ""))
                val_guia_def = pedido_sel.get("numero_guia", "")
                val_control_def = pedido_sel.get("numero_control", pedido_sel.get("control_numero", pedido_sel.get("codigo_control", "")))

                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown("#### 🚚 Actualizar Guía, Repartidor, Control y Estado")
                    
                    with st.form("form_actualizar_guia_control_auto"):
                        st.write(f"**Modificando:** Orden de Venta Nº `{num_fact}`")
                        
                        c_col1, c_col2 = st.columns(2)
                        with c_col1:
                            couriers_opt = ["Servientrega", "Tame Cargo", "Cooperativa", "Uber/Moto", "Retiro en Local", "Otro"]
                            c_idx = couriers_opt.index(val_courier_def) if val_courier_def in couriers_opt else 0
                            nuevo_courier = st.selectbox("Courier / Transporte", couriers_opt, index=c_idx)
                        with c_col2:
                            nuevo_repartidor = st.text_input("Nombre Repartidor / Chofer", value=str(val_repartidor_def or ""), placeholder="Ej: Juan Pérez / Placa HJA-123").strip()

                        g1, g2 = st.columns(2)
                        with g1:
                            guia_val = str(val_guia_def)
                            nueva_guia = st.text_input("Número de Guía", value="" if guia_val == "SIN GUÍA" else guia_val).strip()
                        with g2:
                            ctrl_val = str(val_control_def)
                            nuevo_control = st.text_input("Número de Control (En blanco autogenera)", value="" if ctrl_val in ["SIN CONTROL", "None", "nan", ""] else ctrl_val).strip()

                        if nueva_guia and nueva_guia != "SIN GUÍA":
                            auto_estado = "EN TRÁNSITO"
                        elif (nuevo_control and nuevo_control != "SIN CONTROL") or (val_control_def and str(val_control_def) not in ["SIN CONTROL", "None", ""]):
                            auto_estado = "EMPACADO"
                        else:
                            auto_estado = "PENDIENTE"

                        st.info(f"💡 Estado calculado automáticamente: **{auto_estado}**")

                        estados_opt = ["PENDIENTE", "EMPACADO", "EN TRÁNSITO", "ENTREGADO"]
                        e_idx = estados_opt.index(auto_estado) if auto_estado in estados_opt else 0
                        nuevo_estado = st.selectbox("Estado de Despacho (Automático / Manual)", estados_opt, index=e_idx)

                        submit_guia = st.form_submit_button("💾 Guardar Cambios de Despacho", type="primary", use_container_width=True)

                        if submit_guia:
                            ctrl_envio = nuevo_control if (nuevo_control and nuevo_control.strip() != "") else ""
                            guia_envio = nueva_guia if (nueva_guia and nueva_guia.strip() != "") else "SIN GUÍA"

                            if (guia_envio != "SIN GUÍA") and (not ctrl_envio or ctrl_envio == "SIN CONTROL"):
                                st.error("⚠️ No se puede registrar un Número de Guía ni cambiar a 'EN TRÁNSITO' si el Número de Control está en blanco. Asigne primero el Número de Control.")
                            else:
                                payload = {
                                    "factura_id": f_id_sel,
                                    "numero_factura": str(num_fact),
                                    "courier": nuevo_courier,
                                    "repartidor": nuevo_repartidor or "N/D",
                                    "numero_guia": guia_envio,
                                    "numero_control": ctrl_envio,
                                    "estado_despacho": nuevo_estado
                                }
                                try:
                                    res_put = requests.post(f"{API_URL}/despachos/actualizar", json=payload, timeout=5)
                                    if res_put.status_code in [200, 201]:
                                        st.success(f"✅ Orden de Venta #{num_fact} actualizada con éxito.")
                                        st.rerun() 
                                    else:
                                        st.error(f"Error al actualizar el despacho: {res_put.text}")
                                except Exception as ex:
                                    st.error(f"Error de conexión con el servidor: {str(ex)}")

                with col_b:
                    st.markdown("#### 🏷️ Generar Membrete de Envío (De / Para)")
                    
                    nom_dest = pedido_sel.get('cliente', pedido_sel.get('entidad_nombre', 'Consumidor Final'))
                    ruc_dest = pedido_sel.get('ruc_cedula', pedido_sel.get('entidad_ruc', 'N/D'))
                    telf_dest = pedido_sel.get('telefono', 'N/D')
                    prov_dest = pedido_sel.get('provincia', 'Guayas')
                    ciud_dest = pedido_sel.get('ciudad', 'Guayaquil')
                    dir_dest = pedido_sel.get('direccion_entrega', pedido_sel.get('direccion', 'Dirección no especificada'))
                    ref_dest = pedido_sel.get('referencia_direccion', pedido_sel.get('referencia', 'Sin referencia'))
                    cour_etq = pedido_sel.get('courier', pedido_sel.get('courier_nombre', 'Servientrega'))
                    rep_etq = pedido_sel.get('repartidor', pedido_sel.get('chofer', 'N/D'))
                    guia_etq = pedido_sel.get('numero_guia', 'SIN GUÍA')
                    ctrl_etq = pedido_sel.get('numero_control', pedido_sel.get('control_numero', pedido_sel.get('codigo_control', 'SIN CONTROL')))
                    num_fact_etq = pedido_sel.get('numero_factura', 'N/A')

                    html_label = f"""
                    <div style="border: 2px dashed #1e293b; padding: 20px; border-radius: 10px; background-color: #ffffff; color: #000000; font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 12px;">
                            <span style="font-weight: bold; font-size: 1.2rem;">🛍️ FAJAS ISABELLA</span>
                            <span style="font-size: 0.85rem; font-weight: bold;">ENVÍO: {str(cour_etq).upper()}</span>
                        </div>
                        
                        <div style="background-color: #f1f5f9; padding: 8px; border-radius: 5px; margin-bottom: 12px; font-size: 0.85rem;">
                            <strong>DE (REMITENTE):</strong> FAJAS ISABELLA<br>
                            <strong>Ciudad:</strong> Guayaquil, Ecuador<br>
                            <strong>Atención al cliente:</strong> +593 99 999 9999
                        </div>
                        
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