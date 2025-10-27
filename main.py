from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer
from interfaz import VentanaPrincipal
from conexion import conectar
from utilidades import resource_path, aplicar_tema
from temas.estilos import estilo
from utilidades import verificar_actualizacion_automatica
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
verificar_actualizacion_automatica()

# ======================================================
# 🔹 Ejecutar aplicación
# ======================================================
sys.exit(app.exec())
