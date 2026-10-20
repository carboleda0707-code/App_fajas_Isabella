from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy import text

router = APIRouter()

@router.get("/despachos/reporte")
def obtener_reporte_despachos(db: Session = Depends(get_db)):
    try:
        query = text("""
            SELECT 
                f.id,
                f.numero_factura,
                f.fecha_factura,
                f.entidad_nombre,
                f.cliente,
                f.entidad_ruc,
                f.ruc_cedula,
                f.provincia,
                f.ciudad,
                f.direccion_entrega,
                f.direccion,
                f.referencia_direccion,
                f.referencia,
                f.courier_nombre,
                f.courier,
                f.repartidor,
                f.numero_guia,
                f.numero_guia_2,
                f.numero_control,
                f.estado_despacho,
                f.total_factura,
                f.total
            FROM facturas f
            ORDER BY f.id DESC
        """)
        
        result = db.execute(query).fetchall()
        reporte = []

        for row in result:
            d = row._asdict() if hasattr(row, '_asdict') else dict(zip(row.keys(), row))
            
            val_nc = d.get('numero_control')
            ctrl_str = str(val_nc).strip() if (val_nc is not None and str(val_nc).strip() not in ["None", "null", "", "SIN CONTROL", "nan", "NaN"]) else "SIN CONTROL"

            val_g2 = d.get('numero_guia_2')
            g2_str = str(val_g2).strip() if (val_g2 is not None and str(val_g2).strip() not in ["None", "null", "", "SIN GUÍA 2"]) else "SIN GUÍA 2"

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
                "numero_guia_2": g2_str,
                "numero_control": ctrl_str,
                "estado_despacho": d.get('estado_despacho') or "PENDIENTE",
                "total": float(d.get('total_factura') or d.get('total') or 0.0)
            })

        return reporte

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al obtener reporte: {str(e)}")


@router.post("/despachos/actualizar")
def actualizar_despacho(payload: dict, db: Session = Depends(get_db)):
    try:
        factura_id = payload.get("factura_id") or payload.get("id")
        numero_guia = payload.get("numero_guia")
        numero_guia_2 = payload.get("numero_guia_2")
        numero_control = payload.get("numero_control")
        repartidor = payload.get("repartidor")
        estado_despacho = payload.get("estado_despacho")

        if not factura_id:
            raise HTTPException(status_code=400, detail="ID de orden/factura es requerido.")

        query = text("""
            UPDATE facturas 
            SET numero_guia = :numero_guia,
                numero_guia_2 = :numero_guia_2,
                numero_control = :numero_control,
                repartidor = :repartidor,
                estado_despacho = :estado_despacho
            WHERE id = :factura_id
        """)

        db.execute(query, {
            "numero_guia": numero_guia,
            "numero_guia_2": numero_guia_2,
            "numero_control": numero_control,
            "repartidor": repartidor,
            "estado_despacho": estado_despacho,
            "factura_id": factura_id
        })
        db.commit()

        return {
            "status": "success",
            "message": f"Orden {factura_id} actualizada con éxito.",
            "numero_guia": numero_guia,
            "numero_guia_2": numero_guia_2,
            "numero_control": numero_control,
            "repartidor": repartidor,
            "estado_despacho": estado_despacho
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno al actualizar despacho: {str(e)}")