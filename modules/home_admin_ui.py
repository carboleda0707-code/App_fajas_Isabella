import streamlit as str_lit
import os
import requests
from database import SessionLocal, ConfiguracionWeb
import cloudinary.uploader
from datetime import datetime, time
from zoneinfo import ZoneInfo
import pandas as pd

API_URL = os.getenv("API_URL", "http://localhost:8000/api")

DEFAULT_EMBED = '<blockquote class="instagram-media" data-instgrm-captioned data-instgrm-permalink="https://www.instagram.com/reel/DQIK9pLDl4l/?utm_source=ig_embed&amp;utm_campaign=loading" data-instgrm-version="14" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:540px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"><div style="padding:16px;"> <a href="https://www.instagram.com/reel/DQIK9pLDl4l/?utm_source=ig_embed&amp;utm_campaign=loading" style=" background:#FFFFFF; line-height:0; padding:0 0; text-align:center; text-decoration:none; width:100%;" target="_blank"> <div style=" display: flex; flex-direction: row; align-items: center;"> <div style="background-color: #F4F4F4; border-radius: 50%; flex-grow: 0; height: 40px; margin-right: 14px; width: 40px;"></div> <div style="display: flex; flex-direction: column; flex-grow: 1; justify-content: center;"> <div style=" background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; margin-bottom: 6px; width: 100px;"></div> <div style=" background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; width: 60px;"></div></div></div><div style="padding: 19% 0;"></div> <div style="display:block; height:50px; margin:0 auto 12px; width:50px;"></div><div style="padding-top: 8px;"> <div style=" color:#3897f0; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:550; line-height:18px;">Ver esta publicación en Instagram</div></div><div style="padding: 12.5% 0;"></div></div></a><p style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; line-height:17px; margin-bottom:0; margin-top:8px; overflow:hidden; padding:8px 0 7px; text-align:center; text-overflow:ellipsis; white-space:nowrap;"><a href="https://www.instagram.com/reel/DQIK9pLDl4l/?utm_source=ig_embed&amp;utm_campaign=loading" style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:normal; line-height:17px; text-decoration:none;" target="_blank">Una publicación compartida de FAJAS ISABELLA (@fajasisabella.ec)</a></p></div></blockquote>'

def cargar_config_db():
    db = SessionLocal()
    try:
        rows = db.query(ConfiguracionWeb).all()
        config = {}
        for r in rows:
            config[r.seccion] = r.contenido
        return config
    except Exception as e:
        str_lit.error(f"Error al leer desde PostgreSQL: {e}")
        return {}
    finally:
        db.close()

def guardar_seccion_db(seccion: str, contenido: dict):
    db = SessionLocal()
    try:
        cfg = db.query(ConfiguracionWeb).filter(ConfiguracionWeb.seccion == seccion).first()
        if cfg:
            cfg.contenido = contenido
        else:
            cfg = ConfiguracionWeb(seccion=seccion, contenido=contenido)
            db.add(cfg)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        str_lit.error(f"Error al guardar en PostgreSQL: {e}")
        return False
    finally:
        db.close()

