import streamlit as st
import requests
from datetime import datetime

def render_gestion_cobranzas(api_url: str):
    st.header("📊 Gestión Financiera - Planes Acumulativos y Cobranza")
    st.markdown("Registra nuevos abonos de clientes y gestiona la cartera activa con saldo pendiente.")

    # --------------------------------------------------------------------------
    # 1. FORMULARIO DE INGRESO / APLICACIÓN DE PAGOS Y ABONOS
    # --------------------------------------------------------------------------
    with st.expander("➕ Registrar Nuevo Abono / Aplicar Pago", expanded=True):
        col_busq1, col_busq2 = st.columns([2, 1])
        with col_busq1:
            factura_id_input = st.text_input(
                "Número de Factura o ID de Orden:",
                placeholder="Ej. 2411001 o ID..."
            )
        
        # Cargar detalles si hay búsqueda
        if factura_id_input:
            try:
                # Consulta a la API para obtener los datos de la factura
                res_fact = requests.get(f"{api_url}/web/auth/pedidos/{factura_id_input}", timeout=5)
                # O si buscas por ID directo / endpoint de cartera:
                res_cartera = requests.get(f"{api_url}/cobranzas/ordenes-activas", timeout=5)
            except Exception as e:
                st.caption(f"ℹ️ Ingrese el ID numérico de la factura para cargar los detalles.")

        with st.form("form_nuevo_abono", clear_on_submit=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                factura_id = st.number_input("ID de Factura / Plan:", min_value=1, step=1)
            with col_f2:
                monto_abono = st.number_input("Monto a Abonar ($):", min_value=0.01, step=0.50, format="%.2f")
            with col_f3:
                metodo_pago = st.selectbox("Método de Pago:", ["Transferencia", "Efectivo", "Depósito", "Tarjeta"])

            col_f4, col_f5 = st.columns(2)
            with col_f4:
                referencia = st.text_input("Número de Referencia / Comprobante:", placeholder="Ej. #TRX-984201")
            with col_f5:
                observacion = st.text_input("Observación / Nota:", placeholder="Ej. Segundo abono quincenal")

            btn_guardar_pago = st.form_submit_button("💳 Registrar Pago / Abono", use_container_width=True)

            if btn_guardar_pago:
                if not factura_id or monto_abono <= 0:
                    st.error("⚠️ Debe ingresar un ID de factura válido y un monto mayor a $0.00.")
                else:
                    payload = {
                        "factura_id": int(factura_id),
                        "monto": float(monto_abono),
                        "metodo_pago": metodo_pago,
                        "referencia_bancaria": referencia,
                        "observacion": observacion
                    }
                    try:
                        res = requests.post(f"{api_url}/cobranzas/registrar-abono", json=payload, timeout=8)
                        if res.status_code in [200, 201]:
                            st.success(f"✅ ¡Abono de ${monto_abono:.2f} registrado exitosamente en la Factura #{factura_id}!")
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

    # Intentar obtener datos resumidos de la API
    cartera_total = 0.0
    total_recaudado = 0.0
    saldo_pendiente = 0.0
    planes_activos = 0
    listado_planes = []

    try:
        res_resumen = requests.get(f"{api_url}/cobranzas/resumen", timeout=6)
        if res_resumen.status_code == 200:
            datos_res = res_resumen.json()
            cartera_total = datos_res.get("cartera_total", 0.0)
            total_recaudado = datos_res.get("total_recaudado", 0.0)
            saldo_pendiente = datos_res.get("saldo_pendiente", 0.0)
            planes_activos = datos_res.get("planes_activos", 0)
            listado_planes = datos_res.get("planes", [])
    except Exception:
        pass

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Cartera Activa Total", f"${cartera_total:,.2f}")
    col_m2.metric("Total Recaudado", f"${total_recaudado:,.2f}")
    col_m3.metric("Saldo Pendiente", f"${saldo_pendiente:,.2f}")
    col_m4.metric("Planes Activos", str(planes_activos))

    st.markdown("### 📋 Listado Detallado de Clientes con Saldo Pendiente")

    if not listado_planes:
        st.info("No hay planes acumulativos registrados actualmente o no hay saldo pendiente pendiente por cobrar.")
    else:
        for plan in listado_planes:
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([1.5, 2.5, 1.5, 1.5, 2])
                c1.write(f"**Factura:** #{plan.get('numero_factura')}")
                c2.write(f"**Cliente:** {plan.get('cliente')}")
                c3.write(f"**Total:** ${plan.get('total', 0):.2f}")
                c4.write(f"**Saldo:** :red[${plan.get('saldo_pendiente', 0):.2f}]")
                with c5:
                    if st.button(f"💵 Abonar", key=f"btn_abono_{plan.get('id')}"):
                        st.session_state["factura_abono_seleccionada"] = plan.get('id')
                        st.info(f"Ingresa los datos del abono en el formulario superior para el ID: {plan.get('id')}")