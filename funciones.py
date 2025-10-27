from PySide6.QtWidgets import (
    QMessageBox, QTableWidgetItem, QFileDialog, QDialog, QVBoxLayout,
    QPushButton, QInputDialog, QTableWidget, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QListWidget, QListWidgetItem, QLabel, QCheckBox
)

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QStandardItem, QStandardItemModel
import mysql.connector
import pandas as pd
import csv
import re
import phonenumbers
from utilidades import mostrar_mensaje


# ======================================================
# 📘 CARGA DE DATOS BASE
# ======================================================
def cargar_cursos(conexion):
    cur = conexion.cursor()
    cur.execute("SELECT id, nombre FROM cursos")
    datos = cur.fetchall()
    cur.close()
    return datos


def cargar_filial(conexion):
    cur = conexion.cursor()
    cur.execute("SELECT id, nombre FROM filial")
    datos = cur.fetchall()
    cur.close()
    return datos


# ======================================================
# 🔄 REFRESCAR TABLA DE PERSONAS
# ======================================================
def refrescar_tabla(conexion, tabla, filtros=None):
    if filtros is None:
        filtros = {}

    consulta = """
        SELECT p.id, p.nombre, p.telefono, p.correo,
               COALESCE(GROUP_CONCAT(c.nombre SEPARATOR ', '), '') AS cursos,
               p.afiliado, p.estado, p.filial, p.fecha_ingreso
        FROM personas p
        LEFT JOIN personas_cursos pc ON p.id = pc.persona_id
        LEFT JOIN cursos c ON pc.curso_id = c.id
        WHERE 1=1
    """
    params = []
    if filtros.get("curso"):
        consulta += " AND c.id = %s"
        params.append(filtros["curso"])
    if filtros.get("afiliado") is not None:
        consulta += " AND p.afiliado = %s"
        params.append(filtros["afiliado"])
    if filtros.get("estado") and filtros["estado"] != "Todos":
        consulta += " AND p.estado = %s"
        params.append(filtros["estado"])
    if filtros.get("filial"):
        consulta += " AND p.filial = %s"
        params.append(filtros["filial"])
    if filtros.get("buscar"):
        consulta += " AND (p.nombre LIKE %s OR p.telefono LIKE %s)"
        b = f"%{filtros['buscar']}%"
        params.extend([b, b])

    consulta += " GROUP BY p.id ORDER BY p.id DESC"

    try:
        cur = conexion.cursor()
        tabla.setSortingEnabled(False)
        cur.execute(consulta, params)
        datos = cur.fetchall()
        tabla.setRowCount(len(datos))

        for fila, row in enumerate(datos):
            for col, valor in enumerate(row):
                if col == 5:  # Afiliado
                    valor = "Sí" if valor else "No"
                tabla.setItem(fila, col, QTableWidgetItem(str(valor)))

        tabla.resizeColumnsToContents()
        tabla.setSortingEnabled(True)
    except Exception as e:
        mostrar_mensaje("error", f"Error al refrescar tabla: {e}")
    finally:
        cur.close()


