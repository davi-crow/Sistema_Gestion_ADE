import mysql.connector

# Conectar como root
conexion = mysql.connector.connect(
    host="'192.168.100.142' ",  # IP de tu PC
    port=3307,
    user="root",
    password="root123"
)

cursor = conexion.cursor()

# Crear usuario 'david' con permisos desde cualquier host
cursor.execute("CREATE USER IF NOT EXISTS 'david'@'%'192.168.100.142' IDENTIFIED BY 'holaadios123';")
cursor.execute("GRANT ALL PRIVILEGES ON gestion_de_personas.* TO 'david'@'%';")
cursor.execute("FLUSH PRIVILEGES;")

conexion.commit()
cursor.close()
conexion.close()

print("✅ Usuario 'david' autorizado desde cualquier host")
