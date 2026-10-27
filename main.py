from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from routers import clientes, proveedores, productos, compras, ventas, reportes, web_publica, auth_web, logistica

app = FastAPI(title="Fajas Isabella - Sistema Modular API", version="5.0")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return RedirectResponse(url="/web/index.html")

@app.get("/admin")
@app.get("/panel")
def redirigir_admin():
    return RedirectResponse(url="http://localhost:8501")

# --- ROUTERS DEL NEGOCIO ---
app.include_router(web_publica.router, prefix="/api", tags=["Web Pública"])
app.include_router(ventas.router, prefix="/api", tags=["Ventas"])
app.include_router(clientes.router, prefix="/api", tags=["Clientes"])
app.include_router(proveedores.router, prefix="/api", tags=["Proveedores"])
app.include_router(productos.router, prefix="/api", tags=["Productos & Inventario"])
app.include_router(compras.router, prefix="/api", tags=["Compras"])
app.include_router(reportes.router, prefix="/api", tags=["Reportes"])
app.include_router(logistica.router)
app.include_router(auth_web.router)

# --- ARCHIVOS ESTÁTICOS ---
app.mount("/web", StaticFiles(directory="web", html=True), name="web")
app.mount("/img", StaticFiles(directory="web/img"), name="img")