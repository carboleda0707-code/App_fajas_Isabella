import streamlit as st
import requests
import os
import pandas as pd

# Lectura dinámica de la API: usa la variable de entorno en Railway o localhost en desarrollo
API_URL = st.session_state.get("API_URL", "http://127.0.0.1:8000/api")

def render_inventario():
    accion = st.radio(
        "",
        ("Registrar Nuevo Ítem", "Consultar y Modificar Inventario", "Mantenimiento de Categorías"),
        horizontal=True,
        label_visibility="collapsed"
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
        col_izq, col_der = st.columns([3, 1.2])

        with col_izq:
            st.markdown("#### 🖼️ Registro de Producto Base, Variantes e Imagen")
            
            nombre_producto = st.text_input("Nombre del Modelo / Producto", placeholder="Ej: Panty Alto Diva")
            
            # Selector dinámico de categorías
            categoria = st.selectbox("Categoría del Producto", options=categorias_disponibles)

            st.markdown("#### 🏷️ Tabla de Variantes (Tallas, Colores, Precios y Stock)")
            st.caption("Puedes dejar el SKU vacío para que el sistema lo genere automáticamente de forma compacta (ej: id-talla-color), o escribir uno personalizado.")

            # Tabla inicial limpia sin SKUs quemados estáticos (SKU en blanco para autogeneración)
            df_inicial = pd.DataFrame([
                {"sku": "", "talla": "S", "color": "Negro", "precio": 45.0, "stock_actual": 10},
                {"sku": "", "talla": "M", "color": "Negro", "precio": 45.0, "stock_actual": 10},
                {"sku": "", "talla": "L", "color": "Negro", "precio": 45.0, "stock_actual": 8}
            ])

            df_variantes_editado = st.data_editor(
                df_inicial,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "sku": st.column_config.TextColumn("SKU (Opcional / Autogenerado)", width="medium"),
                    "talla": st.column_config.TextColumn("Talla", width="small"),
                    "color": st.column_config.TextColumn("Color", width="small"),
                    "precio": st.column_config.NumberColumn("Precio ($)", format="$ %.2f", min_value=0.0, width="small"),
                    "stock_actual": st.column_config.NumberColumn("Stock", min_value=0, step=1, width="small")
                }
            )

        with col_der:
            st.markdown("#### Imagen del Producto")
            archivo_imagen = st.file_uploader("Subir imagen:", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
            
            imagen_url_relativa = ""
            if archivo_imagen is not None:
                dir_destino = os.path.join("web", "img")
                os.makedirs(dir_destino, exist_ok=True)
                
                ruta_fisica = os.path.join(dir_destino, archivo_imagen.name)
                with open(ruta_fisica, "wb") as f:
                    f.write(archivo_imagen.getbuffer())
                
                imagen_url_relativa = f"img/{archivo_imagen.name}"
                st.image(archivo_imagen, use_container_width=True)
            else:
                st.info("Sin imagen seleccionada")

            en_liquidacion = st.checkbox("🔥 Marcar como En Liquidación (Oferta)")

        st.divider()

        col_btn, col_msg = st.columns([1.5, 2.5])

        with col_btn:
            btn_guardar = st.button("💾 Guardar Producto y Todas sus Variantes", type="primary", use_container_width=True)

        if btn_guardar:
            if not nombre_producto:
                with col_msg:
                    st.error("Debes ingresar el nombre del modelo.")
            elif not imagen_url_relativa:
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

                    payload = {
                        "nombre": nombre_producto,
                        "modelo": nombre_producto,
                        "categoria": categoria,
                        "imagen_url": imagen_url_relativa,
                        "en_liquidacion": en_liquidacion,
                        "variantes": lista_variantes
                    }

                    res = requests.post(f"{API_URL}/productos", json=payload)

                    if res.status_code == 200:
                        with col_msg:
                            st.success("✅ Producto y variantes guardados satisfactoriamente")
                    else:
                        with col_msg:
                            st.error(f"Error al guardar: {res.text}")
                except Exception as e:
                    with col_msg:
                        st.error(f"Error de conexión con la API: {e}")

    elif accion == "Consultar y Modificar Inventario":
        st.markdown("### 📋 Consulta y Modificación de Inventario Actual")
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
                            "Stock": v.get("Stock", 0)
                        })
                    
                    df_inventario = pd.DataFrame(data_tabla)

                    st.markdown("#### 🔍 Filtrar Inventario")
                    col_f1, col_f2 = st.columns(2)
                    
                    opciones_filtro = ["TODAS"] + categorias_disponibles
                    filtro_cat = col_f1.selectbox("Filtrar por Categoría:", options=opciones_filtro)
                    filtro_texto = col_f2.text_input("Buscar por Nombre o SKU:", placeholder="Escribe para buscar...")

                    df_filtrado = df_inventario.copy()
                    if filtro_cat != "TODAS":
                        df_filtrado = df_filtrado[df_filtrado["Categoría"] == filtro_cat]
                    if filtro_texto:
                        mask = df_filtrado["Producto"].str.contains(filtro_texto, case=False, na=False) | \
                               df_filtrado["SKU"].str.contains(filtro_texto, case=False, na=False)
                        df_filtrado = df_filtrado[mask]

                    st.markdown("#### 📊 Listado General de Variantes Registradas")
                    st.dataframe(df_filtrado, use_container_width=True)

                    st.divider()
                    st.markdown("#### 🛠️ Corrección de Variante e Imagen por ID")
                    st.caption("Introduce el ID de la variante para ver su estado actual, modificar atributos o reemplazar su imagen.")

                    with st.form("form_modificar_variante"):
                        col_form_izq, col_form_der = st.columns([2.2, 1.2])

                        with col_form_izq:
                            c1, c2 = st.columns(2)
                            var_id_input = c1.number_input("ID Variante a Editar", min_value=1, step=1)
                            
                            variante_encontrada = mapa_variantes.get(var_id_input)
                            cat_defecto = 0
                            if variante_encontrada:
                                p_info = variante_encontrada.get("producto") or {}
                                cat_nombre_var = p_info.get("categoria", "")
                                if cat_nombre_var in categorias_disponibles:
                                    cat_defecto = categorias_disponibles.index(cat_nombre_var)

                            nueva_talla = c2.text_input("Talla", value=variante_encontrada.get("Talla", "S") if variante_encontrada else "S")
                            
                            c3, c4 = st.columns(2)
                            nueva_cat = c3.selectbox("Categoría", options=categorias_disponibles, index=cat_defecto)
                            nuevo_color = c4.text_input("Color", value=variante_encontrada.get("Color", "Negro") if variante_encontrada else "Negro")
                            
                            precio_val = float(variante_encontrada.get("Precio ($)", 45.0)) if variante_encontrada else 45.0
                            nuevo_precio = st.number_input("Precio ($)", min_value=0.0, value=precio_val, step=0.5)

                        with col_form_der:
                            st.markdown("**Previsualización Actual**")
                            if variante_encontrada:
                                p_info = variante_encontrada.get("producto") or {}
                                img_url = p_info.get("imagen_url") or variante_encontrada.get("imagen_url")
                                
                                st.caption(f"**Mod.:** {p_info.get('nombre', 'N/D')}")
                                if img_url and os.path.exists(os.path.join("web", img_url)):
                                    st.image(os.path.join("web", img_url), width=110)
                                else:
                                    st.info("Sin imagen registrada")
                            else:
                                st.warning("ID no encontrado")

                            archivo_nueva_imagen = st.file_uploader("Reemplazar foto", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")

                        btn_actualizar = st.form_submit_button("🔄 Actualizar Datos y Variante", type="primary", use_container_width=True)
                        
                        if btn_actualizar:
                            try:
                                files = {}
                                if archivo_nueva_imagen is not None:
                                    files = {"imagen": (archivo_nueva_imagen.name, archivo_nueva_imagen.getvalue(), archivo_nueva_imagen.type)}

                                data_payload = {
                                    "categoria": nueva_cat,
                                    "talla": nueva_talla,
                                    "color": nuevo_color,
                                    "precio": str(nuevo_precio)
                                }

                                res_upd = requests.put(f"{API_URL}/variantes/{var_id_input}", data=data_payload, files=files if files else None)
                                
                                if res_upd.status_code == 200:
                                    st.success(f"✅ Variante ID {var_id_input} actualizada correctamente.")
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

    else:
        # --- PESTAÑA: MANTENIMIENTO DE CATEGORÍAS ---
        st.markdown("### 🏷️ Mantenimiento y Tabla de Categorías Web")
        st.caption("Añade nuevas categorías con su gráfico circular representativo o gestiónalas desde la base de datos.")

        col_c_izq, col_c_der = st.columns([1.2, 1.8])

        with col_c_izq:
            st.markdown("#### ➕ Registrar / Actualizar Categoría")
            
            with st.form("form_crear_categoria", clear_on_submit=True):
                nueva_cat_nombre = st.text_input("Nombre de la Categoría", placeholder="Ej: LINEA REDUCTORA")
                archivo_cat_img = st.file_uploader("Imagen Circular (PNG/JPG)", type=["jpg", "jpeg", "png", "webp"])
                
                btn_guardar_cat = st.form_submit_button("💾 Guardar en Tabla y Web", type="primary", use_container_width=True)
                
                if btn_guardar_cat:
                    if not nueva_cat_nombre:
                        st.error("Debes ingresar el nombre de la categoría.")
                    elif archivo_cat_img is None:
                        st.error("Debes subir la imagen gráfica para el círculo web.")
                    else:
                        try:
                            files = {"imagen": (archivo_cat_img.name, archivo_cat_img.getvalue(), archivo_cat_img.type)}
                            data = {"nombre": nueva_cat_nombre}
                            
                            res = requests.post(f"{API_URL}/categorias", data=data, files=files)
                            if res.status_code == 200:
                                st.success("Actualización Web Satisfactoria")
                            else:
                                st.error(f"Error al guardar: {res.text}")
                        except Exception as e:
                            st.error(f"Error de conexión con la API: {e}")

        with col_c_der:
            st.markdown("#### 📊 Listado de Categorías en Base de Datos")
            try:
                res_get = requests.get(f"{API_URL}/categorias")
                if res_get.status_code == 200:
                    cats_data = res_get.json()
                    if cats_data:
                        df_cats = pd.DataFrame(cats_data)
                        st.dataframe(df_cats[["id", "nombre", "imagen_url"]], use_container_width=True)

                        st.markdown("#### 🗑️ Eliminar por ID de Categoría")
                        c_del1, c_del2 = st.columns([2, 1])
                        cat_id_a_eliminar = c_del1.number_input("ID Categoría", min_value=1, step=1, label_visibility="collapsed")
                        if c_del2.button("❌ Eliminar", type="secondary", use_container_width=True):
                            res_del = requests.delete(f"{API_URL}/categorias/{cat_id_a_eliminar}")
                            if res_del.status_code == 200:
                                st.success("🗑️ Categoría eliminada correctamente.")
                                st.rerun()
                            else:
                                st.error(f"No se pudo eliminar: {res_del.text}")
                    else:
                        st.info("No hay categorías registradas en la tabla todavía.")
            except Exception as ex:
                st.warning(f"No se pudieron cargar las categorías: {ex}")