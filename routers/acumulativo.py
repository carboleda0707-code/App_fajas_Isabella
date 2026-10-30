from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import cloudinary.uploader
from database import get_db, Factura, AbonoPlanAcumulativo

router_acumulativo = APIRouter(prefix="/api/web/acumulativo", tags=["Plan Acumulativo"])


@router_acumulativo.post("/crear")
async def crear_pedido_acumulativo(
    cliente_id: int = Form(...),
    total: float = Form(...),
    abono_inicial: float = Form(...),
    numero_factura: str = Form(...),
    comprobante: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Registra un pedido bajo la modalidad de Plan Acumulativo, 
    calcula el saldo pendiente y guarda el comprobante inicial si existe.
    """
    saldo_inicial = total - abono_inicial
    if saldo_inicial < 0:
        raise HTTPException(
            status_code=400, 
            detail="El abono inicial no puede ser mayor al total del pedido."
        )
    
    # 1. Crear la factura marcada como plan acumulativo
    nueva_factura = Factura(
        tipo_factura="VENTA_WEB_ACUMULATIVO",
        numero_factura=numero_factura,
        entidad_ruc="CONSUMIDOR_FINAL",
        entidad_nombre="Cliente Web Acumulativo",
        total_factura=total,
        cliente_id=cliente_id,
        es_plan_acumulativo=True,
        saldo_pendiente=saldo_inicial,
        estado_acumulativo="EN_PROCESO" if saldo_inicial > 0 else "COMPLETADO"
    )
    db.add(nueva_factura)
    db.commit()
    db.refresh(nueva_factura)

    # 2. Subir comprobante a Cloudinary si fue adjuntado
    comprobante_url = None
    if comprobante:
        try:
            upload_result = cloudinary.uploader.upload(
                comprobante.file, 
                folder="fajas_isabella/abonos_acumulativos"
            )
            comprobante_url = upload_result.get("secure_url")
        except Exception as e:
            print(f"Error al subir comprobante a Cloudinary: {e}")

    # 3. Registrar el primer abono si es mayor a 0
    if abono_inicial > 0:
        nuevo_abono = AbonoPlanAcumulativo(
            factura_id=nueva_factura.id,
            monto=abono_inicial,
            comprobante_url=comprobante_url,
            observacion="Abono inicial de apertura de plan acumulativo"
        )
        db.add(nuevo_abono)
        db.commit()

    return {
        "status": "success",
        "mensaje": "Plan acumulativo registrado correctamente.",
        "factura_id": nueva_factura.id,
        "saldo_pendiente": saldo_inicial
    }


@router_acumulativo.post("/abonar")
async def registrar_nuevo_abono(
    factura_id: int = Form(...),
    monto: float = Form(...),
    referencia_bancaria: Optional[str] = Form(None),
    observacion: Optional[str] = Form(None),
    comprobante: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo abono parcial para un plan acumulativo existente,
    sube el comprobante a Cloudinary y descuenta automáticamente del saldo pendiente.
    """
    factura = db.query(Factura).filter(
        Factura.id == factura_id, 
        Factura.es_plan_acumulativo == True
    ).first()

    if not factura:
        raise HTTPException(status_code=404, detail="Pedido acumulativo no encontrado.")

    saldo_actual = float(getattr(factura, 'saldo_pendiente', factura.total_factura) or 0.0)

    if monto > saldo_actual:
        raise HTTPException(
            status_code=400, 
            detail=f"El monto del abono (${monto:.2f}) supera el saldo pendiente (${saldo_actual:.2f})."
        )

    # Subir comprobante a Cloudinary
    comprobante_url = None
    if comprobante:
        try:
            upload_result = cloudinary.uploader.upload(
                comprobante.file, 
                folder="fajas_isabella/abonos_acumulativos"
            )
            comprobante_url = upload_result.get("secure_url")
        except Exception as e:
            print(f"Error al subir comprobante: {e}")

    # Registrar el abono en la base de datos
    abono = AbonoPlanAcumulativo(
        factura_id=factura.id,
        monto=monto,
        comprobante_url=comprobante_url,
        referencia_bancaria=referencia_bancaria,
        observacion=observacion
    )
    db.add(abono)

    # Actualizar saldo pendiente y estado de la orden de forma segura
    nuevo_saldo = saldo_actual - monto
    if nuevo_saldo <= 0:
        nuevo_saldo = 0.0
        factura.estado_acumulativo = "COMPLETADO"
    else:
        factura.estado_acumulativo = "EN_PROCESO"

    factura.saldo_pendiente = nuevo_saldo
    db.commit()

    return {
        "status": "success",
        "mensaje": "Abono registrado con éxito.",
        "nuevo_saldo_pendiente": round(nuevo_saldo, 2),
        "estado_acumulativo": factura.estado_acumulativo
    }


@router_acumulativo.get("/admin/cartera-acumulativa")
@router_acumulativo.get("/reporte/cartera")
async def obtener_cartera_acumulativa(db: Session = Depends(get_db)):
    """
    Retorna el resumen financiero y la lista detallada de todas las órdenes 
    con plan acumulativo para el control diario de cobranza de forma blindada (Código 500 evitado).
    """
    try:
        facturas_acumulativas = db.query(Factura).filter(
            (Factura.es_plan_acumulativo == True) | (Factura.saldo_pendiente > 0)
        ).all()
        
        detalles = []
        total_cartera = 0.0
        total_recaudado = 0.0
        total_pendiente = 0.0

        for f in facturas_acumulativas:
            total_factura = float(f.total_factura or 0.0)
            
            # Calcular recaudado de forma segura desde la relación de abonos
            recaudado = 0.0
            if hasattr(f, 'abonos_acumulativos') and f.abonos_acumulativos:
                recaudado = sum(float(a.monto or 0.0) for a in f.abonos_acumulativos)
            
            # Obtener saldo pendiente respaldado o calculado
            pendiente = float(getattr(f, 'saldo_pendiente', total_factura - recaudado) or 0.0)
            if pendiente < 0:
                pendiente = 0.0

            total_cartera += total_factura
            total_recaudado += recaudado
            total_pendiente += pendiente

            cliente_nombre = f.entidad_nombre or "Cliente General"
            cliente_telefono = "N/D"
            
            if hasattr(f, 'cliente') and f.cliente:
                if f.cliente.nombre:
                    cliente_nombre = f.cliente.nombre
                if f.cliente.telefono:
                    cliente_telefono = f.cliente.telefono

            fecha_str = str(f.fecha_factura) if f.fecha_factura else "S/F"

            detalles.append({
                "factura_id": f.id,
                "numero_factura": f.numero_factura or f"FAC-{f.id}",
                "cliente": cliente_nombre,
                "telefono": cliente_telefono,
                "fecha": fecha_str,
                "total_orden": round(total_factura, 2),
                "total_abonado": round(recaudado, 2),
                "saldo_pendiente": round(pendiente, 2),
                "estado": getattr(f, 'estado_acumulativo', 'EN_PROCESO') or 'EN_PROCESO',
                "cantidad_abonos": len(f.abonos_acumulativos) if hasattr(f, 'abonos_acumulativos') and f.abonos_acumulativos else 0
            })

        return {
            "status": "success",
            "resumen": {
                "total_cartera": round(total_cartera, 2),
                "total_recaudado": round(total_recaudado, 2),
                "total_pendiente": round(total_pendiente, 2),
                "planes_activos": len(facturas_acumulativas)
            },
            "detalles": detalles
        }
    except Exception as e:
        print(f"Error crítico en cartera-acumulativa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno al calcular cartera: {str(e)}")