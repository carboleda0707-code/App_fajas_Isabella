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
    return db.query(Factura).filter(Factura.tipo_factura == "COMPRA").all()

@router.post("/compras-factura")
def registrar_compra(compra: CompraFacturaSchema, db: Session = Depends(get_db)):
    # Verificar si ya existe la factura de compra
    existe = db.query(Factura).filter(Factura.numero_factura == compra.numero_factura, Factura.tipo_factura == "COMPRA").first()
    if existe:
        raise HTTPException(status_code=400, detail=f"La factura de compra Nº {compra.numero_factura} ya se encuentra registrada.")

    prov = db.query(Proveedor).filter(Proveedor.ruc_cedula == compra.ruc_proveedor).first()
    if not prov:
        prov = Proveedor(ruc_cedula=compra.ruc_proveedor, nombre_empresa=compra.nombre_proveedor)
        db.add(prov)
        db.commit()

    total_factura = sum(item.cantidad * item.valor_neto for item in compra.items)
    nueva_factura = Factura(
        tipo_factura="COMPRA", numero_factura=compra.numero_factura,
        fecha_factura=datetime.strptime(compra.fecha_factura, "%Y-%m-%d").date(),
        entidad_ruc=compra.ruc_proveedor, entidad_nombre=compra.nombre_proveedor,
        total_factura=total_factura
    )
    db.add(nueva_factura)
    db.commit()

    for item in compra.items:
        variante = db.query(VarianteProducto).filter(VarianteProducto.sku == item.sku).first()
        if not variante:
            raise HTTPException(status_code=404, detail=f"SKU {item.sku} no existe.")
        variante.stock_actual += item.cantidad
        
        movimiento = MovimientoInventario(
            sku=variante.sku, tipo_movimiento="COMPRA_PROVEEDOR",
            cantidad=item.cantidad, referencia_factura=f"Fact Compra: {compra.numero_factura}",
            valor_neto=item.valor_neto, entidad_asociada=compra.nombre_proveedor
        )
        db.add(movimiento)
    db.commit()
    return {"status": "success", "message": "Compra registrada exitosamente."}