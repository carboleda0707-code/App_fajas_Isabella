import streamlit as st
import requests
from datetime import date

API_URL = "http://127.0.0.1:8000/api"

def render_ventas():
    st.markdown("### 💳 Ventas y Facturación")
    st.markdown("---")
    
    accion = st.radio("Acción:", ["Registrar Nueva Venta", "Consultar Facturas Emitidas"], horizontal=True)
    st.markdown("---")
    
    if accion == "Consultar Facturas Emitidas":
        if st.button("🔄 Actualizar Facturas"):
            st.rerun()
        try:
            res = requests.get(f"{API_URL}/facturas", timeout=3)
            if res.status_code == 200 and res.json():
                facturas_venta = [f for f in res.json() if f['tipo_factura'] == 'VENTA']
                if facturas_venta:
                    st.dataframe(facturas_venta, use_container_width=True)
                else:
                    st.info("No hay facturas de venta registradas.")
            else:
                st.info("No hay registros en el sistema.")
        except:
            st.error("Error al conectar con el servidor.")
            
    elif accion == "Registrar Nueva Venta":
        try:
            res = requests.get(f"{API_URL}/inventario", timeout=3)
            dict_skus = {f"{item['sku']} | {item['talla']} | {item['color']} (Stock: {item['stock_actual']} | ${item['precio']})": item for item in res.json()} if res.status_code == 200 else {}
        except:
            dict_skus = {}
        lista_desc = list(dict_skus.keys())
        
        try:
            res_c = requests.get(f"{API_URL}/clientes", timeout=3)
            todos_clientes = res_c.json() if res_c.status_code == 200 else []
        except:
            todos_clientes = []
            
        with st.form("form_venta_mod"):
            c1, c2, c3 = st.columns(3)
            with c1:
                num_f = st.text_input("Nº de Factura").strip()
            with c2:
                num_aut = st.text_input("Nº de Autorización").strip()
            with c3:
                metodo = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Tarjeta de Crédito"])
                
            r1, r2, r3 = st.columns(3)
            with r1:
                n_items = st.number_input("Cantidad de Ítems", min_value=1, max_value=20, value=1)
            with r2:
                f_fact = st.date_input("Fecha de Factura", value=date.today())
            with r3:
                cod_t = st.text_input("Código Transferencia (Si aplica)").strip()
                
            st.markdown("---")
            st.markdown("#### Cliente")
            filtro = st.text_input("🔍 Buscar Cliente por RUC o Nombre...").strip().lower()
            cliente_sel = None
            if filtro and todos_clientes:
                filtrados = [c for c in todos_clientes if filtro in c['ruc_cedula'].lower() or filtro in c['nombre'].lower()]
                if filtrados:
                    opts = {f"{c['ruc_cedula']} - {c['nombre']}": c for c in filtrados}
                    sel = st.selectbox("Seleccione cliente:", list(opts.keys()))
                    cliente_sel = opts[sel]

            ruc_c = cliente_sel['ruc_cedula'] if cliente_sel else ""
            nom_c = cliente_sel['nombre'] if cliente_sel else ""
            telf_c = cliente_sel.get('telefono', '') if cliente_sel else ""
            dir_c = cliente_sel.get('direccion', '') if cliente_sel else ""

            if cliente_sel:
                st.success(f"**Cliente seleccionado:** {nom_c}")

            st.markdown("---")
            items = []
            if lista_desc:
                for i in range(int(n_items)):
                    ic1, ic2, ic3 = st.columns([3, 1, 1])
                    with ic1:
                        p_sel = st.selectbox(f"Faja #{i+1}", lista_desc, key=f"mv_sku_{i}")
                        info = dict_skus[p_sel]
                    with ic2:
                        cant = st.number_input(f"Cant #{i+1}", min_value=1, value=1, key=f"mv_cant_{i}")
                    with ic3:
                        prec = st.number_input(f"Precio ($) #{i+1}", min_value=0.0, value=float(info['precio']), key=f"mv_prec_{i}")
                    items.append({"sku": info['sku'], "cantidad": cant, "precio_unitario": prec})
                    
            if st.form_submit_button("Confirmar Venta"):
                if not cliente_sel:
                    st.error("❌ Seleccione un cliente.")
                elif not num_f or not ruc_c:
                    st.warning("Complete los campos obligatorios.")
                else:
                    try:
                        res = requests.post(f"{API_URL}/ventas-factura", json={
                            "numero_factura": num_f, "numero_autorizacion": num_aut,
                            "fecha_factura": str(f_fact), "metodo_pago": metodo,
                            "codigo_transferencia": cod_t, "ruc_cliente": ruc_c,
                            "nombre_cliente": nom_c, "direccion_cliente": dir_c,
                            "telefono_cliente": telf_c, "items": items
                        }, timeout=5)
                        if res.status_code == 200:
                            st.success("✅ ¡Venta registrada exitosamente!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {res.json().get('detail')}")
                    except Exception as e:
                        st.error(f"❌ Error de conexión: {e}")