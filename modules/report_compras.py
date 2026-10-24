import streamlit as st
import requests
import os
import io
import pandas as pd
import openpyxl
from datetime import date, datetime

# --- CONEXIÓN DINÁMICA LOCAL / NUBE ---
API_URL = st.session_state.get("API_URL", "http://localhost:8000/api")

def render_reporte_compras():
    st.markdown("### 🛒 Reportes de Compras a Proveedores")
    st.markdown("---")
    
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        tipo_vista = st.selectbox("Tipo de Vista", ["General (Detallado)", "Consolidado (Resumen)"], key="vista_comp")
    with col_f2:
        fecha_inicio = st.date_input("Desde", value=date(date.today().year, date.today().month, 1), key="ini_comp")
    with col_f3:
        fecha_fin = st.date_input("Hasta", value=date.today(), key="fin_comp")
    with col_f4:
        ordenar_por = st.selectbox(
            "Ordenar por:",
            ["Fecha", "Proveedor", "Nº Factura", "Total ($)"],
            key="ord_comp"
        )
        
    st.markdown("---")
    
    try:
        res = requests.get(f"{API_URL}/facturas", timeout=5)
        if res.status_code == 200:
            facturas = res.json()
            compras = [f for f in facturas if f.get('tipo_factura') == 'COMPRA']
            
            if not compras:
                st.info("No hay registros de compras a proveedores en el sistema.")
                return
                
            compras_filtradas = []
            for c in compras:
                f_str = c.get('fecha_factura')
                if f_str:
                    try:
                        f_date = datetime.strptime(str(f_str)[:10], "%Y-%m-%d").date()
                        if fecha_inicio <= f_date <= fecha_fin:
                            compras_filtradas.append(c)
                    except Exception:
                        compras_filtradas.append(c)
                        
            if not compras_filtradas:
                st.warning("⚠️ No se encontraron compras en el rango de fechas seleccionado.")
                return

            # Preparación de datos para visualización y exportación
            tabla_compras = []
            for c in compras_filtradas:
                tabla_compras.append({
                    "Nº Factura": c.get("numero_factura"),
                    "Fecha": str(c.get("fecha_factura"))[:10],
                    "Proveedor": c.get("entidad_nombre"),
                    "RUC Proveedor": c.get("entidad_ruc"),
                    "Total ($)": float(c.get('total_factura', 0))
                })

            df_compras = pd.DataFrame(tabla_compras)

            # Aplicar ordenamiento explícito
            if not df_compras.empty and ordenar_por in df_compras.columns:
                df_compras = df_compras.sort_values(by=ordenar_por, ascending=True).reset_index(drop=True)

            # --- GENERACIÓN DEL ARCHIVO EXCEL EN MEMORIA CON AUTO-FIT Y ORDEN EXACTO ---
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                sheet_name_str = "Compras Detalladas" if tipo_vista == "General (Detallado)" else "Compras Resumen"
                df_compras.to_excel(writer, index=False, sheet_name=sheet_name_str)
                
                # Autoajustar ancho de columnas según la longitud del texto
                worksheet = writer.sheets[sheet_name_str]
                for col in worksheet.columns:
                    max_len = 0
                    col_letter = col[0].column_letter
                    for cell in col:
                        val = str(cell.value or '')
                        if len(val) > max_len:
                            max_len = len(val)
                    worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

            buffer.seek(0)

            # Botón de Descarga de Excel Nativo
            st.download_button(
                label="📥 Descargar Excel de Compras (Tal cual ordenado)",
                data=buffer,
                file_name=f"Reporte_Compras_{tipo_vista[:7]}_orden_{ordenar_por.replace(' ', '_')}_{fecha_inicio}_al_{fecha_fin}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_dl_compras",
                use_container_width=True
            )
            st.markdown("---")

            if tipo_vista == "General (Detallado)":
                st.markdown("#### 📋 Listado General de Compras a Proveedores")
                df_view = df_compras.copy()
                if "Total ($)" in df_view.columns:
                    df_view["Total ($)"] = df_view["Total ($)"].apply(lambda x: f"${x:,.2f}")
                st.dataframe(df_view, use_container_width=True, hide_index=True)
            else:
                st.markdown("#### 📊 Vista Consolidada de Inversión en Compras")
                total_inversion = sum(float(c.get('total_factura', 0)) for c in compras_filtradas)
                total_ordenes = len(compras_filtradas)
                
                m1, m2 = st.columns(2)
                m1.metric("💸 Inversión Total en Compras", f"${total_inversion:,.2f}")
                m2.metric("📄 Órdenes de Compra Registradas", total_ordenes)
                
                st.markdown("---")
                df_view = df_compras.copy()
                if "Total ($)" in df_view.columns:
                    df_view["Total ($)"] = df_view["Total ($)"].apply(lambda x: f"${x:,.2f}")
                st.dataframe(df_view, use_container_width=True, hide_index=True)
        else:
            st.error("Error al conectar con el servidor para obtener las compras.")
    except Exception as e:
        st.error(f"Error de conexión: {e}")