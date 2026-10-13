import streamlit as st
import requests
import os
import pandas as pd
import io

# Conexión estricta de Producción en Nube
API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

def render_despachos():
    st.subheader("📦 Control de Despachos y Envíos por Courier")
    st.markdown("Gestiona estados de paquetes, asigna guías y genera etiquetas imprimibles 'De / Para'.")

    col1, col2 = st.columns(2)
    with col1:
        filtro_estado = st.selectbox(
            "Filtrar por Estado de Despacho", 
            ["TODOS", "PENDIENTE", "EMPACADO", "EN TRÁNSITO", "ENTREGADO"]
        )
    with col2:
        filtro_provincia = st.text_input("Filtrar por Provincia", placeholder="Ej: Guayas, Pichincha...")

    params = {}
    if filtro_estado != "TODOS":
        params["estado"] = filtro_estado
    if filtro_provincia.strip():
        params["provincia"] = filtro_provincia.strip()

    try:
        response = requests.get(f"{API_URL}/despachos/reporte", params=params)
        if response.status_code == 200:
            data_despachos = response.json()
            
            if not data_despachos:
                st.info("No se encontraron despachos con los filtros seleccionados.")
                return

            df = pd.DataFrame(data_despachos)
            
            # Métricas
            total_pedidos = len(df)
            pendientes = len(df[df["estado_despacho"] == "PENDIENTE"])
            en_transito = len(df[df["estado_despacho"] == "EN TRÁNSITO"])
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Pedidos Listados", total_pedidos)
            m2.metric("Pendientes / Empacando", pendientes)
            m3.metric("En Tránsito (Con Guía)", en_transito)

            st.divider()

            # --- SECCIÓN: TABLA Y BOTÓN EXCEL ---
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                st.markdown("#### 📋 Listado Consolidado (Organizado por Zona)")
            with col_t2:
                try:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df[[
                            "factura_id", "numero_factura", "fecha", "cliente", 
                            "provincia", "ciudad", "courier", "numero_guia", "estado_despacho", "total"
                        ]].to_excel(writer, index=False, sheet_name='Despachos')
                    excel_data = output.getvalue()
                    
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=excel_data,
                        file_name="Listado_Despachos.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except Exception as ex:
                    st.caption("⚠️ Instale openpyxl para exportar Excel (`pip install openpyxl`)")

            st.dataframe(
                df[[
                    "factura_id", "numero_factura", "fecha", "cliente", 
                    "provincia", "ciudad", "courier", "numero_guia", "estado_despacho", "total"
                ]],
                use_container_width=True
            )

            st.divider()

            col_a, col_b = st.columns(2)

            # --- COLUMNA A: ACTUALIZAR GUÍA ---
            with col_a:
                st.markdown("#### 🚚 Actualizar Guía y Estado")
                with st.form("form_actualizar_guia"):
                    f_id_sel = st.selectbox(
                        "Seleccione Pedido / Factura", 
                        options=df["factura_id"].tolist(),
                        format_func=lambda x: f"Factura #{df[df['factura_id'] == x]['numero_factura'].values[0]} - {df[df['factura_id'] == x]['cliente'].values[0]} ({df[df['factura_id'] == x]['ciudad'].values[0]})"
                    )
                    
                    pedido_sel = df[df["factura_id"] == f_id_sel].iloc[0]
                    
                    nuevo_courier = st.text_input("Courier", value=str(pedido_sel["courier"]))
                    guia_val = str(pedido_sel["numero_guia"])
                    nueva_guia = st.text_input("Número de Guía", value="" if guia_val == "SIN GUÍA" else guia_val)
                    nuevo_estado = st.selectbox(
                        "Estado de Despacho", 
                        ["EMPACADO", "EN TRÁNSITO", "ENTREGADO", "PENDIENTE"],
                        index=1 if pedido_sel["estado_despacho"] == "PENDIENTE" else 0
                    )

                    submit_guia = st.form_submit_button("Guardar Cambios")

                    if submit_guia:
                        if not nueva_guia.strip():
                            st.error("Ingrese el número de guía.")
                        else:
                            res_put = requests.put(
                                f"{API_URL}/pedidos/{f_id_sel}/guia", 
                                params={
                                    "numero_guia": nueva_guia.strip(),
                                    "courier_nombre": nuevo_courier.strip(),
                                    "estado_despacho": nuevo_estado
                                }
                            )
                            if res_put.status_code == 200:
                                st.success("¡Guía y estado actualizados!")
                                st.rerun()
                            else:
                                st.error(f"Error: {res_put.text}")

            # --- COLUMNA B: GENERAR MEMBRETE IMPRIMIBLE Y BOTÓN GUARDAR ---
            with col_b:
                st.markdown("#### 🏷️ Generar Membrete de Envío (De / Para)")
                f_id_label = st.selectbox(
                    "Seleccione Pedido para Etiqueta", 
                    options=df["factura_id"].tolist(),
                    format_func=lambda x: f"Factura #{df[df['factura_id'] == x]['numero_factura'].values[0]} - {df[df['factura_id'] == x]['cliente'].values[0]}"
                )
                
                ped_lbl = df[df["factura_id"] == f_id_label].iloc[0]

                html_label = f"""
                <div style="border: 2px dashed #1e293b; padding: 20px; border-radius: 10px; background-color: #ffffff; color: #000000; font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #000; padding-bottom: 8px; margin-bottom: 12px;">
                        <span style="font-weight: bold; font-size: 1.2rem;">🛍️ FAJAS ISABELLA</span>
                        <span style="font-size: 0.85rem; font-weight: bold;">ENVÍO: {ped_lbl['courier'].upper()}</span>
                    </div>
                    
                    <!-- REMITENTE (DE) -->
                    <div style="background-color: #f1f5f9; padding: 8px; border-radius: 5px; margin-bottom: 12px; font-size: 0.85rem;">
                        <strong>DE (REMITENTE):</strong> FAJAS ISABELLA<br>
                        <strong>Ciudad:</strong> Guayaquil, Ecuador<br>
                        <strong>Atención al cliente:</strong> +593 99 999 9999
                    </div>
                    
                    <!-- DESTINATARIO (PARA) -->
                    <div style="border: 1px solid #cbd5e1; padding: 12px; border-radius: 5px; font-size: 0.95rem;">
                        <span style="font-size: 1.1rem; font-weight: bold; color: #2563eb;">PARA (DESTINATARIO):</span><br>
                        <strong>Cliente:</strong> {ped_lbl['cliente']}<br>
                        <strong>CI/RUC:</strong> {ped_lbl['ruc_cedula']}<br>
                        <strong>Provincia/Ciudad:</strong> {ped_lbl['provincia']} - {ped_lbl['ciudad']}<br>
                        <strong>Dirección:</strong> {ped_lbl['direccion']}<br>
                        <strong>Referencia:</strong> {ped_lbl['referencia'] if ped_lbl['referencia'] else 'N/A'}<br>
                    </div>
                    
                    <div style="margin-top: 12px; font-size: 0.85rem; display: flex; justify-content: space-between;">
                        <span><strong>Factura #:</strong> {ped_lbl['numero_factura']}</span>
                        <span><strong>Guía #:</strong> {ped_lbl['numero_guia']}</span>
                    </div>
                </div>
                """
                
                st.components.v1.html(html_label, height=330, scrolling=True)

                # Botón al lado / debajo para guardar el membrete en HTML
                st.download_button(
                    label="💾 Guardar Membrete (HTML)",
                    data=html_label,
                    file_name=f"Membrete_Factura_{ped_lbl['numero_factura']}.html",
                    mime="text/html",
                    use_container_width=True
                )

        else:
            st.error(f"Error al conectar con la API: {response.text}")

    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")