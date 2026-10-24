from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Factura

# Usamos el prefijo /api/logistica para que coincida con las peticiones de Streamlit
router = APIRouter(prefix="/api/logistica", tags=["Logística y Despachos"])

@router.get("/reporte")
def obtener_reporte_logistica(db: Session = Depends(get_db)):
    facturas = db.query(Factura).filter(Factura.tipo_factura == "VENTA").all()
    resultado = []
    for f in facturas:
        val_nc = f.numero_control
        ctrl_str = str(val_nc).strip() if (val_nc is not None and str(val_nc).strip() not in ["None", "null", "", "SIN CONTROL", "nan", "NaN"]) else "SIN CONTROL"

        val_g = f.numero_guia
        guia_str = str(val_g).strip() if (val_g is not None and str(val_g).strip() not in ["None", "null", "", "SIN GUÍA", "nan", "NaN"]) else "SIN GUÍA"

        val_rep = f.repartidor
        rep_str = str(val_rep).strip() if (val_rep is not None and str(val_rep).strip() not in ["None", "null", "", "N/D", "nan", "NaN"]) else "N/D"

        resultado.append({
            "factura_id": f.id,
            "numero_factura": f.numero_factura,
            "fecha": str(f.fecha_factura),
            "ruc_cedula": f.entidad_ruc,
            "cliente": f.entidad_nombre,
            "total_norm": f.total_factura,
            "provincia": f.provincia or "Guayas",
            "ciudad": f.ciudad or "Guayaquil",
            "direccion": f.direccion_entrega or "",
            "referencia": f.referencia_direccion or "",
            "courier_nombre": f.courier_nombre or "Servientrega",
            "courier": f.courier_nombre or "Servientrega",
            "repartidor": rep_str,
            "numero_guia": guia_str,
            "numero_control": ctrl_str,
            "estado_despacho": f.estado_despacho or "PENDIENTE",
            "items": []
        })
    return resultado

@router.post("/actualizar")
def actualizar_estado_logistica(data: dict, db: Session = Depends(get_db)):
    factura_id = data.get("factura_id")
    numero_control = data.get("numero_control")
    courier = data.get("courier")
    repartidor = data.get("repartidor")
    numero_guia = data.get("numero_guia")
    estado_despacho = data.get("estado_despacho")

    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")

    if numero_control:
        factura.numero_control = numero_control.strip()
    if courier:
        factura.courier_nombre = courier.strip()
    if repartidor:
        factura.repartidor = repartidor.strip()
    if numero_guia:
        factura.numero_guia = numero_guia.strip()
    if estado_despacho:
        factura.estado_despacho = estado_despacho.strip().upper()
    
    db.commit()
    return {
        "status": "success", 
        "message": f"Orden Nº {factura.numero_factura} actualizada correctamente a {factura.estado_despacho}."
    }