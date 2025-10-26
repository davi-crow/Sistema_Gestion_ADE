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
