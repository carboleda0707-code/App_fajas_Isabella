import os
import requests
import base64

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

def enviar_correo_nueva_venta(datos_pedido: dict, comprobante_bytes: bytes = None, comprobante_nombre: str = None):
    """
    CUENTA A (Brevo): Notificación interna al equipo de ventas cuando se registra un pedido web.
    """
    api_key = os.getenv("BREVO_VENTAS_API_KEY")
    remitente = os.getenv("EMAIL_VENTAS_ORIGEN", "ventas@fajasisabella.com")
    destinatario = os.getenv("EMAIL_DESTINO_VENTAS", "carboleda0707@gmail.com")

    if not api_key:
        print("⚠️ Advertencia: BREVO_VENTAS_API_KEY no está configurada.")
        return False

    payload = {
        "sender": {"email": remitente, "name": "Fajas Isabella - E-commerce"},
        "to": [{"email": destinatario}],
        "subject": f"🔥 Nuevo Pedido Web #{datos_pedido['num_factura']} - {datos_pedido['razon_social']}",
        "htmlContent": f"""
            <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; padding: 20px; border: 1px solid #eee; border-radius: 8px;">
                <h2 style="color: #e11d48; text-align: center;">¡Nuevo Pedido en la Tienda Web!</h2>
                <p>Se ha registrado el pedido <strong>#{datos_pedido['num_factura']}</strong> exitosamente.</p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <h3>📋 Datos del Cliente:</h3>
                <p>
                    <strong>Cliente:</strong> {datos_pedido['razon_social']}<br>
                    <strong>RUC/Cédula:</strong> {datos_pedido['ruc_cedula']}<br>
                    <strong>Teléfono:</strong> {datos_pedido['telefono']}<br>
                    <strong>Ciudad/Provincia:</strong> {datos_pedido['ciudad']}, {datos_pedido['provincia']}<br>
                    <strong>Dirección:</strong> {datos_pedido['direccion']}
                </p>
                <h3 style="color: #e11d48;">Total a Pagar: ${datos_pedido['total']:.2f}</h3>
                <p>Por favor ingrese al panel administrativo para verificar el comprobante y aprobar el pago.</p>
            </div>
        """
    }

    if comprobante_bytes and comprobante_nombre:
        encoded_file = base64.b64encode(comprobante_bytes).decode('utf-8')
        payload["attachment"] = [{
            "content": encoded_file,
            "name": comprobante_nombre
        }]

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    try:
        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=15)
        if response.status_code == 201:
            print("✅ ¡Correo de notificación a ventas enviado exitosamente vía Brevo A!")
            return True
        else:
            print(f"❌ Error Brevo Ventas: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión al enviar correo de ventas: {e}")
        return False


def enviar_correo_pago_aprobado(correo_cliente: str, nombre_cliente: str, pedido_id: str):
    """
    CUENTA B (Brevo): Notificación directa al cliente final cuando haces clic en 'Aprobar Pago'.
    """
    api_key = os.getenv("BREVO_CLIENTES_API_KEY")
    remitente = os.getenv("EMAIL_CLIENTES_ORIGEN", "despachos@fajasisabella.com")

    if not api_key:
        print("⚠️ Advertencia: BREVO_CLIENTES_API_KEY no está configurada.")
        return False

    if not correo_cliente or "@" not in correo_cliente:
        print("⚠️ El cliente no tiene un correo válido registrado.")
        return False

    payload = {
        "sender": {"email": remitente, "name": "Fajas Isabella"},
        "to": [{"email": correo_cliente}],
        "subject": f"¡Pago Aprobado! Tu pedido #{pedido_id} está en camino a empaque",
        "htmlContent": f"""
            <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; padding: 20px; border: 1px solid #eee; border-radius: 8px;">
                <h2 style="color: #0d9488; text-align: center;">¡Hola {nombre_cliente}, excelentes noticias!</h2>
                <p>Hemos verificado y <b>aprobado tu comprobante de pago</b> correspondiente al pedido <b>#{pedido_id}</b>.</p>
                <p>Tu paquete ya fue asignado a nuestra bodega en Guayaquil para su respectivo proceso de empaque y despacho seguro.</p>
                <br>
                <p>Te notificaremos cuando el courier recoja tu paquete. ¡Gracias por confiar en Fajas Isabella!</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin-top: 20px;">
                <p style="font-size: 11px; color: #888; text-align: center;">Mensaje automático enviado desde la plataforma de Fajas Isabella.</p>
            </div>
        """
    }

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    try:
        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=15)
        if response.status_code == 201:
            print(f"✅ ¡Correo de pago aprobado enviado exitosamente al cliente {correo_cliente} vía Brevo B!")
            return True
        else:
            print(f"❌ Error Brevo Clientes: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión al enviar correo al cliente: {e}")
        return False