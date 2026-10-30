import streamlit as st
import requests

def render_gestion_cobranzas(api_url):
    st.markdown("### 📊 Gestión Financiera - Planes Acumulativos y Cobranza")
    
    if st.button("🔄 Actualizar Reporte de Cartera", key="btn_refrescar_cartera"):
        st.rerun()

    try:
        # Construimos la URL base limpia removiendo '/api' si estuviera duplicado y apuntando directo al endpoint
        base_limpia = api_url.removesuffix("/api").rstrip("/")
        url_endpoint = f"{base_limpia}/api/web/acumulativo/admin/cartera-acumulativa"

        res = requests.get(url_endpoint, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            resumen = data.get("resumen", {})
            detalles = data.get("detalles", [])

            # --- TARJETAS KPI ---
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Cartera Activa Total", f"${resumen.get('total_cartera', 0.0):.2f}")
            col2.metric("Total Recaudado", f"${resumen.get('total_recaudado', 0.0):.2f}")
            col3.metric("Saldo Pendiente", f"${resumen.get('total_pendiente', 0.0):.2f}")
            col4.metric("Planes Activos", resumen.get('planes_activos', 0))

            st.divider()
            st.markdown("##### 📋 Listado Detallado de Clientes con Saldo Pendiente")

            if not detalles:
                st.info("No hay planes acumulativos registrados actualmente.")
                return

            # Renderizar tabla detallada con opciones de recordatorio
            for item in detalles:
                with st.container():
                    c_info1, c_info2, c_info3, c_info4 = st.columns([2, 2, 2, 2])
                    
                    with c_info1:
                        st.markdown(f"**Factura:** #{item['numero_factura']}")
                        st.caption(f"Fecha: {item['fecha']}")
                    with c_info2:
                        st.markdown(f"**Cliente:** {item['cliente']}")
                        st.caption(f"📞 {item['telefono']}")
                    with c_info3:
                        st.markdown(f"Total: **${item['total_orden']:.2f}**")
                        st.markdown(f"Abonado: <span style='color:green;'>**${item['total_abonado']:.2f}**</span>", unsafe_allow_html=True)
                    with c_info4:
                        st.markdown(f"Pendiente: <span style='color:red;'>**${item['saldo_pendiente']:.2f}**</span>", unsafe_allow_html=True)
                        st.markdown(f"Estado: **{item['estado']}**")

                    # Enlace directo para enviar recordatorio por WhatsApp
                    telefono_limpio = item['telefono'].replace("+", "").strip()
                    mensaje_wapp = f"Hola {item['cliente']} 👋, te saludamos de Fajas Isabella. Te recordamos que tu pedido #{item['numero_factura']} tiene un saldo pendiente de ${item['saldo_pendiente']:.2f} en tu Plan Acumulativo. ¿Deseas realizar tu abono hoy? 😊"
                    url_wapp = f"https://wa.me/{telefono_limpio}?text={requests.utils.quote(mensaje_wapp)}"
                    
                    st.markdown(f"""
                        <a href="{url_wapp}" target="_blank" style="text-decoration:none;">
                            <button style="background-color:#16a34a; color:white; border:none; padding:6px 12px; border-radius:6px; font-size:12px; font-weight:bold; cursor:pointer;">
                                📲 Enviar Recordatorio por WhatsApp
                            </button>
                        </a>
                    """, unsafe_allow_html=True)
                    st.divider()
        else:
            st.error(f"Error al conectar con el servidor de cobranzas (Código {res.status_code}): {res.text}")
    except Exception as e:
        st.warning(f"No se pudo cargar la cartera acumulativa: {e}")