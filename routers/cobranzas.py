from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Factura, AbonoPlanAcumulativo, Pago
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/cobranzas", tags=["Cobranzas y Abonos"])

class AbonoSchema(BaseModel):
    factura_id: int
    monto: float
    metodo_pago: str = "Transferencia"
    referencia_bancaria: Optional[str] = ""
    observacion: Optional[str] = ""

@router.get("/resumen")
def obtener_resumen_cobranzas(db: Session = Depends(get_db)):
    """Obtiene el resumen de cartera activa, saldos pendientes y listado de órdenes."""
    facturas = db.query(Factura).all()
    
    cartera_total = 0.0
    total_recaudado = 0.0
    saldo_pendiente_total = 0.0
    planes_activos = 0
    planes_list = []

    for f in facturas:
        total_factura = float(f.total or 0.0)
        saldo_pend = float(f.saldo_pendiente if f.saldo_pendiente is not None else total_factura)
        abonado = total_factura - saldo_pend
        
        if saldo_pend > 0:
            planes_activos += 1
        
        cartera_total += total_factura
        total_recaudado += max(0.0, abonado)
        saldo_pendiente_total += saldo_pend

        planes_list.append({
            "id": f.id,
            "numero_factura": getattr(f, "numero_factura", str(f.id)),
            "cliente": getattr(f, "cliente", "Cliente General"),
            "ruc_cedula": getattr(f, "ruc_cedula", "S/N"),
            "total": total_factura,
            "saldo_pendiente": saldo_pend
        })

    return {
        "cartera_total": cartera_total,
        "total_recaudado": total_recaudado,
        "saldo_pendiente": saldo_pendiente_total,
        "planes_activos": planes_activos,
        "planes": planes_list
    }

@router.post("/registrar-abono")
def registrar_abono_plan(datos: AbonoSchema, db: Session = Depends(get_db)):
    """Registra un nuevo abono o pago a una factura y descuenta el saldo pendiente."""
    factura = db.query(Factura).filter(Factura.id == datos.factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura / Plan no encontrado.")

    if datos.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto a abonar debe ser mayor a 0.")

    saldo_actual = float(factura.saldo_pendiente if factura.saldo_pendiente is not None else factura.total or 0.0)
    
    if datos.monto > saldo_actual and saldo_actual > 0:
        raise HTTPException(status_code=400, detail=f"El abono (${datos.monto:.2f}) excede el saldo pendiente (${saldo_actual:.2f}).")

    # 1. Registrar abono
    nuevo_abono = AbonoPlanAcumulativo(
        factura_id=factura.id,
        monto=datos.monto,
        referencia_bancaria=datos.referencia_bancaria,
        observacion=datos.observacion
    )
    db.add(nuevo_abono)

    # 2. Registrar en pagos si el modelo existe
    try:
        nuevo_pago = Pago(
            factura_id=factura.id,
            metodo_pago=datos.metodo_pago,
            monto=datos.monto,
            codigo_transferencia=datos.referencia_bancaria
        )
        db.add(nuevo_pago)
    except Exception:
        pass

    # 3. Actualizar saldo en la factura
    nuevo_saldo = saldo_actual - datos.monto
    factura.saldo_pendiente = max(0.0, nuevo_saldo)
    
    db.commit()
    return {"status": "success", "nuevo_saldo": factura.saldo_pendiente}