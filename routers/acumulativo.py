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
    calcula el saldo pendiente y guarda el comprobante inicial si existe[cite: 12].
    """
    saldo_inicial = total - abono_inicial
    if saldo_inicial < 0:
        raise HTTPException(
            status_code=400, 
            detail="El abono inicial no puede ser mayor al total del pedido[cite: 12]."
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
        estado_acumulativo="EN_PROCESO"
    )
    db.add(nueva_factura)
    db.commit()
    db.refresh(nueva_factura)

    # 2. Subir comprobante a Cloudinary si fue adjuntado[cite: 12]
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

    # 3. Registrar el primer abono
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
    sube el comprobante a Cloudinary y descuenta automáticamente del saldo pendiente[cite: 12].
    """
    factura = db.query(Factura).filter(
        Factura.id == factura_id, 
        Factura.es_plan_acumulativo == True
    ).first()

    if not factura:
        raise HTTPException(status_code=404, detail="Pedido acumulativo no encontrado.")

    if monto > factura.saldo_pendiente:
        raise HTTPException(
            status_code=400, 
            detail=f"El monto del abono (${monto:.2f}) supera el saldo pendiente (${factura.saldo_pendiente:.2f})."
        )

    # Subir comprobante a Cloudinary[cite: 12]
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

    # Registrar el abono en la base de datos[cite: 12]
    abono = AbonoPlanAcumulativo(
        factura_id=factura.id,
        monto=monto,
        comprobante_url=comprobante_url,
        referencia_bancaria=referencia_bancaria,
        observacion=observacion
    )
    db.add(abono)

    # Actualizar saldo pendiente y estado de la orden[cite: 12]
    factura.saldo_pendiente -= monto
    if factura.saldo_pendiente <= 0:
        factura.saldo_pendiente = 0.0
        factura.estado_acumulativo = "COMPLETADO"

    db.commit()

    return {
        "status": "success",
        "mensaje": "Abono registrado con éxito.",
        "nuevo_saldo_pendiente": round(factura.saldo_pendiente, 2),
        "estado_acumulativo": factura.estado_acumulativo
    }


@router_acumulativo.get("/admin/cartera-acumulativa")
@router_acumulativo.get("/reporte/cartera")
async def obtener_cartera_acumulativa(db: Session = Depends(get_db)):
    """
    Retorna el resumen financiero y la lista detallada de todas las órdenes 
    con plan acumulativo para el control diario de cobranza en el Panel de Administración[cite: 12].
    """
    facturas_acumulativas = db.query(Factura).filter(Factura.es_plan_acumulativo == True).all()
    
    detalles = []
    total_cartera = 0.0
    total_recaudado = 0.0
    total_pendiente = 0.0

    for f in facturas_acumulativas:
        recaudado = sum(a.monto for a in f.abonos_acumulativos)
        pendiente = f.total_factura - recaudado

        total_cartera += f.total_factura
        total_recaudado += recaudado
        total_pendiente += pendiente

        cliente_nombre = f.entidad_nombre
        cliente_telefono = "N/D"
        if f.cliente:
            cliente_nombre = f.cliente.nombre
            cliente_telefono = f.cliente.telefono or "N/D"

        detalles.append({
            "factura_id": f.id,
            "numero_factura": f.numero_factura,
            "cliente": cliente_nombre,
            "telefono": cliente_telefono,
            "fecha": f.fecha_factura.strftime("%Y-%m-%d"),
            "total_orden": round(f.total_factura, 2),
            "total_abonado": round(recaudado, 2),
            "saldo_pendiente": round(pendiente, 2),
            "estado": f.estado_acumulativo,
            "cantidad_abonos": len(f.abonos_acumulativos)
        })

    return {
        "resumen": {
            "total_cartera": round(total_cartera, 2),
            "total_recaudado": round(total_recaudado, 2),
            "total_pendiente": round(total_pendiente, 2),
            "planes_activos": len(facturas_acumulativas)
        },
        "detalles": detalles
    }