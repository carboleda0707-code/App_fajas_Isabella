import os
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Obtener y validar la URL de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback para desarrollo local si no está presente en el entorno
    DATABASE_URL = "postgresql+psycopg2://postgres:Litos0707@localhost:5432/fajas_isabella_db"

# Corrección para compatibilidad con SQLAlchemy en la nube usando psycopg2
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DATABASE_URL.startswith("postgresql://") and "psycopg2" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS SQLALCHEMY ---

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    ruc_cedula = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    direccion = Column(String)
    telefono = Column(String)

class Proveedor(Base):
    __tablename__ = "proveedores"
    id = Column(Integer, primary_key=True, index=True)
    ruc_cedula = Column(String, unique=True, index=True, nullable=False)
    nombre_empresa = Column(String, nullable=False)
    contacto = Column(String)
    telefono = Column(String)
    direccion = Column(String)

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    modelo = Column(String, nullable=True)
    categoria = Column(String, index=True)
    imagen_url = Column(String, nullable=True)
    en_liquidacion = Column(Boolean, default=False)
    
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- CREACIÓN AUTOMÁTICA DE TABLAS AL INICIAR ---
Base.metadata.create_all(bind=engine)