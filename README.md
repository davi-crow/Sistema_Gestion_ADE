# Sistema_Gestion_ADE
Aplicación de escritorio desarrollada en **Python (PySide6)** para la gestión integral de estudiantes, cursos y pagos de la Asociación Nacional de Electricistas ADE.  
Permite registrar, editar y desmatricular personas, administrar cursos, llevar control de deudas, generar respaldos locales y conectar con bases de datos MySQL.

---

## 🚀 Características principales

- 🧍‍♂️ **Gestión de personas:** registrar, editar o eliminar estudiantes fácilmente.  
- 📚 **Control de cursos:** asignar cursos por filial o tipo.  
- 💰 **Pagos y deudas:** seguimiento automático de pagos, montos y saldos pendientes.  
- 🧾 **Respaldo local y en la nube:** respaldo automático de la base de datos.  
- 🎨 **Interfaz moderna:** desarrollada con PySide6 y temas personalizables.  
- 🔒 **Conexión segura:** configuración mediante archivo `config.ini` y variables `.env`.  
- 🌐 **Actualizaciones automáticas:** descarga de nuevas versiones directamente desde GitHub.

---

## 🛠️ Instalación

1. Descarga la última versión desde la pestaña **[Releases](https://github.com/davi-crow/Sistema_Gestion_ADE/releases)**.  
2. Extrae el `.zip` o ejecuta directamente el `.exe` (no requiere instalación).  
3. Asegúrate de tener acceso a tu base de datos MySQL configurada correctamente.  

> ⚙️ Archivos necesarios:
> - `config.ini` → parámetros de conexión (host, usuario, contraseña)
> - `clave.env` → claves o tokens
> - `my.cnf` → configuración MySQL
> - `init.sql` → estructura base de datos
> - `temas/` e `iconos/` → recursos de la interfaz

---

## 💡 Uso básico

1. Ejecuta **`Sistema_Gestion_ADE.exe`**.  
2. Inicia sesión o accede directamente al panel principal.  
3. Utiliza los menús para registrar estudiantes, cursos y pagos.  
4. En el menú **Ayuda → Buscar actualizaciones**, verifica si existe una nueva versión disponible.

---

## 🧰 Requisitos de desarrollo

Si deseas modificar o compilar el proyecto:

```bash
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd Sistema_Gestion_ADE
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Para generar el ejecutable:

pyinstaller --onefile --noconsole --icon "iconos/ade.ico" ^
  --name "Sistema_Gestion_ADE" ^
  --add-data "temas;temas" ^
  --add-data "iconos;iconos" ^
  --add-data "client_secret.json;." ^
  --add-data "Respaldo_Local;Respaldo_Local" ^
  --add-data "init.sql;." ^
  --add-data "config.ini;." ^
  --add-data "my.cnf;." ^
  --add-data "clave.env;." ^
  --hidden-import pandas ^
  --hidden-import pydrive2 ^
  main.py

🔄 Actualizaciones automáticas

El programa puede verificar actualizaciones en GitHub y descargar nuevas versiones.
También puedes hacerlo manualmente desde Releases
.

📦 Estructura del proyecto
Sistema_Gestion_ADE/
├── main.py
├── interfaz.py
├── conexion.py
├── utilidades.py
├── temas/
├── iconos/
├── Respaldo_Local/
├── init.sql
├── config.ini
├── clave.env
├── version.py
└── README.md

🧑‍💻 Tecnologías utilizadas

Python 3.13

PySide6

MySQL Connector

Pandas

PyInstaller

GitHub Actions

📄 Licencia

Este proyecto está licenciado bajo la MIT License.
Puedes usarlo, modificarlo y distribuirlo libremente, siempre que mantengas el aviso de copyright.

© 2025 David Alonso Mora Ureña

☕ Agradecimientos

A la Academia ADE por inspirar el desarrollo del sistema.

A la comunidad Python por las herramientas open-source.


