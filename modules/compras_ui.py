import streamlit as st
import requests
from datetime import date
import os
import pandas as pd

# Conexión estricta de Producción en Nube
API_BASE = os.getenv("API_BASE_URL", "https://fajasisabella-production.up.railway.app").rstrip("/")
API_URL = f"{API_BASE}/api" if not API_BASE.endswith("/api") else API_BASE

SVG_FALLBACK = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'><rect width='100%' height='100%' fill='%23f1f5f9'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='%2394a3b8' font-size='10'>Fajas Isabella</text></svg>"

def obtener_url_imagen(img_path):
    if not img_path or str(img_path).strip() in ["", "None", "null", "/logo.png", "logo.png"]:
        return SVG_FALLBACK
    
    img_str = str(img_path).strip()
    if img_str.startswith("http://") or img_str.startswith("https://"):
        return img_str
    
    # Limpiar cualquier prefijo para obtener solo el nombre del archivo
    nombre_archivo = img_str.split('/')[-1].strip()
    
    # Ruta oficial donde FastAPI sirve la carpeta estática web/img
    return f"{API_BASE}/img/{nombre_archivo}"

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
        try:
            res_inv = requests.get(f"{API_URL}/inventario", timeout=5)
            inventario = res_inv.json() if res_inv.status_code == 200 else []
        except:
            inventario = []

        if not inventario:
            st.warning("⚠️ No hay productos o variantes registradas en el inventario. Debe crearlos primero en el Módulo de Inventario.")
            return

        dict_skus = {}
        info_variantes = {}

        for item in inventario:
            sku_val = item.get('sku') or item.get('SKU') or 'N/D'
            
            nombre_prod = "Faja"
            imagen_url = ""
            
            # Extracción flexible de producto e imagen según el tipo de objeto retornado
            if isinstance(item.get('producto'), dict):
                nombre_prod = item.get('producto', {}).get('nombre') or item.get('producto', {}).get('modelo') or "Faja"
                imagen_url = item.get('producto', {}).get('imagen_url') or ""
            else:
                nombre_prod = item.get('Producto') or item.get('producto') or item.get('nombre') or item.get('modelo') or item.get('Modelo') or "Faja"
                imagen_url = item.get('imagen_url') or item.get('imagen') or item.get('Imagen') or ""

            talla_val = item.get('talla') or item.get('Talla') or 'Única'
            color_val = item.get('color') or item.get('Color') or 'Único'
            
            label_desc = f"🛍️ {str(nombre_prod).upper()} — [Talla: {talla_val} | Color: {color_val}] (SKU: {sku_val})"
            
            dict_skus[label_desc] = sku_val
            info_variantes[sku_val] = {
                "nombre": nombre_prod,
                "talla": talla_val,
                "color": color_val,
                "imagen_url": obtener_url_imagen(imagen_url)
            }

        lista_desc_skus = list(dict_skus.keys())

        # Consultar Proveedores para Autocompletar
        try:
            res_prov = requests.get(f"{API_URL}/proveedores", timeout=5)
            proveedores = res_prov.json() if res_prov.status_code == 200 else []
        except:
            proveedores = []
        
        dict_provs = {p.get('nombre_empresa') or p.get('nombre', ''): p for p in proveedores} if proveedores else {}

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
                ruc_sugerido = dict_provs[sel_prov].get("ruc_cedula") or dict_provs[sel_prov].get("ruc") or ""
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
                
                col_img, col_sel, col_cant, col_costo = st.columns([1, 3.5, 1.2, 1.3])
                
                with col_sel:
                    sel_sku_desc = st.selectbox(
                        f"Seleccionar Producto / Variante #{i+1}", 
                        lista_desc_skus, 
                        key=f"comp_sku_{i}"
                    )
                    sku_elegido = dict_skus[sel_sku_desc]
                    info_var = info_variantes.get(sku_elegido, {})

                with col_img:
                    img_path_var = info_var.get("imagen_url", SVG_FALLBACK)
                    try:
                        st.image(img_path_var, width=80)
                    except:
                        st.image(SVG_FALLBACK, width=80)

                with col_cant:
                    cant_ing = st.number_input(f"Cantidad Recibida #{i+1}", min_value=1, value=1, key=f"comp_cant_{i}")
                with col_costo:
                    val_neto = st.number_input(f"Costo Unit. ($) #{i+1}", min_value=0.0, value=0.0, step=0.5, key=f"comp_val_{i}")
                
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