from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional
import re, unicodedata, json, io
import pandas as pd
from database import get_db, Producto, VarianteProducto, Categoria
from utils.cloudinary_uploader import subir_archivo_a_nube

router = APIRouter()

def generar_sku_compacto(nombre: str, talla: str, color: str) -> str:
    nombre_clean = re.sub(r'[^a-zA-Z]', '', nombre).upper()[:4].ljust(4, 'X')
    talla_clean = re.sub(r'[^a-zA-Z0-9]', '', talla).upper()
    color_norm = unicodedata.normalize('NFD', color)
    color_clean = re.sub(r'[^a-zA-Z]', '', "".join([c for c in color_norm if unicodedata.category(c) != 'Mn']))
    color_code = color_clean[:2].capitalize() if len(color_clean) >= 2 else color_clean.ljust(2, 'x').capitalize()
    return f"{nombre_clean}-{talla_clean}-{color_code}"

@router.get("/inventario")
def listar_inventario(db: Session = Depends(get_db)):
    resultados = db.query(VarianteProducto, Producto).outerjoin(Producto, VarianteProducto.producto_id == Producto.id).all()
    lista = []
    for v, p in resultados:
        p_nom = p.nombre if p else f"Producto #{v.producto_id}"
        p_cat = p.categoria if p else "GENERAL"
        p_img = p.imagen_url if p else ""
        v_img = v.imagen_url or p_img
        
        prod_dict = {
            "nombre": p_nom, 
            "categoria": p_cat, 
            "imagen_url": p_img,
            "imagen_1": p.imagen_1 if p else "",
            "imagen_2": p.imagen_2 if p else "",
            "imagen_3": p.imagen_3 if p else "",
            "imagen_4": p.imagen_4 if p else "",
            "video_url": p.video_url if p else "",
            "cartilla_url": p.cartilla_url if p else "",
            "en_liquidacion": bool(p.en_liquidacion) if p else False,
            "es_nuevo": bool(p.es_nuevo) if p else False,
            "en_oferta": bool(p.en_oferta) if p else False,
            "descuento_oferta": float(p.descuento_oferta or 0.0) if p else 0.0,
            "tipo_descuento": p.tipo_descuento if p and p.tipo_descuento else "GENERAL"
        }
        lista.append({
            "id": v.id, 
            "SKU": v.sku or "", 
            "Talla": v.talla or "", 
            "Color": v.color or "",
            "Precio ($)": float(v.precio or 0.0), 
            "descuento_porcentaje": float(v.descuento_porcentaje or 0.0),
            "Stock": v.stock_actual or 0,
            "Stock Mínimo": v.stock_minimo or 2, 
            "Stock Máximo": v.stock_maximo or 20,
            "Fecha Creación": str(v.fecha_creacion)[:10] if v.fecha_creacion else "",
            "Última Venta": str(v.fecha_ultima_venta)[:10] if v.fecha_ultima_venta else "Sin ventas",
            "imagen_url": v_img, 
            **prod_dict, 
            "producto": prod_dict
        })
    return lista

