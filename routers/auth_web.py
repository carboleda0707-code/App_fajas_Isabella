from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from database import get_db, ClienteWeb, Factura
import traceback

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
    try:
        existente = db.query(ClienteWeb).filter(ClienteWeb.correo == data.correo).first()
        if existente:
            raise HTTPException(status_code=400, detail="Este correo ya se encuentra registrado.")
        
        # Corrección: Bcrypt limita la contraseña a 72 bytes máximo
        password_bytes = data.password.encode('utf-8')[:72]
        hashed_password = pwd_context.hash(password_bytes)
        
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
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        error_detallado = traceback.format_exc()
        print("ERROR EN REGISTRO:", error_detallado)
        raise HTTPException(status_code=400, detail=f"Error interno: {str(e)}")

@router.post("/login")
def login_cliente_web(data: LoginWebSchema, db: Session = Depends(get_db)):
    try:
        cliente = db.query(ClienteWeb).filter(ClienteWeb.correo == data.correo).first()
        password_bytes = data.password.encode('utf-8')[:72]
        
        if not cliente or not pwd_context.verify(password_bytes, cliente.password_hash):
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en login: {str(e)}")

@router.get("/pedidos/{cliente_id}")
def obtener_historial_pedidos(cliente_id: int, db: Session = Depends(get_db)):
    facturas = db.query(Factura).filter(Factura.cliente_web_id == cliente_id).all()
    
    resultado = []
    for f in facturas:
        val_nc = f.numero_control
        ctrl_str = str(val_nc).strip() if (val_nc is not None and str(val_nc).strip() not in ["None", "null", "", "SIN CONTROL", "nan", "NaN"]) else "SIN CONTROL"

        val_g2 = f.numero_guia_2
        g2_str = str(val_g2).strip() if (val_g2 is not None and str(val_g2).strip() not in ["None", "null", "", "SIN GUÍA 2"]) else "SIN GUÍA 2"

        resultado.append({
            "factura_id": f.id,
            "numero_factura": f.numero_factura,
            "fecha": str(f.fecha_factura),
            "total": f.total_factura,
            "estado_despacho": f.estado_despacho or "PENDIENTE",
            "courier": f.courier_nombre or "Pendiente",
            "numero_guia": f.numero_guia or "SIN GUÍA",
            "numero_guia_2": g2_str,      # <--- Guía del motorizado independiente
            "numero_control": ctrl_str    # <--- Número de control independiente
        })
        
    return resultado