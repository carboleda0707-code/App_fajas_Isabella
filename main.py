from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
# Importamos el nuevo router de despachos junto con los demás
from routers import clientes, proveedores, productos, compras, ventas, reportes, web_publica, auth_web, despachos

app = FastAPI(title="Fajas Isabella - Sistema Modular API", version="5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redirección de la ruta raíz a la página web principal
@app.get("/")
def home():
    return RedirectResponse(url="/web/index.html")

# --- RUTA INTERNA PARA ACCEDER AL PANEL ADMINISTRATIVO STREAMLIT ---
@app.get("/admin")
@app.get("/panel")
def redirigir_admin():
    return RedirectResponse(url="http://localhost:8501")

# Todos los routers del negocio estandarizados bajo el prefijo /api
app.include_router(web_publica.router, prefix="/api", tags=["Web Pública"])
app.include_router(ventas.router, prefix="/api", tags=["Ventas"])
app.include_router(clientes.router, prefix="/api", tags=["Clientes"])
app.include_router(proveedores.router, prefix="/api", tags=["Proveedores"])
app.include_router(productos.router, prefix="/api", tags=["Productos & Inventario"])
app.include_router(compras.router, prefix="/api", tags=["Compras"])
app.include_router(reportes.router, prefix="/api", tags=["Reportes"])
app.include_router(despachos.router, prefix="/api", tags=["Despachos"])  # <--- ROUTER DE LOGÍSTICA Y DESPACHOS
app.include_router(auth_web.router)

# Archivos estáticos
app.mount("/web", StaticFiles(directory="web", html=True), name="web")
app.mount("/img", StaticFiles(directory="web/img"), name="img")