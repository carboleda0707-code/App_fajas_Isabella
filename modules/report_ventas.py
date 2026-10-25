import streamlit as st
import requests
import os
import io
import pandas as pd
import openpyxl
from datetime import date, datetime

# --- CONEXIÓN DINÁMICA LOCAL / NUBE ---
API_URL = st.session_state.get("API_URL", "http://localhost:8000/api")

def render_reporte_ventas():
    st.markdown("### 📊 Reportes de Ventas y Facturación")
    st.markdown("---")
    
    # Filtros de visualización superior
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        tipo_vista = st.selectbox("Tipo de Vista", ["General (Detallado)", "Consolidado por Agrupación"])
    with col_f2:
        fecha_inicio = st.date_input("Desde", value=date(date.today().year, date.today().month, 1), key="ini_v")
    with col_f3:
        fecha_fin = st.date_input("Hasta", value=date.today(), key="fin_v")
    with col_f4:
        ordenar_por = st.selectbox(
            "Ordenar por:",
            ["Fecha", "Cliente", "Ciudad", "Nº Factura", "Total Factura ($)"],
            key="ord_ventas"
        )
        
    # Selector de criterio de agrupación si está en vista consolidada
    criterio_agrupacion = "Cliente"
    if tipo_vista == "Consolidado por Agrupación":
        col_ag1, col_ag2 = st.columns([2, 2])
        with col_ag1:
            criterio_agrupacion = st.selectbox("Agrupar por:", ["Cliente", "Ciudad", "Estado de Despacho", "Ítems / Producto (SKU)"])
        st.markdown("---")
        
    st.markdown("---")
    
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
                    try:
                        f_date = datetime.strptime(str(f_str)[:10], "%Y-%m-%d").date()
                        if fecha_inicio <= f_date <= fecha_fin:
                            ventas_filtradas.append(v)
                    except Exception:
                        pass
                        
            if not ventas_filtradas:
                st.warning("⚠️ No se encontraron ventas en el rango de fechas seleccionado.")
                return

            # Preparación de estructuras para visualización y exportación
            tabla_general = []
            agrupado_sku = {}
            diccionario_grupos = {}

            if tipo_vista == "General (Detallado)":
                for v in ventas_filtradas:
                    num_fac = str(v.get("numero_factura"))
                    
                    # Buscar ítems correspondientes a esta orden/factura
                    items_v = v.get("items") or v.get("detalles") or v.get("productos") or []
                    if not items_v:
                        for m in movimientos:
                            ref_f = str(m.get('referencia_factura', '')).strip()
                            num_m = str(m.get('numero_factura', '')).strip()
                            if num_fac in ref_f or num_fac in num_m or (ref_f and ref_f.lstrip('0') == num_fac.lstrip('0')):
                                items_v.append(m)

                    if items_v:
                        for it in items_v:
                            sku = it.get("sku") or it.get("sku_producto") or it.get("codigo_producto") or it.get("SKU") or "N/A"
                            cant = abs(int(it.get("cantidad", it.get("cant", 1))))
                            if cant == 0:
                                cant = 1
                            
                            val_neto_reg = float(it.get("valor_neto", 0.0))
                            if val_neto_reg > 0:
                                subtotal = val_neto_reg
                                prec = subtotal / cant
                            else:
                                prec = float(it.get("precio_unitario") or it.get("precio") or it.get("precio_venta") or 0.0)
                                subtotal = cant * prec

                            prod_desc = info_productos.get(sku, f"SKU: {sku}")

                            tabla_general.append({
                                "Nº Factura": num_fac,
                                "Fecha": str(v.get("fecha_factura"))[:10],
                                "Cliente": v.get("entidad_nombre"),
                                "RUC/CI": v.get("entidad_ruc"),
                                "SKU / Producto": prod_desc,
                                "Cantidad": cant,
                                "Precio Unit. ($)": prec,
                                "Subtotal ($)": subtotal,
                                "Provincia": v.get("provincia") or "N/D",
                                "Ciudad": v.get("ciudad") or "N/D",
                                "Courier": v.get("courier_nombre") or "Servientrega",
                                "Estado": v.get("estado_despacho") or "PENDIENTE",
                                "Total Factura ($)": float(v.get('total_factura', 0))
                            })
                    else:
                        # Si no hay ítems detallados registrados, se muestra la fila general de la factura
                        monto_tot = float(v.get('total_factura', 0))
                        tabla_general.append({
                            "Nº Factura": num_fac,
                            "Fecha": str(v.get("fecha_factura"))[:10],
                            "Cliente": v.get("entidad_nombre"),
                            "RUC/CI": v.get("entidad_ruc"),
                            "SKU / Producto": "Sin detalle de ítems",
                            "Cantidad": 1,
                            "Precio Unit. ($)": monto_tot,
                            "Subtotal ($)": monto_tot,
                            "Provincia": v.get("provincia") or "N/D",
                            "Ciudad": v.get("ciudad") or "N/D",
                            "Courier": v.get("courier_nombre") or "Servientrega",
                            "Estado": v.get("estado_despacho") or "PENDIENTE",
                            "Total Factura ($)": monto_tot
                        })

                df_general = pd.DataFrame(tabla_general)
                if not df_general.empty and ordenar_por in df_general.columns:
                    df_general = df_general.sort_values(by=ordenar_por, ascending=True).reset_index(drop=True)
            else:
                if criterio_agrupacion == "Ítems / Producto (SKU)":
                    facturas_con_sku = set()
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
                                facturas_con_sku.add(num_fact)
                                if sku not in agrupado_sku:
                                    agrupado_sku[sku] = []
                                agrupado_sku[sku].append({
                                    "fecha": fecha_dia,
                                    "num_factura": num_fact,
                                    "cantidad": cant,
                                    "precio": precio
                                })

                    for v in ventas_filtradas:
                        num_fac = str(v.get("numero_factura"))
                        if num_fac not in facturas_con_sku:
                            sku_gen = "SIN-SKU (Importada/Directa)"
                            if sku_gen not in agrupado_sku:
                                agrupado_sku[sku_gen] = []
                            agrupado_sku[sku_gen].append({
                                "fecha": str(v.get("fecha_factura"))[:10],
                                "num_factura": num_fac,
                                "cantidad": 1,
                                "precio": float(v.get("total_factura", 0.0))
                            })
                else:
                    key_map = {
                        "Cliente": "entidad_nombre",
                        "Ciudad": "ciudad",
                        "Estado de Despacho": "estado_despacho"
                    }
                    campo_agrupacion = key_map.get(criterio_agrupacion, "entidad_nombre")
                    for v in ventas_filtradas:
                        val_grupo = str(v.get(campo_agrupacion) or "No Definido").strip().title()
                        if val_grupo not in diccionario_grupos:
                            diccionario_grupos[val_grupo] = []
                        diccionario_grupos[val_grupo].append(v)

            # --- GENERACIÓN DEL ARCHIVO EXCEL EN MEMORIA CON AUTO-FIT ---
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                if tipo_vista == "General (Detallado)":
                    df_general.to_excel(writer, index=False, sheet_name="Ventas Detalladas")
                else:
                    if criterio_agrupacion == "Ítems / Producto (SKU)":
                        filas_sku = []
                        for sku, regs in sorted(agrupado_sku.items()):
                            for r in regs:
                                filas_sku.append({
                                    "SKU": sku,
                                    "Fecha": r['fecha'],
                                    "Nº Factura": r['num_factura'],
                                    "Cantidad": r['cantidad'],
                                    "Precio Unitario ($)": r['precio'],
                                    "Subtotal ($)": r['cantidad'] * r['precio']
                                })
                        pd.DataFrame(filas_sku).to_excel(writer, index=False, sheet_name="Consolidado SKU")
                    else:
                        filas_grupos = []
                        for grupo, lista_vals in sorted(diccionario_grupos.items()):
                            for v in sorted(lista_vals, key=lambda x: str(x.get(key_map.get(criterio_agrupacion, 'entidad_nombre')))):
                                filas_grupos.append({
                                    f"Agrupado por {criterio_agrupacion}": grupo,
                                    "Nº Factura": v.get("numero_factura"),
                                    "Fecha": str(v.get("fecha_factura"))[:10],
                                    "Cliente": v.get("entidad_nombre"),
                                    "Ciudad": v.get("ciudad") or "N/D",
                                    "Estado": v.get("estado_despacho") or "PENDIENTE",
                                    "Total ($)": float(v.get("total_factura", 0))
                                })
                        pd.DataFrame(filas_grupos).to_excel(writer, index=False, sheet_name=f"Consolidado {criterio_agrupacion}")

                # Autoajustar ancho de columnas al contenido del texto para todas las hojas
                for sheetname in writer.sheets:
                    worksheet = writer.sheets[sheetname]
                    for col in worksheet.columns:
                        max_len = 0
                        col_letter = col[0].column_letter
                        for cell in col:
                            val = str(cell.value or '')
                            if len(val) > max_len:
                                max_len = len(val)
                        worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

            buffer.seek(0)

            # Botón de Descarga Nativo
            st.download_button(
                label="📥 Descargar Excel de Ventas (Tal cual ordenado)",
                data=buffer,
                file_name=f"Reporte_Ventas_orden_{ordenar_por.replace(' ', '_')}_{fecha_inicio}_al_{fecha_fin}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.markdown("---")

            # --- RENDERIZADO VISUAL EN PANTALLA ---
            if tipo_vista == "General (Detallado)":
                st.markdown("#### 📋 Listado Detallado de Facturas e Ítems de Venta")
                df_view = df_general.copy()
                for col_moneda in ["Precio Unit. ($)", "Subtotal ($)", "Total Factura ($)"]:
                    if col_moneda in df_view.columns:
                        df_view[col_moneda] = df_view[col_moneda].apply(lambda x: f"${x:,.2f}")
                st.dataframe(df_view, use_container_width=True, hide_index=True)
            else:
                if criterio_agrupacion == "Ítems / Producto (SKU)":
                    st.markdown("#### 📦 Reporte Consolidado Organizado por Ítems / Productos")
                    st.markdown("---")

                    total_general_unidades = 0
                    total_general_recaudado = 0.0

                    for sku, registros in sorted(agrupado_sku.items()):
                        nombre_prod = info_productos.get(sku, f"Producto SKU: {sku}" if sku != "SIN-SKU (Importada/Directa)" else "Facturas Registradas Directamente sin Detalle de SKU")
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
                                📊 Subtotal {sku} ➔ Unidades / Registros: {subtotal_cant} &nbsp;|&nbsp; Total Recaudado: ${subtotal_dinero:,.2f}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    st.markdown("---")
                    m1, m2 = st.columns(2)
                    m1.metric("📦 Unidades / Registros Totales", total_general_unidades)
                    m2.metric("💰 Ingresos Globales Consolidados", f"${total_general_recaudado:,.2f}")

                else:
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
            st.error("Error al conectar con el servidor para obtener las facturas.")
    except Exception as e:
        st.error(f"Error al generar el reporte: {e}")