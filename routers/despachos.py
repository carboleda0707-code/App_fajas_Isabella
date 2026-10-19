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
        # Lectura directa de la columna control_numero de la base de datos
        val_control = getattr(p, 'control_numero', None)
        if val_control is None and hasattr(p, '__dict__'):
            val_control = p.__dict__.get('control_numero')

        ctrl_str = str(val_control).strip() if (val_control is not None and str(val_control).strip() not in ["None", "null", ""]) else "SIN CONTROL"

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
            "numero_control": ctrl_str,
            "control_numero": ctrl_str,
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
    numero_guia = payload.get("numero_guia", "SIN GUÍA").strip()
    estado_solicitado = payload.get("estado_despacho", "").upper().strip()

    ctrl_actual_bd = getattr(factura, 'control_numero', None)
    ctrl_actual_str = str(ctrl_actual_bd).strip() if (ctrl_actual_bd is not None and str(ctrl_actual_bd).strip() not in ["None", "null", ""]) else ""

    # Regla: Autogenerar número de control si se registra guía o pasa a estado avanzado y no lo tenía
    if (numero_guia and numero_guia != "SIN GUÍA") or estado_solicitado in ["EMPACADO", "EN TRÁNSITO", "ENTREGADO"]:
        if not ctrl_actual_str or ctrl_actual_str == "SIN CONTROL":
            ordenes_venta = db.query(Factura).filter(Factura.tipo_factura == "VENTA").all()
            max_num = 0
            for ord_item in ordenes_venta:
                ctrl_val = getattr(ord_item, 'control_numero', None)
                ctrl = str(ctrl_val or "").strip()
                if ctrl.isdigit():
                    val = int(ctrl)
                    if val > max_num:
                        max_num = val
            ctrl_actual_str = str(max_num + 1)

    # Determinación automática o manual del estado según tus reglas exactas
    if estado_solicitado == "ENTREGADO":
        if not numero_guia or numero_guia == "SIN GUÍA":
            raise HTTPException(status_code=400, detail="⚠️ No se puede marcar como ENTREGADO sin un Número de Guía.")
        if not ctrl_actual_str or ctrl_actual_str == "SIN CONTROL":
            raise HTTPException(status_code=400, detail="⚠️ No se puede marcar como ENTREGADO sin un Número de Control.")
        estado_despacho = "ENTREGADO"
    else:
        has_control = bool(ctrl_actual_str and ctrl_actual_str not in ["SIN CONTROL", "None", "null", ""])
        has_guia = bool(numero_guia and numero_guia != "SIN GUÍA")

        if has_control and has_guia:
            estado_despacho = "EN TRÁNSITO"
        elif has_control:
            estado_despacho = "EMPACADO"
        else:
            estado_despacho = "PENDIENTE"

    # Guardar directamente en la columna real control_numero
    factura.control_numero = ctrl_actual_str if ctrl_actual_str != "SIN CONTROL" else None
    factura.courier_nombre = courier.strip() if courier else "Servientrega"
    factura.repartidor = repartidor.strip() if repartidor else "N/D"
    factura.numero_guia = numero_guia if numero_guia else "SIN GUÍA"
    factura.estado_despacho = estado_despacho
    
    db.commit()
    db.refresh(factura)
    
    return {
        "status": "success",
        "message": f"Orden {factura.numero_factura} actualizada con éxito.",
        "numero_control": ctrl_actual_str,
        "control_numero": ctrl_actual_str,
        "numero_guia": factura.numero_guia,
        "repartidor": factura.repartidor,
        "estado": factura.estado_despacho
    }