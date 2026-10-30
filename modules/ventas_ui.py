import streamlit as st
import requests
import os
import pandas as pd
import json
from datetime import date

def render_ventas():
    st.markdown("### 💳 Módulo de Ventas y Facturación")
    
    API_URL = st.session_state.get("API_URL", "http://localhost:8000/api")
    
    # Pestañas de control de ventas
    tab_nueva, tab_historial = st.tabs(["🛒 Registrar Venta / Plan Acumulativo", "📋 Historial de Ventas"])
    
    with tab_nueva:
        st.markdown("##### 📝 Registro Manual de Venta o Abono Inicial")
        
        # 1. Datos del Cliente
        st.markdown("###### 1. Información del Cliente")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            ruc_cliente = st.text_input("RUC o Cédula *", placeholder="Ej: 0912345678")
        with col_c2:
            nombre_cliente = st.text_input("Nombre / Razón Social *", placeholder="Ej: María Pérez")
        with col_c3:
            telefono_cliente = st.text_input("Teléfono / WhatsApp", placeholder="Ej: 0991234567")

        col_c4, col_c5 = st.columns(2)
        with col_c4:
            correo_cliente = st.text_input("Correo Electrónico", placeholder="cliente@email.com")
        with col_c5:
            direccion_cliente = st.text_input("Dirección del Cliente", placeholder="Calle Principal y Secundaria")

        st.markdown("---")
        
        # 2. Datos de Facturación y Envío
        st.markdown("###### 2. Datos de Facturación y Logística")
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            num_factura = st.text_input("Número de Factura / Orden *", value=f"FAC-{date.today().strftime('%Y%m%d')}-01")
        with col_f2:
            fecha_factura = st.date_input("Fecha de Factura", value=date.today())
        with col_f3:
            metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Tarjeta de Crédito", "Plan Acumulativo"])

        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            provincia = st.text_input("Provincia", value="Guayas")
        with col_l2:
            ciudad = st.text_input("Ciudad", value="Guayaquil")
        with col_l3:
            courier = st.selectbox("Courier de Envío", ["Servientrega", "TAME", "Coop. Transporte", "Retiro en Local"])

        direccion_entrega = st.text_input("Dirección de Entrega (Si difiere de la del cliente)", placeholder="Dejar en blanco si es la misma")
        referencia_dir = st.text_input("Referencia de Ubicación", placeholder="Ej: Cerca del parque central, casa de dos pisos")

        if metodo_pago == "Transferencia":
            codigo_trans = st.text_input("Código o Referencia de Transferencia")
        else:
            codigo_trans = ""

        # Si es Plan Acumulativo, pedir el abono inicial
        abono_inicial = 0.0
        if metodo_pago == "Plan Acumulativo":
            st.info("💡 **Plan Acumulativo:** El cliente puede dejar un abono inicial y el saldo restante quedará pendiente para seguimiento en el módulo de Cobranzas.")
            abono_inicial = st.number_input("Valor de Abono Inicial ($)", min_value=0.0, value=0.0, step=1.0)

        st.markdown("---")

        # 3. Ítems del Producto
        st.markdown("###### 3. Selección de Productos (SKU)")
        
        # Obtener inventario disponible para la venta
        try:
            res_inv = requests.get(f"{API_URL}/inventario", timeout=5)
            inventario_lista = res_inv.json() if res_inv.status_code == 200 else []
        except Exception:
            inventario_lista = []

        if not inventario_lista:
            st.warning("⚠️ No hay productos o variantes con stock disponibles en el inventario.")
        else:
            # Crear un dataframe editable para los ítems de la venta
            df_items_inicial = pd.DataFrame([
                {"SKU": "", "Cantidad": 1, "Precio Unitario ($)": 0.0}
            ])

            st.caption("Ingresa el SKU exacto de la variante. Si dejas el precio en 0.0, el sistema aplicará automáticamente el precio oficial respetando la regla de descuentos activos.")
            df_items_editado = st.data_editor(
                df_items_inicial,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "SKU": st.column_config.TextColumn("SKU / Código de Barra", width="medium"),
                    "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1, width="small"),
                    "Precio Unitario ($)": st.column_config.NumberColumn("Precio Unitario ($ - 0 para Auto)", format="$ %.2f", min_value=0.0, width="small", help="Si se deja en 0.0, el backend calcula el precio con descuento automáticamente.")
                }
            )

            if st.button("🚀 Registrar Venta en el Sistema", type="primary", use_container_width=True):
                if not ruc_cliente or not nombre_cliente or not num_factura:
                    st.error("⚠️ Por favor completa los campos obligatorios del cliente y el número de factura.")
                elif df_items_editado.empty:
                    st.error("⚠️ Debes agregar al menos un producto a la venta.")
                else:
                    # Preparar ítems
                    items_payload = []
                    for _, row in df_items_editado.iterrows():
                        sku_val = str(row.get("SKU", "")).strip()
                        cant_val = int(row.get("Cantidad", 1))
                        precio_val = float(row.get("Precio Unitario ($)", 0.0))
                        
                        if sku_val:
                            items_payload.append({
                                "sku": sku_val,
                                "cantidad": cant_val,
                                "precio_unitario": precio_val
                            })

                    if not items_payload:
                        st.error("⚠️ Especifica al menos un SKU válido en la tabla de productos.")
                    else:
                        payload_venta = {
                            "numero_factura": num_factura.strip(),
                            "fecha_factura": str(fecha_factura),
                            "metodo_pago": metodo_pago,
                            "codigo_transferencia": codigo_trans,
                            "ruc_cliente": ruc_cliente.strip(),
                            "nombre_cliente": nombre_cliente.strip(),
                            "direccion_cliente": direccion_cliente.strip() if direccion_cliente else "",
                            "telefono_cliente": telefono_cliente.strip() if telefono_cliente else "",
                            "provincia": provincia,
                            "ciudad": ciudad,
                            "direccion_entrega": direccion_entrega if direccion_entrega else direccion_cliente,
                            "referencia_direccion": referencia_dir,
                            "courier_nombre": courier,
                            "abono_inicial": abono_inicial,
                            "items": items_payload
                        }

                        try:
                            resp = requests.post(f"{API_URL}/ventas-factura", json=payload_venta, timeout=10)
                            if resp.status_code == 200:
                                st.success("✅ ¡Venta registrada y stock descontado exitosamente!")
                                st.balloons()
                            else:
                                err_det = resp.json().get("detail", "Error desconocido")
                                st.error(f"❌ Error al procesar la venta: {err_det}")
                        except Exception as ex:
                            st.error(f"❌ Error de conexión con la API: {ex}")

    with tab_historial:
        st.markdown("##### 📋 Historial General de Ventas")
        try:
            res_rep = requests.get(f"{API_URL}/ventas/reporte", timeout=5)
            if res_rep.status_code == 200:
                facturas_data = res_rep.json()
                if facturas_data:
                    df_ventas = pd.DataFrame(facturas_data)
                    st.dataframe(df_ventas, use_container_width=True)
                else:
                    st.info("No hay ventas registradas todavía.")
            else:
                st.warning("No se pudo obtener el reporte de ventas del servidor.")
        except Exception as e:
            st.error(f"Error de conexión: {e}")