import sys
import os
import socket

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import streamlit as st
from modules.login_admin import render_login_admin

from modules.inventario_ui import render_inventario
from modules.ventas_ui import render_ventas
from modules.logistica_ui import render_logistica
from modules.compras_ui import render_compras
from modules.proveedores_ui import render_proveedores
from modules.clientes_ui import render_clientes
from modules.reportes_ui import render_reportes

# Configuración general de la página
st.set_page_config(
    page_title="Fajas Isabella - Sistema Modular", 
    page_icon="🛍️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BLINDAJE Y AUTO-DETECCIÓN INTELIGENTE DE ENTORNO ---
def obtener_url_api():
    # 1. Prioridad máxima: Si configuras una variable manual, se respeta siempre
    if os.getenv("API_BASE_URL"):
        return os.getenv("API_BASE_URL").strip()
    
    # 2. Detección estricta de entorno cloud (Railway, Render, etc.)
    es_nube = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PORT")
    if es_nube:
        return "https://fajasisabella-production.up.railway.app"
    
    # 3. Detección local segura
    try:
        hostname = socket.gethostname().lower()
        if "localhost" in hostname or "desktop" in hostname or os.getenv("USERNAME") or os.getenv("USER"):
            return "http://localhost:8000"
    except Exception:
        pass
    
    # 4. Fallback por defecto absoluto para desarrollo local
    return "http://localhost:8000"

base_url = obtener_url_api().rstrip("/")
st.session_state["API_URL"] = f"{base_url}/api" if not base_url.endswith("/api") else base_url

# --- ESTADOS DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = None
if "rol_actual" not in st.session_state:
    st.session_state["rol_actual"] = None

# --- EVALUACIÓN DE LOGIN DEL PANEL ---
if not st.session_state["autenticado"]:
    render_login_admin()
    st.stop()

# --- INFORMACIÓN Y CERRAR SESIÓN EN SIDEBAR ---
st.sidebar.markdown(f"👤 **Usuario:** {st.session_state['usuario_actual']}")
st.sidebar.markdown(f"🛡️ **Rol:** `{st.session_state['rol_actual']}`")

# 🕵️‍♂️ Chivato visual del entorno activo en la barra lateral
st.sidebar.caption(f"🔌 **API Activa:** `{st.session_state['API_URL']}`")

if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
    st.session_state["autenticado"] = False
    st.session_state["usuario_actual"] = None
    st.session_state["rol_actual"] = None
    st.rerun()

# --- MENÚ LATERAL SEGÚN EL ROL ---
rol = st.session_state["rol_actual"]

if rol == "Administrador":
    modulos_disponibles = [
        "📦 Inventario", 
        "💳 Ventas", 
        "🚚 Logística",
        "📥 Compras", 
        "🏭 Proveedores",
        "👥 Clientes",
        "📊 Reportes"
    ]
elif rol == "Ventas":
    modulos_disponibles = [
        "💳 Ventas",
        "📦 Inventario",
        "👥 Clientes"
    ]
elif rol == "Despacho":
    modulos_disponibles = [
        "🚚 Logística"  # Acceso exclusivo al módulo de logística
    ]
else:
    modulos_disponibles = ["📦 Inventario"]

# 🧠 Inicializar el estado del menú si no existe
if "menu_modulo_activo" not in st.session_state:
    st.session_state["menu_modulo_activo"] = modulos_disponibles[0]

# 🛡️ Asegurar que si cambia el rol, la sección seleccionada siga siendo válida
if st.session_state["menu_modulo_activo"] not in modulos_disponibles:
    st.session_state["menu_modulo_activo"] = modulos_disponibles[0]

seccion = st.sidebar.radio(
    "Seleccione el Módulo de Trabajo:", 
    modulos_disponibles, 
    key="menu_modulo_activo"
)

# --- ENCABEZADO SUPERIOR EN 2 NIVELES ---
col_head1, col_head2 = st.columns([2.5, 1.5])

with col_head1:
    st.markdown(
        """
        <div style="line-height: 1.2;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #1e293b;">🛍️ Fajas Isabella</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #334155; margin-top: 4px;">Panel de Gestión Administrativa</div>
        </div>
        """, 
        unsafe_allow_html=True
    )

with col_head2:
    st.markdown(
        f"""
        <div style="text-align: right; line-height: 1.3; padding-top: 4px;">
            <span style="font-size: 0.85rem; color: #64748b; font-weight: 600;">Módulo Activo:</span><br>
            <span style="font-size: 0.95rem; color: #FF4B4B; font-weight: 700;">{seccion}</span>
        </div>
        """, 
        unsafe_allow_html=True
    )

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# --- RENDERIZADO DE MÓDULOS ---
if seccion == "📦 Inventario":
    render_inventario()
elif seccion == "💳 Ventas":
    render_ventas()
elif seccion == "🚚 Logística":
    render_logistica()
elif seccion == "📥 Compras":
    render_compras()
elif seccion == "🏭 Proveedores":
    render_proveedores()
elif seccion == "👥 Clientes":
    render_clientes()
elif seccion == "📊 Reportes":
    render_reportes()