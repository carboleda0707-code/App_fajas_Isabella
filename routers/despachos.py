from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Factura
from datetime import date

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
        # Mapeo robusto compatible con control_numero o numero_control
        val_control = getattr(p, 'control_numero', None) or getattr(p, 'numero_control', None) or getattr(p, 'codigo_control', None)
        
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
            "numero_control": str(val_control).strip() if (val_control and str(val_control).strip() not in ["None", "null", ""]) else "SIN CONTROL",
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
    numero_guia = payload.get("numero_guia", "SIN GUÍA")
    numero_control_payload = str(payload.get("numero_control", "")).strip()
    estado_despacho = payload.get("estado_despacho", "PENDIENTE").upper().strip()

    ctrl_actual_bd = getattr(factura, 'control_numero', None) or getattr(factura, 'numero_control', None)

    # --- LÓGICA DE SECUENCIAL DIARIO AUTOMÁTICO AL EMPACAR ---
    if estado_despacho in ["EMPACADO", "EN TRÁNSITO", "ENTREGADO"] and (not ctrl_actual_bd or str(ctrl_actual_bd).strip() in ["SIN CONTROL", "", "None"]):
        if not numero_control_payload or numero_control_payload in ["SIN CONTROL", "", "None"]:
            ordenes_venta = db.query(Factura).filter(Factura.tipo_factura == "VENTA").all()
            max_num = 0
            for ord_item in ordenes_venta:
                ctrl_val = getattr(ord_item, 'control_numero', None) or getattr(ord_item, 'numero_control', None)
                ctrl = str(ctrl_val or "").strip()
                if ctrl.isdigit():
                    val = int(ctrl)
                    if val > max_num:
                        max_num = val
            numero_control = str(max_num + 1)
        else:
            numero_control = numero_control_payload
    else:
        if numero_control_payload and numero_control_payload not in ["SIN CONTROL", "", "None"]:
            numero_control = numero_control_payload
        else:
            numero_control = str(ctrl_actual_bd).strip() if ctrl_actual_bd else "SIN CONTROL"

    # Guardar en ambas propiedades para total compatibilidad con SQLAlchemy
    if hasattr(factura, 'control_numero'):
        setattr(factura, 'control_numero', numero_control)
    if hasattr(factura, 'numero_control'):
        setattr(factura, 'numero_control', numero_control)

    factura.courier_nombre = courier.strip() if courier else "Servientrega"
    factura.repartidor = repartidor.strip() if repartidor else "N/D"
    factura.numero_guia = numero_guia.strip() if numero_guia else "SIN GUÍA"
    factura.estado_despacho = estado_despacho
    
    db.commit()
    db.refresh(factura)
    
    return {
        "status": "success",
        "message": f"Despacho de la Orden {factura.numero_factura} actualizado correctamente.",
        "numero_control": numero_control,
        "numero_guia": factura.numero_guia,
        "repartidor": factura.repartidor,
        "estado": factura.estado_despacho
    }