# ======================================================
# 👤 CRUD PERSONAS
# ======================================================
def agregar_persona(conexion, ventana):
    nombre = ventana.nombre_input.text().strip()
    telefono = ventana.telefono_input.text().strip()
    correo = ventana.correo_input.text().strip()
    afiliado_val = 1 if ventana.afiliado_check.isChecked() else 0
    estado_val = ventana.estado_combo.currentText()
    filial_val = ventana.filial_combo.currentText()
    fecha_val = ventana.fecha_ingreso.date().toString("yyyy-MM-dd")

    if not nombre:
        mostrar_mensaje("error", "El nombre es obligatorio", ventana)
        return

    try:
        cur = conexion.cursor()
        cur.execute("""
            INSERT INTO personas (nombre, telefono, correo, afiliado, estado, filial, fecha_ingreso)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nombre, telefono, correo, afiliado_val, estado_val, filial_val, fecha_val))
        persona_id = cur.lastrowid

        total_deuda = 0
        for i in range(ventana.modelo.rowCount()):
            item = ventana.modelo.item(i)
            if item.checkState() == Qt.Checked:
                curso_id = int(item.data(Qt.UserRole))
                cur.execute("SELECT precio_afiliado, precio_normal FROM cursos WHERE id=%s", (curso_id,))
                pa, pn = cur.fetchone()
                precio = pa if afiliado_val else pn
                cur.execute("INSERT INTO personas_cursos (persona_id, curso_id, precio) VALUES (%s, %s, %s)",
                            (persona_id, curso_id, precio))
                total_deuda += precio

        cur.execute("UPDATE personas SET debe=%s WHERE id=%s", (total_deuda, persona_id))
        conexion.commit()
        mostrar_mensaje("info", f"Persona agregada correctamente. Total ₡{total_deuda:,.2f}", ventana)
        refrescar_tabla(conexion, ventana.tabla)
        limpiar_campos(ventana)

    except Exception as e:
        conexion.rollback()
        mostrar_mensaje("error", f"Error al agregar persona: {e}", ventana)
    finally:
        cur.close()


def actualizar_persona(conexion, ventana):
    fila = ventana.tabla.currentRow()
    if fila < 0:
        mostrar_mensaje("error", "Seleccione una persona para editar", ventana)
        return

    persona_id = int(ventana.tabla.item(fila, 0).text())
    nombre = ventana.nombre_input.text().strip()
    telefono = ventana.telefono_input.text().strip()
    correo = ventana.correo_input.text().strip()
    estado_val = ventana.estado_combo.currentData()
    afiliado_val = 1 if ventana.afiliado_check.isChecked() else 0
    estado_val = ventana.estado_combo.currentData()
    filial_val = ventana.filial_combo.currentData()
    fecha_val = ventana.fecha_ingreso.date().toString("yyyy-MM-dd")

    if not nombre:
        mostrar_mensaje("error", "El nombre es obligatorio", ventana)
        return

    try:
        cur = conexion.cursor()
        cur.execute("""
            UPDATE personas
            SET nombre=%s, telefono=%s, correo=%s, afiliado=%s, estado=%s, filial=%s, fecha_ingreso=%s
            WHERE id=%s
        """, (nombre, telefono, correo, afiliado_val, estado_val, filial_val, fecha_val, persona_id))

        cur.execute("DELETE FROM personas_cursos WHERE persona_id=%s", (persona_id,))
        total_deuda = 0
        for i in range(ventana.modelo.rowCount()):
            item = ventana.modelo.item(i)
            if item.checkState() == Qt.Checked:
                curso_id = int(item.data(Qt.UserRole))
                cur.execute("SELECT precio_afiliado, precio_normal FROM cursos WHERE id=%s", (curso_id,))
                pa, pn = cur.fetchone()
                precio = pa if afiliado_val else pn
                cur.execute("INSERT INTO personas_cursos (persona_id, curso_id, precio) VALUES (%s, %s, %s)",
                            (persona_id, curso_id, precio))
                total_deuda += precio

        cur.execute("""
            UPDATE personas
            SET debe_original=%s,
                debe = GREATEST(debe_original - COALESCE((SELECT SUM(monto) FROM pagos WHERE persona_id=%s),0), 0)
            WHERE id=%s
        """, (total_deuda, persona_id, persona_id))
        conexion.commit()
        mostrar_mensaje("info", f"Persona actualizada correctamente. Total ₡{total_deuda:,.2f}", ventana)
        refrescar_tabla(conexion, ventana.tabla)
        limpiar_campos(ventana)
    except Exception as e:
        conexion.rollback()
        mostrar_mensaje("error", f"Error al actualizar persona: {e}", ventana)
    finally:
        cur.close()


def limpiar_campos(ventana):
    ventana.nombre_input.clear()
    ventana.telefono_input.clear()
    ventana.correo_input.clear()
    ventana.afiliado_check.setChecked(False)
    for i in range(ventana.modelo.rowCount()):
        ventana.modelo.item(i).setCheckState(Qt.Unchecked)
    ventana.filial_combo.setCurrentIndex(0)
    ventana.fecha_ingreso.setDate(QDate.currentDate())
    ventana.estado_combo.setCurrentIndex(0)


# ======================================================
# 🗑️ ELIMINAR PERSONA SELECCIONADA
# ======================================================
def eliminar_persona(conexion, ventana):
    """Elimina una sola persona seleccionada de la tabla."""
    fila = ventana.tabla.currentRow()
    if fila < 0:
        mostrar_mensaje("error", "Seleccione una persona para eliminar", ventana)
        return

    persona_id = int(ventana.tabla.item(fila, 0).text())

    confirmar = QMessageBox.question(
        ventana,
        "Confirmar eliminación",
        f"¿Desea eliminar a la persona con ID {persona_id}?",
        QMessageBox.Yes | QMessageBox.No
    )

    if confirmar == QMessageBox.No:
        return

    try:
        cur = conexion.cursor()
        cur.execute("DELETE FROM personas WHERE id = %s", (persona_id,))
        conexion.commit()
        mostrar_mensaje("info", "Persona eliminada correctamente.", ventana)
        refrescar_tabla(conexion, ventana.tabla)
    except Exception as e:
        conexion.rollback()
        mostrar_mensaje("error", f"Error al eliminar persona: {e}", ventana)
    finally:
        cur.close()


# ======================================================
# 🔃 DESMATRICULAR PERSONA (ELIMINA CURSOS Y DEUDA)
# ======================================================
def desmatricular_persona(conexion, ventana):
    """Desmatricula a la persona seleccionada: elimina sus cursos y su deuda."""
    fila = ventana.tabla.currentRow()
    if fila < 0:
        mostrar_mensaje("error", "Seleccione una persona para desmatricular", ventana)
        return

    persona_id = int(ventana.tabla.item(fila, 0).text())
    nombre = ventana.tabla.item(fila, 1).text()

    # Obtener los cursos matriculados de esa persona
    cur = conexion.cursor()
    cur.execute("""
        SELECT c.id, c.nombre, c.precio_normal, c.precio_afiliado, p.afiliado
        FROM personas_cursos pc
        JOIN cursos c ON pc.curso_id = c.id
        JOIN personas p ON p.id = pc.persona_id
        WHERE pc.persona_id = %s
    """, (persona_id,))
    cursos = cur.fetchall()

    if not cursos:
        mostrar_mensaje("info", f"{nombre} no tiene cursos matriculados.", ventana)
        cur.close()
        return
    dialog = QDialog(ventana)
    dialog.setWindowTitle(f"Desmatricular cursos - {nombre}")
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel(f"Seleccione los cursos que desea desmatricular de {nombre}:"))

    checks = []
    for cid, nom, precio_normal, precio_afiliado, afiliado in cursos:
        precio = precio_afiliado if afiliado else precio_normal
        chk = QCheckBox(f"{nom} - ₡{precio:.2f}")
        chk.setProperty("curso_id", cid)
        chk.setProperty("precio", precio)
        layout.addWidget(chk)
        checks.append(chk)

    btn_guardar = QPushButton("Desmatricular seleccionados")
    layout.addWidget(btn_guardar)

    def confirmar_desmatriculacion():
        seleccionados = [chk for chk in checks if chk.isChecked()]
        if not seleccionados:
            QMessageBox.warning(dialog, "Sin selección", "No se seleccionó ningún curso.")
            return

        total_restar = sum(chk.property("precio") for chk in seleccionados)
        ids_cursos = [chk.property("curso_id") for chk in seleccionados]

        # Confirmar acción
        resp = QMessageBox.question(
            dialog,
            "Confirmar desmatriculación",
            f"¿Desea desmatricular {len(ids_cursos)} curso(s) y restar ₡{total_restar:.2f} de la deuda?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.No:
            return

        try:
            # Eliminar solo los cursos seleccionados
            for cid in ids_cursos:
                cur.execute("DELETE FROM personas_cursos WHERE persona_id = %s AND curso_id = %s", (persona_id, cid))

            # Restar la deuda solo por esos cursos
            cur.execute("""
                UPDATE personas
                SET debe = GREATEST(debe - %s, 0)
                WHERE id = %s
            """, (total_restar, persona_id))

            conexion.commit()
            mostrar_mensaje("info", f"Se desmatricularon {len(ids_cursos)} curso(s) y se redujo la deuda en ₡{total_restar:.2f}.", ventana)
            refrescar_tabla(conexion, ventana.tabla)
            dialog.close()

        except Exception as e:
            conexion.rollback()
            mostrar_mensaje("error", f"Error al desmatricular cursos: {e}", ventana)

    btn_guardar.clicked.connect(confirmar_desmatriculacion)
    dialog.exec()
    cur.close()

   

# ======================================================
# 🗑️ ELIMINAR PERSONAS (UNA O VARIAS)
# ======================================================
def eliminar_personas_seleccionadas(conexion, ventana):
    """Elimina una o varias personas seleccionadas de la tabla."""
    seleccion = ventana.tabla.selectionModel().selectedRows()
    if not seleccion:
        mostrar_mensaje("error", "Seleccione al menos una persona para eliminar", ventana)
        return

    confirmacion = QMessageBox.question(
        ventana,
        "Confirmar eliminación",
        f"¿Desea eliminar las {len(seleccion)} personas seleccionadas?",
        QMessageBox.Yes | QMessageBox.No
    )
    if confirmacion == QMessageBox.No:
        return

    try:
        cur = conexion.cursor()
        for index in seleccion:
            fila = index.row()
            persona_id = int(ventana.tabla.item(fila, 0).text())
            cur.execute("DELETE FROM personas WHERE id = %s", (persona_id,))
        conexion.commit()
        mostrar_mensaje("info", f"{len(seleccion)} personas eliminadas correctamente.", ventana)
        refrescar_tabla(conexion, ventana.tabla)
    except Exception as e:
        conexion.rollback()
        mostrar_mensaje("error", f"Error al eliminar personas: {e}", ventana)
    finally:
        cur.close()


# ======================================================
# ✏️ CARGAR PERSONA PARA EDITAR
# ======================================================
def cargar_persona_para_editar(conexion, ventana):
    """Carga los datos de la persona seleccionada en los campos de edición."""
    fila = ventana.tabla.currentRow()
    if fila < 0:
        mostrar_mensaje("error", "Seleccione una persona para editar", ventana)
        return

    persona_id = int(ventana.tabla.item(fila, 0).text())

    # Cargar datos básicos desde la tabla
    ventana.nombre_input.setText(ventana.tabla.item(fila, 1).text())
    ventana.telefono_input.setText(ventana.tabla.item(fila, 2).text())
    ventana.correo_input.setText(ventana.tabla.item(fila, 3).text())
    ventana.afiliado_check.setChecked(ventana.tabla.item(fila, 5).text() == "Sí")
    ventana.filial_combo.setCurrentText(ventana.tabla.item(fila, 6).text())
    ventana.estado_combo.setCurrentText(ventana.tabla.item(fila, 8).text())

    # Cargar cursos asignados desde la BD
    try:
        cur = conexion.cursor()
        cur.execute("""
            SELECT c.nombre
            FROM cursos c
            INNER JOIN personas_cursos pc ON c.id = pc.curso_id
            WHERE pc.persona_id = %s
        """, (persona_id,))
        cursos_asignados = [nombre for (nombre,) in cur.fetchall()]
    except Exception as e:
        mostrar_mensaje("error", f"Error al cargar cursos: {e}", ventana)
        return
    finally:
        cur.close()

    # Marcar cursos seleccionados
    for i in range(ventana.modelo.rowCount()):
        item = ventana.modelo.item(i)
        item.setCheckState(Qt.Checked if item.text() in cursos_asignados else Qt.Unchecked)

    # Guardar ID actual para referencia en actualización
    ventana.persona_editando = persona_id

# ======================================================
# 🗃️ CURSOS
# ======================================================
# ======================================================
# ➕ AGREGAR UN SOLO CURSO
# ======================================================
def agregar_curso(conexion, ventana):
    """Agrega un nuevo curso con sus precios y actualiza la interfaz."""
    nombre_curso, ok = QInputDialog.getText(ventana, "Agregar curso", "Nombre del nuevo curso:")
    if not (ok and nombre_curso.strip()):
        return  # Cancelado o vacío

    try:
        # Pedir precios
        precio_normal, ok_normal = QInputDialog.getDouble(
            ventana,
            "Precio Particular",
            "Ingrese el precio para particulares:",
            80000, 0, 1000000, 0
        )
        if not ok_normal:
            return

        precio_afiliado, ok_afiliado = QInputDialog.getDouble(
            ventana,
            "Precio Socio",
            "Ingrese el precio para afiliados:",
            67500, 0, 1000000, 0
        )
        if not ok_afiliado:
            return

        # Guardar en BD
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO cursos (nombre, precio_normal, precio_afiliado)
            VALUES (%s, %s, %s)
        """, (nombre_curso.strip(), float(precio_normal), float(precio_afiliado)))
        conexion.commit()
        cursor.close()

        mostrar_mensaje("info",
            f"✅ Curso '{nombre_curso}' agregado correctamente.\n"
            f"Normal: ₡{precio_normal:,.2f} | Afiliado: ₡{precio_afiliado:,.2f}",
            ventana
        )

        refrescar_cursos(conexion, ventana)
    except Exception as e:
        mostrar_mensaje("error", f"Error al agregar curso: {e}", ventana)


