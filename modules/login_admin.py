import streamlit as st
from database import SessionLocal, Usuario

def render_login_admin():
    st.markdown("<h2 style='text-align: center; color: #1e293b;'>🛍️ Fajas Isabella</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #64748b;'>Acceso al Panel Administrativo</h4>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        opcion = st.radio(
            "Seleccione una opción:",
            ["Iniciar Sesión", "Registrar Usuario", "Olvidé mi Contraseña"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.markdown("---")

        db = SessionLocal()

        # --- 1. INICIAR SESIÓN ---
        if opcion == "Iniciar Sesión":
            with st.form("form_login_admin"):
                usuario_input = st.text_input("Usuario o Correo")
                password_input = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("Ingresar al Panel", use_container_width=True)
                
                if submit:
                    user = db.query(Usuario).filter(
                        ((Usuario.username == usuario_input) | (Usuario.email == usuario_input)),
                        Usuario.password == password_input,
                        Usuario.activo == True
                    ).first()
                    
                    if user:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_actual"] = user.username
                        st.session_state["rol_actual"] = user.rol
                        st.success(f"¡Bienvenido {user.username} ({user.rol})!")
                        db.close()
                        st.rerun()
                    else:
                        st.error("Credenciales inválidas, usuario desactivado o no registrado.")

        # --- 2. REGISTRAR USUARIO ADMINISTRATIVO ---
        elif opcion == "Registrar Usuario":
            with st.form("form_registro_admin"):
                nuevo_user = st.text_input("Nombre de Usuario")
                nuevo_email = st.text_input("Correo Electrónico")
                nuevo_pass = st.text_input("Contraseña", type="password")
                nuevo_rol = st.selectbox("Rol Asignado", ["Administrador", "Ventas", "Despacho"])
                submit_reg = st.form_submit_button("Registrar Usuario Panel", use_container_width=True)
                
                if submit_reg:
                    if nuevo_user and nuevo_email and nuevo_pass:
                        user_existente = db.query(Usuario).filter(
                            (Usuario.username == nuevo_user) | (Usuario.email == nuevo_email)
                        ).first()

                        if user_existente:
                            st.warning("El nombre de usuario o correo ya se encuentra registrado.")
                        else:
                            nuevo_usuario = Usuario(
                                username=nuevo_user,
                                email=nuevo_email,
                                password=nuevo_pass,
                                rol=nuevo_rol
                            )
                            db.add(nuevo_usuario)
                            db.commit()
                            st.success(f"¡Usuario `{nuevo_user}` registrado con éxito como `{nuevo_rol}`! Ya puede iniciar sesión.")
                    else:
                        st.warning("Por favor completa todos los campos.")

        # --- 3. RECUPERAR CONTRASEÑA ---
        elif opcion == "Olvidé mi Contraseña":
            with st.form("form_recuperar_admin"):
                email_rec = st.text_input("Correo Electrónico Registrado")
                submit_rec = st.form_submit_button("Enviar Instrucciones", use_container_width=True)
                
                if submit_rec:
                    if email_rec:
                        user = db.query(Usuario).filter(Usuario.email == email_rec).first()
                        if user:
                            st.success(f"📩 Instrucciones de restablecimiento enviadas a `{user.email}`.")
                        else:
                            st.error("No existe ningún usuario registrado con ese correo.")
                    else:
                        st.warning("Ingresa un correo válido.")

        db.close()