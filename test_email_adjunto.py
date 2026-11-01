import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- COLOCA TUS CREDENCIALES REALES AQUÍ PARA LA PRUEBA ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_EMISOR = "carboleda0707@gmail.com"
EMAIL_PASSWORD = "nrlzjjxinvvekyoy"
DESTINATARIO = "carboleda0707@hotmail.com"

try:
    print("1. Creando mensaje con archivo adjunto simulado...")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Prueba con Comprobante Adjunto - Fajas Isabella"
    msg["From"] = EMAIL_EMISOR
    msg["To"] = DESTINATARIO

    # Cuerpo HTML con acentos y eñes para probar la codificación UTF-8
    cuerpo_html = """
    <div style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #e11d48;">¡Prueba de Envío Exitosa!</h2>
        <p>Este correo verifica el envío de archivos adjuntos (comprobantes de pago) con codificación UTF-8 para Ecuador.</p>
    </div>
    """
    msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))

    # Simular un archivo adjunto (por ejemplo, un pequeño archivo de texto o comprobante de prueba)
    nombre_archivo = "comprobante_prueba.txt"
    contenido_archivo = b"Este es el contenido simulado del comprobante de transferencia bancaria."
    
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(contenido_archivo)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{nombre_archivo}"')
    msg.attach(part)

    print("2. Conectando al servidor SMTP...")
    server = smtplib.SMTP(str(SMTP_SERVER), int(SMTP_PORT), timeout=15)
    server.ehlo()
    server.starttls()
    server.ehlo()
    
    print("3. Autenticando...")
    server.login(EMAIL_EMISOR, EMAIL_PASSWORD)
    
    print("4. Enviando correo con adjunto...")
    server.sendmail(EMAIL_EMISOR, DESTINATARIO, msg.as_string().encode('utf-8'))
    server.quit()
    
    print("✅ ¡ÉXITO TOTAL! El correo con archivo adjunto se envió correctamente.")

except Exception as e:
    print(f"❌ ERROR DETECTADO: {type(e).__name__} -> {e}")