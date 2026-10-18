from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime
from database import get_db, Proveedor, Factura, VarianteProducto, MovimientoInventario

router = APIRouter()

class ItemCompraSchema(BaseModel):
    sku: str
    cantidad: int
    valor_neto: float

class CompraFacturaSchema(BaseModel):
    numero_factura: str
    fecha_factura: str
    ruc_proveedor: str
    nombre_proveedor: str
    items: List[ItemCompraSchema]

@router.get("/compras-factura")
def listar_facturas_compra(db: Session = Depends(get_db)):
    facturas = db.query(Factura).filter(Factura.tipo_factura == "COMPRA").order_by(Factura.id.desc()).all()
    resultado = []
    for f in facturas:
        resultado.append({
            "id": f.id,
            "numero_factura": f.numero_factura,
            "fecha_factura": str(f.fecha_factura),
            "ruc_proveedor": f.entidad_ruc,
            "nombre_proveedor": f.entidad_nombre,
            "total_factura": float(f.total_factura or 0.0)
        })
    return resultado

@router.post("/compras-factura")
def registrar_compra(compra: CompraFacturaSchema, db: Session = Depends(get_db)):
    num_fact = compra.numero_factura.strip()
    ruc_prov = compra.ruc_proveedor.strip()
    
    # 1. Verificar si la factura de compra ya fue ingresada
    existe = db.query(Factura).filter(
        Factura.numero_factura == num_fact, 
        Factura.tipo_factura == "COMPRA"
    ).first()
    if existe:
        raise HTTPException(
            status_code=400, 
            detail=f"La factura de compra Nº {num_fact} ya se encuentra registrada."
        )

    if not compra.items:
        raise HTTPException(status_code=400, detail="Debe ingresar al menos un ítem o variante.")

    # 2. Validación previa: Verificar que TODOS los SKUs existan ANTES de tocar el inventario
    for item in compra.items:
        sku_clean = item.sku.strip()
        variante = db.query(VarianteProducto).filter(VarianteProducto.sku == sku_clean).first()
        if not variante:
            raise HTTPException(status_code=404, detail=f"El SKU '{sku_clean}' no existe en la base de datos de inventario.")
        if item.cantidad <= 0:
            raise HTTPException(status_code=400, detail=f"La cantidad para el SKU '{sku_clean}' debe ser mayor a cero.")
        if item.valor_neto < 0:
            raise HTTPException(status_code=400, detail=f"El costo unitario para el SKU '{sku_clean}' no puede ser negativo.")

    try:
        # 3. Buscar o Crear Proveedor automáticamente si no existe
        prov = db.query(Proveedor).filter(Proveedor.ruc_cedula == ruc_prov).first()
        if not prov:
            prov = Proveedor(
                ruc_cedula=ruc_prov, 
                nombre_empresa=compra.nombre_proveedor.strip()
            )
            db.add(prov)
            db.flush()

        # 4. Registrar la Factura de Compra
        total_factura = sum(item.cantidad * item.valor_neto for item in compra.items)
        nueva_factura = Factura(
            tipo_factura="COMPRA", 
            numero_factura=num_fact,
            fecha_factura=datetime.strptime(compra.fecha_factura, "%Y-%m-%d").date(),
            entidad_ruc=ruc_prov, 
            entidad_nombre=compra.nombre_proveedor.strip(),
            total_factura=total_factura
        )
        db.add(nueva_factura)
        db.flush()

        # 5. Actualizar Stock e Historial de Movimientos de forma segura
        for item in compra.items:
            sku_clean = item.sku.strip()
            variante = db.query(VarianteProducto).filter(VarianteProducto.sku == sku_clean).first()
            
            # Sumar stock recibido a la bodega
            variante.stock_actual += int(item.cantidad)
            
            # Registrar Kardex / Movimiento
            movimiento = MovimientoInventario(
                sku=variante.sku, 
                tipo_movimiento="COMPRA_PROVEEDOR",
                cantidad=int(item.cantidad), 
                referencia_factura=f"Fact Compra: {num_fact}",
                valor_neto=float(item.valor_neto), 
                entidad_asociada=compra.nombre_proveedor.strip()
            )
            db.add(movimiento)
            
        db.commit()
        return {"status": "success", "message": "¡Compra registrada e inventario actualizado exitosamente!"}
    
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error interno al procesar la compra: {str(e)}")