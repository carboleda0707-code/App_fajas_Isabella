from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db, Producto, Categoria
from typing import Optional

router = APIRouter()

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
                    "sku": v.sku,
                    "talla": v.talla,
                    "color": v.color,
                    "precio": float(v.precio),
                    "stock": v.stock_actual
                })
            
            # Formatear la URL de la imagen limpia preservando el nombre original del archivo
            img_clean = getattr(prod, 'imagen_url', '') or ''
            if img_clean:
                img_clean = img_clean.split('/')[-1]

            resultado.append({
                "id": prod.id,
                "nombre": prod.nombre,
                "categoria": prod.categoria,
                "imagen_url": img_clean,
                "en_liquidacion": getattr(prod, 'en_liquidacion', False),
                "variantes": variantes_data
            })
            
    return resultado

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