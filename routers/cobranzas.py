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
    """Obtiene el resumen de cartera activa consultando todas las facturas con saldo pendiente."""
    # Consultar todas las facturas o ventas registradas
    facturas = db.query(Factura).all()
    
    cartera_total = 0.0
    total_recaudado = 0.0
    saldo_pendiente_total = 0.0
    planes_activos = 0
    planes_list = []

    for f in facturas:
        # Extraer valores asegurando compatibilidad con los nombres de columnas reales
        total_factura = float(getattr(f, "total_factura", None) or getattr(f, "total", 0.0))
        saldo_pend = float(getattr(f, "saldo_pendiente", None) if getattr(f, "saldo_pendiente", None) is not None else total_factura)
        abonado = total_factura - saldo_pend
        
        # Considerar activo si tiene saldo pendiente mayor a 0 o es plan acumulativo
        es_acumulativo = getattr(f, "es_plan_acumulativo", True)
        
        if saldo_pend > 0 and es_acumulativo:
            planes_activos += 1
            cartera_total += total_factura
            total_recaudado += max(0.0, abonado)
            saldo_pendiente_total += saldo_pend

            planes_list.append({
                "id": f.id,
                "numero_factura": str(getattr(f, "numero_factura", f.id)),
                "cliente": str(getattr(f, "cliente", "Cliente General")),
                "ruc_cedula": str(getattr(f, "ruc_cedula", "S/N")),
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

    total_factura = float(getattr(factura, "total_factura", None) or getattr(factura, "total", 0.0))
    saldo_actual = float(getattr(factura, "saldo_pendiente", None) if getattr(factura, "saldo_pendiente", None) is not None else total_factura)
    
    if datos.monto > saldo_actual and saldo_actual > 0:
        raise HTTPException(status_code=400, detail=f"El abono (${datos.monto:.2f}) excede el saldo pendiente (${saldo_actual:.2f}).")

    # 1. Registrar abono en la tabla correspondiente
    try:
        nuevo_abono = AbonoPlanAcumulativo(
            factura_id=factura.id,
            monto=datos.monto,
            referencia_bancaria=datos.referencia_bancaria,
            observacion=datos.observacion
        )
        db.add(nuevo_abono)
    except Exception:
        pass

    # 2. Registrar en pagos
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

    # 3. Actualizar saldo pendiente en la factura
    nuevo_saldo = saldo_actual - datos.monto
    factura.saldo_pendiente = max(0.0, nuevo_saldo)
    
    db.commit()
    return {"status": "success", "nuevo_saldo": factura.saldo_pendiente}