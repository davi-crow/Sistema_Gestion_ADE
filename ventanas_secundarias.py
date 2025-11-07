import configparser
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox,
    QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QDialog, QTextEdit, QTextBrowser, QScrollBar, QStyledItemDelegate
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QBrush, QTextCursor
from funciones import cargar_cursos
from openai import OpenAI
from datetime import datetime
import mysql.connector
import sys
import json
import threading
import os



class VentanaPagos(QWidget):
    def __init__(self, conexion):
        super().__init__()
        self.conexion = conexion
        self.cursor = conexion.cursor()
        self.setWindowTitle("Gestión de Pagos")
        self.resize(800, 400)
        
        # Layout principal
        self.layout = QVBoxLayout()
        
        # Tabla de pagos
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Nombre", "Debe", "Pagó", "Curso", "Precio normal", "Precio afiliado"
        ])
        self.layout.addWidget(self.tabla)
        
        # Botones
        botones_layout = QHBoxLayout()
        self.btn_editar = QPushButton("Registrar pago a persona seleccionada")
        self.btn_eliminar = QPushButton("Eliminar pago (Historial pagos)")
        
        botones_layout.addWidget(self.btn_editar)
        botones_layout.addWidget(self.btn_eliminar)
        self.layout.addLayout(botones_layout)

        self.btn_editar.clicked.connect(self.abrir_formulario_pago)
        self.btn_eliminar.clicked.connect(self.eliminar_pago)

        self.setLayout(self.layout)
        self.refrescar_tabla()


    def refrescar_tabla(self):
        """Carga en la tabla las personas con sus deudas y pagos."""
        self.cursor.execute("""
            SELECT p.id, p.nombre, p.debe, p.pagado, c.nombre, c.precio_normal, c.precio_afiliado
            FROM personas p
            LEFT JOIN personas_cursos pc ON p.id = pc.persona_id
            LEFT JOIN cursos c ON pc.curso_id = c.id
            WHERE p.debe > 0
            ORDER BY p.id
        """)
        datos = self.cursor.fetchall()
        
        self.tabla.setRowCount(len(datos))
        for fila, row in enumerate(datos):
            for col, valor in enumerate(row):
                self.tabla.setItem(fila, col, QTableWidgetItem(str(valor)))
        self.tabla.resizeColumnsToContents()


    def abrir_formulario_pago(self):
        """Abre una pequeña ventana para registrar un pago."""
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Seleccione una persona para registrar el pago")
            return

        persona_id = int(self.tabla.item(fila, 0).text())
        nombre = self.tabla.item(fila, 1).text()
        debe = float(self.tabla.item(fila, 2).text())

        form = QWidget()
        form.setWindowTitle(f"Registrar pago - {nombre}")
        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel(f"Debe actualmente: ₡{debe:.2f}"))
        form_layout.addWidget(QLabel("Cantidad pagada:"))
        pago_input = QLineEdit()
        pago_input.setPlaceholderText("Ingrese monto pagado")
        form_layout.addWidget(pago_input)

        btn_guardar = QPushButton("Registrar pago")
        form_layout.addWidget(btn_guardar)
        form.setLayout(form_layout)
        form.show()

        def registrar_pago():
            try:
                monto = float(pago_input.text())
            except ValueError:
                QMessageBox.warning(form, "Error", "Ingrese un número válido")
                return
            
            if monto <= 0:
                QMessageBox.warning(form, "Error", "El monto debe ser mayor a 0")
                return
            if monto > debe:
                QMessageBox.warning(form, "Error", "El pago no puede ser mayor a la deuda")
                return

            # Guardar pago en la tabla pagos
            self.cursor.execute("""
                INSERT INTO pagos (persona_id, monto, estado)
                VALUES (%s, %s, 'Pagado')
            """, (persona_id, monto))

            # Actualizar persona
            self.cursor.execute("""
                UPDATE personas
                SET debe = debe - %s,
                    pagado = COALESCE(pagado, 0) + %s
                WHERE id = %s
            """, (monto, monto, persona_id))

            self.conexion.commit()
            self.refrescar_tabla()
            form.close()
            QMessageBox.information(self, "Pago registrado", f"Se registró un pago de ₡{monto:.2f} a {nombre}")

        btn_guardar.clicked.connect(registrar_pago)


    def eliminar_pago(self):
        """Permite eliminar un pago específico de la persona seleccionada."""
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Seleccione una persona para eliminar un pago")
            return

        persona_id = int(self.tabla.item(fila, 0).text())
        nombre = self.tabla.item(fila, 1).text()

        # Obtener los pagos realizados por esa persona
        self.cursor.execute("""
            SELECT id, monto, fecha FROM pagos
            WHERE persona_id = %s
            ORDER BY fecha DESC
        """, (persona_id,))
        pagos = self.cursor.fetchall()

        if not pagos:
            QMessageBox.information(self, "Sin pagos", f"{nombre} no tiene pagos registrados.")
            return

        # Crear ventana para seleccionar pago a eliminar
        ventana = QWidget()
        ventana.setWindowTitle(f"Eliminar pago - {nombre}")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Seleccione el pago a eliminar:"))

        lista_pagos = QComboBox()
        for pid, monto, fecha in pagos:
            lista_pagos.addItem(f"ID {pid} - ₡{monto:.2f} ({fecha})", pid)
        layout.addWidget(lista_pagos)

        btn_borrar = QPushButton("Eliminar pago seleccionado")
        layout.addWidget(btn_borrar)
        ventana.setLayout(layout)
        ventana.show()

        def borrar_pago():
            pago_id = lista_pagos.currentData()
            self.cursor.execute("SELECT monto FROM pagos WHERE id = %s", (pago_id,))
            resultado = self.cursor.fetchone()
            if not resultado:
                QMessageBox.warning(ventana, "Error", "No se encontró el pago.")
                return
            monto = resultado[0]

            # Eliminar el pago y ajustar los totales
            self.cursor.execute("DELETE FROM pagos WHERE id = %s", (pago_id,))
            self.cursor.execute("""
                UPDATE personas
                SET 
                    pagado = GREATEST(pagado - %s, 0),
                    debe = debe + %s
                WHERE id = %s
            """, (monto, monto, persona_id))
            self.conexion.commit()

            self.refrescar_tabla()
            ventana.close()
            QMessageBox.information(self, "Pago eliminado", f"Se eliminó el pago de ₡{monto:.2f} para {nombre}")

        btn_borrar.clicked.connect(borrar_pago)

