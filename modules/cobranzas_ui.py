import streamlit as st
import requests

def render_gestion_cobranzas(api_url: str):
    st.header("📊 Gestión Financiera - Planes Acumulativos y Cobranza")
    st.markdown("Registra nuevos abonos de clientes y gestiona la cartera activa con saldo pendiente.")

    # --------------------------------------------------------------------------
    # OBTENER DATOS DE LA CARTERA
    # --------------------------------------------------------------------------
    listado_planes = []
    cartera_total = 0.0
    total_recaudado = 0.0
    saldo_pendiente_total = 0.0
    planes_activos = 0

    try:
        res_resumen = requests.get(f"{api_url}/cobranzas/resumen", timeout=6)
        if res_resumen.status_code == 200:
            datos_res = res_resumen.json()
            cartera_total = datos_res.get("cartera_total", 0.0)
            total_recaudado = datos_res.get("total_recaudado", 0.0)
            saldo_pendiente_total = datos_res.get("saldo_pendiente", 0.0)
            planes_activos = datos_res.get("planes_activos", 0)
            listado_planes = datos_res.get("planes", [])
    except Exception as e:
        st.warning(f"No se pudo conectar con la API de cobranzas: {e}")

    # --------------------------------------------------------------------------
    # 1. FORMULARIO DE INGRESO CON BÚSQUEDA FLEXIBLE Y VISUALIZACIÓN
    # --------------------------------------------------------------------------
    with st.expander("➕ Registrar Nuevo Abono / Aplicar Pago", expanded=True):
        
        filtro_busqueda = st.text_input(
            "🔍 Buscar cliente por RUC, Cédula o Nombre:",
            placeholder="Escribe el RUC, Cédula o nombre del cliente..."
        ).strip().lower()

        # Filtrar órdenes con saldo pendiente evaluando múltiples nombres posibles de campos
        ordenes_filtradas = []
        for plan in listado_planes:
            # Extraer campos de forma segura sin importar cómo los envíe la API
            cliente_nombre = str(plan.get('cliente') or plan.get('entidad_nombre') or 'Cliente General').lower()
            cliente_ruc = str(plan.get('ruc_cedula') or plan.get('ruc') or plan.get('entidad_ruc') or '').lower()
            num_factura = str(plan.get('numero_factura') or plan.get('id') or '').lower()
            saldo_val = float(plan.get('saldo_pendiente', 0.0))

            # Coincidencia con el filtro de búsqueda
            coincide = (
                not filtro_busqueda or 
                filtro_busqueda in cliente_nombre or 
                filtro_busqueda in cliente_ruc or 
                filtro_busqueda in num_factura
            )

            if coincide and saldo_val > 0:
                # Guardar datos normalizados para el selectbox
                plan['nombre_limpio'] = plan.get('cliente') or plan.get('entidad_nombre') or 'Cliente'
                plan['ruc_limpio'] = plan.get('ruc_cedula') or plan.get('ruc') or plan.get('entidad_ruc') or 'S/N'
                ordenes_filtradas.append(plan)

        # Si no hay texto de filtro, mostrar todas las que tengan saldo para comodidad
        if not filtro_busqueda and not ordenes_filtradas:
            for plan in listado_planes:
                if float(plan.get('saldo_pendiente', 0.0)) > 0:
                    plan['nombre_limpio'] = plan.get('cliente') or plan.get('entidad_nombre') or 'Cliente'
                    plan['ruc_limpio'] = plan.get('ruc_cedula') or plan.get('ruc') or plan.get('entidad_ruc') or 'S/N'
                    ordenes_filtradas.append(plan)

        opciones_map = {}
        for p in ordenes_filtradas:
            # 👇 AQUÍ SE MUESTRA CLARAMENTE EL NOMBRE Y EL RUC/CÉDULA AL LADO EN EL SELECTOR
            label = f"Factura #{p.get('numero_factura')} | 👤 {p.get('nombre_limpio')} (RUC/CI: {p.get('ruc_limpio')}) | Saldo: ${float(p.get('saldo_pendiente', 0)):.2f}"
            opciones_map[label] = p.get('id')

        if not opciones_map:
            st.info("ℹ️ No hay órdenes con saldo pendiente que coincidan con la búsqueda.")

        with st.form("form_nuevo_abono", clear_on_submit=True):
            seleccion_orden = st.selectbox(
                "Seleccione la Orden / Factura del cliente:",
                options=list(opciones_map.keys()) if opciones_map else ["No hay órdenes disponibles"]
            )
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                monto_abono = st.number_input("Monto a Abonar ($):", min_value=0.01, step=0.50, format="%.2f")
            with col_f2:
                metodo_pago = st.selectbox("Método de Pago:", ["Transferencia", "Efectivo", "Depósito", "Tarjeta"])

            col_f3, col_f4 = st.columns(2)
            with col_f3:
                referencia = st.text_input("Número de Referencia / Comprobante:", placeholder="Ej. #TRX-984201")
            with col_f4:
                observacion = st.text_input("Observación / Nota:", placeholder="Ej. Abono quincenal")

            btn_guardar_pago = st.form_submit_button("💳 Registrar Pago / Abono", use_container_width=True)

            if btn_guardar_pago:
                if not opciones_map or seleccion_orden not in opciones_map or seleccion_orden == "No hay órdenes disponibles":
                    st.error("⚠️ Debe seleccionar una orden válida con saldo pendiente.")
                elif monto_abono <= 0:
                    st.error("⚠️ El monto a abonar debe ser mayor a $0.00.")
                else:
                    factura_id_seleccionada = opciones_map[seleccion_orden]
                    payload = {
                        "factura_id": int(factura_id_seleccionada),
                        "monto": float(monto_abono),
                        "metodo_pago": metodo_pago,
                        "referencia_bancaria": referencia,
                        "observacion": observacion
                    }
                    try:
                        res = requests.post(f"{api_url}/cobranzas/registrar-abono", json=payload, timeout=8)
                        if res.status_code in [200, 201]:
                            st.success(f"✅ ¡Abono de ${monto_abono:.2f} registrado exitosamente!")
                            st.rerun()
                        else:
                            detail = res.json().get("detail", "Error al procesar abono")
                            st.error(f"❌ Error: {detail}")
                    except Exception as err:
                        st.error(f"❌ Error de conexión con la API: {err}")

    st.markdown("---")

    # --------------------------------------------------------------------------
    # 2. MÉTRICAS GENERALES DE CARTERA
    # --------------------------------------------------------------------------
    if st.button("🔄 Actualizar Reporte de Cartera", key="btn_refresh_cobranzas"):
        st.rerun()

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Cartera Activa Total", f"${cartera_total:,.2f}")
    col_m2.metric("Total Recaudado", f"${total_recaudado:,.2f}")
    col_m3.metric("Saldo Pendiente", f"${saldo_pendiente_total:,.2f}")
    col_m4.metric("Planes Activos", str(planes_activos))

    st.markdown("### 📋 Listado Detallado de Clientes con Saldo Pendiente")

    if not listado_planes:
        st.info("No hay planes acumulativos registrados actualmente.")
    else:
        for plan in listado_planes:
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([1.5, 2.5, 1.5, 1.5, 2])
                c1.write(f"**Factura:** #{plan.get('numero_factura')}")
                c2.write(f"**Cliente:** {plan.get('cliente') or plan.get('entidad_nombre')}")
                c3.write(f"**Total:** ${plan.get('total', 0):.2f}")
                c4.write(f"**Saldo:** :red[${plan.get('saldo_pendiente', 0):.2f}]")
                with c5:
                    if st.button(f"🔎 Seleccionar", key=f"btn_sel_{plan.get('id')}"):
                        st.info(f"Orden #{plan.get('numero_factura')} lista para abonar.")