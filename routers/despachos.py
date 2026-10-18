from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Factura

router = APIRouter(tags=["Despachos y Logística"])

@router.get("/despachos/reporte")
def obtener_reporte_despachos(
    estado: str = None, 
    provincia: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Factura).filter(Factura.tipo_factura == "VENTA")
    
    if estado and estado != "TODOS":
        query = query.filter(Factura.estado_despacho == estado.upper())
    if provincia:
        query = query.filter(Factura.provincia.ilike(f"%{provincia}%"))
        
    pedidos = query.order_by(Factura.provincia.asc(), Factura.ciudad.asc(), Factura.id.desc()).all()
    
    reporte = []
    for p in pedidos:
        reporte.append({
            "factura_id": p.id,
            "numero_factura": p.numero_factura,
            "fecha": str(p.fecha_factura) if p.fecha_factura else "N/A",
            "cliente": p.entidad_nombre,
            "ruc_cedula": p.entidad_ruc,
            "provincia": getattr(p, 'provincia', 'Guayas'),
            "ciudad": getattr(p, 'ciudad', 'Guayaquil'),
            "direccion": getattr(p, 'direccion_entrega', 'N/A'),
            "referencia": getattr(p, 'referencia_direccion', ''),
            "courier": getattr(p, 'courier_nombre', 'Servientrega'),
            "repartidor": getattr(p, 'repartidor', 'N/D') or 'N/D',
            "numero_guia": getattr(p, 'numero_guia', None) or "SIN GUÍA",
            "numero_control": getattr(p, 'numero_control', None) or "SIN CONTROL",
            "estado_despacho": getattr(p, 'estado_despacho', 'PENDIENTE'),
            "total": float(p.total_factura) if p.total_factura else 0.0
        })
    return reporte

@router.post("/despachos/actualizar")
def actualizar_despacho(payload: dict, db: Session = Depends(get_db)):
    factura_id = payload.get("factura_id")
    numero_factura = payload.get("numero_factura")
    
    factura = None
    if factura_id:
        factura = db.query(Factura).filter(Factura.id == factura_id).first()
    
    # Búsqueda flexible de la orden de venta
    if not factura and numero_factura:
        num_str = str(numero_factura).strip()
        factura = db.query(Factura).filter(
            (Factura.numero_factura == num_str) | 
            (Factura.id == int(num_str) if num_str.isdigit() else False)
        ).first()
        
    if not factura:
        raise HTTPException(status_code=404, detail="Orden de Venta no encontrada en el sistema.")
    
    courier = payload.get("courier", factura.courier_nombre)
    repartidor = payload.get("repartidor", "N/D")
    numero_guia = payload.get("numero_guia", "SIN GUÍA")
    numero_control_payload = payload.get("numero_control", "")
    estado_despacho = payload.get("estado_despacho", "PENDIENTE")

    # --- LÓGICA DE SECUENCIAL DIARIO AUTOMÁTICO (SOLO AL EMPACAR) ---
    # Si la orden se marca como EMPACADO y aún no tiene número de control asignado,
    # calculamos el siguiente número secuencial (1, 2, 3...) basado en las órdenes de su misma fecha.
    if estado_despacho.upper() == "EMPACADO" and (not factura.numero_control or factura.numero_control in ["SIN CONTROL", ""]):
        if not numero_control_payload or numero_control_payload in ["SIN CONTROL", ""]:
            fecha_obj = factura.fecha_factura
            ordenes_misma_fecha = db.query(Factura).filter(Factura.fecha_factura == fecha_obj).all()
            max_num = 0
            for ord_item in ordenes_misma_fecha:
                ctrl = str(ord_item.numero_control or "").strip()
                if ctrl.isdigit():
                    val = int(ctrl)
                    if val > max_num:
                        max_num = val
            numero_control = str(max_num + 1)
        else:
            numero_control = str(numero_control_payload).strip()
    else:
        # Mantener el control existente o el enviado manualmente
        if numero_control_payload and numero_control_payload not in ["SIN CONTROL", ""]:
            numero_control = str(numero_control_payload).strip()
        else:
            numero_control = factura.numero_control or "SIN CONTROL"

    # Asignar valores finales
    factura.courier_nombre = courier.strip() if courier else "Servientrega"
    factura.repartidor = repartidor.strip() if repartidor else "N/D"
    factura.numero_guia = numero_guia.strip() if numero_guia else "SIN GUÍA"
    factura.numero_control = numero_control
    factura.estado_despacho = estado_despacho.upper().strip()
    
    db.commit()
    db.refresh(factura)
    
    return {
        "status": "success",
        "message": f"Despacho de la Orden {factura.numero_factura} actualizado correctamente.",
        "numero_control": factura.numero_control,
        "numero_guia": factura.numero_guia,
        "repartidor": factura.repartidor,
        "estado": factura.estado_despacho
    }