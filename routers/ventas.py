from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import get_db, Cliente, Factura, Pago, VarianteProducto, MovimientoInventario

router = APIRouter()

class ItemVentaSchema(BaseModel):
    sku: str
    cantidad: int
    precio_unitario: float

class VentaFacturaSchema(BaseModel):
    numero_factura: str
    numero_autorizacion: str
    fecha_factura: str
    metodo_pago: str
    codigo_transferencia: Optional[str] = ""
    ruc_cliente: str
    nombre_cliente: str
    direccion_cliente: Optional[str] = ""
    telefono_cliente: Optional[str] = ""
    items: List[ItemVentaSchema]

@router.post("/ventas-factura")
def registrar_venta(venta: VentaFacturaSchema, db: Session = Depends(get_db)):
    
    # --- VALIDACIÓN DE FACTURA DUPLICADA ---
    existe = db.query(Factura).filter(
        Factura.numero_factura == venta.numero_factura, 
        Factura.tipo_factura == "VENTA"
    ).first()
    
    if existe:
        raise HTTPException(
            status_code=400, 
            detail=f"La factura de venta Nº {venta.numero_factura} ya se encuentra registrada en el sistema."
        )
    # ----------------------------------------

    cliente = db.query(Cliente).filter(Cliente.ruc_cedula == venta.ruc_cliente).first()
    if not cliente:
        cliente = Cliente(
            ruc_cedula=venta.ruc_cliente, nombre=venta.nombre_cliente,
            direccion=venta.direccion_cliente, telefono=venta.telefono_cliente
        )
        db.add(cliente)
        db.commit()

    for item in venta.items:
        variante = db.query(VarianteProducto).filter(VarianteProducto.sku == item.sku).first()
        if not variante:
            raise HTTPException(status_code=404, detail=f"SKU {item.sku} no existe.")
        if variante.stock_actual < item.cantidad:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para {item.sku}.")

    total_calculado = sum(item.cantidad * item.precio_unitario for item in venta.items)
    
    nueva_factura = Factura(
        tipo_factura="VENTA", numero_factura=venta.numero_factura,
        numero_autorizacion=venta.numero_autorizacion,
        fecha_factura=datetime.strptime(venta.fecha_factura, "%Y-%m-%d").date(),
        entidad_ruc=venta.ruc_cliente, entidad_nombre=venta.nombre_cliente,
        total_factura=total_calculado
    )
    db.add(nueva_factura)
    db.commit()
    db.refresh(nueva_factura)

    nuevo_pago = Pago(
        factura_id=nueva_factura.id, metodo_pago=venta.metodo_pago,
        codigo_transferencia=venta.codigo_transferencia if venta.metodo_pago == "Transferencia" else None,
        monto=total_calculado
    )
    db.add(nuevo_pago)

    for item in venta.items:
        variante = db.query(VarianteProducto).filter(VarianteProducto.sku == item.sku).first()
        variante.stock_actual -= item.cantidad
        
        movimiento = MovimientoInventario(
            sku=variante.sku, tipo_movimiento="VENTA_LOCAL",
            cantidad=-item.cantidad, referencia_factura=f"Fact Venta: {venta.numero_factura}",
            valor_neto=item.precio_unitario, entidad_asociada=venta.nombre_cliente
        )
        db.add(movimiento)
    db.commit()
    return {"status": "success", "message": "Venta y pago registrados exitosamente."}