import socket

try:
    print("Probando conexion a smtp.gmail.com en el puerto 587 desde Railway...")
    s = socket.create_connection(("smtp.gmail.com", 587), timeout=10)
    print("¡CONEXIÓN EXITOSA! Railway SÍ tiene salida al puerto 587 de Google.")
    s.close()
except Exception as e:
    print(f"BLOQUEO DETECTADO O ERROR: {e}")