# ======================================================
# ➕ AGREGAR VARIOS CURSOS DESDE UNA TABLA
# ======================================================
def agregar_varios_cursos_tabla(conexion, ventana):
    """Permite agregar varios cursos de una sola vez desde una tabla editable."""
    dialog = QDialog(ventana)
    dialog.setWindowTitle("Agregar varios cursos")
    dialog.resize(650, 450)
    layout = QVBoxLayout(dialog)

    # Tabla de entrada
    tabla = QTableWidget(5, 3)
    tabla.setHorizontalHeaderLabels(["Nombre del curso", "Precio normal", "Precio afiliado"])
    tabla.horizontalHeader().setStretchLastSection(True)
    layout.addWidget(tabla)

    # Botones
    btn_agregar_fila = QPushButton("Agregar fila")
    btn_guardar = QPushButton("Guardar cursos")
    layout.addWidget(btn_agregar_fila)
    layout.addWidget(btn_guardar)

    # Función para agregar filas dinámicamente
    def agregar_fila():
        tabla.insertRow(tabla.rowCount())

    btn_agregar_fila.clicked.connect(agregar_fila)

    # Función para guardar los cursos
    def guardar_cursos():
        cursos = []
        for fila in range(tabla.rowCount()):
            nombre_item = tabla.item(fila, 0)
            normal_item = tabla.item(fila, 1)
            afiliado_item = tabla.item(fila, 2)

            if nombre_item and nombre_item.text().strip():
                nombre = nombre_item.text().strip()
                try:
                    precio_normal = float(normal_item.text()) if normal_item else 0.0
                    precio_afiliado = float(afiliado_item.text()) if afiliado_item else 0.0
                    cursos.append((nombre, precio_normal, precio_afiliado))
                except ValueError:
                    QMessageBox.warning(dialog, "Error", f"Fila {fila+1}: los precios deben ser números.")
                    return

        if not cursos:
            QMessageBox.warning(dialog, "Error", "No hay cursos válidos para guardar.")
            return

        try:
            cur = conexion.cursor()
            cur.executemany("""
                INSERT INTO cursos (nombre, precio_normal, precio_afiliado)
                VALUES (%s, %s, %s)
            """, cursos)
            conexion.commit()
            cur.close()

            mostrar_mensaje("info", f"✅ Se agregaron {len(cursos)} cursos correctamente.", ventana)
            refrescar_cursos(conexion, ventana)
            dialog.close()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Error al guardar cursos: {e}")

    btn_guardar.clicked.connect(guardar_cursos)
    dialog.exec()