def render_home_admin():
    str_lit.markdown("### 🌐 Panel de Gestión del Home Web y Campañas (PostgreSQL)")
    str_lit.markdown("Actualiza el contenido multimedia, los textos, gestiona las campañas web y analiza su rendimiento financiero.")

    tab0, tab1, tab2, tab3, tab_campana, tab_analisis = str_lit.tabs([
        "🖼️ Banner Slider", 
        "📌 Historia", 
        "💬 En Vivo", 
        "📢 Publicidad", 
        "🎉 Campaña Masiva Web",
        "📊 Análisis de Campaña"
    ])

    config = cargar_config_db()

    # --- SECCIÓN 0.5 ---
    with tab0:
        str_lit.subheader("Administrar Sección 0.5 (Banner Slider Rotativo - 4 Diapositivas)")
        with str_lit.form("form_sec05"):
            sec05_cfg = config.get("sec05", {})
            slides_data = []
            
            # Opciones de destino disponibles para los botones de los slides
            opciones_destino = {
                "Catálogo General": "index.html#catalogo",
                "Nuevos Modelos": "index.html#nuevo",
                "Ofertas / Liquidación": "index.html#ofertas"
            }
            
            for i in range(1, 5):
                str_lit.markdown(f"---")
                str_lit.markdown(f"#### 🖼️ Diapositiva (Slide) {i}")
                s_cfg = sec05_cfg.get(f"slide{i}", {})
                
                archivo_slide = str_lit.file_uploader(f"Subir Imagen Slide {i} (.jpg/.png)", type=["jpg", "jpeg", "png"], key=f"up_slide_{i}")
                s_tag = str_lit.text_input(f"Etiqueta / Badge {i}", value=s_cfg.get("tag", f"Colección {i}"))
                s_titulo = str_lit.text_input(f"Título Principal {i}", value=s_cfg.get("titulo", f"Título de Ejemplo {i}"))
                s_desc = str_lit.text_area(f"Descripción {i}", value=s_cfg.get("descripcion", f"Descripción de la diapositiva {i}..."))
                
                # Fila dividida para el Botón y su Destino
                col_b1, col_b2 = str_lit.columns(2)
                with col_b1:
                    s_btn_texto = str_lit.text_input(f"Texto del Botón {i}", value=s_cfg.get("btn_texto", "Ver Colección"))
                with col_b2:
                    # Intentar recuperar la opción seleccionada previamente si existe
                    destino_actual_guardado = s_cfg.get("btn_destino", "index.html#catalogo")
                    indice_default = 0
                    for idx_opt, (k_opt, v_opt) in enumerate(opciones_destino.items()):
                        if v_opt == destino_actual_guardado:
                            indice_default = idx_opt
                            break
                            
                    s_btn_nombre_destino = str_lit.selectbox(f"¿A dónde se dirige? ({i})", list(opciones_destino.keys()), index=indice_default, key=f"sel_dest_{i}")
                    s_btn_destino = opciones_destino[s_btn_nombre_destino]

                # Control deslizante para el tiempo de transición del banner
                s_tiempo = str_lit.slider(
                    f"⏱️ Tiempo de Transición (segundos) - Slide {i}", 
                    min_value=2, 
                    max_value=10, 
                    value=int(s_cfg.get("tiempo", 5)), 
                    step=1,
                    key=f"slider_tiempo_{i}"
                )
                
                slides_data.append({
                    "file_uploader": archivo_slide,
                    "tag": s_tag,
                    "titulo": s_titulo,
                    "descripcion": s_desc,
                    "btn_texto": s_btn_texto,
                    "btn_destino": s_btn_destino,
                    "tiempo": s_tiempo,
                    "imagen_actual": s_cfg.get("imagen", ""),
                    "btn_completo": f"{s_btn_texto} → {s_btn_destino}"
                })

            subm_sec05 = str_lit.form_submit_button("💾 Guardar Cambios de Sección 0.5 en BD", use_container_width=True)
            
            if subm_sec05:
                payload_sec05 = {}
                for idx, data in enumerate(slides_data, start=1):
                    img_url = data["imagen_actual"]
                    archivo_subido = data["file_uploader"]
                    if archivo_subido is not None:
                        try:
                            resultado = cloudinary.uploader.upload(archivo_subido.getvalue(), folder="fajas_isabella/home/slider", resource_type="auto")
                            if resultado.get("secure_url"):
                                img_url = resultado.get("secure_url")
                        except Exception as e:
                            str_lit.warning(f"No se pudo subir a Cloudinary (Slide {idx}): {e}")
                    
                    payload_sec05[f"slide{idx}"] = {
                        "tag": data["tag"], 
                        "titulo": data["titulo"], 
                        "descripcion": data["descripcion"],
                        "btn_texto": data["btn_texto"], 
                        "btn_destino": data["btn_destino"],
                        "tiempo": data["tiempo"],
                        "btn_completo": data["btn_completo"],
                        "imagen": img_url
                    }
                
                if guardar_seccion_db("sec05", payload_sec05):
                    str_lit.success("✅ ¡Sección 0.5 subida a Cloudinary y guardada con éxito en PostgreSQL!")

    # --- SECCIÓN 1 ---
    with tab1:
        str_lit.subheader("Administrar Sección 1 (Historia, Imagen/Video y Textos)")
        with str_lit.form("form_sec1"):
            archivo_sec1 = str_lit.file_uploader("Subir Archivo Multimedia (Imagen .jpg/.png o Video .mp4)", type=["jpg", "jpeg", "png", "mp4"], key="up_sec1")
            sec1_cfg = config.get("sec1", {})
            nuevo_titulo = str_lit.text_input("Título Principal", value=sec1_cfg.get("titulo", "HISTORIA"))
            nuevo_subtitulo = str_lit.text_input("Subtítulo", value=sec1_cfg.get("subtitulo", "12 AÑOS RESALTANDO TU BELLEZA"))
            nuevo_p1 = str_lit.text_area("Párrafo 1", value=sec1_cfg.get("parrafo1", ""))
            nuevo_p2 = str_lit.text_area("Párrafo 2", value=sec1_cfg.get("parrafo2", ""))
            nuevo_p3 = str_lit.text_area("Párrafo 3 (Resaltado)", value=sec1_cfg.get("parrafo3", ""))

            subm_sec1 = str_lit.form_submit_button("💾 Guardar Cambios de Sección 1 en BD", use_container_width=True)
            if subm_sec1:
                multimedia_url = sec1_cfg.get("multimedia", "banner_historia.jpg")
                if archivo_sec1 is not None:
                    try:
                        resultado = cloudinary.uploader.upload(archivo_sec1.getvalue(), folder="fajas_isabella/home/historia", resource_type="auto")
                        if resultado.get("secure_url"):
                            multimedia_url = resultado.get("secure_url")
                    except Exception as e:
                        str_lit.warning(f"Error al subir a Cloudinary: {e}")
                
                payload_sec1 = {
                    "titulo": nuevo_titulo, "subtitulo": nuevo_subtitulo, "parrafo1": nuevo_p1,
                    "parrafo2": nuevo_p2, "parrafo3": nuevo_p3, "multimedia": multimedia_url
                }
                if guardar_seccion_db("sec1", payload_sec1):
                    str_lit.success("✅ ¡Sección 1 guardada con éxito en PostgreSQL!")

    # --- SECCIÓN 2 ---
    with tab2:
        str_lit.subheader("Administrar Sección 2 (Comunidad y Confianza - En Vivo / Redes)")
        with str_lit.form("form_sec2"):
            sec2_cfg = config.get("sec2", {})
            nuevo_ig_embed = str_lit.text_area("Código HTML del Post/Reel de Instagram", value=sec2_cfg.get("instagram_embed", DEFAULT_EMBED), height=150)
            nuevo_tk_url = str_lit.text_input("URL / Enlace de TikTok Live", value=sec2_cfg.get("tiktok_url", "https://tiktok.com"))

            subm_sec2 = str_lit.form_submit_button("💾 Guardar Cambios de Sección 2 en BD", use_container_width=True)
            if subm_sec2:
                if guardar_seccion_db("sec2", {"instagram_embed": nuevo_ig_embed, "tiktok_url": nuevo_tk_url}):
                    str_lit.success("✅ ¡Sección 2 guardada con éxito en PostgreSQL!")

    # --- SECCIÓN 3 ---
    with tab3:
        str_lit.subheader("Administrar Sección 3 (Publicidad - Imágenes/Videos y Textos)")
        with str_lit.form("form_sec3"):
            sec3_cfg = config.get("sec3", {})
            p1_cfg = sec3_cfg.get("card1", {})
            p1_file = str_lit.file_uploader("Imagen/Video Publi 1", type=["jpg", "jpeg", "png", "mp4"], key="pub_1")
            p1_tag = str_lit.text_input("Tag Publi 1", value=p1_cfg.get("tag", "PUBLICIDAD 1"))
            p1_title = str_lit.text_input("Título Publi 1", value=p1_cfg.get("titulo", ""))
            p1_desc = str_lit.text_area("Descripción Publi 1", value=p1_cfg.get("descripcion", ""))
            p1_link = str_lit.text_input("Texto Enlace Publi 1", value=p1_cfg.get("link_texto", "Ver Colección →"))

            p2_cfg = sec3_cfg.get("card2", {})
            p2_file = str_lit.file_uploader("Imagen/Video Publi 2", type=["jpg", "jpeg", "png", "mp4"], key="pub_2")
            p2_tag = str_lit.text_input("Tag Publi 2", value=p2_cfg.get("tag", "PUBLICIDAD 2"))
            p2_title = str_lit.text_input("Título Publi 2", value=p2_cfg.get("titulo", ""))
            p2_desc = str_lit.text_area("Descripción Publi 2", value=p2_cfg.get("descripcion", ""))
            p2_link = str_lit.text_input("Texto Enlace Publi 2", value=p2_cfg.get("link_texto", "Ver Modelos →"))

            p3_cfg = sec3_cfg.get("card3", {})
            p3_file = str_lit.file_uploader("Imagen/Video Publi 3", type=["jpg", "jpeg", "png", "mp4"], key="pub_3")
            p3_tag = str_lit.text_input("Tag Publi 3", value=p3_cfg.get("tag", "PUBLICIDAD 3"))
            p3_title = str_lit.text_input("Título Publi 3", value=p3_cfg.get("titulo", ""))
            p3_desc = str_lit.text_area("Descripción Publi 3", value=p3_cfg.get("descripcion", ""))
            p3_link = str_lit.text_input("Texto Enlace Publi 3", value=p3_cfg.get("link_texto", "Descubrir →"))

            subm_sec3 = str_lit.form_submit_button("💾 Guardar Cambios de Sección 3 en BD", use_container_width=True)
            if subm_sec3:
                def subir_pub_nube(archivo, url_anterior):
                    if archivo is not None:
                        try:
                            res = cloudinary.uploader.upload(archivo.getvalue(), folder="fajas_isabella/home/publicidad", resource_type="auto")
                            return res.get("secure_url", url_anterior)
                        except Exception as e:
                            str_lit.warning(f"Error subiendo a Cloudinary: {e}")
                    return url_anterior

                m1 = subir_pub_nube(p1_file, p1_cfg.get("multimedia", "publi_1.jpg"))
                m2 = subir_pub_nube(p2_file, p2_cfg.get("multimedia", "publi_2.jpg"))
                m3 = subir_pub_nube(p3_file, p3_cfg.get("multimedia", "publi_3.jpg"))

                payload_sec3 = {
                    "card1": {"tag": p1_tag, "titulo": p1_title, "descripcion": p1_desc, "link_texto": p1_link, "multimedia": m1},
                    "card2": {"tag": p2_tag, "titulo": p2_title, "descripcion": p2_desc, "link_texto": p2_link, "multimedia": m2},
                    "card3": {"tag": p3_tag, "titulo": p3_title, "descripcion": p3_desc, "link_texto": p3_link, "multimedia": m3}
                }
                if guardar_seccion_db("sec3", payload_sec3):
                    str_lit.success("✅ ¡Sección 3 guardada con éxito en PostgreSQL!")

    # --- CAMPAÑA MASIVA WEB (FESTIVO) ---
    with tab_campana:
        str_lit.subheader("🎉 Campaña Masiva Web (Descuento Festivo General)")
        str_lit.info("💡 Este descuento aplica automáticamente a **todos los productos y variantes** exclusivamente para la **Tienda Web** (WhatsApp, Correo, Paymentez) durante el tiempo de validez configurado. No afecta ventas físicas manuales ni planes acumulativos.")

        campana_cfg = config.get("campana_festiva", {})
        activo_def = campana_cfg.get("activo", False)
        porcentaje_def = float(campana_cfg.get("porcentaje", 0.0))
        nombre_def = campana_cfg.get("nombre", "Campaña Festiva")
        
        try:
            f_ini_def = datetime.fromisoformat(campana_cfg.get("fecha_inicio")).date() if campana_cfg.get("fecha_inicio") else datetime.now(ZoneInfo("America/Guayaquil")).date()
            h_ini_def = datetime.fromisoformat(campana_cfg.get("fecha_inicio")).time() if campana_cfg.get("fecha_inicio") else time(0, 0)
        except Exception:
            f_ini_def = datetime.now(ZoneInfo("America/Guayaquil")).date()
            h_ini_def = time(0, 0)

        try:
            f_fin_def = datetime.fromisoformat(campana_cfg.get("fecha_fin")).date() if campana_cfg.get("fecha_fin") else datetime.now(ZoneInfo("America/Guayaquil")).date()
            h_fin_def = datetime.fromisoformat(campana_cfg.get("fecha_fin")).time() if campana_cfg.get("fecha_fin") else time(23, 59)
        except Exception:
            f_fin_def = datetime.now(ZoneInfo("America/Guayaquil")).date()
            h_fin_def = time(23, 59)

        with str_lit.form("form_campana_festiva"):
            activar_campana = str_lit.checkbox("🟢 Activar Campaña Masiva Web", value=activo_def)
            nombre_campana = str_lit.text_input("Nombre / Motivo de la Campaña", value=nombre_def, placeholder="Ej: San Valentín / Black Friday")
            porcentaje_campana = str_lit.number_input("Porcentaje de Descuento (%)", min_value=0.0, max_value=100.0, value=porcentaje_def, step=1.0)
            
            str_lit.markdown("---")
            str_lit.markdown("##### ⏱️ Tiempo de Validez (Zona Horaria Ecuador)")
            
            col_fi, col_ff = str_lit.columns(2)
            with col_fi:
                fecha_inicio = str_lit.date_input("Fecha de Inicio", value=f_ini_def)
                hora_inicio = str_lit.time_input("Hora de Inicio", value=h_ini_def)
            with col_ff:
                fecha_fin = str_lit.date_input("Fecha de Fin", value=f_fin_def)
                hora_fin = str_lit.time_input("Hora de Fin", value=h_fin_def)

            subm_campana = str_lit.form_submit_button("💾 Guardar y Aplicar Campaña Web", use_container_width=True)
            
            if subm_campana:
                dt_inicio = datetime.combine(fecha_inicio, hora_inicio).isoformat()
                dt_fin = datetime.combine(fecha_fin, hora_fin).isoformat()
                
                payload_campana = {
                    "activo": activar_campana,
                    "nombre": nombre_campana,
                    "porcentaje": porcentaje_campana,
                    "fecha_inicio": dt_inicio,
                    "fecha_fin": dt_fin
                }
                
                if guardar_seccion_db("campana_festiva", payload_campana):
                    str_lit.success("✅ ¡Campaña Masiva Web configurada y guardada exitosamente!")
                    str_lit.rerun()

    # --- ANÁLISIS Y REPORTE DE CAMPAÑA WEB ---
    with tab_analisis:
        str_lit.subheader("📊 Análisis de Campaña Web e Ítems Más Vendidos")
        str_lit.markdown("Consulta el rendimiento financiero de cualquier campaña o período festivo web, desglosado por productos más vendidos y por factura.")

        col_f1, col_f2 = str_lit.columns(2)
        with col_f1:
            filtro_f_ini = str_lit.date_input("Fecha Inicio Análisis", value=datetime.now(ZoneInfo("America/Guayaquil")).date(), key="rep_f_ini")
        with col_f2:
            filtro_f_fin = str_lit.date_input("Fecha Fin Análisis", value=datetime.now(ZoneInfo("America/Guayaquil")).date(), key="rep_f_fin")

        if str_lit.button("🔍 Generar Reporte Completo de Campaña", type="primary", use_container_width=True):
            try:
                db_ses = SessionLocal()
                from database import Factura, MovimientoInventario, VarianteProducto
                
                facturas_web = db_ses.query(Factura).filter(
                    Factura.tipo_factura.like("VENTA WEB%"),
                    Factura.fecha_factura >= filtro_f_ini,
                    Factura.fecha_factura <= filtro_f_fin
                ).all()

                if facturas_web:
                    numeros_facturas = [f.numero_factura for f in facturas_web]
                    total_recaudado = sum(float(f.total_factura or 0.0) for f in facturas_web)
                    cantidad_pedidos = len(facturas_web)
                    ticket_promedio = total_recaudado / cantidad_pedidos if cantidad_pedidos > 0 else 0.0

                    movimientos = db_ses.query(MovimientoInventario).filter(
                        MovimientoInventario.referencia_factura.in_(numeros_facturas),
                        MovimientoInventario.tipo_movimiento == "VENTA"
                    ).all()

                    conteo_items = {}
                    for m in movimientos:
                        sku_item = m.sku
                        cant_vendida = abs(m.cantidad)
                        monto_item = float(m.valor_neto or 0.0)

                        if sku_item not in conteo_items:
                            conteo_items[sku_item] = {
                                "unidades": 0,
                                "total_recaudado": 0.0
                            }
                        conteo_items[sku_item]["unidades"] += cant_vendida
                        conteo_items[sku_item]["total_recaudado"] += monto_item

                    data_items = []
                    total_unidades_todas = 0
                    for sku_k, info in conteo_items.items():
                        total_unidades_todas += info["unidades"]
                        var_db = db_ses.query(VarianteProducto).filter(VarianteProducto.sku == sku_k).first()
                        if var_db and var_db.producto:
                            prod_nombre = var_db.producto.nombre
                            prod_cat = var_db.producto.categoria
                            talla_col = f"{var_db.talla} / {var_db.color}"
                        else:
                            prod_nombre = sku_k
                            prod_cat = "N/D"
                            talla_col = "N/D"

                        data_items.append({
                            "SKU": sku_k,
                            "Producto": prod_nombre,
                            "Categoría": prod_cat,
                            "Talla / Color": talla_col,
                            "Unidades Vendidas": info["unidades"],
                            "Total Ingresos ($)": round(info["total_recaudado"], 2)
                        })

                    db_ses.close()

                    m1, m2, m3, m4 = str_lit.columns(4)
                    m1.metric("💰 Total Vendido", f"${total_recaudado:,.2f}")
                    m2.metric("📦 Total Pedidos Web", cantidad_pedidos)
                    m3.metric("🔥 Prendas Vendidas", total_unidades_todas)
                    m4.metric("📈 Ticket Promedio", f"${ticket_promedio:,.2f}")

                    str_lit.divider()
                    
                    str_lit.markdown("##### 🏆 Ranking de Ítems / Prendas Más Vendidos")
                    df_items = pd.DataFrame(data_items)
                    if not df_items.empty:
                        df_items = df_items.sort_values(by="Unidades Vendidas", ascending=False)
                        str_lit.dataframe(
                            df_items, 
                            use_container_width=True, 
                            hide_index=True,
                            column_config={
                                "Total Ingresos ($)": str_lit.column_config.NumberColumn(format="$ %.2f")
                            }
                        )

                    str_lit.divider()

                    str_lit.markdown("##### 📋 Registro Detallado por Factura")
                    data_detalle = []
                    for f in facturas_web:
                        data_detalle.append({
                            "Factura": f.numero_factura,
                            "Fecha": str(f.fecha_factura),
                            "Cliente": f.entidad_nombre,
                            "RUC / Cédula": f.entidad_ruc,
                            "Canal / Tipo": f.tipo_factura,
                            "Total ($)": float(f.total_factura or 0.0)
                        })

                    df_reporte = pd.DataFrame(data_detalle)
                    str_lit.dataframe(
                        df_reporte, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "Total ($)": str_lit.column_config.NumberColumn(format="$ %.2f")
                        }
                    )
                else:
                    db_ses.close()
                    str_lit.warning("⚠️ No se encontraron ventas web registradas en el rango de fechas seleccionado.")

            except Exception as err_rep:
                str_lit.error(f"❌ Error al generar el reporte: {err_rep}")