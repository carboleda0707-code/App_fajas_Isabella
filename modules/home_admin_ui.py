import streamlit as str_lit
import os
import requests
from database import SessionLocal, ConfiguracionWeb
import cloudinary.uploader

# URL base de la API (detecta si está en Railway o en local)
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

DEFAULT_EMBED = '<blockquote class="instagram-media" data-instgrm-captioned data-instgrm-permalink="https://www.instagram.com/reel/DQIK9pLDl4l/?utm_source=ig_embed&amp;utm_campaign=loading" data-instgrm-version="14" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:540px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"><div style="padding:16px;"> <a href="https://www.instagram.com/reel/DQIK9pLDl4l/?utm_source=ig_embed&amp;utm_campaign=loading" style=" background:#FFFFFF; line-height:0; padding:0 0; text-align:center; text-decoration:none; width:100%;" target="_blank"> <div style=" display: flex; flex-direction: row; align-items: center;"> <div style="background-color: #F4F4F4; border-radius: 50%; flex-grow: 0; height: 40px; margin-right: 14px; width: 40px;"></div> <div style="display: flex; flex-direction: column; flex-grow: 1; justify-content: center;"> <div style=" background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; margin-bottom: 6px; width: 100px;"></div> <div style=" background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; width: 60px;"></div></div></div><div style="padding: 19% 0;"></div> <div style="display:block; height:50px; margin:0 auto 12px; width:50px;"></div><div style="padding-top: 8px;"> <div style=" color:#3897f0; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:550; line-height:18px;">Ver esta publicación en Instagram</div></div><div style="padding: 12.5% 0;"></div></div></a><p style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; line-height:17px; margin-bottom:0; margin-top:8px; overflow:hidden; padding:8px 0 7px; text-align:center; text-overflow:ellipsis; white-space:nowrap;"><a href="https://www.instagram.com/reel/DQIK9pLDl4l/?utm_source=ig_embed&amp;utm_campaign=loading" style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:normal; line-height:17px; text-decoration:none;" target="_blank">Una publicación compartida de FAJAS ISABELLA (@fajasisabella.ec)</a></p></div></blockquote>'

