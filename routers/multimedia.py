import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db, Sucursal  # Conexión y modelo de base de datos

router = APIRouter(tags=["Multimedia Híbrida"])

# Carpeta de caché temporal en la nube (Railway)
CACHE_DIR = "app_cache_images"
os.makedirs(CACHE_DIR, exist_ok=True)

@router.get("/media/{codigo_sucursal}/{filename:path}")
async def obtener_imagen_hibrida(codigo_sucursal: str, filename: str, db: Session = Depends(get_db)):
    """
    Endpoint inteligente de Lazy Caching:
    1. Busca en la caché del servidor en la nube.
    2. Si no existe, consulta la IP local del mini-servidor de la sucursal en PostgreSQL.
    3. Descarga la imagen vía HTTP desde la PC física de la tienda (soportando subcarpetas), la guarda en caché y la entrega.
    """
    # 1. Ruta local en el contenedor de Railway
    ruta_cache_cloud = os.path.join(CACHE_DIR, filename)
    
    # Asegurar que subdirectorios en caché existan si el filename incluye rutas (ej. historia/banner.jpg)
    os.makedirs(os.path.dirname(ruta_cache_cloud), exist_ok=True)
    
    # Si ya existe en la caché de la nube, se sirve de inmediato (Velocidad máxima)
    if os.path.exists(ruta_cache_cloud):
        return FileResponse(ruta_cache_cloud)
    
    # 2. Si no está en la nube, buscamos la IP/URL del mini-servidor de la sucursal en la BD
    sucursal = db.query(Sucursal).filter(Sucursal.codigo_slug == codigo_sucursal).first()
    if not sucursal or not sucursal.ip_o_url_local:
        raise HTTPException(
            status_code=404, 
            detail="Sucursal no registrada o el mini-servidor local no tiene una IP/URL configurada"
        )
    
    # Construir la URL del mini-servidor local de la tienda física usando /local-img/
    # Ej: http://192.168.1.50:8001/local-img/historia/banner_historia.jpg
    url_mini_servidor_local = f"{sucursal.ip_o_url_local}/local-img/{filename}"
    
    try:
        # 3. Petición al mini-servidor físico de la tienda (Fallback)
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(url_mini_servidor_local)
            
            if response.status_code == 200:
                # Guardamos el archivo en la caché local de Railway
                with open(ruta_cache_cloud, "wb") as f:
                    f.write(response.content)
                
                return Response(
                    content=response.content, 
                    media_type=response.headers.get("content-type", "image/jpeg")
                )
            else:
                raise HTTPException(
                    status_code=404, 
                    detail="La imagen no fue encontrada en el mini-servidor local de la sucursal."
                )
                
    except httpx.RequestError:
        raise HTTPException(
            status_code=503, 
            detail="El mini-servidor local de la sucursal no está disponible temporalmente (offline o apagado)."
        )