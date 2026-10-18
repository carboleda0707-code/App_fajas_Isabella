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
            "repartidor": getattr(p, 'repartidor', 'N/D') or 'N/D',             # <--- Enviado al panel
            "numero_guia": getattr(p, 'numero_guia', None) or "SIN GUÍA",
            "numero_control": getattr(p, 'numero_control', None) or "SIN CONTROL", # <--- Enviado al panel
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
        factura = db.query(Factura).filter(Factura.numero_factura == numero_factura).first()
        
    if not factura:
        raise HTTPException(status_code=404, detail="Orden de Venta no encontrada en el sistema.")
    
    # Asignar y guardar los cambios de logística en PostgreSQL
    factura.courier_nombre = payload.get("courier", factura.courier_nombre)
    factura.repartidor = payload.get("repartidor", "N/D").strip()               # <--- Captura y guarda el repartidor
    factura.numero_guia = payload.get("numero_guia", "SIN GUÍA").strip()
    factura.numero_control = payload.get("numero_control", "SIN CONTROL").strip() # <--- Captura y guarda el número de control
    factura.estado_despacho = payload.get("estado_despacho", "PENDIENTE").upper().strip()
    
    db.commit()
    db.refresh(factura)
    
    return {
        "status": "success",
        "message": f"Despacho de la orden {factura.numero_factura} actualizado correctamente.",
        "numero_control": factura.numero_control,
        "repartidor": factura.repartidor,
        "estado": factura.estado_despacho
    }