import streamlit as st
import requests
import os
import pandas as pd
import json

# --- CONEXIÓN DINÁMICA A LA API SEGÚN EL ENTORNO (LOCAL / NUBE) ---
API_URL = st.session_state.get("API_URL", "http://localhost:8000/api")
API_BASE = API_URL.removesuffix("/api")

def render_inventario():
    st.markdown("<p style='color: black; font-weight: bold;'>🖼️ Productos e Inventarios</p>", unsafe_allow_html=True)   
    
    # 1. Inicializar el estado en session_state si no existe
    if "accion_inventario" not in st.session_state:
        st.session_state.accion_inventario = "Registrar Nuevo Ítem"

    # 2. Vincular el st.radio con st.session_state usando 'key'
    accion = st.radio(
        "Acción:",
        ("Registrar Nuevo Ítem", "Mantenimiento Inventario", "Mantenimiento de Categorías"),
        horizontal=True,
        key="accion_inventario"
    )

    # Cargar categorías de forma dinámica desde la tabla de PostgreSQL
    try:
        res_cat = requests.get(f"{API_URL}/categorias")
        if res_cat.status_code == 200 and res_cat.json():
            categorias_disponibles = [c["nombre"] for c in res_cat.json()]
        else:
            categorias_disponibles = ["GENERAL"]
    except Exception:
        categorias_disponibles = ["GENERAL"]

    if accion == "Registrar Nuevo Ítem":
        # --- ENCABEZADO CON BOTÓN DE EXCEL AL LADO ---
        col_tit, col_btn_excel = st.columns([1.8, 2.2])
        with col_tit:
            st.markdown("##### 🖼️ Registra Productos - Variantes")
        with col_btn_excel:
            with st.expander("📥 Cargar Plantilla Excel (Restauración Masiva)"):
                st.caption("Sube tu backup en Excel para restaurar o recargar el inventario completo.")
                reiniciar_desde_cero = st.checkbox(
                    "🗑️ Borrar inventario anterior (Restaurar desde 0)",
                    value=True,
                    key="chk_reiniciar_excel"
                )
                archivo_excel = st.file_uploader("Selecciona archivo Excel (.xlsx)", type=["xlsx", "xls"], key="up_excel_masivo", label_visibility="collapsed")
                
                if archivo_excel is not None:
                    if st.button("🚀 Procesar y Sincronizar Inventario", type="primary", use_container_width=True, key="btn_ejecutar_excel"):
                        with st.spinner("Sincronizando inventario con la plantilla..."):
                            try:
                                files = {"file": (archivo_excel.name, archivo_excel.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                                data = {"reiniciar": str(reiniciar_desde_cero).lower()}
                                
                                response = requests.post(f"{API_URL}/inventario/importar-excel", data=data, files=files, timeout=60)
                                
                                if response.status_code == 200:
                                    res_json = response.json()
                                    st.success(f"✅ {res_json.get('message', 'Importación exitosa')}")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    error_msg = response.json().get('detail', 'Error desconocido')
                                    st.error(f"❌ Error: {error_msg}")
                            except Exception as e:
                                st.error(f"❌ Error de conexión: {e}")

        st.markdown("---")

        col_izq, col_der = st.columns([3, 1.2])

        with col_izq:
            nombre_producto = st.text_input("Nombre del Modelo / Producto", placeholder="Ej: Panty Alto Diva")
            categoria = st.selectbox("Categoría del Producto", options=categorias_disponibles)

            st.markdown("###### 🏷️ Variantes (Tallas, Colores, Precios y Stock)")
            st.caption("Puedes dejar el SKU vacío para que el sistema lo genere automáticamente de forma compacta (ej: id-talla-color), o escribir uno personalizado.")

            df_inicial = pd.DataFrame([
                {"sku": "", "talla": "S", "color": "Negro", "precio": 45.0, "stock_actual": 10, "stock_minimo": 2, "stock_maximo": 20},
                {"sku": "", "talla": "M", "color": "Negro", "precio": 45.0, "stock_actual": 15, "stock_minimo": 2, "stock_maximo": 20},
                {"sku": "", "talla": "L", "color": "Negro", "precio": 55.0, "stock_actual": 8, "stock_minimo": 2, "stock_maximo": 20}
            ])

            df_variantes_editado = st.data_editor(
                df_inicial,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "sku": st.column_config.TextColumn("SKU", width="small"),
                    "talla": st.column_config.TextColumn("Talla", width="small"),
                    "color": st.column_config.TextColumn("Color", width="small"),
                    "precio": st.column_config.NumberColumn("Precio ($)", format="$ %.2f", min_value=0.0, width="small"),
                    "stock_actual": st.column_config.NumberColumn("Stock", min_value=0, step=1, width="small"),
                    "stock_minimo": st.column_config.NumberColumn("Stock Mín.", min_value=0, step=1, width="small"),
                    "stock_maximo": st.column_config.NumberColumn("Stock Máx.", min_value=0, step=1, width="small")
                }
            )

        with col_der:
            st.markdown("##### Imagen del Producto")
            archivo_imagen = st.file_uploader("Subir imagen:", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
            
            if archivo_imagen is not None:
                st.image(archivo_imagen, use_container_width=True)
            else:
                st.info("Sin imagen seleccionada")

            st.markdown("---")
            st.markdown("###### 🏷️ Estado y Promociones")

            en_liquidacion = st.checkbox("🔥 Marcar como En Liquidación", key="reg_liq")
            es_nuevo = st.checkbox("✨ Marcar como Nuevo (New)", key="reg_new")
            
            en_oferta = st.checkbox("🏷️ Marcar como Oferta", key="reg_ofe")
            porcentaje_oferta = 0.0
            if en_oferta:
                porcentaje_oferta = st.number_input(
                    "Porcentaje de Oferta (%):",
                    min_value=1.0,
                    max_value=100.0,
                    value=10.0,
                    step=1.0,
                    help="Ingrese el porcentaje de descuento a aplicar para esta oferta"
                )

        st.divider()

        col_btn, col_msg = st.columns([1.5, 2.5])

        with col_btn:
            btn_guardar = st.button("💾 Guardar Producto y Todas sus Variantes", type="primary", use_container_width=True)

        if btn_guardar:
            if not nombre_producto:
                with col_msg:
                    st.error("Debes ingresar el nombre del modelo.")
            elif archivo_imagen is None:
                with col_msg:
                    st.error("Debes subir una imagen.")
            elif df_variantes_editado.empty:
                with col_msg:
                    st.error("Debe existir al menos una variante en la tabla.")
            else:
                try:
                    lista_variantes = []
                    for index, row in df_variantes_editado.iterrows():
                        talla = str(row.get("talla", "")).strip()
                        color = str(row.get("color", "")).strip()
                        sku_val = str(row.get("sku", "")).strip() if pd.notna(row.get("sku")) else ""
                        
                        if not sku_val or sku_val.lower() in ["none", "nan", ""]:
                            sku_val = ""
                        
                        lista_variantes.append({
                            "sku": sku_val,
                            "talla": talla,
                            "color": color,
                            "stock_actual": int(row.get("stock_actual", 0)),
                            "precio": float(row.get("precio", 0.0))
                        })

                    data_form = {
                        "nombre": nombre_producto,
                        "modelo": nombre_producto,
                        "categoria": categoria,
                        "en_liquidacion": str(en_liquidacion).lower(),
                        "es_nuevo": str(es_nuevo).lower(),
                        "en_oferta": str(en_oferta).lower(),
                        "descuento_oferta": str(porcentaje_oferta),
                        "variantes": json.dumps(lista_variantes)
                    }

                    files_form = {
                        "imagen": (archivo_imagen.name, archivo_imagen.getvalue(), archivo_imagen.type)
                    }

                    res = requests.post(f"{API_URL}/productos", data=data_form, files=files_form)

                    if res.status_code == 200:
                        with col_msg:
                            st.success("✅ Producto y variantes guardados satisfactoriamente")
                    else:
                        with col_msg:
                            st.error(f"Error al guardar: {res.text}")
                except Exception as e:
                    with col_msg:
                        st.error(f"Error de conexión con la API: {e}")

    elif accion == "Mantenimiento Inventario":
        st.markdown("##### 📋 Mantenimiento de Inventario")
        try:
            res = requests.get(f"{API_URL}/inventario")
            if res.status_code == 200:
                raw_json = res.json()
                if raw_json:
                    data_tabla = []
                    mapa_variantes = {}
                    
                    for v in raw_json:
                        var_id = v.get("id")
                        prod_info = v.get("producto") or {}
                        mapa_variantes[var_id] = v
                        
                        data_tabla.append({
                            "ID Var": var_id,
                            "Producto": prod_info.get("nombre", "N/D"),
                            "Categoría": prod_info.get("categoria", "N/D"),
                            "SKU": v.get("SKU", ""),
                            "Talla": v.get("Talla", ""),
                            "Color": v.get("Color", ""),
                            "Precio ($)": v.get("Precio ($)", 0.0),
                            "Stock": v.get("Stock", 0),
                            "Stock Mín.": v.get("Stock Mínimo", 2),
                            "Stock Máx.": v.get("Stock Máximo", 20)
                        })
                    
                    df_inventario = pd.DataFrame(data_tabla)

                    col_f1, col_f2 = st.columns(2)
                    
                    opciones_filtro = ["TODAS"] + categorias_disponibles
                    filtro_cat = col_f1.selectbox("🔍 Filtrar por Categoría:", options=opciones_filtro)
                    filtro_texto = col_f2.text_input("🔍 Buscar por Nombre o SKU:", placeholder="Escribe para buscar...")

                    df_filtrado = df_inventario.copy()
                    if filtro_cat != "TODAS":
                        df_filtrado = df_filtrado[df_filtrado["Categoría"] == filtro_cat]
                    if filtro_texto:
                        mask = df_filtrado["Producto"].str.contains(filtro_texto, case=False, na=False) | \
                               df_filtrado["SKU"].str.contains(filtro_texto, case=False, na=False)
                        df_filtrado = df_filtrado[mask]

                    st.markdown("##### 📊 Listado de Variantes")
                    st.dataframe(df_filtrado, use_container_width=True)

                    st.divider()
                    st.markdown("##### 🛠️ Corrección de Variante y Estados")
                    st.caption("Ingresa el ID de la Variante - Visualiza - Modifica Atributos, Promociones, Stock Mín/Máx o Reemplaza su imagen.")

                    col_id_sel, _ = st.columns([1.5, 2.5])
                    var_id_input = col_id_sel.number_input("ID Variante a Editar", min_value=1, step=1, value=int(df_filtrado.iloc[0]["ID Var"]) if not df_filtrado.empty else 1)
                    
                    variante_encontrada = mapa_variantes.get(var_id_input)
                    cat_defecto = 0
                    p_info = {}
                    liq_def = False
                    nuevo_def = False
                    oferta_def = False
                    desc_oferta_def = 0.0
                    stock_min_def = 2
                    stock_max_def = 20

                    if variante_encontrada:
                        p_info = variante_encontrada.get("producto") or {}
                        cat_nombre_var = p_info.get("categoria", "")
                        if cat_nombre_var in categorias_disponibles:
                            cat_defecto = categorias_disponibles.index(cat_nombre_var)
                        
                        liq_def = bool(p_info.get("en_liquidacion", False))
                        nuevo_def = bool(p_info.get("es_nuevo", False))
                        oferta_def = bool(p_info.get("en_oferta", False))
                        desc_oferta_def = float(p_info.get("descuento_oferta", 0.0) or 0.0)
                        stock_min_def = int(variante_encontrada.get("Stock Mínimo", 2))
                        stock_max_def = int(variante_encontrada.get("Stock Máximo", 20))

                    with st.form("form_modificar_variante"):
                        col_form_izq, col_form_der = st.columns([2.2, 1.2])

                        with col_form_izq:
                            c1, c2, c3 = st.columns([1.5, 1, 1])
                            nueva_cat = c1.selectbox("Categoría", options=categorias_disponibles, index=cat_defecto)
                            nueva_talla = c2.text_input("Talla", value=variante_encontrada.get("Talla", "S") if variante_encontrada else "S")
                            nuevo_color = c3.text_input("Color", value=variante_encontrada.get("Color", "Negro") if variante_encontrada else "Negro")
                            
                            c4, c5, c6 = st.columns(3)
                            precio_val = float(variante_encontrada.get("Precio ($)", 45.0)) if variante_encontrada else 45.0
                            nuevo_precio = c4.number_input("Precio ($)", min_value=0.0, value=precio_val, step=0.5)
                            nuevo_stock_min = c5.number_input("Stock Mín.", min_value=0, value=stock_min_def, step=1)
                            nuevo_stock_max = c6.number_input("Stock Máx.", min_value=0, value=stock_max_def, step=1)

                            st.markdown("---")
                            st.markdown("###### 🏷️ Estado y Promociones (Modificar / Quitar)")
                            ec1, ec2, ec3 = st.columns(3)
                            edit_liquidacion = ec1.checkbox("🔥 En Liquidación", value=liq_def, key="edit_liq")
                            edit_es_nuevo = ec2.checkbox("✨ Nuevo (New)", value=nuevo_def, key="edit_new")
                            edit_en_oferta = ec3.checkbox("🏷️ En Oferta", value=oferta_def, key="edit_ofe")

                            edit_descuento_oferta = st.number_input(
                                "Porcentaje de Oferta (%)",
                                min_value=0.0,
                                max_value=100.0,
                                value=desc_oferta_def,
                                step=1.0,
                                help="Porcentaje de descuento asignado a la oferta"
                            )

                        with col_form_der:
                            st.markdown("**Previsualización Actual**")
                            if variante_encontrada:
                                img_url = p_info.get("imagen_url") or variante_encontrada.get("imagen_url")
                                st.caption(f"**Mod.:** {p_info.get('nombre', 'N/D')}")
                                if img_url:
                                    url_imagen_completa = f"{API_BASE}/{img_url}"
                                    st.image(url_imagen_completa, width=110)
                                else:
                                    st.info("Sin imagen registrada")
                            else:
                                st.warning("ID no encontrado")

                            archivo_nueva_imagen = st.file_uploader("Reemplazar foto", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")

                        btn_actualizar = st.form_submit_button("🔄 Actualizar Datos y Variante", type="primary", use_container_width=True)
                        
                        if btn_actualizar:
                            if not variante_encontrada:
                                st.error("El ID de variante seleccionado no es válido.")
                            else:
                                try:
                                    files = {}
                                    if archivo_nueva_imagen is not None:
                                        files = {"imagen": (archivo_nueva_imagen.name, archivo_nueva_imagen.getvalue(), archivo_nueva_imagen.type)}

                                    data_payload = {
                                        "categoria": nueva_cat,
                                        "talla": nueva_talla,
                                        "color": nuevo_color,
                                        "precio": str(nuevo_precio),
                                        "stock_minimo": str(nuevo_stock_min),
                                        "stock_maximo": str(nuevo_stock_max),
                                        "en_liquidacion": str(edit_liquidacion).lower(),
                                        "es_nuevo": str(edit_es_nuevo).lower(),
                                        "en_oferta": str(edit_en_oferta).lower(),
                                        "descuento_oferta": str(edit_descuento_oferta)
                                    }

                                    res_upd = requests.put(f"{API_URL}/variantes/{var_id_input}", data=data_payload, files=files if files else None)
                                    
                                    if res_upd.status_code == 200:
                                        st.success(f"✅ Variante ID {var_id_input} y estados actualizados correctamente.")
                                        st.rerun()
                                    else:
                                        st.error(f"No se pudo actualizar: {res_upd.text}")
                                except Exception as err:
                                    st.error(f"Error de comunicación con la API: {err}")
                else:
                    st.info("No hay variantes registradas en el sistema todavía.")
            else:
                st.error(f"Error HTTP al consultar el inventario: {res.text}")
        except Exception as e:
            st.warning(f"Error de conexión con el endpoint de inventario: {e}")

    elif accion == "Mantenimiento de Categorías":
        st.markdown("##### 🗂️ Mantenimiento de Categorías")
        
        col_c1, col_c2 = st.columns([1.5, 2])
        
        with col_c1:
            st.markdown("###### ➕ Registrar Nueva Categoría")
            with st.form("form_nueva_categoria"):
                nombre_cat = st.text_input("Nombre de la Categoría", placeholder="Ej: Fajas Reductoras")
                img_cat = st.file_uploader("Imagen de Categoría", type=["jpg", "jpeg", "png", "webp"])
                
                btn_crear_cat = st.form_submit_button("💾 Guardar Categoría", type="primary", use_container_width=True)
                
                if btn_crear_cat:
                    if not nombre_cat:
                        st.error("Debes ingresar el nombre de la categoría.")
                    else:
                        try:
                            files = {}
                            if img_cat is not None:
                                files = {"imagen": (img_cat.name, img_cat.getvalue(), img_cat.type)}
                            data_cat = {"nombre": nombre_cat}
                            
                            res_c = requests.post(f"{API_URL}/categorias", data=data_cat, files=files if files else None)
                            if res_c.status_code == 200:
                                st.success("✅ Categoría creada exitosamente.")
                                st.rerun()
                            else:
                                st.error(f"Error al crear categoría: {res_c.text}")
                        except Exception as e:
                            st.error(f"Error de conexión: {e}")

        with col_c2:
            st.markdown("###### 📋 Categorías Existentes")
            try:
                res_get_cat = requests.get(f"{API_URL}/categorias")
                if res_get_cat.status_code == 200:
                    cats = res_get_cat.json()
                    if cats:
                        for c in cats:
                            c_id = c.get("id")
                            c_nombre = c.get("nombre")
                            c_img = c.get("imagen_url")
                            
                            cols_item = st.columns([1, 3])
                            with cols_item[0]:
                                if c_img:
                                    st.image(f"{API_BASE}/{c_img}", width=60)
                                else:
                                    st.write("Sin img")
                            with cols_item[1]:
                                st.write(f"**{c_nombre}** (ID: {c_id})")
                                if st.button("🗑️ Eliminar", key=f"del_cat_{c_id}"):
                                    res_del = requests.delete(f"{API_URL}/categorias/{c_id}")
                                    if res_del.status_code == 200:
                                        st.success(f"Categoría eliminada.")
                                        st.rerun()
                                    else:
                                        st.error(f"No se pudo eliminar: {res_del.text}")
                            st.divider()
                    else:
                        st.info("No hay categorías registradas.")
                else:
                    st.error("No se pudieron cargar las categorías.")
            except Exception as e:
                st.warning(f"Error al conectar con la API: {e}")