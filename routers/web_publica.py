import hashlib
import urllib.parse
import base64
import requests
from datetime import datetime, date
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, Producto, Categoria, Cliente, Factura, Pago, VarianteProducto, MovimientoInventario, AbonoPlanAcumulativo
from typing import Optional
from pydantic import BaseModel
import json
import os
import secrets
import string
import cloudinary.uploader
from config import (
    NOMBRE_EMPRESA, TELEFONO_WHATSAPP, CORREO_EMPRESA, DIRECCION_EMPRESA,
    INSTAGRAM_URL, FACEBOOK_URL, TIKTOK_URL, WHATSAPP_LINK,
    EMAIL_EMISOR
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
# GESTIÓN DE CAMPAÑA FESTIVA WEB (ZONA HORARIA ECUADOR)
# ==============================================================================

def obtener_campana_festiva_activa(db: Session) -> Optional[dict]:
    """Verifica si existe una campaña festiva web activa y dentro del rango de fecha/hora actual."""
    try:
        row = db.execute(text("SELECT contenido FROM configuracion_web WHERE seccion = 'campana_festiva';")).fetchone()
        if not row:
            return None
        contenido = row[0]
        if isinstance(contenido, str):
            contenido = json.loads(contenido)
        
        if not contenido.get("activo", False):
            return None
            
        now_ec = datetime.now(ZoneInfo("America/Guayaquil"))
        inicio_str = contenido.get("fecha_inicio")
        fin_str = contenido.get("fecha_fin")
        
        if inicio_str and fin_str:
            inicio = datetime.fromisoformat(inicio_str).replace(tzinfo=ZoneInfo("America/Guayaquil"))
            fin = datetime.fromisoformat(fin_str).replace(tzinfo=ZoneInfo("America/Guayaquil"))
            
            if inicio <= now_ec <= fin:
                return contenido
    except Exception as e:
        print(f"Error al verificar campaña festiva web: {e}")
    return None


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
                VALUES (:seccion, CAST(:contenido AS jsonb))
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
            VALUES (:seccion, CAST(:contenido AS jsonb), NOW()) 
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
    
    campana_festiva = obtener_campana_festiva_activa(db)
    porcentaje_festivo = float(campana_festiva.get("porcentaje", 0.0)) if campana_festiva else 0.0
    
    resultado = []
    for prod in productos_db:
        variantes = [v for v in prod.variantes if (getattr(v, 'stock_actual', 0) or getattr(v, 'stock', 0)) > 0]
        
        if variantes:
            variantes_data = []
            for v in variantes:
                stock_val = getattr(v, 'stock_actual', 0) or getattr(v, 'stock', 0)
                
                precio_original = float(v.precio)
                desc_var = float(getattr(v, 'descuento_porcentaje', 0.0) or 0.0)
                en_oferta_prod = bool(getattr(prod, 'en_oferta', False))
                desc_oferta_prod = float(getattr(prod, 'descuento_oferta', 0.0) or 0.0)
                
                if porcentaje_festivo > 0:
                    porcentaje_aplicado = porcentaje_festivo
                else:
                    porcentaje_aplicado = desc_var if desc_var > 0 else (desc_oferta_prod if en_oferta_prod else 0.0)
                    
                precio_final = precio_original * (1 - (porcentaje_aplicado / 100.0)) if porcentaje_aplicado > 0 else precio_original

                variantes_data.append({
                    "id": v.id,
                    "sku": v.sku,
                    "talla": v.talla,
                    "color": v.color,
                    "precio": precio_original,
                    "descuento_porcentaje": porcentaje_aplicado,
                    "precio_final": round(precio_final, 2),
                    "stock": stock_val,
                    "imagen_url": getattr(v, 'imagen_url', '') or ''
                })
            
            resultado.append({
                "id": prod.id,
                "nombre": prod.nombre,
                "modelo": getattr(prod, 'modelo', prod.nombre),
                "categoria": prod.categoria,
                "imagen_url": getattr(prod, 'imagen_url', '') or '',
                "imagen_1": getattr(prod, 'imagen_1', '') or '',
                "imagen_2": getattr(prod, 'imagen_2', '') or '',
                "imagen_3": getattr(prod, 'imagen_3', '') or '',
                "imagen_4": getattr(prod, 'imagen_4', '') or '',
                "video_url": getattr(prod, 'video_url', '') or '',
                "cartilla_url": getattr(prod, 'cartilla_url', '') or '',
                "en_liquidacion": bool(getattr(prod, 'en_liquidacion', False)),
                "es_nuevo": bool(getattr(prod, 'es_nuevo', False)),
                "en_oferta": bool(getattr(prod, 'en_oferta', False)) or (porcentaje_festivo > 0),
                "descuento_oferta": porcentaje_festivo if porcentaje_festivo > 0 else float(getattr(prod, 'descuento_oferta', 0.0) or 0.0),
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
    
    campana_festiva = obtener_campana_festiva_activa(db)
    porcentaje_festivo = float(campana_festiva.get("porcentaje", 0.0)) if campana_festiva else 0.0

    variantes_data = []
    for v in variantes_activas:
        precio_original = float(v.precio)
        desc_var = float(getattr(v, 'descuento_porcentaje', 0.0) or 0.0)
        en_oferta_prod = bool(getattr(prod, 'en_oferta', False))
        desc_oferta_prod = float(getattr(prod, 'descuento_oferta', 0.0) or 0.0)
        
        if porcentaje_festivo > 0:
            porcentaje_aplicado = porcentaje_festivo
        else:
            porcentaje_aplicado = desc_var if desc_var > 0 else (desc_oferta_prod if en_oferta_prod else 0.0)
            
        precio_final = precio_original * (1 - (porcentaje_aplicado / 100.0)) if porcentaje_aplicado > 0 else precio_original

        variantes_data.append({
            "id": v.id,
            "sku": v.sku,
            "talla": v.talla,
            "color": v.color,
            "precio": precio_original,
            "descuento_porcentaje": porcentaje_aplicado,
            "precio_final": round(precio_final, 2),
            "stock": v.stock_actual,
            "imagen_url": getattr(v, 'imagen_url', '') or ''
        })

    return {
        "status": "success",
        "id": prod.id,
        "nombre": prod.nombre,
        "categoria": prod.categoria,
        "imagen_url": getattr(prod, 'imagen_url', '') or '',
        "imagen_1": getattr(prod, 'imagen_1', '') or '',
        "imagen_2": getattr(prod, 'imagen_2', '') or '',
        "imagen_3": getattr(prod, 'imagen_3', '') or '',
        "imagen_4": getattr(prod, 'imagen_4', '') or '',
        "video_url": getattr(prod, 'video_url', '') or '',
        "cartilla_url": getattr(prod, 'cartilla_url', '') or '',
        "en_liquidacion": bool(getattr(prod, 'en_liquidacion', False)),
        "es_nuevo": bool(getattr(prod, 'es_nuevo', False)),
        "en_oferta": bool(getattr(prod, 'en_oferta', False)) or (porcentaje_festivo > 0),
        "descuento_oferta": porcentaje_festivo if porcentaje_festivo > 0 else float(getattr(prod, 'descuento_oferta', 0.0) or 0.0),
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

# --- AUTENTICACIÓN Y GESTIÓN DE CLIENTES UNIFICADA ---

@router.post("/api/web/auth/login")
def login_cliente(datos: LoginSchema, db: Session = Depends(get_db)):
    correo = datos.correo.lower().strip()
    cliente = db.query(Cliente).filter(Cliente.correo == correo).first()

    if not cliente:
        raise HTTPException(status_code=400, detail="Correo no registrado en el sistema.")

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


# ==============================================================================
# FUNCIÓN AUXILIAR COMÚN PARA PROCESAR PEDIDOS (CON APLICACIÓN FESTIVA WEB)
# ==============================================================================

async def _procesar_checkout_comun(
    nombre: str,
    telefono: str,
    correo: Optional[str],
    ruc_cedula: str,
    razon_social: str,
    provincia: str,
    ciudad: str,
    direccion: str,
    referencia: Optional[str],
    items: str,
    comprobante: Optional[UploadFile],
    tipo_venta: str,
    metodo_pago: str,
    abono_inicial: float,
    db: Session
):
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
        cliente_db.cliente_web = True
        if correo_limpio and not cliente_db.correo:
            cliente_db.correo = correo_limpio
            
        if not cliente_db.password:
            password_temporal = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            cliente_db.password = generar_hash_sha256(password_temporal)
        db.commit()
    else:
        password_temporal = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        password_hash_temp = generar_hash_sha256(password_temporal)
        reg_correo = correo_limpio if correo_limpio else f"{ruc_cedula.strip()}@fajasisabella.com"
        
        cliente_db = Cliente(
            ruc_cedula=ruc_cedula,
            nombre=razon_social,
            correo=reg_correo,
            password=password_hash_temp,
            telefono=telefono,
            direccion=direccion,
            ciudad=ciudad,
            cliente_web=True
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

    campana_festiva = obtener_campana_festiva_activa(db)
    porcentaje_festivo = float(campana_festiva.get("porcentaje", 0.0)) if campana_festiva else 0.0

    total_pedido = 0.0
    items_validados = []
    for item in lista_items:
        sku_p = item.get("sku") or item.get("codigo") or item.get("name") or "FAJA-WEB"
        cant_p = int(item.get("cantidad", 1))
        
        variante_db = db.query(VarianteProducto).filter(VarianteProducto.sku == sku_p).first()
        if variante_db:
            precio_base = float(variante_db.precio)
            desc_var = float(getattr(variante_db, 'descuento_porcentaje', 0.0) or 0.0)
            prod_db = variante_db.producto
            en_oferta_prod = bool(getattr(prod_db, 'en_oferta', False))
            desc_oferta_prod = float(getattr(prod_db, 'descuento_oferta', 0.0) or 0.0)
            
            if porcentaje_festivo > 0:
                p_aplicado = porcentaje_festivo
            else:
                p_aplicado = desc_var if desc_var > 0 else (desc_oferta_prod if en_oferta_prod else 0.0)
                
            prec_p = precio_base * (1 - (p_aplicado / 100.0)) if p_aplicado > 0 else precio_base
        else:
            prec_p = float(item.get('precio', 0))

        subtotal_item = cant_p * prec_p
        total_pedido += subtotal_item
        
        item_copia = dict(item)
        item_copia['precio'] = round(prec_p, 2)
        item_copia['sku'] = sku_p
        items_validados.append(item_copia)
    
    file_url = ""
    comprobante_bytes = None
    comprobante_nombre = None

    if comprobante:
        try:
            comprobante_bytes = await comprobante.read()
            comprobante_nombre = comprobante.filename or "comprobante_pago.jpg"
            
            upload_result = cloudinary.uploader.upload(comprobante_bytes)
            file_url = upload_result.get("secure_url", comprobante_nombre)
        except Exception as e:
            print(f"⚠️ Advertencia al procesar comprobante: {e}")
            file_url = comprobante_nombre if comprobante_nombre else "comprobante_adjunto"

    es_acumulativo = (metodo_pago == "Plan Acumulativo")
    saldo_pendiente = 0.0
    estado_acumulativo = "COMPLETADO"

    if es_acumulativo:
        saldo_pendiente = total_pedido - abono_inicial
        if saldo_pendiente < 0:
            raise HTTPException(status_code=400, detail="El abono inicial no puede superar el total de la orden.")
        estado_acumulativo = "EN_PROCESO" if saldo_pendiente > 0 else "COMPLETADO"

    fecha_ecuador = datetime.now(ZoneInfo("America/Guayaquil")).date()
    prefijo_ym = fecha_ecuador.strftime('%y%m')
    
    facturas_mes_count = db.query(Factura).filter(Factura.numero_factura.like(f"{prefijo_ym}%")).count()
    siguiente_consecutivo = facturas_mes_count + 1
    num_factura_str = f"{prefijo_ym}{siguiente_consecutivo:03d}"
    
    tipo_factura_str = f"VENTA WEB {tipo_venta.upper()}"
    
    nueva_factura = Factura(
        tipo_factura=tipo_factura_str,
        numero_factura=num_factura_str,
        fecha_factura=fecha_ecuador,
        entidad_ruc=ruc_cedula,
        entidad_nombre=razon_social,
        total_factura=total_pedido,
        cliente_id=cliente_db.id,
        provincia=provincia,
        ciudad=ciudad,
        direccion_entrega=direccion,
        referencia_direccion=referencia,
        estado_despacho="POR APROBAR",
        url_pagofactura=file_url,
        es_plan_acumulativo=es_acumulativo,
        saldo_pendiente=saldo_pendiente,
        estado_acumulativo=estado_acumulativo
    )
    db.add(nueva_factura)
    db.commit()
    db.refresh(nueva_factura)

    monto_pago = abono_inicial if es_acumulativo else total_pedido
    if monto_pago > 0:
        pago = Pago(
            factura_id=nueva_factura.id,
            metodo_pago=metodo_pago,
            codigo_transferencia=file_url if metodo_pago == "Transferencia" else None,
            monto=monto_pago
        )
        db.add(pago)

    if es_acumulativo and abono_inicial > 0:
        nuevo_abono = AbonoPlanAcumulativo(
            factura_id=nueva_factura.id,
            monto=abono_inicial,
            comprobante_url=file_url,
            referencia_bancaria="",
            observacion="Abono inicial registrado desde la Tienda Web"
        )
        db.add(nuevo_abono)

    for item in items_validados:
        sku_p = item.get("sku")
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
            fecha_hora=fecha_ecuador
        )
        db.add(nuevo_mov)
        
    db.commit()

    return {
        "cliente_db": cliente_db,
        "lista_items": items_validados,
        "total_pedido": total_pedido,
        "num_factura_str": num_factura_str,
        "password_temporal": password_temporal,
        "comprobante_bytes": comprobante_bytes,
        "comprobante_nombre": comprobante_nombre
    }


# ==============================================================================
# FUNCIÓN DE ENVÍO DE CORREO EN SEGUNDO PLANO (BREVO API HTTP - PUERTO 443)
# ==============================================================================

def enviar_correo_background(
    emisor, destinatarios, empresa, num_factura, cuerpo_html, comprobante_bytes, comprobante_nombre
):
    try:
        print("==================================================")
        print("🔍 [CHIVATO BREVO API HTTP] Iniciando envío por HTTPS (Puerto 443)...")
        
        api_key = os.getenv("MAIL_API_KEY", "")
        if not api_key:
            print("❌ [BREVO ERROR]: La variable de entorno MAIL_API_KEY no está configurada en Railway.")
            return

        url = "https://api.brevo.com/v3/smtp/email"
        
        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }

        to_list = [{"email": dest} for dest in destinatarios]

        payload = {
            "sender": {"name": empresa, "email": emisor or "ventas@fajasisabella.com"},
            "to": to_list,
            "subject": f"🛍️ Confirmación de Pedido #{num_factura} - {empresa}",
            "htmlContent": cuerpo_html
        }

        if comprobante_bytes and comprobante_nombre:
            encoded_file = base64.b64encode(comprobante_bytes).decode('utf-8')
            payload["attachment"] = [{
                "content": encoded_file,
                "name": comprobante_nombre
            }]

        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code in [200, 201]:
            print("✅ [CHIVATO BREVO API HTTP]: ¡Correo enviado exitosamente a través de la API de Brevo!")
        else:
            print(f"❌ [CHIVATO BREVO API ERROR]: Código {response.status_code} - {response.text}")
            
    except Exception as api_err:
        print(f"❌ [CHIVATO BREVO EXCEPTION]: {type(api_err).__name__}: {str(api_err)}")


# ==============================================================================
# ENDPOINTS DE CHECKOUT (WHATSAPP Y CORREO)
# ==============================================================================

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
    metodo_pago: Optional[str] = Form("Transferencia"),
    abono_inicial: Optional[float] = Form(0.0),
    comprobante: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        res = await _procesar_checkout_comun(
            nombre, telefono, correo, ruc_cedula, razon_social,
            provincia, ciudad, direccion, referencia, items, comprobante, "WHATSAPP",
            metodo_pago, abono_inicial, db
        )
        
        detalle_texto = ""
        for idx, item in enumerate(res["lista_items"], 1):
            p_precio = float(item.get('precio', 0))
            p_cant = int(item.get('cantidad', 1))
            subtotal = p_precio * p_cant
            detalle_texto += f"{idx}. *{item.get('nombre', 'Prenda')}*\n   - Talla: {item.get('talla', 'N/D')} | Color: {item.get('color', 'N/D')}\n   - SKU: {item.get('sku', 'N/D')}\n   - Cantidad: {p_cant} x ${p_precio:.2f} = ${subtotal:.2f}\n\n"

        mensaje_plano = f"¡Hola Fajas Isabella! 👋 Acabo de realizar un pedido y transferencia:\n\n*Factura:* #{res['num_factura_str']}\n*Cliente:* {nombre}\n*RUC/Cédula:* {ruc_cedula}\n*Destino:* {provincia}, {ciudad} - {direccion}\n\n{detalle_texto}💰 *Total Pagado:* ${res['total_pedido']:.2f}\n\n"
        
        if res["password_temporal"]:
            mensaje_plano += f"🔐 *Acceso Web Temporal:*\n- Usuario: {res['cliente_db'].correo}\n- Clave Temporal: *{res['password_temporal']}*\n*(Por seguridad se te pedirá cambiarla al iniciar sesión)*\n\n"
        
        mensaje_plano += "Adjunto mi comprobante para la verificación."

        phone_clean = str(TELEFONO_WHATSAPP).replace("+", "").replace(" ", "").strip()
        mensaje_encoded = urllib.parse.quote(mensaje_plano)
        whatsapp_url = f"https://wa.me/{phone_clean}?text={mensaje_encoded}"

        return {
            "status": "success",
            "whatsapp_url": whatsapp_url,
            "mensaje": "Pedido registrado correctamente."
        }

    except Exception as db_err:
        db.rollback()
        print(f"❌ [CHIVATO CHECKOUT WHATSAPP ERROR]: {str(db_err)}")
        raise HTTPException(status_code=500, detail=f"Error en servidor/BD: {str(db_err)}")


@router.post("/api/web/auth/checkout-correo")
async def checkout_correo(
    background_tasks: BackgroundTasks,
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
    metodo_pago: Optional[str] = Form("Transferencia"),
    abono_inicial: Optional[float] = Form(0.0),
    comprobante: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        res = await _procesar_checkout_comun(
            nombre, telefono, correo, ruc_cedula, razon_social,
            provincia, ciudad, direccion, referencia, items, comprobante, "CORREO",
            metodo_pago, abono_inicial, db
        )
        
        correo_limpio = correo.lower().strip() if (correo and correo.strip() != "") else None

        if os.getenv("MAIL_API_KEY"):
            destinatarios = [CORREO_EMPRESA]
            if correo_limpio and correo_limpio not in destinatarios:
                destinatarios.append(correo_limpio)

            filas_items = ""
            for item in res["lista_items"]:
                cant = int(item.get('cantidad', 1))
                prec = float(item.get('precio', 0))
                filas_items += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{item.get('nombre')} ({item.get('talla', 'N/D')} / {item.get('color', 'N/D')})</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{cant}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${prec:.2f}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${(cant * prec):.2f}</td>
                </tr>
                """

            cuerpo_html = f"""
            <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 10px; padding: 20px;">
                <h2 style="color: #e11d48; text-align: center;">¡Nuevo Pedido Generado en {NOMBRE_EMPRESA}!</h2>
                <p>Se ha registrado el pedido <strong>#{res['num_factura_str']}</strong> exitosamente.</p>
                
                <hr style="border: 0; border-top: 1px solid #eee;">
                
                <h3>📋 Datos del Cliente y Envío</h3>
                <p>
                    <strong>Cliente / Razón Social:</strong> {razon_social}<br>
                    <strong>RUC / Cédula:</strong> {ruc_cedula}<br>
                    <strong>Teléfono:</strong> {telefono}<br>
                    <strong>Correo:</strong> {correo_limpio or 'No registrado'}<br>
                    <strong>Dirección de Entrega:</strong> {direccion}, {ciudad}, {provincia}<br>
                    <strong>Referencia:</strong> {referencia or 'N/A'}
                </p>

                <h3>🛍️ Detalle del Pedido</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <thead>
                        <tr style="background-color: #f8fafc;">
                            <th style="padding: 8px; text-align: left;">Producto</th>
                            <th style="padding: 8px; text-align: center;">Cant.</th>
                            <th style="padding: 8px; text-align: right;">Precio</th>
                            <th style="padding: 8px; text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_items}
                    </tbody>
                </table>

                <h3 style="text-align: right; color: #e11d48; margin-top: 15px;">Total Pedido: ${res['total_pedido']:.2f}</h3>
            """

            if res["password_temporal"]:
                cuerpo_html += f"""
                <div style="background-color: #fff1f2; padding: 12px; border-radius: 8px; margin-top: 15px;">
                    <p style="margin: 0; font-size: 13px; color: #9f1239;">
                        🔑 <strong>Acceso a Cuenta Cliente:</strong><br>
                        <strong>Usuario:</strong> {res['cliente_db'].correo}<br>
                        <strong>Clave Temporal:</strong> {res['password_temporal']}
                    </p>
                </div>
                """

            cuerpo_html += f"""
                <hr style="border: 0; border-top: 1px solid #eee; margin-top: 20px;">
                <p style="font-size: 11px; color: #888; text-align: center;">Mensaje automático enviado desde la plataforma de {NOMBRE_EMPRESA}.</p>
            </div>
            """

            background_tasks.add_task(
                enviar_correo_background,
                EMAIL_EMISOR or CORREO_EMPRESA,
                destinatarios,
                NOMBRE_EMPRESA,
                res['num_factura_str'],
                cuerpo_html,
                res["comprobante_bytes"],
                res["comprobante_nombre"]
            )
        else:
            print("⚠️ [CHIVATO BREVO WARNING]: No se intentó el envío porque la variable MAIL_API_KEY no está configurada en Railway.")

        return {
            "status": "success",
            "mensaje": "Pedido registrado y en proceso de notificación por correo."
        }

    except Exception as db_err:
        db.rollback()
        print(f"❌ [CHIVATO CHECKOUT CORREO ERROR]: {str(db_err)}")
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