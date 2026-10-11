from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # <-- Añadimos esto
from routers import clientes, proveedores, productos, compras, ventas, reportes, web_publica

app = FastAPI(title="Fajas Isabella - Sistema Modular API", version="5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir carpeta de imágenes estáticas
app.mount("/web", StaticFiles(directory="web", html=True), name="web")

# Routers de la API
app.include_router(clientes.router, prefix="/api", tags=["Clientes"])
app.include_router(proveedores.router, prefix="/api", tags=["Proveedores"])
app.include_router(productos.router, prefix="/api", tags=["Productos & Inventario"])
app.include_router(compras.router, prefix="/api", tags=["Compras"])
app.include_router(ventas.router, prefix="/api", tags=["Ventas"])
app.include_router(reportes.router, prefix="/api", tags=["Reportes"])
app.include_router(web_publica.router, prefix="/api", tags=["Web Pública"])