def calcular_total_deuda(curso_combo, conexion, es_afiliado):
    """
    Calcula el total a pagar según los cursos seleccionados
    y si la persona es afiliada o no.
    """
    total = 0.0
    try:
        cur = conexion.cursor()
        for i in range(curso_combo.model().rowCount()):
            item = curso_combo.model().item(i)
            if item.checkState() == Qt.Checked:
                curso_id = item.data(Qt.UserRole)
                cur.execute("SELECT precio_afiliado, precio_normal FROM cursos WHERE id = %s", (curso_id,))
                resultado = cur.fetchone()
                if resultado:
                    precio_afiliado, precio_normal = resultado
                    total += precio_afiliado if es_afiliado else precio_normal
        cur.close()
    except Exception as e:
        print(f"⚠️ Error al calcular deuda: {e}")
    return total
    
# ======================================================
# 🔄 REFRESCAR COMBO DE CURSOS
# ======================================================
def refrescar_cursos(conexion, ventana):
    """Recarga el combo de cursos con los datos más recientes."""
    modelo = QStandardItemModel()
    ventana.curso_combo.setModel(modelo)

    try:
        cur = conexion.cursor()
        cur.execute("SELECT id, nombre FROM cursos ORDER BY nombre ASC")
        for curso_id, nombre in cur.fetchall():
            item = QStandardItem(nombre)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setData(curso_id, Qt.UserRole)
            item.setCheckState(Qt.Unchecked)
            modelo.appendRow(item)
        cur.close()

        modelo.itemChanged.connect(
        lambda: ventana.label_total.setText(
            f"Total a pagar: ₡{calcular_total_deuda(ventana.curso_combo, conexion, ventana.afiliado_check.isChecked()):,.2f}"
        )
    )


    except Exception as e:
        mostrar_mensaje("error", f"Error al refrescar cursos: {e}", ventana)


