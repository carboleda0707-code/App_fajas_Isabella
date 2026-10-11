from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
from database import get_db, Producto, VarianteProducto, Categoria

router = APIRouter()

class VarianteSchema(BaseModel):
    sku: str
    talla: str
    color: str
    stock_actual: int
    precio: float

class ProductoNuevoSchema(BaseModel):
    nombre: str
    modelo: Optional[str] = None
    categoria: Optional[str] = "GENERAL"
    imagen_url: Optional[str] = ""
    en_liquidacion: Optional[bool] = False
    variantes: List[VarianteSchema]

@router.get("/inventario")
def listar_inventario(db: Session = Depends(get_db)):
    resultados = db.query(VarianteProducto, Producto).outerjoin(Producto, VarianteProducto.producto_id == Producto.id).all()
    
    lista_salida = []
    for variante, producto in resultados:
        p_nombre = str(producto.nombre) if producto and producto.nombre else f"Producto #{variante.producto_id}"
        p_cat = str(producto.categoria) if producto and producto.categoria else "GENERAL"
        
        lista_salida.append({
            "id": int(variante.id),
            "SKU": str(variante.sku) if variante.sku else "",
            "Talla": str(variante.talla) if variante.talla else "",
            "Color": str(variante.color) if variante.color else "",
            "Precio ($)": float(variante.precio) if variante.precio else 0.0,
            "Stock": int(variante.stock_actual) if variante.stock_actual is not None else 0,
            "producto": {
                "nombre": p_nombre,
                "categoria": p_cat
            }
        })
    return lista_salida

@router.put("/variantes/{var_id}")
def actualizar_variante(
    var_id: int,
    categoria: str = Form(...),
    talla: str = Form(...),
    color: str = Form(...),
    precio: float = Form(...),
    imagen: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    variante = db.query(VarianteProducto).filter(VarianteProducto.id == var_id).first()
    if not variante:
        raise HTTPException(status_code=404, detail="Variante no encontrada")
    
    variante.talla = talla.strip()
    variante.color = color.strip()
    variante.precio = float(precio)
        
    if variante.producto:
        variante.producto.categoria = categoria.strip()
        
        if imagen and imagen.filename:
            cat_folder_name = categoria.lower().replace(" ", "_")
            dir_destino = os.path.join("web", "img", "productos", cat_folder_name)
            os.makedirs(dir_destino, exist_ok=True)
            
            ruta_fisica = os.path.join(dir_destino, imagen.filename)
            with open(ruta_fisica, "wb") as buffer:
                shutil.copyfileobj(imagen.file, buffer)
            
            variante.producto.imagen_url = f"img/productos/{cat_folder_name}/{imagen.filename}"
        
    db.commit()
    return {"status": "success", "message": f"Variante ID {var_id} actualizada correctamente."}

@router.post("/productos")
def crear_o_actualizar_producto(data: ProductoNuevoSchema, db: Session = Depends(get_db)):
    try:
        modelo_nombre = data.modelo or data.nombre
        prod = db.query(Producto).filter(Producto.nombre == data.nombre).first()
        
        if prod:
            prod.modelo = modelo_nombre
            prod.categoria = data.categoria or prod.categoria
            prod.imagen_url = data.imagen_url or prod.imagen_url
            if data.en_liquidacion is not None:
                prod.en_liquidacion = data.en_liquidacion
        else:
            prod = Producto(
                nombre=data.nombre, 
                modelo=modelo_nombre, 
                categoria=data.categoria or "GENERAL",
                imagen_url=data.imagen_url or "",
                en_liquidacion=data.en_liquidacion if data.en_liquidacion is not None else False
            )
            db.add(prod)
            db.commit()
            db.refresh(prod)

        cat_prefix = (data.categoria or "GEN")[:3].upper()
        skus_procesados_lote = set()

        for idx, v in enumerate(data.variantes):
            sku_limpio = str(v.sku).strip() if v.sku else ""
            
            if not sku_limpio or sku_limpio.lower() in ["none", "nan", ""]:
                talla_code = str(v.talla).upper().strip()
                color_code = str(v.color).upper().strip()[:3]
                prod_clean = data.nombre.upper().replace(' ', '-')
                sku_limpio = f"{cat_prefix}-{prod_clean}-{talla_code}-{color_code}"

            sku_candidate = sku_limpio
            contador = 1
            while sku_candidate in skus_procesados_lote:
                sku_candidate = f"{sku_limpio}-{contador}"
                contador += 1
            
            sku_limpio = sku_candidate
            skus_procesados_lote.add(sku_limpio)

            existe_sku = db.query(VarianteProducto).filter(VarianteProducto.sku == sku_limpio).first()
            if existe_sku:
                existe_sku.stock_actual = v.stock_actual
                existe_sku.precio = v.precio
                existe_sku.talla = v.talla
                existe_sku.color = v.color
            else:
                variante = VarianteProducto(
                    sku=sku_limpio, 
                    producto_id=prod.id, 
                    talla=v.talla,
                    color=v.color, 
                    stock_actual=v.stock_actual, 
                    precio=v.precio
                )
                db.add(variante)
                
        db.commit()
        return {"status": "success", "message": f"Producto '{data.nombre}' y sus variantes guardados exitosamente."}

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

# --- ENDPOINTS DE CATEGORÍAS ---
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
        cat_slug = cat_nombre.lower().replace(" ", "_")
        
        _, ext = os.path.splitext(imagen.filename)
        if not ext:
            ext = ".jpg"
            
        nombre_archivo_web = f"cat-{cat_slug}{ext}"
        
        dir_destino = os.path.join("web", "img", "categorias")
        os.makedirs(dir_destino, exist_ok=True)
        
        ruta_fisica = os.path.join(dir_destino, nombre_archivo_web)
        with open(ruta_fisica, "wb") as buffer:
            shutil.copyfileobj(imagen.file, buffer)
            
        imagen_relativa = f"img/categorias/{nombre_archivo_web}"
        
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
    
    cat_folder_name = cat_db.nombre.lower().replace(" ", "_")
    ruta_fisica = os.path.join("web", "img", "categorias", f"cat-{cat_folder_name}.jpg")
    if os.path.exists(ruta_fisica):
        os.remove(ruta_fisica)
        
    db.delete(cat_db)
    db.commit()
    return {"status": "success", "message": "Categoría eliminada."}