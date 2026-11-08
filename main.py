from dotenv import load_dotenv
load_dotenv()  # Carga las variables del archivo .env antes de importar los routers

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os

from routers import (
    clientes, 
    proveedores, 
    productos, 
    compras, 
    ventas, 
    reportes, 
    web_publica, 
    auth_web, 
    logistica, 
    acumulativo, 
    cobranzas
)

app = FastAPI(
    title="Fajas Isabella - Sistema Modular API", 
    version="5.0",
    description="API RESTful unificada para gestión de inventarios, e-commerce y cobranzas acumulativas."
)

# --- CONFIGURACIÓN DE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REDIRECCIONES DE CONVENIENCIA ---
@app.get("/")
def home():
    return RedirectResponse(url="/web/index.html")

@app.get("/admin")
@app.get("/panel")
def redirigir_admin():
    panel_url = os.getenv("STREAMLIT_PANEL_URL", "http://localhost:8501")
    return RedirectResponse(url=panel_url)

# --- ROUTERS DEL NEGOCIO ---
app.include_router(web_publica.router, tags=["Web Pública"])
app.include_router(ventas.router, prefix="/api", tags=["Ventas"])
app.include_router(clientes.router, prefix="/api", tags=["Clientes"])
app.include_router(proveedores.router, prefix="/api", tags=["Proveedores"])
app.include_router(productos.router, prefix="/api", tags=["Productos & Inventario"])
app.include_router(compras.router, prefix="/api", tags=["Compras"])
app.include_router(reportes.router, prefix="/api", tags=["Reportes"])
app.include_router(logistica.router, tags=["Logística y Despachos"])
app.include_router(auth_web.router, tags=["Autenticación Web"])
app.include_router(acumulativo.router_acumulativo, tags=["Plan Acumulativo"])
app.include_router(cobranzas.router, tags=["Cobranzas y Abonos"])

# --- ARCHIVOS ESTÁTICOS ---
if os.path.exists("web"):
    app.mount("/web", StaticFiles(directory="web", html=True), name="web")
if os.path.exists("web/img"):
    app.mount("/img", StaticFiles(directory="web/img"), name="img")