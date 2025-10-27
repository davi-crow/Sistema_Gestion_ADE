import mysql.connector
import configparser
import sys
import os
import socket

# ==============================================
# 🔹 RUTA DE RECURSOS (compatible con PyInstaller)
# ==============================================
def resource_path(relative_path):
    """Devuelve la ruta absoluta del recurso, compatible con PyInstaller."""
    try:
        base_path = sys._MEIPASS  # Carpeta temporal de PyInstaller
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# ==============================================
# 🔹 CARGAR CONFIGURACIÓN DESDE config.ini
# ==============================================
def cargar_config():
    ruta_config = resource_path("config.ini")
    if not os.path.exists(ruta_config):
        raise FileNotFoundError("❌ No se encontró el archivo config.ini")
    
    config = configparser.ConfigParser()
    config.read(ruta_config)
    return config["database"]


# ==============================================
# 🔹 DETECTAR IP LOCAL AUTOMÁTICAMENTE
# ==============================================
def obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
        return ip_local
    except Exception:
        return "127.0.0.1"


# ==============================================
# 🔹 CONECTAR A MYSQL
# ==============================================
def conectar():
    config = cargar_config()

    # Si en el config.ini host = auto → usar IP local
    host = config.get("host", "127.0.0.1")
    if host.lower() == "auto":
        host = obtener_ip_local()

    conexion = mysql.connector.connect(
        host=host,
        user=config.get("user", "root"),
        password=config.get("password", ""),
        database=config.get("database", "gestion_de_personas"),
        port=int(config.get("port", 3306))
    )
    return conexion
