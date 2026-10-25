import hashlib
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db, Producto, Categoria, Cliente, Factura, Pago, MovimientoInventario
from typing import Optional
from pydantic import BaseModel
import json
import os
import shutil
from datetime import date
from config import (
    NOMBRE_EMPRESA, TELEFONO_WHATSAPP, CORREO_EMPRESA, DIRECCION_EMPRESA,
    INSTAGRAM_URL, FACEBOOK_URL, TIKTOK_URL, WHATSAPP_LINK
)

router = APIRouter()

def generar_hash_sha256(password: str) -> str:
    """Genera el hash SHA-256 estricto para las contraseñas."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class LoginSchema(BaseModel):
    correo: str
    password: str

class SetPasswordSchema(BaseModel):
    correo: str
    password: str
    password_confirm: str

@router.get("/config/empresa")
def obtener_info_empresa():
    return {
        "nombre": NOMBRE_EMPRESA,
        "telefono_whatsapp": TELEFONO_WHATSAPP,
        "correo": CORREO_EMPRESA,
        "direccion": DIRECCION_EMPRESA,
        "redes": {
            "instagram": INSTAGRAM_URL,
            "facebook": FACEBOOK_URL,
            "tiktok": TIKTOK_URL,
            "whatsapp": WHATSAPP_LINK
        }
    }

@router.get("/web/inventario")
def listar_inventario_publico(categoria: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Producto)
    
    if categoria and categoria.upper() != "TODAS":
        query = query.filter(Producto.categoria.ilike(f"%{categoria}%"))
        
    productos_db = query.all()
    
    resultado = []
    for prod in productos_db:
        variantes = [v for v in prod.variantes if v.stock_actual > 0]
        
        if variantes:
            variantes_data = []
            for v in variantes:
                variantes_data.append({
                    "id": v.id,
                    "sku": v.sku,
                    "talla": v.talla,
                    "color": v.color,
                    "precio": float(v.precio),
                    "stock": v.stock_actual
                })
            
            img_clean = getattr(prod, 'imagen_url', '') or ''
            
            resultado.append({
                "id": prod.id,
                "nombre": prod.nombre,
                "modelo": getattr(prod, 'modelo', prod.nombre),
                "categoria": prod.categoria,
                "imagen_url": img_clean,
                "en_liquidacion": bool(getattr(prod, 'en_liquidacion', False)),
                "es_nuevo": bool(getattr(prod, 'es_nuevo', False)),
                "en_oferta": bool(getattr(prod, 'en_oferta', False)),
                "descuento_oferta": float(getattr(prod, 'descuento_oferta', 0.0) or 0.0),
                "variantes": variantes_data
            })
            
    return resultado

@router.get("/web/producto/{producto_id}")
def obtener_producto_dinamico(producto_id: int, db: Session = Depends(get_db)):
    prod = db.query(Producto).filter(Producto.id == producto_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    variantes_activas = [v for v in prod.variantes if v.stock_actual > 0]
    
    variantes_data = []
    for v in variantes_activas:
        variantes_data.append({
            "id": v.id,
            "sku": v.sku,
            "talla": v.talla,
            "color": v.color,
            "precio": float(v.precio),
            "stock": v.stock_actual
        })

    img_clean = getattr(prod, 'imagen_url', '') or ''
    if img_clean:
        img_clean = img_clean.split('/')[-1]

    return {
        "status": "success",
        "id": prod.id,
        "nombre": prod.nombre,
        "categoria": prod.categoria,
        "imagen_url": img_clean,
        "variantes": variantes_data
    }

@router.get("/web/categorias")
def listar_categorias_publicas(db: Session = Depends(get_db)):
    try:
        categorias_db = db.query(Categoria).all()
        resultado = []
        for cat in categorias_db:
            img_clean = getattr(cat, 'imagen_url', '') or ''
            if img_clean:
                img_clean = img_clean.split('/')[-1]

            resultado.append({
                "nombre": getattr(cat, 'nombre', getattr(cat, 'categoria', '')),
                "imagen_url": img_clean
            })
        return resultado
    except Exception:
        return []

# --- AUTENTICACIÓN Y GESTIÓN DE CLIENTES UNIFICADA ---

@router.post("/api/web/auth/login")
def login_cliente(datos: LoginSchema, db: Session = Depends(get_db)):
    correo = datos.correo.lower().strip()
    cliente = db.query(Cliente).filter(Cliente.correo == correo).first()

    if not cliente:
        raise HTTPException(status_code=400, detail="Correo no registrado en el sistema.")

    if not cliente.password:
        return {
            "status": "requiere_password",
            "mensaje": "Detectamos una compra previa por transferencia. Por favor configure su contraseña.",
            "correo": cliente.correo
        }

    password_hash = generar_hash_sha256(datos.password)
    if cliente.password != password_hash:
        raise HTTPException(status_code=400, detail="Contraseña incorrecta.")

    return {
        "status": "success",
        "mensaje": "Inicio de sesión exitoso",
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "correo": cliente.correo
        }
    }

@router.post("/api/web/auth/configurar-password")
def configurar_password_inicial(datos: SetPasswordSchema, db: Session = Depends(get_db)):
    if datos.password != datos.password_confirm:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden.")

    correo = datos.correo.lower().strip()
    cliente = db.query(Cliente).filter(Cliente.correo == correo).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    cliente.password = generar_hash_sha256(datos.password)
    cliente.cliente_web = True
    db.commit()

    return {
        "status": "success",
        "mensaje": "Contraseña configurada exitosamente. Ya puede iniciar sesión."
    }

@router.post("/api/web/auth/registro")
def registrar_cliente_web(
    nombre: str = Form(...),
    correo: str = Form(...),
    password: str = Form(...),
    telefono: Optional[str] = Form(None),
    direccion: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    correo_limpio = correo.lower().strip()
    existente = db.query(Cliente).filter(Cliente.correo == correo_limpio).first()
    
    if existente:
        if existente.password:
            raise HTTPException(status_code=400, detail="El correo ya está registrado en el sistema.")
        else:
            existente.nombre = nombre
            existente.password = generar_hash_sha256(password)
            existente.telefono = telefono or existente.telefono
            existente.direccion = direccion or existente.direccion
            existente.cliente_web = True
            db.commit()
            db.refresh(existente)
            return {
                "status": "success",
                "mensaje": "Cuenta activada y registrada exitosamente.",
                "cliente": {"id": existente.id, "nombre": existente.nombre, "correo": existente.correo}
            }

    nuevo_cliente = Cliente(
        ruc_cedula=correo_limpio[:20],
        nombre=nombre,
        correo=correo_limpio,
        password=generar_hash_sha256(password),
        telefono=telefono,
        direccion=direccion,
        cliente_web=True
    )
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)

    return {
        "status": "success",
        "mensaje": "¡Registro exitoso!",
        "cliente": {"id": nuevo_cliente.id, "nombre": nuevo_cliente.nombre, "correo": nuevo_cliente.correo}
    }

@router.post("/api/web/auth/checkout-whatsapp")
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
    cliente_db = None
    if correo:
        correo_limpio = correo.lower().strip()
        cliente_db = db.query(Cliente).filter(Cliente.correo == correo_limpio).first()
    
    if not cliente_db:
        cliente_db = db.query(Cliente).filter(Cliente.ruc_cedula == ruc_cedula).first()

    if cliente_db:
        cliente_db.nombre = nombre
        cliente_db.telefono = telefono
        cliente_db.direccion = direccion
        cliente_db.ciudad = ciudad
        cliente_db.cliente_web = True
        if correo and not cliente_db.correo:
            cliente_db.correo = correo.lower().strip()
        db.commit()
    else:
        cliente_db = Cliente(
            ruc_cedula=ruc_cedula,
            nombre=nombre,
            correo=correo.lower().strip() if correo else None,
            telefono=telefono,
            direccion=direccion,
            ciudad=ciudad,
            cliente_web=True,
            password=None
        )
        db.add(cliente_db)
        db.commit()
        db.refresh(cliente_db)

    lista_items = json.loads(items)
    total_pedido = sum(item['precio'] * item['cantidad'] for item in lista_items)
    
    num_factura_str = f"FAC-WAPP-{int(date.today().strftime('%Y%m%d'))}-{cliente_db.id}"
    
    nueva_factura = Factura(
        tipo_factura="VENTA WEB WHATSAPP",
        numero_factura=num_factura_str,
        entidad_ruc=ruc_cedula,
        entidad_nombre=razon_social,
        total_factura=total_pedido,
        cliente_id=cliente_db.id,
        provincia=provincia,
        ciudad=ciudad,
        direccion_entrega=direccion,
        referencia_direccion=referencia,
        courier_nombre="Por Definir",
        estado_despacho="PENDIENTE"
    )
    db.add(nueva_factura)
    db.commit()
    db.refresh(nueva_factura)

    if comprobante:
        os.makedirs("static/comprobantes", exist_ok=True)
        file_path = f"static/comprobantes/{nueva_factura.id}_{comprobante.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(comprobante.file, buffer)
        
        pago = Pago(
            factura_id=nueva_factura.id,
            metodo_pago="TRANSFERENCIA",
            codigo_transferencia=file_path,
            monto=total_pedido
        )
        db.add(pago)
        db.commit()

    detalle_texto = ""
    for idx, item in enumerate(lista_items, 1):
        subtotal = item['precio'] * item['cantidad']
        detalle_texto += f"{idx}. *{item['nombre']}*%0A   - Talla: {item['talla']} | Color: {item['color']}%0A   - SKU: {item['sku']}%0A   - Cantidad: {item['cantidad']} x ${item['precio']:.2f} = ${subtotal:.2f}%0A%0A"

    mensaje_wapp = f"¡Hola Fajas Isabella! 👋 Acabo de realizar un pedido y transferencia:%0A%0A*Factura:* #{num_factura_str}%0A*Cliente:* {nombre}%0A*RUC/Cédula:* {ruc_cedula}%0A*Destino:* {provincia}, {ciudad} - {direccion}%0A%0A{detalle_texto}💰 *Total Pagado:* ${total_pedido:.2f}%0A%0AAdjunto mi comprobante para la verificación."
    
    # Uso dinámico del teléfono importado desde config.ini
    whatsapp_url = f"https://wa.me/{TELEFONO_WHATSAPP}?text={mensaje_wapp}"

    return {
        "status": "success",
        "whatsapp_url": whatsapp_url,
        "mensaje": "Pedido registrado correctamente."
    }

@router.get("/api/web/auth/pedidos/{cliente_id}")
def obtener_pedidos_cliente(cliente_id: int, db: Session = Depends(get_db)):
    facturas = db.query(Factura).filter(Factura.cliente_id == cliente_id).all()
    resultado = []
    for f in facturas:
        resultado.append({
            "id": f.id,
            "numero_factura": f.numero_factura,
            "fecha": str(f.fecha_factura),
            "total": f.total_factura,
            "estado_despacho": f.estado_despacho,
            "courier": f.courier_nombre or "Pendiente",
            "numero_guia": f.numero_guia or "Por emitir"
        })
    return resultado