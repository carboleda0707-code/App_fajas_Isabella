from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json

router = APIRouter(prefix="/api/despachos", tags=["Logística y Despachos"])

# Conexión a PostgreSQL (usando la variable de entorno de Railway o local)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL no configurada en el entorno.")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

class DespachoUpdate(BaseModel):
    factura_id: Optional[int] = None
    numero_factura: str
    courier: Optional[str] = "Servientrega"
    repartidor: Optional[str] = "N/D"
    numero_guia: Optional[str] = "SIN GUÍA"
    numero_control: Optional[str] = "SIN CONTROL"
    estado_despacho: Optional[str] = "PENDIENTE"

@router.get("/reporte")
def obtener_reporte_despachos():
    """Obtiene todas las facturas/órdenes con sus datos de logística, control, estado y sus ítems."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                id, 
                numero_factura, 
                cliente, 
                ruc_cedula, 
                telefono, 
                provincia, 
                ciudad, 
                direccion, 
                referencia, 
                fecha,
                COALESCE(courier, 'Servientrega') as courier,
                COALESCE(repartidor, 'N/D') as repartidor,
                COALESCE(numero_guia, 'SIN GUÍA') as numero_guia,
                COALESCE(numero_control, 'SIN CONTROL') as numero_control,
                COALESCE(estado_despacho, 'PENDIENTE') as estado_despacho,
                detalles as items
            FROM facturas
            ORDER BY id DESC;
        """)
        filas = cur.fetchall()
        
        resultado = []
        for fila in filas:
            f_dict = dict(fila)
            # Asegurar que los items vengan en formato de lista si están guardados como JSON text
            items_raw = f_dict.get("items")
            if isinstance(items_raw, str):
                try:
                    f_dict["items"] = json.loads(items_raw)
                except:
                    f_dict["items"] = []
            elif not items_raw:
                f_dict["items"] = []
            resultado.append(f_dict)
            
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en base de datos: {str(e)}")
    finally:
        cur.close()
        conn.close()

@router.post("/actualizar")
def actualizar_despacho(data: DespachoUpdate):
    """Actualiza el estado de embalaje, número de control, courier, chofer y guía en la base de datos."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if data.factura_id:
            cur.execute("SELECT id FROM facturas WHERE id = %s;", (data.factura_id,))
        else:
            cur.execute("SELECT id FROM facturas WHERE numero_factura = %s;", (data.numero_factura,))
        
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Orden de venta #{data.numero_factura} no encontrada.")
        
        f_id = row["id"]

        cur.execute("""
            UPDATE facturas 
            SET courier = %s,
                repartidor = %s,
                numero_guia = %s,
                numero_control = %s,
                estado_despacho = %s
            WHERE id = %s;
        """, (
            data.courier,
            data.repartidor or "N/D",
            data.numero_guia or "SIN GUÍA",
            data.numero_control or "SIN CONTROL",
            data.estado_despacho or "PENDIENTE",
            f_id
        ))
        
        conn.commit()
        return {"status": "success", "message": f"Orden #{data.numero_factura} actualizada correctamente a {data.estado_despacho}"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar despacho: {str(e)}")
    finally:
        cur.close()
        conn.close()