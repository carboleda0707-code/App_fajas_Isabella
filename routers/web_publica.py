import hashlib
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, Producto, Categoria, Cliente, Factura, Pago, MovimientoInventario
from typing import Optional
from pydantic import BaseModel
import json
import os
import shutil
from datetime import date
import secrets
import string
import cloudinary.uploader
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

class WebConfigModel(BaseModel):
    seccion: str
    contenido: dict


# ==============================================================================
# GESTIÓN DINÁMICA DEL HOME (POSTGRESQL + JSONB)
# ==============================================================================

def init_web_db_table(db: Session):
    """Crea la tabla configuracion_web e inserta valores por defecto si no existen."""
    try:
        db.execute(text("""
        CREATE TABLE IF NOT EXISTS configuracion_web (
            id SERIAL PRIMARY KEY,
            seccion VARCHAR(50) UNIQUE NOT NULL,
            contenido JSONB NOT NULL,
            actualizado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))
        db.commit()

        default_data = [
            (
                'sec05',
                json.dumps({
                    "slide1": {
                        "tag": "Alta Compresión",
                        "titulo": "Moldea tu Figura al Instante",
                        "descripcion": "Descubre la nueva línea de fajas reductoras y postoperatorias de máxima comodidad.",
                        "btn_texto": "Ver Colección →",
                        "imagen": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=1200&q=80"
                    },
                    "slide2": {
                        "tag": "Calidad Colombiana",
                        "titulo": "Recuperación y Cuidado Seguro",
                        "descripcion": "Diseños especializados con microcápsulas y costuras invisibles para tu diario vivir.",
                        "btn_texto": "Explorar Modelos →",
                        "imagen": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=1200&q=80"
                    },
                    "slide3": {
                        "tag": "Efecto Cintura",
                        "titulo": "Definición Reloj de Arena",
                        "descripcion": "Cinturillas de látex térmico ideales para moldear postura y reducir medidas.",
                        "btn_texto": "Ver Cinturillas →",
                        "imagen": "https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=1200&q=80"
                    },
                    "slide4": {
                        "tag": "Envíos Seguros",
                        "titulo": "Envíos Directos a Todo Ecuador",
                        "descripcion": "Garantía de fábrica directa hasta la puerta de tu hogar.",
                        "btn_texto": "Comprar Ahora →",
                        "imagen": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=1200&q=80"
                    }
                })
            ),
            (
                'sec1',
                json.dumps({
                    "titulo": "HISTORIA",
                    "subtitulo": "12 AÑOS RESALTANDO TU BELLEZA",
                    "parrafo1": "Fajas Isabella empezó vendiendo desde la sala de su casa, con la convicción de que toda mujer merece sentirse segura y hermosa en su cuerpo.",
                    "parrafo2": "Hoy somos un equipo que fabrica directamente fajas colombianas, con ventas al por mayor y al por menor, y más de 80 modelos entre fajas látex reductoras, fajas postoperatorias, cinturillas y accesorios.",
                    "parrafo3": "Nuestra marca está registrada ante el SENADI como \"FAJAS Isabella RESALTA TU BELLEZA\", un respaldo de la calidad y la confianza que nos han dado nuestras clientas.",
                    "multimedia": "banner_historia.jpg"
                })
            ),
            (
                'sec2',
                json.dumps({
                    "tiktok_url": "https://tiktok.com"
                })
            ),
            (
                'sec3',
                json.dumps({
                    "card1": {
                        "tag": "PUBLICIDAD 1",
                        "titulo": "Moldeadoras de Alta Compresión",
                        "descripcion": "Control total y definición perfecta para uso diario.",
                        "link_texto": "Ver Colección →",
                        "multimedia": "publi_1.jpg"
                    },
                    "card2": {
                        "tag": "PUBLICIDAD 2",
                        "titulo": "Confort y Recuperación Segura",
                        "descripcion": "Diseñadas por expertos para garantizar tu bienestar.",
                        "link_texto": "Ver Modelos →",
                        "multimedia": "publi_2.jpg"
                    },
                    "card3": {
                        "tag": "PUBLICIDAD 3",
                        "titulo": "Reduce Medidas al Instante",
                        "descripcion": "Moldea tu cintura con máxima comodidad.",
                        "link_texto": "Descubrir →",
                        "multimedia": "publi_3.jpg"
                    }
                })
            )
        ]

        for seccion, contenido in default_data:
            db.execute(text("""
                INSERT INTO configuracion_web (seccion, contenido)
                VALUES (:seccion, :contenido::jsonb)
                ON CONFLICT (seccion) DO NOTHING;
            """), {"seccion": seccion, "contenido": contenido})
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error al inicializar tabla web: {e}")


@router.get("/api/web/home-config")
@router.get("/web/home-config")
@router.get("/web/home")
def get_web_home(db: Session = Depends(get_db)):
    """Obtiene la configuración completa del Home almacenada en PostgreSQL."""
    init_web_db_table(db)
    try:
        result = db.execute(text("SELECT seccion, contenido FROM configuracion_web;")).fetchall()
        resultado = {}
        for row in result:
            seccion_name = row[0]
            seccion_content = row[1]
            if isinstance(seccion_content, str):
                seccion_content = json.loads(seccion_content)
            resultado[seccion_name] = seccion_content
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener configuración web: {str(e)}")


@router.post("/api/web/home-config")
@router.post("/web/home-config")
@router.post("/web/home")
def update_web_home(config: WebConfigModel, db: Session = Depends(get_db)):
    """Actualiza o guarda una sección de la web en PostgreSQL (UPSERT)."""
    init_web_db_table(db)
    try:
        db.execute(text("""
            INSERT INTO configuracion_web (seccion, contenido, actualizado_at) 
            VALUES (:seccion, :contenido::jsonb, NOW()) 
            ON CONFLICT (seccion) 
            DO UPDATE SET 
                contenido = EXCLUDED.contenido, 
                actualizado_at = NOW();
        """), {"seccion": config.seccion, "contenido": json.dumps(config.contenido)})
        db.commit()
        return {
            "status": "success",
            "message": f"Sección '{config.seccion}' actualizada exitosamente en PostgreSQL."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar la sección: {str(e)}")


# ==============================================================================
# ENDPOINTS PÚBLICOS DE CONFIG, INVENTARIO Y AUTENTICACIÓN
# ==============================================================================

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

@router.get("/api/web/inventario")
@router.get("/web/inventario")
def listar_inventario_publico(categoria: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Producto)
    
    if categoria and categoria.upper() != "TODAS":
        query = query.filter(Producto.categoria.ilike(f"%{categoria}%"))
        
    productos_db = query.all()
    
    resultado = []
    for prod in productos_db:
        variantes = [v for v in prod.variantes if (getattr(v, 'stock_actual', 0) or getattr(v, 'stock', 0)) > 0]
        
        if variantes:
            variantes_data = []
            for v in variantes:
                stock_val = getattr(v, 'stock_actual', 0) or getattr(v, 'stock', 0)
                variantes_data.append({
                    "id": v.id,
                    "sku": v.sku,
                    "talla": v.talla,
                    "color": v.color,
                    "precio": float(v.precio),
                    "stock": stock_val,
                    "imagen_url": getattr(v, 'imagen_url', '') or ''
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

@router.get("/api/web/producto/{producto_id}")
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
            "stock": v.stock_actual,
            "imagen_url": getattr(v, 'imagen_url', '') or ''
        })

    img_clean = getattr(prod, 'imagen_url', '') or ''

    return {
        "status": "success",
        "id": prod.id,
        "nombre": prod.nombre,
        "categoria": prod.categoria,
        "imagen_url": img_clean,
        "variantes": variantes_data
    }

@router.get("/api/web/categorias")
@router.get("/web/categorias")
def listar_categorias_publicas(db: Session = Depends(get_db)):
    try:
        categorias_db = db.query(Categoria).all()
        resultado = []
        for cat in categorias_db:
            img_clean = getattr(cat, 'imagen_url', '') or ''
            resultado.append({
                "nombre": getattr(cat, 'nombre', getattr(cat, 'categoria', '')),
                "imagen_url": img_clean
            })
        return resultado
    except Exception:
        return []

# --- AUTENTICACIÓN Y GESTIÓN DE CLIENTES UNIFICADA (CON VALIDACIÓN DE UNICIDAD) ---

@router.post("/api/web/auth/login")
def login_cliente(datos: LoginSchema, db: Session = Depends(get_db)):
    correo = datos.correo.lower().strip()
    cliente = db.query(Cliente).filter(Cliente.correo == correo).first()

    if not cliente:
        raise HTTPException(status_code=400, detail="Correo no registrado en el sistema.")

    if not cliente.password or str(cliente.cliente_web).upper() == "POR_ACTUALIZAR":
        return {
            "status": "requiere_password",
            "mensaje": "Detectamos una cuenta provisional. Por favor configure su contraseña.",
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
    ruc_cedula: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    correo_limpio = correo.lower().strip()
    
    query_filtro = (Cliente.correo == correo_limpio)
    if ruc_cedula:
        query_filtro = (query_filtro) | (Cliente.ruc_cedula == ruc_cedula)
        
    existente = db.query(Cliente).filter(query_filtro).first()
    
    if existente:
        if existente.password and str(existente.cliente_web).upper() != "POR_ACTUALIZAR":
            raise HTTPException(status_code=400, detail="Ya existe una cuenta registrada con este correo o RUC/Cédula.")
        else:
            existente.nombre = nombre
            existente.correo = correo_limpio
            existente.password = generar_hash_sha256(password)
            existente.telefono = telefono or existente.telefono
            existente.direccion = direccion or existente.direccion
            if ruc_cedula:
                existente.ruc_cedula = ruc_cedula
            existente.cliente_web = True
            db.commit()
            db.refresh(existente)
            return {
                "status": "success",
                "mensaje": "¡Cuenta activada y registrada exitosamente!",
                "cliente": {"id": existente.id, "nombre": existente.nombre, "correo": existente.correo}
            }

    nuevo_cliente = Cliente(
        ruc_cedula=ruc_cedula or correo_limpio[:20],
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
    try:
        correo_limpio = correo.lower().strip() if (correo and correo.strip() != "") else None
        
        cliente_db = None
        if correo_limpio:
            cliente_db = db.query(Cliente).filter(Cliente.correo == correo_limpio).first()
        if not cliente_db and ruc_cedula:
            cliente_db = db.query(Cliente).filter(Cliente.ruc_cedula == ruc_cedula).first()

        password_temporal = None
        if cliente_db:
            cliente_db.nombre = razon_social
            cliente_db.telefono = telefono
            cliente_db.direccion = direccion
            cliente_db.ciudad = ciudad
            if correo_limpio and not cliente_db.correo:
                cliente_db.correo = correo_limpio
                
            if not cliente_db.password or str(cliente_db.cliente_web).upper() == "POR_ACTUALIZAR":
                password_temporal = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
                cliente_db.password = generar_hash_sha256(password_temporal)
                cliente_db.cliente_web = "POR_ACTUALIZAR"
            db.commit()
        else:
            password_temporal = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            password_hash_temp = generar_hash_sha256(password_temporal)
            reg_correo = correo_limpio if correo_limpio else f"{ruc_cedula.strip()}@fajasisabella.com"
            
            cliente_db = Cliente(
                ruc_cedula=ruc_cedula,
                nombre=razon_social,
                correo=reg_correo,
                telefono=telefono,
                direccion=direccion,
                ciudad=ciudad,
                cliente_web="POR_ACTUALIZAR",
                password=password_hash_temp
            )
            db.add(cliente_db)
            db.commit()
            db.refresh(cliente_db)

        try:
            lista_items = json.loads(items) if items else []
        except Exception:
            raise HTTPException(status_code=400, detail="El formato de los ítems del carrito es inválido.")

        if not lista_items:
            raise HTTPException(status_code=400, detail="El carrito está vacío.")

        total_pedido = sum(float(item.get('precio', 0)) * int(item.get('cantidad', 1)) for item in lista_items)
        
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

        for item in lista_items:
            sku_p = item.get("sku") or item.get("codigo") or item.get("name") or "FAJA-WEB"
            cant_p = int(item.get("cantidad", 1))
            prec_p = float(item.get("precio", 0))
            subtotal_p = cant_p * prec_p
            
            nuevo_mov = MovimientoInventario(
                sku=sku_p,
                tipo_movimiento="VENTA",
                cantidad=-cant_p,
                referencia_factura=num_factura_str,
                valor_neto=subtotal_p,
                entidad_asociada=razon_social,
                fecha_hora=date.today()
            )
            db.add(nuevo_mov)
        db.commit()

        if comprobante:
            try:
                # Lectura segura de bytes para Cloudinary
                file_bytes = await comprobante.read()
                upload_result = cloudinary.uploader.upload(file_bytes)
                file_url = upload_result.get("secure_url", comprobante.filename)
            except Exception as e:
                file_url = comprobante.filename

            pago = Pago(
                factura_id=nueva_factura.id,
                metodo_pago="TRANSFERENCIA",
                codigo_transferencia=file_url,
                monto=total_pedido
            )
            db.add(pago)
            db.commit()

        detalle_texto = ""
        for idx, item in enumerate(lista_items, 1):
            p_precio = float(item.get('precio', 0))
            p_cant = int(item.get('cantidad', 1))
            subtotal = p_precio * p_cant
            detalle_texto += f"{idx}. *{item.get('nombre', 'Prenda')}*%0A   - Talla: {item.get('talla', 'N/D')} | Color: {item.get('color', 'N/D')}%0A   - SKU: {item.get('sku', 'N/D')}%0A   - Cantidad: {p_cant} x ${p_precio:.2f} = ${subtotal:.2f}%0A%0A"

        mensaje_wapp = f"¡Hola Fajas Isabella! 👋 Acabo de realizar un pedido y transferencia:%0A%0A*Factura:* #{num_factura_str}%0A*Cliente:* {nombre}%0A*RUC/Cédula:* {ruc_cedula}%0A*Destino:* {provincia}, {ciudad} - {direccion}%0A%0A{detalle_texto}💰 *Total Pagado:* ${total_pedido:.2f}%0A%0A"
        
        if password_temporal:
            mensaje_wapp += f"🔐 *Acceso Web Temporal:*%0A- Usuario: {cliente_db.correo}%0A- Clave Temporal: *{password_temporal}*%0A*(Por seguridad se te pedirá cambiarla al iniciar sesión)*%0A%0A"
        
        mensaje_wapp += "Adjunto mi comprobante para la verificación."
        
        whatsapp_url = f"https://wa.me/{TELEFONO_WHATSAPP}?text={mensaje_wapp}"

        return {
            "status": "success",
            "whatsapp_url": whatsapp_url,
            "mensaje": "Pedido registrado correctamente."
        }

    except Exception as db_err:
        db.rollback()
        # Esto te mostrará el error exacto en la alerta en caso de que falle la BD
        raise HTTPException(status_code=500, detail=f"Error en servidor/BD: {str(db_err)}")


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