from database import SessionLocal, init_db, Producto, VarianteProducto

def poblar_datos():
    init_db()
    db = SessionLocal()

    # Verificar si ya existen productos para no duplicar
    if db.query(Producto.id).first():
        print("La base de datos ya contiene registros.")
        db.close()
        return

    print("Cargando catálogo ampliado de productos de Fajas Isabella...")

    # Producto 1: Faja Chaleco Reductora
    prod1 = Producto(nombre="Faja Chaleco Latex", modelo="Chaleco Clásico", descripcion="Chaleco reductor de látex de alta compresión con varillas flexibles.")
    db.add(prod1)
    db.commit()
    db.refresh(prod1)

    variantes_prod1 = [
        VarianteProducto(sku="FAJA-CHALECO-XS-NEGRO", producto_id=prod1.id, talla="XS", color="Negro", stock_actual=4, precio=45.00),
        VarianteProducto(sku="FAJA-CHALECO-S-NEGRO", producto_id=prod1.id, talla="S", color="Negro", stock_actual=10, precio=45.00),
        VarianteProducto(sku="FAJA-CHALECO-M-NEGRO", producto_id=prod1.id, talla="M", color="Negro", stock_actual=8, precio=45.00),
        VarianteProducto(sku="FAJA-CHALECO-L-BEIGE", producto_id=prod1.id, talla="L", color="Beige", stock_actual=6, precio=45.00),
        VarianteProducto(sku="FAJA-CHALECO-XL-BEIGE", producto_id=prod1.id, talla="XL", color="Beige", stock_actual=5, precio=48.00),
    ]
    db.add_all(variantes_prod1)

    # Producto 2: Cinturilla Deportiva
    prod2 = Producto(nombre="Cinturilla Deportiva Latex", modelo="PowerSport", descripcion="Ideal para entrenamientos, máxima sudoración y soporte lumbar.")
    db.add(prod2)
    db.commit()
    db.refresh(prod2)

    variantes_prod2 = [
        VarianteProducto(sku="CINT-SPORT-XS-NEGRO", producto_id=prod2.id, talla="XS", color="Negro", stock_actual=7, precio=35.00),
        VarianteProducto(sku="CINT-SPORT-S-AZUL", producto_id=prod2.id, talla="S", color="Azul", stock_actual=6, precio=35.00),
        VarianteProducto(sku="CINT-SPORT-M-ROSA", producto_id=prod2.id, talla="M", color="Rosa", stock_actual=9, precio=35.00),
        VarianteProducto(sku="CINT-SPORT-L-NEGRO", producto_id=prod2.id, talla="L", color="Negro", stock_actual=4, precio=38.00),
    ]
    db.add_all(variantes_prod2)

    # Producto 3: Faja Enteriza Moldeadora
    prod3 = Producto(nombre="Faja Enteriza invisible", modelo="Full Body Control", descripcion="Control total de abdomen, cintura, cadera y levanta glúteos natural.")
    db.add(prod3)
    db.commit()
    db.refresh(prod3)

    variantes_prod3 = [
        VarianteProducto(sku="ENT-INV-S-COCOA", producto_id=prod3.id, talla="S", color="Cocoa", stock_actual=5, precio=65.00),
        VarianteProducto(sku="ENT-INV-M-COCOA", producto_id=prod3.id, talla="M", color="Cocoa", stock_actual=8, precio=65.00),
        VarianteProducto(sku="ENT-INV-L-NEGRO", producto_id=prod3.id, talla="L", color="Negro", stock_actual=6, precio=65.00),
        VarianteProducto(sku="ENT-INV-XL-NEGRO", producto_id=prod3.id, talla="XL", color="Negro", stock_actual=3, precio=70.00),
    ]
    db.add_all(variantes_prod3)

    # Producto 4: Short Levanta Glúteos
    prod4 = Producto(nombre="Short Levanta Glúteos Compresión", modelo="PushUp Classic", descripcion="Short moldeador con encaje de silicona en las piernas.")
    db.add(prod4)
    db.commit()
    db.refresh(prod4)

    variantes_prod4 = [
        VarianteProducto(sku="SHORT-PUSH-S-BEIGE", producto_id=prod4.id, talla="S", color="Beige", stock_actual=12, precio=28.00),
        VarianteProducto(sku="SHORT-PUSH-M-BEIGE", producto_id=prod4.id, talla="M", color="Beige", stock_actual=15, precio=28.00),
        VarianteProducto(sku="SHORT-PUSH-L-NEGRO", producto_id=prod4.id, talla="L", color="Negro", stock_actual=10, precio=28.00),
    ]
    db.add_all(variantes_prod4)

    # Producto 5: Faja Postquirúrgica Alta
    prod5 = Producto(nombre="Faja Postquirúrgica con Corchetes", modelo="Recuperación Total", descripcion="Diseñada para procesos estéticos y postparto con doble refuerzo.")
    db.add(prod5)
    db.commit()
    db.refresh(prod5)

    variantes_prod5 = [
        VarianteProducto(sku="POST-ALT-S-AZUL", producto_id=prod5.id, talla="S", color="Azul", stock_actual=4, precio=80.00),
        VarianteProducto(sku="POST-ALT-M-BEIGE", producto_id=prod5.id, talla="M", color="Beige", stock_actual=7, precio=80.00),
        VarianteProducto(sku="POST-ALT-L-BEIGE", producto_id=prod5.id, talla="L", color="Beige", stock_actual=5, precio=85.00),
    ]
    db.add_all(variantes_prod5)

    db.commit()
    db.close()
    print("¡Catálogo ampliado de prueba cargado con éxito!")

if __name__ == "__main__":
    poblar_datos()