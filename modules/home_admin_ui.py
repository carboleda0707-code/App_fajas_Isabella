import streamlit as st
import os
import json
import re

JS_FILE = "web/home.js"

DEFAULT_EMBED = '<blockquote class="instagram-media" data-instgrm-captioned data-instgrm-permalink="https://www.instagram.com/reel/DQIK9pLDl4l/?utm_source=ig_embed&amp;utm_campaign=loading" data-instgrm-version="14" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:540px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"><div style="padding:16px;"> <a href="https://www.instagram.com/reel/DQIK9pLDl4l/?utm_source=ig_embed&amp;utm_campaign=loading" style=" background:#FFFFFF; line-height:0; padding:0 0; text-align:center; text-decoration:none; width:100%;" target="_blank"> <div style=" display: flex; flex-direction: row; align-items: center;"> <div style="background-color: #F4F4F4; border-radius: 50%; flex-grow: 0; height: 40px; margin-right: 14px; width: 40px;"></div> <div style="display: flex; flex-direction: column; flex-grow: 1; justify-content: center;"> <div style=" background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; margin-bottom: 6px; width: 100px;"></div> <div style=" background-color: #F4F4F4; border-radius: 4px; flex-grow: 0; height: 14px; width: 60px;"></div></div></div><div style="padding: 19% 0;"></div> <div style="display:block; height:50px; margin:0 auto 12px; width:50px;"></div><div style="padding-top: 8px;"> <div style=" color:#3897f0; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:550; line-height:18px;">Ver esta publicación in Instagram</div></div><div style="padding: 12.5% 0;"></div></div></a><p style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; line-height:17px; margin-bottom:0; margin-top:8px; overflow:hidden; padding:8px 0 7px; text-align:center; text-overflow:ellipsis; white-space:nowrap;"><a href="https://www.instagram.com/reel/DQIK9pLDl4l/?utm_source=ig_embed&amp;utm_campaign=loading" style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:normal; line-height:17px; text-decoration:none;" target="_blank">Una publicación compartida de FAJAS ISABELLA (@fajasisabella.ec)</a></p></div></blockquote>'