def cargar_config_db():
    """Consulta las secciones almacenadas en PostgreSQL mediante el ORM."""
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
    """Guarda o actualiza el JSONB de una sección directamente en PostgreSQL."""
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
    str_lit.markdown("### 🌐 Panel de Gestión del Home Web (PostgreSQL)")
    str_lit.markdown("Actualiza el contenido multimedia, los textos y los enlaces dinámicos de tu tienda online directamente en la base de datos.")

    tab0, tab1, tab2, tab3 = str_lit.tabs(["🖼️ Sección 0.5: Banner Slider", "📌 Sección 1: Historia", "💬 Sección 2: Testimonios / En Vivo", "📢 Sección 3: Publicidad (3 Cols)"])

    config = cargar_config_db()

    # --- SECCIÓN 0.5: BANNER SLIDER ---
    with tab0:
        str_lit.subheader("Administrar Sección 0.5 (Banner Slider Rotativo - 4 Diapositivas)")
        str_lit.info("Configura las 4 imágenes, etiquetas, títulos y descripciones del banner principal que rota cada 2 segundos.")
        
        with str_lit.form("form_sec05"):
            sec05_cfg = config.get("sec05", {})
            
            slides_data = []
            for i in range(1, 5):
                str_lit.markdown(f"---")
                str_lit.markdown(f"#### 🖼️ Diapositiva (Slide) {i}")
                s_cfg = sec05_cfg.get(f"slide{i}", {})
                
                archivo_slide = str_lit.file_uploader(f"Subir Imagen Slide {i} (.jpg/.png)", type=["jpg", "jpeg", "png"], key=f"up_slide_{i}")
                s_tag = str_lit.text_input(f"Etiqueta / Badge {i}", value=s_cfg.get("tag", f"Colección {i}"))
                s_titulo = str_lit.text_input(f"Título Principal {i}", value=s_cfg.get("titulo", f"Título de Ejemplo {i}"))
                s_desc = str_lit.text_area(f"Descripción {i}", value=s_cfg.get("descripcion", f"Descripción de la diapositiva {i}..."))
                s_btn = str_lit.text_input(f"Texto del Botón {i}", value=s_cfg.get("btn_texto", "Ver Colección →"))
                
                slides_data.append({
                    "file_uploader": archivo_slide,
                    "tag": s_tag,
                    "titulo": s_titulo,
                    "descripcion": s_desc,
                    "btn_texto": s_btn,
                    "imagen_actual": s_cfg.get("imagen", "")
                })

            subm_sec05 = str_lit.form_submit_button("💾 Guardar Cambios de Sección 0.5 en BD", use_container_width=True)
            
            if subm_sec05:
                payload_sec05 = {}
                
                for idx, data in enumerate(slides_data, start=1):
                    img_url = data["imagen_actual"]
                    archivo_subido = data["file_uploader"]
                    
                    if archivo_subido is not None:
                        try:
                            bytes_data = archivo_subido.getvalue()
                            resultado = cloudinary.uploader.upload(bytes_data, folder="fajas_isabella/home/slider", resource_type="auto")
                            url_nube = resultado.get("secure_url")
                            if url_nube:
                                img_url = url_nube
                        except Exception as e:
                            str_lit.warning(f"No se pudo subir a Cloudinary (Slide {idx}): {e}")
                    
                    payload_sec05[f"slide{idx}"] = {
                        "tag": data["tag"],
                        "titulo": data["titulo"],
                        "descripcion": data["descripcion"],
                        "btn_texto": data["btn_texto"],
                        "imagen": img_url
                    }
                
                if guardar_seccion_db("sec05", payload_sec05):
                    str_lit.success("✅ ¡Sección 0.5 subida a Cloudinary y guardada con éxito en PostgreSQL!")

    # --- SECCIÓN 1: HISTORIA ---
    with tab1:
        str_lit.subheader("Administrar Sección 1 (Historia, Imagen/Video y Textos)")
        with str_lit.form("form_sec1"):
            str_lit.info("Sube la imagen o video del lado izquierdo (se subirá a Cloudinary) y personaliza los textos.")
            
            archivo_sec1 = str_lit.file_uploader("Subir Archivo Multimedia (Imagen .jpg/.png o Video .mp4)", type=["jpg", "jpeg", "png", "mp4"], key="up_sec1")
            
            str_lit.markdown("---")
            str_lit.markdown("#### Textos de la Columna Derecha")
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
                        bytes_data = archivo_sec1.getvalue()
                        resultado = cloudinary.uploader.upload(bytes_data, folder="fajas_isabella/home/historia", resource_type="auto")
                        url_nube = resultado.get("secure_url")
                        if url_nube:
                            multimedia_url = url_nube
                            str_lit.success("✅ Archivo multimedia subido exitosamente a Cloudinary.")
                    except Exception as e:
                        str_lit.warning(f"Error al subir multimedia a Cloudinary: {e}")
                
                payload_sec1 = {
                    "titulo": nuevo_titulo,
                    "subtitulo": nuevo_subtitulo,
                    "parrafo1": nuevo_p1,
                    "parrafo2": nuevo_p2,
                    "parrafo3": nuevo_p3,
                    "multimedia": multimedia_url
                }
                
                if guardar_seccion_db("sec1", payload_sec1):
                    str_lit.success("✅ ¡Sección 1 guardada con éxito en PostgreSQL!")

    # --- SECCIÓN 2: REDES ---
    with tab2:
        str_lit.subheader("Administrar Sección 2 (Comunidad y Confianza - En Vivo / Redes)")
        with str_lit.form("form_sec2"):
            str_lit.info("Pega aquí el código HTML completo de inserción (Blockquote) de Instagram y la URL de TikTok.")
            
            sec2_cfg = config.get("sec2", {})
            
            str_lit.markdown("#### 📸 Código de Inserción (Embed HTML) de Instagram")
            nuevo_ig_embed = str_lit.text_area("Código HTML del Post/Reel de Instagram", value=sec2_cfg.get("instagram_embed", DEFAULT_EMBED), height=150)

            str_lit.markdown("---")
            str_lit.markdown("#### 🎵 Enlace de TikTok Live")
            nuevo_tk_url = str_lit.text_input("URL / Enlace de TikTok Live", value=sec2_cfg.get("tiktok_url", "https://tiktok.com"))

            subm_sec2 = str_lit.form_submit_button("💾 Guardar Cambios de Sección 2 en BD", use_container_width=True)
            if subm_sec2:
                payload_sec2 = {
                    "instagram_embed": nuevo_ig_embed,
                    "tiktok_url": nuevo_tk_url
                }
                if guardar_seccion_db("sec2", payload_sec2):
                    str_lit.success("✅ ¡Sección 2 guardada con éxito en PostgreSQL!")

    # --- SECCIÓN 3: PUBLICIDAD ---
    with tab3:
        str_lit.subheader("Administrar Sección 3 (Publicidad - Imágenes/Videos y Textos)")
        with str_lit.form("form_sec3"):
            str_lit.info("Sube multimedia (se almacenará de forma segura en Cloudinary) y personaliza las tarjetas publicitarias.")
            
            sec3_cfg = config.get("sec3", {})

            # Tarjeta 1
            str_lit.markdown("---")
            str_lit.markdown("#### 🔹 Publicidad 1")
            p1_cfg = sec3_cfg.get("card1", {})
            p1_file = str_lit.file_uploader("Imagen/Video Publi 1", type=["jpg", "jpeg", "png", "mp4"], key="pub_1")
            p1_tag = str_lit.text_input("Tag Publi 1", value=p1_cfg.get("tag", "PUBLICIDAD 1"))
            p1_title = str_lit.text_input("Título Publi 1", value=p1_cfg.get("titulo", ""))
            p1_desc = str_lit.text_area("Descripción Publi 1", value=p1_cfg.get("descripcion", ""))
            p1_link = str_lit.text_input("Texto Enlace Publi 1", value=p1_cfg.get("link_texto", "Ver Colección →"))

            # Tarjeta 2
            str_lit.markdown("---")
            str_lit.markdown("#### 🔹 Publicidad 2")
            p2_cfg = sec3_cfg.get("card2", {})
            p2_file = str_lit.file_uploader("Imagen/Video Publi 2", type=["jpg", "jpeg", "png", "mp4"], key="pub_2")
            p2_tag = str_lit.text_input("Tag Publi 2", value=p2_cfg.get("tag", "PUBLICIDAD 2"))
            p2_title = str_lit.text_input("Título Publi 2", value=p2_cfg.get("titulo", ""))
            p2_desc = str_lit.text_area("Descripción Publi 2", value=p2_cfg.get("descripcion", ""))
            p2_link = str_lit.text_input("Texto Enlace Publi 2", value=p2_cfg.get("link_texto", "Ver Modelos →"))

            # Tarjeta 3
            str_lit.markdown("---")
            str_lit.markdown("#### 🔹 Publicidad 3")
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
                    str_lit.success("✅ ¡Sección 3 subida a Cloudinary y guardada con éxito en PostgreSQL!")