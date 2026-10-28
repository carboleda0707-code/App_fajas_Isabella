import os
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

# Configura automáticamente con la variable CLOUDINARY_URL
cloudinary.config(secure=True)

async def subir_archivo_a_nube(file: UploadFile, folder: str = "fajas_isabella") -> str:
    """
    Sube imágenes o videos a Cloudinary y retorna la URL segura HTTPS.
    """
    try:
        resource_type = "video" if file.content_type and file.content_type.startswith("video/") else "image"

        resultado = cloudinary.uploader.upload(
            file.file,
            folder=folder,
            resource_type=resource_type
        )
        return resultado.get("secure_url")
    except Exception as e:
        print(f"Error al subir a Cloudinary: {e}")
        raise e