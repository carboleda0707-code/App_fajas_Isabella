import streamlit as st
import requests
import os
import pandas as pd
import io
from datetime import date, datetime

# Conexión estricta de Producción en Nube
API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

def generar_excel_contifico(data_facturas):
    """
    Transforma las facturas y sus ítems al formato plano por ítem 
    requerido por la plantilla de importación masiva de Contifico.
    """
    filas_contifico = []
    
    for f in data_facturas:
        num_fact = f.get("numero_factura", "001-001-000000000")
        fecha = f.get("fecha", f.get("fecha_factura", ""))
        ruc = f.get("ruc_cedula", f.get("entidad_ruc", "9999999999001"))
        cliente = f.get("cliente", f.get("entidad_nombre", "Consumidor Final"))
        forma_pago = f.get("metodo_pago", "Efectivo")
        
        # Determinar tipo de identificación para Contifico
        # 04 = RUC, 05 = Cédula, 07 = Consumidor Final
        tipo_id = "05"
        if len(str(ruc)) == 13:
            tipo_id = "04"
        elif str(ruc) == "9999999999001":
            tipo_id = "07"

        items = f.get("items", [])
        if not items:
            filas_contifico.append({
                "Tipo Identificación": tipo_id,
                "Identificación": ruc,
                "Razón Social": cliente,
                "Fecha": fecha,
                "Número Factura": num_fact,
                "Código Producto": "FAJA-GEN",
                "Cantidad": 1,
                "Precio Unitario": float(f.get("total_norm", f.get("total", 0.0))),
                "Forma de Pago": forma_pago
            })
        else:
            for it in items:
                sku = it.get("sku", it.get("sku_producto", "SKU-001"))
                cant = int(it.get("cantidad", 1))
                precio = float(it.get("precio_unitario", it.get("precio", 0.0)))
                
                filas_contifico.append({
                    "Tipo Identificación": tipo_id,
                    "Identificación": ruc,
                    "Razón Social": cliente,
                    "Fecha": fecha,
                    "Número Factura": num_fact,
                    "Código Producto": sku,
                    "Cantidad": cant,
                    "Precio Unitario": precio,
                    "Forma de Pago": forma_pago
                })

    df_contifico = pd.DataFrame(filas_contifico)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_contifico.to_excel(writer, index=False, sheet_name='Importacion_Contifico')
    return output.getvalue()


