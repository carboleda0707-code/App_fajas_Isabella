import os
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

# Configuración explícita y directa por credenciales individuales (Evita errores de firma en la nube)
CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "d82ff3dh")
API_KEY = os.getenv("CLOUDINARY_API_KEY", "497969875898695")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "RHSctv9tinyq-sNNlbtKv4wX1iA")

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET,
    secure=True
)

async def subir_archivo_a_nube(file: UploadFile, folder: str = "fajas_isabella") -> str:
    """
    Sube un archivo a Cloudinary y retorna su URL segura HTTPS.
    """
    if not file or not file.filename:
        return ""
        
    try:
        content_type = file.content_type or ""
        resource_type = "video" if content_type.startswith("video/") else "image"
        
        contenido = await file.read()
        
        resultado = cloudinary.uploader.upload(
            contenido,
            folder=folder,
            resource_type=resource_type
        )
        
        await file.seek(0)
        return resultado.get("secure_url", "")
    except Exception as e:
        print(f"Error al subir archivo a Cloudinary: {e}")
        raise e