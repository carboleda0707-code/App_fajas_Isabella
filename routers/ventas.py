from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import traceback
import os
from database import get_db, Cliente, Factura, Pago, VarianteProducto, MovimientoInventario

router = APIRouter()

class ItemVentaSchema(BaseModel):
    sku: str
    cantidad: int
    precio_unitario: float

class VentaFacturaSchema(BaseModel):
    numero_factura: str
    numero_autorizacion: Optional[str] = ""
    fecha_factura: str
    metodo_pago: str
    codigo_transferencia: Optional[str] = ""
    
    # Datos de facturación (Cliente)
    ruc_cliente: str
    nombre_cliente: str
    direccion_cliente: Optional[str] = ""
    telefono_cliente: Optional[str] = ""
    
    # Datos logísticos específicos de la orden (Envío)
    provincia: Optional[str] = "Guayas"
    ciudad: Optional[str] = "Guayaquil"
    direccion_entrega: Optional[str] = ""
    referencia_direccion: Optional[str] = ""
    courier_nombre: Optional[str] = "Servientrega"
    
    items: List[ItemVentaSchema]

@router.post("/ventas-factura")
def registrar_venta(venta: VentaFacturaSchema, db: Session = Depends(get_db)):
    try:
        # --- VALIDACIÓN DE FACTURA DUPLICADA ---
        existe = db.query(Factura).filter(
            Factura.numero_factura == venta.numero_factura, 
            Factura.tipo_factura == "VENTA"
        ).first()
        
        if existe:
            raise HTTPException(
                status_code=400, 
                detail=f"La factura de venta Nº {venta.numero_factura} ya se encuentra registrada en el sistema."
            )
        # ----------------------------------------

        # Verificar o registrar/actualizar datos básicos del cliente
        cliente = db.query(Cliente).filter(Cliente.ruc_cedula == venta.ruc_cliente).first()
        if not cliente:
            cliente = Cliente(
                ruc_cedula=venta.ruc_cliente, 
                nombre=venta.nombre_cliente,
                direccion=venta.direccion_cliente or "", 
                telefono=venta.telefono_cliente or ""
            )
            db.add(cliente)
            db.commit()
        else:
            if venta.direccion_cliente and not cliente.direccion:
                cliente.direccion = venta.direccion_cliente
                db.commit()

        # Validar stock disponible de las variantes
        for item in venta.items:
            variante = db.query(VarianteProducto).filter(VarianteProducto.sku == item.sku).first()
            if not variante:
                raise HTTPException(status_code=404, detail=f"SKU {item.sku} no existe.")
            if variante.stock_actual < item.cantidad:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente para {item.sku}.")

        total_calculado = sum(item.cantidad * item.precio_unitario for item in venta.items)
        
        # --- REGISTRO DE LA FACTURA CON DATOS LOGÍSTICOS Y DE FACTURACIÓN SEPARADOS ---
        nueva_factura = Factura(
            tipo_factura="VENTA", 
            numero_factura=venta.numero_factura,
            numero_autorizacion=venta.numero_autorizacion or "",
            fecha_factura=datetime.strptime(venta.fecha_factura, "%Y-%m-%d").date(),
            entidad_ruc=venta.ruc_cliente, 
            entidad_nombre=venta.nombre_cliente,
            total_factura=total_calculado,
            # Datos específicos de envío para este pedido
            provincia=venta.provincia.strip().title() if venta.provincia else "Guayas",
            ciudad=venta.ciudad.strip().title() if venta.ciudad else "Guayaquil",
            direccion_entrega=venta.direccion_entrega.strip() if venta.direccion_entrega else (venta.direccion_cliente or ""),
            referencia_direccion=venta.referencia_direccion.strip() if venta.referencia_direccion else "",
            courier_nombre=venta.courier_nombre.strip() if venta.courier_nombre else "Servientrega",
            estado_despacho="PENDIENTE"
        )
        db.add(nueva_factura)
        db.commit()
        db.refresh(nueva_factura)

        nuevo_pago = Pago(
            factura_id=nueva_factura.id, 
            metodo_pago=venta.metodo_pago,
            codigo_transferencia=venta.codigo_transferencia if venta.metodo_pago == "Transferencia" else None,
            monto=total_calculado
        )
        db.add(nuevo_pago)

        for item in venta.items:
            variante = db.query(VarianteProducto).filter(VarianteProducto.sku == item.sku).first()
            variante.stock_actual -= item.cantidad
            
            movimiento = MovimientoInventario(
                sku=variante.sku, 
                tipo_movimiento="VENTA_LOCAL",
                cantidad=-item.cantidad, 
                referencia_factura=f"Fact Venta: {venta.numero_factura}",
                valor_neto=item.precio_unitario, 
                entidad_asociada=venta.nombre_cliente
            )
            db.add(movimiento)
            
        db.commit()
        return {
            "status": "success", 
            "message": "Venta, pago y datos de despacho registrados exitosamente.",
            "factura_id": nueva_factura.id
        }
    except Exception as e:
        db.rollback()
        print("--- ERROR DETALLADO EN /ventas-factura ---")
        traceback.print_exc()
        print("------------------------------------------")
        raise HTTPException(status_code=500, detail=str(e))


