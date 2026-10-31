import streamlit as st
import requests
import os
import pandas as pd
import json

# --- CONEXIÓN DINÁMICA INTELIGENTE (LOCAL / NUBE) ---
if "API_URL" not in st.session_state:
    env_api = os.getenv("API_BASE_URL")
    if env_api:
        base = env_api.strip().rstrip("/")
        if not base.startswith("http"):
            base = f"https://{base}"
        st.session_state["API_URL"] = f"{base}/api"
    else:
        st.session_state["API_URL"] = "http://localhost:8000/api"

API_URL = st.session_state["API_URL"]
API_BASE = API_URL.removesuffix("/api")

def resolver_url_imagen(url_o_path: str) -> str:
    """Retorna la URL correcta ya sea externa (Cloudinary https://) o local."""
    if not url_o_path:
        return ""
    if url_o_path.startswith("http://") or url_o_path.startswith("https://"):
        return url_o_path
    return f"{API_BASE}/{url_o_path.lstrip('/')}"

def render_inventario():
    st.markdown("<p style='color: black; font-weight: bold;'>🖼️ Productos e Inventarios</p>", unsafe_allow_html=True)   
    
    if "accion_inventario" not in st.session_state:
        st.session_state.accion_inventario = "Registrar Nuevo Ítem"

    accion = st.radio(
        "Acción:",
        ("Registrar Nuevo Ítem", "Mantenimiento Inventario", "Mantenimiento de Categorías"),
        horizontal=True,
        key="accion_inventario"
    )

    try:
        res_cat = requests.get(f"{API_URL}/categorias")
        if res_cat.status_code == 200 and res_cat.json():
            categorias_disponibles = [c["nombre"] for c in res_cat.json()]
        else:
            categorias_disponibles = ["GENERAL"]
    except Exception:
        categorias_disponibles = ["GENERAL"]

    if accion == "Registrar Nuevo Ítem":
        col_tit, col_btn_excel = st.columns([1.8, 2.2])
        with col_tit:
            st.markdown("##### 🖼️ Registra Productos - Variantes y Multimedia")
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

            st.markdown("###### 🏷️ Variantes (Tallas, Colores, Precios, Stock y Descuento %)")
            st.caption("Agrega las variantes reales de tu producto. Si usas modalidad Individual, el % de oferta base se aplicará a las variantes.")

            df_inicial = pd.DataFrame(columns=["sku", "talla", "color", "precio", "descuento_%", "stock_actual", "stock_minimo", "stock_maximo", "imagen_variante"])

            df_variantes_editado = st.data_editor(
                df_inicial,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "sku": st.column_config.TextColumn("SKU (Opcional)", width="small"),
                    "talla": st.column_config.TextColumn("Talla *", width="small"),
                    "color": st.column_config.TextColumn("Color *", width="small"),
                    "precio": st.column_config.NumberColumn("Precio ($) *", format="$ %.2f", min_value=0.0, width="small"),
                    "descuento_%": st.column_config.NumberColumn("Descuento %", format="%d%%", min_value=0, max_value=100, step=1, width="small"),
                    "stock_actual": st.column_config.NumberColumn("Stock", min_value=0, step=1, width="small"),
                    "stock_minimo": st.column_config.NumberColumn("Stock Mín.", min_value=0, step=1, width="small"),
                    "stock_maximo": st.column_config.NumberColumn("Stock Máx.", min_value=0, step=1, width="small"),
                    "imagen_variante": st.column_config.TextColumn("Foto Variante (Opcional)", width="medium")
                }
            )

        with col_der:
            st.markdown("##### 📸 Imagen Principal del Producto")
            archivo_imagen = st.file_uploader("Subir imagen general:", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
            
            if archivo_imagen is not None:
                st.image(archivo_imagen, use_container_width=True)
            else:
                st.info("Sin imagen principal")

            st.markdown("---")
            st.markdown("###### 🏷️ Estado General y Descuentos")

            en_liquidacion = st.checkbox("🔥 En Liquidación", key="reg_liq")
            es_nuevo = st.checkbox("✨ Nuevo (New)", key="reg_new")
            en_oferta = st.checkbox("🏷️ En Oferta", key="reg_ofe")

            desc_oferta_reg = 0.0
            tipo_desc_reg = "GENERAL"
            if en_oferta or en_liquidacion:
                col_d1, col_d2 = st.columns(2)
                desc_oferta_reg = col_d1.number_input("% Oferta Base", min_value=0, max_value=100, value=0, step=1, key="reg_desc_val")
                tipo_desc_reg = col_d2.selectbox("Modalidad", options=["GENERAL", "INDIVIDUAL"], key="reg_tipo_desc")

            st.markdown("---")
            with st.expander("📂 Archivos Adicionales (Galería, Video, Cartilla)"):
                img_1 = st.file_uploader("Galería #1", type=["jpg", "jpeg", "png", "webp"], key="reg_img1")
                img_2 = st.file_uploader("Galería #2", type=["jpg", "jpeg", "png", "webp"], key="reg_img2")
                img_3 = st.file_uploader("Galería #3", type=["jpg", "jpeg", "png", "webp"], key="reg_img3")
                img_4 = st.file_uploader("Galería #4", type=["jpg", "jpeg", "png", "webp"], key="reg_img4")
                video_file = st.file_uploader("Video Demostrativo", type=["mp4", "mov", "webm"], key="reg_video")
                cartilla_file = st.file_uploader("Cartilla / Guía Tallas", type=["jpg", "jpeg", "png", "webp", "pdf"], key="reg_cartilla")

        st.divider()

        col_btn, col_msg = st.columns([1.5, 2.5])

        with col_btn:
            btn_guardar = st.button("💾 Guardar Producto y Todas sus Variantes", type="primary", use_container_width=True)

        if btn_guardar:
            campos_faltantes = []
            if not nombre_producto or str(nombre_producto).strip() in ["", "None", "nan"]:
                campos_faltantes.append("Nombre del Modelo / Producto")
            if archivo_imagen is None:
                campos_faltantes.append("Imagen Principal del Producto")
            if df_variantes_editado is None or df_variantes_editado.empty:
                campos_faltantes.append("Al menos una variante en la tabla")

            if campos_faltantes:
                with col_msg:
                    st.error(f"⚠️ **Campos incompletos o inválidos:** {', '.join(campos_faltantes)}. Por favor revísalos.")
            else:
                try:
                    lista_variantes = []
                    for index, row in df_variantes_editado.iterrows():
                        talla = str(row.get("talla", "")).strip()
                        color = str(row.get("color", "")).strip()
                        sku_val = str(row.get("sku", "")).strip() if pd.notna(row.get("sku")) else ""
                        img_var_val = str(row.get("imagen_variante", "")).strip() if pd.notna(row.get("imagen_variante")) else ""
                        desc_var_val = float(row.get("descuento_%", 0) or 0)
                        
                        if tipo_desc_reg == "GENERAL":
                            desc_var_val = 0.0
                        elif tipo_desc_reg == "INDIVIDUAL" and desc_var_val == 0 and desc_oferta_reg > 0:
                            desc_var_val = float(desc_oferta_reg)

                        if not sku_val or sku_val.lower() in ["none", "nan", ""]:
                            sku_val = ""
                        
                        lista_variantes.append({
                            "sku": sku_val,
                            "talla": talla,
                            "color": color,
                            "stock_actual": int(row.get("stock_actual", 0) or 0),
                            "stock_minimo": int(row.get("stock_minimo", 2) or 2),
                            "stock_maximo": int(row.get("stock_maximo", 20) or 20),
                            "precio": float(row.get("precio", 0.0) or 0.0),
                            "descuento_porcentaje": desc_var_val,
                            "imagen_url": img_var_val
                        })

                    data_form = {
                        "nombre": nombre_producto,
                        "modelo": nombre_producto,
                        "categoria": categoria,
                        "en_liquidacion": str(en_liquidacion).lower(),
                        "es_nuevo": str(es_nuevo).lower(),
                        "en_oferta": str(en_oferta).lower(),
                        "descuento_oferta": str(desc_oferta_reg),
                        "tipo_descuento": tipo_desc_reg,
                        "variantes": json.dumps(lista_variantes)
                    }

                    files_form = {
                        "imagen": (archivo_imagen.name, archivo_imagen.getvalue(), archivo_imagen.type)
                    }
                    if 'img_1' in locals() and img_1: files_form["imagen_1"] = (img_1.name, img_1.getvalue(), img_1.type)
                    if 'img_2' in locals() and img_2: files_form["imagen_2"] = (img_2.name, img_2.getvalue(), img_2.type)
                    if 'img_3' in locals() and img_3: files_form["imagen_3"] = (img_3.name, img_3.getvalue(), img_3.type)
                    if 'img_4' in locals() and img_4: files_form["imagen_4"] = (img_4.name, img_4.getvalue(), img_4.type)
                    if 'video_file' in locals() and video_file: files_form["video"] = (video_file.name, video_file.getvalue(), video_file.type)
                    if 'cartilla_file' in locals() and cartilla_file: files_form["cartilla"] = (cartilla_file.name, cartilla_file.getvalue(), cartilla_file.type)

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
        st.markdown("##### 📋 Mantenimiento y Edición de Inventario")
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
                            "SKU": v.get("SKU", "") or v.get("sku", ""),
                            "Talla": v.get("Talla", "") or v.get("talla", ""),
                            "Color": v.get("Color", "") or v.get("color", ""),
                            "Precio ($)": v.get("Precio ($)", 0.0) or v.get("precio", 0.0),
                            "Descuento %": v.get("descuento_porcentaje", 0) or 0,
                            "Stock": v.get("Stock", 0) or v.get("stock_actual", 0),
                            "Stock Mín.": v.get("Stock Mínimo", 2),
                            "Stock Máx.": v.get("Stock Máximo", 20)
                        })
                    
                    df_inventario = pd.DataFrame(data_tabla)

                    col_f1, col_f2 = st.columns(2)
                    opciones_filtro = ["TODAS"] + categorias_disponibles
                    filtro_cat = col_f1.selectbox("🔍 Filtrar por Categoría:", options=opciones_filtro, key="filtro_cat_select")
                    filtro_texto = col_f2.text_input("🔍 Buscar por Nombre o SKU:", placeholder="Escribe para buscar...", key="filtro_texto_select")

                    df_filtrado = df_inventario.copy()
                    if filtro_cat != "TODAS":
                        df_filtrado = df_filtrado[df_filtrado["Categoría"] == filtro_cat]
                    if filtro_texto:
                        mask = df_filtrado["Producto"].str.contains(filtro_texto, case=False, na=False) | \
                               df_filtrado["SKU"].str.contains(filtro_texto, case=False, na=False)
                        df_filtrado = df_filtrado[mask]

                    st.divider()
                    st.markdown("##### 🛠️ Corrección de Variante, Estados, Multimedia y Fotos")
                    st.caption("Selecciona la variante, edita sus atributos y gestiona por separado su foto específica y la foto general del ítem.")

                    col_id_sel, col_btn_del = st.columns([3.0, 1.0], vertical_alignment="bottom")
                    
                    var_id_input = None
                    if not df_filtrado.empty:
                        opciones_selectbox = {}
                        lista_labels = []
                        for _, row in df_filtrado.iterrows():
                            v_id = row["ID Var"]
                            label_desc = f"ID {v_id} — {row['Producto']} [Talla: {row['Talla']} | Color: {row['Color']} | SKU: {row['SKU']}]"
                            opciones_selectbox[label_desc] = v_id
                            lista_labels.append(label_desc)
                        
                        idx_sel_defecto = 0
                        if "var_id_editando" in st.session_state:
                            var_guardada = st.session_state["var_id_editando"]
                            for i_lbl, lbl_txt in enumerate(lista_labels):
                                if opciones_selectbox[lbl_txt] == var_guardada:
                                    idx_sel_defecto = i_lbl
                                    break

                        sel_var_label = col_id_sel.selectbox("Seleccionar Variante a Editar", options=lista_labels, index=idx_sel_defecto, key="select_variante_editar")
                        var_id_input = opciones_selectbox[sel_var_label]
                        st.session_state["var_id_editando"] = var_id_input

                        if col_btn_del.button("🗑️ Eliminar Variante", type="secondary", use_container_width=True, key=f"btn_del_var_{var_id_input}"):
                            try:
                                res_del_var = requests.delete(f"{API_URL}/variantes/{var_id_input}")
                                if res_del_var.status_code == 200:
                                    st.success(f"✅ Variante ID {var_id_input} eliminada correctamente.")
                                    if "var_id_editando" in st.session_state:
                                        del st.session_state["var_id_editando"]
                                    st.rerun()
                                else:
                                    st.error(f"No se pudo eliminar la variante: {res_del_var.text}")
                            except Exception as err_del:
                                st.error(f"Error de conexión al eliminar: {err_del}")
                    else:
                        st.warning("⚠️ No se encontraron variantes con los filtros seleccionados.")
                        var_id_input = 1
                    
                    variante_encontrada = mapa_variantes.get(var_id_input)
                    cat_defecto = 0
                    p_info = {}
                    liq_def = False
                    nuevo_def = False
                    oferta_def = False
                    stock_min_def = 2
                    stock_max_def = 20
                    desc_var_def = 0
                    desc_oferta_def = 0.0
                    tipo_desc_def = "GENERAL"

                    if variante_encontrada:
                        p_info = variante_encontrada.get("producto") or {}
                        cat_nombre_var = p_info.get("categoria", "")
                        if cat_nombre_var in categorias_disponibles:
                            cat_defecto = categorias_disponibles.index(cat_nombre_var)
                        
                        liq_def = bool(p_info.get("en_liquidacion", False))
                        nuevo_def = bool(p_info.get("es_nuevo", False))
                        oferta_def = bool(p_info.get("en_oferta", False))
                        desc_oferta_def = float(p_info.get("descuento_oferta", 0.0) or 0.0)
                        tipo_desc_def = p_info.get("tipo_descuento", "GENERAL") or "GENERAL"
                        stock_min_def = int(variante_encontrada.get("Stock Mínimo", 2))
                        stock_max_def = int(variante_encontrada.get("Stock Máximo", 20))
                        desc_var_def = int(variante_encontrada.get("descuento_porcentaje", 0) or 0)

                    with st.form("form_modificar_variante"):
                        col_form_izq, col_form_der = st.columns([2.2, 1.2])

                        with col_form_izq:
                            c1, c2, c3 = st.columns([1.5, 1, 1])
                            nueva_cat = c1.selectbox("Categoría", options=categorias_disponibles, index=cat_defecto)
                            nueva_talla = c2.text_input("Talla", value=variante_encontrada.get("Talla") or variante_encontrada.get("talla") or "S")
                            nuevo_color = c3.text_input("Color", value=variante_encontrada.get("Color") or variante_encontrada.get("color") or "Negro")
                            
                            c4, c5, c6, c7 = st.columns(4)
                            precio_val = float(variante_encontrada.get("Precio ($)") or variante_encontrada.get("precio") or 45.0) if variante_encontrada else 45.0
                            nuevo_precio = c4.number_input("Precio ($)", min_value=0.0, value=precio_val, step=0.5)
                            nuevo_desc_var = c5.number_input("Descuento %", min_value=0, max_value=100, value=desc_var_def, step=1)
                            nuevo_stock_min = c6.number_input("Stock Mín.", min_value=0, value=stock_min_def, step=1)
                            nuevo_stock_max = c7.number_input("Stock Máx.", min_value=0, value=stock_max_def, step=1)

                            st.markdown("---")
                            st.markdown("###### 🏷️ Estado General y Descuentos del Producto")
                            ec1, ec2, ec3 = st.columns(3)
                            edit_liquidacion = ec1.checkbox("🔥 En Liquidación", value=liq_def, key="edit_liq")
                            edit_es_nuevo = ec2.checkbox("✨ Nuevo (New)", value=nuevo_def, key="edit_new")
                            edit_en_oferta = ec3.checkbox("🏷️ En Oferta", value=oferta_def, key="edit_ofe")

                            col_md1, col_md2 = st.columns(2)
                            edit_desc_oferta = col_md1.number_input("% Oferta Base", min_value=0, max_value=100, value=int(desc_oferta_def), step=1, key="edit_desc_oferta")
                            idx_tipo_def = 0 if tipo_desc_def == "GENERAL" else 1
                            edit_tipo_desc = col_md2.selectbox("Modalidad Descuento", options=["GENERAL", "INDIVIDUAL"], index=idx_tipo_def, key="edit_tipo_desc")

                            st.markdown("---")
                            with st.expander("📂 Modificar Archivos Adicionales (Galería, Video, Cartilla)"):
                                edit_img_1 = st.file_uploader("Actualizar Galería #1", type=["jpg", "jpeg", "png", "webp"], key="edit_img1")
                                edit_img_2 = st.file_uploader("Actualizar Galería #2", type=["jpg", "jpeg", "png", "webp"], key="edit_img2")
                                edit_img_3 = st.file_uploader("Actualizar Galería #3", type=["jpg", "jpeg", "png", "webp"], key="edit_img3")
                                edit_img_4 = st.file_uploader("Actualizar Galería #4", type=["jpg", "jpeg", "png", "webp"], key="edit_img4")
                                edit_video_file = st.file_uploader("Actualizar Video Demostrativo", type=["mp4", "mov", "webm"], key="edit_video")
                                edit_cartilla_file = st.file_uploader("Actualizar Cartilla / Guía Tallas", type=["jpg", "jpeg", "png", "webp", "pdf"], key="edit_cartilla")

                        with col_form_der:
                            st.markdown("**Gestión de Fotos (Variante vs Ítem)**")
                            
                            col_f_var, col_f_prod = st.columns(2)
                            
                            with col_f_var:
                                st.markdown("<p style='font-size:11px; font-weight:bold; text-align:center;'>FOTO VARIANTE</p>", unsafe_allow_html=True)
                                img_var_url = variante_encontrada.get("imagen_url") if variante_encontrada else ""
                                if img_var_url and str(img_var_url).strip() not in ["", "None", "nan", "null"]:
                                    url_v = str(img_var_url).strip()
                                    if not url_v.startswith("http"): url_v = resolver_url_imagen(url_v)
                                    st.image(url_v, width=100)
                                else:
                                    st.info("Sin foto variante")
                                archivo_nueva_imagen_variante = st.file_uploader("Subir Variante", type=["jpg", "jpeg", "png", "webp"], key="up_img_var", label_visibility="collapsed")

                            with col_f_prod:
                                st.markdown("<p style='font-size:11px; font-weight:bold; text-align:center;'>FOTO DEL ÍTEM</p>", unsafe_allow_html=True)
                                img_gen_url = p_info.get("imagen_url") if p_info else ""
                                if img_gen_url and str(img_gen_url).strip() not in ["", "None", "nan", "null"]:
                                    url_p = str(img_gen_url).strip()
                                    if not url_p.startswith("http"): url_p = resolver_url_imagen(url_p)
                                    st.image(url_p, width=100)
                                else:
                                    st.info("Sin foto ítem")
                                archivo_nueva_imagen_producto = st.file_uploader("Subir Ítem", type=["jpg", "jpeg", "png", "webp"], key="up_img_prod", label_visibility="collapsed")

                        col_btn_acc, col_msg_acc = st.columns([1.8, 2.2])
                        with col_btn_acc:
                            btn_actualizar = st.form_submit_button("🔄 Actualizar Datos y Variante", type="primary", use_container_width=True)
                        
                        if btn_actualizar:
                            if not variante_encontrada:
                                with col_msg_acc:
                                    st.error("El ID de variante seleccionado no es válido.")
                            else:
                                try:
                                    files = {}
                                    if archivo_nueva_imagen_variante is not None:
                                        files["imagen_variante"] = (archivo_nueva_imagen_variante.name, archivo_nueva_imagen_variante.getvalue(), archivo_nueva_imagen_variante.type)
                                    if archivo_nueva_imagen_producto is not None:
                                        files["imagen_producto"] = (archivo_nueva_imagen_producto.name, archivo_nueva_imagen_producto.getvalue(), archivo_nueva_imagen_producto.type)
                                    
                                    if 'edit_img_1' in locals() and edit_img_1: files["imagen_1"] = (edit_img_1.name, edit_img_1.getvalue(), edit_img_1.type)
                                    if 'edit_img_2' in locals() and edit_img_2: files["imagen_2"] = (edit_img_2.name, edit_img_2.getvalue(), edit_img_2.type)
                                    if 'edit_img_3' in locals() and edit_img_3: files["imagen_3"] = (edit_img_3.name, edit_img_3.getvalue(), edit_img_3.type)
                                    if 'edit_img_4' in locals() and edit_img_4: files["imagen_4"] = (edit_img_4.name, edit_img_4.getvalue(), edit_img_4.type)
                                    if 'edit_video_file' in locals() and edit_video_file: files["video"] = (edit_video_file.name, edit_video_file.getvalue(), edit_video_file.type)
                                    if 'edit_cartilla_file' in locals() and edit_cartilla_file: files["cartilla"] = (edit_cartilla_file.name, edit_cartilla_file.getvalue(), edit_cartilla_file.type)

                                    data_payload = {
                                        "categoria": nueva_cat,
                                        "talla": nueva_talla,
                                        "color": nuevo_color,
                                        "precio": str(nuevo_precio),
                                        "descuento_porcentaje": str(nuevo_desc_var),
                                        "stock_minimo": str(nuevo_stock_min),
                                        "stock_maximo": str(nuevo_stock_max),
                                        "en_liquidacion": str(edit_liquidacion).lower(),
                                        "es_nuevo": str(edit_es_nuevo).lower(),
                                        "en_oferta": str(edit_en_oferta).lower(),
                                        "descuento_oferta": str(edit_desc_oferta),
                                        "tipo_descuento": edit_tipo_desc
                                    }

                                    res_upd = requests.put(f"{API_URL}/variantes/{var_id_input}", data=data_payload, files=files if files else None)
                                    
                                    if res_upd.status_code == 200:
                                        with col_msg_acc:
                                            st.success("✅ Variante actualizada")
                                        st.session_state["var_id_editando"] = var_id_input
                                    else:
                                        with col_msg_acc:
                                            st.error(f"No se pudo actualizar: {res_upd.text}")
                                except Exception as err:
                                    with col_msg_acc:
                                        st.error(f"Error de comunicación: {err}")
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
                                    st.image(resolver_url_imagen(c_img), width=60)
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