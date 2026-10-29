import configparser
import os

config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(__file__), "config.ini")

if os.path.exists(config_file_path):
    config.read(config_file_path, encoding="utf-8")

# Datos Principales de la Empresa
NOMBRE_EMPRESA = config.get("EMPRESA", "nombre", fallback="Fajas Isabella")
TELEFONO_WHATSAPP = config.get("EMPRESA", "telefono_whatsapp", fallback="593985389751")
CORREO_EMPRESA = config.get("EMPRESA", "correo_contacto", fallback="ventas@fajasisabella.com")
DIRECCION_EMPRESA = config.get("EMPRESA", "direccion_local", fallback="Guayaquil, Ecuador")

# Redes Sociales
INSTAGRAM_URL = config.get("REDES_SOCIALES", "instagram", fallback="https://instagram.com/fajasisabella.ec")
FACEBOOK_URL = config.get("REDES_SOCIALES", "facebook", fallback="https://facebook.com/FajasIsabella?")
TIKTOK_URL = config.get("REDES_SOCIALES", "tiktok", fallback="https://www.tiktok.com/@fajasisabella.ec")
WHATSAPP_LINK = config.get("REDES_SOCIALES", "whatsapp_url", fallback=f"https://wa.me/{+593985389751}")

# Credenciales de Correo Electrónico (SMTP)
SMTP_SERVER = config.get("EMAIL_NOTIFICACIONES", "smtp_server", fallback="smtp.gmail.com")
SMTP_PORT = config.getint("EMAIL_NOTIFICACIONES", "smtp_port", fallback=587)
EMAIL_EMISOR = config.get("EMAIL_NOTIFICACIONES", "email_emisor", fallback="")
EMAIL_PASSWORD = config.get("EMAIL_NOTIFICACIONES", "email_password", fallback="")