def eliminar_curso(conexion, ventana):
    cursos = cargar_cursos(conexion)
    if not cursos:
        mostrar_mensaje("error", "No hay cursos disponibles para eliminar.")
        return

    dialog = QDialog(ventana)
    dialog.setWindowTitle("Eliminar cursos")
    dialog.resize(400, 400)
    layout = QVBoxLayout()
    lista = QListWidget()
    for cid, nombre in cursos:
        item = QListWidgetItem(nombre)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked)
        item.setData(Qt.UserRole, cid)
        lista.addItem(item)
    layout.addWidget(lista)
    btn = QPushButton("Eliminar seleccionados")
    layout.addWidget(btn)
    dialog.setLayout(layout)

    def eliminar_seleccion():
        seleccionados = [lista.item(i).data(Qt.UserRole)
                         for i in range(lista.count()) if lista.item(i).checkState() == Qt.Checked]
        if not seleccionados:
            QMessageBox.warning(dialog, "Error", "No seleccionó ningún curso.")
            return
        try:
            cur = conexion.cursor()
            cur.executemany("DELETE FROM cursos WHERE id=%s", [(i,) for i in seleccionados])
            conexion.commit()
            mostrar_mensaje("info", f"{len(seleccionados)} cursos eliminados.")
            refrescar_cursos(conexion, ventana)
            dialog.close()
        except Exception as e:
            conexion.rollback()
            mostrar_mensaje("error", f"Error al eliminar cursos: {e}")

    btn.clicked.connect(eliminar_seleccion)
    dialog.exec()


