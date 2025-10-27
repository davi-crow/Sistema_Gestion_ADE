
import mysql.connector
import sys
import os


def resource_path(relative_path):
    """Devuelve la ruta absoluta del recurso, incluso cuando está empaquetado con PyInstaller."""
    try:
        # PyInstaller crea una carpeta temporal _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ruta_db = resource_path("gestion_de_personas.db")  # si fuera un archivo local

def inicializar_bd():
    # Conectar a MySQL sin base de datos
    conexion = mysql.connector.connect(
        host="192.168.50.119",
        user="david",
        password="holaadios123"
    )
    cursor = conexion.cursor()

    # Crear base de datos
    cursor.execute("CREATE DATABASE IF NOT EXISTS gestion_de_personas")
    cursor.execute("USE gestion_de_personas")


    # Crear tabla cursos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cursos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        precio_normal DECIMAL(10, 2) DEFAULT 0,
        precio_afiliado DECIMAL(10, 2) DEFAULT 0,
        informacion TEXT                  
    )
    """)
    

 
    
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    persona_id INT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    monto DECIMAL(10,2) NOT NULL,
    estado ENUM('Pendiente', 'Pagado') DEFAULT 'Pendiente'
  
    )
    """)        
           
    # Crear tabla personas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        telefono VARCHAR(20),
        correo VARCHAR(100),
        afiliado BOOLEAN DEFAULT FALSE,
        estado ENUM('Pendiente', 'No localizado', 'No aceptó curso', 'Activo') DEFAULT 'Pendiente',
        filial ENUM('San Jose', 'Alajuela', 'Cartago', 'Heredia', 'Guanacaste', 'Puntarenas', 'Limon'),
        fecha_ingreso DATE,
        debe DECIMAL (10, 2) DEFAULT 0,           
        pagado DECIMAL(10, 2) DEFAULT 0,
        debe_original decimal (10,2) DEFAULT 0                       
        
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personas_cursos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        persona_id INT NOT NULL,
        curso_id INT NOT NULL,
        precio DECIMAL(10, 2),
        FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE,
        FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE
    )
    """)
    

    
    # Insertar cursos por defecto si no existen
    cursor.execute("SELECT COUNT(*) FROM cursos")
    if cursor.fetchone()[0] == 0:
        cursos_default = [
            ('SMAW, Soldadura por arco metálico protegido', 85000.0, 70000.0),  
            ('Módulo 2 Réles inteligentes', 80000.0, 68000.0 ),  
            ("MÓDULO 2 CAT-RC", 80000.0, 67500.0),
            ("MÓDULO 3 CAT-RC", 80000.0, 67500.0),
            ("AIRES ACONDICIONADOS", 0.0, 0.0),  # No se especificó precio
            ("Plantas eléctricas y Transferencias automáticas", 85000, 75000),
            ("Módulo 1: Relés inteligentes", 78000.0, 65000.0),
            ("Circuito cerrado de televisión", 78000.0, 65000.0),
            ("Reparación de electrodomésticos módulo 1", 70000.0, 60000.0),
            ("Curso de Alarmas", 78000.0, 60000.0),
            ("Circuito cerrado de televisión (segundo listado)", 78000.0, 65000.0),
            ("Curso de Cámaras de Seguridad", 0.0, 0.0)     
        ]
    
        cursor.executemany("""
            INSERT INTO cursos (nombre, precio_normal, precio_afiliado)
            VALUES (%s, %s, %s)
        """, cursos_default)




    conexion.commit()
    cursor.close()
    conexion.close()

    print("✅ Base de datos 'gestion_de_personas' inicializada correctamente.")

# Ejecutar inicialización

inicializar_bd()