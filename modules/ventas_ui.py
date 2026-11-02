import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime

def render_ventas():
    st.markdown("### 💳 Módulo de Ventas y Facturación")
    
    API_URL = st.session_state.get("API_URL", "http://localhost:8000/api")
    
    tab_nueva, tab_historial = st.tabs(["🛒 Registrar Venta / Plan Acumulativo", "📋 Historial de Ventas"])
    
    with tab_nueva:
        st.markdown("##### 📝 Registro Manual de Venta o Abono Inicial")
        
        # 1. Búsqueda y Selección Inteligente de Cliente
        st.markdown("###### 1. Información del Cliente")
        try:
            res_cli = requests.get(f"{API_URL}/clientes", timeout=5)
            lista_clientes = res_cli.json() if res_cli.status_code == 200 else []
        except Exception:
            lista_clientes = []

        opciones_cli = {"-- NUEVO CLIENTE (Ingreso Manual) --": None}
        for c in lista_clientes:
            etiqueta = f"{c.get('ruc_cedula', '')} - {c.get('nombre', '')}"
            opciones_cli[etiqueta] = c

        cliente_seleccionado_str = st.selectbox(
            "🔍 Buscar Cliente Registrado (por Cédula o Nombre)", 
            options=list(opciones_cli.keys()),
            help="Escribe o selecciona un cliente para autocompletar sus datos automáticamente."
        )

        sel_data = opciones_cli.get(cliente_seleccionado_str)

        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            ruc_cliente = st.text_input("RUC o Cédula *", value=sel_data.get('ruc_cedula', '') if sel_data else "", placeholder="Ej: 0912345678")
        with col_c2:
            nombre_cliente = st.text_input("Nombre / Razón Social *", value=sel_data.get('nombre', '') if sel_data else "", placeholder="Ej: María Pérez")
        with col_c3:
            telefono_cliente = st.text_input("Teléfono / WhatsApp", value=sel_data.get('telefono', '') if sel_data else "", placeholder="Ej: 0991234567")

        col_c4, col_c5 = st.columns(2)
        with col_c4:
            correo_cliente = st.text_input("Correo Electrónico", value=sel_data.get('correo', '') if sel_data else "", placeholder="cliente@email.com")
        with col_c5:
            direccion_cliente = st.text_input("Dirección del Cliente", value=sel_data.get('direccion', '') if sel_data else "", placeholder="Calle Principal y Secundaria")

        st.markdown("---")
        
        # 2. Datos de Facturación y Logística
        st.markdown("###### 2. Datos de Facturación y Logística")
        
        hoy = date.today()
        prefijo_aamm = hoy.strftime("%y%m") # Ej: "2611" para noviembre 2026
        
        siguiente_consecutivo = 1
        try:
            res_rep = requests.get(f"{API_URL}/ventas/reporte", timeout=5)
            if res_rep.status_code == 200:
                facturas_existentes = res_rep.json()
                consecutivos_mes = []
                for f in facturas_existentes:
                    num_fac = str(f.get("numero_factura", ""))
                    if num_fac.startswith(prefijo_aamm):
                        sufijo = num_fac[len(prefijo_aamm):]
                        if sufijo.isdigit():
                            consecutivos_mes.append(int(sufijo))
                if consecutivos_mes:
                    siguiente_consecutivo = max(consecutivos_mes) + 1
        except Exception:
            pass
        
        num_factura_auto = f"{prefijo_aamm}{siguiente_consecutivo:03d}"

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            num_factura = st.text_input("Número de Factura / Orden (Automático) *", value=num_factura_auto, disabled=True, help="Generado automáticamente por el sistema (AAMM + Secuencial).")
        with col_f2:
            fecha_factura = st.date_input("Fecha de Factura", value=hoy)
        with col_f3:
            metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Tarjeta de Crédito", "Plan Acumulativo"])

        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            provincia = st.text_input("Provincia", value="Guayas")
        with col_l2:
            ciudad = st.text_input("Ciudad", value="Guayaquil")
        with col_l3:
            courier = st.selectbox("Courier de Envío", ["Servientrega", "TAME", "Coop. Transporte", "Retiro en Local"])

        col_dir1, col_dir2 = st.columns(2)
        with col_dir1:
            direccion_entrega = st.text_input("Dirección de Entrega (Si difiere)", placeholder="Dejar en blanco si es la misma")
        with col_dir2:
            referencia_dir = st.text_input("Referencia de Ubicación", placeholder="Ej: Cerca del parque central")

        codigo_trans = ""
        if metodo_pago == "Transferencia":
            codigo_trans = st.text_input("Código o Referencia de Transferencia")

        abono_inicial = 0.0
        if metodo_pago == "Plan Acumulativo":
            st.info("💡 **Plan Acumulativo:** El cliente puede dejar un abono inicial y el saldo restante quedará pendiente.")
            abono_inicial = st.number_input("Valor de Abono Inicial ($)", min_value=0.0, value=0.0, step=1.0)

        st.markdown("---")

        # 3. Selección de Productos
        st.markdown("###### 3. Selección e Ingreso de Productos")
        
        inventario_lista = []
        try:
            res_inv = requests.get(f"{API_URL}/inventario", timeout=5)
            if res_inv.status_code == 200:
                inventario_lista = res_inv.json()
        except Exception:
            pass

        if not inventario_lista:
            try:
                res_prod = requests.get(f"{API_URL}/productos", timeout=5)
                if res_prod.status_code == 200:
                    inventario_lista = res_prod.json()
            except Exception:
                pass

        diccionario_productos_bd = {}
        opciones_desplegable = ["-- Seleccione un producto / variante --"]
        
        for prod in inventario_lista:
            p_nombre = prod.get("nombre") or prod.get("titulo") or prod.get("descripcion") or "Producto"
            variantes = prod.get("variantes", [])
            if not variantes:
                variantes = [prod]
                
            for var in variantes:
                sku_v = var.get("SKU") or var.get("sku") or var.get("codigo_sku") or ""
                talla_v = var.get("Talla") or var.get("talla") or "Única"
                color_v = var.get("Color") or var.get("color") or "Único"
                stock_v = var.get("Stock") or var.get("stock_actual") or var.get("stock") or 0
                precio_v = float(var.get("Precio ($)") or var.get("precio") or 0.0)
                descuento_v = float(var.get("descuento_porcentaje") or var.get("oferta") or 0.0)
                
                if sku_v:
                    etiqueta = f"{p_nombre} - Talla: {talla_v} / Color: {color_v} [Stock: {stock_v}] [SKU: {sku_v}]"
                    diccionario_productos_bd[etiqueta] = {
                        "sku": sku_v,
                        "nombre": p_nombre,
                        "talla": talla_v,
                        "color": color_v,
                        "precio": precio_v,
                        "descuento": descuento_v,
                        "stock": stock_v
                    }
                    if etiqueta not in opciones_desplegable:
                        opciones_desplegable.append(etiqueta)

        col_sel1, col_sel2, col_sel3 = st.columns([3, 1, 1])
        with col_sel1:
            prod_seleccionado_etiqueta = st.selectbox(
                "🏷️ Seleccionar Producto para la Venta", 
                options=opciones_desplegable,
                key="select_producto_externo"
            )
        with col_sel2:
            cant_ingresar = st.number_input("Cantidad", min_value=1, value=1, step=1, key="input_cant_externo")
        with col_sel3:
            st.write("&nbsp;")
            btn_agregar = st.button("➕ Añadir Item", type="secondary", use_container_width=True)

        if "lista_items_venta" not in st.session_state:
            st.session_state.lista_items_venta = []

        if btn_agregar:
            if prod_seleccionado_etiqueta == "-- Seleccione un producto / variante --":
                st.warning("⚠️ Selecciona un producto válido de la lista antes de añadir.")
            else:
                info_p = diccionario_productos_bd.get(prod_seleccionado_etiqueta)
                if info_p:
                    existe = False
                    for item in st.session_state.lista_items_venta:
                        if item["SKU"] == info_p["sku"]:
                            item["Cantidad"] += cant_ingresar
                            item["Subtotal ($)"] = round(item["Cantidad"] * info_p["precio"], 2)
                            existe = True
                            break
                    
                    if not existe:
                        st.session_state.lista_items_venta.append({
                            "SKU": info_p["sku"],
                            "Producto": info_p["nombre"],
                            "Talla": info_p["talla"],
                            "Color": info_p["color"],
                            "Cantidad": cant_ingresar,
                            "Precio Unit. ($)": info_p["precio"],
                            "Oferta (%)": info_p["descuento"],
                            "Subtotal ($)": round(cant_ingresar * info_p["precio"], 2)
                        })
                    st.toast(f"✅ ¡{info_p['nombre']} añadido a la lista!", icon="🛍️")

        st.markdown("###### 📋 Lista de Productos Añadidos a la Factura")
        
        if st.session_state.lista_items_venta:
            df_tabla_items = pd.DataFrame(st.session_state.lista_items_venta)
            
            df_editado = st.data_editor(
                df_tabla_items,
                use_container_width=True,
                num_rows="dynamic",
                key="tabla_items_agregados",
                column_config={
                    "SKU": st.column_config.TextColumn("SKU", disabled=True),
                    "Producto": st.column_config.TextColumn("Producto", disabled=True),
                    "Talla": st.column_config.TextColumn("Talla", disabled=True),
                    "Color": st.column_config.TextColumn("Color", disabled=True),
                    "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1),
                    "Precio Unit. ($)": st.column_config.NumberColumn("Precio Unit. ($)", format="$ %.2f", disabled=True),
                    "Oferta (%)": st.column_config.NumberColumn("Oferta (%)", format="%.1f %%", disabled=True),
                    "Subtotal ($)": st.column_config.NumberColumn("Subtotal ($)", format="$ %.2f", disabled=True)
                }
            )
            
            # Sincronización robusta del editor de datos con el estado de la sesión
            if df_editado is not None and not df_editado.empty:
                nueva_lista = []
                for _, row in df_editado.iterrows():
                    cant_f = int(row.get("Cantidad", 1))
                    p_f = float(row.get("Precio Unit. ($)", 0.0))
                    row_dict = row.to_dict()
                    row_dict["Subtotal ($)"] = round(cant_f * p_f, 2)
                    nueva_lista.append(row_dict)
                st.session_state.lista_items_venta = nueva_lista
            
            total_factura = sum(item["Subtotal ($)"] for item in st.session_state.lista_items_venta)
            st.markdown(f"#### 💰 Total Factura: `${total_factura:.2f}`")

            col_limpiar, col_esp = st.columns([2, 8])
            with col_limpiar:
                if st.button("🗑️ Vaciar Lista de Productos", type="secondary"):
                    st.session_state.lista_items_venta = []
                    st.rerun()
        else:
            st.info("👈 Selecciona una prenda en el desplegable superior y haz clic en **'➕ Añadir Item'** para agregar productos a esta factura.")

        st.markdown("---")

        if st.button("🚀 Registrar Venta en el Sistema", type="primary", use_container_width=True):
            if not ruc_cliente or not nombre_cliente:
                st.error("⚠️ Por favor completa los campos obligatorios del cliente (RUC/Cédula y Nombre).")
            elif not st.session_state.lista_items_venta:
                st.error("⚠️ Debes añadir al menos un producto a la lista antes de registrar la venta.")
            else:
                items_payload = []
                for item in st.session_state.lista_items_venta:
                    items_payload.append({
                        "sku": item["SKU"],
                        "cantidad": int(item["Cantidad"]),
                        "precio_unitario": float(item["Precio Unit. ($)"])
                    })

                payload_venta = {
                    "numero_factura": num_factura_auto,
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
                        st.success("✅ ¡Venta registrada exitosamente!")
                        st.session_state.lista_items_venta = []
                        st.rerun()  # Refrescar para limpiar estado y actualizar consecutivos
                    else:
                        err_det = resp.json().get("detail", "Error desconocido")
                        st.error(f"❌ Error al procesar la venta: {err_det}")
                except Exception as ex:
                    st.error(f"❌ Error de conexión con la API: {ex}")

    # --- PESTAÑA 2: HISTORIAL DE VENTAS ---
    with tab_historial:
        st.markdown("##### 📋 Historial de Ventas")
        subtab_generales, subtab_aprobar, subtab_acumulativo = st.tabs([
            "📊 Ventas Generales (Filtro Fecha)", 
            "🔍 Ventas por Aprobar", 
            "💳 Ventas Plan Acumulativo"
        ])
        
        with subtab_generales:
            st.markdown("###### 📅 Filtrar Ventas Generales por Fecha")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                fecha_inicio = st.date_input("Fecha Inicio", value=date(2026, 1, 1), key="f_ini_gen")
            with col_f2:
                fecha_fin = st.date_input("Fecha Fin", value=date.today(), key="f_fin_gen")

            try:
                res_rep = requests.get(f"{API_URL}/ventas/reporte", timeout=5)
                if res_rep.status_code == 200:
                    facturas_data = res_rep.json()
                    if facturas_data:
                        df_ventas = pd.DataFrame(facturas_data)
                        if "fecha" in df_ventas.columns:
                            df_ventas["fecha_dt"] = pd.to_datetime(df_ventas["fecha"]).dt.date
                            df_filtrado = df_ventas[(df_ventas["fecha_dt"] >= fecha_inicio) & (df_ventas["fecha_dt"] <= fecha_fin)]
                            df_filtrado = df_filtrado.drop(columns=["fecha_dt"])
                            st.dataframe(df_filtrado, use_container_width=True)
                        else:
                            st.dataframe(df_ventas, use_container_width=True)
                    else:
                        st.info("No hay ventas registradas todavía.")
                else:
                    st.warning("No se pudo obtener el reporte de ventas del servidor.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

        with subtab_aprobar:
            st.markdown("###### 🔍 Auditoría y Aprobación de Órdenes Web")
            try:
                res_aprob = requests.get(f"{API_URL}/ventas/por-aprobar", timeout=5)
                if res_aprob.status_code == 200:
                    ordenes_pendientes = res_aprob.json()
                    if not ordenes_pendientes:
                        st.success("🎉 ¡Excelente! No hay órdenes web pendientes de aprobación.")
                    else:
                        for orden in ordenes_pendientes:
                            # Protección de ID única para el expander y elementos internos
                            with st.expander(f"Orden #{orden['numero_factura']} - {orden['cliente']} (${orden['total_factura']:.2f}) [POR APROBAR]"):
                                col_info1, col_info2 = st.columns([1, 1])
                                with col_info1:
                                    st.markdown("**👤 Datos del Cliente y Envío**")
                                    st.write(f"**Cédula/RUC:** {orden['ruc_cedula']}")
                                    st.write(f"**Nombre:** {orden['cliente']}")
                                    st.write(f"**Teléfono:** {orden['telefono']}")
                                    st.write(f"**Ciudad / Prov:** {orden['ciudad']} / {orden['provincia']}")
                                    st.write(f"**Dirección:** {orden['direccion_entrega']}")
                                    st.write(f"**Referencia:** {orden['referencia_direccion']}")
                                    
                                    st.markdown("**🛍️ Detalle de Variantes Compradas**")
                                    items_data = []
                                    for it in orden.get('items', []):
                                        p_unit = float(it.get('precio_unitario', 0.0))
                                        cant = int(it.get('cantidad', 1))
                                        subtotal_item = p_unit * cant
                                        items_data.append({
                                            "SKU": it.get('sku', 'N/D'),
                                            "Cantidad": cant,
                                            "Valor U.": f"${p_unit:.2f}",
                                            "Subtotal": f"${subtotal_item:.2f}"
                                        })
                                    if items_data:
                                        st.dataframe(pd.DataFrame(items_data), use_container_width=True, hide_index=True)
                                    else:
                                        st.info("Sin ítems registrados en esta orden.")

                                with col_info2:
                                    st.markdown("**🧾 Comprobante de Pago (Transferencia)**")
                                    comp_url = orden.get('comprobante_url')
                                    if comp_url:
                                        img_src = comp_url if comp_url.startswith("http") else f"{API_URL.replace('/api', '')}/{comp_url.lstrip('/')}"
                                        col_img1, col_img_centro, col_img2 = st.columns([1, 3, 1])
                                        with col_img_centro:
                                            st.image(img_src, caption="Comprobante de Transferencia", width=260)
                                    else:
                                        st.warning("⚠️ Sin imagen adjunta o la ruta no está disponible.")
                                    
                                    st.markdown("---")
                                    # Botón con key segura basada en el ID único de la factura/orden
                                    if st.button(f"✅ Aprobar Pago y Enviar a Bodega", key=f"btn_aprobar_pago_{orden['id']}", type="primary", use_container_width=True):
                                        try:
                                            res_post = requests.post(f"{API_URL}/ventas/{orden['id']}/aprobar-pago", timeout=5)
                                            if res_post.status_code == 200:
                                                st.success(f"¡Orden Nº {orden['numero_factura']} aprobada, enviada a Bodega y correo enviado al cliente!")
                                                st.rerun()
                                            else:
                                                err_msg = res_post.json().get("detail", "Error al aprobar")
                                                st.error(f"❌ {err_msg}")
                                        except Exception as ex:
                                            st.error(f"❌ Error de conexión: {ex}")
                else:
                    st.warning("No se pudieron cargar las órdenes por aprobar.")
            except Exception as e:
                st.error(f"Error de conexión con la API: {e}")

        with subtab_acumulativo:
            st.markdown("###### 💳 Ventas en Modalidad Plan Acumulativo")
            try:
                res_rep = requests.get(f"{API_URL}/ventas/reporte", timeout=5)
                if res_rep.status_code == 200:
                    data = res_rep.json()
                    df_all = pd.DataFrame(data)
                    if not df_all.empty and "es_plan_acumulativo" in df_all.columns:
                        df_acum = df_all[df_all["es_plan_acumulativo"] == True]
                        if not df_acum.empty:
                            st.dataframe(df_acum, use_container_width=True)
                        else:
                            st.info("No hay planes acumulativos registrados.")
                    else:
                        st.info("No hay datos disponibles para planes acumulativos.")
                else:
                    st.warning("No se pudo obtener la información de reporte.")
            except Exception as e:
                st.error(f"Error: {e}")