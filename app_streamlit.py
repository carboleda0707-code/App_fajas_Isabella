import sys
import os
import socket

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import streamlit as st
import streamlit.components.v1 as components
from modules.login_admin import render_login_admin

from modules.inventario_ui import render_inventario
from modules.ventas_ui import render_ventas
from modules.logistica_ui import render_logistica
from modules.compras_ui import render_compras
from modules.proveedores_ui import render_proveedores
from modules.clientes_ui import render_clientes
from modules.reportes_ui import render_reportes
from modules.home_admin_ui import render_home_admin
from modules.cobranzas_ui import render_gestion_cobranzas
from modules.dashboard_ui import render_dashboard_admin  # <--- NUEVO PANEL EJECUTIVO

# Configuración general de la página
st.set_page_config(
    page_title="Fajas Isabella - Sistema Modular", 
    page_icon="🛍️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BLINDAJE Y AUTO-DETECCIÓN INTELIGENTE DE ENTORNO ---
def obtener_url_api():
    if os.getenv("API_BASE_URL"):
        return os.getenv("API_BASE_URL").strip()
    
    es_nube = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PORT")
    if es_nube:
        return "https://fajasisabella-production.up.railway.app"
    
    try:
        hostname = socket.gethostname().lower()
        if "localhost" in hostname or "desktop" in hostname or os.getenv("USERNAME") or os.getenv("USER"):
            return "http://localhost:8000"
    except Exception:
        pass
    
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

# --- WIDGET DE NOTIFICACIONES EN TIEMPO REAL ---
def render_live_notifications_widget(api_url: str):
    widget_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    </head>
    <body>
        <script>
            (function() {{
                const parentDoc = window.parent.document;
                const originalTitle = parentDoc.title;
                let flashTimer = null;

                if (!parentDoc.getElementById('sound-cash')) {{
                    const audioTag = parentDoc.createElement('audio');
                    audioTag.id = 'sound-cash';
                    audioTag.preload = 'auto';
                    audioTag.innerHTML = '<source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">';
                    parentDoc.body.appendChild(audioTag);
                }}

                let ultimoIdConocido = null;
                const apiUrl = "{api_url}/web/pedidos/ultimo-reciente";

                async function verificarNuevosPedidos() {{
                    try {{
                        const res = await fetch(apiUrl);
                        if (!res.ok) return;
                        const data = await res.json();
                        
                        if (!data || typeof data.id === 'undefined') return;

                        if (ultimoIdConocido !== null && data.id > ultimoIdConocido) {{
                            dispararAlertaVenta(data.numero_factura || '0000', data.total || 0.0, data.cliente || 'Cliente');
                        }}
                        ultimoIdConocido = data.id;
                    }} catch (e) {{}}
                }}

                function iniciarParpadeoPestaña(numFactura) {{
                    if (flashTimer) clearInterval(flashTimer);
                    let toggle = false;
                    flashTimer = setInterval(() => {{
                        parentDoc.title = toggle ? "🎉 ¡Nueva Venta #" + numFactura + "!" : originalTitle;
                        toggle = !toggle;
                    }}, 1000);

                    const detenerParpadeo = () => {{
                        if (!parentDoc.hidden) {{
                            clearInterval(flashTimer);
                            parentDoc.title = originalTitle;
                            parentDoc.removeEventListener('visibilitychange', detenerParpadeo);
                            parentDoc.removeEventListener('mousemove', detenerParpadeo);
                        }}
                    }};
                    parentDoc.addEventListener('visibilitychange', detenerParpadeo);
                    parentDoc.addEventListener('mousemove', detenerParpadeo);
                }}

                function dispararAlertaVenta(numFactura, total, cliente) {{
                    const sound = parentDoc.getElementById('sound-cash');
                    if (sound) {{
                        sound.currentTime = 0;
                        sound.play().catch(err => console.log("Audio bloqueado", err));
                    }}

                    if (typeof confetti === 'function') {{
                        confetti({{
                            particleCount: 150,
                            spread: 90,
                            origin: {{ y: 0.7 }}
                        }});
                    }}

                    iniciarParpadeoPestaña(numFactura);

                    const card = parentDoc.createElement('div');
                    card.style.position = 'fixed';
                    card.style.bottom = '30px';
                    card.style.right = '30px';
                    card.style.backgroundColor = '#e11d48';
                    card.style.color = '#ffffff';
                    card.style.padding = '18px 25px';
                    card.style.borderRadius = '16px';
                    card.style.boxShadow = '0 15px 30px rgba(0,0,0,0.4)';
                    card.style.fontWeight = 'bold';
                    card.style.fontSize = '15px';
                    card.style.zIndex = '99999999';
                    card.style.fontFamily = 'sans-serif';
                    card.style.border = '2px solid #ffffff';
                    card.innerHTML = "🎉 ¡Nueva Venta en Directo!<br><span style='font-size:13px; font-weight:normal;'>Factura #" + numFactura + " - " + cliente + " ($" + Number(total).toFixed(2) + ")</span>";
                    
                    parentDoc.body.appendChild(card);
                    setTimeout(() => {{ card.remove(); }}, 10000);
                }}

                setInterval(verificarNuevosPedidos, 20000);
                verificarNuevosPedidos();
            }})();
        </script>
    </body>
    </html>
    """
    components.html(widget_html, height=0, width=0)

render_live_notifications_widget(st.session_state["API_URL"])

# --- INFORMACIÓN Y CERRAR SESIÓN EN SIDEBAR ---
st.sidebar.markdown(f"👤 **Usuario:** {st.session_state['usuario_actual']}")
st.sidebar.markdown(f"🛡️ **Rol:** `{st.session_state['rol_actual']}`")
st.sidebar.caption(f"🔌 **API Activa:** `{st.session_state['API_URL']}`")

if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
    st.session_state["autenticado"] = False
    st.session_state["usuario_actual"] = None
    st.session_state["rol_actual"] = None
    st.rerun()

# --- MENÚ LATERAL INTELIGENTE ---
rol_actual_str = str(st.session_state["rol_actual"] or "").strip()

es_administrador = "Administrador" in rol_actual_str
es_ventas = "Ventas" in rol_actual_str
es_logistica = "Logística" in rol_actual_str or "Despacho" in rol_actual_str
es_inventario = "Inventario" in rol_actual_str

modulos_disponibles = []

if es_administrador:
    modulos_disponibles = [
        "📊 Panel Ejecutivo",       # <--- NUEVA PRESENTACIÓN EN EL MENÚ
        "📦 Inventario", 
        "💳 Ventas", 
        "✨ Cobranzas Acumulativas",  
        "🚚 Logística",
        "📥 Compras", 
        "🏭 Proveedores",
        "👥 Clientes",
        "📊 Reportes",
        "🌐 Panel Web"
    ]
else:
    if es_ventas:
        modulos_disponibles.extend(["📊 Panel Ejecutivo", "💳 Ventas", "✨ Cobranzas Acumulativas", "👥 Clientes"])
    if es_logistica:
        modulos_disponibles.append("🚚 Logística")
    if es_inventario:
        modulos_disponibles.append("📦 Inventario")
    
    if not modulos_disponibles:
        modulos_disponibles = ["📊 Panel Ejecutivo", "📦 Inventario"]

modulos_disponibles = list(dict.fromkeys(modulos_disponibles))

if "menu_modulo_activo" not in st.session_state:
    st.session_state["menu_modulo_activo"] = modulos_disponibles[0]

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
if seccion == "📊 Panel Ejecutivo":
    render_dashboard_admin(st.session_state["API_URL"])  # <--- NUEVA VISTA INTEGRADA
elif seccion == "📦 Inventario":
    render_inventario()
elif seccion == "💳 Ventas":
    render_ventas()
elif seccion == "✨ Cobranzas Acumulativas":
    render_gestion_cobranzas(st.session_state["API_URL"])
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
elif seccion == "🌐 Panel Web":
    render_home_admin()