def cargar_config():
    default_data = {
        "sec1": {
            "titulo": "HISTORIA",
            "subtitulo": "12 AÑOS RESALTANDO TU BELLEZA",
            "parrafo1": "Fajas Isabella empezó vendiendo desde la sala de su casa, con la convicción de que toda mujer merece sentirse segura y hermosa en su cuerpo.",
            "parrafo2": "Hoy somos un equipo que fabrica directamente fajas colombianas, con ventas al por mayor y al por menor, y más de 80 modelos entre fajas látex reductoras, fajas postoperatorias, cinturillas y accesorios.",
            "parrafo3": "Nuestra marca está registrada ante el SENADI como \"FAJAS Isabella RESALTA TU BELLEZA\", un respaldo de la calidad y la confianza que nos han dado nuestras clientas.",
            "multimedia": "banner_historia.mp4"
        },
        "sec2": {
            "instagram_embed": DEFAULT_EMBED,
            "tiktok_url": "https://tiktok.com"
        },
        "sec3": {
            "card1": {"tag": "PUBLICIDAD 1", "titulo": "Moldeadoras de Alta Compresión", "descripcion": "Control total y definición perfecta para uso diario.", "link_texto": "Ver Colección →"},
            "card2": {"tag": "PUBLICIDAD 2", "titulo": "Confort y Recuperación Segura", "descripcion": "Diseñadas por expertos para garantizar tu bienestar.", "link_texto": "Ver Modelos →"},
            "card3": {"tag": "PUBLICIDAD 3", "titulo": "Reduce Medidas al Instante", "descripcion": "Moldea tu cintura con máxima comodidad.", "link_texto": "Descubrir →"}
        }
    }

    if os.path.exists(JS_FILE):
        try:
            with open(JS_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                match = re.search(r"const\s+homeConfig\s*=\s*(\{.*?\});\s*(?:\n|window\.inicializarHome)", content, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    return json.loads(json_str)
        except Exception:
            pass
    return default_data

def guardar_config(data):
    os.makedirs("web", exist_ok=True)
    json_config_str = json.dumps(data, ensure_ascii=False, indent=4)
    
    if os.path.exists(JS_FILE):
        with open(JS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        nuevo_contenido = re.sub(
            r"const\s+homeConfig\s*=\s*\{.*?\};",
            f"const homeConfig = {json_config_str};",
            content,
            flags=re.DOTALL
        )
        
        with open(JS_FILE, "w", encoding="utf-8") as f:
            f.write(nuevo_contenido)

def render_home_admin():
    st.markdown("### 🌐 Panel de Gestión del Home Web")
    st.markdown("Actualiza el contenido multimedia y los enlaces dinámicos de las secciones de la tienda online.")

    tab1, tab2, tab3 = st.tabs(["📌 Sección 1: Historia", "💬 Sección 2: Testimonios / En Vivo", "📢 Sección 3: Publicidad (3 Cols)"])

    config = cargar_config()

    # --- SECCIÓN 1 ---
    with tab1:
        st.subheader("Administrar Sección 1 (Historia, Imagen/Video y Textos)")
        with st.form("form_sec1"):
            st.info("Sube la imagen o video del lado izquierdo y personaliza los textos del lado derecho.")
            
            archivo_sec1 = st.file_uploader("Subir Archivo Multimedia (Imagen .jpg/.png o Video .mp4)", type=["jpg", "jpeg", "png", "mp4"], key="up_sec1")
            
            st.markdown("---")
            st.markdown("#### Textos de la Columna Derecha")
            sec1_cfg = config.get("sec1", {})
            nuevo_titulo = st.text_input("Título Principal", value=sec1_cfg.get("titulo", "HISTORIA"))
            nuevo_subtitulo = st.text_input("Subtítulo", value=sec1_cfg.get("subtitulo", "12 AÑOS RESALTANDO TU BELLEZA"))
            
            nuevo_p1 = st.text_area("Párrafo 1", value=sec1_cfg.get("parrafo1", ""))
            nuevo_p2 = st.text_area("Párrafo 2", value=sec1_cfg.get("parrafo2", ""))
            nuevo_p3 = st.text_area("Párrafo 3 (Se mostrará resaltado)", value=sec1_cfg.get("parrafo3", ""))

            subm_sec1 = st.form_submit_button("💾 Guardar Cambios de Sección 1", use_container_width=True)
            
            if subm_sec1:
                multimedia_actual = sec1_cfg.get("multimedia", "banner_historia.jpg")
                if archivo_sec1 is not None:
                    ext = archivo_sec1.name.split('.')[-1].lower()
                    nombre_archivo = "banner_historia.mp4" if ext == "mp4" else "banner_historia.jpg"
                    ruta_destino = os.path.join("web/img", nombre_archivo)
                    with open(ruta_destino, "wb") as f:
                        f.write(archivo_sec1.getbuffer())
                    st.success(f"✅ Archivo multimedia {nombre_archivo} guardado con éxito.")
                else:
                    nombre_archivo = multimedia_actual
                
                config["sec1"] = {
                    "titulo": nuevo_titulo,
                    "subtitulo": nuevo_subtitulo,
                    "parrafo1": nuevo_p1,
                    "parrafo2": nuevo_p2,
                    "parrafo3": nuevo_p3,
                    "multimedia": nombre_archivo
                }
                guardar_config(config)
                st.success("✅ ¡Sección 1 actualizada correctamente!")

    # --- SECCIÓN 2 ---
    with tab2:
        st.subheader("Administrar Sección 2 (Comunidad y Confianza - En Vivo / Redes)")
        with st.form("form_sec2"):
            st.info("Pega aquí el código HTML completo de inserción (Blockquote) que te da Instagram para tu Reel o Post.")
            
            sec2_cfg = config.get("sec2", {})
            
            st.markdown("#### 📸 Código de Inserción (Embed HTML) de Instagram")
            nuevo_ig_embed = st.text_area("Código HTML del Post/Reel de Instagram", value=sec2_cfg.get("instagram_embed", DEFAULT_EMBED), height=150)

            st.markdown("---")
            st.markdown("#### 🎵 Enlace de TikTok Live")
            nuevo_tk_url = st.text_input("URL / Enlace de TikTok Live", value=sec2_cfg.get("tiktok_url", "https://tiktok.com"))

            subm_sec2 = st.form_submit_button("💾 Guardar Cambios de Sección 2", use_container_width=True)
            if subm_sec2:
                config["sec2"] = {
                    "instagram_embed": nuevo_ig_embed,
                    "tiktok_url": nuevo_tk_url
                }
                guardar_config(config)
                st.success("✅ ¡Sección 2 actualizada con éxito!")

    # --- SECCIÓN 3 ---
    with tab3:
        st.subheader("Administrar Sección 3 (Publicidad 1, 2 y 3 - Imágenes y Textos)")
        with st.form("form_sec3"):
            st.info("Sube imágenes/videos y personaliza los textos de cada tarjeta publicitaria.")
            
            sec3_cfg = config.get("sec3", {})

            st.markdown("---")
            st.markdown("#### 🔹 Publicidad 1")
            p1_file = st.file_uploader("Imagen/Video Publi 1", type=["jpg", "jpeg", "png", "mp4"], key="pub_1")
            p1_tag = st.text_input("Tag Publi 1", value=sec3_cfg.get("card1", {}).get("tag", "PUBLICIDAD 1"))
            p1_title = st.text_input("Título Publi 1", value=sec3_cfg.get("card1", {}).get("titulo", ""))
            p1_desc = st.text_area("Descripción Publi 1", value=sec3_cfg.get("card1", {}).get("descripcion", ""))
            p1_link = st.text_input("Texto Enlace Publi 1", value=sec3_cfg.get("card1", {}).get("link_texto", "Ver Colección →"))

            st.markdown("---")
            st.markdown("#### 🔹 Publicidad 2")
            p2_file = st.file_uploader("Imagen/Video Publi 2", type=["jpg", "jpeg", "png", "mp4"], key="pub_2")
            p2_tag = st.text_input("Tag Publi 2", value=sec3_cfg.get("card2", {}).get("tag", "PUBLICIDAD 2"))
            p2_title = st.text_input("Título Publi 2", value=sec3_cfg.get("card2", {}).get("titulo", ""))
            p2_desc = st.text_area("Descripción Publi 2", value=sec3_cfg.get("card2", {}).get("descripcion", ""))
            p2_link = st.text_input("Texto Enlace Publi 2", value=sec3_cfg.get("card2", {}).get("link_texto", "Ver Modelos →"))

            st.markdown("---")
            st.markdown("#### 🔹 Publicidad 3")
            p3_file = st.file_uploader("Imagen/Video Publi 3", type=["jpg", "jpeg", "png", "mp4"], key="pub_3")
            p3_tag = st.text_input("Tag Publi 3", value=sec3_cfg.get("card3", {}).get("tag", "PUBLICIDAD 3"))
            p3_title = st.text_input("Título Publi 3", value=sec3_cfg.get("card3", {}).get("titulo", ""))
            p3_desc = st.text_area("Descripción Publi 3", value=sec3_cfg.get("card3", {}).get("descripcion", ""))
            p3_link = st.text_input("Texto Enlace Publi 3", value=sec3_cfg.get("card3", {}).get("link_texto", "Descubrir →"))

            subm_sec3 = st.form_submit_button("💾 Guardar Cambios de Sección 3", use_container_width=True)
            if subm_sec3:
                if p1_file is not None:
                    ext = p1_file.name.split('.')[-1].lower()
                    nombre = "publi_1.mp4" if ext == "mp4" else "publi_1.jpg"
                    with open(os.path.join("web/img", nombre), "wb") as f:
                        f.write(p1_file.getbuffer())
                if p2_file is not None:
                    ext = p2_file.name.split('.')[-1].lower()
                    nombre = "publi_2.mp4" if ext == "mp4" else "publi_2.jpg"
                    with open(os.path.join("web/img", nombre), "wb") as f:
                        f.write(p2_file.getbuffer())
                if p3_file is not None:
                    ext = p3_file.name.split('.')[-1].lower()
                    nombre = "publi_3.mp4" if ext == "mp4" else "publi_3.jpg"
                    # CORREGIDO EL ERROR DE SINTAXIS AQUÍ:
                    with open(os.path.join("web/img", nombre), "wb") as f:
                        f.write(p3_file.getbuffer())

                config["sec3"] = {
                    "card1": {"tag": p1_tag, "titulo": p1_title, "descripcion": p1_desc, "link_texto": p1_link},
                    "card2": {"tag": p2_tag, "titulo": p2_title, "descripcion": p2_desc, "link_texto": p2_link},
                    "card3": {"tag": p3_tag, "titulo": p3_title, "descripcion": p3_desc, "link_texto": p3_link}
                }
                guardar_config(config)
                st.success("✅ ¡Sección 3 actualizada con éxito!")