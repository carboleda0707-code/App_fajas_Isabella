import os
import boto3
from botocore.config import Config
from fastapi import UploadFile
import uuid

# --- CREDENCIALES DE CLOUDFLARE R2 ---
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "fajas-isabella-media")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL", "")
R2_PUBLIC_DOMAIN = os.getenv("R2_PUBLIC_DOMAIN", "")

def obtener_cliente_s3():
    """Inicializa y retorna el cliente S3 validando que el endpoint no esté vacío."""
    endpoint = os.getenv("R2_ENDPOINT_URL", R2_ENDPOINT_URL)
    access_key = os.getenv("R2_ACCESS_KEY_ID", R2_ACCESS_KEY_ID)
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY", R2_SECRET_ACCESS_KEY)

    if not endpoint or not endpoint.startswith("http"):
        raise ValueError("⚠️ R2_ENDPOINT_URL no está configurado correctamente en las variables de entorno o archivo .env.")

    return boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

async def subir_archivo_a_nube(file: UploadFile, folder: str = "fajas_isabella") -> str:
    """
    Sube un archivo a Cloudflare R2 y retorna su URL pública HTTPS.
    """
    if not file or not file.filename:
        return ""
        
    try:
        s3_client = obtener_cliente_s3()
        bucket_name = os.getenv("R2_BUCKET_NAME", R2_BUCKET_NAME)
        public_domain = os.getenv("R2_PUBLIC_DOMAIN", R2_PUBLIC_DOMAIN)
        endpoint_url = os.getenv("R2_ENDPOINT_URL", R2_ENDPOINT_URL)

        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{folder}/{uuid.uuid4()}{file_extension}"
        
        contenido = await file.read()
        print(f"Subiendo archivo '{file.filename}' a Cloudflare R2 en la ruta '{unique_filename}'...")
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=unique_filename,
            Body=contenido,
            ContentType=file.content_type or "application/octet-stream"
        )
        
        if public_domain:
            secure_url = f"{public_domain.rstrip('/')}/{unique_filename}"
        else:
            secure_url = f"{endpoint_url.rstrip('/')}/{bucket_name}/{unique_filename}"
            
        print(f"¡Subida exitosa a R2! URL: {secure_url}")
        
        # Corregido: Llamada síncrona a seek(0) sin await
        file.seek(0)
        return secure_url
        
    except Exception as e:
        print(f"❌ [ERROR CLOUDFLARE R2 UPLOAD]: {e}")
        raise e