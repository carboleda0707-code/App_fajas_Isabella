from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from database import get_db, ClienteWeb, Factura

router = APIRouter(prefix="/api/web/auth", tags=["Autenticación Clientes Web"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegistroWebSchema(BaseModel):
    nombre: str
    correo: EmailStr
    password: str
    telefono: str = None
    direccion: str = None

class LoginWebSchema(BaseModel):
    correo: EmailStr
    password: str

@router.post("/registro")
def registrar_cliente_web(data: RegistroWebSchema, db: Session = Depends(get_db)):
    existente = db.query(ClienteWeb).filter(ClienteWeb.correo == data.correo).first()
    if existente:
        raise HTTPException(status_code=400, detail="Este correo ya se encuentra registrado.")
    
    hashed_password = pwd_context.hash(data.password)
    
    nuevo_cliente = ClienteWeb(
        nombre=data.nombre,
        correo=data.correo,
        password_hash=hashed_password,
        telefono=data.telefono,
        direccion=data.direccion
    )
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    
    return {
        "status": "success",
        "mensaje": "¡Cuenta creada exitosamente!",
        "cliente": {
            "id": nuevo_cliente.id,
            "nombre": nuevo_cliente.nombre,
            "correo": nuevo_cliente.correo,
            "telefono": nuevo_cliente.telefono,
            "direccion": nuevo_cliente.direccion
        }
    }

@router.post("/login")
def login_cliente_web(data: LoginWebSchema, db: Session = Depends(get_db)):
    cliente = db.query(ClienteWeb).filter(ClienteWeb.correo == data.correo).first()
    if not cliente or not pwd_context.verify(data.password, cliente.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    
    return {
        "status": "success",
        "mensaje": f"¡Bienvenido de nuevo, {cliente.nombre}!",
        "cliente": {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "correo": cliente.correo,
            "telefono": cliente.telefono,
            "direccion": cliente.direccion
        }
    }

@router.get("/pedidos/{cliente_id}")
def obtener_historial_pedidos(cliente_id: int, db: Session = Depends(get_db)):
    facturas = db.query(Factura).filter(Factura.cliente_web_id == cliente_id).all()
    
    resultado = []
    for f in facturas:
        resultado.append({
            "factura_id": f.id,
            "numero_factura": f.numero_factura,
            "fecha": str(f.fecha_factura),
            "total": f.total_factura,
            "estado_despacho": f.estado_despacho,
            "courier": f.courier_nombre or "Pendiente",
            "numero_guia": f.numero_guia or "SIN GUÍA"
        })
        
    return resultado