import os
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Detección automática de entorno:
is_railway = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID") or os.getenv("PORT")

if is_railway:
    # Si estamos en producción (Railway), toma la URL de forma segura desde las variables de entorno
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    # Si estamos en desarrollo local, usamos la base de datos local de DBeaver
    DATABASE_URL = "postgresql+psycopg2://postgres:Litos0707@localhost:5432/fajas_isabella_db"

if not DATABASE_URL:
    DATABASE_URL = "postgresql+psycopg2://postgres:Litos0707@localhost:5432/fajas_isabella_db"

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DATABASE_URL.startswith("postgresql://") and "psycopg2" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    ruc_cedula = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    direccion = Column(String, nullable=True)
    ciudad = Column(String(100), nullable=True)
    telefono = Column(String, nullable=True)
    correo = Column(String, unique=True, index=True, nullable=True)
    password = Column(String(255), nullable=True)  # Contraseña en formato estricto SHA-256
    cliente_web = Column(Boolean, default=False)   # Indicador si proviene o interactúa por la web
    tipo_precio = Column(String(50), default='REGULAR')
    descuento_porcentaje = Column(Float, default=0.0)

    facturas = relationship("Factura", back_populates="cliente")

class Proveedor(Base):
    __tablename__ = "proveedores"
    id = Column(Integer, primary_key=True, index=True)
    ruc_cedula = Column(String, unique=True, index=True)
    nombre_empresa = Column(String)
    contacto = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    ciudad = Column(String, nullable=True)
    correo = Column(String, nullable=True)

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    modelo = Column(String, nullable=True)
    categoria = Column(String, index=True)
    imagen_url = Column(String, nullable=True)
    en_liquidacion = Column(Boolean, default=False)
    es_nuevo = Column(Boolean, default=False)
    en_oferta = Column(Boolean, default=False)
    descuento_oferta = Column(Float, default=0.0)
    
    variantes = relationship("VarianteProducto", back_populates="producto", cascade="all, delete-orphan")

class VarianteProducto(Base):
    __tablename__ = "variantes_producto"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    talla = Column(String, nullable=False) 
    color = Column(String, nullable=False)
    stock_actual = Column(Integer, default=0)
    precio = Column(Float, nullable=False)
    
    stock_minimo = Column(Integer, default=2)
    stock_maximo = Column(Integer, default=20)
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_ultima_venta = Column(DateTime, nullable=True)
    
    producto = relationship("Producto", back_populates="variantes")

class Factura(Base):
    __tablename__ = "facturas"
    id = Column(Integer, primary_key=True, index=True)
    tipo_factura = Column(String, nullable=False)
    numero_factura = Column(String, unique=True, index=True, nullable=False)
    numero_autorizacion = Column(String, nullable=True)
    fecha_factura = Column(Date, default=date.today)
    entidad_ruc = Column(String, nullable=False)
    entidad_nombre = Column(String, nullable=False)
    total_factura = Column(Float, nullable=False, default=0.0)
    
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    provincia = Column(String(100), nullable=True)
    ciudad = Column(String(100), nullable=True)
    direccion_entrega = Column(String, nullable=True)
    referencia_direccion = Column(String, nullable=True)
    courier_nombre = Column(String(50), nullable=True)
    repartidor = Column(String(100), nullable=True)
    numero_guia = Column(String(100), nullable=True)
    numero_control = Column(String(100), nullable=True)
    estado_despacho = Column(String(30), default='PENDIENTE')

    cliente = relationship("Cliente", back_populates="facturas")
    pagos = relationship("Pago", back_populates="factura", cascade="all, delete-orphan")

class Pago(Base):
    __tablename__ = "pagos"
    id = Column(Integer, primary_key=True, index=True)
    factura_id = Column(Integer, ForeignKey("facturas.id"))
    metodo_pago = Column(String, nullable=False)
    codigo_transferencia = Column(String, nullable=True)
    monto = Column(Float, nullable=False)
    fecha_pago = Column(DateTime, default=datetime.now)
    
    factura = relationship("Factura", back_populates="pagos")

class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    imagen_url = Column(String)

class MovimientoInventario(Base):
    __tablename__ = "movimientos_inventario"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, nullable=False)
    tipo_movimiento = Column(String, nullable=False) 
    cantidad = Column(Integer, nullable=False)
    referencia_factura = Column(String) 
    valor_neto = Column(Float, nullable=True)
    entidad_asociada = Column(String) 
    fecha_hora = Column(DateTime, default=datetime.now)

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default="Ventas")
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)

def asegurar_columnas_logistica():
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS provincia VARCHAR(100);"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS ciudad VARCHAR(100);"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS direccion_entrega TEXT;"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS referencia_direccion TEXT;"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS courier_nombre VARCHAR(50);"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS repartidor VARCHAR(100);"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS numero_guia VARCHAR(100);"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS numero_control VARCHAR(100);"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS estado_despacho VARCHAR(30) DEFAULT 'PENDIENTE';"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS cliente_id INTEGER;"))
        conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS ciudad VARCHAR(100);"))
        conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS correo VARCHAR;"))
        conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS password VARCHAR(255);"))
        conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS telefono VARCHAR(50);"))
        conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS direccion TEXT;"))
        conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS cliente_web BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS tipo_precio VARCHAR(50) DEFAULT 'REGULAR';"))
        conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS descuento_porcentaje FLOAT DEFAULT 0.0;"))
        conn.execute(text("ALTER TABLE movimientos_inventario ADD COLUMN IF NOT EXISTS valor_neto FLOAT;"))
        conn.execute(text("ALTER TABLE productos ADD COLUMN IF NOT EXISTS en_liquidacion BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE productos ADD COLUMN IF NOT EXISTS es_nuevo BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE productos ADD COLUMN IF NOT EXISTS en_oferta BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE productos ADD COLUMN IF NOT EXISTS descuento_oferta FLOAT DEFAULT 0.0;"))
        conn.execute(text("ALTER TABLE variantes_producto ADD COLUMN IF NOT EXISTS stock_minimo INTEGER DEFAULT 2;"))
        conn.execute(text("ALTER TABLE variantes_producto ADD COLUMN IF NOT EXISTS stock_maximo INTEGER DEFAULT 20;"))
        conn.execute(text("ALTER TABLE variantes_producto ADD COLUMN IF NOT EXISTS fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
        conn.execute(text("ALTER TABLE variantes_producto ADD COLUMN IF NOT EXISTS fecha_ultima_venta TIMESTAMP;"))

try:
    asegurar_columnas_logistica()
except Exception as e:
    print(f"Nota sobre migración automática en caliente: {e}")