from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from routers import clientes, proveedores, productos, compras, ventas, reportes, web_publica

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

# Router de la Web Pública con el prefijo /api
app.include_router(web_publica.router, prefix="/api", tags=["Web Pública"])

# Routers del sistema (Ventas mapeado bajo /api para sincronía con el frontend)
app.include_router(ventas.router, prefix="/api", tags=["Ventas"])
app.include_router(clientes.router, tags=["Clientes"])
app.include_router(proveedores.router, tags=["Proveedores"])
app.include_router(productos.router, tags=["Productos & Inventario"])
app.include_router(compras.router, tags=["Compras"])
app.include_router(reportes.router, tags=["Reportes"])

# Archivos estáticos
app.mount("/web", StaticFiles(directory="web", html=True), name="web")
app.mount("/img", StaticFiles(directory="web/img"), name="img")