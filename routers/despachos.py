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
    # Consulta SQL directa para asegurar lectura de la columna física 'control_numero' en Postgres
    sql_query = text("""
        SELECT id, numero_factura, tipo_factura, fecha_factura, entidad_nombre, entidad_ruc, 
               provincia, ciudad, direccion_entrega, referencia_direccion, courier_nombre, 
               repartidor, numero_guia, control_numero, estado_despacho, total_factura
        FROM facturas 
        WHERE tipo_factura = 'VENTA'
    """)
    result = db.execute(sql_query).fetchall()
    
    reporte = []
    for row in result:
        # Mapeo por nombre de columna devuelto por SQL
        row_dict = row._asdict() if hasattr(row, '_asdict') else dict(row)
        
        # Filtros opcionales en memoria
        est_db = str(row_dict.get('estado_despacho') or 'PENDIENTE').upper().strip()
        prov_db = str(row_dict.get('provincia') or 'Guayas')
        
        if estado and estado != "TODOS" and est_db != estado.upper():
            continue
        if provincia and provincia.lower() not in prov_db.lower():
            continue
            
        val_control = row_dict.get('control_numero')
        ctrl_str = str(val_control).strip() if (val_control is not None and str(val_control).strip() not in ["None", "null", "", "SIN CONTROL"]) else "SIN CONTROL"

        reporte.append({
            "factura_id": row_dict.get('id'),
            "numero_factura": row_dict.get('numero_factura'),
            "fecha": str(row_dict.get('fecha_factura')) if row_dict.get('fecha_factura') else "N/A",
            "cliente": row_dict.get('entidad_nombre') or "Consumidor Final",
            "ruc_cedula": row_dict.get('entidad_ruc') or "N/D",
            "provincia": prov_db,
            "ciudad": row_dict.get('ciudad') or "Guayaquil",
            "direccion": row_dict.get('direccion_entrega') or "N/A",
            "referencia": row_dict.get('referencia_direccion') or "",
            "courier": row_dict.get('courier_nombre') or "Servientrega",
            "repartidor": row_dict.get('repartidor') or "N/D",
            "numero_guia": row_dict.get('numero_guia') or "SIN GUÍA",
            "numero_control": ctrl_str,
            "control_numero": ctrl_str,
            "estado_despacho": est_db,
            "total": float(row_dict.get('total_factura') or 0.0)
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

    # Leer control actual directamente con SQL
    res_ctrl = db.execute(text("SELECT control_numero FROM facturas WHERE id = :fid"), {"fid": factura.id}).fetchone()
    ctrl_actual_str = str(res_ctrl[0]).strip() if (res_ctrl and res_ctrl[0] is not None and str(res_ctrl[0]).strip() not in ["None", "null", ""]) else ""

    # Regla: Autogenerar número de control si se registra guía o pasa a estado avanzado y no lo tenía
    if (numero_guia and numero_guia != "SIN GUÍA") or estado_solicitado in ["EMPACADO", "EN TRÁNSITO", "ENTREGADO"]:
        if not ctrl_actual_str or ctrl_actual_str == "SIN CONTROL":
            res_max = db.execute(text("SELECT MAX(CAST(NULLIF(control_numero, '') AS INTEGER)) FROM facturas WHERE tipo_factura = 'VENTA' AND control_numero ~ '^[0-9]+$'")).fetchone()
            max_num = res_max[0] if res_max and res_max[0] is not None else 0
            ctrl_actual_str = str(max_num + 1)

    # Determinación de estado según reglas exactas
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

    # Actualizar directamente con SQL para garantizar persistencia en control_numero
    db.execute(text("""
        UPDATE facturas 
        SET control_numero = :ctrl, 
            courier_nombre = :courier, 
            repartidor = :repartidor, 
            numero_guia = :guia, 
            estado_despacho = :estado 
        WHERE id = :fid
    """), {
        "ctrl": ctrl_actual_str if ctrl_actual_str != "SIN CONTROL" else None,
        "courier": courier.strip() if courier else "Servientrega",
        "repartidor": repartidor.strip() if repartidor else "N/D",
        "guia": numero_guia if numero_guia else "SIN GUÍA",
        "estado": estado_despacho,
        "fid": factura.id
    })
    db.commit()
    
    return {
        "status": "success",
        "message": f"Orden {factura.numero_factura} actualizada con éxito.",
        "numero_control": ctrl_actual_str,
        "control_numero": ctrl_actual_str,
        "numero_guia": numero_guia,
        "repartidor": repartidor,
        "estado": estado_despacho
    }