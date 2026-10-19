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
        # p.numero_control ahora lee directamente de la columna 'control_numero' de Postgres
        val_ctrl = p.numero_control
        if not val_ctrl or str(val_ctrl).strip() in ["None", "null", ""]:
            val_ctrl = "SIN CONTROL"

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
            "numero_control": str(val_ctrl).strip(),
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

    # Si viene un número de control se guarda, si no y se marca empacado, se calcula secuencial
    if not numero_control_payload or numero_control_payload in ["SIN CONTROL", "", "None"]:
        if estado_despacho in ["EMPACADO", "EN TRÁNSITO", "ENTREGADO"]:
            ordenes = db.query(Factura).filter(Factura.tipo_factura == "VENTA").all()
            max_num = 0
            for o in ordenes:
                c = str(o.numero_control or "").strip()
                if c.isdigit() and int(c) > max_num:
                    max_num = int(c)
            factura.numero_control = str(max_num + 1)
        else:
            factura.numero_control = "SIN CONTROL"
    else:
        factura.numero_control = numero_control_payload

    factura.courier_nombre = courier.strip() if courier else "Servientrega"
    factura.repartidor = repartidor.strip() if repartidor else "N/D"
    factura.numero_guia = numero_guia.strip() if numero_guia else "SIN GUÍA"
    factura.estado_despacho = estado_despacho
    
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