@router.post("/inventario/importar-excel")
async def importar_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Formato de archivo inválido")
    try:
        df = pd.read_excel(io.BytesIO(await file.read()))
        df.columns = [str(c).strip().lower() for c in df.columns]
        if 'precio ($)' in df.columns: 
            df.rename(columns={'precio ($)': 'precio'}, inplace=True)
        
        for col in ['nombre', 'talla', 'color', 'precio', 'stock']:
            if col not in df.columns: 
                raise HTTPException(status_code=400, detail=f"Falta columna: {col}")
        
        procesados = 0
        for _, r in df.iterrows():
            nombre = str(r.get('nombre', '')).strip()
            if not nombre or nombre.lower() == 'nan': 
                continue
            
            cat = str(r.get('categoria', 'GENERAL')).strip().upper()
            talla = str(r.get('talla', 'Única')).strip()
            color = str(r.get('color', 'Único')).strip()
            sku_ex = str(r.get('sku', '')).strip()
            
            precio = float(r.get('precio', 0.0) or 0.0)
            stock = int(r.get('stock', 0) or 0)
            s_min = int(r.get('stock_minimo', 2) or 2)
            s_max = int(r.get('stock_maximo', 20) or 20)
            desc_var = float(r.get('descuento_porcentaje', 0.0) or 0.0)
            
            variante = db.query(VarianteProducto).filter(VarianteProducto.sku == sku_ex).first() if sku_ex and sku_ex.lower() not in ['none', 'nan', ''] else None
            
            if not variante:
                prod = db.query(Producto).filter(Producto.nombre.ilike(nombre)).first()
                if not prod:
                    prod = Producto(nombre=nombre, modelo=nombre, categoria=cat or "GENERAL", imagen_url="")
                    db.add(prod)
                    db.commit()
                    db.refresh(prod)
                elif cat and cat != "NAN":
                    prod.categoria = cat
                    db.commit()
                    
                sku_limpio = generar_sku_compacto(nombre, talla, color)
                variante = db.query(VarianteProducto).filter_by(producto_id=prod.id, talla=talla, color=color).first()
                
                if variante:
                    variante.stock_actual = stock
                    variante.precio = precio
                    variante.sku = sku_limpio
                    variante.stock_minimo = s_min
                    variante.stock_maximo = s_max
                    variante.descuento_porcentaje = desc_var
                else:
                    variante = VarianteProducto(sku=sku_limpio, producto_id=prod.id, talla=talla, color=color, stock_actual=stock, precio=precio, stock_minimo=s_min, stock_maximo=s_max, descuento_porcentaje=desc_var)
                    db.add(variante)
            else:
                variante.stock_actual = stock
                variante.precio = precio
                variante.stock_minimo = s_min
                variante.stock_maximo = s_max
                variante.descuento_porcentaje = desc_var
                if variante.producto and cat and cat != "NAN": 
                    variante.producto.categoria = cat
            procesados += 1
        db.commit()
        return {"status": "success", "message": f"Se procesaron {procesados} variantes correctamente."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/variantes/{var_id}")
async def actualizar_variante(
    var_id: int, 
    categoria: str = Form(...), 
    talla: str = Form(...), 
    color: str = Form(...),
    precio: float = Form(...), 
    descuento_porcentaje: float = Form(0.0),
    stock_minimo: int = Form(2), 
    stock_maximo: int = Form(20),
    en_liquidacion: bool = Form(False), 
    es_nuevo: bool = Form(False), 
    en_oferta: bool = Form(False),
    descuento_oferta: float = Form(0.0),
    tipo_descuento: str = Form("GENERAL"),
    imagen: Optional[UploadFile] = File(None),
    imagen_variante: Optional[UploadFile] = File(None), 
    db: Session = Depends(get_db)
):
    v = db.query(VarianteProducto).filter(VarianteProducto.id == var_id).first()
    if not v: 
        raise HTTPException(status_code=404, detail="Variante no encontrada")
    
    v.talla = talla.strip()
    v.color = color.strip()
    v.precio = float(precio)
    v.stock_minimo = stock_minimo
    v.stock_maximo = stock_maximo
    
    # Si el producto está en modo general o sin oferta, se limpia el descuento individual de esta variante
    if tipo_descuento == "GENERAL" or (not en_oferta and not en_liquidacion):
        v.descuento_porcentaje = 0.0
    else:
        v.descuento_porcentaje = float(descuento_porcentaje)
    
    archivo_imagen = imagen if (imagen and imagen.filename) else imagen_variante
    if archivo_imagen and archivo_imagen.filename:
        img_url = await subir_archivo_a_nube(archivo_imagen, folder="fajas_isabella/variantes")
        if img_url: 
            v.imagen_url = img_url
    
    if v.producto:
        v.sku = generar_sku_compacto(v.producto.nombre, v.talla, v.color)
        v.producto.categoria = categoria.strip()
        v.producto.en_liquidacion = en_liquidacion
        v.producto.es_nuevo = es_nuevo
        v.producto.en_oferta = en_oferta
        v.producto.descuento_oferta = float(descuento_oferta) if (en_oferta or en_liquidacion) else 0.0
        v.producto.tipo_descuento = tipo_descuento
        
    db.commit()
    return {"status": "success", "message": f"Variante ID {var_id} actualizada correctamente."}

@router.post("/productos")
async def crear_o_actualizar_producto(
    nombre: str = Form(...), 
    modelo: Optional[str] = Form(None), 
    categoria: str = Form("GENERAL"),
    en_liquidacion: bool = Form(False), 
    es_nuevo: bool = Form(False), 
    en_oferta: bool = Form(False),
    descuento_oferta: float = Form(0.0), 
    tipo_descuento: str = Form("GENERAL"),
    variantes: str = Form(...), 
    imagen: Optional[UploadFile] = File(None),
    imagen_1: Optional[UploadFile] = File(None),
    imagen_2: Optional[UploadFile] = File(None),
    imagen_3: Optional[UploadFile] = File(None),
    imagen_4: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    cartilla: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        prod = db.query(Producto).filter(Producto.nombre == nombre).first()
        
        img_rel = prod.imagen_url if prod else ""
        i1_url = prod.imagen_1 if prod and prod.imagen_1 else ""
        i2_url = prod.imagen_2 if prod and prod.imagen_2 else ""
        i3_url = prod.imagen_3 if prod and prod.imagen_3 else ""
        i4_url = prod.imagen_4 if prod and prod.imagen_4 else ""
        vid_url = prod.video_url if prod and prod.video_url else ""
        cart_url = prod.cartilla_url if prod and prod.cartilla_url else ""

        if imagen and imagen.filename:
            img_rel = await subir_archivo_a_nube(imagen, folder="fajas_isabella/productos")
        if imagen_1 and imagen_1.filename:
            i1_url = await subir_archivo_a_nube(imagen_1, folder="fajas_isabella/productos/galeria")
        if imagen_2 and imagen_2.filename:
            i2_url = await subir_archivo_a_nube(imagen_2, folder="fajas_isabella/productos/galeria")
        if imagen_3 and imagen_3.filename:
            i3_url = await subir_archivo_a_nube(imagen_3, folder="fajas_isabella/productos/galeria")
        if imagen_4 and imagen_4.filename:
            i4_url = await subir_archivo_a_nube(imagen_4, folder="fajas_isabella/productos/galeria")
        if video and video.filename:
            vid_url = await subir_archivo_a_nube(video, folder="fajas_isabella/productos/videos")
        if cartilla and cartilla.filename:
            cart_url = await subir_archivo_a_nube(cartilla, folder="fajas_isabella/productos/cartillas")

        val_desc_oferta = float(descuento_oferta) if (en_oferta or en_liquidacion) else 0.0

        if prod:
            prod.modelo = modelo or nombre
            prod.categoria = categoria or prod.categoria
            if img_rel: prod.imagen_url = img_rel
            if i1_url: prod.imagen_1 = i1_url
            if i2_url: prod.imagen_2 = i2_url
            if i3_url: prod.imagen_3 = i3_url
            if i4_url: prod.imagen_4 = i4_url
            if vid_url: prod.video_url = vid_url
            if cart_url: prod.cartilla_url = cart_url
            prod.en_liquidacion = en_liquidacion
            prod.es_nuevo = es_nuevo
            prod.en_oferta = en_oferta
            prod.descuento_oferta = val_desc_oferta
            prod.tipo_descuento = tipo_descuento
        else:
            prod = Producto(
                nombre=nombre, 
                modelo=modelo or nombre, 
                categoria=categoria or "GENERAL",
                imagen_url=img_rel,
                imagen_1=i1_url,
                imagen_2=i2_url,
                imagen_3=i3_url,
                imagen_4=i4_url,
                video_url=vid_url,
                cartilla_url=cart_url,
                en_liquidacion=en_liquidacion, 
                es_nuevo=es_nuevo,
                en_oferta=en_oferta, 
                descuento_oferta=val_desc_oferta,
                tipo_descuento=tipo_descuento
            )
            db.add(prod)
            db.commit()
            db.refresh(prod)
            
        skus_lote = set()
        lista_variantes = json.loads(variantes)
        
        for v_data in lista_variantes:
            t_val = str(v_data.get("talla", "")).strip()
            c_val = str(v_data.get("color", "")).strip()
            s_val = int(v_data.get("stock_actual", 0))
            p_val = float(v_data.get("precio", 0.0))
            s_min = int(v_data.get("stock_minimo", 2))
            s_max = int(v_data.get("stock_maximo", 20))
            v_img = str(v_data.get("imagen_url", "")).strip()

            # --- SANEAMIENTO Y REGLA DE ORO AUTOMÁTICA AL GUARDAR ---
            if tipo_descuento == "GENERAL" or (not en_oferta and not en_liquidacion):
                desc_var = 0.0  # Si es general o no hay oferta, limpiamos el individual a 0 en todas las variantes
            elif tipo_descuento == "INDIVIDUAL":
                desc_var = float(v_data.get("descuento_porcentaje", 0.0))
                if desc_var == 0 and val_desc_oferta > 0:
                    desc_var = val_desc_oferta  # Hereda la base si está en 0
            else:
                desc_var = 0.0
            
            sku = generar_sku_compacto(nombre, t_val, c_val)
            cnt = 1
            while sku in skus_lote:
                sku = f"{sku}-{cnt}"
                cnt += 1
            skus_lote.add(sku)
            
            existe = db.query(VarianteProducto).filter(VarianteProducto.sku == sku).first()
            if existe:
                existe.stock_actual = s_val
                existe.precio = p_val
                existe.talla = t_val
                existe.color = c_val
                existe.stock_minimo = s_min
                existe.stock_maximo = s_max
                existe.descuento_porcentaje = desc_var
                if v_img: 
                    existe.imagen_url = v_img
            else:
                db.add(VarianteProducto(
                    sku=sku, 
                    producto_id=prod.id, 
                    talla=t_val, 
                    color=c_val,
                    stock_actual=s_val, 
                    precio=p_val, 
                    descuento_porcentaje=desc_var,
                    stock_minimo=s_min,
                    stock_maximo=s_max, 
                    imagen_url=v_img or None
                ))
        db.commit()
        return {"status": "success", "message": f"Producto '{nombre}' y sus variantes guardados exitosamente."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/variantes/{var_id}")
def eliminar_variante(var_id: int, db: Session = Depends(get_db)):
    v = db.query(VarianteProducto).filter(VarianteProducto.id == var_id).first()
    if not v: 
        raise HTTPException(status_code=404, detail="Variante no encontrada.")
    db.delete(v)
    db.commit()
    return {"status": "success", "message": "Variante eliminada."}

@router.get("/categorias")
def listar_categorias(db: Session = Depends(get_db)):
    return [{"id": c.id, "nombre": c.nombre, "imagen_url": c.imagen_url} for c in db.query(Categoria).all()]

@router.post("/categorias")
async def crear_categoria(nombre: str = Form(...), imagen: Optional[UploadFile] = File(None), db: Session = Depends(get_db)):
    try:
        cat_nom = nombre.strip().upper()
        img_rel = ""
        if imagen and imagen.filename:
            img_rel = await subir_archivo_a_nube(imagen, folder="fajas_isabella/categorias")
            
        cat_db = db.query(Categoria).filter(Categoria.nombre == cat_nom).first()
        if cat_db: 
            if img_rel:
                cat_db.imagen_url = img_rel
        else: 
            db.add(Categoria(nombre=cat_nom, imagen_url=img_rel))
        db.commit()
        return {"status": "success", "message": f"Categoría '{cat_nom}' guardada."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/categorias/{cat_id}")
def eliminar_categoria(cat_id: int, db: Session = Depends(get_db)):
    c = db.query(Categoria).filter(Categoria.id == cat_id).first()
    if not c: 
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")
    db.delete(c)
    db.commit()
    return {"status": "success", "message": "Categoría eliminada."}