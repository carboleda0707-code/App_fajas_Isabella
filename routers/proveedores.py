from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, Proveedor

router = APIRouter()

class ProveedorSchema(BaseModel):
    ruc_cedula: str
    nombre_empresa: str
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

@router.get("/proveedores")
def listar_proveedores(db: Session = Depends(get_db)):
    return db.query(Proveedor).all()

@router.post("/proveedores")
def guardar_proveedor(prov: ProveedorSchema, db: Session = Depends(get_db)):
    db_prov = db.query(Proveedor).filter(Proveedor.ruc_cedula == prov.ruc_cedula).first()
    if db_prov:
        db_prov.nombre_empresa = prov.nombre_empresa
        db_prov.contacto = prov.contacto
        db_prov.telefono = prov.telefono
        db_prov.direccion = prov.direccion
    else:
        db_prov = Proveedor(**prov.dict())
        db.add(db_prov)
    db.commit()
    return {"status": "success", "message": "Proveedor guardado."}

@router.delete("/proveedores/{proveedor_id}")
def eliminar_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    prov = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
    db.delete(prov)
    db.commit()
    return {"status": "success", "message": "Proveedor eliminado."}