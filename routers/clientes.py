from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, Cliente

router = APIRouter()

class ClienteSchema(BaseModel):
    ruc_cedula: str
    nombre: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None

@router.get("/clientes")
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(Cliente).all()

@router.post("/clientes")
def guardar_cliente(cliente: ClienteSchema, db: Session = Depends(get_db)):
    db_cliente = db.query(Cliente).filter(Cliente.ruc_cedula == cliente.ruc_cedula).first()
    if db_cliente:
        db_cliente.nombre = cliente.nombre
        db_cliente.direccion = cliente.direccion
        db_cliente.telefono = cliente.telefono
    else:
        db_cliente = Cliente(**cliente.dict())
        db.add(db_cliente)
    db.commit()
    return {"status": "success", "message": "Cliente guardado."}

@router.delete("/clientes/{cliente_id}")
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    db.delete(cliente)
    db.commit()
    return {"status": "success", "message": "Cliente eliminado."}