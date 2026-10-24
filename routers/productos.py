from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import shutil
import re
import unicodedata
import json
import io
import pandas as pd
from database import get_db, Producto, VarianteProducto, Categoria

router = APIRouter()

def generar_sku_compacto(nombre_producto: str, talla: str, color: str) -> str:
    """
    Genera SKU con formato: 4 letras del nombre - Talla - Color (ej: PACA-S-Ne)
    """
    nombre_clean = re.sub(r'[^a-zA-Z]', '', nombre_producto).upper()
    prefix = nombre_clean[:4] if len(nombre_clean) >= 4 else nombre_clean.ljust(4, 'X')
    
    talla_clean = re.sub(r'[^a-zA-Z0-9]', '', talla).upper()
    
    color_norm = unicodedata.normalize('NFD', color)
    color_norm = "".join([c for c in color_norm if unicodedata.category(c) != 'Mn'])
    color_clean = re.sub(r'[^a-zA-Z]', '', color_norm)
    color_code = color_clean[:2].capitalize() if len(color_clean) >= 2 else color_clean.ljust(2, 'x').capitalize()
    
    return f"{prefix}-{talla_clean}-{color_code}"

@router.get("/inventario")
def listar_inventario(db: Session = Depends(get_db)):
    resultados = db.query(VarianteProducto, Producto).outerjoin(Producto, VarianteProducto.producto_id == Producto.id).all()
    
    lista_salida = []
    for variante, producto in resultados:
        p_nombre = str(producto.nombre) if producto and producto.nombre else f"Producto #{variante.producto_id}"
        p_cat = str(producto.categoria) if producto and producto.categoria else "GENERAL"
        p_img = str(producto.imagen_url) if producto and producto.imagen_url else ""
        p_liq = bool(producto.en_liquidacion) if producto else False
        p_nuevo = bool(producto.es_nuevo) if producto else False
        p_oferta = bool(producto.en_oferta) if producto else False
        p_desc_oferta = float(producto.descuento_oferta) if producto and hasattr(producto, 'descuento_oferta') and producto.descuento_oferta else 0.0
        
        lista_salida.append({
            "id": int(variante.id),
            "SKU": str(variante.sku) if variante.sku else "",
            "Talla": str(variante.talla) if variante.talla else "",
            "Color": str(variante.color) if variante.color else "",
            "Precio ($)": float(variante.precio) if variante.precio else 0.0,
            "Stock": int(variante.stock_actual) if variante.stock_actual is not None else 0,
            
            # --- CAMPOS DE INTELIGENCIA DE INVENTARIO ---
            "Stock Mínimo": int(variante.stock_minimo) if variante.stock_minimo is not None else 2,
            "Stock Máximo": int(variante.stock_maximo) if variante.stock_maximo is not None else 20,
            "Fecha Creación": str(variante.fecha_creacion)[:10] if variante.fecha_creacion else "",
            "Última Venta": str(variante.fecha_ultima_venta)[:10] if variante.fecha_ultima_venta else "Sin ventas",
            
            "nombre": p_nombre,
            "categoria": p_cat,
            "imagen_url": p_img,
            "en_liquidacion": p_liq,
            "es_nuevo": p_nuevo,
            "en_oferta": p_oferta,
            "descuento_oferta": p_desc_oferta,
            "producto": {
                "nombre": p_nombre,
                "categoria": p_cat,
                "imagen_url": p_img,
                "en_liquidacion": p_liq,
                "es_nuevo": p_nuevo,
                "en_oferta": p_oferta,
                "descuento_oferta": p_desc_oferta
            }
        })
    return lista_salida

