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
    try:
        sql = text("""
            SELECT id, numero_factura, fecha_factura, entidad_nombre, cliente, 
                   entidad_ruc, ruc_cedula, provincia, ciudad, direccion_entrega, 
                   direccion, referencia_direccion, referencia, courier_nombre, 
                   courier, repartidor, numero_guia, numero_control, 
                   estado_despacho, total_factura, total, tipo_factura
            FROM facturas 
            WHERE tipo_factura = 'VENTA' OR tipo_factura IS NULL
            ORDER BY id DESC
        """)
        result = db.execute(sql).fetchall()
        
        reporte = []
        for row in result:
            d = row._asdict() if hasattr(row, '_asdict') else dict(zip(row.keys(), row))
            
            val_nc = d.get('numero_control')
            ctrl_str = str(val_nc).strip() if (val_nc is not None and str(val_nc).strip() not in ["None", "null", "", "SIN CONTROL"]) else "SIN CONTROL"

            reporte.append({
                "factura_id": d.get('id'),
                "id": d.get('id'),
                "numero_factura": str(d.get('numero_factura')),
                "fecha": str(d.get('fecha_factura')) if d.get('fecha_factura') else "N/A",
                "cliente": d.get('entidad_nombre') or d.get('cliente') or "Consumidor Final",
                "ruc_cedula": d.get('entidad_ruc') or d.get('ruc_cedula') or "N/D",
                "provincia": d.get('provincia') or "Guayas",
                "ciudad": d.get('ciudad') or "Guayaquil",
                "direccion": d.get('direccion_entrega') or d.get('direccion') or "N/A",
                "referencia": d.get('referencia_direccion') or d.get('referencia') or "",
                "courier": d.get('courier_nombre') or d.get('courier') or "Servientrega",
                "repartidor": d.get('repartidor') or "N/D",
                "numero_guia": d.get('numero_guia') or "SIN GUÍA",
                "numero_control": d.get('numero_control') or "SIN CONTROL",  
                "estado_despacho": d.get('estado_despacho') or "PENDIENTE",
                "total": float(d.get('total_factura') or d.get('total') or 0.0)
            })
        return reporte
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener reporte: {str(e)}")

@router.post("/despachos/actualizar")
def actualizar_despacho(payload: dict, db: Session = Depends(get_db)):
    try:
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
            
        numero_control = payload.get("numero_control", "").strip()
        if not numero_control or numero_control.upper() in ["SIN CONTROL", "NONE", "NULL", ""]:
            numero_control = None

        estado_solicitado = payload.get("estado_despacho", "").upper().strip()

        if estado_solicitado == "ENTREGADO":
            if numero_guia == "SIN GUÍA":
                raise HTTPException(status_code=400, detail="⚠️ No se puede marcar como ENTREGADO sin un Número de Guía.")
            if not numero_control:
                raise HTTPException(status_code=400, detail="⚠️ No se puede marcar como ENTREGADO sin un Número de Control.")
            estado_despacho = "ENTREGADO"
        else:
            has_control = bool(numero_control)
            has_guia = bool(numero_guia != "SIN GUÍA")

            if has_control and has_guia:
                estado_despacho = "EN TRÁNSITO"
            elif has_control:
                estado_despacho = "EMPACADO"
            else:
                estado_despacho = "PENDIENTE"

        db.execute(text("""
            UPDATE facturas 
            SET numero_control = :ctrl, 
                courier_nombre = :courier, 
                repartidor = :repartidor, 
                numero_guia = :guia, 
                estado_despacho = :estado 
            WHERE id = :fid
        """), {
            "ctrl": numero_control,
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
            "numero_control": numero_control,
            "numero_guia": numero_guia,
            "repartidor": repartidor,
            "estado": estado_despacho
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno al actualizar despacho: {str(e)}")