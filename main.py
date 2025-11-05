from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer
from interfaz import VentanaPrincipal
from auto_discover import auto_find_server
from conexion import conectar
from utilidades import (
    resource_path,
    aplicar_tema,
    obtener_tema,
    verificar_actualizacion_con_dialogo
)
from temas.estilos import estilo
import sys, os

auto_find_server()
# ======================================================
# 🔹 Crear aplicación
# ======================================================
def main():
    app = QApplication(sys.argv)

    # Aplicar estilo base global
    app.setStyleSheet(str(estilo()).strip())

    # Aplicar tema guardado por el usuario
    tema_guardado = obtener_tema()
    aplicar_tema(app, tema_guardado)
    print(f"🎨 Tema aplicado al iniciar: {tema_guardado}")

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
        return 1

    # ======================================================
    # 🔹 Crear ventana principal
    # ======================================================
    window = VentanaPrincipal(conexion)

    # ======================================================
    # 🔹 Splash Screen
    # ======================================================
    logo_path = resource_path("iconos/logo.png")
    splash = None

    if os.path.exists(logo_path):
        pixmap = QPixmap(logo_path).scaled(
            250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
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
        # 🔄 Verificar actualización con un pequeño retraso
        QTimer.singleShot(3000, lambda: verificar_actualizacion_con_dialogo(window))

    QTimer.singleShot(2000, mostrar_ventana)

    # ======================================================
    # 🔹 Ejecutar aplicación
    # ======================================================
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())