from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, Proveedor

router = APIRouter(tags=["Proveedores"])

class ProveedorSchema(BaseModel):
    ruc_cedula: str
    nombre: str
    ciudad: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None

@router.get("/proveedores")
def listar_proveedores(db: Session = Depends(get_db)):
    proveedores = db.query(Proveedor).all()
    resultado = []
    for p in proveedores:
        resultado.append({
            "id": p.id,
            "ruc_cedula": p.ruc_cedula,
            "nombre": getattr(p, 'nombre', getattr(p, 'nombre_empresa', '')),
            "ciudad": p.ciudad or "",
            "telefono": p.telefono or "",
            "correo": p.correo or "",
            "direccion": p.direccion or ""
        })
    return resultado

@router.post("/proveedores")
def guardar_proveedor(prov: ProveedorSchema, db: Session = Depends(get_db)):
    existente = db.query(Proveedor).filter(Proveedor.ruc_cedula == prov.ruc_cedula).first()
    if existente:
        raise HTTPException(status_code=400, detail="El RUC del proveedor ya se encuentra registrado.")
    
    nuevo_prov = Proveedor(
        ruc_cedula=prov.ruc_cedula.strip(),
        nombre=prov.nombre.strip(),
        ciudad=prov.ciudad.strip().title() if prov.ciudad else None,
        telefono=prov.telefono.strip() if prov.telefono else None,
        correo=prov.correo.strip().lower() if prov.correo else None,
        direccion=prov.direccion.strip() if prov.direccion else None
    )
    db.add(nuevo_prov)
    db.commit()
    db.refresh(nuevo_prov)
    return nuevo_prov

@router.put("/proveedores/{proveedor_id}")
def actualizar_proveedor(proveedor_id: int, prov: ProveedorSchema, db: Session = Depends(get_db)):
    db_prov = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not db_prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
    
    db_prov.ruc_cedula = prov.ruc_cedula.strip()
    db_prov.nombre = prov.nombre.strip()
    db_prov.ciudad = prov.ciudad.strip().title() if prov.ciudad else None
    db_prov.telefono = prov.telefono.strip() if prov.telefono else None
    db_prov.correo = prov.correo.strip().lower() if prov.correo else None
    db_prov.direccion = prov.direccion.strip() if prov.direccion else None
    
    db.commit()
    db.refresh(db_prov)
    return {"status": "success", "message": "Proveedor actualizado correctamente.", "proveedor_id": db_prov.id}

@router.delete("/proveedores/{proveedor_id}")
def eliminar_proveedor(proveedor_id: int, db: Session = Depends(get_db)):
    prov = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
    db.delete(prov)
    db.commit()
    return {"status": "success", "message": "Proveedor eliminado."}