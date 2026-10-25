from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import get_db, Cliente, Factura, Pago, MovimientoInventario
from typing import Optional
import os
import shutil
import json
import urllib.parse
from datetime import date, datetime
import traceback
import hashlib
from config import TELEFONO_WHATSAPP

router = APIRouter(prefix="/api/web/auth", tags=["Autenticación Clientes Web"])

def generar_hash_sha256(password: str) -> str:
    """Genera el hash SHA-256 estricto para las contraseñas."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class RegistroWebSchema(BaseModel):
    nombre: str
    correo: EmailStr
    password: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None

class LoginWebSchema(BaseModel):
    correo: EmailStr
    password: str

class SetPasswordSchema(BaseModel):
    correo: EmailStr
    password: str
    password_confirm: str

@router.post("/registro")
def registrar_cliente_web(data: RegistroWebSchema, db: Session = Depends(get_db)):
    try:
        existente = db.query(Cliente).filter(Cliente.correo == data.correo).first()
        if existente:
            if existente.password:
                raise HTTPException(status_code=400, detail="Este correo ya se encuentra registrado.")
            else:
                # Si ya existía por transferencia previa, activamos su cuenta y asignamos la contraseña
                existente.nombre = data.nombre
                existente.password = generar_hash_sha256(data.password)
                existente.telefono = data.telefono or existente.telefono
                existente.direccion = data.direccion or existente.direccion
                existente.cliente_web = True
                db.commit()
                db.refresh(existente)
                return {
                    "status": "success",
                    "mensaje": "¡Cuenta activada y registrada exitosamente!",
                    "cliente": {
                        "id": existente.id,
                        "nombre": existente.nombre,
                        "correo": existente.correo,
                        "telefono": existente.telefono,
                        "direccion": existente.direccion
                    }
                }
        
        hashed_password = generar_hash_sha256(data.password)
        
        nuevo_cliente = Cliente(
            ruc_cedula=data.correo[:20], # Generación temporal si no provee cédula en registro directo
            nombre=data.nombre,
            correo=data.correo,
            password=hashed_password,
            telefono=data.telefono,
            direccion=data.direccion,
            cliente_web=True
        )
        db.add(nuevo_cliente)
        db.commit()
        db.refresh(nuevo_cliente)
        
        return {
            "status": "success",
            "mensaje": "¡Cuenta creada exitosamente!",
            "cliente": {
                "id": nuevo_cliente.id,
                "nombre": nuevo_cliente.nombre,
                "correo": nuevo_cliente.correo,
                "telefono": nuevo_cliente.telefono,
                "direccion": nuevo_cliente.direccion
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        error_detallado = traceback.format_exc()
        print("ERROR EN REGISTRO:", error_detallado)
        raise HTTPException(status_code=400, detail=f"Error interno: {str(e)}")

@router.post("/login")
def login_cliente_web(data: LoginWebSchema, db: Session = Depends(get_db)):
    try:
        cliente = db.query(Cliente).filter(Cliente.correo == data.correo).first()
        
        if not cliente:
            raise HTTPException(status_code=401, detail="Correo no registrado en el sistema.")
        
        # Si realizó compra por transferencia y aún no configura su contraseña
        if not cliente.password:
            return {
                "status": "requiere_password",
                "mensaje": "Detectamos una compra previa por transferencia. Por favor configure su contraseña.",
                "correo": cliente.correo
            }
        
        password_hash = generar_hash_sha256(data.password)
        if cliente.password != password_hash:
            raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
        
        return {
            "status": "success",
            "mensaje": f"¡Bienvenido de nuevo, {cliente.nombre}!",
            "cliente": {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "correo": cliente.correo,
                "telefono": cliente.telefono,
                "direccion": cliente.direccion
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en login: {str(e)}")

@router.post("/configurar-password")
def configurar_password_inicial(data: SetPasswordSchema, db: Session = Depends(get_db)):
    try:
        if data.password != data.password_confirm:
            raise HTTPException(status_code=400, detail="Las contraseñas no coinciden.")

        cliente = db.query(Cliente).filter(Cliente.correo == data.correo).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado.")

        cliente.password = generar_hash_sha256(data.password)
        cliente.cliente_web = True
        db.commit()

        return {
            "status": "success",
            "mensaje": "Contraseña configurada exitosamente. Ya puede iniciar sesión."
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al configurar contraseña: {str(e)}")

@router.get("/pedidos/{cliente_id}")
def obtener_historial_pedidos(cliente_id: int, db: Session = Depends(get_db)):
    facturas = db.query(Factura).filter(Factura.cliente_id == cliente_id).all()
    
    resultado = []
    for f in facturas:
        val_nc = f.numero_control
        ctrl_str = str(val_nc).strip() if (val_nc is not None and str(val_nc).strip() not in ["None", "null", "", "SIN CONTROL", "nan", "NaN"]) else "SIN CONTROL"

        resultado.append({
            "factura_id": f.id,
            "numero_factura": f.numero_factura,
            "fecha": str(f.fecha_factura),
            "total": f.total_factura,
            "estado_despacho": f.estado_despacho or "PENDIENTE",
            "courier": f.courier_nombre or "Pendiente",
            "numero_guia": f.numero_guia or "SIN GUÍA",
            "numero_control": ctrl_str
        })
        
    return resultado

@router.post("/checkout-whatsapp")
async def checkout_whatsapp(
    nombre: str = Form(...),
    telefono: str = Form(...),
    correo: Optional[str] = Form(None),
    ruc_cedula: str = Form(...),
    razon_social: str = Form(...),
    provincia: str = Form(...),
    ciudad: str = Form(...),
    direccion: str = Form(...),
    referencia: Optional[str] = Form(None),
    items: str = Form(...),
    comprobante: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        # 1. Registrar o actualizar automáticamente al cliente en la tabla unificada con cliente_web = True
        cliente = None
        if correo:
            cliente = db.query(Cliente).filter(Cliente.correo == correo.lower().strip()).first()
        if not cliente:
            cliente = db.query(Cliente).filter(Cliente.ruc_cedula == ruc_cedula).first()

        if cliente:
            cliente.nombre = razon_social
            cliente.telefono = telefono
            cliente.direccion = direccion
            cliente.ciudad = ciudad
            cliente.cliente_web = True
            if correo and not cliente.correo:
                cliente.correo = correo.lower().strip()
            db.commit()
        else:
            cliente = Cliente(
                ruc_cedula=ruc_cedula,
                nombre=razon_social,
                correo=correo.lower().strip() if correo else None,
                telefono=telefono,
                direccion=direccion,
                ciudad=ciudad,
                tipo_precio="REGULAR",
                cliente_web=True,
                password=None # Sin contraseña hasta que decida registrarse/loguearse
            )
            db.add(cliente)
            db.commit()
            db.refresh(cliente)

        # 2. Guardar la imagen del comprobante de pago si fue adjuntada
        ruta_comprobante = None
        if comprobante and comprobante.filename:
            dir_comprobantes = os.path.join("web", "comprobantes")
            os.makedirs(dir_comprobantes, exist_ok=True)
            ruta_fisica = os.path.join(dir_comprobantes, comprobante.filename)
            with open(ruta_fisica, "wb") as buffer:
                shutil.copyfileobj(comprobante.file, buffer)
            ruta_comprobante = f"comprobantes/{comprobante.filename}"

        # 3. Parsear ítems y calcular el total de la orden
        lista_items = json.loads(items)
        total_pedido = sum(float(item.get("precio", 0)) * int(item.get("cantidad", 1)) for item in lista_items)

        # 4. Generar número de orden interno
        prefijo_orden = datetime.now().strftime("%y%m")
        conteo = db.query(Factura).count() + 1
        numero_orden = f"{prefijo_orden}{conteo:03d}"

        # 5. Crear la orden en la base de datos vinculada a cliente_id con estado "POR APROBAR"
        nueva_factura = Factura(
            tipo_factura="VENTA",
            numero_factura=numero_orden,
            fecha_factura=date.today(),
            entidad_ruc=ruc_cedula,
            entidad_nombre=razon_social,
            total_factura=total_pedido,
            cliente_id=cliente.id,
            provincia=provincia,
            ciudad=ciudad,
            direccion_entrega=direccion,
            referencia_direccion=referencia,
            estado_despacho="POR APROBAR"
        )
        db.add(nueva_factura)
        db.commit()
        db.refresh(nueva_factura)

        # 5.1 Registrar cada ítem en la tabla movimientos_inventario
        for item in lista_items:
            sku_p = item.get("sku") or item.get("codigo") or item.get("name") or "FAJA-WEB"
            cant_p = int(item.get("cantidad", 1))
            prec_p = float(item.get("precio", 0))
            subtotal_p = cant_p * prec_p
            
            nuevo_mov = MovimientoInventario(
                sku=sku_p,
                tipo_movimiento="VENTA",
                cantidad=-cant_p,
                referencia_factura=numero_orden,
                valor_neto=subtotal_p,
                entidad_asociada=razon_social,
                fecha_hora=datetime.now()
            )
            db.add(nuevo_mov)
        db.commit()

        # 6. Registrar el pago asociado en la tabla Pagos
        nuevo_pago = Pago(
            factura_id=nueva_factura.id,
            metodo_pago="TRANSFERENCIA",
            codigo_transferencia=ruta_comprobante or "Sin comprobante adjunto",
            monto=total_pedido
        )
        db.add(nuevo_pago)
        db.commit()

        # 7. Construir mensaje estructurado para WhatsApp
        mensaje = f"¡Hola! 👋 Acabo de realizar un pedido en Fajas Isabella:\n\n"
        mensaje += f"📦 *Orden N°:* {numero_orden} (Por Aprobar)\n"
        mensaje += f"👤 *Cliente:* {nombre} ({razon_social})\n"
        mensaje += f"🆔 *RUC/Cédula:* {ruc_cedula}\n"
        mensaje += f"📍 *Envío:* {provincia} - {ciudad}\n"
        mensaje += f"🏠 *Dirección:* {direccion} ({referencia})\n\n"
        mensaje += f"🛍️ *Detalle de Productos:*\n"
        for item in lista_items:
            p_nombre = item.get("name") or item.get("nombre") or "Producto"
            mensaje += f"- {p_nombre} (Talla: {item.get('talla')}, Color: {item.get('color')}) x{item.get('cantidad')} - ${item.get('precio')}\n"
        
        mensaje += f"\n💰 *Total Cancelado:* ${total_pedido:.2f}\n"
        if ruta_comprobante:
            mensaje += f"📎 *Comprobante de pago subido al sistema.*"

        encoded_mensaje = urllib.parse.quote(mensaje)
        whatsapp_url = f"https://wa.me/{TELEFONO_WHATSAPP}?text={encoded_mensaje}"

        return {
            "status": "success",
            "mensaje": "Pedido registrado en estado 'Por Aprobar' exitosamente.",
            "whatsapp_url": whatsapp_url
        }
    except Exception as e:
        db.rollback()
        error_det = traceback.format_exc()
        print("ERROR EN CHECKOUT WHATSAPP:", error_det)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")