@router.post("/inventario/importar-excel")
async def importar_inventario_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel válido (.xlsx o .xls)")
    
    try:
        contenido = await file.read()
        df = pd.read_excel(io.BytesIO(contenido))
        
        # Normalizar nombres de columnas a minúsculas y limpiar espacios
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Mapear columnas flexibles
        if 'precio ($)' in df.columns and 'precio' not in df.columns:
            df.rename(columns={'precio ($)': 'precio'}, inplace=True)
            
        columnas_requeridas = ['nombre', 'talla', 'color', 'precio', 'stock']
        for col in columnas_requeridas:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Falta la columna obligatoria en el Excel: '{col}'")
        
        procesados = 0
        
        for _, row in df.iterrows():
            nombre = str(row.get('nombre', '')).strip()
            if not nombre or nombre.lower() == 'nan':
                continue
            
            categoria = str(row.get('categoria', 'GENERAL')).strip().upper()
            talla = str(row.get('talla', 'Única')).strip()
            color = str(row.get('color', 'Único')).strip()
            sku_excel = str(row.get('sku', '')).strip()
            
            try:
                precio = float(row.get('precio', 0.0))
            except:
                precio = 0.0
                
            try:
                stock = int(row.get('stock', 0))
            except:
                stock = 0

            # --- CAPTURA OPCIONAL DE STOCK MÍNIMO Y MÁXIMO DESDE EXCEL ---
            try:
                stock_min = int(row.get('stock_minimo', 2))
            except:
                stock_min = 2

            try:
                stock_max = int(row.get('stock_maximo', 20))
            except:
                stock_max = 20

            variante = None
            
            # 1. Buscar por SKU exacto si viene en la plantilla
            if sku_excel and sku_excel.lower() not in ['none', 'nan', '']:
                variante = db.query(VarianteProducto).filter(VarianteProducto.sku == sku_excel).first()

            # 2. Si no hay SKU, buscar o crear producto y variante
            if not variante:
                prod = db.query(Producto).filter(Producto.nombre.ilike(nombre)).first()
                if not prod:
                    prod = Producto(
                        nombre=nombre,
                        modelo=nombre,
                        categoria=categoria or "GENERAL",
                        imagen_url="img/logo.png",
                        en_liquidacion=False,
                        es_nuevo=False,
                        en_oferta=False,
                        descuento_oferta=0.0
                    )
                    db.add(prod)
                    db.commit()
                    db.refresh(prod)
                else:
                    if categoria and categoria != "NAN":
                        prod.categoria = categoria
                        db.commit()

                sku_limpio = generar_sku_compacto(nombre, talla, color)

                variante = db.query(VarianteProducto).filter(
                    VarianteProducto.producto_id == prod.id,
                    VarianteProducto.talla == talla,
                    VarianteProducto.color == color
                ).first()

                if variante:
                    variante.stock_actual = stock
                    variante.precio = precio
                    variante.sku = sku_limpio
                    variante.stock_minimo = stock_min
                    variante.stock_maximo = stock_max
                else:
                    variante = VarianteProducto(
                        sku=sku_limpio,
                        producto_id=prod.id,
                        talla=talla,
                        color=color,
                        stock_actual=stock,
                        precio=precio,
                        stock_minimo=stock_min,
                        stock_maximo=stock_max
                    )
                    db.add(variante)
            else:
                # Actualizar datos directamente de la variante encontrada por SKU
                variante.stock_actual = stock
                variante.precio = precio
                variante.stock_minimo = stock_min
                variante.stock_maximo = stock_max
                if variante.producto:
                    variante.producto.nombre = nombre
                    if categoria and categoria != "NAN":
                        variante.producto.categoria = categoria

            procesados += 1

        db.commit()
        return {
            "status": "success", 
            "message": f"Actualización masiva completada. Se procesaron {procesados} variantes correctamente."
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo Excel: {str(e)}")

@router.put("/variantes/{var_id}")
def actualizar_variante(
    var_id: int,
    categoria: str = Form(...),
    talla: str = Form(...),
    color: str = Form(...),
    precio: float = Form(...),
    stock_minimo: int = Form(2),
    stock_maximo: int = Form(20),
    en_liquidacion: bool = Form(False),
    es_nuevo: bool = Form(False),
    en_oferta: bool = Form(False),
    descuento_oferta: float = Form(0.0),
    imagen: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    variante = db.query(VarianteProducto).filter(VarianteProducto.id == var_id).first()
    if not variante:
        raise HTTPException(status_code=404, detail="Variante no encontrada")
    
    variante.talla = talla.strip()
    variante.color = color.strip()
    variante.precio = float(precio)
    variante.stock_minimo = stock_minimo
    variante.stock_maximo = stock_maximo
    
    if variante.producto:
        variante.sku = generar_sku_compacto(variante.producto.nombre, variante.talla, variante.color)
        variante.producto.categoria = categoria.strip()
        variante.producto.en_liquidacion = en_liquidacion
        variante.producto.es_nuevo = es_nuevo
        variante.producto.en_oferta = en_oferta
        variante.producto.descuento_oferta = descuento_oferta
        
        if imagen and imagen.filename:
            dir_destino = os.path.join("web", "img")
            os.makedirs(dir_destino, exist_ok=True)
            
            ruta_fisica = os.path.join(dir_destino, imagen.filename)
            with open(ruta_fisica, "wb") as buffer:
                shutil.copyfileobj(imagen.file, buffer)
            
            variante.producto.imagen_url = f"img/{imagen.filename}"
        
    db.commit()
    return {"status": "success", "message": f"Variante ID {var_id} y sus estados actualizados correctamente."}

@router.post("/productos")
def crear_o_actualizar_producto(
    nombre: str = Form(...),
    modelo: Optional[str] = Form(None),
    categoria: str = Form("GENERAL"),
    en_liquidacion: bool = Form(False),
    es_nuevo: bool = Form(False),
    en_oferta: bool = Form(False),
    descuento_oferta: float = Form(0.0),
    variantes: str = Form(...),
    imagen: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        modelo_nombre = modelo or nombre
        prod = db.query(Producto).filter(Producto.nombre == nombre).first()
        
        imagen_url_relativa = prod.imagen_url if prod and prod.imagen_url else "img/logo.png"
        if imagen and imagen.filename:
            dir_destino = os.path.join("web", "img")
            os.makedirs(dir_destino, exist_ok=True)
            
            ruta_fisica = os.path.join(dir_destino, imagen.filename)
            with open(ruta_fisica, "wb") as buffer:
                shutil.copyfileobj(imagen.file, buffer)
                
            imagen_url_relativa = f"img/{imagen.filename}"

        lista_variantes = json.loads(variantes)
        
        if prod:
            prod.modelo = modelo_nombre
            prod.categoria = categoria or prod.categoria
            prod.imagen_url = imagen_url_relativa
            prod.en_liquidacion = en_liquidacion
            prod.es_nuevo = es_nuevo
            prod.en_oferta = en_oferta
            prod.descuento_oferta = descuento_oferta
            db.commit()
            db.refresh(prod)
        else:
            prod = Producto(
                nombre=nombre, 
                modelo=modelo_nombre, 
                categoria=categoria or "GENERAL",
                imagen_url=imagen_url_relativa,
                en_liquidacion=en_liquidacion,
                es_nuevo=es_nuevo,
                en_oferta=en_oferta,
                descuento_oferta=descuento_oferta
            )
            db.add(prod)
            db.commit()
            db.refresh(prod)

        skus_procesados_lote = set()

        for v in lista_variantes:
            talla_val = str(v.get("talla", "")).strip()
            color_val = str(v.get("color", "")).strip()
            stock_val = int(v.get("stock_actual", 0))
            precio_val = float(v.get("precio", 0.0))
            
            # --- CAPTURAR STOCK MÍNIMO Y MÁXIMO DESDE EL FORMULARIO ---
            stock_min = int(v.get("stock_minimo", 2))
            stock_max = int(v.get("stock_maximo", 20))
            
            sku_limpio = generar_sku_compacto(nombre, talla_val, color_val)

            sku_candidate = sku_limpio
            contador = 1
            while sku_candidate in skus_procesados_lote:
                sku_candidate = f"{sku_limpio}-{contador}"
                contador += 1
            
            sku_limpio = sku_candidate
            skus_procesados_lote.add(sku_limpio)

            existe_sku = db.query(VarianteProducto).filter(VarianteProducto.sku == sku_limpio).first()
            if existe_sku:
                existe_sku.stock_actual = stock_val
                existe_sku.precio = precio_val
                existe_sku.talla = talla_val
                existe_sku.color = color_val
                existe_sku.stock_minimo = stock_min
                existe_sku.stock_maximo = stock_max
            else:
                variante = VarianteProducto(
                    sku=sku_limpio, 
                    producto_id=prod.id, 
                    talla=talla_val,
                    color=color_val, 
                    stock_actual=stock_val, 
                    precio=precio_val,
                    stock_minimo=stock_min,
                    stock_maximo=stock_max
                )
                db.add(variante)
                
        db.commit()
        return {"status": "success", "message": f"Producto '{nombre}' y sus variantes guardados exitosamente.", "imagen_url": imagen_url_relativa}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno al guardar producto: {str(e)}")

@router.delete("/variantes/{variante_id}")
def eliminar_variante(variante_id: int, db: Session = Depends(get_db)):
    variante = db.query(VarianteProducto).filter(VarianteProducto.id == variante_id).first()
    if not variante:
        raise HTTPException(status_code=404, detail="Variante no encontrada.")
    db.delete(variante)
    db.commit()
    return {"status": "success", "message": "Variante eliminada."}

@router.get("/categorias")
def listar_categorias(db: Session = Depends(get_db)):
    categorias = db.query(Categoria).all()
    return [{"id": c.id, "nombre": c.nombre, "imagen_url": c.imagen_url} for c in categorias]

@router.post("/categorias")
def crear_o_actualizar_categoria(
    nombre: str = Form(...),
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        cat_nombre = nombre.strip().upper()
        nombre_archivo = imagen.filename
        
        dir_destino = os.path.join("web", "img")
        os.makedirs(dir_destino, exist_ok=True)
        
        ruta_fisica = os.path.join(dir_destino, nombre_archivo)
        with open(ruta_fisica, "wb") as buffer:
            shutil.copyfileobj(imagen.file, buffer)
            
        imagen_relativa = f"img/{nombre_archivo}"
        
        cat_db = db.query(Categoria).filter(Categoria.nombre == cat_nombre).first()
        if cat_db:
            cat_db.imagen_url = imagen_relativa
        else:
            cat_db = Categoria(nombre=cat_nombre, imagen_url=imagen_relativa)
            db.add(cat_db)
            
        db.commit()
        return {"status": "success", "message": f"Categoría '{cat_nombre}' guardada exitosamente."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/categorias/{categoria_id}")
def eliminar_categoria(categoria_id: int, db: Session = Depends(get_db)):
    cat_db = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not cat_db:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    db.delete(cat_db)
    db.commit()
    return {"status": "success", "message": "Categoría eliminada."}