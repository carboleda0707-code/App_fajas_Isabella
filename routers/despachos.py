from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, Factura

router = APIRouter(tags=["Despachos y Logística"])

@router.get("/despachos/reporte")
def obtener_reporte_despachos(
    estado: str = None, 
    provincia: str = None,
    db: Session = Depends(get_db)
):
    sql = text("""
        SELECT id, numero_factura, tipo_factura, fecha_factura, entidad_nombre, entidad_ruc, 
               provincia, ciudad, direccion_entrega, referencia_direccion, courier_nombre, 
               repartidor, numero_guia, control_numero, estado_despacho, total_factura
        FROM facturas 
        WHERE tipo_factura = 'VENTA'
        ORDER BY id DESC
    """)
    result = db.execute(sql).fetchall()
    
    reporte = []
    for row in result:
        d = row._asdict() if hasattr(row, '_asdict') else dict(zip(row.keys(), row))
        
        ctrl_val = d.get('control_numero')
        ctrl_str = str(ctrl_val).strip() if (ctrl_val is not None and str(ctrl_val).strip() not in ["None", "null", "", "SIN CONTROL"]) else "SIN CONTROL"

        reporte.append({
            "factura_id": d.get('id'),
            "numero_factura": d.get('numero_factura'),
            "fecha": str(d.get('fecha_factura')) if d.get('fecha_factura') else "N/A",
            "cliente": d.get('entidad_nombre') or "Consumidor Final",
            "ruc_cedula": d.get('entidad_ruc') or "N/D",
            "provincia": d.get('provincia') or "Guayas",
            "ciudad": d.get('ciudad') or "Guayaquil",
            "direccion": d.get('direccion_entrega') or "N/A",
            "referencia": d.get('referencia_direccion') or "",
            "courier": d.get('courier_nombre') or "Servientrega",
            "repartidor": d.get('repartidor') or "N/D",
            "numero_guia": d.get('numero_guia') or "SIN GUÍA",
            "control_numero": ctrl_str,
            "estado_despacho": d.get('estado_despacho') or "PENDIENTE",
            "total": float(d.get('total_factura') or 0.0)
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
    
    courier = payload.get("courier", "Servientrega")
    repartidor = payload.get("repartidor", "N/D")
    numero_guia = payload.get("numero_guia", "SIN GUÍA").strip()
    if not numero_guia:
        numero_guia = "SIN GUÍA"
        
    estado_solicitado = payload.get("estado_despacho", "").upper().strip()

    # Leer control_numero directamente de la BD
    res_ctrl = db.execute(text("SELECT control_numero FROM facturas WHERE id = :fid"), {"fid": factura.id}).fetchone()
    ctrl_actual_str = str(res_ctrl[0]).strip() if (res_ctrl and res_ctrl[0] is not None and str(res_ctrl[0]).strip() not in ["None", "null", "", "SIN CONTROL"]) else ""

    # Autogenerar si hay guía o estado avanzado y no tiene control
    if (numero_guia != "SIN GUÍA") or estado_solicitado in ["EMPACADO", "EN TRÁNSITO", "ENTREGADO"]:
        if not ctrl_actual_str:
            res_max = db.execute(text("SELECT MAX(CAST(NULLIF(control_numero, '') AS INTEGER)) FROM facturas WHERE tipo_factura = 'VENTA' AND control_numero ~ '^[0-9]+$'")).fetchone()
            max_num = res_max[0] if res_max and res_max[0] is not None else 0
            ctrl_actual_str = str(max_num + 1)

    if estado_solicitado == "ENTREGADO":
        if numero_guia == "SIN GUÍA":
            raise HTTPException(status_code=400, detail="⚠️ No se puede marcar como ENTREGADO sin un Número de Guía.")
        if not ctrl_actual_str:
            raise HTTPException(status_code=400, detail="⚠️ No se puede marcar como ENTREGADO sin un Número de Control.")
        estado_despacho = "ENTREGADO"
    else:
        has_control = bool(ctrl_actual_str)
        has_guia = bool(numero_guia != "SIN GUÍA")

        if has_control and has_guia:
            estado_despacho = "EN TRÁNSITO"
        elif has_control:
            estado_despacho = "EMPACADO"
        else:
            estado_despacho = "PENDIENTE"

    # Actualizar control_numero en la BD
    db.execute(text("""
        UPDATE facturas 
        SET control_numero = :ctrl, 
            courier_nombre = :courier, 
            repartidor = :repartidor, 
            numero_guia = :guia, 
            estado_despacho = :estado 
        WHERE id = :fid
    """), {
        "ctrl": ctrl_actual_str if ctrl_actual_str else None,
        "courier": courier,
        "repartidor": repartidor,
        "guia": numero_guia,
        "estado": estado_despacho,
        "fid": factura.id
    })
    db.commit()
    
    return {
        "status": "success",
        "message": f"Orden {factura.numero_factura} actualizada con éxito.",
        "control_numero": ctrl_actual_str,
        "numero_guia": numero_guia,
        "repartidor": repartidor,
        "estado": estado_despacho
    }