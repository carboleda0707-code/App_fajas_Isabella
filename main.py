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

# Redireccionar la raíz '/' a la página web pública
@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/web/index.html")

# Servir carpeta de imágenes y archivos estáticos
app.mount("/web", StaticFiles(directory="web", html=True), name="web")

# Routers de la API
app.include_router(clientes.router, prefix="/api", tags=["Clientes"])
app.include_router(proveedores.router, prefix="/api", tags=["Proveedores"])
app.include_router(productos.router, prefix="/api", tags=["Productos & Inventario"])
app.include_router(compras.router, prefix="/api", tags=["Compras"])
app.include_router(ventas.router, prefix="/api", tags=["Ventas"])
app.include_router(reportes.router, prefix="/api", tags=["Reportes"])
app.include_router(web_publica.router, prefix="/api", tags=["Web Pública"])