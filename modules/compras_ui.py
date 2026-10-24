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
    nombre_archivo = img_str.split('/')[-1].strip()
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

        # 1. Agrupar variantes por Producto / Modelo principal
        productos_dict = {}
        info_variantes = {}

        for item in inventario:
            sku_val = item.get('sku') or item.get('SKU') or 'N/D'
            
            if isinstance(item.get('producto'), dict):
                nombre_prod = item.get('producto', {}).get('nombre') or item.get('producto', {}).get('modelo') or "Faja"
                imagen_url = item.get('producto', {}).get('imagen_url') or ""
            else:
                nombre_prod = item.get('Producto') or item.get('producto') or item.get('nombre') or item.get('modelo') or "Faja"
                imagen_url = item.get('imagen_url') or item.get('imagen') or ""

            talla_val = item.get('talla') or item.get('Talla') or 'Única'
            color_val = item.get('color') or item.get('Color') or 'Único'
            
            # Agrupación por nombre de producto
            if nombre_prod not in productos_dict:
                productos_dict[nombre_prod] = []
            
            productos_dict[nombre_prod].append({
                "sku": sku_val,
                "talla": talla_val,
                "color": color_val,
                "imagen_url": obtener_url_imagen(imagen_url)
            })

            info_variantes[sku_val] = {
                "nombre": nombre_prod,
                "talla": talla_val,
                "color": color_val,
                "imagen_url": obtener_url_imagen(imagen_url)
            }

        lista_productos = list(productos_dict.keys())

        # Consultar Proveedores para Autocompletar
        try:
            res_prov = requests.get(f"{API_URL}/proveedores", timeout=5)
            proveedores = res_prov.json() if res_prov.status_code == 200 else []
        except:
            proveedores = []
        
        dict_provs = {p.get('nombre') or p.get('nombre_empresa', ''): p for p in proveedores} if proveedores else {}

        st.subheader("📄 Membrete y Cabecera de la Factura de Compra")
        
        with st.form("form_compra_nueva"):
            c1, c2 = st.columns(2)
            with c1:
                num_f = st.text_input("Nº Factura Proveedor (Ej: 001-001-000012345)").strip()
            with c2:
                f_compra = st.date_input("Fecha de Compra", value=date.today())
                
            if dict_provs:
                sel_prov = st.selectbox("Seleccionar Proveedor Registrado", ["-- Ingresar Proveedor Nuevo --"] + list(dict_provs.keys()))
            else:
                sel_prov = "-- Ingresar Proveedor Nuevo --"

            if sel_prov != "-- Ingresar Proveedor Nuevo --":
                prov_sel_data = dict_provs[sel_prov]
                ruc_sugerido = prov_sel_data.get("ruc_cedula") or ""
                nombre_sugerido = sel_prov
            else:
                ruc_sugerido = ""
                nombre_sugerido = ""

            rc1, rc2 = st.columns(2)
            with rc1:
                ruc_p = st.text_input("RUC / Cédula Proveedor", value=ruc_sugerido).strip()
            with rc2:
                nom_p = st.text_input("Nombre / Razón Social Proveedor", value=nombre_sugerido).strip()

            st.markdown("---")
            st.subheader("📦 Detalle de Ítems y Variantes Recibidas en Bodega")
            
            num_lineas = st.number_input("Número de productos distintos en la factura", min_value=1, max_value=30, value=1, step=1)
            
            items_compra = []
            
            for i in range(int(num_lineas)):
                st.markdown(f"**Línea de Producto #{i+1}**")
                
                # 2. Selección de Producto principal
                sel_producto = st.selectbox(
                    f"Seleccionar Producto / Modelo #{i+1}", 
                    lista_productos, 
                    key=f"comp_prod_{i}"
                )
                
                variantes_del_producto = productos_dict.get(sel_producto, [])
                
                if variantes_del_producto:
                    # Mostrar la imagen de referencia del producto
                    img_muestra = variantes_del_producto[0].get("imagen_url", SVG_FALLBACK)
                    col_img_m, col_info_m = st.columns([1, 5])
                    with col_img_m:
                        try:
                            st.image(img_muestra, width=70)
                        except:
                            st.image(SVG_FALLBACK, width=70)
                    with col_info_m:
                        st.caption(f"Se registrarán las **{len(variantes_del_producto)} variantes** asociadas a este modelo[cite: 11]. Indique cantidad y costo unitario para cada una:")

                    # Listar todas las variantes del producto seleccionado con validación de costo > 0
                    for v_idx, var in enumerate(variantes_del_producto):
                        sku_v = var["sku"]
                        talla_v = var["talla"]
                        color_v = var["color"]
                        
                        cols_v = st.columns([3, 1.2, 1.3])
                        with cols_v[0]:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🏷️ **Talla:** {talla_v} | **Color:** {color_v} *(SKU: {sku_v})*")
                        with cols_v[1]:
                            cant_ing = st.number_input("Cantidad", min_value=0, value=0, key=f"cant_{i}_{v_idx}")
                        with cols_v[2]:
                            val_neto = st.number_input("Costo Unit. ($)", min_value=0.0, value=0.0, step=0.5, key=f"costo_{i}_{v_idx}")
                        
                        if cant_ing > 0:
                            items_compra.append({
                                "sku": sku_v,
                                "cantidad": int(cant_ing),
                                "valor_neto": float(val_neto)
                            })
                
                st.markdown("---")

            submitted = st.form_submit_button("💾 Guardar Compra e Incrementar Stock", type="primary", use_container_width=True)
            
            if submitted:
                # 3. Validaciones estrictas antes de enviar
                if not num_f or not ruc_p or not nom_p:
                    st.warning("⚠️ Complete todos los campos obligatorios del proveedor y número de factura.")
                elif not items_compra:
                    st.warning("⚠️ Debe ingresar al menos una cantidad mayor a 0 en las variantes de la compra.")
                else:
                    # Validar que ningún costo unitario sea 0 si la cantidad es mayor a 0
                    costos_invalidos = any(item["valor_neto"] <= 0 for item in items_compra)
                    
                    if costos_invalidos:
                        st.error("❌ **Error de validación:** Todas las variantes con cantidad a comprar mayor a 0 deben tener obligatoriamente un **Costo Unitario mayor a 0**[cite: 11]. Por favor verifique.")
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
                            if resp.status_code in (200, 201):
                                st.success("✅ ¡Compra registrada con éxito y stock actualizado en bodega!")
                                st.balloons()
                            else:
                                detail = resp.json().get('detail', 'Error al procesar la compra')
                                st.error(f"❌ {detail}")
                        except Exception as e:
                            st.error(f"❌ Error de conexión con el servidor: {e}")