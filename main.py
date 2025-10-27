from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer
from interfaz import VentanaPrincipal
from conexion import conectar
from utilidades import resource_path, aplicar_tema
from temas.estilos import estilo
import sys, os, requests

# ======================================================
# 🔹 Crear aplicación
# ======================================================
app = QApplication(sys.argv)

# Aplicar estilo base global
app.setStyleSheet(str(estilo()).strip())

# Aplicar tema inicial
aplicar_tema(app, "verde_suave")  # Solo uno

# ======================================================
# 🔹 Conectar base de datos
# ======================================================
try:
    conexion = conectar()
    if not conexion.is_connected():
        raise Exception("No se pudo establecer la conexión con MySQL.")
    print("✅ Conexión exitosa con la base de datos.")
except Exception as e:
    QMessageBox.critical(
        None,
        "Error de conexión",
        f"❌ No se pudo conectar a la base de datos.\nDetalles: {e}\n\n"
        "Verifique las credenciales o que el servidor MySQL esté activo."
    )
    sys.exit(1)


# ======================================================
# 🔹 Función de actualización (opcional)
# ======================================================
def verificar_actualizacion():
    """Comprueba si hay una versión nueva en un servidor remoto."""
    try:
        version_actual = "1.2"
        url_version = "https://tu-sitio.com/version.txt"
        version_remota = requests.get(url_version, timeout=5).text.strip()
        if version_actual != version_remota:
            print(f"⚠️ Nueva versión disponible: {version_remota} (actual: {version_actual})")
        else:
            print("✅ La aplicación está actualizada.")
    except Exception as e:
        print(f"⚠️ No se pudo verificar la actualización: {e}")


# ======================================================
# 🔹 Crear ventana principal
# ======================================================
window = VentanaPrincipal(conexion)

# ======================================================
# 🔹 Mostrar Splash Screen
# ======================================================
logo_path = resource_path("iconos/logo.png")
splash = None

if os.path.exists(logo_path):
    pixmap = QPixmap(logo_path).scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    splash.show()
else:
    print(f"⚠️ No se encontró el logo en: {logo_path}")


# ======================================================
# 🔹 Mostrar ventana principal tras el splash
# ======================================================
def mostrar_ventana():
    if splash:
        splash.close()
    window.show()

QTimer.singleShot(2000, mostrar_ventana)

# ======================================================
# 🔹 Ejecutar aplicación
# ======================================================
sys.exit(app.exec())
