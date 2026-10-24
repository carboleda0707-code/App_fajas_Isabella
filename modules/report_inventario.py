import streamlit as st
import requests
import os
import io
import pandas as pd

# --- CONEXIÓN DINÁMICA LOCAL / NUBE ---
API_URL = st.session_state.get("API_URL", "http://localhost:8000/api")

def render_reporte_inventario():
    st.markdown("### 📦 Reportes de Inventario y Stock")
    st.markdown("---")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        tipo_vista = st.selectbox(
            "Tipo de Vista", 
            ["General (Stock por Variante)", "Consolidado (Valoración de Stock)"]
        )
    with col_f2:
        # Filtro por categoría
        categoria_filtro = st.selectbox(
            "Filtrar por Categoría:",
            ["TODAS", "PANTYS COSTILLERO", "POST OPERATORIO", "GENERAL"]
        )
    with col_f3:
        # Selector de ordenamiento explícito
        ordenar_por = st.selectbox(
            "Ordenar por:",
            ["nombre", "Stock", "Precio ($)", "categoria", "id", "SKU"]
        )
        
    st.markdown("---")

    try:
        res = requests.get(f"{API_URL}/inventario", timeout=5)
        if res.status_code == 200:
            inventario = res.json()
            if not inventario:
                st.info("No hay productos registrados en el inventario.")
                return
                
            # Aplicar filtro por categoría
            inventario_filtrado = inventario
            if categoria_filtro != "TODAS":
                inventario_filtrado = [
                    i for i in inventario 
                    if str(i.get('categoria') or i.get('producto', {}).get('categoria', '')).upper() == categoria_filtro
                ]

            if not inventario_filtrado:
                st.warning("⚠️ No se encontraron productos para la categoría seleccionada.")
                return

            df_inv = pd.DataFrame(inventario_filtrado)

            # 1. 🧹 Eliminar la columna anidada 'producto' para que no salga en el Excel
            if 'producto' in df_inv.columns:
                df_inv = df_inv.drop(columns=['producto'])

            # 2. 🔀 Aplicar el ordenamiento seleccionado en el DataFrame antes de exportar
            if ordenar_por in df_inv.columns:
                df_inv = df_inv.sort_values(by=ordenar_por, ascending=True).reset_index(drop=True)

            # --- GENERACIÓN DEL ARCHIVO EXCEL EN MEMORIA (UNA SOLA VEZ Y LIMPIO) ---
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_inv.to_excel(writer, index=False, sheet_name="Inventario")
                
                # Autoajustar ancho de columnas según la longitud del texto
                worksheet = writer.sheets["Inventario"]
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
                label="📥 Descargar Excel de Inventario (Tal cual ordenado)",
                data=buffer,
                file_name=f"Reporte_Inventario_{categoria_filtro.replace(' ', '_')}_orden_por_{ordenar_por}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.markdown("---")

            if tipo_vista == "General (Stock por Variante)":
                st.markdown("#### 📋 Inventario General Actual por Variante")
                st.dataframe(df_inv, use_container_width=True, hide_index=True)
            else:
                st.markdown("#### 💰 Consolidado y Valoración Total de Inventario")
                
                total_unidades_fisicas = 0
                valor_total_inventario = 0.0
                total_skus = len(inventario_filtrado)
                
                for item in inventario_filtrado:
                    stock = int(item.get('Stock') or item.get('stock_actual') or item.get('stock') or 0)
                    precio = float(item.get('Precio ($)') or item.get('precio') or 0.0)
                    
                    total_unidades_fisicas += stock
                    valor_total_inventario += (stock * precio)
                
                m1, m2, m3 = st.columns(3)
                m1.metric("📦 Unidades en Bodega (Stock)", f"{total_unidades_fisicas:,} prendas")
                m2.metric("🏷️ Modelos / SKUs Únicos", f"{total_skus} variantes")
                m3.metric("💵 Valor Estimado en Inventario", f"${valor_total_inventario:,.2f}")
                
                st.markdown("---")
                st.dataframe(df_inv, use_container_width=True, hide_index=True)
        else:
            st.error("Error al obtener la información del inventario desde el servidor.")
    except Exception as e:
        st.error(f"Error de conexión con el servidor: {e}")