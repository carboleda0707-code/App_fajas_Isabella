from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import traceback
import os
from database import get_db, Cliente, Factura, Pago, VarianteProducto, MovimientoInventario

router = APIRouter(tags=["Ventas y Clientes"])

# --- ESQUEMAS PARA CLIENTES ---
class ClienteSchema(BaseModel):
    ruc_cedula: str
    nombre: str
    ciudad: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    tipo_precio: Optional[str] = "REGULAR"
    descuento_porcentaje: Optional[float] = 0.0

# --- ESQUEMAS PARA VENTAS ---
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


# --- ENDPOINTS CRUD DE CLIENTES ---

@router.get("/clientes")
def obtener_clientes(db: Session = Depends(get_db)):
    clientes = db.query(Cliente).all()
    resultado = []
    for c in clientes:
        resultado.append({
            "id": c.id,
            "ruc_cedula": c.ruc_cedula,
            "nombre": c.nombre,
            "ciudad": c.ciudad or "",
            "telefono": c.telefono or "",
            "correo": c.correo or "",
            "direccion": c.direccion or "",
            "tipo_precio": c.tipo_precio or "REGULAR",
            "descuento_porcentaje": float(c.descuento_porcentaje or 0.0)
        })
    return resultado

@router.post("/clientes")
def crear_cliente(data: ClienteSchema, db: Session = Depends(get_db)):
    existente = db.query(Cliente).filter(Cliente.ruc_cedula == data.ruc_cedula).first()
    if existente:
        raise HTTPException(status_code=400, detail="El RUC o Cédula ya se encuentra registrado.")
    
    nuevo_cliente = Cliente(
        ruc_cedula=data.ruc_cedula,
        nombre=data.nombre,
        ciudad=data.ciudad.strip().title() if data.ciudad else None,
        telefono=data.telefono.strip() if data.telefono else None,
        correo=data.correo.strip().lower() if data.correo else None,
        direccion=data.direccion.strip() if data.direccion else None,
        tipo_precio=data.tipo_precio or "REGULAR",
        descuento_porcentaje=data.descuento_porcentaje or 0.0
    )
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return nuevo_cliente

@router.put("/clientes/{cliente_id}")
def actualizar_cliente(cliente_id: int, data: ClienteSchema, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    
    cliente.ruc_cedula = data.ruc_cedula.strip()
    cliente.nombre = data.nombre.strip()
    cliente.ciudad = data.ciudad.strip().title() if data.ciudad else None
    cliente.telefono = data.telefono.strip() if data.telefono else None
    cliente.correo = data.correo.strip().lower() if data.correo else None
    cliente.direccion = data.direccion.strip() if data.direccion else None
    cliente.tipo_precio = data.tipo_precio or "REGULAR"
    cliente.descuento_porcentaje = data.descuento_porcentaje or 0.0
    
    db.commit()
    db.refresh(cliente)
    return {"status": "success", "mensaje": "Cliente actualizado correctamente.", "cliente_id": cliente.id}

@router.delete("/clientes/{cliente_id}")
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    
    db.delete(cliente)
    db.commit()
    return {"status": "success", "mensaje": f"Cliente ID {cliente_id} eliminado correctamente."}


# --- ENDPOINT DE REPORTE Y LISTADO DE VENTAS CON RECÁLCULO ROBUSTO ---

@router.get("/ventas/reporte")
def obtener_reporte_ventas(db: Session = Depends(get_db)):
    facturas = db.query(Factura).filter(Factura.tipo_factura == "VENTA").all()
    resultado = []
    for f in facturas:
        # Recálculo robusto: si total_factura es 0 o nulo, sumamos los pagos asociados
        total_real = f.total_factura
        if not total_real or total_real == 0.0:
            total_real = sum(p.monto for p in f.pagos) if f.pagos else 0.0
            
        resultado.append({
            "id": f.id,
            "numero_factura": f.numero_factura,
            "fecha": str(f.fecha_factura),
            "ruc_cedula": f.entidad_ruc,
            "cliente": f.entidad_nombre,
            "total_factura": float(total_real),
            "provincia": f.provincia or "Guayas",
            "ciudad": f.ciudad or "Guayaquil",
            "direccion_entrega": f.direccion_entrega or "",
            "referencia_direccion": f.referencia_direccion or "",
            "courier": f.courier_nombre or "Servientrega",
            "numero_guia": f.numero_guia or "",
            "estado_despacho": f.estado_despacho or "PENDIENTE"
        })
    return resultado


# --- ENDPOINT REGISTRO DE VENTA ---

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

        # Verificar o registrar/actualizar datos básicos del cliente
        cliente = db.query(Cliente).filter(Cliente.ruc_cedula == venta.ruc_cliente).first()
        if not cliente:
            cliente = Cliente(
                ruc_cedula=venta.ruc_cliente, 
                nombre=venta.nombre_cliente,
                direccion=venta.direccion_cliente or "", 
                telefono=venta.telefono_cliente or "",
                ciudad=venta.ciudad or "Guayaquil"
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
            "message": "Venta, pago y datos logísticos registrados exitosamente.",
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
def actualizar_guia_logistica(
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


# --- ENDPOINTS DE PAGOS Y PASARELA ---

PAYMENTEZ_APP_CODE = os.getenv("PAYMENTEZ_APP_CODE", "test_app_code")
PAYMENTEZ_APP_KEY = os.getenv("PAYMENTEZ_APP_KEY", "test_app_key")

@router.post("/pagos/iniciar-paymentez")
def iniciar_transaccion_paymentez(data: dict, db: Session = Depends(get_db)):
    try:
        items = data.get("items", [])
        if not items:
            raise HTTPException(status_code=400, detail="El carrito está vacío.")

        total_pedido = sum(item.get("cantidad", 1) * item.get("precio_unitario", 0.0) for item in items)
        
        if PAYMENTEZ_APP_CODE == "test_app_code":
            return {
                "status": "success",
                "mode": "sandbox_simulado",
                "total": total_pedido,
                "checkout_url": "#",
                "mensaje": f"Simulación de pago exitosa por ${total_pedido:.2f}."
            }
            
        return {"status": "success", "checkout_url": "URL_OFICIAL_PAYMENTEZ"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en pasarela de pagos: {str(e)}")


@router.get("/debug/db-info")
def debug_db_info(db: Session = Depends(get_db)):
    from database import DATABASE_URL
    total_facturas = db.query(Factura).count()
    facturas_lista = [f.numero_factura for f in db.query(Factura).all()]
    return {
        "database_url": DATABASE_URL,
        "total_facturas": total_facturas,
        "numeros_facturas": facturas_lista
    }