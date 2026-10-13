import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import streamlit as st
from modules.login_admin import render_login_admin

from modules.inventario_ui import render_inventario
from modules.ventas_ui import render_ventas
from modules.despachos_ui import render_despachos
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

# --- CONFIGURACIÓN GLOBAL Y CENTRALIZADA DE LA API (NUBE) ---
default_cloud_url = "https://fajasisabella-production.up.railway.app"
base_url = os.getenv("API_BASE_URL", default_cloud_url).rstrip("/")
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
    st.stop()  # Bloquea el panel administrativo si no se autentica

# --- INFORMACIÓN Y CERRAR SESIÓN EN SIDEBAR ---
st.sidebar.markdown(f"👤 **Usuario:** {st.session_state['usuario_actual']}")
st.sidebar.markdown(f"🛡️ **Rol:** `{st.session_state['rol_actual']}`")
if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
    st.session_state["autenticado"] = False
    st.session_state["usuario_actual"] = None
    st.session_state["rol_actual"] = None
    st.rerun()

st.sidebar.markdown("---")

# --- MENÚ LATERAL SEGÚN EL ROL ---
rol = st.session_state["rol_actual"]

if rol == "Administrador":
    modulos_disponibles = [
        "📦 Módulo de Inventario", 
        "💳 Módulo de Ventas", 
        "🚚 Logística y Despachos",
        "📥 Módulo de Compras", 
        "🏭 Mantenimiento de Proveedores",
        "👥 Mantenimiento de Clientes",
        "📊 Reportes y Auditoría"
    ]
elif rol == "Ventas":
    modulos_disponibles = [
        "💳 Módulo de Ventas",
        "📦 Módulo de Inventario",
        "👥 Mantenimiento de Clientes"
    ]
elif rol == "Despacho":
    modulos_disponibles = [
        "🚚 Logística y Despachos",
        "📦 Módulo de Inventario"
    ]
else:
    modulos_disponibles = ["📦 Módulo de Inventario"]

seccion = st.sidebar.radio("Seleccione el Módulo de Trabajo:", modulos_disponibles)

# --- ENCABEZADO SUPERIOR PROFESIONAL ---
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown("#### 🛍️ **Fajas Isabella** — Panel de Gestión Administrativa")
with col_head2:
    st.markdown(f"<div style='text-align: right;'><b>Módulo Activo:</b><br><span style='color: #FF4B4B;'>{seccion}</span></div>", unsafe_allow_html=True)

#st.markdown("---")

# --- RENDERIZADO DE MÓDULOS ---
if seccion == "📦 Módulo de Inventario":
    render_inventario()
elif seccion == "💳 Módulo de Ventas":
    render_ventas()
elif seccion == "🚚 Logística y Despachos":
    render_despachos()
elif seccion == "📥 Módulo de Compras":
    render_compras()
elif seccion == "🏭 Mantenimiento de Proveedores":
    render_proveedores()
elif seccion == "👥 Mantenimiento de Clientes":
    render_clientes()
elif seccion == "📊 Reportes y Auditoría":
    render_reportes()