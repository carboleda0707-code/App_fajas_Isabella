from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, MovimientoInventario, Pago, Factura

router = APIRouter()

@router.get("/movimientos")
def listar_movimientos(db: Session = Depends(get_db)):
    return db.query(MovimientoInventario).order_by(MovimientoInventario.fecha_hora.desc()).all()

@router.get("/pagos")
def listar_pagos(db: Session = Depends(get_db)):
    return db.query(Pago).all()

@router.get("/facturas")
def listar_facturas(db: Session = Depends(get_db)):
    return db.query(Factura).all()