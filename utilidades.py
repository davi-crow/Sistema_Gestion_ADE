import os, sys
from PySide6.QtWidgets import QMessageBox


def resource_path(relative_path):
    """Devuelve la ruta absoluta incluso empaquetado con PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def aplicar_tema(app, nombre_tema: str):
    """Aplica un tema Python según el nombre elegido."""
    if nombre_tema == "verde suave":
        from temas.verde_suave import obtener_estilo
    elif nombre_tema == "oscuro":
        from temas.oscuro import obtener_estilo
    elif nombre_tema == "rosa pastel":
        from temas.rosa_pastel import obtener_estilo
    elif nombre_tema == "azul moderno":
        from temas.azul_moderno import obtener_estilo
    elif nombre_tema == "claro":
        from temas.claro import obtener_estilo   
    else:
        from temas.default import obtener_estilo

    app.setStyleSheet(obtener_estilo())



# ======================================================
# 🔹 Mostrar mensajes genéricos
# ======================================================
def mostrar_mensaje(tipo, texto, parent=None):
    """Muestra un mensaje tipo info o error en una ventana modal."""
    msg = QMessageBox(parent)
    msg.setWindowTitle("Notificación")
    msg.setText(texto)
    msg.setIcon(QMessageBox.Information if tipo == "info" else QMessageBox.Critical)
    msg.exec()