class VentanaPendientes(QWidget):
    def __init__(self, conexion):
        super().__init__()
        self.conexion = conexion
        self.cursor = self.conexion.cursor()
        self.setWindowTitle("Personas Pendientes")
        self.setGeometry(300, 200, 600, 400)

        layout = QVBoxLayout()

        # Tabla de pendientes
        self.tabla_pendientes = QTableWidget()
        self.tabla_pendientes.setColumnCount(3)
        self.tabla_pendientes.setHorizontalHeaderLabels(["Nombre", "Teléfono", "Estado"])
        self.tabla_pendientes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla_pendientes)

        # Botón para editar persona
        self.btn_editar = QPushButton("Editar persona seleccionada")
        self.btn_editar.clicked.connect(self.abrir_formulario_edicion)
        layout.addWidget(self.btn_editar)

        self.setLayout(layout)

        # Cargar tabla inicialmente
        self.refrescar_tabla()

    # -----------------------------------------------
    def refrescar_tabla(self):
        """Carga la tabla con las personas pendientes"""
        self.cursor.execute("SELECT id, nombre, telefono, estado FROM personas WHERE estado = 'Pendiente'")
        resultados = self.cursor.fetchall()

        self.tabla_pendientes.setRowCount(0)
        for fila, persona in enumerate(resultados):
            self.tabla_pendientes.insertRow(fila)
            for columna, dato in enumerate(persona[1:]):  # Saltar id para mostrar solo columnas visibles
                self.tabla_pendientes.setItem(fila, columna, QTableWidgetItem(str(dato)))

    # -----------------------------------------------
    def abrir_formulario_edicion(self):
        """Abre un formulario para editar datos y estado de la persona seleccionada"""
        fila = self.tabla_pendientes.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Seleccione una persona para editar")
            return

        # Obtener datos de la tabla
        persona_id = self.obtener_id_persona(fila)
        nombre = self.tabla_pendientes.item(fila, 0).text()
        telefono = self.tabla_pendientes.item(fila, 1).text()
        estado_actual = self.tabla_pendientes.item(fila, 2).text()

        # Ventana de edición
        form = QWidget()
        form.setWindowTitle("Editar Persona")
        form_layout = QVBoxLayout()

        # Campos
        nombre_input = QLineEdit(nombre)
        form_layout.addWidget(QLabel("Nombre:"))
        form_layout.addWidget(nombre_input)

        telefono_input = QLineEdit(telefono)
        form_layout.addWidget(QLabel("Teléfono:"))
        form_layout.addWidget(telefono_input)

        estado_combo = QComboBox()
        estado_combo.addItems(["Pendiente", "No localizado", "No aceptó curso", "Activo"])
        estado_combo.setCurrentText(estado_actual)
        form_layout.addWidget(QLabel("Estado:"))
        form_layout.addWidget(estado_combo)

        # Botón guardar
        btn_guardar = QPushButton("Guardar cambios")
        form_layout.addWidget(btn_guardar)
        form.setLayout(form_layout)
        form.show()

        # Función para guardar cambios
        def guardar_cambios():
            nuevo_nombre = nombre_input.text()
            nuevo_telefono = telefono_input.text()
            nuevo_estado = estado_combo.currentText()

            if not nuevo_nombre:
                QMessageBox.warning(form, "Error", "El nombre es obligatorio")
                return

            self.cursor.execute("""
                UPDATE personas
                SET nombre=%s, telefono=%s, estado=%s
                WHERE id=%s
            """, (nuevo_nombre, nuevo_telefono, nuevo_estado, persona_id))
            self.conexion.commit()

            self.refrescar_tabla()
            form.close()
            QMessageBox.information(self, "Actualización", "Persona actualizada correctamente")

        btn_guardar.clicked.connect(guardar_cambios)

    # -----------------------------------------------
    def obtener_id_persona(self, fila):
        """Obtiene el id de la persona desde la base de datos usando el nombre y teléfono visibles"""
        nombre = self.tabla_pendientes.item(fila, 0).text()
        telefono = self.tabla_pendientes.item(fila, 1).text()
        self.cursor.execute("SELECT id FROM personas WHERE nombre=%s AND telefono=%s", (nombre, telefono))
        resultado = self.cursor.fetchone()
        return resultado[0] if resultado else None
    


class ChatGPTApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asistente IA - ParallelDevs")
        self.resize(600, 500)
        self.setStyleSheet("""
            QWidget { background-color: #121212; color: #f0f0f0; }
            QTextBrowser, QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 5px;
            }
            QPushButton {
                background-color: #2d89ef;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #1b66c9; }
            QComboBox {
                background-color: #1e1e1e;
                color: white;
                border-radius: 6px;
                padding: 4px;
            }
        """)

        self.layout = QVBoxLayout(self)

        # Selector de modo
        self.modo_selector = QComboBox()
        self.modo_selector.addItems([
            "Invitaciones a cursos",
            "Mensajes generales",
            "Asistente libre"
        ])
        self.layout.addWidget(self.modo_selector)

        # Área de chat
        self.chat_box = QTextBrowser()
        self.chat_box.setReadOnly(True)
        self.layout.addWidget(self.chat_box)

        # Campo de entrada y botón
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Escribe tu mensaje y presiona Enter...")
        self.input_field.returnPressed.connect(self.enviar_mensaje)

        self.btn_enviar = QPushButton("Enviar")
        self.btn_enviar.clicked.connect(self.enviar_mensaje)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.btn_enviar)
        self.layout.addLayout(input_layout)

        # Inicializa historial
        self.historial = []
        self.historial_file = "historial_chatgpt.json"
        self.cargar_historial()

    def enviar_mensaje(self):
        user_msg = self.input_field.text().strip()
        if not user_msg:
            return

        self.chat_box.append(f"<b>Tú:</b> {user_msg}")
        self.input_field.clear()

        modo = self.modo_selector.currentText()

        if modo == "Invitaciones a cursos":
            system_prompt = "Eres un asistente que redacta invitaciones amables y profesionales para cursos educativos."
        elif modo == "Mensajes generales":
            system_prompt = "Eres un asistente que redacta mensajes y comunicados institucionales con tono profesional."
        else:
            system_prompt = "Eres un asistente útil y conversacional."

        try:
            from openai import OpenAI
            client = OpenAI(api_key="")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ]
            )

            respuesta = response.choices[0].message.content
            self.chat_box.append(f"<b>Asistente:</b> {respuesta}")
            self.chat_box.verticalScrollBar().setValue(
                self.chat_box.verticalScrollBar().maximum()
            )

            self.historial.append({"modo": modo, "usuario": user_msg, "asistente": respuesta})
            self.guardar_historial()

        except Exception as e:
            self.chat_box.append(f"<b style='color:red;'>Error:</b> {str(e)}")

    def guardar_historial(self):
        try:
            with open(self.historial_file, "w", encoding="utf-8") as f:
                json.dump(self.historial, f, ensure_ascii=False, indent=4)
        except:
            pass

    def cargar_historial(self):
        if os.path.exists(self.historial_file):
            with open(self.historial_file, "r", encoding="utf-8") as f:
                self.historial = json.load(f)
            for msg in self.historial[-10:]:
                self.chat_box.append(f"<b>{msg['modo']} - Tú:</b> {msg['usuario']}")
                self.chat_box.append(f"<b>Asistente:</b> {msg['asistente']}")
    def generar_recordatorio(self):
        self.chat_area.append("🧾 Generando recordatorio de pago...\n")

        def tarea():
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Eres un asistente que ayuda con la gestión de pagos."},
                        {"role": "user", "content": "Genera un mensaje amable recordando al cliente que tiene una deuda pendiente."}
                    ]
                )
                mensaje = response.choices[0].message.content
            except Exception as e:
                mensaje = f"⚠️ Error: {e}"

            self.chat_area.append(f"💬 Mensaje sugerido:\n{mensaje}\n")
            self.historial.append(f"💬 Recordatorio generado:\n{mensaje}")
            self.guardar_historial()
            self.scroll_al_final()

        threading.Thread(target=tarea).start()

    # --- Scroll automático ---
    def scroll_al_final(self):
        scrollbar: QScrollBar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())






