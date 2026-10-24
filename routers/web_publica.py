from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Producto, Categoria
from typing import Optional
from config import (
    NOMBRE_EMPRESA, TELEFONO_WHATSAPP, CORREO_EMPRESA, DIRECCION_EMPRESA,
    INSTAGRAM_URL, FACEBOOK_URL, TIKTOK_URL, WHATSAPP_LINK
)

router = APIRouter()

@router.get("/config/empresa")
def obtener_info_empresa():
    """
    Retorna la información corporativa, redes sociales y contacto configurada en config.ini.
    """
    return {
        "nombre": NOMBRE_EMPRESA,
        "telefono_whatsapp": TELEFONO_WHATSAPP,
        "correo": CORREO_EMPRESA,
        "direccion": DIRECCION_EMPRESA,
        "redes": {
            "instagram": INSTAGRAM_URL,
            "facebook": FACEBOOK_URL,
            "tiktok": TIKTOK_URL,
            "whatsapp": WHATSAPP_LINK
        }
    }

@router.get("/web/inventario")
def listar_inventario_publico(categoria: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Producto)
    
    if categoria and categoria.upper() != "TODAS":
        query = query.filter(Producto.categoria.ilike(f"%{categoria}%"))
        
    productos_db = query.all()
    
    resultado = []
    for prod in productos_db:
        variantes = [v for v in prod.variantes if v.stock_actual > 0]
        
        if variantes:
            variantes_data = []
            for v in variantes:
                variantes_data.append({
                    "id": v.id,
                    "sku": v.sku,
                    "talla": v.talla,
                    "color": v.color,
                    "precio": float(v.precio),
                    "stock": v.stock_actual
                })
            
            # Formatear la URL de la imagen limpia preservando el nombre original
            img_clean = getattr(prod, 'imagen_url', '') or ''
            
            resultado.append({
                "id": prod.id,
                "nombre": prod.nombre,
                "modelo": getattr(prod, 'modelo', prod.nombre),
                "categoria": prod.categoria,
                "imagen_url": img_clean,
                "en_liquidacion": bool(getattr(prod, 'en_liquidacion', False)),
                "es_nuevo": bool(getattr(prod, 'es_nuevo', False)),
                "en_oferta": bool(getattr(prod, 'en_oferta', False)),
                "descuento_oferta": float(getattr(prod, 'descuento_oferta', 0.0) or 0.0),
                "variantes": variantes_data
            })
            
    return resultado

@router.get("/web/producto/{producto_id}")
def obtener_producto_dinamico(producto_id: int, db: Session = Depends(get_db)):
    """
    Retorna el producto con sus variantes, precio y stock actualizado al milisegundo para el modal.
    """
    prod = db.query(Producto).filter(Producto.id == producto_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Filtrar únicamente variantes activas con stock > 0
    variantes_activas = [v for v in prod.variantes if v.stock_actual > 0]
    
    variantes_data = []
    for v in variantes_activas:
        variantes_data.append({
            "id": v.id,
            "sku": v.sku,
            "talla": v.talla,
            "color": v.color,
            "precio": float(v.precio),
            "stock": v.stock_actual
        })

    img_clean = getattr(prod, 'imagen_url', '') or ''
    if img_clean:
        img_clean = img_clean.split('/')[-1]

    return {
        "status": "success",
        "id": prod.id,
        "nombre": prod.nombre,
        "categoria": prod.categoria,
        "imagen_url": img_clean,
        "variantes": variantes_data
    }

@router.get("/web/categorias")
def listar_categorias_publicas(db: Session = Depends(get_db)):
    """
    Retorna EXCLUSIVAMENTE las categorías registradas en la tabla independiente de categorías de la BD.
    """
    try:
        categorias_db = db.query(Categoria).all()
        
        resultado = []
        for cat in categorias_db:
            img_clean = getattr(cat, 'imagen_url', '') or ''
            if img_clean:
                img_clean = img_clean.split('/')[-1]

            resultado.append({
                "nombre": getattr(cat, 'nombre', getattr(cat, 'categoria', '')),
                "imagen_url": img_clean
            })
        return resultado
    except Exception:
        return []