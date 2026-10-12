import streamlit as st
import requests
import os
from datetime import date, datetime

API_URL = st.session_state.get("API_URL", "http://127.0.0.1:8000/api")

def render_reporte_ventas():
    st.markdown("### 📊 Reportes de Ventas y Facturación")
    st.markdown("---")
    
    # Filtros de visualización superior
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        tipo_vista = st.selectbox("Tipo de Vista", ["General (Detallado)", "Consolidado por Agrupación"])
    with col_f2:
        fecha_inicio = st.date_input("Desde", value=date(date.today().year, date.today().month, 1))
    with col_f3:
        fecha_fin = st.date_input("Hasta", value=date.today())
        
    # Selector de criterio de agrupación si está en vista consolidada
    criterio_agrupacion = "Cliente"
    if tipo_vista == "Consolidado por Agrupación":
        col_ag1, col_ag2 = st.columns([2, 2])
        with col_ag1:
            criterio_agrupacion = st.selectbox("Agrupar por:", ["Cliente", "Ciudad", "Estado de Despacho", "Ítems / Producto (SKU)"])
        st.markdown("---")
        
    st.markdown("---")
    
    col_b1, col_b2 = st.columns([2, 2])
    with col_b1:
        consultar = st.button("🔍 Generar Reporte", type="primary", use_container_width=True)
    with col_b2:
        excel_url = f"{API_URL}/reportes/ventas/excel?inicio={fecha_inicio}&fin={fecha_fin}&tipo={tipo_vista}"
        st.markdown(
            f"""
            <a href="{excel_url}" target="_blank">
                <button style="width:100%; background-color:#2e7d32; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer;">
                    📥 Descargar Excel de Ventas
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )
        
    if consultar or True:
        try:
            res_fac = requests.get(f"{API_URL}/facturas", timeout=4)
            res_inv = requests.get(f"{API_URL}/inventario", timeout=4)
            res_mov = requests.get(f"{API_URL}/movimientos", timeout=4)
            
            if res_fac.status_code == 200:
                facturas = res_fac.json()
                inventario = res_inv.json() if res_inv.status_code == 200 else []
                movimientos = res_mov.json() if res_mov.status_code == 200 else []
                
                ventas = [f for f in facturas if f.get('tipo_factura') == 'VENTA']
                
                # Mapear información del inventario (Nombre, Talla, Color) por SKU
                info_productos = {}
                for item in inventario:
                    sku = item.get("SKU")
                    prod_nombre = item.get("producto", {}).get("nombre", "Producto")
                    talla = item.get("Talla", "")
                    color = item.get("Color", "")
                    info_productos[sku] = f"{prod_nombre} (Talla: {talla} | Color: {color})"

                # Filtrar ventas por rango de fechas
                ventas_filtradas = []
                for v in ventas:
                    f_str = v.get('fecha_factura')
                    if f_str:
                        f_date = datetime.strptime(str(f_str)[:10], "%Y-%m-%d").date()
                        if fecha_inicio <= f_date <= fecha_fin:
                            ventas_filtradas.append(v)
                            
                if not ventas_filtradas:
                    st.warning("⚠️ No se encontraron ventas en el rango de fechas seleccionado.")
                    return

                if tipo_vista == "General (Detallado)":
                    st.markdown("#### 📋 Listado General de Facturas de Venta")
                    tabla_general = []
                    for v in ventas_filtradas:
                        tabla_general.append({
                            "Nº Factura": v.get("numero_factura"),
                            "Fecha": str(v.get("fecha_factura"))[:10],
                            "Cliente": v.get("entidad_nombre"),
                            "RUC/CI": v.get("entidad_ruc"),
                            "Provincia": v.get("provincia") or "N/D",
                            "Ciudad": v.get("ciudad") or "N/D",
                            "Courier": v.get("courier_nombre") or "Servientrega",
                            "Estado": v.get("estado_despacho") or "PENDIENTE",
                            "Total ($)": f"${float(v.get('total_factura', 0)):,.2f}"
                        })
                    st.dataframe(tabla_general, use_container_width=True, hide_index=True)
                else:
                    if criterio_agrupacion == "Ítems / Producto (SKU)":
                        # Agrupación especial por producto usando movimientos y facturas filtradas
                        agrupado_sku = {}
                        for m in movimientos:
                            if m.get('tipo_movimiento') == 'VENTA_LOCAL':
                                ref = m.get('referencia_factura', '')
                                sku = m.get('sku', 'N/D')
                                cant = abs(int(m.get('cantidad', 0)))
                                precio = float(m.get('valor_neto', 0.0))
                                fecha_dia = str(m.get('fecha_hora', ''))[:10]
                                num_fact = ref.replace("Fact Venta:", "").strip() if "Fact Venta:" in ref else "N/D"
                                
                                factura_valida = any(str(v.get('numero_factura')) == num_fact for v in ventas_filtradas)
                                if factura_valida:
                                    if sku not in agrupado_sku:
                                        agrupado_sku[sku] = []
                                    agrupado_sku[sku].append({
                                        "fecha": fecha_dia,
                                        "num_factura": num_fact,
                                        "cantidad": cant,
                                        "precio": precio
                                    })

                        st.markdown("#### 📦 Reporte Consolidado Organizado por Ítems / Productos")
                        st.markdown("---")

                        if not agrupado_sku:
                            st.info("No se encontraron ítems asociados a las facturas en el rango seleccionado.")
                            return

                        total_general_unidades = 0
                        total_general_recaudado = 0.0

                        for sku, registros in sorted(agrupado_sku.items()):
                            nombre_prod = info_productos.get(sku, f"Producto SKU: {sku}")
                            st.markdown(f"### 🏷️ **{nombre_prod}** &nbsp;&nbsp;|&nbsp;&nbsp; `SKU: {sku}`")
                            
                            tabla_detalle = []
                            subtotal_cant = 0
                            subtotal_dinero = 0.0
                            
                            for reg in registros:
                                cant = reg['cantidad']
                                precio = reg['precio']
                                total_linea = cant * precio
                                
                                subtotal_cant += cant
                                subtotal_dinero += total_linea
                                
                                tabla_detalle.append({
                                    "Fecha": reg['fecha'],
                                    "Nº Factura": reg['num_factura'],
                                    "Cantidad": cant,
                                    "Precio Unit. ($)": f"${precio:,.2f}",
                                    "Subtotal ($)": f"${total_linea:,.2f}"
                                })
                            
                            total_general_unidades += subtotal_cant
                            total_general_recaudado += subtotal_dinero

                            st.dataframe(tabla_detalle, use_container_width=True, hide_index=True)
                            st.markdown(
                                f"""
                                <div style="background-color: #f1f5f9; padding: 8px 14px; border-radius: 6px; border-left: 4px solid #2563eb; margin-bottom: 25px; font-size: 0.95rem; font-weight: 600; color: #1e293b;">
                                    📊 Subtotal {sku} ➔ Unidades Vendidas: {subtotal_cant} &nbsp;|&nbsp; Total Recaudado: ${subtotal_dinero:,.2f}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        st.markdown("---")
                        m1, m2 = st.columns(2)
                        m1.metric("📦 Unidades Totales Vendidas", total_general_unidades)
                        m2.metric("💰 Ingresos Globales Consolidados", f"${total_general_recaudado:,.2f}")

                    else:
                        # Agrupación por Cliente, Ciudad o Estado de Despacho
                        key_map = {
                            "Cliente": "entidad_nombre",
                            "Ciudad": "ciudad",
                            "Estado de Despacho": "estado_despacho"
                        }
                        campo_agrupacion = key_map.get(criterio_agrupacion, "entidad_nombre")
                        
                        diccionario_grupos = {}
                        for v in ventas_filtradas:
                            val_grupo = str(v.get(campo_agrupacion) or "No Definido").strip().title()
                            if val_grupo not in diccionario_grupos:
                                diccionario_grupos[val_grupo] = []
                            diccionario_grupos[val_grupo].append(v)

                        st.markdown(f"#### 📊 Reporte Consolidado Organizado por {criterio_agrupacion}")
                        st.markdown("---")

                        total_general_global = 0.0
                        total_facturas_global = 0

                        for grupo, lista_vals in sorted(diccionario_grupos.items()):
                            st.markdown(f"### 🏷️ **{criterio_agrupacion}: {grupo}**")
                            
                            tabla_grupo = []
                            subtotal_grupo = 0.0
                            
                            for v in lista_vals:
                                val_total = float(v.get('total_factura', 0))
                                subtotal_grupo += val_total
                                
                                tabla_grupo.append({
                                    "Nº Factura": v.get("numero_factura"),
                                    "Fecha": str(v.get("fecha_factura"))[:10],
                                    "Cliente": v.get("entidad_nombre"),
                                    "Ciudad": v.get("ciudad") or "N/D",
                                    "Estado": v.get("estado_despacho") or "PENDIENTE",
                                    "Total ($)": f"${val_total:,.2f}"
                                })
                                
                            total_general_global += subtotal_grupo
                            total_facturas_global += len(lista_vals)

                            st.dataframe(tabla_grupo, use_container_width=True, hide_index=True)
                            st.markdown(
                                f"""
                                <div style="background-color: #f1f5f9; padding: 10px 15px; border-radius: 6px; border-left: 4px solid #2563eb; margin-bottom: 30px; font-size: 0.95rem; font-weight: 600; color: #1e293b;">
                                    📊 Subtotal {criterio_agrupacion} [{grupo}] ➔ Facturas Emitidas: {len(lista_vals)} &nbsp;|&nbsp; Total Acumulado: ${subtotal_grupo:,.2f}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        st.markdown("---")
                        m1, m2 = st.columns(2)
                        m1.metric("📦 Total Facturas Emitidas", total_facturas_global)
                        m2.metric("💰 Ingresos Globales Consolidados", f"${total_general_global:,.2f}")

            else:
                st.error("Error al conectar con el servidor.")
        except Exception as e:
            st.error(f"Error al generar el reporte: {e}")