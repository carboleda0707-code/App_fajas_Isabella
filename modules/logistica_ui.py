import streamlit as st
import requests
import os
import pandas as pd
from datetime import date

API_URL = st.session_state.get("API_URL", "http://localhost:8000/api")


def obtener_items_orden(ord_sel):
    items = (
        ord_sel.get("items") or 
        ord_sel.get("detalles") or 
        ord_sel.get("productos") or 
        []
    )
    
    if items:
        return items

    num_fact_str = str(ord_sel.get("numero_factura", "")).strip()
    f_id_str = str(ord_sel.get("factura_id", ord_sel.get("id", ""))).strip()

    if num_fact_str or f_id_str:
        try:
            res_mov = requests.get(f"{API_URL}/movimientos", timeout=4)
            if res_mov.status_code == 200:
                movs = res_mov.json()
                items_kardex = []
                for m in movs:
                    ref_f = str(m.get('referencia_factura', '')).strip()
                    num_m = str(m.get('numero_factura', '')).strip()
                    
                    if (num_fact_str and (num_fact_str in ref_f or num_fact_str in num_m or ref_f.lstrip('0') == num_fact_str.lstrip('0'))) or \
                       (f_id_str and f_id_str in ref_f):
                        items_kardex.append(m)
                return items_kardex
        except Exception:
            pass

    return []


