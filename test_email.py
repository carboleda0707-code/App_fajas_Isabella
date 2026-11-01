import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configura tus datos aquí directamente para la prueba
SMTP_SERVER = "smtp.gmail.com"  # O tu servidor (ej. smtp.office365.com)
SMTP_PORT = 587
EMAIL_EMISOR = "tu_correo@gmail.com"
EMAIL_PASSWORD = "tu_contraseña_de_aplicacion"
DESTINATARIO = "tu_correo@gmail.com" # Envíatelo a ti mismo para probar

try:
    print("1. Conectando al servidor SMTP...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
    server.ehlo()
    
    print("2. Iniciando TLS...")
    server.starttls()
    server.ehlo()
    
    print("3. Autenticando...")
    server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
    
    print("4. Armando mensaje...")
    msg = MIMEMultipart()
    msg["Subject"] = "Prueba de envío Fajas Isabella"
    msg["From"] = EMAIL_EMISOR
    msg["To"] = DESTINATARIO
    msg.attach(MIMEText("Este es un correo de prueba para verificar el sistema.", "plain"))
    
    print("5. Enviando correo...")
    server.sendmail(EMAIL_EMISOR, DESTINATARIO, msg.as_string())
    server.quit()
    print("✅ ¡ÉXITO! El correo se envió correctamente.")

except Exception as e:
    print(f"❌ ERROR DETECTADO: {type(e).__name__} -> {e}")