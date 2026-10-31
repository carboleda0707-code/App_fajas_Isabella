import configparser
import os

config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), "config.ini")

if os.path.exists(config_file_path):
    config.read(config_file_path, encoding="utf-8")

# Datos Principales de la Empresa con respaldo en Variables de Entorno
NOMBRE_EMPRESA = config.get("EMPRESA", "nombre", fallback=os.getenv("NOMBRE_EMPRESA", "Fajas Isabella"))
TELEFONO_WHATSAPP = config.get("EMPRESA", "telefono_whatsapp", fallback=os.getenv("TELEFONO_WHATSAPP", "+593 985 389 751"))
CORREO_EMPRESA = config.get("EMPRESA", "correo_contacto", fallback=os.getenv("CORREO_EMPRESA", "ventas@fajasisabella.com"))
DIRECCION_EMPRESA = config.get("EMPRESA", "direccion_local", fallback=os.getenv("DIRECCION_EMPRESA", "Guayaquil, Ecuador"))

# Redes Sociales
INSTAGRAM_URL = config.get("REDES_SOCIALES", "instagram", fallback="https://instagram.com/fajasisabella.ec")
FACEBOOK_URL = config.get("REDES_SOCIALES", "facebook", fallback="https://facebook.com/FajasIsabella?")
TIKTOK_URL = config.get("REDES_SOCIALES", "tiktok", fallback="https://www.tiktok.com/@fajasisabella.ec")
WHATSAPP_LINK = config.get("REDES_SOCIALES", "whatsapp_url", fallback="https://wa.me/+593985389751")

# Credenciales de Correo Electrónico (SMTP) con respaldo prioritario en os.getenv
SMTP_SERVER = config.get("EMAIL_NOTIFICACIONES", "smtp_server", fallback=os.getenv("SMTP_SERVER", "smtp.gmail.com"))
SMTP_PORT = config.getint("EMAIL_NOTIFICACIONES", "smtp_port", fallback=int(os.getenv("SMTP_PORT", 587)))
EMAIL_EMISOR = config.get("EMAIL_NOTIFICACIONES", "email_emisor", fallback=os.getenv("EMAIL_EMISOR", ""))
EMAIL_PASSWORD = config.get("EMAIL_NOTIFICACIONES", "email_password", fallback=os.getenv("EMAIL_PASSWORD", ""))