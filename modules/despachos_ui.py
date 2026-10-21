import streamlit as st
import requests
import os
import pandas as pd
from datetime import date

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
    st.markdown("Gestiona estados, guías, números de control y genera etiquetas múltiples (3 por hoja A4).")

    col_btn1, _ = st.columns([0.15, 0.85])
    with col_btn1:
        if st.button("🔄 Actualizar", key="btn_refresh_desp"):
            st.rerun()

    try:
        response = requests.get(f"{API_URL}/despachos/reporte", timeout=8)

        if response.status_code == 200:
            data_despachos = response.json()
            if not data_despachos:
                st.info("No se encontraron despachos registrados en el sistema.")
                return

            df_raw = pd.DataFrame(data_despachos)

            st.markdown("##### 🔍 Filtros de Búsqueda")
            col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.5, 1.5, 1.5])
            with col_f1:
                busqueda = st.text_input("Buscador Rápido:", placeholder="Buscar por Nº Orden, Cliente, Guía o Control...").strip()
            with col_f2:
                filtro_estado = st.selectbox("Estado Despacho:", ["TODOS", "EN TRÁNSITO", "PENDIENTE", "EMPACADO", "ENTREGADO"])
            with col_f3:
                fecha_inicio = st.date_input("Fecha Desde:", value=date(2025, 1, 1))
            with col_f4:
                fecha_fin = st.date_input("Fecha Hasta:", value=date.today())

            st.divider()

            df_filtrado = df_raw.copy()
            if busqueda:
                mask = (
                    df_filtrado.get("numero_factura", "").astype(str).str.contains(busqueda, case=False, na=False) |
                    df_filtrado.get("cliente", "").astype(str).str.contains(busqueda, case=False, na=False) |
                    df_filtrado.get("numero_guia", "").astype(str).str.contains(busqueda, case=False, na=False) |
                    df_filtrado.get("numero_control", "").astype(str).str.contains(busqueda, case=False, na=False)
                )
                df_filtrado = df_filtrado[mask]

            if filtro_estado != "TODOS":
                col_est = "estado_despacho" if "estado_despacho" in df_filtrado.columns else "estado"
                if col_est in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado[col_est].astype(str).str.upper() == filtro_estado]

            if "fecha" in df_filtrado.columns:
                df_filtrado["fecha_dt"] = pd.to_datetime(df_filtrado["fecha"], errors="coerce").dt.date
                df_filtrado = df_filtrado[
                    (df_filtrado["fecha_dt"].isna()) | 
                    ((df_filtrado["fecha_dt"] >= fecha_inicio) & (df_filtrado["fecha_dt"] <= fecha_fin))
                ]

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

            # --- TABLA CON SELECCIÓN MÚLTIPLE (CHECKBOX) ---
            st.markdown("#### 📋 Listado de Pedidos y Selección para Impresión Múltiple (3 por A4)")
            
            df_tabla_ui = []
            for idx, r in df_filtrado.iterrows():
                estado_bruto = r.get("estado_despacho", "PENDIENTE")
                
                guia_val = str(r.get("numero_guia", "SIN GUÍA")).strip()
                guia_tabla = guia_val if guia_val not in ["None", "null", "", "nan", "NaN"] else "SIN GUÍA"

                control_val = str(r.get("numero_control", "SIN CONTROL")).strip()
                control_tabla = control_val if control_val not in ["None", "null", "", "SIN CONTROL", "nan", "NaN"] else "SIN CONTROL"

                df_tabla_ui.append({
                    "Seleccionar": False,
                    "Nº Orden Venta": r.get("numero_factura", "N/A"),
                    "Fecha": r.get("fecha", "N/A"),
                    "Cliente": r.get("cliente", "Consumidor Final"),
                    "Provincia": r.get("provincia", "Guayas"),
                    "Ciudad": r.get("ciudad", "Guayaquil"),
                    "Courier": r.get("courier", "Servientrega"),
                    "Nº Guía": guia_tabla,
                    "Nº Control": control_tabla,
                    "Estado": obtener_semaforo_estado(estado_bruto),
                    "_raw": r
                })

            df_edit_table = pd.DataFrame(df_tabla_ui)
            
            if not df_edit_table.empty:
                columns_config = {
                    "Seleccionar": st.column_config.CheckboxColumn("🖨️ Imprimir", default=False),
                    "_raw": None
                }
                
                df_resultado_editado = st.data_editor(
                    df_edit_table.drop(columns=["_raw"]),
                    column_config=columns_config,
                    use_container_width=True,
                    hide_index=True,
                    key="editor_tabla_despachos"
                )

                seleccionados_indices = df_resultado_editado[df_resultado_editado["Seleccionar"] == True].index.tolist()
                pedidos_seleccionados_lote = [df_tabla_ui[i]["_raw"] for i in seleccionados_indices]

                if pedidos_seleccionados_lote:
                    st.markdown(f"**{len(pedidos_seleccionados_lote)} pedido(s) marcado(s) para impresión múltiple.**")
                    
                    html_lote = """
                    <!DOCTYPE html>
                    <html lang="es">
                    <head>
                        <meta charset="UTF-8">
                        <title>Membretes Múltiples (3 por A4)</title>
                        <style>
                            @page { size: A4 portrait; margin: 10mm; }
                            body { font-family: Arial, sans-serif; margin: 0; background: #fff; }
                            .hoja-a4 {
                                height: 275mm;
                                display: flex;
                                flex-direction: column;
                                justify-content: space-between;
                                page-break-after: always;
                                box-sizing: border-box;
                                margin-bottom: 20px;
                            }
                            .membrete-card {
                                border: 2px dashed #1e293b;
                                padding: 12px 18px;
                                border-radius: 8px;
                                background-color: #ffffff;
                                color: #000000;
                                box-sizing: border-box;
                                height: 87mm;
                                display: flex;
                                flex-direction: column;
                                justify-content: space-between;
                            }
                            .header {
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                border-bottom: 2px solid #000;
                                padding-bottom: 4px;
                            }
                            .remitente-box {
                                background-color: #f1f5f9;
                                padding: 6px;
                                border-radius: 4px;
                                font-size: 0.8rem;
                            }
                            .destinatario-box {
                                border: 1px solid #cbd5e1;
                                padding: 8px;
                                border-radius: 4px;
                                font-size: 0.85rem;
                            }
                            .footer-info {
                                font-size: 0.8rem;
                                display: flex;
                                justify-content: space-between;
                                font-weight: bold;
                            }
                            @media print {
                                .no-print { display: none; }
                                .hoja-a4 { margin-bottom: 0; page-break-after: always; }
                            }
                        </style>
                    </head>
                    <body>
                        <div class="no-print" style="text-align: center; margin: 15px;">
                            <button onclick="window.print()" style="padding: 10px 25px; font-size: 16px; background: #2563eb; color: white; border: none; border-radius: 5px; cursor: pointer;">
                                🖨️ Imprimir Membretes (3 por Hoja A4)
                            </button>
                        </div>
                    """
                    
                    for i in range(0, len(pedidos_seleccionados_lote), 3):
                        grupo = pedidos_seleccionados_lote[i:i+3]
                        html_lote += '<div class="hoja-a4">'
                        for ped in grupo:
                            n_ord = ped.get('numero_factura')
                            c_cli = ped.get('cliente', 'Consumidor Final')
                            r_ruc = ped.get('ruc_cedula', 'N/D')
                            t_tel = ped.get('telefono', 'N/D')
                            p_pro = ped.get('provincia', 'Guayas')
                            c_ciu = ped.get('ciudad', 'Guayaquil')
                            d_dir = ped.get('direccion', 'N/A')
                            r_ref = ped.get('referencia', 'Sin referencia')
                            co_cur = str(ped.get('courier', 'Servientrega')).upper()
                            
                            raw_rep = ped.get('repartidor')
                            re_rep = str(raw_rep).strip() if (raw_rep is not None and str(raw_rep).strip() not in ["None", "null", "", "N/D", "nan", "NaN"]) else "N/D"

                            raw_guia = ped.get('numero_guia')
                            gu_g = str(raw_guia).strip() if (raw_guia is not None and str(raw_guia).strip() not in ["None", "null", "", "SIN GUÍA", "nan", "NaN"]) else "SIN GUÍA"

                            raw_ctrl = ped.get('numero_control')
                            co_c = str(raw_ctrl).strip() if (raw_ctrl is not None and str(raw_ctrl).strip() not in ["None", "null", "", "SIN CONTROL", "nan", "NaN"]) else "SIN CONTROL"
                            
                            html_lote += f"""
                            <div class="membrete-card">
                                <div class="header">
                                    <span style="font-weight: bold; font-size: 1.1rem;">🛍️ FAJAS ISABELLA</span>
                                    <span style="font-size: 0.85rem; font-weight: bold;">ENVÍO: {co_cur}</span>
                                </div>
                                <div class="remitente-box">
                                    <strong>DE (REMITENTE):</strong> FAJAS ISABELLA | Guayaquil, Ecuador | Tel: +593 99 999 9999
                                </div>
                                <div class="destinatario-box">
                                    <strong style="color: #2563eb;">PARA (DESTINATARIO):</strong> {c_cli}<br>
                                    <strong>CI/RUC:</strong> {r_ruc} | <strong>Teléfono:</strong> {t_tel}<br>
                                    <strong>Destino:</strong> {p_pro} - {c_ciu}<br>
                                    <strong>Dirección:</strong> {d_dir} | <strong>Ref:</strong> {r_ref}
                                </div>
                                <div class="footer-info">
                                    <span>Orden #: {n_ord}</span>
                                    <span>Guía #: {gu_g}</span>
                                    <span>Control #: {co_c}</span>
                                    <span>Chofer: {re_rep}</span>
                                </div>
                            </div>
                            """
                        for _ in range(3 - len(grupo)):
                            html_lote += '<div style="height: 87mm;"></div>'
                            
                        html_lote += '</div>'

                    html_lote += "</body></html>"

                    st.download_button(
                        label="📥 Descargar HTML Lote Membretes (3 por A4)",
                        data=html_lote,
                        file_name=f"Membretes_Lote_{date.today()}.html",
                        mime="text/html",
                        use_container_width=True
                    )

            st.divider()

            # --- GESTIÓN Y DETALLE DE ORDEN SELECCIONADA ---
            opts_pedidos = {
                f"Orden #{r.get('numero_factura')} - {r.get('cliente', 'N/A')} ({r.get('ciudad', 'Guayaquil')})": r
                for _, r in df_filtrado.iterrows()
            }

            if opts_pedidos:
                st.markdown("#### 🎛️ Gestión, Regla de Oro y Detalle de Orden Seleccionada")
                
                keys_pedidos = list(opts_pedidos.keys())
                if "ultima_orden_seleccionada" not in st.session_state or st.session_state.ultima_orden_seleccionada not in keys_pedidos:
                    st.session_state.ultima_orden_seleccionada = keys_pedidos[0]

                ped_sel_label = st.selectbox(
                    "Seleccione Orden de Venta", 
                    keys_pedidos, 
                    index=keys_pedidos.index(st.session_state.ultima_orden_seleccionada),
                    key="sel_pedido_act_log"
                )
                st.session_state.ultima_orden_seleccionada = ped_sel_label
                pedido_sel = opts_pedidos[ped_sel_label]

                f_id_sel = pedido_sel.get("factura_id", pedido_sel.get("id"))
                num_fact = pedido_sel.get("numero_factura")
                
                # Saneamiento robusto para el detalle seleccionado
                raw_g_sel = pedido_sel.get("numero_guia")
                guia_show = str(raw_g_sel).strip() if (raw_g_sel is not None and str(raw_g_sel).strip() not in ["None", "null", "", "SIN GUÍA", "nan", "NaN"]) else "SIN GUÍA"

                raw_c_sel = pedido_sel.get("numero_control")
                control_show = str(raw_c_sel).strip() if (raw_c_sel is not None and str(raw_c_sel).strip() not in ["None", "null", "", "SIN CONTROL", "nan", "NaN"]) else "SIN CONTROL"

                raw_r_sel = pedido_sel.get("repartidor")
                repartidor_show = str(raw_r_sel).strip() if (raw_r_sel is not None and str(raw_r_sel).strip() not in ["None", "null", "", "N/D", "nan", "NaN"]) else "N/D"

                courier_show = pedido_sel.get("courier", "Servientrega")
                
                with st.expander(f"📦 Ver información completa y productos de la Orden Nº {num_fact}", expanded=False):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write(f"**Cliente:** {pedido_sel.get('cliente', 'N/A')}")
                        st.write(f"**RUC/Cédula:** {pedido_sel.get('ruc_cedula', 'N/A')}")
                        st.write(f"**Fecha:** {pedido_sel.get('fecha', 'N/A')}")
                    with c2:
                        st.write(f"**Provincia / Ciudad:** {pedido_sel.get('provincia', 'Guayas')} / {pedido_sel.get('ciudad', 'Guayaquil')}")
                        st.write(f"**Dirección:** {pedido_sel.get('direccion', 'N/A')}")
                        st.write(f"**Referencia:** {pedido_sel.get('referencia', 'Sin referencia')}")
                    with c3:
                        st.write(f"**Courier / Repartidor:** {courier_show} ({repartidor_show})")
                        st.write(f"**Nº Guía:** `{guia_show}`")
                        st.write(f"**Nº Control:** `{control_show}`")
                        st.write(f"**Estado Despacho:** `{pedido_sel.get('estado_despacho', 'PENDIENTE')}`")

                st.markdown("---")

                val_courier_def = courier_show
                val_repartidor_def = "" if repartidor_show == "N/D" else repartidor_show
                val_guia_def = "" if guia_show == "SIN GUÍA" else guia_show
                val_ctrl_def = "" if control_show == "SIN CONTROL" else control_show

                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown("#### 🚚 Actualizar Guía, Control, Repartidor y Estado")
                    
                    with st.form("form_actualizar_despacho_final"):
                        st.write(f"**Modificando:** Orden de Venta Nº `{num_fact}`")
                        
                        c_col1, c_col2 = st.columns(2)
                        with c_col1:
                            couriers_opt = ["Servientrega", "Tame Cargo", "Cooperativa", "Uber/Moto", "Retiro en Local", "Otro"]
                            c_idx = couriers_opt.index(val_courier_def) if val_courier_def in couriers_opt else 0
                            nuevo_courier = st.selectbox("Courier / Transporte", couriers_opt, index=c_idx)
                        with c_col2:
                            nuevo_repartidor = st.text_input("Nombre Repartidor / Chofer", value=str(val_repartidor_def or ""), placeholder="Ej: Moto Hermano 15").strip()

                        g1, g2 = st.columns(2)
                        with g1:
                            nueva_guia = st.text_input("Número de Guía", value=val_guia_def, placeholder="Ingresar Guía...").strip()
                        with g2:
                            nuevo_control = st.text_input("Número de Control", value=val_ctrl_def, placeholder="Ingresar Control...").strip()

                        st.markdown("---")
                        st.info("ℹ️ **Regla de Oro:** Si ingresas Número de Guía, es obligatorio tener un Número de Control guardado. Al tener ambos valores, el estado cambia automáticamente a **EN TRÁNSITO**.")

                        submit_guia = st.form_submit_button("💾 Guardar Cambios de Despacho", type="primary", use_container_width=True)

                        if submit_guia:
                            nc_temp = nuevo_control if nuevo_control != "" else "SIN CONTROL"
                            ng_temp = nueva_guia if nueva_guia != "" else "SIN GUÍA"

                            if ng_temp != "SIN GUÍA" and nc_temp == "SIN CONTROL":
                                st.error("⚠️ Regla de Oro Violada: ¡No puedes guardar un Número de Guía sin haber ingresado y guardado primero el Número de Control!")
                            else:
                                est_calculado = "EN TRÁNSITO" if (ng_temp != "SIN GUÍA" and nc_temp != "SIN CONTROL") else ""

                                payload = {
                                    "factura_id": f_id_sel,
                                    "numero_factura": str(num_fact),
                                    "courier": nuevo_courier,
                                    "repartidor": nuevo_repartidor or "N/D",
                                    "numero_guia": ng_temp,
                                    "numero_control": nc_temp,
                                    "estado_despacho": est_calculado
                                }
                                try:
                                    with st.spinner("Guardando en servidor..."):
                                        res_put = requests.post(f"{API_URL}/despachos/actualizar", json=payload, timeout=8)
                                    
                                    if res_put.status_code in [200, 201]:
                                        st.success(f"✅ Orden de Venta #{num_fact} actualizada con éxito y puesta en Tránsito.")
                                        st.rerun() 
                                    else:
                                        try:
                                            err_detail = res_put.json().get("detail", res_put.text)
                                        except:
                                            err_detail = res_put.text
                                        st.error(f"⚠️ Error del servidor: {err_detail}")
                                except Exception as ex:
                                    st.error(f"❌ Error de conexión al guardar: {str(ex)}")

                with col_b:
                    st.markdown("#### 🏷️ Membrete Individual de Vista Previa")
                    
                    nom_dest = pedido_sel.get('cliente', 'Consumidor Final')
                    ruc_dest = pedido_sel.get('ruc_cedula', 'N/D')
                    telf_dest = pedido_sel.get('telefono', 'N/D')
                    prov_dest = pedido_sel.get('provincia', 'Guayas')
                    ciud_dest = pedido_sel.get('ciudad', 'Guayaquil')
                    dir_dest = pedido_sel.get('direccion', 'Dirección no especificada')
                    ref_dest = pedido_sel.get('referencia', 'Sin referencia')
                    cour_etq = courier_show
                    
                    rep_etq = repartidor_show
                    guia_etq = guia_show
                    control_etq = control_show
                    num_fact_etq = str(num_fact)

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
                            <span><strong>Control #:</strong> {control_etq}</span>
                        </div>
                        <div style="margin-top: 5px; font-size: 0.8rem; color: #555;">
                            <strong>Repartidor / Chofer:</strong> {rep_etq}
                        </div>
                    </div>
                    """
                    
                    st.components.v1.html(html_label, height=350, scrolling=True)

                    st.download_button(
                        label="💾 Guardar Membrete Individual (HTML)",
                        data=html_label,
                        file_name=f"Membrete_Orden_{num_fact_etq}.html",
                        mime="text/html",
                        use_container_width=True
                    )
        else:
            st.error(f"Error al conectar con la API: {response.text}")
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")