def refrescar_cursos(conexion, ventana):
    modelo = QStandardItemModel()
    ventana.curso_combo.setModel(modelo)
    cur = conexion.cursor()
    cur.execute("SELECT id, nombre FROM cursos")
    for cid, nombre in cur.fetchall():
        item = QStandardItem(nombre)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setData(cid, Qt.UserRole)
        item.setCheckState(Qt.Unchecked)
        modelo.appendRow(item)
    cur.close()
    ventana.modelo = modelo
# ======================================================
# 📂 IMPORTAR / EXPORTAR DATOS
# ======================================================
def importar_desde_excel(conexion, ventana):
    # Seleccionar archivo
    archivo, _ = QFileDialog.getOpenFileName(
        ventana,
        "Seleccionar archivo Excel",
        "",
        "Excel Files (*.xlsx *.xls)"
    )
    if not archivo:
        return

    try:
        # Leer Excel
        df = pd.read_excel(archivo)
        df = df.rename(columns=lambda x: str(x).strip().lower())

        cur = conexion.cursor()

        # Cargar cursos disponibles (nombre -> id)
        cursos_disponibles = {c[1].lower(): c[0] for c in cargar_cursos(conexion)}

        # Valores válidos de ENUM
        filiales_validas = ['San José', 'Alajuela', 'Cartago', 'Heredia', 'Guanacaste', 'Puntarenas', 'Limón']
        estados_validos = ['Pendiente', 'No localizado', 'No contesta', 'Activo']

        filas_agregadas = 0

        # Recorrer filas del Excel
        for _, fila in df.iterrows():
            # --- Normalizar datos ---
            nombre = str(fila.get('nombre', '')).strip().title()

            # --- Manejo seguro del teléfono ---
            telefono_val = fila.get('telefono', '')
            if pd.notna(telefono_val):  # si no es NaN
                # Si viene como número (float o int), conviértelo sin decimales
                if isinstance(telefono_val, (int, float)):
                    telefono = str(int(telefono_val))
                else:
                    telefono = str(telefono_val).strip()
                # Evita guardar "nan" como texto
                telefono = telefono if telefono.lower() != 'nan' else None
            else:
                telefono = None

            # Correo
            correo = str(fila.get('correo', '')).strip().lower()
            if correo.lower() == 'nan':
                correo = None

            # Afiliado
            afiliado_val = 1 if str(fila.get('afiliado', '')).strip().lower() in ['sí', 'si', '1', 'true'] else 0

            # Estado
            estado_val = str(fila.get('estado', '')).strip().title()
            if estado_val not in estados_validos:
                estado_val = 'Pendiente'

            # Filial
            filial = str(fila.get('filial', '')).strip().title()
            if filial not in filiales_validas:
                filial = None

            # Fecha
            fecha_val = pd.to_datetime(fila.get('fecha_ingreso', ''), errors='coerce')
            fecha_val = fecha_val.strftime('%Y-%m-%d') if pd.notnull(fecha_val) else None

            # Insertar persona
            cur.execute("""
                INSERT INTO personas (nombre, telefono, correo, afiliado, estado, filial, fecha_ingreso)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nombre, telefono, correo, afiliado_val, estado_val, filial, fecha_val))
            persona_id = cur.lastrowid

            # Insertar curso si existe
            curso_nombre = str(fila.get('curso', '')).strip().lower()
            curso_id = cursos_disponibles.get(curso_nombre)
            if curso_id:
                cur.execute("""
                    INSERT INTO personas_cursos (persona_id, curso_id)
                    VALUES (%s, %s)
                """, (persona_id, curso_id))

            filas_agregadas += 1

        conexion.commit()

        # Actualizar tabla en interfaz
        refrescar_tabla(conexion, ventana.tabla)
        QMessageBox.information(
            ventana,
            "Importación exitosa",
            f"✅ Se importaron correctamente {filas_agregadas} registros desde el archivo Excel."
        )

    except Exception as e:
        conexion.rollback()
        QMessageBox.critical(
            ventana,
            "Error al importar",
            f"❌ Ocurrió un error durante la importación:\n\n{str(e)}"
        )


def exportar_csv(ventana):
    filas = ventana.tabla.rowCount()
    cols = ventana.tabla.columnCount()
    if filas == 0:
        mostrar_mensaje("error", "No hay datos para exportar")
        return
    with open("personas_export.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([ventana.tabla.horizontalHeaderItem(i).text() for i in range(cols)])
        for fila in range(filas):
            writer.writerow([ventana.tabla.item(fila, c).text() for c in range(cols)])
    mostrar_mensaje("info", "Datos exportados a personas_export.csv")


def exportar_nombres_txt(conexion):
    try:
        cur = conexion.cursor()
        cur.execute("SELECT nombre FROM personas")
        nombres = cur.fetchall()
        with open("nombres.txt", "w", encoding="utf-8") as f:
            for n in nombres:
                f.write(n[0] + "\n")
        mostrar_mensaje("info", "Nombres exportados a nombres.txt")
    except Exception as e:
        mostrar_mensaje("error", f"Error al exportar TXT: {e}")


def importar_nombres_txt(conexion, ventana):
    ruta, _ = QFileDialog.getOpenFileName(ventana, "Seleccionar archivo TXT", "", "Text Files (*.txt)")
    if not ruta:
        return
    try:
        cur = conexion.cursor()
        with open(ruta, "r", encoding="utf-8") as f:
            for linea in f:
                n = linea.strip()
                if n:
                    cur.execute("INSERT INTO personas (nombre) VALUES (%s)", (n,))
        conexion.commit()
        refrescar_tabla(conexion, ventana.tabla)
        mostrar_mensaje("info", "Nombres importados correctamente")
    except Exception as e:
        mostrar_mensaje("error", f"Error al importar TXT: {e}")