class ChatGPTApp(QWidget):
    def __init__(self):
        super().__init__()

        # --- Cargar configuración y cliente OpenAI ---
        config = configparser.ConfigParser()
        config.read("config.ini")
        api_key = config["openai"]["api_key"]
        self.client = OpenAI(api_key=api_key)

        # --- Archivo historial ---
        self.historial_path = "historial_chat.json"
        self.historial = self.cargar_historial()

        # --- Configuración de ventana ---
        self.setWindowTitle("💬 Asistente ChatGPT")
        self.setGeometry(400, 200, 700, 500)

        # --- Layout principal ---
        layout = QVBoxLayout()

        # --- Título ---
        titulo = QLabel("🧠 ChatGPT Asistente IA")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ffff;")
        layout.addWidget(titulo)

        # --- Área de chat ---
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        layout.addWidget(self.chat_area)

        # Cargar historial anterior
        for mensaje in self.historial:
            self.chat_area.append(mensaje)

        # --- Campo de entrada + botón ---
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Escribe tu mensaje aquí y presiona Enter...")
        self.input_field.returnPressed.connect(self.enviar_mensaje)

        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.enviar_mensaje)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        self.setLayout(layout)

        # --- Diseño oscuro ---
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI';
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #333;
                border-radius: 10px;
                padding: 8px;
            }
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 6px;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #0078d7;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
        """)

    # -------------------------
    # Cargar y guardar historial
    # -------------------------
    def cargar_historial(self):
        if os.path.exists(self.historial_path):
            with open(self.historial_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def guardar_historial(self):
        with open(self.historial_path, "w", encoding="utf-8") as f:
            json.dump(self.historial, f, ensure_ascii=False, indent=2)

    # -------------------------
    # Enviar mensaje
    # -------------------------
    def enviar_mensaje(self):
        texto = self.input_field.text().strip()
        if not texto:
            return

        self.chat_area.append(f"🧑‍💻 Tú: {texto}")
        self.historial.append(f"🧑‍💻 Tú: {texto}")
        self.input_field.clear()
        self.scroll_abajo()

        # Llamada al modelo en hilo
        hilo = threading.Thread(target=self.obtener_respuesta, args=(texto,))
        hilo.start()

    # -------------------------
    # Obtener respuesta del modelo
    # -------------------------
    def obtener_respuesta(self, texto):
        try:
            respuesta = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un asistente útil y amigable para un sistema de gestión de personas y pagos."},
                    {"role": "user", "content": texto}
                ]
            )

            contenido = respuesta.choices[0].message.content.strip()

        except Exception as e:
            contenido = f"⚠️ Error: {str(e)}"

        # Mostrar respuesta
        self.chat_area.append(f"🤖 ChatGPT: {contenido}\n")
        self.historial.append(f"🤖 ChatGPT: {contenido}\n")
        self.scroll_abajo()
        self.guardar_historial()

    # -------------------------
    # Scroll automático
    # -------------------------
    def scroll_abajo(self):
        self.chat_area.moveCursor(QTextCursor.End)
        self.chat_area.ensureCursorVisible()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = ChatGPTApp()
    ventana.show()
    sys.exit(app.exec())

class CheckNegroDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        check_state = index.data(Qt.CheckStateRole)
        if check_state is not None:
            rect = option.rect
            check_rect = QRect(rect.x() + 5, rect.y() + (rect.height() // 2 - 6), 12, 12)
            painter.save()
            painter.setPen(Qt.black)
            painter.drawRect(check_rect)
            if check_state == Qt.Checked:
                painter.fillRect(check_rect.adjusted(2, 2, -2, -2), QBrush(Qt.black))
            painter.restore()