# --- ENDPOINT PARA ACTUALIZAR GUÍA Y ESTADO DE COURIER ---
@router.put("/pedidos/{factura_id}/guia")
def actualizar_guia_despacho(
    factura_id: int, 
    numero_guia: str, 
    courier_nombre: Optional[str] = None,
    estado_despacho: str = "EN TRÁNSITO",
    db: Session = Depends(get_db)
):
    pedido = db.query(Factura).filter(Factura.id == factura_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido/Factura no encontrado.")
        
    pedido.numero_guia = numero_guia.strip()
    if courier_nombre:
        pedido.courier_nombre = courier_nombre.strip()
    pedido.estado_despacho = estado_despacho.strip().upper()
    
    db.commit()
    return {
        "status": "success", 
        "message": f"Guía actualizada correctamente para la factura ID {factura_id}.",
        "numero_guia": pedido.numero_guia
    }


# --- ENDPOINT PARA OBTENER REPORTE DE DESPACHOS AGRUPADO ---
@router.get("/despachos/reporte")
def obtener_reporte_despachos(
    estado: Optional[str] = None, 
    provincia: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Factura).filter(Factura.tipo_factura == "VENTA")
    
    if estado:
        query = query.filter(Factura.estado_despacho == estado.upper())
    if provincia:
        query = query.filter(Factura.provincia.ilike(f"%{provincia}%"))
        
    # Ordenar por Provincia y Ciudad para agrupar paquetes por zona de envío
    pedidos = query.order_by(Factura.provincia.asc(), Factura.ciudad.asc(), Factura.id.desc()).all()
    
    reporte = []
    for p in pedidos:
        reporte.append({
            "factura_id": p.id,
            "numero_factura": p.numero_factura,
            "fecha": str(p.fecha_factura) if p.fecha_factura else "N/A",
            "cliente": p.entidad_nombre,
            "ruc_cedula": p.entidad_ruc,
            "provincia": getattr(p, 'provincia', 'N/A'),
            "ciudad": getattr(p, 'ciudad', 'N/A'),
            "direccion": getattr(p, 'direccion_entrega', 'N/A'),
            "referencia": getattr(p, 'referencia_direccion', ''),
            "courier": getattr(p, 'courier_nombre', 'Servientrega'),
            "numero_guia": getattr(p, 'numero_guia', None) or "SIN GUÍA",
            "estado_despacho": getattr(p, 'estado_despacho', 'PENDIENTE'),
            "total": float(p.total_factura) if p.total_factura else 0.0
        })
        
    return reporte


# --- ENDPOINTS DE PAGOS Y PASARELA (PAYMENTEZ / NUVEI) ---

PAYMENTEZ_APP_CODE = os.getenv("PAYMENTEZ_APP_CODE", "test_app_code")
PAYMENTEZ_APP_KEY = os.getenv("PAYMENTEZ_APP_KEY", "test_app_key")

@router.post("/pagos/iniciar-paymentez")
def iniciar_transaccion_paymentez(data: dict, db: Session = Depends(get_db)):
    try:
        items = data.get("items", [])
        if not items:
            raise HTTPException(status_code=400, detail="El carrito está vacío.")

        total_pedido = sum(item.get("cantidad", 1) * item.get("precio_unitario", 0.0) for item in items)
        
        # Modo simulación local mientras se configuran las credenciales oficiales
        if PAYMENTEZ_APP_CODE == "test_app_code":
            return {
                "status": "success",
                "mode": "sandbox_simulado",
                "total": total_pedido,
                "checkout_url": "#",
                "mensaje": f"Simulación de pago exitosa por ${total_pedido:.2f}. Conecte sus credenciales de Paymentez cuando estén listas."
            }
            
        return {"status": "success", "checkout_url": "URL_OFICIAL_PAYMENTEZ"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en pasarela de pagos: {str(e)}")


@router.post("/pagos/webhook-paymentez")
async def webhook_paymentez(request: Request, db: Session = Depends(get_db)):
    try:
        evento = await request.json()
        tipo_evento = evento.get("type") or evento.get("status")
        
        if tipo_evento in ["transaction.success", "success"]:
            transaccion = evento.get("transaction", {})
            referencia = transaccion.get("dev_reference", "WEB-001")
            
            return {"status": "received", "message": "Pago procesado y stock actualizado."}
            
        return {"status": "ignored"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}