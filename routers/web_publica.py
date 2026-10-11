from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db, VarianteProducto, Producto
from typing import Optional

router = APIRouter()

@router.get("/web/inventario")
def listar_inventario_publico(categoria: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Retorna productos estructurados con sus galerías de variantes (talla, color, precio, stock).
    """
    query = db.query(Producto)
    
    if categoria and categoria.upper() != "TODAS":
        query = query.filter(Producto.categoria.ilike(f"%{categoria}%"))
        
    productos_db = query.all()
    
    resultado = []
    for prod in productos_db:
        # Filtrar solo variantes con stock disponible
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
            
            resultado.append({
                "id": prod.id,
                "nombre": prod.nombre,
                "categoria": prod.categoria,
                "descripcion": getattr(prod, 'descripcion', ''),
                "imagen_url": getattr(prod, 'imagen_url', ''),
                "variantes": variantes_data
            })
            
    return resultado