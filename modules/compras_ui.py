import streamlit as st
import requests
from datetime import date
import os

API_URL = st.session_state.get("API_URL", "http://127.0.0.1:8000/api")

def render_compras():
    st.markdown("### 📥 Compras a Proveedores")
    st.markdown("---")
    
    accion = st.radio("Acción:", ["Registrar Nueva Compra", "Consultar Facturas de Compra Ingresadas"], horizontal=True)
    st.markdown("---")
    
    if accion == "Consultar Facturas de Compra Ingresadas":
        if st.button("🔄 Actualizar Listado"):
            st.rerun()
        try:
            res = requests.get(f"{API_URL}/compras-factura", timeout=3)
            if res.status_code == 200 and res.json():
                st.dataframe(res.json(), use_container_width=True)
            else:
                st.info("No hay facturas de compra registradas.")
        except:
            st.error("Error al conectar con el servidor.")
            
    elif accion == "Registrar Nueva Compra":
        try:
            res = requests.get(f"{API_URL}/inventario", timeout=3)
            dict_skus = {f"{item['sku']} | {item['talla']} | {item['color']}": item['sku'] for item in res.json()} if res.status_code == 200 else {}
        except:
            dict_skus = {}

        lista_desc = list(dict_skus.keys())
        
        with st.form("form_compra_mod"):
            c1, c2, c3 = st.columns(3)
            with c1:
                num_f = st.text_input("Nº Factura Proveedor").strip()
            with c2:
                f_compra = st.date_input("Fecha de Compra", value=date.today())
            with c3:
                n_items = st.number_input("Cantidad de Ítems", min_value=1, max_value=20, value=1)
                
            p1, p2 = st.columns(2)
            with p1:
                ruc_p = st.text_input("RUC Proveedor").strip()
            with p2:
                nom_p = st.text_input("Nombre de Empresa Proveedora").strip()
                
            st.markdown("---")
            items = []
            if lista_desc:
                for i in range(int(n_items)):
                    ic1, ic2, ic3 = st.columns(3)
                    with ic1:
                        sel = st.selectbox(f"SKU #{i+1}", lista_desc, key=f"mc_sku_{i}")
                        sku = dict_skus[sel]
                    with ic2:
                        cant = st.number_input(f"Cantidad #{i+1}", min_value=1, value=1, key=f"mc_cant_{i}")
                    with ic3:
                        val = st.number_input(f"Valor Neto Unit. ($) #{i+1}", min_value=0.0, value=0.0, key=f"mc_val_{i}")
                    items.append({"sku": sku, "cantidad": cant, "valor_neto": val})
                    
            if st.form_submit_button("Registrar Compra"):
                if not num_f or not ruc_p or not nom_p:
                    st.warning("Complete todos los datos obligatorios.")
                else:
                    try:
                        res = requests.post(f"{API_URL}/compras-factura", json={
                            "numero_factura": num_f, "fecha_factura": str(f_compra),
                            "ruc_proveedor": ruc_p, "nombre_proveedor": nom_p, "items": items
                        }, timeout=5)
                        if res.status_code == 200:
                            st.success("✅ ¡Compra ingresada con éxito!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {res.json().get('detail')}")
                    except Exception as e:
                        st.error(f"❌ Error de conexión: {e}")