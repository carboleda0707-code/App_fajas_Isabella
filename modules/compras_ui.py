import streamlit as st
import requests
from datetime import date
import os
import pandas as pd

# Conexión estricta de Producción en Nube
API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

def render_compras():
    st.markdown("### 📥 Módulo de Compras a Proveedores")
    st.markdown("---")
    
    accion = st.radio(
        "Acción a realizar:", 
        ["📥 Registrar Nueva Compra", "📋 Consultar Facturas de Compra Ingresadas"], 
        horizontal=True
    )
    st.markdown("---")
    
    if accion == "📋 Consultar Facturas de Compra Ingresadas":
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            if st.button("🔄 Actualizar Listado", use_container_width=True):
                st.rerun()
        try:
            res = requests.get(f"{API_URL}/compras-factura", timeout=5)
            if res.status_code == 200 and res.json():
                df_compras = pd.DataFrame(res.json())
                st.dataframe(df_compras, use_container_width=True, hide_index=True)
            else:
                st.info("No hay facturas de compra registradas aún.")
        except Exception as e:
            st.error(f"Error al conectar con el servidor: {e}")
            
    elif accion == "📥 Registrar Nueva Compra":
        # 1. Consultar Inventario para mapear variantes
        try:
            res_inv = requests.get(f"{API_URL}/inventario", timeout=5)
            inventario = res_inv.json() if res_inv.status_code == 200 else []
        except:
            inventario = []

        if not inventario:
            st.warning("⚠️ No hay productos o variantes registradas en el inventario. Debe crearlos primero en el Módulo de Inventario.")
            return

        dict_skus = {f"{item['sku']} — [{item.get('modelo', 'Faja')} | Talla: {item['talla']} | Color: {item['color']}]": item['sku'] for item in inventario}
        lista_desc_skus = list(dict_skus.keys())

        # 2. Consultar Proveedores para Autocompletar
        try:
            res_prov = requests.get(f"{API_URL}/proveedores", timeout=5)
            proveedores = res_prov.json() if res_prov.status_code == 200 else []
        except:
            proveedores = []
        
        dict_provs = {p['nombre_empresa']: p for p in proveedores} if proveedores else {}

        st.subheader("📄 Membrete y Cabecera de la Factura")
        
        with st.form("form_compra_nueva"):
            c1, c2 = st.columns(2)
            with c1:
                num_f = st.text_input("Nº Factura Proveedor (Ej: 001-001-000012345)").strip()
            with c2:
                f_compra = st.date_input("Fecha de Compra", value=date.today())
                
            p1, p2 = st.columns(2)
            with p1:
                if dict_provs:
                    sel_prov = st.selectbox("Seleccionar Proveedor Guardado", ["-- Ingresar Nuevo Proveedor --"] + list(dict_provs.keys()))
                else:
                    sel_prov = "-- Ingresar Nuevo Proveedor --"
            with p2:
                pass

            if sel_prov != "-- Ingresar Nuevo Proveedor --":
                ruc_sugerido = dict_provs[sel_prov].get("ruc_cedula", "")
                nombre_sugerido = sel_prov
            else:
                ruc_sugerido = ""
                nombre_sugerido = ""

            rc1, rc2 = st.columns(2)
            with rc1:
                ruc_p = st.text_input("RUC / Cédula Proveedor", value=ruc_sugerido).strip()
            with rc2:
                nom_p = st.text_input("Nombre de Empresa Proveedora", value=nombre_sugerido).strip()

            st.markdown("---")
            st.subheader("📦 Detalle de Variantes Recibidas en Bodega")
            
            num_lineas = st.number_input("Número de variantes distintas en la factura", min_value=1, max_value=30, value=1, step=1)
            
            items_compra = []
            for i in range(int(num_lineas)):
                st.markdown(f"**Línea #{i+1}**")
                ic1, ic2, ic3 = st.columns([2.5, 1, 1])
                with ic1:
                    sel_sku_desc = st.selectbox(f"Seleccionar Producto/Variante #{i+1}", lista_desc_skus, key=f"comp_sku_{i}")
                    sku_elegido = dict_skus[sel_sku_desc]
                with ic2:
                    cant_ing = st.number_input(f"Cantidad Recibida #{i+1}", min_value=1, value=1, key=f"comp_cant_{i}")
                with ic3:
                    val_neto = st.number_input(f"Costo Unitario ($) #{i+1}", min_value=0.0, value=0.0, step=0.5, key=f"comp_val_{i}")
                
                items_compra.append({
                    "sku": sku_elegido,
                    "cantidad": int(cant_ing),
                    "valor_neto": float(val_neto)
                })
                st.markdown("---")

            submitted = st.form_submit_button("💾 Guardar Compra e Incrementar Stock", use_container_width=True)
            
            if submitted:
                if not num_f or not ruc_p or not nom_p:
                    st.warning("⚠️ Complete todos los campos obligatorios del proveedor y factura.")
                else:
                    payload = {
                        "numero_factura": num_f,
                        "fecha_factura": str(f_compra),
                        "ruc_proveedor": ruc_p,
                        "nombre_proveedor": nom_p,
                        "items": items_compra
                    }
                    try:
                        resp = requests.post(f"{API_URL}/compras-factura", json=payload, timeout=10)
                        if resp.status_code == 200:
                            st.success("✅ ¡Compra registrada con éxito y stock actualizado en bodega!")
                            st.balloons()
                        else:
                            detail = resp.json().get('detail', 'Error al procesar')
                            st.error(f"❌ Ocurrió un error: {detail}")
                    except Exception as e:
                        st.error(f"❌ Error de conexión: {e}")