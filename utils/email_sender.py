import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_SERVER, SMTP_PORT, EMAIL_EMISOR, EMAIL_PASSWORD, NOMBRE_EMPRESA

def enviar_correo_notificacion(destinatario: str, asunto: str, mensaje_html: str):
    if not EMAIL_EMISOR or not EMAIL_PASSWORD:
        print("⚠️ No se ha configurado la contraseña de aplicación o el correo emisor en config.ini")
        return False

    server = None
    try:
        # Forzar codificación utf-8 explícita para evitar errores con tildes o eñes
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = f"{NOMBRE_EMPRESA} <{EMAIL_EMISOR}>"
        msg["To"] = destinatario

        msg.attach(MIMEText(mensaje_html, "html", "utf-8"))

        server = smtplib.SMTP(str(SMTP_SERVER), int(SMTP_PORT), timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
        server.sendmail(EMAIL_EMISOR, destinatario, msg.as_string().encode('utf-8'))
        server.quit()
        print("✅ ¡Correo enviado exitosamente!")
        return True

    except Exception as e:
        print(f"❌ Error al enviar el correo electrónico: {type(e).__name__}: {e}")
        return False
    finally:
        if server:
            try:
                server.quit()
            except:
                pass