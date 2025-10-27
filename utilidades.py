import os, sys
from PySide6.QtWidgets import QMessageBox
import tempfile
import subprocess
import requests

__version__ = "1.2"  # versión actual local

OWNER = "davi-crow"
REPO = "Sistema_Gestion_ADE"

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


def verificar_actualizacion_automatica():
    """Verifica automáticamente si hay una nueva versión en GitHub y la instala."""
    try:
        print("🔍 Buscando actualizaciones...")
        api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
        r = requests.get(api_url, timeout=10)
        r.raise_for_status()
        data = r.json()

        version_remota = data.get("tag_name", "").lstrip("v")
        if not version_remota:
            print("⚠️ No se pudo obtener la versión remota.")
            return

        if version_remota == __version__:
            print("✅ Ya tienes la versión más reciente.")
            return

        print(f"⚠️ Nueva versión disponible: {version_remota} (actual: {__version__})")

        # Buscar el archivo ejecutable en los assets
        assets = data.get("assets", [])
        download_url = None
        for a in assets:
            if a["name"].endswith(".exe"):
                download_url = a["browser_download_url"]
                break

        if not download_url:
            print("⚠️ No se encontró el ejecutable en la release.")
            return

        # Descarga el nuevo .exe en una carpeta temporal
        tmp_dir = tempfile.mkdtemp(prefix="update_")
        new_exe_path = os.path.join(tmp_dir, os.path.basename(download_url))
        print(f"⬇️ Descargando nueva versión desde {download_url}...")
        with requests.get(download_url, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            with open(new_exe_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("✅ Descarga completada.")

        # Ruta actual del ejecutable
        current_exe = sys.executable if getattr(sys, "frozen", False) else "Sistema_Gestion_ADE.exe"

        # Crea un script temporal para reemplazar el exe
        updater_bat = os.path.join(tmp_dir, "updater.bat")
        with open(updater_bat, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
            echo Actualizando...
            timeout /t 1 >nul
            taskkill /F /IM "{os.path.basename(current_exe)}" >nul 2>&1
            timeout /t 1 >nul
            copy /Y "{new_exe_path}" "{current_exe}" >nul
            start "" "{current_exe}"
            """)

        print("🔄 Aplicando actualización...")
        subprocess.Popen(["cmd", "/c", updater_bat], cwd=tmp_dir)
        sys.exit(0)  # Cierra la app para permitir el reemplazo

    except Exception as e:
        print(f"⚠️ Error durante la actualización: {e}")