def render_logistica():
    st.markdown("<p style='color: black; font-weight: bold;'>📦 Gestión de Logística y Despachos</p>", unsafe_allow_html=True)   
     
    accion = st.radio(
        "Acción:",
        ["📦 1. Embalaje", "🚚 2. Envío", "🖨️ 3. Imprimir Membrete"],
        horizontal=True,
        key="radio_logistica_accion"
    )

    st.divider()

    try:
        response = requests.get(f"{API_URL}/logistica/reporte", timeout=8)
        data_despachos = response.json() if response.status_code == 200 else []
    except Exception as e:
        st.error(f"❌ Error al conectar con la API: {str(e)}")
        data_despachos = []

    df_raw = pd.DataFrame(data_despachos) if data_despachos else pd.DataFrame()

    # --- BOTÓN 1: EMBALAJE ---
    if accion == "📦 1. Embalaje":
        st.markdown("##### 📦 1. Embalaje de Pedidos")
        st.caption("Filtra órdenes pendientes o por aprobar, revisa el detalle exacto de ítems e ingresa el Número de Control para pasar a EMPACADO.")

        if df_raw.empty:
            st.info("No hay órdenes registradas en la base de datos.")
            return

        col_est = "estado_despacho" if "estado_despacho" in df_raw.columns else "estado"
        df_pendientes = df_raw[df_raw[col_est].astype(str).str.upper().isin(["PENDIENTE", "POR APROBAR"])].copy()

        if df_pendientes.empty:
            st.success("🎉 No hay órdenes pendientes ni por aprobar de embalaje.")
            return

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            f_ciudad = st.text_input("Filtrar por Ciudad:", placeholder="Ej: Guayaquil", key="emb_f_ciudad").strip()
        with col_f2:
            f_ruc = st.text_input("Filtrar por RUC/Cédula:", placeholder="Ej: 0914592936", key="emb_f_ruc").strip()
        with col_f3:
            f_orden = st.text_input("Filtrar por Nº Orden:", placeholder="Ej: 54566", key="emb_f_orden").strip()

        df_filtered = df_pendientes.copy()
        if f_ciudad:
            df_filtered = df_filtered[df_filtered.get("ciudad", "").astype(str).str.contains(f_ciudad, case=False, na=False)]
        if f_ruc:
            df_filtered = df_filtered[df_filtered.get("ruc_cedula", "").astype(str).str.contains(f_ruc, case=False, na=False)]
        if f_orden:
            df_filtered = df_filtered[df_filtered.get("numero_factura", "").astype(str).str.contains(f_orden, case=False, na=False)]

        if df_filtered.empty:
            st.warning("No se encontraron órdenes con los filtros ingresados.")
            return

        opts_emb = {
            f"Orden #{r.get('numero_factura')} - {r.get('cliente', 'N/A')} ({r.get('ciudad', 'Guayaquil')}) [{r.get('estado_despacho', 'PENDIENTE')}]": r
            for _, r in df_filtered.iterrows()
        }
        ord_sel_label = st.selectbox("Seleccione Orden de Venta a Embalar:", list(opts_emb.keys()), key="emb_sel_ord")
        ord_sel = opts_emb[ord_sel_label]

        st.markdown("---")
        
        c_det1, c_det2 = st.columns([0.65, 0.35])
        with c_det1:
            st.markdown("##### 📄 Detalle del Cliente y Destino")
            st.write(f"**Cliente:** {ord_sel.get('cliente', 'N/A')}")
            st.write(f"**CI/RUC:** {ord_sel.get('ruc_cedula', 'N/A')} | **Teléfono:** {ord_sel.get('telefono', 'N/A')}")
            st.write(f"**Destino:** {ord_sel.get('provincia', 'Guayas')} - {ord_sel.get('ciudad', 'Guayaquil')}")
            st.write(f"**Dirección:** {ord_sel.get('direccion', 'N/A')}")
            st.write(f"**Referencia:** {ord_sel.get('referencia', 'Sin referencia')}")
            st.write(f"**Estado Actual:** `{ord_sel.get('estado_despacho', 'PENDIENTE')}`")

            st.markdown("---")
            st.markdown("##### 🛍️ Ítems a Empacar (Solo SKU y Cantidad)")
            
            items_factura = obtener_items_orden(ord_sel)

            if items_factura:
                tabla_items = []
                for idx, it in enumerate(items_factura, 1):
                    sku = it.get("sku") or it.get("sku_producto") or it.get("codigo_producto") or "N/A"
                    cant = abs(int(it.get("cantidad", it.get("cant", 1))))
                    
                    tabla_items.append({
                        "Item #": idx,
                        "SKU": sku,
                        "Cantidad": cant
                    })
                
                st.dataframe(pd.DataFrame(tabla_items), use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ No se encontraron registros de ítems en esta orden o el Kardex está vacío.")

        with c_det2:
            st.markdown("##### 🔢 Registrar Número de Control")
            f_id = ord_sel.get("factura_id", ord_sel.get("id"))
            num_fact = ord_sel.get("numero_factura")

            ctrl_actual = str(ord_sel.get("numero_control", "")).strip()
            if ctrl_actual in ["None", "null", "SIN CONTROL", "nan", ""]:
                ctrl_actual = ""

            num_control_input = st.text_input("Número de Control:", value=ctrl_actual, placeholder="Digite Nº de Control...", key=f"emb_ctrl_{num_fact}").strip()

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Guardar y Pasar a EMPACADO", type="primary", use_container_width=True, key=f"btn_emb_save_{num_fact}"):
                if not num_control_input:
                    st.error("⚠️ Debe digitar obligatoriamente un Número de Control real para pasar a estado EMPACADO.")
                else:
                    payload = {
                        "factura_id": f_id,
                        "numero_factura": str(num_fact),
                        "numero_control": num_control_input,
                        "estado_despacho": "EMPACADO"
                    }
                    try:
                        res = requests.post(f"{API_URL}/logistica/actualizar", json=payload, timeout=8)
                        if res.status_code in [200, 201]:
                            st.success(f"✅ Orden #{num_fact} guardada y cambiada a estado EMPACADO.")
                            st.rerun()
                        else:
                            st.error(f"Error al actualizar: {res.text}")
                    except Exception as ex:
                        st.error(f"Error de conexión: {str(ex)}")

    # --- BOTÓN 2: ENVÍO ---
    elif accion == "🚚 2. Envío":
        st.markdown("### 🚚 2. Gestión de Envío")
        st.caption("Filtra órdenes empacadas, asigna courier, repartidor y número de guía real para pasar a EN TRÁNSITO.")

        if df_raw.empty:
            st.info("No hay órdenes registradas.")
            return

        col_est = "estado_despacho" if "estado_despacho" in df_raw.columns else "estado"
        df_empacados = df_raw[df_raw[col_est].astype(str).str.upper() == "EMPACADO"].copy()

        if df_empacados.empty:
            st.info("ℹ️ No hay órdenes con estado EMPACADO listas para envío.")
            return

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            f_ciudad = st.text_input("Filtrar por Ciudad:", placeholder="Ej: Guayaquil", key="env_f_ciudad").strip()
        with col_f2:
            f_ruc = st.text_input("Filtrar por RUC/Cédula:", placeholder="Ej: 0914592936", key="env_f_ruc").strip()
        with col_f3:
            f_orden = st.text_input("Filtrar por Nº Orden:", placeholder="Ej: 54566", key="env_f_orden").strip()

        df_filtered = df_empacados.copy()
        if f_ciudad:
            df_filtered = df_filtered[df_filtered.get("ciudad", "").astype(str).str.contains(f_ciudad, case=False, na=False)]
        if f_ruc:
            df_filtered = df_filtered[df_filtered.get("ruc_cedula", "").astype(str).str.contains(f_ruc, case=False, na=False)]
        if f_orden:
            df_filtered = df_filtered[df_filtered.get("numero_factura", "").astype(str).str.contains(f_orden, case=False, na=False)]

        if df_filtered.empty:
            st.warning("No se encontraron órdenes empacadas con los filtros ingresados.")
            return

        opts_env = {
            f"Orden #{r.get('numero_factura')} - {r.get('cliente', 'N/A')} ({r.get('ciudad', 'Guayaquil')})": r
            for _, r in df_filtered.iterrows()
        }
        ord_sel_label = st.selectbox("Seleccione Orden Empacada:", list(opts_env.keys()), key="env_sel_ord")
        ord_sel = opts_env[ord_sel_label]

        st.markdown("---")

        c_det1, c_det2 = st.columns([0.5, 0.5])
        with c_det1:
            st.markdown("#### 📄 Detalle de la Orden e Ítems")
            st.write(f"**Cliente:** {ord_sel.get('cliente', 'N/A')}")
            st.write(f"**CI/RUC:** {ord_sel.get('ruc_cedula', 'N/A')} | **Tel:** {ord_sel.get('telefono', 'N/A')}")
            st.write(f"**Destino:** {ord_sel.get('provincia', 'Guayas')} - {ord_sel.get('ciudad', 'Guayaquil')}")
            st.write(f"**Dirección:** {ord_sel.get('direccion', 'N/A')}")
            st.write(f"**Referencia:** {ord_sel.get('referencia', 'Sin referencia')}")

            items_factura = obtener_items_orden(ord_sel)
            if items_factura:
                tabla_items = []
                for idx, it in enumerate(items_factura, 1):
                    sku = it.get("sku") or it.get("sku_producto") or it.get("codigo_producto") or "N/A"
                    cant = abs(int(it.get("cantidad", it.get("cant", 1))))
                    prec_bruto = (
                        it.get("precio_unitario") or 
                        it.get("precio") or 
                        it.get("precio_venta") or 
                        it.get("costo_unitario") or 
                        0.0
                    )
                    prec = float(prec_bruto)
                    subtotal = cant * prec
                    
                    tabla_items.append({
                        "Item #": idx,
                        "SKU": sku,
                        "Cantidad": cant,
                        "Precio Unit. ($)": f"${prec:,.2f}",
                        "Subtotal ($)": f"${subtotal:,.2f}"
                    })
                
                st.dataframe(pd.DataFrame(tabla_items), use_container_width=True, hide_index=True)

        with c_det2:
            st.markdown("#### 📝 Asignar Datos de Envío Reales")
            f_id = ord_sel.get("factura_id", ord_sel.get("id"))
            num_fact = ord_sel.get("numero_factura")

            raw_c = str(ord_sel.get("numero_control", "")).strip()
            val_c = "" if raw_c in ["None", "null", "SIN CONTROL", "nan"] else raw_c

            raw_g = str(ord_sel.get("numero_guia", "")).strip()
            val_g = "" if raw_g in ["None", "null", "SIN GUÍA", "nan"] else raw_g

            raw_r = str(ord_sel.get("repartidor", "")).strip()
            val_r = "" if raw_r in ["None", "null", "N/D", "nan"] else raw_r

            cour_actual = ord_sel.get("courier", "Servientrega")

            num_control = st.text_input("Número de Control:", value=val_c, key=f"env_ctrl_{num_fact}").strip()
            
            couriers_opt = ["Servientrega", "Tame Cargo", "Cooperativa", "Uber/Moto", "Retiro en Local", "Otro"]
            c_idx = couriers_opt.index(cour_actual) if cour_actual in couriers_opt else 0
            courier_sel = st.selectbox("Seleccionar Courier / Transporte:", couriers_opt, index=c_idx, key=f"env_cour_{num_fact}")

            repartidor = st.text_input("Nombre Repartidor / Chofer:", value=val_r, placeholder="Ej: Carlos Moto 02", key=f"env_rep_{num_fact}").strip()
            
            num_guia = st.text_input("Número de Guía (Real del Courier):", value=val_g, placeholder="Digite Nº de Guía real...", key=f"env_guia_{num_fact}").strip()

            if st.button("💾 Guardar y Pasar a EN TRÁNSITO", type="primary", use_container_width=True, key=f"btn_env_save_{num_fact}"):
                if not num_control or not num_guia:
                    st.error("⚠️ REGLA DE ORO: Tanto el Número de Control como el Número de Guía real son obligatorios para pasar a EN TRÁNSITO.")
                else:
                    payload = {
                        "factura_id": f_id,
                        "numero_factura": str(num_fact),
                        "numero_control": num_control,
                        "courier": courier_sel,
                        "repartidor": repartidor or "N/D",
                        "numero_guia": num_guia,
                        "estado_despacho": "EN TRÁNSITO"
                    }
                    try:
                        res = requests.post(f"{API_URL}/logistica/actualizar", json=payload, timeout=8)
                        if res.status_code in [200, 201]:
                            st.success(f"✅ Orden #{num_fact} asignada a courier y pasada a EN TRÁNSITO.")
                            st.rerun()
                        else:
                            st.error(f"Error al actualizar: {res.text}")
                    except Exception as ex:
                        st.error(f"Error de conexión: {str(ex)}")

    # --- BOTÓN 3: IMPRIMIR MEMBRETE ---
    elif accion == "🖨️ 3. Imprimir Membrete":
        st.markdown("### 🖨️ 3. Impresión de Membretes de Envío (Formato 3x2 Ampliado)")
        st.caption("Selecciona órdenes en estado EN TRÁNSITO que posean su guía real registrada para generar la cuadrícula A4.")

        if df_raw.empty:
            st.info("No hay órdenes registradas.")
            return

        col_est = "estado_despacho" if "estado_despacho" in df_raw.columns else "estado"
        df_transito = df_raw[df_raw[col_est].astype(str).str.upper().isin(["EN TRÁNSITO", "EN TRANSITO"])].copy()

        if df_transito.empty:
            st.info("ℹ️ No hay órdenes en estado EN TRÁNSITO para imprimir membretes.")
            return

        opts_imp = {
            f"Orden #{r.get('numero_factura')} - {r.get('cliente', 'N/A')} (Guía: {r.get('numero_guia', 'SIN GUÍA')})": r
            for _, r in df_transito.iterrows()
        }

        ordenes_seleccionadas = st.multiselect(
            "Seleccione las órdenes a imprimir (Máximo 6 por hoja A4):",
            options=list(opts_imp.keys()),
            max_selections=6,
            key="ms_imprimir_a4_3x2_grande"
        )

        if ordenes_seleccionadas:
            pedidos_lote = [opts_imp[k] for k in ordenes_seleccionadas]
            
            html_a4 = """
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>Membretes de Envío 3x2 A4</title>
                <style>
                    @page { size: A4 portrait; margin: 6mm; }
                    body { font-family: Arial, sans-serif; margin: 0; background: #fff; }
                    .no-print { text-align: center; margin: 15px; }
                    .hoja-a4 {
                        width: 198mm;
                        height: 285mm;
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        grid-template-rows: repeat(3, 1fr);
                        gap: 3mm;
                        box-sizing: border-box;
                    }
                    .membrete-card {
                        border: 2px dashed #1e293b;
                        padding: 10px 12px;
                        border-radius: 6px;
                        background-color: #ffffff;
                        color: #000000;
                        box-sizing: border-box;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                        font-size: 0.85rem;
                        overflow: hidden;
                    }
                    .header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        border-bottom: 2px solid #000;
                        padding-bottom: 4px;
                        font-weight: bold;
                        font-size: 0.95rem;
                    }
                    .remitente-box {
                        background-color: #f1f5f9;
                        padding: 4px 6px;
                        border-radius: 3px;
                        font-size: 0.75rem;
                    }
                    .destinatario-box {
                        border: 1.5px solid #cbd5e1;
                        padding: 6px 8px;
                        border-radius: 4px;
                        font-size: 0.82rem;
                        line-height: 1.3;
                    }
                    .footer-info {
                        font-size: 0.8rem;
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 4px;
                        font-weight: bold;
                    }
                    @media print {
                        .no-print { display: none; }
                    }
                </style>
            </head>
            <body>
                <div class="no-print">
                    <button onclick="window.print()" style="padding: 10px 25px; font-size: 16px; background: #2563eb; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">
                        🖨️ Imprimir Cuadrícula A4 (3x2)
                    </button>
                </div>
                <div class="hoja-a4">
            """

            for ped in pedidos_lote:
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
                re_rep = str(raw_rep).strip() if (raw_rep is not None and str(raw_rep).strip() not in ["None", "null", "", "N/D"]) else "N/D"

                raw_guia = ped.get('numero_guia')
                gu_g = str(raw_guia).strip() if (raw_guia is not None and str(raw_guia).strip() not in ["None", "null", "", "SIN GUÍA"]) else "PENDIENTE GUÍA"

                raw_ctrl = ped.get('numero_control')
                co_c = str(raw_ctrl).strip() if (raw_ctrl is not None and str(raw_ctrl).strip() not in ["None", "null", "", "SIN CONTROL"]) else "PENDIENTE CONTROL"

                html_a4 += f"""
                <div class="membrete-card">
                    <div class="header">
                        <span>🛍️ FAJAS ISABELLA</span>
                        <span>ENVÍO: {co_cur}</span>
                    </div>
                    <div class="remitente-box">
                        <strong>DE:</strong> FAJAS ISABELLA | Guayaquil | Tel: +593 99 999 9999
                    </div>
                    <div class="destinatario-box">
                        <strong style="color: #2563eb;">PARA:</strong> {c_cli}<br>
                        <strong>CI/RUC:</strong> {r_ruc} | <strong>Tel:</strong> {t_tel}<br>
                        <strong>Destino:</strong> {p_pro} - {c_ciu}<br>
                        <strong>Dir:</strong> {d_dir} | <strong>Ref:</strong> {r_ref}
                    </div>
                    <div class="footer-info">
                        <div>Orden #: {n_ord}</div>
                        <div>Chofer: {re_rep}</div>
                        <div>Guía #: {gu_g}</div>
                        <div>Control #: {co_c}</div>
                    </div>
                </div>
                """

            html_a4 += """
                </div>
            </body>
            </html>
            """

            st.components.v1.html(html_a4, height=680, scrolling=True)

            st.download_button(
                label="📥 Descargar Hoja A4 3x2 en HTML",
                data=html_a4,
                file_name=f"Membretes_3x2_{date.today()}.html",
                mime="text/html",
                use_container_width=True
            )