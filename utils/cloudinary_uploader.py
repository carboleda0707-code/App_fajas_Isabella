import os
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

# --- CHIVATO DE CREDENCIALES ---
cloud_name_env = os.getenv("CLOUDINARY_CLOUD_NAME", "")
api_key_env = os.getenv("CLOUDINARY_API_KEY", "")
api_secret_env = os.getenv("CLOUDINARY_API_SECRET", "")

print(f"--- [CHIVATO CLOUDINARY] ---")
print(f"CLOUD_NAME leído: '{cloud_name_env}' (Largo: {len(cloud_name_env)})")
print(f"API_KEY leído: '{api_key_env}' (Largo: {len(api_key_env)})")
print(f"API_SECRET leído: '{api_secret_env[:4]}...' (Largo: {len(api_secret_env)})")
print(f"---------------------------")

# Configuración explícita
cloudinary.config(
    cloud_name=cloud_name_env.strip(),
    api_key=api_key_env.strip(),
    api_secret=api_secret_env.strip(),
    secure=True
)

async def subir_archivo_a_nube(file: UploadFile, folder: str = "fajas_isabella") -> str:
    """
    Sube un archivo a Cloudinary y retorna su URL segura HTTPS con depuración.
    """
    if not file or not file.filename:
        return ""
        
    try:
        content_type = file.content_type or ""
        resource_type = "video" if content_type.startswith("video/") else "image"
        
        contenido = await file.read()
        print(f"Subiendo archivo '{file.filename}' a la carpeta '{folder}'...")
        
        resultado = cloudinary.uploader.upload(
            contenido,
            folder=folder,
            resource_type=resource_type
        )
        
        print(f"¡Subida exitosa! URL: {resultado.get('secure_url', '')}")
        await file.seek(0)
        return resultado.get("secure_url", "")
    except Exception as e:
        print(f"❌ [ERROR CLOUDINARY UPLOAD]: {e}")
        raise e