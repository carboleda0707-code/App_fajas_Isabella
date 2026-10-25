import streamlit as st
from database import SessionLocal, Usuario
from datetime import datetime
import hashlib

def cifrar_password(password: str) -> str:
    """Convierte una contraseña en texto plano a un Hash SHA-256 seguro."""
    if not password:
        return ""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def inicializar_usuario_admin_por_defecto(db):
    """
    Crea el usuario superadministrador inicial por defecto si la base de datos no tiene usuarios.
    Credenciales oficiales: admin / FajasIsabella2026* (Guardado con Hash SHA-256)
    """
    try:
        total_usuarios = db.query(Usuario).count()
        if total_usuarios == 0:
            admin_defecto = Usuario(
                username="admin",
                email="admin@fajasisabella.com",
                password=cifrar_password("FajasIsabella2026*"),
                rol="Administrador",
                activo=True,
                fecha_creacion=datetime.now(),
                fecha_actualizacion=datetime.now()
            )
            db.add(admin_defecto)
            db.commit()
            st.toast("⚙️ Usuario Administrador inicial verificado y cifrado.", icon="🔐")
    except Exception as e:
        db.rollback()


def render_login_admin():
    st.markdown("<h2 style='text-align: center; color: #1e293b;'>🛍️ Fajas Isabella</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #64748b;'>Acceso al Panel Administrativo</h4>", unsafe_allow_html=True)
    
    db = SessionLocal()
    
    # 1. Asegurar existencia de usuario Admin Inicial si la base de datos está vacía
    inicializar_usuario_admin_por_defecto(db)

    # --- PANTALLA PRINCIPAL DE LOGIN Y ADMINISTRACIÓN ---
    col1, col2, col3 = st.columns([1, 2.5, 1])
    with col2:
        opcion = st.radio(
            "Seleccione una opción:",
            ["Iniciar Sesión", "Registrar Usuario", "🔑 Cambiar Contraseña", "⚙️ Administrar Roles"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.markdown("---")

        # --- 1. INICIAR SESIÓN ---
        if opcion == "Iniciar Sesión":
            with st.form("form_login_admin"):
                usuario_input = st.text_input("Usuario o Correo").strip()
                password_input = st.text_input("Contraseña", type="password").strip()
                submit = st.form_submit_button("Ingresar al Panel", use_container_width=True)
                
                if submit:
                    pass_hash = cifrar_password(password_input)
                    user = db.query(Usuario).filter(
                        ((Usuario.username == usuario_input) | (Usuario.email == usuario_input)),
                        Usuario.password == pass_hash,
                        Usuario.activo == True
                    ).first()
                    
                    if user:
                        roles_str = str(user.rol).upper()
                        if "PENDIENTE" in roles_str and roles_str == "PENDIENTE":
                            st.warning("⏳ Tu cuenta se encuentra **PENDIENTE** de aprobación por un Administrador. Por favor contacte al Administrador para que asigne sus roles de trabajo.")
                        else:
                            st.session_state["autenticado"] = True
                            st.session_state["usuario_actual"] = user.username
                            st.session_state["rol_actual"] = user.rol
                            st.success(f"¡Bienvenido {user.username} ({user.rol})!")
                            db.close()
                            st.rerun()
                    else:
                        st.error("Credenciales inválidas, usuario desactivado o no registrado.")

        # --- 2. REGISTRAR USUARIO (ROL PENDIENTE POR DEFECTO + CONTRASEÑA CIFRADA) ---
        elif opcion == "Registrar Usuario":
            with st.form("form_registro_admin"):
                nuevo_user = st.text_input("Nombre de Usuario").strip()
                nuevo_email = st.text_input("Correo Electrónico").strip()
                nuevo_pass = st.text_input("Contraseña", type="password").strip()
                st.caption("ℹ️ *Todo nuevo registro se crea con estado **PENDIENTE**. Un Administrador deberá activar y asignar sus roles.*")
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
                                password=cifrar_password(nuevo_pass),
                                rol="PENDIENTE",
                                activo=True,
                                fecha_creacion=datetime.now(),
                                fecha_actualizacion=datetime.now()
                            )
                            db.add(nuevo_usuario)
                            db.commit()
                            st.success(f"¡Usuario `{nuevo_user}` registrado con éxito! Su cuenta quedó en estado **PENDIENTE** hasta que un Administrador asigne sus roles.")
                    else:
                        st.warning("Por favor completa todos los campos.")

        # --- 3. CAMBIAR / RENOVAR CONTRASEÑA ---
        elif opcion == "🔑 Cambiar Contraseña":
            st.subheader("🔑 Renovación de Credenciales")
            st.caption("Actualiza tu contraseña ingresando tus datos actuales y la nueva clave.")
            
            with st.form("form_renovar_pass"):
                user_renova = st.text_input("Usuario o Correo").strip()
                pass_actual = st.text_input("Contraseña Actual", type="password").strip()
                pass_nueva1 = st.text_input("Nueva Contraseña", type="password").strip()
                pass_nueva2 = st.text_input("Confirmar Nueva Contraseña", type="password").strip()
                submit_renova = st.form_submit_button("Actualizar Contraseña", type="primary", use_container_width=True)
                
                if submit_renova:
                    if not user_renova or not pass_actual or not pass_nueva1 or not pass_nueva2:
                        st.warning("⚠️ Por favor completa todos los campos.")
                    elif pass_nueva1 != pass_nueva2:
                        st.error("❌ Las nuevas contraseñas no coinciden.")
                    else:
                        pass_actual_hash = cifrar_password(pass_actual)
                        usuario_db = db.query(Usuario).filter(
                            ((Usuario.username == user_renova) | (Usuario.email == user_renova)),
                            Usuario.password == pass_actual_hash
                        ).first()
                        
                        if usuario_db:
                            usuario_db.password = cifrar_password(pass_nueva1)
                            usuario_db.fecha_actualizacion = datetime.now()
                            db.commit()
                            st.success("🎉 ¡Contraseña actualizada exitosamente! Ya puedes iniciar sesión con tu nueva clave.")
                        else:
                            st.error("⛔ Usuario, correo o contraseña actual incorrectos.")

        # --- 4. ADMINISTRAR ROLES Y USUARIOS (EXCLUSIVO ADMINISTRADORES) ---
        elif opcion == "⚙️ Administrar Roles":
            st.subheader("👥 Gestión de Usuarios y Permisos")
            st.caption("Aprueba usuarios nuevos, asigna múltiples roles operativos y renueva credenciales.")

            es_admin = False
            usuario_admin_logueado = None

            if st.session_state.get("autenticado") and str(st.session_state.get("rol_actual")).upper() == "ADMINISTRADOR":
                es_admin = True
                usuario_admin_logueado = st.session_state.get("usuario_actual")
            else:
                st.info("🔐 Ingrese credenciales de **Administrador** para gestionar los usuarios:")
                admin_user_input = st.text_input("Usuario / Correo Administrador", key="auth_admin_user").strip()
                admin_pass_input = st.text_input("Contraseña Administrador", type="password", key="auth_admin_pass").strip()
                
                if admin_user_input and admin_pass_input:
                    admin_pass_hash = cifrar_password(admin_pass_input)
                    admin_check = db.query(Usuario).filter(
                        ((Usuario.username == admin_user_input) | (Usuario.email == admin_user_input)),
                        Usuario.password == admin_pass_hash,
                        Usuario.activo == True
                    ).first()
                    
                    if admin_check and str(admin_check.rol).upper() == "ADMINISTRADOR":
                        es_admin = True
                        usuario_admin_logueado = admin_check.username
                    else:
                        st.error("⛔ Credenciales incorrectas o el usuario no posee rol de Administrador.")

            if es_admin:
                st.success("🔓 Sesión de Administrador verificada con éxito.")
                st.markdown("---")
                
                # Excluir al administrador actual para evitar bloqueos
                usuarios_lista = db.query(Usuario).filter(Usuario.username != usuario_admin_logueado).order_by(Usuario.id.asc()).all()
                
                if not usuarios_lista:
                    st.info("No hay otros usuarios registrados en el sistema para administrar.")
                else:
                    # 🟢 MÓDULOS OFICIALES ACTUALIZADOS (Sin Bodega)
                    roles_disponibles = ["Administrador", "Inventario", "Ventas", "Logística", "Compras"]
                    
                    st.markdown("##### 📋 Listado de Colaboradores y Permisos")
                    for u in usuarios_lista:
                        with st.container():
                            c_u1, c_u2, c_u3, c_u4 = st.columns([2, 2.2, 1, 1.2])
                            
                            with c_u1:
                                st.markdown(f"👤 **{u.username}**")
                                st.caption(f"Email: {u.email}")
                                if hasattr(u, "fecha_creacion") and u.fecha_creacion:
                                    st.caption(f"Creado: {u.fecha_creacion.strftime('%Y-%m-%d %H:%M')}")
                            
                            with c_u2:
                                roles_actuales = [r.strip() for r in str(u.rol).split(",")] if u.rol and u.rol != "PENDIENTE" else []
                                roles_actuales = [r for r in roles_actuales if r in roles_disponibles]
                                
                                nuevos_roles = st.multiselect(
                                    "Módulos Asignados",
                                    options=roles_disponibles,
                                    default=roles_actuales,
                                    key=f"multi_rol_{u.id}"
                                )
                            
                            with c_u3:
                                st.markdown("<br>", unsafe_allow_html=True)
                                esta_activo = st.checkbox("Activo", value=bool(u.activo), key=f"chk_act_{u.id}")
                            
                            with c_u4:
                                st.markdown("<br>", unsafe_allow_html=True)
                                if st.button("💾 Guardar", key=f"btn_save_u_{u.id}", type="primary"):
                                    rol_final = ",".join(nuevos_roles) if nuevos_roles else "PENDIENTE"
                                    u.rol = rol_final
                                    u.activo = esta_activo
                                    u.fecha_actualizacion = datetime.now()
                                    db.commit()
                                    st.success(f"¡Permisos de {u.username} actualizados!")
                                    
                                    # Limpiar sesión y retornar al login
                                    st.session_state.pop("autenticado", None)
                                    st.session_state.pop("rol_actual", None)
                                    st.session_state.pop("usuario_actual", None)
                                    st.rerun()

                            # --- OPCIÓN DE RENOVACIÓN DE CLAVE POR EL ADMIN ---
                            with st.expander(f"🔑 Renovar Clave para {u.username}"):
                                nueva_clave_admin = st.text_input(f"Nueva Clave para {u.username}", type="password", key=f"new_p_{u.id}")
                                if st.button(f"🔄 Forzar Cambio de Clave", key=f"btn_pass_{u.id}"):
                                    if nueva_clave_admin.strip():
                                        u.password = cifrar_password(nueva_clave_admin.strip())
                                        u.fecha_actualizacion = datetime.now()
                                        db.commit()
                                        st.success(f"✅ ¡Contraseña de {u.username} renovada y cifrada exitosamente!")
                                        
                                        st.session_state.pop("autenticado", None)
                                        st.session_state.pop("rol_actual", None)
                                        st.session_state.pop("usuario_actual", None)
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ Ingresa una contraseña válida.")

                            st.divider()

        db.close()