def render_ventas():
    st.markdown("<p style='color: black; font-weight: bold;'>💳 Ventas y Facturación</p>", unsafe_allow_html=True)        
    accion = st.radio("Acción: ", ["Registrar Nueva Venta", "Consultar Facturas Emitidas"], horizontal=True)
    
    if accion == "Consultar Facturas Emitidas":
        col_btn1, col_btn2 = st.columns([0.15, 0.85])
        with col_btn1:
            if st.button("🔄 Actualizar"):
                st.rerun()
                
        st.subheader("📋 Consulta y Control General de Facturas Emitidas")
        
        try:
            res = requests.get(f"{API_URL}/despachos/reporte", timeout=3)
            if res.status_code != 200:
                res = requests.get(f"{API_URL}/facturas", timeout=3)
                
            if res.status_code == 200:
                facturas_data = res.json()
                if not facturas_data:
                    st.info("No hay facturas de venta registradas en el sistema.")
                    return
                
                if isinstance(facturas_data, list) and len(facturas_data) > 0 and "tipo_factura" in facturas_data[0]:
                    facturas_data = [f for f in facturas_data if f.get('tipo_factura') == 'VENTA']

                df_raw = pd.DataFrame(facturas_data)
                
                col_total_key = "total" if "total" in df_raw.columns else ("total_factura" if "total_factura" in df_raw.columns else None)
                df_raw["total_norm"] = pd.to_numeric(df_raw[col_total_key], errors="coerce").fillna(0.0) if col_total_key else 0.0
                
                # --- SECCIÓN DE FILTROS Y BÚSQUEDA ---
                st.markdown("##### 🔍 Filtros de Búsqueda y Rango")
                col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.5, 1.5, 1.5])
                
                with col_f1:
                    busqueda = st.text_input("Buscador Rápido:", placeholder="Buscar por Nº Factura, Cliente o RUC...").strip()
                
                with col_f2:
                    f_estado = st.selectbox(
                        "Estado Despacho:",
                        ["TODOS", "PENDIENTE", "EMPACADO", "EN TRÁNSITO", "ENTREGADO"]
                    )
                
                with col_f3:
                    fecha_inicio = st.date_input("Fecha Desde:", value=date(2026, 1, 1))
                
                with col_f4:
                    fecha_fin = st.date_input("Fecha Hasta:", value=date.today())
                    
                st.markdown("")

                # --- APLICAR FILTROS ---
                df_filtrado = df_raw.copy()

                if busqueda:
                    mask = (
                        df_filtrado.get("numero_factura", "").astype(str).str.contains(busqueda, case=False, na=False) |
                        df_filtrado.get("cliente", df_filtrado.get("entidad_nombre", "")).astype(str).str.contains(busqueda, case=False, na=False) |
                        df_filtrado.get("ruc_cedula", df_filtrado.get("entidad_ruc", "")).astype(str).str.contains(busqueda, case=False, na=False)
                    )
                    df_filtrado = df_filtrado[mask]

                if f_estado != "TODOS":
                    col_estado = "estado_despacho" if "estado_despacho" in df_filtrado.columns else "estado"
                    if col_estado in df_filtrado.columns:
                        df_filtrado = df_filtrado[df_filtrado[col_estado].astype(str).str.upper() == f_estado]

                col_fecha_name = "fecha" if "fecha" in df_filtrado.columns else ("fecha_factura" if "fecha_factura" in df_filtrado.columns else None)
                if col_fecha_name:
                    df_filtrado["fecha_dt"] = pd.to_datetime(df_filtrado[col_fecha_name], errors="coerce").dt.date
                    df_filtrado = df_filtrado[(df_filtrado["fecha_dt"] >= fecha_inicio) & (df_filtrado["fecha_dt"] <= fecha_fin)]

                # --- TARJETAS DE MÉTRICAS (KPIs) ---
                total_monto = df_filtrado["total_norm"].sum()
                cant_facturas = len(df_filtrado)
                
                col_est_estado = "estado_despacho" if "estado_despacho" in df_filtrado.columns else "estado"
                pendientes = len(df_filtrado[df_filtrado[col_est_estado].astype(str).str.upper() == "PENDIENTE"]) if col_est_estado in df_filtrado.columns else 0

                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric("💰 Total Ventas ($)", f"${total_monto:,.2f}")
                kpi2.metric("📄 Facturas Encontradas", f"{cant_facturas}")
                kpi3.metric("⏳ Pendientes de Entrega", f"{pendientes}")

                st.markdown("---")

                # --- BOTONES DE EXPORTACIÓN (EXCEL GENERAL Y CONTIFICO) ---
                col_exp1, col_exp2 = st.columns(2)
                with col_exp1:
                    try:
                        output_gen = io.BytesIO()
                        with pd.ExcelWriter(output_gen, engine='openpyxl') as writer:
                            df_filtrado.to_excel(writer, index=False, sheet_name='Ventas')
                        st.download_button(
                            label="📥 Descargar Listado General (Excel)",
                            data=output_gen.getvalue(),
                            file_name="Listado_General_Ventas.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except Exception:
                        pass

                with col_exp2:
                    try:
                        # Convertir dataframe filtrado a dict para armar formato contifico
                        lista_dict_filtrada = df_filtrado.to_dict(orient="records")
                        excel_contifico_bytes = generar_excel_contifico(lista_dict_filtrada)
                        st.download_button(
                            label="📤 Descargar Formato Masivo para Contifico",
                            data=excel_contifico_bytes,
                            file_name="Importacion_Contifico_Ventas.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    except Exception as ex:
                        st.caption(f"⚠️ Error generando formato Contifico: {ex}")

                st.markdown("")

                # --- TABLA RESUMEN COMPACTA DE FACTURAS ---
                data_tabla = []
                for _, r in df_filtrado.iterrows():
                    data_tabla.append({
                        "Nº Factura": r.get("numero_factura", "N/A"),
                        "Fecha": r.get("fecha", r.get("fecha_factura", "N/A")),
                        "RUC / Cédula": r.get("ruc_cedula", r.get("entidad_ruc", "N/A")),
                        "Cliente": r.get("cliente", r.get("entidad_nombre", "Consumidor Final")),
                        "Total ($)": f"${r.get('total_norm', 0.0):,.2f}",
                        "Ciudad": r.get("ciudad", "N/A"),
                        "Courier": r.get("courier", r.get("courier_nombre", "Servientrega")),
                        "Nº Guía": r.get("numero_guia", "SIN GUÍA"),
                        "Estado Despacho": r.get("estado_despacho", "PENDIENTE")
                    })

                df_pantalla = pd.DataFrame(data_tabla)
                st.dataframe(df_pantalla, use_container_width=True, hide_index=True)

                # --- DETALLE INDIVIDUAL DE FACTURA ---
                st.divider()
                st.markdown("#### 🔎 Inspeccionar Detalle de Factura / Orden")
                
                lista_facturas = df_filtrado["numero_factura"].dropna().unique().tolist() if "numero_factura" in df_filtrado.columns else []
                if lista_facturas:
                    factura_sel = st.selectbox("Seleccione una Factura para ver su información detallada:", lista_facturas)
                    
                    fact_info = df_filtrado[df_filtrado["numero_factura"] == factura_sel].iloc[0]
                    monto_factura_tot = float(fact_info.get("total_norm", 0.0))
                    
                    with st.expander(f"📦 Ver información completa y productos de la Factura Nº {factura_sel}", expanded=True):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.write(f"**Cliente:** {fact_info.get('cliente', fact_info.get('entidad_nombre', 'N/A'))}")
                            st.write(f"**RUC/Cédula:** {fact_info.get('ruc_cedula', fact_info.get('entidad_ruc', 'N/A'))}")
                            st.write(f"**Fecha:** {fact_info.get('fecha', fact_info.get('fecha_factura', 'N/A'))}")
                        with c2:
                            st.write(f"**Provincia / Ciudad:** {fact_info.get('provincia', 'Guayas')} / {fact_info.get('ciudad', 'Guayaquil')}")
                            st.write(f"**Dirección:** {fact_info.get('direccion', fact_info.get('direccion_entrega', 'N/A'))}")
                            st.write(f"**Referencia:** {fact_info.get('referencia', fact_info.get('referencia_direccion', 'Sin referencia'))}")
                        with c3:
                            st.write(f"**Courier:** {fact_info.get('courier', fact_info.get('courier_nombre', 'Servientrega'))}")
                            st.write(f"**Nº Guía:** {fact_info.get('numero_guia', 'SIN GUÍA')}")
                            st.write(f"**Estado Despacho:** `{fact_info.get('estado_despacho', 'PENDIENTE')}`")

                        st.markdown("---")
                        st.markdown("##### 🛍️ Detalle de Ítems / Fajas Vendidas")

                        items_factura = fact_info.get("items", [])
                        num_fact_str = str(factura_sel).strip()

                        if not items_factura:
                            try:
                                res_mov = requests.get(f"{API_URL}/movimientos", timeout=3)
                                if res_mov.status_code == 200:
                                    movs = res_mov.json()
                                    for m in movs:
                                        ref_f = str(m.get('referencia_factura', '')).strip()
                                        num_m = str(m.get('numero_factura', '')).strip()
                                        if num_fact_str in ref_f or num_fact_str in num_m or (ref_f and ref_f.lstrip('0') == num_fact_str.lstrip('0')):
                                            items_factura.append(m)
                            except Exception:
                                items_factura = []

                        if items_factura:
                            tabla_items = []
                            for idx, it in enumerate(items_factura, 1):
                                sku = it.get("sku", it.get("sku_producto", it.get("codigo_producto", "N/A")))
                                cant = abs(int(it.get("cantidad", it.get("cant", 1))))
                                
                                prec_bruto = (
                                    it.get("precio_unitario") or 
                                    it.get("precio") or 
                                    it.get("precio_venta") or 
                                    it.get("costo_unitario") or 
                                    0.0
                                )
                                prec = float(prec_bruto)
                                
                                if prec == 0.0 and monto_factura_tot > 0 and len(items_factura) > 0:
                                    prec = monto_factura_tot / len(items_factura) / cant
                                
                                subtotal = cant * prec
                                
                                tabla_items.append({
                                    "Item #": idx,
                                    "SKU": sku,
                                    "Cantidad": cant,
                                    "Precio Unit. ($)": f"${prec:,.2f}",
                                    "Subtotal ($)": f"${subtotal:,.2f}"
                                })
                            
                            st.dataframe(pd.DataFrame(tabla_items), use_container_width=True, hide_index=True)
                        else:
                            st.info(f"⚠️ No se encontraron ítems desglosados en el Kardex para la Factura Nº {factura_sel}.")
            else:
                st.error("No se pudo obtener el historial de ventas desde el servidor.")
        except Exception as e:
            st.error(f"Error al conectar con el servidor: {e}")
            
    elif accion == "Registrar Nueva Venta":
        # ... (Tu lógica existente para registro de ventas se mantiene intacta)
        pass