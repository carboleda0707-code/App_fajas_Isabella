import sys
import os

# Asegurar que la raíz del proyecto esté en el PYTHONPATH de forma dinámica (Compatible con la nube)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import streamlit as st
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

# --- CSS PARA HACER EL ENCABEZADO PEGAJOSO (STICKY) Y VISIBLE ---
st.markdown("""
    <style>
        /* Ajuste de margen superior de Streamlit */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.5rem !important;
        }
        
        /* Caja del encabezado sticky */
        .sticky-header {
            position: -webkit-sticky;
            position: sticky;
            top: 0px;
            background-color: #ffffff;
            z-index: 999;
            padding-top: 5px;
            padding-bottom: 12px;
            border-bottom: 2px solid #eaeaea;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# 1. Menú Lateral (Sidebar)
st.sidebar.markdown("### 🎛️ Panel de Control")
st.sidebar.markdown("---")

seccion = st.sidebar.radio(
    "Seleccione el Módulo de Trabajo:",
    [
        "📦 Módulo de Inventario", 
        "💳 Módulo de Ventas", 
        "🚚 Logística y Despachos",
        "📥 Módulo de Compras", 
        "🏭 Mantenimiento de Proveedores",
        "👥 Mantenimiento de Clientes",
        "📊 Reportes y Auditoría"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Versión:** 5.0 Modular\n\nBase de Datos: **Conectada** 🟢")

# 2. Encabezado Fijo Visible
st.markdown(f"""
    <div class="sticky-header">
        <span style="font-size: 1.8rem; font-weight: 800; color: #1e293b;">🛍️ Fajas Isabella</span>
        <span style="font-size: 1.1rem; color: #2563eb; font-weight: 600; margin-left: 15px;">| &nbsp; {seccion}</span>
        <p style="font-size: 0.88rem; color: #64748b; margin: 2px 0 0 0;">Sistema Profesional de Gestión, Inventario y Auditoría Financiera</p>
    </div>
""", unsafe_allow_html=True)

# 3. Renderizado del Módulo Activo
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