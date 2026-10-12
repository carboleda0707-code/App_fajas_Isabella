import os
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# 1. Obtener la URL de la base de datos desde las variables de entorno (Railway / Producción)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback para entorno de desarrollo local
    DATABASE_URL = "postgresql+psycopg2://postgres:Litos0707@localhost:5432/fajas_isabella_db"

# 2. Corrección automática de prefijos para compatibilidad con SQLAlchemy en la nube
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
    ciudad = Column(String(100), nullable=True)
    telefono = Column(String)
    correo = Column(String, nullable=True)
    tipo_precio = Column(String(50), default='REGULAR')
    descuento_porcentaje = Column(Float, default=0.0)

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
    
    provincia = Column(String(100), nullable=True)
    ciudad = Column(String(100), nullable=True)
    direccion_entrega = Column(String, nullable=True)
    referencia_direccion = Column(String, nullable=True)
    courier_nombre = Column(String(50), nullable=True)
    numero_guia = Column(String(100), nullable=True)
    estado_despacho = Column(String(30), default='PENDIENTE')

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

# --- NUEVO: MODELO DE USUARIOS PARA EL PANEL ADMINISTRATIVO ---
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default="Ventas")  # Administrador, Ventas, Despacho
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- CREACIÓN Y AUTO-MIGRACIÓN EN CALIENTE AL INICIAR ---
Base.metadata.create_all(bind=engine)

def asegurar_columnas_logistica():
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS provincia VARCHAR(100);"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS ciudad VARCHAR(100);"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS direccion_entrega TEXT;"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS referencia_direccion TEXT;"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS courier_nombre VARCHAR(50);"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS numero_guia VARCHAR(100);"))
        conn.execute(text("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS estado_despacho VARCHAR(30) DEFAULT 'PENDIENTE';"))
        conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS ciudad VARCHAR(100);"))
        conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS correo VARCHAR;"))
        conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS tipo_precio VARCHAR(50) DEFAULT 'REGULAR';"))
        conn.execute(text("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS descuento_porcentaje FLOAT DEFAULT 0.0;"))
        conn.execute(text("ALTER TABLE movimientos_inventario ADD COLUMN IF NOT EXISTS valor_neto FLOAT;"))

try:
    asegurar_columnas_logistica()
except Exception as e:
    print(f"Nota sobre migración automática en caliente: {e}")

# --- CREAR USUARIO ADMINISTRADOR MASTER INICIAL SI NO EXISTE ---
def crear_usuario_inicial():
    db = SessionLocal()
    try:
        admin_existente = db.query(Usuario).filter(Usuario.username == "admin").first()
        if not admin_existente:
            admin_default = Usuario(
                username="admin",
                email="admin@fajasisabella.com",
                password="FajasIsabella2026*",
                rol="Administrador",
                activo=True
            )
            db.add(admin_default)
            db.commit()
            print("🟢 Usuario Administrador inicial creado correctamente.")
    except Exception as e:
        print(f"⚠️ Error al crear usuario inicial: {e}")
        db.rollback()
    finally:
        db.close()

try:
    crear_usuario_inicial()
except Exception as e:
    print(f"Nota sobre usuario inicial: {e}")