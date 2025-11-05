import os, sys
from PySide6.QtWidgets import QMessageBox
import tempfile
import subprocess
import requests
import zipfile
import shutil
from importlib import import_module
import configparser
from packaging import version

__version__ = "1.3.2"

RUTA_CONFIG = os.path.join(os.path.dirname(__file__), "config.ini")
 
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
    temas_disponibles = {
        "verde suave": "temas.verde_suave",
        "oscuro": "temas.oscuro",
        "rosa pastel": "temas.rosa_pastel",
        "azul moderno": "temas.azul_moderno",
        "claro": "temas.claro",
    }
    nombre_normalizado = (
            nombre_tema.strip().lower().replace("_", " ").replace("-", " ")
        )

    modulo_tema = temas_disponibles.get(nombre_normalizado, "temas.default")
    obtener_estilo = import_module(modulo_tema).obtener_estilo

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

def verificar_actualizacion_con_dialogo(parent=None):
    """Verifica si hay una nueva versión disponible en GitHub y gestiona la actualización automática."""
    try:
        print("🔍 Buscando actualizaciones...")
        api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"

        # --- Solicitud a GitHub ---
        r = requests.get(api_url, timeout=10)
        if r.status_code == 404:
            print("ℹ️ No hay ninguna release publicada todavía.")
            return
        r.raise_for_status()

        data = r.json()

        # 🧩 Normalizar versiones
        version_remota = data.get("tag_name", "").strip().lower().lstrip("v")
        version_local = __version__.strip().lower().lstrip("v")

        if not version_remota:
            print("⚠️ No se pudo obtener la versión remota desde GitHub.")
            return

        # ✅ Comparar versiones de manera segura
        if version.parse(version_local) >= version.parse(version_remota):
            print(f"✅ La aplicación está actualizada. (Versión {version_local})")
            return

        print(f"⚠️ Nueva versión disponible: {version_remota} (actual: {version_local})")

        # --- Mostrar diálogo al usuario ---
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Actualización disponible")
        msg.setText(f"⚠️ Se ha detectado una nueva versión ({version_remota}).")
        msg.setInformativeText("¿Desea descargar e instalar la actualización ahora?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        respuesta = msg.exec()

        if respuesta != QMessageBox.Yes:
            print("🚫 El usuario canceló la actualización.")
            return

        # --- Buscar el ZIP en los assets del release ---
        assets = data.get("assets", [])
        download_url = None
        for a in assets:
            if a["name"].lower().endswith(".zip"):
                download_url = a["browser_download_url"]
                break

        if not download_url:
            QMessageBox.warning(parent, "Error", "No se encontró el archivo ZIP en la release.")
            return

        # Si el cuerpo del release contiene “disable_updates”, no actualizar
        if "disable_updates" in data.get("body", "").lower():
            print("🚫 Actualizaciones temporalmente desactivadas.")
            return

        # --- Descargar ZIP temporalmente ---
        tmp_dir = tempfile.mkdtemp(prefix="update_")
        zip_path = os.path.join(tmp_dir, "update.zip")
        print(f"⬇️ Descargando nueva versión desde: {download_url}")

        with requests.get(download_url, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

        print("✅ Descarga completada. Descomprimiendo...")

        # --- Extraer archivos ---
        extract_dir = os.path.join(tmp_dir, "extracted")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # --- Determinar directorio de la app actual ---
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.getcwd()

        # --- Reemplazar archivos ---
        for root, dirs, files in os.walk(extract_dir):
            rel_path = os.path.relpath(root, extract_dir)
            dest_path = os.path.join(app_dir, rel_path)
            os.makedirs(dest_path, exist_ok=True)
            for file in files:
                shutil.copy2(os.path.join(root, file), os.path.join(dest_path, file))

        print("🔁 Archivos reemplazados correctamente.")

        # --- Preparar reinicio ---
        exe_path = sys.executable if getattr(sys, "frozen", False) else os.path.join(app_dir, "Sistema_Gestion_ADE.exe")
        updater_bat = os.path.join(tmp_dir, "restart.bat")

        with open(updater_bat, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
title Actualizando...
echo 🔁 Instalando la nueva versión {version_remota}...
timeout /t 1 >nul
start "" "{exe_path}"
exit
""")

        # --- Reiniciar aplicación ---
        subprocess.Popen(["cmd", "/c", updater_bat], cwd=tmp_dir)
        QMessageBox.information(parent, "Actualización completada", f"✅ Se instaló la versión {version_remota}.\nLa aplicación se reiniciará ahora.")
        sys.exit(0)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("ℹ️ No hay releases en GitHub (404 detectado).")
            return
        else:
            QMessageBox.warning(parent, "Error HTTP", f"Error en la solicitud: {e}")
            print(f"⚠️ Error HTTP: {e}")
    except Exception as e:
        QMessageBox.warning(parent, "Error de actualización", f"Ocurrió un error: {e}")
        print(f"⚠️ Error durante la actualización: {e}")

def cargar_config():
    cfg = configparser.ConfigParser()
    if os.path.exists(RUTA_CONFIG):
        cfg.read(RUTA_CONFIG, encoding="utf-8")
    return cfg

def obtener_tema():
    cfg = cargar_config()
    # por defecto “oscuro” si no está definido
    return cfg.get("tema", "actual", fallback="oscuro")

def guardar_tema(nombre_tema: str):
    cfg = cargar_config()
    if "tema" not in cfg:
        cfg["tema"] = {}
    cfg["tema"]["actual"] = nombre_tema
    with open(RUTA_CONFIG, "w", encoding="utf-8") as f:
        cfg.write(f)


