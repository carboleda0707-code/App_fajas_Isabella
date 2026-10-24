import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_SERVER, SMTP_PORT, EMAIL_EMISOR, EMAIL_PASSWORD, NOMBRE_EMPRESA

def enviar_correo_notificacion(destinatario: str, asunto: str, mensaje_html: str):
    if not EMAIL_EMISOR or not EMAIL_PASSWORD:
        print("⚠️ No se ha configurado la contraseña de aplicación o el correo emisor en config.ini")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = f"{NOMBRE_EMPRESA} <{EMAIL_EMISOR}>"
        msg["To"] = destinatario

        msg.attach(MIMEText(mensaje_html, "html"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        server.sendmail(EMAIL_EMISOR, destinatario, server.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Error al enviar el correo electrónico: {e}")
        return False