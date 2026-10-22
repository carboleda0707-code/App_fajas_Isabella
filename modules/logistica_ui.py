import streamlit as st
import requests
import os
import pandas as pd
from datetime import date

API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production-ea5a.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

def render_logistica():
    # --- TÍTULO PROPIO DEL MÓDULO (ENCABEZADO GLOBAL YA EN RENDER_APP) ---
    st.title("📦 Gestión de Logística y Despachos")

    # Botones principales en estilo Radio Horizontal (Consistente con Inventario/Ventas)
    accion = st.radio(
        "Acción:",
        ["📦 1. Embalaje", "🚚 2. Envío", "🖨️ 3. Imprimir Membrete"],
        horizontal=True,
        key="radio_logistica_accion"
    )

    st.divider()

    # Obtener reporte general de ventas/despachos desde la API
    try:
        response = requests.get(f"{API_URL}/despachos/reporte", timeout=8)
        data_despachos = response.json() if response.status_code == 200 else []
    except Exception as e:
        st.error(f"❌ Error al conectar con la API: {str(e)}")
        data_despachos = []

    df_raw = pd.DataFrame(data_despachos) if data_despachos else pd.DataFrame()

    # =========================================================================
    # BOTÓN 1: EMBALAJE (Órdenes PENDIENTES -> EMPACADO)
    # =========================================================================
    if accion == "📦 1. Embalaje":
        st.markdown("### 📦 1. Embalaje de Pedidos")
        st.caption("Filtra órdenes pendientes, revisa el detalle de items e ingresa el Número de Control para pasar a estado EMPACADO.")

        if df_raw.empty:
            st.info("No hay órdenes registradas.")
            return

        col_est = "estado_despacho" if "estado_despacho" in df_raw.columns else "estado"
        df_pendientes = df_raw[df_raw[col_est].astype(str).str.upper() == "PENDIENTE"].copy()

        if df_pendientes.empty:
            st.success("🎉 No hay órdenes pendientes de embalaje.")
            return

        # Filtros de búsqueda (Ciudad, RUC/Cédula, Orden)
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
            st.warning("No se encontraron órdenes pendientes con los filtros ingresados.")
            return

        opts_emb = {
            f"Orden #{r.get('numero_factura')} - {r.get('cliente', 'N/A')} ({r.get('ciudad', 'Guayaquil')})": r
            for _, r in df_filtered.iterrows()
        }
        ord_sel_label = st.selectbox("Seleccione Orden de Venta a Embalar:", list(opts_emb.keys()), key="emb_sel_ord")
        ord_sel = opts_emb[ord_sel_label]

        st.markdown("---")
        
        c_det1, c_det2 = st.columns([0.6, 0.4])
        with c_det1:
            st.markdown("#### 📄 Detalle de la Orden e Items")
            st.write(f"**Cliente:** {ord_sel.get('cliente', 'N/A')}")
            st.write(f"**CI/RUC:** {ord_sel.get('ruc_cedula', 'N/A')} | **Teléfono:** {ord_sel.get('telefono', 'N/A')}")
            st.write(f"**Destino:** {ord_sel.get('provincia', 'Guayas')} - {ord_sel.get('ciudad', 'Guayaquil')}")
            st.write(f"**Dirección:** {ord_sel.get('direccion', 'N/A')}")
            st.write(f"**Referencia:** {ord_sel.get('referencia', 'Sin referencia')}")

            items = ord_sel.get("items", ord_sel.get("detalles", []))
            if items:
                st.markdown("**Ítems a Empacar:**")
                st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)

        with c_det2:
            st.markdown("#### 🔢 Registrar Número de Control")
            f_id = ord_sel.get("factura_id", ord_sel.get("id"))
            num_fact = ord_sel.get("numero_factura")

            ctrl_actual = str(ord_sel.get("numero_control", "")).strip()
            ctrl_actual = "" if ctrl_actual in ["None", "null", "SIN CONTROL", "nan"] else ctrl_actual

            num_control_input = st.text_input("Número de Control:", value=ctrl_actual, placeholder="Digite Nº de Control...", key=f"emb_ctrl_{num_fact}").strip()

            if st.button("💾 Guardar y Pasar a EMPACADO", type="primary", use_container_width=True, key=f"btn_emb_save_{num_fact}"):
                if not num_control_input:
                    st.error("⚠️ Debe digitar un Número de Control para pasar a estado EMPACADO.")
                else:
                    payload = {
                        "factura_id": f_id,
                        "numero_factura": str(num_fact),
                        "numero_control": num_control_input,
                        "estado_despacho": "EMPACADO"
                    }
                    try:
                        res = requests.post(f"{API_URL}/despachos/actualizar", json=payload, timeout=8)
                        if res.status_code in [200, 201]:
                            st.success(f"✅ Orden #{num_fact} guardada y cambiada a estado EMPACADO.")
                            st.rerun()
                        else:
                            st.error(f"Error al actualizar: {res.text}")
                    except Exception as ex:
                        st.error(f"Error de conexión: {str(ex)}")

    # =========================================================================
    # BOTÓN 2: ENVÍO (Órdenes EMPACADO -> EN TRÁNSITO)
    # =========================================================================
    elif accion == "🚚 2. Envío":
        st.markdown("### 🚚 2. Gestión de Envío")
        st.caption("Filtra órdenes empacadas, asigna courier, repartidor y número de guía para pasar a estado EN TRÁNSITO.")

        if df_raw.empty:
            st.info("No hay órdenes registradas.")
            return

        col_est = "estado_despacho" if "estado_despacho" in df_raw.columns else "estado"
        df_empacados = df_raw[df_raw[col_est].astype(str).str.upper() == "EMPACADO"].copy()

        if df_empacados.empty:
            st.info("ℹ️ No hay órdenes con estado EMPACADO listas para envío.")
            return

        # Filtros de búsqueda (Ciudad, RUC/Cédula, Orden)
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

            items = ord_sel.get("items", ord_sel.get("detalles", []))
            if items:
                st.markdown("**Ítems:**")
                st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)

        with c_det2:
            st.markdown("#### 📝 Asignar Datos de Envío")
            f_id = ord_sel.get("factura_id", ord_sel.get("id"))
            num_fact = ord_sel.get("numero_factura")

            raw_c = str(ord_sel.get("numero_control", "")).strip()
            val_c = "" if raw_c in ["None", "null", "SIN CONTROL", "nan"] else raw_c

            raw_g = str(ord_sel.get("numero_guia", "")).strip()
            val_g = "" if raw_g in ["None", "null", "SIN GUÍA", "nan"] else raw_g

            raw_r = str(ord_sel.get("repartidor", "")).strip()
            val_r = "" if raw_r in ["None", "null", "N/D", "nan"] else raw_r

            cour_actual = ord_sel.get("courier", "Servientrega")

            # Configuración limpia de sesión para el número de control
            ctrl_key_env = f"env_ctrl_{num_fact}"
            if ctrl_key_env not in st.session_state or not st.session_state[ctrl_key_env]:
                st.session_state[ctrl_key_env] = val_c

            num_control = st.text_input("Número de Control (Ver/Modificar):", key=ctrl_key_env).strip()
            
            couriers_opt = ["Servientrega", "Tame Cargo", "Cooperativa", "Uber/Moto", "Retiro en Local", "Otro"]
            c_idx = couriers_opt.index(cour_actual) if cour_actual in couriers_opt else 0
            courier_sel = st.selectbox("Seleccionar Courier / Transporte:", couriers_opt, index=c_idx, key=f"env_cour_{num_fact}")

            repartidor = st.text_input("Nombre Repartidor / Chofer:", value=val_r, placeholder="Ej: Carlos Moto 02", key=f"env_rep_{num_fact}").strip()
            num_guia = st.text_input("Número de Guía:", value=val_g, placeholder="Digite Nº de Guía...", key=f"env_guia_{num_fact}").strip()

            if st.button("💾 Guardar y Pasar a EN TRÁNSITO", type="primary", use_container_width=True, key=f"btn_env_save_{num_fact}"):
                if not num_control or not num_guia:
                    st.error("⚠️ Tanto el Número de Control como el Número de Guía son obligatorios para enviar la orden.")
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
                        res = requests.post(f"{API_URL}/despachos/actualizar", json=payload, timeout=8)
                        if res.status_code in [200, 201]:
                            st.success(f"✅ Orden #{num_fact} asignada a courier y pasada a EN TRÁNSITO.")
                            st.rerun()
                        else:
                            st.error(f"Error al actualizar: {res.text}")
                    except Exception as ex:
                        st.error(f"Error de conexión: {str(ex)}")

    # =========================================================================
    # BOTÓN 3: IMPRIMIR MEMBRETE (Solo EN TRÁNSITO -> 1 a 3 por Hoja A4)
    # =========================================================================
    elif accion == "🖨️ 3. Imprimir Membrete":
        st.markdown("### 🖨️ 3. Impresión de Membretes de Envío")
        st.caption("Selecciona de 1 a 3 órdenes en estado EN TRÁNSITO para generar la hoja A4 de membretes lista para imprimir.")

        if df_raw.empty:
            st.info("No hay órdenes registradas.")
            return

        col_est = "estado_despacho" if "estado_despacho" in df_raw.columns else "estado"
        df_transito = df_raw[df_raw[col_est].astype(str).str.upper().isin(["EN TRÁNSITO", "EN TRANSITO"])].copy()

        if df_transito.empty:
            st.info("ℹ️ No hay órdenes en estado EN TRÁNSITO para imprimir membretes.")
            return

        opts_imp = {
            f"Orden #{r.get('numero_factura')} - {r.get('cliente', 'N/A')} ({r.get('ciudad', 'Guayaquil')})": r
            for _, r in df_transito.iterrows()
        }

        ordenes_seleccionadas = st.multiselect(
            "Seleccione las órdenes a imprimir (Máximo 3 por hoja A4):",
            options=list(opts_imp.keys()),
            max_selections=3,
            key="ms_imprimir_a4"
        )

        if ordenes_seleccionadas:
            pedidos_lote = [opts_imp[k] for k in ordenes_seleccionadas]
            
            html_a4 = """
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>Membretes de Envío A4</title>
                <style>
                    @page { size: A4 portrait; margin: 10mm; }
                    body { font-family: Arial, sans-serif; margin: 0; background: #fff; }
                    .hoja-a4 {
                        height: 275mm;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-around;
                        box-sizing: border-box;
                    }
                    .membrete-card {
                        border: 2px dashed #1e293b;
                        padding: 14px 18px;
                        border-radius: 8px;
                        background-color: #ffffff;
                        color: #000000;
                        box-sizing: border-box;
                        height: 85mm;
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
                    }
                </style>
            </head>
            <body>
                <div class="no-print" style="text-align: center; margin: 15px;">
                    <button onclick="window.print()" style="padding: 10px 25px; font-size: 16px; background: #2563eb; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">
                        🖨️ Click Aquí para Imprimir Hoja A4
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
                gu_g = str(raw_guia).strip() if (raw_guia is not None and str(raw_guia).strip() not in ["None", "null", "", "SIN GUÍA"]) else "SIN GUÍA"

                raw_ctrl = ped.get('numero_control')
                co_c = str(raw_ctrl).strip() if (raw_ctrl is not None and str(raw_ctrl).strip() not in ["None", "null", "", "SIN CONTROL"]) else "SIN CONTROL"

                html_a4 += f"""
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

            html_a4 += """
                </div>
            </body>
            </html>
            """

            st.components.v1.html(html_a4, height=600, scrolling=True)

            st.download_button(
                label="📥 Descargar Hoja A4 en HTML",
                data=html_a4,
                file_name=f"Membretes_A4_{date.today()}.html",
                mime="text/html",
                use_container_width=True
            )