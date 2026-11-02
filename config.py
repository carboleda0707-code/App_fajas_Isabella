import configparser
import os

config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), "config.ini")

if os.path.exists(config_file_path):
    config.read(config_file_path, encoding="utf-8")

# Datos Principales de la Empresa (Leyendo de Railway o del config.ini con fallback seguro)
NOMBRE_EMPRESA = os.getenv("NOMBRE_EMPRESA") or config.get("EMPRESA", "nombre", fallback="Fajas Isabella")
TELEFONO_WHATSAPP = os.getenv("TELEFONO_WHATSAPP") or config.get("EMPRESA", "telefono_whatsapp", fallback="+593 98 538 9751")
CORREO_EMPRESA = os.getenv("CORREO_EMPRESA") or config.get("EMPRESA", "correo_contacto", fallback="ventas@fajasisabella.com")
DIRECCION_EMPRESA = os.getenv("DIRECCION_EMPRESA") or config.get("EMPRESA", "direccion_local", fallback="Guayaquil, Ecuador")

# Redes Sociales
INSTAGRAM_URL = config.get("REDES_SOCIALES", "instagram", fallback="https://instagram.com/fajasisabella.ec")
FACEBOOK_URL = config.get("REDES_SOCIALES", "facebook", fallback="https://www.facebook.com/FajasIsabella?")
TIKTOK_URL = config.get("REDES_SOCIALES", "tiktok", fallback="https://www.tiktok.com/@fajasisabella.ec")
WHATSAPP_LINK = config.get("REDES_SOCIALES", "whatsapp_url", fallback="https://wa.me/+593985389751")

# Credenciales de Correo Electrónico (SMTP - Puerto 465 SSL)
SMTP_SERVER = os.getenv("SMTP_SERVER") or config.get("EMAIL_NOTIFICACIONES", "smtp_server", fallback="smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT") or config.getint("EMAIL_NOTIFICACIONES", "smtp_port", fallback=465))
EMAIL_EMISOR = os.getenv("EMAIL_EMISOR") or config.get("EMAIL_NOTIFICACIONES", "email_emisor", fallback="carboleda0707@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") or config.get("EMAIL_NOTIFICACIONES", "email_password", fallback="nrlzjjxinvvekyoy")