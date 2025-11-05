from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTableWidget,
    QDateEdit, QSizePolicy, QAbstractItemView, QMenu, QDialog, QTextEdit, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, QDate, QSize, QTimer
from PySide6.QtGui import QAction, QIcon, QStandardItemModel, QStandardItem, QColor
from utilidades import verificar_actualizacion_con_dialogo
from funciones import (
    cargar_cursos, refrescar_tabla, agregar_persona, eliminar_persona,
    exportar_csv, actualizar_persona, eliminar_personas_seleccionadas, cargar_persona_para_editar, 
    importar_desde_excel, agregar_curso, eliminar_curso, desmatricular_persona, exportar_nombres_txt, importar_nombres_txt, agregar_varios_cursos_tabla
)
from openai import OpenAI
from ventanas_secundarias import VentanaPagos, VentanaPendientes, CheckNegroDelegate
from utilidades import resource_path, aplicar_tema, mostrar_mensaje, guardar_tema, obtener_tema
import mysql.connector
import os


class VentanaPrincipal(QMainWindow):
    def __init__(self, conexion):
        super().__init__()
        self.conexion = conexion
        self.setWindowTitle("Sistema de Gestión de Clientes")
        self.setGeometry(100, 100, 1100, 600)
        self.setWindowIcon(QIcon(resource_path("iconos/logo.png")))

        central_widget = QWidget()
        self.layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)
        
        

        # Comprobar si hay actualización

        self.crear_menu()
        self.crear_formulario()
        self.crear_filtros()
        self.crear_tabla()
        self.crear_pie()

        try:
            refrescar_tabla(self.conexion, self.tabla)
        except Exception as e:
            mostrar_mensaje("error", f"No se pudo refrescar la tabla: {e}")

    def crear_formulario(self):
        self.form_layout = QHBoxLayout()
        self.form_left = QVBoxLayout()
        self.form_right = QVBoxLayout()

    # --- Fecha de ingreso ---
        self.form_left.addWidget(QLabel("Fecha de ingreso"))
        self.fecha_ingreso = QDateEdit()
        self.fecha_ingreso.setCalendarPopup(True)
        self.fecha_ingreso.setDate(QDate.currentDate())
        self.fecha_ingreso.setFixedWidth(500)
        self.form_left.addWidget(self.fecha_ingreso)

        # --- Nombre ---
        self.form_left.addWidget(QLabel("Nombre"))
        self.nombre_input = QLineEdit()
        self.nombre_input.setFixedWidth(500)
        self.nombre_input.setFixedHeight(30)
        self.form_left.addWidget(self.nombre_input)

        # --- Teléfono ---
        self.form_left.addWidget(QLabel("Teléfono"))
        self.telefono_input = QLineEdit()
        self.telefono_input.setFixedWidth(500)
        self.telefono_input.setFixedHeight(30)
        self.form_left.addWidget(self.telefono_input)

        # --- Correo ---
        self.form_left.addWidget(QLabel("Correo"))
        self.correo_input = QLineEdit()
        self.correo_input.setFixedWidth(500)
        self.correo_input.setFixedHeight(30)
        self.form_left.addWidget(self.correo_input)

            # --- Cursos (con checks) ---
        self.form_left.addWidget(QLabel("Cursos"))

        self.curso_combo = QComboBox()
        self.curso_combo.setFixedWidth(500)
        self.curso_combo.setFixedHeight(30)

        self.modelo = QStandardItemModel()
        self.curso_combo.setModel(self.modelo)
        self.curso_combo.setItemDelegate(CheckNegroDelegate(self.curso_combo))

        # --- Cargar cursos desde la base de datos ---
        cur = self.conexion.cursor()
        cur.execute("SELECT id, nombre FROM cursos")

        for cid, nombre in cur.fetchall():
            item = QStandardItem(nombre)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setData(cid, Qt.UserRole)
            item.setCheckState(Qt.Unchecked)
            item.setForeground(QColor("#003300"))   # Texto verde oscuro
            item.setBackground(QColor("#F6FFFF"))   # Fondo celeste muy suave
            self.modelo.appendRow(item)

        cur.close()

        # --- Actualizar color dinámicamente ---
        def actualizar_color_item():
            for i in range(self.modelo.rowCount()):
                item = self.modelo.item(i)
                if item.checkState() == Qt.Checked:
                    item.setForeground(QColor("#0078D7"))  # Azul Windows
                    item.setBackground(QColor("#E6F0FF"))  # Azul claro
                else:
                    item.setForeground(QColor("#1c1c1c"))  # Texto normal
                    item.setBackground(QColor("#FFFFFF"))  # Fondo blanco

        self.modelo.dataChanged.connect(actualizar_color_item)
        actualizar_color_item()  # Llamada inicial

        self.form_left.addWidget(self.curso_combo)


        # --- Afiliado ---
        self.afiliado_check = QCheckBox("Afiliado")
        self.form_left.addWidget(self.afiliado_check)

        # --- Total dinámico ---
        self.label_total = QLabel("Total a pagar: ₡0.00")
        self.form_left.addWidget(self.label_total)

        def calcular_total_deuda(curso_combo, conexion, es_afiliado):
            c = conexion.cursor()
            total = 0.0
            for i in range(curso_combo.model().rowCount()):
                it = curso_combo.model().item(i)
                if it.checkState() == Qt.Checked:
                    curso_id = it.data(Qt.UserRole)
                    c.execute("SELECT precio_afiliado, precio_normal FROM cursos WHERE id = %s", (curso_id,))
                    pa, pn = c.fetchone()
                    pa = float(pa)
                    pn = float(pn)
                    total += pa if es_afiliado else pn
            c.close()
            return total

        

        def actualizar_total_label():
            total = calcular_total_deuda(self.curso_combo, self.conexion, self.afiliado_check.isChecked())
            self.label_total.setText(f"Total a pagar: ₡{total:,.2f}")


        self.modelo.itemChanged.connect(actualizar_total_label)
        self.afiliado_check.stateChanged.connect(actualizar_total_label)
        actualizar_total_label()


                # --- Filial ---
        self.form_left.addWidget(QLabel("Filial"))

        self.filial_combo = QComboBox()
        self.filial_combo.setFixedWidth(500)
        self.filial_combo.setFixedHeight(30)

        # 💡 Agregar las filiales directamente
        self.filial_combo.addItems([
            "San José",
            "Alajuela",
            "Cartago",
            "Heredia",
            "Guanacaste",
            "Puntarenas",
            "Limón"
        ])

        self.form_left.addWidget(self.filial_combo)



        # --- Estado ---
        self.form_left.addWidget(QLabel("Estado"))
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Pendiente", "No localizado", "No contesta", "Activo"])
        self.form_left.addWidget(self.estado_combo)

                # --- Botón para abrir ventana de pendientes ---
        boton_pendientes = QPushButton("💾Ver pendientes")
        boton_pendientes.setFixedWidth(230)
        boton_pendientes.setIcon(QIcon("iconos/pendientes.png"))
        boton_pendientes.setIconSize(QSize(20, 30))
        boton_pendientes.clicked.connect(self.ventana_pendientes)
        self.form_left.addWidget(boton_pendientes)

        # --- CRUD Personas ---
        btn_agregar = QPushButton("🗂️Agregar")
        btn_agregar.setFixedWidth(230)
        btn_agregar.setIcon(QIcon("iconos/add.png"))
        btn_agregar.setIconSize(QSize(20, 30))
        btn_agregar.clicked.connect(lambda: agregar_persona(self.conexion, self))
        self.form_right.addWidget(btn_agregar, alignment=Qt.AlignmentFlag.AlignHCenter)

        btn_editar = QPushButton("💻Editar")
        btn_editar.setFixedWidth(230)
        btn_editar.setIcon(QIcon("iconos/edit.png"))
        btn_editar.setIconSize(QSize(20, 30))
        btn_editar.clicked.connect(lambda: cargar_persona_para_editar(self.conexion, self))
        self.form_right.addWidget(btn_editar, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_actualizar = QPushButton("📊Actualizar")
        btn_actualizar.setFixedWidth(230)
        btn_actualizar.setIcon(QIcon("iconos/update.png"))
        btn_actualizar.setIconSize(QSize(20, 30))
        btn_actualizar.clicked.connect(lambda: actualizar_persona(self.conexion, self))
        self.form_right.addWidget(btn_actualizar, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_eliminar = QPushButton("🧾Eliminar")
        btn_eliminar.setFixedWidth(230)
        btn_eliminar.setIcon(QIcon("iconos/delete.png"))
        btn_eliminar.setIconSize(QSize(20, 30))
        btn_eliminar.clicked.connect(lambda: eliminar_persona(self.conexion, self))
        self.form_right.addWidget(btn_eliminar, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_eliminar_seleccionados = QPushButton("🔒Eliminar Seleccionados")
        btn_eliminar_seleccionados.setFixedWidth(230)
        btn_eliminar_seleccionados.setIcon(QIcon("iconos/delete2.png"))
        btn_eliminar_seleccionados.setIconSize(QSize(20, 30))
        btn_eliminar_seleccionados.clicked.connect(lambda: eliminar_personas_seleccionadas(self.conexion, self))
        self.form_right.addWidget(btn_eliminar_seleccionados, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Exportar / Importar ---
        btn_exportar = QPushButton("🧠Exportar a CSV")
        btn_exportar.setFixedWidth(230)
        btn_exportar.setIcon(QIcon("iconos/export.png"))
        btn_exportar.setIconSize(QSize(20, 30))
        btn_exportar.clicked.connect(lambda: exportar_csv(self.tabla))
        self.form_right.addWidget(btn_exportar, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_importar = QPushButton("⚙️Importar desde Excel")
        btn_importar.setFixedWidth(230)
        btn_importar.setIcon(QIcon("iconos/import.png"))
        btn_importar.setIconSize(QSize(20, 30))
        self.form_right.addWidget(btn_importar, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_importar.clicked.connect(lambda: importar_desde_excel(self.conexion, self))


        btn_exportar_txt = QPushButton("📁Exportar nombres TXT")
        btn_exportar_txt.setFixedWidth(230)
        btn_exportar_txt.setIcon(QIcon("iconos/exportar.png"))
        btn_exportar_txt.setIconSize(QSize(20, 30))
        btn_exportar_txt.clicked.connect(lambda: exportar_nombres_txt(self.conexion))
        self.form_right.addWidget(btn_exportar_txt, alignment=Qt.AlignmentFlag.AlignCenter)
        

        btn_importar_txt = QPushButton("Importar nombres TXT")
        btn_importar_txt.setFixedWidth(230)
        btn_importar_txt.setIcon(QIcon("iconos/importar.png"))
        btn_importar_txt.setIconSize(QSize(20, 30))
        btn_importar_txt.clicked.connect(lambda: importar_nombres_txt(self.conexion, self))
        self.form_right.addWidget(btn_importar_txt, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Gestión de cursos ---
        boton_agregar_curso = QPushButton("📧Agregar curso")
        boton_agregar_curso.setFixedWidth(230)
        boton_agregar_curso.setIcon(QIcon("iconos/course.png"))
        boton_agregar_curso.setIconSize(QSize(20, 30))
        boton_agregar_curso.clicked.connect(lambda: agregar_curso(self.conexion, self))
        self.form_right.addWidget(boton_agregar_curso, alignment=Qt.AlignmentFlag.AlignCenter)

        boton_agregar_varios = QPushButton("🌐Agregar varios cursos")
        boton_agregar_varios.setFixedWidth(230)
        boton_agregar_varios.setIcon(QIcon("iconos/course.png"))
        boton_agregar_varios.setIconSize(QSize(20, 30))
        boton_agregar_varios.clicked.connect(lambda: agregar_varios_cursos_tabla(self.conexion, self))
        self.form_right.addWidget(boton_agregar_varios, alignment=Qt.AlignmentFlag.AlignCenter)

        boton_eliminar_curso = QPushButton("🧰Eliminar curso")
        boton_eliminar_curso.setFixedWidth(230)
        boton_eliminar_curso.setIcon(QIcon("iconos/eliminar.png"))
        boton_eliminar_curso.setIconSize(QSize(20, 30))
        boton_eliminar_curso.clicked.connect(lambda: eliminar_curso(self.conexion, self))
        self.form_right.addWidget(boton_eliminar_curso, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Desmatricular ---
        btn_desmatricular = QPushButton("📅Desmatricular persona seleccionada")
        btn_desmatricular.setFixedWidth(230)
        btn_desmatricular.setIcon(QIcon("iconos/remove.png"))
        btn_desmatricular.setIconSize(QSize(20, 30))
        btn_desmatricular.clicked.connect(lambda: desmatricular_persona(self.conexion, self))
        self.form_right.addWidget(btn_desmatricular, alignment=Qt.AlignmentFlag.AlignCenter)


        

        # Botón de pendientes (lado izquierdo)


        # Integrar
        self.form_layout.addLayout(self.form_left, 2)
        self.form_layout.addLayout(self.form_right, 1)
        self.layout.addLayout(self.form_layout)

        # Selector de tema
    
            # --- Sección de selección de tema ---
        tema_layout = QHBoxLayout()
        tema_label = QLabel("Tema de la interfaz:")
        tema_combo = QComboBox()
        tema_combo.setFixedHeight(30)
        tema_combo.setFixedWidth(180)

        # Lista de temas visibles (texto) + clave interna (para guardar/aplicar)
        temas = [
            ("Default",       "default"),
            ("Claro",         "claro"),
            ("Oscuro",        "oscuro"),
            ("Rosa pastel",   "rosa_pastel"),
            ("Verde suave",   "verde_suave"),
            ("Azul moderno",  "azul_moderno"),
        ]
        for texto, clave in temas:
            tema_combo.addItem(texto, clave)

        tema_layout.addWidget(tema_label)
        tema_layout.addWidget(tema_combo)
        self.layout.addLayout(tema_layout)

        # --- Aplicar el tema guardado al iniciar ---
        tema_guardado = obtener_tema() or "oscuro"  # usa 'oscuro' si no existe
        idx = tema_combo.findData(tema_guardado)
        if idx != -1:
            tema_combo.setCurrentIndex(idx)

        aplicar_tema(QApplication.instance(), tema_guardado)

        # --- Aplicar y guardar al cambiar ---
        def on_tema_changed(index: int):
            clave = tema_combo.itemData(index)
            app = QApplication.instance()
            aplicar_tema(app, clave)
            guardar_tema(clave)
            print(f"🎨 Tema cambiado y guardado: {clave}")

        tema_combo.currentIndexChanged.connect(on_tema_changed)

      

    # ==================== MENÚ ====================
    def crear_menu(self):
        menubar = self.menuBar()

        menu_gestion = QMenu("➤Gestión", menubar)
        menubar.addMenu(menu_gestion)

        accion_pagos = QAction("✔️​Pagos", menubar)
        accion_pagos.triggered.connect(self.ventana_pagos)
        menu_gestion.addAction(accion_pagos)

        accion_ver_cursos = QAction("​📈​Ver / Editar cursos", menubar)
        accion_ver_cursos.triggered.connect(self.ventana_info_cursos)
        menu_gestion.addAction(accion_ver_cursos)
        
        barra_menu = self.menuBar()

        # Crear menú "Ayuda"
        menu_ayuda = barra_menu.addMenu("Ayuda")

        # Crear acción para verificar actualizaciones
        accion_actualizar = QAction("Buscar actualizaciones", self)
        accion_actualizar.triggered.connect(lambda: verificar_actualizacion_con_dialogo(self))

        # Agregar la acción al menú "Ayuda"
        menu_ayuda.addAction(accion_actualizar)
        
        accion_actualizar = QAction("Buscar actualizaciones", self)
        accion_actualizar.triggered.connect(lambda: verificar_actualizacion_con_dialogo(self))
        menu_ayuda.addAction(accion_actualizar)
        QTimer.singleShot(3000, lambda: verificar_actualizacion_con_dialogo(self))

    # Abrir ventana de pagos
    def ventana_pagos(self):
        try:
            self._vp = VentanaPagos(self.conexion)
            self._vp.show()
        except Exception as e:
            mostrar_mensaje("error", f"No se pudo abrir Pagos: {e}")

    # Abrir ventana de pendientes
    def ventana_pendientes(self):
        try:
            self._vpend = VentanaPendientes(self.conexion)
            self._vpend.show()
        except Exception as e:
            mostrar_mensaje("error", f"No se pudo abrir Pendientes: {e}")

    # Placeholder para “Ver / Editar cursos”
    def ventana_info_cursos(self):
        QMessageBox.information(self, "Cursos", "Aquí puedes abrir tu gestión de cursos.")

    from openai import OpenAI

    def sugerir_mejoras(codigo_usuario):
        client = OpenAI(api_key="sk-proj-XXXX")
        prompt = f"Analiza y mejora este fragmento de Python:\n{codigo_usuario}"
        res = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content


    # ==================== FORMULARIO ====================

    # ==================== FILTROS ====================
    def crear_filtros(self):
        filtro_layout = QHBoxLayout()

        # --- Filtro por curso ---
        self.filtro_curso = QComboBox()
        self.filtro_curso.addItem("Todos", None)
        self.filtro_curso.setMinimumWidth(150)
        self.filtro_curso.setMaximumWidth(250)
        for c in cargar_cursos(self.conexion):
            self.filtro_curso.addItem(c[1], c[0])
        filtro_layout.addWidget(QLabel("Filtrar por curso:"))
        filtro_layout.addWidget(self.filtro_curso)

        # --- Filtro por afiliado ---
        self.filtro_afiliado = QComboBox()
        self.filtro_afiliado.addItem("Todos", None)
        self.filtro_afiliado.addItem("Sí", True)
        self.filtro_afiliado.addItem("No", False)
        filtro_layout.addWidget(QLabel("Afiliado:"))
        filtro_layout.addWidget(self.filtro_afiliado)

        self.filtro_filial = QComboBox()
        self.filtro_filial.addItem("Todas", None)

        # 💡 Lista basada en el ENUM de la base de datos
        filiales = [
            "San José",
            "Alajuela",
            "Cartago",
            "Heredia",
            "Guanacaste",
            "Puntarenas",
            "Limón"
        ]

        for nombre in filiales:
            self.filtro_filial.addItem(nombre, nombre)

        filtro_layout.addWidget(QLabel("Filial:"))
        filtro_layout.addWidget(self.filtro_filial)
        

        # --- Filtro por estado ---
        self.filtro_estado = QComboBox()
        self.filtro_estado.addItem("Todos", None)
        self.filtro_estado.addItems(["Pendiente", "No localizado", "No contesta", "Activo"])
        filtro_layout.addWidget(QLabel("Estado:"))
        filtro_layout.addWidget(self.filtro_estado)



        # --- Campo de búsqueda ---
        filtro_layout.addStretch()
        self.buscar_input = QLineEdit()
        self.buscar_input.setPlaceholderText("🔍 Buscar por nombre o teléfono...")
        filtro_layout.addWidget(self.buscar_input)

        # --- Botón de filtro ---
        btn_filtrar = QPushButton("Aplicar filtro")
        btn_filtrar.clicked.connect(self.aplicar_filtro)
        filtro_layout.addWidget(btn_filtrar)

        self.layout.addLayout(filtro_layout)


    def aplicar_filtro(self):
        curso = self.filtro_curso.currentData()
        txt = self.filtro_afiliado.currentText()
        afiliado = None if txt == "Todos" else (1 if txt == "Sí" else 0)
        afiliado = None if txt == "Todos" else (1 if txt == "Sí" else 0)
        buscar = self.buscar_input.text()
        estado = None if self.filtro_estado.currentText() == "Todos" else self.filtro_estado.currentText()
        filial = self.filtro_filial.currentData()

        refrescar_tabla(
            self.conexion,
            self.tabla,
            filtros={
                "curso": curso,
                "afiliado": afiliado,
                "buscar": buscar,
                "estado": estado,
                "filial": filial
            }
        )
    # ==================== TABLA ====================
    def crear_tabla(self):
        self.tabla = QTableWidget()
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Nombre", "Teléfono", "Correo", "cursos",
            "Afiliado", "Estado", "Filial", "Fecha_ingreso"
        ])

        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabla.setMinimumHeight(200)

        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.layout.addWidget(self.tabla, 1)

        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setItemDelegate(CheckNegroDelegate())

    def agregar_persona_gui(self):
        datos = {
            "nombre": self.nombre_input.text(),
            "telefono": self.telefono_input.text(),
            "correo": self.correo_input.text(),
            "afiliado": self.afiliado_check.isChecked(),
            "estado": self.estado_combo.currentText(),
            "filial": self.filial_combo.currentText(),
            "fecha_ingreso": self.fecha_ingreso.date().toString("yyyy-MM-dd")
        }
        cursos = []
        for i in range(self.modelo.rowCount()):
            item = self.modelo.item(i)
            if item.checkState() == Qt.Checked:
                curso_id = item.data(Qt.UserRole)
                c = self.conexion.cursor()
                c.execute("SELECT precio_afiliado, precio_normal FROM cursos WHERE id=%s", (curso_id,))
                cursos.append(c.fetchone())
                c.close()
        total = agregar_persona(self.conexion, datos, cursos)
        mostrar_mensaje("info", f"Persona agregada con deuda ₡{total:,.2f}")

    def ventana_info_cursos(self): 
            dialog = QDialog(self)
            dialog.setWindowTitle("Información de cursos")
            dialog.resize(700, 500)

            layout = QVBoxLayout(dialog)

            # Crear el árbol
            tree = QTreeWidget()
            tree.setHeaderLabels(["Curso", "Información (editable)"])
            layout.addWidget(tree)

            # Cargar cursos desde la base de datos
            cursor = self.conexion.cursor()
            cursor.execute("SELECT id, nombre, informacion FROM cursos")
            cursos = cursor.fetchall()

            editores = {}  # Para guardar referencias a los QTextEdit

            for curso_id, nombre, info in cursos:
                item_curso = QTreeWidgetItem([nombre])
                tree.addTopLevelItem(item_curso)

                # Cuadro de texto editable
                text_edit = QTextEdit()
                text_edit.setPlaceholderText("Escribe horarios, detalles u observaciones aquí...")
                if info:
                    text_edit.setPlainText(info)
                tree.setItemWidget(item_curso, 1, text_edit)

                # Guardar referencia para acceder al texto después
                editores[curso_id] = text_edit

            # Botón guardar
            btn_guardar = QPushButton("💾 Guardar cambios")
            layout.addWidget(btn_guardar)

            def guardar_cambios():
                try:
                    for curso_id, editor in editores.items():
                        texto = editor.toPlainText().strip()
                        cursor.execute("UPDATE cursos SET informacion = %s WHERE id = %s", (texto, curso_id))
                    self.conexion.commit()
                    QMessageBox.information(dialog, "Éxito", "Información guardada correctamente.")
                except Exception as e:
                    QMessageBox.critical(dialog, "Error", f"No se pudo guardar la información:\n{e}")

            btn_guardar.clicked.connect(guardar_cambios)

            dialog.setLayout(layout)
            dialog.exec()
    
    # ==================== PIE DE PÁGINA ====================
    def crear_pie(self):
        pie = QLabel("ADE – Asociación Nacional de Electricistas")
        pie.setStyleSheet("color: gray; font-size: 9pt; margin-top: 10px;")
        pie.setAlignment(Qt.AlignRight)
        self.layout.addWidget(pie)

