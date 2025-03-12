import sys
import sqlite3
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QLineEdit, QComboBox, QTextEdit,
    QListWidget, QFormLayout, QInputDialog, QDialog, QDialogButtonBox, QMenuBar, QSpinBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# -----------------------------
# Funciones Auxiliares y Inicialización de la DB
# -----------------------------
def inicializar_db():
    conn = sqlite3.connect("cultivos.db")
    cursor = conn.cursor()
    # Tabla: usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT CHECK(role IN ('admin', 'usuario')),
            email TEXT
        )
    """)
    # Tabla: hectareas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hectareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER,
            tipo_de_cultivo TEXT,
            siembra TEXT,
            primera_cosecha TEXT,
            cosecha_rutinaria TEXT,
            tipo_suelo TEXT,
            temperatura REAL
        )
    """)
    # Tabla: tipo_suelo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipo_suelo (
            codigo INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            descripcion TEXT,
            imagen TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM tipo_suelo")
    if cursor.fetchone()[0] == 0:
        default_suelos = [
            ("Arenoso", "Suelos con alta cantidad de arena.", "arenoso.jpg"),
            ("Limoso", "Suelos con alta proporción de limo.", "limoso.jpg"),
            ("Franco", "Suelos equilibrados.", "franco.jpg"),
            ("Arcilloso", "Suelos con alta cantidad de arcilla.", "arcilloso.jpg")
        ]
        cursor.executemany("INSERT INTO tipo_suelo (nombre, descripcion, imagen) VALUES (?, ?, ?)", default_suelos)
    # Tabla: tipo_hortaliza
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipo_hortaliza (
            codigo INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            descripcion TEXT,
            imagen TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM tipo_hortaliza")
    if cursor.fetchone()[0] == 0:
        default_hortalizas = [
            ("Bulbos", "Vegetales de forma redonda que crecen bajo tierra.", "bulbos.jpg"),
            ("Tallos comestibles", "Vegetales con tallos comestibles.", "tallos.jpg"),
            ("Raíces comestibles", "Vegetales con raíces comestibles.", "raices.jpg"),
            ("Frutos", "Vegetales de tipo fruto.", "frutos.jpg"),
            ("Hojas", "Vegetales donde se consumen las hojas.", "hojas.jpg"),
            ("Flores", "Vegetales en los que se consumen las flores.", "flores.jpg"),
            ("Tubérculos", "Vegetales con tubérculos comestibles.", "tuberculos.jpg")
        ]
        cursor.executemany("INSERT INTO tipo_hortaliza (nombre, descripcion, imagen) VALUES (?, ?, ?)", default_hortalizas)
    # Tabla: clima
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clima (
            codigo INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            grados_temperatura REAL,
            descripcion TEXT,
            imagen TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM clima")
    if cursor.fetchone()[0] == 0:
        default_climas = [
            ("Tropical", 30, "Clima cálido y húmedo.", "tropical.jpg"),
            ("Seco", 25, "Clima árido con poca humedad.", "seco.jpg"),
            ("Templado", 20, "Clima moderado.", "templado.jpg"),
            ("Continental", 15, "Clima con estaciones bien marcadas.", "continental.jpg"),
            ("Polar", 0, "Clima muy frío.", "polar.jpg")
        ]
        cursor.executemany("INSERT INTO clima (nombre, grados_temperatura, descripcion, imagen) VALUES (?, ?, ?, ?)", default_climas)
    # Tabla: gestion_cultivo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gestion_cultivo (
            codigo INTEGER PRIMARY KEY AUTOINCREMENT,
            id_persona INTEGER,
            id_tipo_hortaliza INTEGER,
            id_tipo_suelo INTEGER,
            id_clima INTEGER,
            video TEXT,
            observaciones TEXT,
            FOREIGN KEY(id_persona) REFERENCES usuarios(id),
            FOREIGN KEY(id_tipo_hortaliza) REFERENCES tipo_hortaliza(codigo),
            FOREIGN KEY(id_tipo_suelo) REFERENCES tipo_suelo(codigo),
            FOREIGN KEY(id_clima) REFERENCES clima(codigo)
        )
    """)
    # NUEVA TABLA: tipo_cultivo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipo_cultivo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            meses_primera INTEGER,
            meses_rutinaria INTEGER
        )
    """)
    # Insertar usuario admin por defecto
    cursor.execute("INSERT OR IGNORE INTO usuarios (username, password, role, email) VALUES ('admin', 'admin123', 'admin', NULL)")
    conn.commit()
    conn.close()

def obtener_personas():
    conn = sqlite3.connect("cultivos.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM usuarios")
    personas = cursor.fetchall()
    conn.close()
    return personas

def obtener_tipo_hortaliza():
    conn = sqlite3.connect("cultivos.db")
    cursor = conn.cursor()
    cursor.execute("SELECT codigo, nombre FROM tipo_hortaliza")
    datos = cursor.fetchall()
    conn.close()
    return datos

def obtener_tipo_suelo():
    conn = sqlite3.connect("cultivos.db")
    cursor = conn.cursor()
    cursor.execute("SELECT codigo, nombre FROM tipo_suelo")
    datos = cursor.fetchall()
    conn.close()
    return datos

def obtener_climas():
    conn = sqlite3.connect("cultivos.db")
    cursor = conn.cursor()
    cursor.execute("SELECT codigo, nombre FROM clima")
    datos = cursor.fetchall()
    conn.close()
    return datos

# -----------------------------
# Clase Hectarea
# -----------------------------
class Hectarea:
    def __init__(self, numero, tipo_de_cultivo, siembra, primera_cosecha=None, cosecha_rutinaria=None, tipo_suelo=None, temperatura=None):
        self.numero = numero
        self.tipo_de_cultivo = tipo_de_cultivo.lower()
        self.siembra = datetime.strptime(siembra, "%Y-%m-%d")
        if self.tipo_de_cultivo == "limones":
            self.primeracosecha = self.siembra.replace(year=self.siembra.year + 5)
            self.cosecha_rutinaria = (self.primeracosecha + timedelta(days=180)).strftime("%Y-%m-%d")
        else:
            # Se calcularán automáticamente según los tiempos del cultivo registrado
            if not primera_cosecha:
                if self.tipo_de_cultivo == "maíz":
                    self.primeracosecha = self.siembra + timedelta(days=90)
                elif self.tipo_de_cultivo == "trigo":
                    self.primeracosecha = self.siembra + timedelta(days=120)
                elif self.tipo_de_cultivo == "tomate":
                    self.primeracosecha = self.siembra + timedelta(days=70)
                else:
                    self.primeracosecha = self.siembra + timedelta(days=80)
            else:
                self.primeracosecha = datetime.strptime(primera_cosecha, "%Y-%m-%d")
            if not cosecha_rutinaria:
                if self.tipo_de_cultivo == "maíz":
                    self.cosecha_rutinaria = (self.primeracosecha + timedelta(days=30)).strftime("%Y-%m-%d")
                elif self.tipo_de_cultivo == "trigo":
                    self.cosecha_rutinaria = (self.primeracosecha + timedelta(days=30)).strftime("%Y-%m-%d")
                elif self.tipo_de_cultivo == "tomate":
                    self.cosecha_rutinaria = (self.primeracosecha + timedelta(days=15)).strftime("%Y-%m-%d")
                else:
                    self.cosecha_rutinaria = (self.primeracosecha + timedelta(days=20)).strftime("%Y-%m-%d")
            else:
                self.cosecha_rutinaria = cosecha_rutinaria
        self.tipo_suelo = tipo_suelo
        try:
            self.temperatura = float(temperatura) if temperatura not in (None, "") else None
        except ValueError:
            self.temperatura = None

    def guardar_en_bd(self):
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hectareas (numero, tipo_de_cultivo, siembra, primera_cosecha, cosecha_rutinaria, tipo_suelo, temperatura) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (self.numero, self.tipo_de_cultivo, self.siembra.strftime("%Y-%m-%d"),
              self.primeracosecha.strftime("%Y-%m-%d"), self.cosecha_rutinaria, self.tipo_suelo, self.temperatura))
        conn.commit()
        conn.close()

    @staticmethod
    def eliminar(numero):
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hectareas WHERE numero = ?", (numero,))
        conn.commit()
        conn.close()

    @staticmethod
    def actualizar(numero, tipo, siembra, primera, rutinaria, tipo_suelo, temperatura):
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE hectareas 
            SET tipo_de_cultivo = ?, siembra = ?, primera_cosecha = ?, cosecha_rutinaria = ?, tipo_suelo = ?, temperatura = ?
            WHERE numero = ?
        """, (tipo.lower(), siembra, primera, rutinaria, tipo_suelo, temperatura, numero))
        conn.commit()
        conn.close()

# -----------------------------
# Pantallas de la Aplicación
# -----------------------------

# LoginScreen: Inicio de sesión
class LoginScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Acceso al Sistema de Cultivos")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        subtitle = QLabel("Seleccione un usuario:")
        subtitle.setFont(QFont("Helvetica", 14))
        layout.addWidget(subtitle, alignment=Qt.AlignCenter)
        self.users_list = QListWidget()
        layout.addWidget(self.users_list)
        self.refresh_users()
        btn_recuperar = QPushButton("Recuperar Contraseña")
        btn_recuperar.clicked.connect(self.recuperar_contrasena)
        layout.addWidget(btn_recuperar, alignment=Qt.AlignCenter)
        self.users_list.itemDoubleClicked.connect(self.do_login)
        self.setLayout(layout)
    
    def refresh_users(self):
        self.users_list.clear()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM usuarios")
        users = cursor.fetchall()
        conn.close()
        for u in users:
            self.users_list.addItem(u[0])
    
    def do_login(self, item):
        username = item.text()
        password, ok = QInputDialog.getText(self, "Contraseña",
                                              f"Ingrese la contraseña para {username}:",
                                              QLineEdit.Password)
        if not ok:
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT password, role, email FROM usuarios WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        if result and password == result[0]:
            self.controller.current_user = username
            self.controller.user_role = result[1]
            self.controller.current_email = result[2]
            self.controller.show_screen("main")
        else:
            QMessageBox.critical(self, "Error", "Contraseña incorrecta.")
    
    def recuperar_contrasena(self):
        email, ok = QInputDialog.getText(self, "Recuperar Contraseña", "Ingrese su correo electrónico:")
        if not ok or not email:
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM usuarios WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        if result:
            QMessageBox.information(self, "Recuperación", 
                                    f"Usuario: {result[0]}\nContraseña: {result[1]}\n(Se simula envío de correo)")
        else:
            QMessageBox.critical(self, "Error", "No se encontró un usuario con ese correo.")

# MainScreen: Pantalla principal con menú interno
class MainScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        main_layout = QVBoxLayout(self)
        self.header_label = QLabel("")
        self.header_label.setFont(QFont("Helvetica", 16, QFont.Bold))
        main_layout.addWidget(self.header_label, alignment=Qt.AlignLeft)
        self.email_label = QLabel("")
        main_layout.addWidget(self.email_label, alignment=Qt.AlignLeft)
        menu_layout = QHBoxLayout()
        btn_registrar = QPushButton("Registrar Hectárea")
        btn_registrar.clicked.connect(lambda: controller.show_screen("registrar"))
        menu_layout.addWidget(btn_registrar)
        btn_mostrar = QPushButton("Mostrar Hectáreas")
        btn_mostrar.clicked.connect(self.show_hectareas)
        menu_layout.addWidget(btn_mostrar)
        btn_buscar = QPushButton("Buscar Hectárea")
        btn_buscar.clicked.connect(lambda: controller.show_screen("buscar"))
        menu_layout.addWidget(btn_buscar)
        btn_perfil = QPushButton("Perfil")
        btn_perfil.clicked.connect(lambda: controller.show_screen("perfil"))
        menu_layout.addWidget(btn_perfil)
        btn_informe = QPushButton("Informe Cultivo")
        btn_informe.clicked.connect(lambda: controller.show_screen("informe"))
        menu_layout.addWidget(btn_informe)
        btn_consulta = QPushButton("Consulta Cultivo")
        btn_consulta.clicked.connect(lambda: controller.show_screen("consulta"))
        menu_layout.addWidget(btn_consulta)
        btn_gestion_hectareas = QPushButton("Gestionar Hectáreas")
        btn_gestion_hectareas.clicked.connect(lambda: controller.show_screen("gestionar_hectareas"))
        menu_layout.addWidget(btn_gestion_hectareas)
        btn_gestion_cultivo = QPushButton("Gestión Cultivo")
        btn_gestion_cultivo.clicked.connect(lambda: controller.show_screen("gestion_cultivo"))
        menu_layout.addWidget(btn_gestion_cultivo)
        btn_gestion_usuarios = QPushButton("Gestionar Usuarios")
        btn_gestion_usuarios.clicked.connect(lambda: controller.show_screen("usuarios"))
        menu_layout.addWidget(btn_gestion_usuarios)
        btn_logout = QPushButton("Logout")
        btn_logout.clicked.connect(lambda: controller.show_screen("login"))
        menu_layout.addWidget(btn_logout)
        main_layout.addLayout(menu_layout)
        self.content_area = QTextEdit()
        self.content_area.setReadOnly(True)
        main_layout.addWidget(self.content_area)
        self.setLayout(main_layout)
    
    def update_header(self):
        if self.controller.user_role == "usuario":
            self.header_label.setText(f"Bienvenido {self.controller.current_user}")
            self.email_label.setText(f"({self.controller.current_email})")
        else:
            self.header_label.setText(f"Bienvenido {self.controller.current_user} ({self.controller.user_role})")
            self.email_label.setText("")
    
    def show_hectareas(self):
        self.content_area.clear()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hectareas")
        hectareas = cursor.fetchall()
        conn.close()
        if hectareas:
            texto = ""
            for h in hectareas:
                texto += (f"Hectárea {h[1]}:\n  Tipo: {h[2]}\n  Siembra: {h[3]}\n  1ra Cosecha: {h[4]}\n"
                          f"  Cosecha Rutinaria: {h[5]}\n  Tipo de Suelo: {h[6]}\n  Temperatura: {h[7]}\n\n")
            self.content_area.setPlainText(texto)
        else:
            self.content_area.setPlainText("No hay hectáreas registradas.")

# RegistrarScreen: Registro de Hectáreas (sin campos para fechas de cosecha)
class RegistrarScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Registrar Hectárea")
        title.setFont(QFont("Helvetica", 14, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        form_layout = QFormLayout()
        # Se usan QComboBox para seleccionar cultivo y suelo (se actualizarán dinámicamente)
        self.combo_crop = QComboBox()
        form_layout.addRow("Tipo de Cultivo:", self.combo_crop)
        self.entry_siembra = QLineEdit()
        form_layout.addRow("Fecha de Siembra (YYYY-MM-DD):", self.entry_siembra)
        self.combo_suelo = QComboBox()
        form_layout.addRow("Tipo de Suelo:", self.combo_suelo)
        self.entry_temp = QLineEdit()
        form_layout.addRow("Temperatura (°C):", self.entry_temp)
        layout.addLayout(form_layout)
        btn_registrar = QPushButton("Registrar")
        btn_registrar.clicked.connect(self.registrar_hectarea)
        layout.addWidget(btn_registrar, alignment=Qt.AlignCenter)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_opciones()
    
    def cargar_opciones(self):
        # Consultar la tabla tipo_cultivo para los cultivos
        self.combo_crop.clear()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM tipo_cultivo")
        rows = cursor.fetchall()
        conn.close()
        crop_types = [r[0] for r in rows] if rows else ["limones", "maíz", "trigo", "tomate"]
        self.combo_crop.addItems(crop_types)
        # Consultar la tabla tipo_suelo para los suelos
        self.combo_suelo.clear()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM tipo_suelo")
        suelos = cursor.fetchall()
        conn.close()
        suelo_types = [s[0] for s in suelos] if suelos else ["Sin suelo registrado"]
        self.combo_suelo.addItems(suelo_types)
    
    def registrar_hectarea(self):
        siembra = self.entry_siembra.text().strip()
        crop = self.combo_crop.currentText()
        if not siembra:
            QMessageBox.critical(self, "Error", "Ingrese la fecha de siembra.")
            return
        # Se pasan None para primera cosecha y cosecha rutinaria, para que se calculen automáticamente
        suelo = self.combo_suelo.currentText()
        temperatura = self.entry_temp.text().strip()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(numero) FROM hectareas")
        max_num = cursor.fetchone()[0]
        conn.close()
        numero = 1 if max_num is None else max_num + 1
        try:
            hectarea = Hectarea(numero, crop, siembra, None, None, suelo, temperatura)
            hectarea.guardar_en_bd()
            QMessageBox.information(self, "Registro", "Hectárea registrada con éxito.")
            self.controller.show_screen("main")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

# BuscarScreen: Búsqueda de Hectáreas
class BuscarScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Buscar Hectárea")
        title.setFont(QFont("Helvetica", 14, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        self.entry_numero = QLineEdit()
        self.entry_numero.setPlaceholderText("Número de Hectárea")
        layout.addWidget(self.entry_numero)
        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(self.buscar_hectarea)
        layout.addWidget(btn_buscar, alignment=Qt.AlignCenter)
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)
    
    def buscar_hectarea(self):
        num_text = self.entry_numero.text().strip()
        if not num_text.isdigit():
            self.result_area.setPlainText("Ingrese un número válido.")
            return
        num = int(num_text)
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hectareas WHERE numero = ?", (num,))
        hectarea = cursor.fetchone()
        conn.close()
        self.result_area.clear()
        if hectarea:
            texto = (f"Hectárea {hectarea[1]}:\n  Tipo: {hectarea[2]}\n  Siembra: {hectarea[3]}\n"
                     f"  1ra Cosecha: {hectarea[4]}\n  Cosecha Rutinaria: {hectarea[5]}\n"
                     f"  Tipo de Suelo: {hectarea[6]}\n  Temperatura: {hectarea[7]}")
            self.result_area.setPlainText(texto)
        else:
            self.result_area.setPlainText(f"No se encontró la Hectárea {num}.")

# PerfilScreen: Perfil de Usuario
class PerfilScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Perfil de Usuario")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        self.info_label = QLabel("")
        self.info_label.setFont(QFont("Helvetica", 14))
        layout.addWidget(self.info_label, alignment=Qt.AlignCenter)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)
    
    def cargar_perfil(self):
        user = self.controller.current_user
        email = self.controller.current_email
        role = self.controller.user_role
        self.info_label.setText(f"Usuario: {user}\nEmail: {email}\nRol: {role}")

# InformeScreen: Informe de Gestión de Cultivo
class InformeScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Informe de Gestión Cultivo")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        self.informe_area = QTextEdit()
        self.informe_area.setReadOnly(True)
        layout.addWidget(self.informe_area)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)
    
    def cargar_informe(self):
        self.informe_area.clear()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT gc.codigo, u.username, th.nombre, ts.nombre, c.nombre, gc.video, gc.observaciones
            FROM gestion_cultivo gc
            JOIN usuarios u ON gc.id_persona = u.id
            JOIN tipo_hortaliza th ON gc.id_tipo_hortaliza = th.codigo
            JOIN tipo_suelo ts ON gc.id_tipo_suelo = ts.codigo
            JOIN clima c ON gc.id_clima = c.codigo
        """)
        registros = cursor.fetchall()
        conn.close()
        if registros:
            texto = ""
            for r in registros:
                texto += (f"Código: {r[0]}\nUsuario: {r[1]}\nTipo Hortaliza: {r[2]}\n"
                          f"Tipo Suelo: {r[3]}\nClima: {r[4]}\nVideo: {r[5]}\nObservaciones: {r[6]}\n"
                          + "-" * 40 + "\n")
            self.informe_area.setPlainText(texto)
        else:
            self.informe_area.setPlainText("No hay registros de gestión cultivo.")

# ConsultaScreen: Consulta de Tipos de Cultivo (Hortalizas)
class ConsultaScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Consulta Tipo de Cultivo (Hortaliza)")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        self.entry_consulta = QLineEdit()
        self.entry_consulta.setPlaceholderText("Ingrese el nombre del tipo de hortaliza")
        layout.addWidget(self.entry_consulta)
        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(self.buscar_tipo)
        layout.addWidget(btn_buscar, alignment=Qt.AlignCenter)
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)
    
    def buscar_tipo(self):
        nombre = self.entry_consulta.text().strip()
        if not nombre:
            QMessageBox.critical(self, "Error", "Ingrese un nombre para consultar.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, nombre, descripcion, imagen FROM tipo_hortaliza WHERE nombre LIKE ?", ('%' + nombre + '%',))
        registros = cursor.fetchall()
        conn.close()
        self.result_area.clear()
        if registros:
            texto = ""
            for r in registros:
                texto += (f"Código: {r[0]}\nNombre: {r[1]}\nDescripción: {r[2]}\nImagen: {r[3]}\n"
                          + "-" * 30 + "\n")
            self.result_area.setPlainText(texto)
        else:
            self.result_area.setPlainText("No se encontró el tipo de cultivo.")

# GestionarHectareasScreen: Gestión de Hectáreas (Admin)
class GestionarHectareasScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Gestionar Hectáreas")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        self.hectareas_list = QListWidget()
        layout.addWidget(self.hectareas_list)
        self.refresh_hectareas()
        btn_editar = QPushButton("Editar Seleccionada")
        btn_editar.clicked.connect(self.edit_hectarea)
        layout.addWidget(btn_editar, alignment=Qt.AlignCenter)
        btn_eliminar = QPushButton("Eliminar Seleccionada")
        btn_eliminar.clicked.connect(self.delete_hectarea)
        layout.addWidget(btn_eliminar, alignment=Qt.AlignCenter)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)
    
    def refresh_hectareas(self):
        self.hectareas_list.clear()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT numero, tipo_de_cultivo, siembra, primera_cosecha, cosecha_rutinaria, tipo_suelo, temperatura FROM hectareas")
        hectareas = cursor.fetchall()
        conn.close()
        for h in hectareas:
            self.hectareas_list.addItem(
                f"N° {h[0]}: {h[1]} | Siembra: {h[2]} | 1ra: {h[3]} | Rutinaria: {h[4]} | Suelo: {h[5]} | Temp: {h[6]}"
            )
    
    def delete_hectarea(self):
        selected = self.hectareas_list.currentItem()
        if not selected:
            QMessageBox.critical(self, "Error", "Seleccione una hectárea para eliminar.")
            return
        line = selected.text()
        numero = int(line.split(":")[0].replace("N°", "").strip())
        if QMessageBox.question(self, "Confirmar", f"¿Está seguro de eliminar la hectárea {numero}?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            Hectarea.eliminar(numero)
            QMessageBox.information(self, "Éxito", "Hectárea eliminada.")
            self.refresh_hectareas()
    
    def edit_hectarea(self):
        selected = self.hectareas_list.currentItem()
        if not selected:
            QMessageBox.critical(self, "Error", "Seleccione una hectárea para editar.")
            return
        line = selected.text()
        numero = int(line.split(":")[0].replace("N°", "").strip())
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tipo_de_cultivo, siembra, primera_cosecha, cosecha_rutinaria, tipo_suelo, temperatura 
            FROM hectareas WHERE numero = ?
        """, (numero,))
        data = cursor.fetchone()
        conn.close()
        if not data:
            QMessageBox.critical(self, "Error", "No se encontraron datos para la hectárea seleccionada.")
            return
        new_tipo, ok1 = QInputDialog.getText(self, "Editar", "Nuevo tipo de cultivo:", text=data[0])
        new_siembra, ok2 = QInputDialog.getText(self, "Editar", "Nueva fecha de siembra (YYYY-MM-DD):", text=data[1])
        new_primera, ok3 = QInputDialog.getText(self, "Editar", "Nueva fecha de primera cosecha (YYYY-MM-DD):", text=data[2])
        new_rutinaria, ok4 = QInputDialog.getText(self, "Editar", "Nueva cosecha rutinaria:", text=data[3])
        new_suelo, ok5 = QInputDialog.getText(self, "Editar", "Nuevo tipo de suelo:", text=data[4])
        new_temp, ok6 = QInputDialog.getText(self, "Editar", "Nueva temperatura (°C):", text=str(data[5]) if data[5] is not None else "")
        if not (ok1 and ok2 and ok3 and ok4 and ok5):
            QMessageBox.critical(self, "Error", "Edición cancelada o campos incompletos.")
            return
        try:
            Hectarea.actualizar(numero, new_tipo, new_siembra, new_primera, new_rutinaria, new_suelo, new_temp)
            QMessageBox.information(self, "Éxito", "Hectárea actualizada.")
            self.refresh_hectareas()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

# GestionCultivoScreen: Gestión de Cultivos (Admin)
class GestionCultivoScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Gestión Cultivo")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        btn_registrar = QPushButton("Registrar Gestión Cultivo")
        btn_registrar.clicked.connect(self.registrar_gestion)
        layout.addWidget(btn_registrar, alignment=Qt.AlignCenter)
        self.gestion_list = QListWidget()
        layout.addWidget(self.gestion_list)
        self.cargar_gestiones()
        btn_editar = QPushButton("Editar Seleccionada")
        btn_editar.clicked.connect(self.editar_gestion)
        layout.addWidget(btn_editar, alignment=Qt.AlignCenter)
        btn_eliminar = QPushButton("Eliminar Seleccionada")
        btn_eliminar.clicked.connect(self.eliminar_gestion)
        layout.addWidget(btn_eliminar, alignment=Qt.AlignCenter)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)
    
    def cargar_gestiones(self):
        self.gestion_list.clear()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, id_persona, id_tipo_hortaliza, id_tipo_suelo, id_clima, video, observaciones FROM gestion_cultivo")
        gestiones = cursor.fetchall()
        conn.close()
        for g in gestiones:
            self.gestion_list.addItem(
                f"Código: {g[0]} | Persona ID: {g[1]} | Hortaliza ID: {g[2]} | Suelo ID: {g[3]} | Clima ID: {g[4]} | Video: {g[5]} | Obs: {g[6]}"
            )
    
    def registrar_gestion(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Registrar Gestión Cultivo")
        d_layout = QFormLayout(dialog)
        personas = obtener_personas()
        if not personas:
            QMessageBox.critical(dialog, "Error", "No hay usuarios registrados.")
            return
        personas_dict = {f"{p[0]}: {p[1]}": p[0] for p in personas}
        combo_persona = QComboBox()
        combo_persona.addItems(list(personas_dict.keys()))
        d_layout.addRow("Seleccione Persona:", combo_persona)
        hort_data = obtener_tipo_hortaliza()
        if not hort_data:
            QMessageBox.critical(dialog, "Error", "No hay tipos de hortaliza registrados.")
            return
        hort_dict = {f"{h[0]}: {h[1]}": h[0] for h in hort_data}
        combo_hortaliza = QComboBox()
        combo_hortaliza.addItems(list(hort_dict.keys()))
        d_layout.addRow("Seleccione Tipo de Hortaliza:", combo_hortaliza)
        suelo_data = obtener_tipo_suelo()
        if not suelo_data:
            QMessageBox.critical(dialog, "Error", "No hay tipos de suelo registrados.")
            return
        suelo_dict = {f"{s[0]}: {s[1]}": s[0] for s in suelo_data}
        combo_suelo = QComboBox()
        combo_suelo.addItems(list(suelo_dict.keys()))
        d_layout.addRow("Seleccione Tipo de Suelo:", combo_suelo)
        clima_data = obtener_climas()
        if not clima_data:
            QMessageBox.critical(dialog, "Error", "No hay climas registrados.")
            return
        clima_dict = {f"{c[0]}: {c[1]}": c[0] for c in clima_data}
        combo_clima = QComboBox()
        combo_clima.addItems(list(clima_dict.keys()))
        d_layout.addRow("Seleccione Clima:", combo_clima)
        entry_video = QLineEdit()
        d_layout.addRow("Video (URL o ruta):", entry_video)
        entry_obs = QLineEdit()
        d_layout.addRow("Observaciones:", entry_obs)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        d_layout.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec_() == QDialog.Accepted:
            try:
                id_persona = personas_dict[combo_persona.currentText()]
                id_hortaliza = hort_dict[combo_hortaliza.currentText()]
                id_suelo = suelo_dict[combo_suelo.currentText()]
                id_clima = clima_dict[combo_clima.currentText()]
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al obtener valores: {e}")
                return
            video = entry_video.text().strip()
            observaciones = entry_obs.text().strip()
            conn = sqlite3.connect("cultivos.db")
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO gestion_cultivo (id_persona, id_tipo_hortaliza, id_tipo_suelo, id_clima, video, observaciones)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (id_persona, id_hortaliza, id_suelo, id_clima, video, observaciones))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Gestión cultivo registrada.")
            self.cargar_gestiones()
    
    def editar_gestion(self):
        selected = self.gestion_list.currentItem()
        if not selected:
            QMessageBox.critical(self, "Error", "Seleccione una gestión para editar.")
            return
        line = selected.text()
        codigo = int(line.split("|")[0].split(":")[1].strip())
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_persona, id_tipo_hortaliza, id_tipo_suelo, id_clima, video, observaciones 
            FROM gestion_cultivo WHERE codigo = ?
        """, (codigo,))
        data = cursor.fetchone()
        conn.close()
        if not data:
            QMessageBox.critical(self, "Error", "No se encontró la gestión seleccionada.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Gestión Cultivo")
        d_layout = QFormLayout(dialog)
        personas = obtener_personas()
        personas_dict = {f"{p[0]}: {p[1]}": p[0] for p in personas}
        combo_persona = QComboBox()
        combo_persona.addItems(list(personas_dict.keys()))
        for key, value in personas_dict.items():
            if value == data[0]:
                index = combo_persona.findText(key)
                combo_persona.setCurrentIndex(index)
                break
        d_layout.addRow("Seleccione Persona:", combo_persona)
        hort_data = obtener_tipo_hortaliza()
        hort_dict = {f"{h[0]}: {h[1]}": h[0] for h in hort_data}
        combo_hortaliza = QComboBox()
        combo_hortaliza.addItems(list(hort_dict.keys()))
        for key, value in hort_dict.items():
            if value == data[1]:
                index = combo_hortaliza.findText(key)
                combo_hortaliza.setCurrentIndex(index)
                break
        d_layout.addRow("Seleccione Tipo de Hortaliza:", combo_hortaliza)
        suelo_data = obtener_tipo_suelo()
        suelo_dict = {f"{s[0]}: {s[1]}": s[0] for s in suelo_data}
        combo_suelo = QComboBox()
        combo_suelo.addItems(list(suelo_dict.keys()))
        for key, value in suelo_dict.items():
            if value == data[2]:
                index = combo_suelo.findText(key)
                combo_suelo.setCurrentIndex(index)
                break
        d_layout.addRow("Seleccione Tipo de Suelo:", combo_suelo)
        clima_data = obtener_climas()
        clima_dict = {f"{c[0]}: {c[1]}": c[0] for c in clima_data}
        combo_clima = QComboBox()
        combo_clima.addItems(list(clima_dict.keys()))
        for key, value in clima_dict.items():
            if value == data[3]:
                index = combo_clima.findText(key)
                combo_clima.setCurrentIndex(index)
                break
        d_layout.addRow("Seleccione Clima:", combo_clima)
        entry_video = QLineEdit()
        entry_video.setText(data[4])
        d_layout.addRow("Video (URL o ruta):", entry_video)
        entry_obs = QLineEdit()
        entry_obs.setText(data[5])
        d_layout.addRow("Observaciones:", entry_obs)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        d_layout.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec_() == QDialog.Accepted:
            try:
                id_persona = personas_dict[combo_persona.currentText()]
                id_hortaliza = hort_dict[combo_hortaliza.currentText()]
                id_suelo = suelo_dict[combo_suelo.currentText()]
                id_clima = clima_dict[combo_clima.currentText()]
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al obtener valores: {e}")
                return
            video = entry_video.text().strip()
            observaciones = entry_obs.text().strip()
            conn = sqlite3.connect("cultivos.db")
            cur = conn.cursor()
            cur.execute("""
                UPDATE gestion_cultivo
                SET id_persona = ?, id_tipo_hortaliza = ?, id_tipo_suelo = ?, id_clima = ?, video = ?, observaciones = ?
                WHERE codigo = ?
            """, (id_persona, id_hortaliza, id_suelo, id_clima, video, observaciones, codigo))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Gestión cultivo actualizada.")
            self.cargar_gestiones()
    
    def eliminar_gestión(self):
        # Este método no se usa; se conecta el botón a eliminar_gestion
        pass

    def eliminar_gestion(self):
        selected = self.gestion_list.currentItem()
        if not selected:
            QMessageBox.critical(self, "Error", "Seleccione una gestión para eliminar.")
            return
        line = selected.text()
        try:
            codigo = int(line.split("|")[0].split(":")[1].strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al obtener el código: {e}")
            return
        if QMessageBox.question(self, "Confirmar",
                                f"¿Está seguro de eliminar la gestión con código {codigo}?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            conn = sqlite3.connect("cultivos.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gestion_cultivo WHERE codigo = ?", (codigo,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Gestión cultivo eliminada.")
            self.cargar_gestiones()

# CultivosScreen: Pantalla para mostrar datos de ejemplo (sin CRUD)
class CultivosScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        label = QLabel("Pantalla: Cultivos (Ejemplo)")
        label.setFont(QFont("Helvetica", 16, QFont.Bold))
        layout.addWidget(label, alignment=Qt.AlignCenter)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText("Aquí se mostrarían cultivos en general (ej. maíz, trigo, tomate, etc.)\nEste ejemplo no tiene ABM.")
        layout.addWidget(text)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)

# TipoHortalizaManagementScreen: ABM para tipo_hortaliza
class TipoHortalizaManagementScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Gestionar Tipos de Hortaliza")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        self.list_hortalizas = QListWidget()
        layout.addWidget(self.list_hortalizas)
        form_layout = QFormLayout()
        self.input_nombre = QLineEdit()
        self.input_descripcion = QLineEdit()
        self.input_imagen = QLineEdit()
        form_layout.addRow("Nombre:", self.input_nombre)
        form_layout.addRow("Descripción:", self.input_descripcion)
        form_layout.addRow("Imagen (ruta/URL):", self.input_imagen)
        layout.addLayout(form_layout)
        btn_crear = QPushButton("Crear/Actualizar")
        btn_crear.clicked.connect(self.crear_actualizar_hortaliza)
        layout.addWidget(btn_crear, alignment=Qt.AlignCenter)
        btn_eliminar = QPushButton("Eliminar Seleccionada")
        btn_eliminar.clicked.connect(self.eliminar_hortaliza)
        layout.addWidget(btn_eliminar, alignment=Qt.AlignCenter)
        btn_limpiar = QPushButton("Limpiar Campos")
        btn_limpiar.clicked.connect(self.limpiar_campos)
        layout.addWidget(btn_limpiar, alignment=Qt.AlignCenter)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        self.cargar_hortalizas()
        self.list_hortalizas.itemClicked.connect(self.cargar_en_formulario)
    
    def cargar_hortalizas(self):
        self.list_hortalizas.clear()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, nombre, descripcion, imagen FROM tipo_hortaliza")
        rows = cursor.fetchall()
        conn.close()
        for r in rows:
            self.list_hortalizas.addItem(f"{r[0]} | {r[1]} | {r[2]} | {r[3]}")
    
    def crear_actualizar_hortaliza(self):
        nombre = self.input_nombre.text().strip()
        descripcion = self.input_descripcion.text().strip()
        imagen = self.input_imagen.text().strip()
        if not nombre:
            QMessageBox.critical(self, "Error", "El nombre es obligatorio.")
            return
        selected = self.list_hortalizas.currentItem()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        if selected:
            codigo = selected.text().split("|")[0].strip()
            try:
                cursor.execute("""
                    UPDATE tipo_hortaliza
                    SET nombre = ?, descripcion = ?, imagen = ?
                    WHERE codigo = ?
                """, (nombre, descripcion, imagen, codigo))
                conn.commit()
                QMessageBox.information(self, "Éxito", "Tipo de hortaliza actualizado.")
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Error", "Ya existe una hortaliza con ese nombre.")
        else:
            try:
                cursor.execute("""
                    INSERT INTO tipo_hortaliza (nombre, descripcion, imagen)
                    VALUES (?, ?, ?)
                """, (nombre, descripcion, imagen))
                conn.commit()
                QMessageBox.information(self, "Éxito", "Nuevo tipo de hortaliza creado.")
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Error", "Ya existe una hortaliza con ese nombre.")
        conn.close()
        self.cargar_hortalizas()
        self.limpiar_campos()
    
    def eliminar_hortaliza(self):
        selected = self.list_hortalizas.currentItem()
        if not selected:
            QMessageBox.critical(self, "Error", "Seleccione un tipo de hortaliza para eliminar.")
            return
        codigo = selected.text().split("|")[0].strip()
        if QMessageBox.question(self, "Confirmar", f"¿Desea eliminar el código {codigo}?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            conn = sqlite3.connect("cultivos.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tipo_hortaliza WHERE codigo = ?", (codigo,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Hortaliza eliminada.")
            self.cargar_hortalizas()
            self.limpiar_campos()
    
    def cargar_en_formulario(self, item):
        line = item.text().split("|")
        nombre = line[1].strip()
        descripcion = line[2].strip()
        imagen = line[3].strip()
        self.input_nombre.setText(nombre)
        self.input_descripcion.setText(descripcion)
        self.input_imagen.setText(imagen)
    
    def limpiar_campos(self):
        self.input_nombre.clear()
        self.input_descripcion.clear()
        self.input_imagen.clear()
        self.list_hortalizas.clearSelection()

# TipoSueloManagementScreen: ABM para tipo_suelo
class TipoSueloManagementScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Gestionar Tipos de Suelo")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        self.list_suelos = QListWidget()
        layout.addWidget(self.list_suelos)
        form_layout = QFormLayout()
        self.input_nombre = QLineEdit()
        self.input_descripcion = QLineEdit()
        self.input_imagen = QLineEdit()
        form_layout.addRow("Nombre:", self.input_nombre)
        form_layout.addRow("Descripción:", self.input_descripcion)
        form_layout.addRow("Imagen (ruta/URL):", self.input_imagen)
        layout.addLayout(form_layout)
        btn_crear = QPushButton("Crear/Actualizar")
        btn_crear.clicked.connect(self.crear_actualizar_suelo)
        layout.addWidget(btn_crear, alignment=Qt.AlignCenter)
        btn_eliminar = QPushButton("Eliminar Seleccionado")
        btn_eliminar.clicked.connect(self.eliminar_suelo)
        layout.addWidget(btn_eliminar, alignment=Qt.AlignCenter)
        btn_limpiar = QPushButton("Limpiar Campos")
        btn_limpiar.clicked.connect(self.limpiar_campos)
        layout.addWidget(btn_limpiar, alignment=Qt.AlignCenter)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        self.cargar_suelos()
        self.list_suelos.itemClicked.connect(self.cargar_en_formulario)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_suelos()
    
    def cargar_suelos(self):
        self.list_suelos.clear()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, nombre, descripcion, imagen FROM tipo_suelo")
        rows = cursor.fetchall()
        conn.close()
        for r in rows:
            self.list_suelos.addItem(f"{r[0]} | {r[1]} | {r[2]} | {r[3]}")
    
    def crear_actualizar_suelo(self):
        nombre = self.input_nombre.text().strip()
        descripcion = self.input_descripcion.text().strip()
        imagen = self.input_imagen.text().strip()
        if not nombre:
            QMessageBox.critical(self, "Error", "El nombre es obligatorio.")
            return
        selected = self.list_suelos.currentItem()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        if selected:
            codigo = selected.text().split("|")[0].strip()
            try:
                cursor.execute("""
                    UPDATE tipo_suelo
                    SET nombre = ?, descripcion = ?, imagen = ?
                    WHERE codigo = ?
                """, (nombre, descripcion, imagen, codigo))
                conn.commit()
                QMessageBox.information(self, "Éxito", "Tipo de suelo actualizado.")
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Error", "Ya existe un tipo de suelo con ese nombre.")
        else:
            try:
                cursor.execute("""
                    INSERT INTO tipo_suelo (nombre, descripcion, imagen)
                    VALUES (?, ?, ?)
                """, (nombre, descripcion, imagen))
                conn.commit()
                QMessageBox.information(self, "Éxito", "Nuevo tipo de suelo creado.")
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Error", "Ya existe un tipo de suelo con ese nombre.")
        conn.close()
        self.cargar_suelos()
        self.limpiar_campos()
    
    def eliminar_suelo(self):
        selected = self.list_suelos.currentItem()
        if not selected:
            QMessageBox.critical(self, "Error", "Seleccione un tipo de suelo para eliminar.")
            return
        codigo = selected.text().split("|")[0].strip()
        if QMessageBox.question(self, "Confirmar", f"¿Desea eliminar el código {codigo}?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            conn = sqlite3.connect("cultivos.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tipo_suelo WHERE codigo = ?", (codigo,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Tipo de suelo eliminado.")
            self.cargar_suelos()
            self.limpiar_campos()
    
    def cargar_en_formulario(self, item):
        line = item.text().split("|")
        nombre = line[1].strip()
        descripcion = line[2].strip()
        imagen = line[3].strip()
        self.input_nombre.setText(nombre)
        self.input_descripcion.setText(descripcion)
        self.input_imagen.setText(imagen)
    
    def limpiar_campos(self):
        self.input_nombre.clear()
        self.input_descripcion.clear()
        self.input_imagen.clear()
        self.list_suelos.clearSelection()

# ClimaManagementScreen: ABM para clima
class ClimaManagementScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Gestionar Clima")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        self.list_climas = QListWidget()
        layout.addWidget(self.list_climas)
        form_layout = QFormLayout()
        self.input_nombre = QLineEdit()
        self.input_grados = QLineEdit()
        self.input_descripcion = QLineEdit()
        self.input_imagen = QLineEdit()
        form_layout.addRow("Nombre:", self.input_nombre)
        form_layout.addRow("Grados Temperatura:", self.input_grados)
        form_layout.addRow("Descripción:", self.input_descripcion)
        form_layout.addRow("Imagen (ruta/URL):", self.input_imagen)
        layout.addLayout(form_layout)
        btn_crear = QPushButton("Crear/Actualizar")
        btn_crear.clicked.connect(self.crear_actualizar_clima)
        layout.addWidget(btn_crear, alignment=Qt.AlignCenter)
        btn_eliminar = QPushButton("Eliminar Seleccionado")
        btn_eliminar.clicked.connect(self.eliminar_clima)
        layout.addWidget(btn_eliminar, alignment=Qt.AlignCenter)
        btn_limpiar = QPushButton("Limpiar Campos")
        btn_limpiar.clicked.connect(self.limpiar_campos)
        layout.addWidget(btn_limpiar, alignment=Qt.AlignCenter)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        self.cargar_climas()
        self.list_climas.itemClicked.connect(self.cargar_en_formulario)
    
    def cargar_climas(self):
        self.list_climas.clear()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, nombre, grados_temperatura, descripcion, imagen FROM clima")
        rows = cursor.fetchall()
        conn.close()
        for r in rows:
            self.list_climas.addItem(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}")
    
    def crear_actualizar_clima(self):
        nombre = self.input_nombre.text().strip()
        grados_str = self.input_grados.text().strip()
        descripcion = self.input_descripcion.text().strip()
        imagen = self.input_imagen.text().strip()
        if not nombre:
            QMessageBox.critical(self, "Error", "El nombre es obligatorio.")
            return
        try:
            grados = float(grados_str) if grados_str else 0.0
        except ValueError:
            QMessageBox.critical(self, "Error", "Ingrese un valor numérico en grados de temperatura.")
            return
        selected = self.list_climas.currentItem()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        if selected:
            codigo = selected.text().split("|")[0].strip()
            try:
                cursor.execute("""
                    UPDATE clima
                    SET nombre = ?, grados_temperatura = ?, descripcion = ?, imagen = ?
                    WHERE codigo = ?
                """, (nombre, grados, descripcion, imagen, codigo))
                conn.commit()
                QMessageBox.information(self, "Éxito", "Clima actualizado.")
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Error", "Ya existe un clima con ese nombre.")
        else:
            try:
                cursor.execute("""
                    INSERT INTO clima (nombre, grados_temperatura, descripcion, imagen)
                    VALUES (?, ?, ?, ?)
                """, (nombre, grados, descripcion, imagen))
                conn.commit()
                QMessageBox.information(self, "Éxito", "Nuevo clima creado.")
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Error", "Ya existe un clima con ese nombre.")
        conn.close()
        self.cargar_climas()
        self.limpiar_campos()
    
    def eliminar_clima(self):
        selected = self.list_climas.currentItem()
        if not selected:
            QMessageBox.critical(self, "Error", "Seleccione un clima para eliminar.")
            return
        codigo = selected.text().split("|")[0].strip()
        if QMessageBox.question(self, "Confirmar", f"¿Desea eliminar el código {codigo}?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            conn = sqlite3.connect("cultivos.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clima WHERE codigo = ?", (codigo,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Clima eliminado.")
            self.cargar_climas()
            self.limpiar_campos()
    
    def cargar_en_formulario(self, item):
        line = item.text().split("|")
        nombre = line[1].strip()
        grados = line[2].strip()
        descripcion = line[3].strip()
        imagen = line[4].strip()
        self.input_nombre.setText(nombre)
        self.input_grados.setText(grados)
        self.input_descripcion.setText(descripcion)
        self.input_imagen.setText(imagen)
    
    def limpiar_campos(self):
        self.input_nombre.clear()
        self.input_grados.clear()
        self.input_descripcion.clear()
        self.input_imagen.clear()
        self.list_climas.clearSelection()

# TipoCultivoManagementScreen: ABM para tipo_cultivo (Solo Admin)
class TipoCultivoManagementScreen(QWidget):
    """
    Pantalla de ABM para la tabla tipo_cultivo.
    Permite ingresar el nombre del cultivo, seleccionar cuántos meses tarda en dar la primera cosecha
    y cuántos meses tarda en dar la cosecha rutinaria.
    """
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Gestionar Tipos de Cultivo")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        self.list_cultivos = QListWidget()
        layout.addWidget(self.list_cultivos)
        form_layout = QFormLayout()
        self.input_nombre = QLineEdit()
        form_layout.addRow("Nombre:", self.input_nombre)
        self.spin_primera = QSpinBox()
        self.spin_primera.setMinimum(0)
        self.spin_primera.setMaximum(100)
        form_layout.addRow("Meses para 1ra Cosecha:", self.spin_primera)
        self.spin_rutinaria = QSpinBox()
        self.spin_rutinaria.setMinimum(0)
        self.spin_rutinaria.setMaximum(100)
        form_layout.addRow("Meses para Cosecha Rutinaria:", self.spin_rutinaria)
        layout.addLayout(form_layout)
        btn_crear = QPushButton("Crear/Actualizar")
        btn_crear.clicked.connect(self.crear_actualizar_cultivo)
        layout.addWidget(btn_crear, alignment=Qt.AlignCenter)
        btn_eliminar = QPushButton("Eliminar Seleccionado")
        btn_eliminar.clicked.connect(self.eliminar_cultivo)
        layout.addWidget(btn_eliminar, alignment=Qt.AlignCenter)
        btn_limpiar = QPushButton("Limpiar Campos")
        btn_limpiar.clicked.connect(self.limpiar_campos)
        layout.addWidget(btn_limpiar, alignment=Qt.AlignCenter)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        self.cargar_cultivos()
        self.list_cultivos.itemClicked.connect(self.cargar_en_formulario)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_cultivos()
    
    def cargar_cultivos(self):
        self.list_cultivos.clear()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, meses_primera, meses_rutinaria FROM tipo_cultivo")
        rows = cursor.fetchall()
        conn.close()
        for r in rows:
            self.list_cultivos.addItem(f"{r[0]} | {r[1]} | 1ra: {r[2]} meses | Rutinaria: {r[3]} meses")
    
    def crear_actualizar_cultivo(self):
        nombre = self.input_nombre.text().strip()
        meses_primera = self.spin_primera.value()
        meses_rutinaria = self.spin_rutinaria.value()
        if not nombre:
            QMessageBox.critical(self, "Error", "El nombre es obligatorio.")
            return
        selected = self.list_cultivos.currentItem()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        if selected:
            cultivo_id = selected.text().split("|")[0].strip()
            try:
                cursor.execute("""
                    UPDATE tipo_cultivo
                    SET nombre = ?, meses_primera = ?, meses_rutinaria = ?
                    WHERE id = ?
                """, (nombre, meses_primera, meses_rutinaria, cultivo_id))
                conn.commit()
                QMessageBox.information(self, "Éxito", "Tipo de cultivo actualizado.")
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Error", "Ya existe un tipo de cultivo con ese nombre.")
        else:
            try:
                cursor.execute("""
                    INSERT INTO tipo_cultivo (nombre, meses_primera, meses_rutinaria)
                    VALUES (?, ?, ?)
                """, (nombre, meses_primera, meses_rutinaria))
                conn.commit()
                QMessageBox.information(self, "Éxito", "Nuevo tipo de cultivo creado.")
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Error", "Ya existe un tipo de cultivo con ese nombre.")
        conn.close()
        self.cargar_cultivos()
        self.limpiar_campos()
    
    def eliminar_cultivo(self):
        selected = self.list_cultivos.currentItem()
        if not selected:
            QMessageBox.critical(self, "Error", "Seleccione un tipo de cultivo para eliminar.")
            return
        cultivo_id = selected.text().split("|")[0].strip()
        if QMessageBox.question(self, "Confirmar", f"¿Desea eliminar el tipo de cultivo con ID {cultivo_id}?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            conn = sqlite3.connect("cultivos.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tipo_cultivo WHERE id = ?", (cultivo_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Tipo de cultivo eliminado.")
            self.cargar_cultivos()
            self.limpiar_campos()
    
    def cargar_en_formulario(self, item):
        parts = item.text().split("|")
        nombre = parts[1].strip()
        primera_str = parts[2].strip()  # "1ra: X meses"
        rutinaria_str = parts[3].strip()  # "Rutinaria: Y meses"
        try:
            meses_primera = int(primera_str.split(":")[1].split()[0])
            meses_rutinaria = int(rutinaria_str.split(":")[1].split()[0])
        except Exception as e:
            meses_primera = 0
            meses_rutinaria = 0
        self.input_nombre.setText(nombre)
        self.spin_primera.setValue(meses_primera)
        self.spin_rutinaria.setValue(meses_rutinaria)
    
    def limpiar_campos(self):
        self.input_nombre.clear()
        self.spin_primera.setValue(0)
        self.spin_rutinaria.setValue(0)
        self.list_cultivos.clearSelection()

# UserManagementScreen: Gestión de Usuarios (Solo Admin)
class UserManagementScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        title = QLabel("Gestión de Usuarios")
        title.setFont(QFont("Helvetica", 18, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)
        self.user_list = QListWidget()
        layout.addWidget(self.user_list)
        self.refresh_user_list()
        form_layout = QFormLayout()
        self.new_username = QLineEdit()
        form_layout.addRow("Username:", self.new_username)
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.new_password)
        self.new_email = QLineEdit()
        form_layout.addRow("Email:", self.new_email)
        layout.addLayout(form_layout)
        btn_crear = QPushButton("Crear Usuario")
        btn_crear.clicked.connect(self.create_user)
        layout.addWidget(btn_crear, alignment=Qt.AlignCenter)
        btn_eliminar = QPushButton("Eliminar Usuario")
        btn_eliminar.clicked.connect(self.delete_user)
        layout.addWidget(btn_eliminar, alignment=Qt.AlignCenter)
        btn_editar = QPushButton("Editar Usuario")
        btn_editar.clicked.connect(self.edit_user)
        layout.addWidget(btn_editar, alignment=Qt.AlignCenter)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)
    
    def refresh_user_list(self):
        self.user_list.clear()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, email FROM usuarios")
        users = cursor.fetchall()
        conn.close()
        for user in users:
            self.user_list.addItem(f"{user[0]} - {user[1] if user[1] else ''}")
    
    def create_user(self):
        username = self.new_username.text().strip()
        password = self.new_password.text().strip()
        email = self.new_email.text().strip()
        if not username or not password or not email:
            QMessageBox.critical(self, "Error", "Todos los campos son requeridos para crear un usuario.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (username, password, role, email) VALUES (?, ?, 'usuario', ?)",
                           (username, password, email))
            conn.commit()
            QMessageBox.information(self, "Éxito", "Usuario creado correctamente.")
            self.refresh_user_list()
            self.new_username.clear()
            self.new_password.clear()
            self.new_email.clear()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "El usuario ya existe.")
        conn.close()
    
    def delete_user(self):
        selected = self.user_list.currentItem()
        if not selected:
            QMessageBox.critical(self, "Error", "Seleccione un usuario para eliminar.")
            return
        user_info = selected.text()
        username = user_info.split(" - ")[0]
        if username == "admin":
            QMessageBox.critical(self, "Error", "No se puede eliminar el usuario admin.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Éxito", "Usuario eliminado.")
        self.refresh_user_list()
    
    def edit_user(self):
        selected = self.user_list.currentItem()
        if not selected:
            QMessageBox.critical(self, "Error", "Seleccione un usuario para editar.")
            return
        user_info = selected.text()
        username = user_info.split(" - ")[0]
        if username == "admin":
            QMessageBox.critical(self, "Error", "No se puede editar el usuario admin.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, email FROM usuarios WHERE username = ?", (username,))
        data = cursor.fetchone()
        conn.close()
        if not data:
            QMessageBox.critical(self, "Error", "No se encontró información del usuario.")
            return
        new_username, ok1 = QInputDialog.getText(self, "Editar Usuario", "Nuevo username:", text=data[0])
        new_password, ok2 = QInputDialog.getText(self, "Editar Usuario", "Nueva contraseña:", text=data[1], echo=QLineEdit.Password)
        new_email, ok3 = QInputDialog.getText(self, "Editar Usuario", "Nuevo email:", text=data[2])
        if not (ok1 and ok2 and ok3 and new_username and new_password and new_email):
            QMessageBox.critical(self, "Error", "Todos los campos son requeridos para editar el usuario.")
            return
        try:
            conn = sqlite3.connect("cultivos.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE usuarios
                SET username = ?, password = ?, email = ?
                WHERE username = ?
            """, (new_username, new_password, new_email, username))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Usuario actualizado correctamente.")
            self.refresh_user_list()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "El nuevo username ya existe.")

# CultivosScreen: Pantalla para mostrar datos de ejemplo (sin CRUD)
class CultivosScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        label = QLabel("Pantalla: Cultivos (Ejemplo)")
        label.setFont(QFont("Helvetica", 16, QFont.Bold))
        layout.addWidget(label, alignment=Qt.AlignCenter)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText("Aquí se mostrarían cultivos en general (ej. maíz, trigo, tomate, etc.)\nEste ejemplo no tiene ABM.")
        layout.addWidget(text)
        btn_volver = QPushButton("Volver")
        btn_volver.clicked.connect(lambda: self.controller.show_screen("main"))
        layout.addWidget(btn_volver, alignment=Qt.AlignCenter)
        self.setLayout(layout)

# -----------------------------
# Clase Principal: MainWindow y Controlador de Pantallas
# -----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Cultivos")
        self.setGeometry(100, 100, 900, 600)
        self.current_user = None
        self.user_role = None
        self.current_email = None
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #e8f5e9;
            }
            QPushButton {
                background-color: #66bb6a;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4caf50;
            }
            QLabel {
                color: #33691e;
            }
            QLineEdit, QComboBox, QTextEdit, QListWidget {
                background-color: #f1f8e9;
                border: 1px solid #c5e1a5;
                border-radius: 3px;
                padding: 4px;
            }
        """)
        self.screens = {}
        self.screens["login"] = LoginScreen(self)
        self.screens["main"] = MainScreen(self)
        self.screens["registrar"] = RegistrarScreen(self)
        self.screens["buscar"] = BuscarScreen(self)
        self.screens["perfil"] = PerfilScreen(self)
        self.screens["informe"] = InformeScreen(self)
        self.screens["consulta"] = ConsultaScreen(self)
        self.screens["gestionar_hectareas"] = GestionarHectareasScreen(self)
        self.screens["gestion_cultivo"] = GestionCultivoScreen(self)
        self.screens["usuarios"] = UserManagementScreen(self)
        self.screens["cultivos"] = CultivosScreen(self)
        self.screens["gestion_hortaliza"] = TipoHortalizaManagementScreen(self)
        self.screens["gestion_suelo"] = TipoSueloManagementScreen(self)
        self.screens["gestion_clima"] = ClimaManagementScreen(self)
        self.screens["gestion_tipo_cultivo"] = TipoCultivoManagementScreen(self)
        for screen in self.screens.values():
            self.stack.addWidget(screen)
        self.show_screen("login")
    
    def update_menu(self):
        menu_bar = self.menuBar()
        menu_bar.clear()
        if self.user_role == "admin":
            datos_menu = menu_bar.addMenu("Datos")
            accion_gestionar_suelo = datos_menu.addAction("Gestionar Tipos de Suelo")
            accion_gestionar_suelo.triggered.connect(lambda: self.show_screen("gestion_suelo"))
            accion_gestionar_tipo_cultivo = datos_menu.addAction("Gestionar Tipos de Cultivo")
            accion_gestionar_tipo_cultivo.triggered.connect(lambda: self.show_screen("gestion_tipo_cultivo"))
    
    def show_screen(self, name):
        # Restricción de acceso: Solo el administrador puede acceder a las pantallas de gestión de usuarios,
        # gestión de tipo cultivo, gestión de cultivo y gestión de hectáreas.
        if name in ["usuarios", "gestion_tipo_cultivo", "gestion_cultivo", "gestionar_hectareas"] and self.user_role != "admin":
            QMessageBox.critical(self, "Acceso Denegado", "Solo el administrador puede acceder a esta opción.")
            return
        if name == "login":
            self.screens["login"].refresh_users()
            self.menuBar().clear()
        elif name == "main":
            self.screens["main"].update_header()
            self.update_menu()
        elif name == "perfil":
            self.screens["perfil"].cargar_perfil()
        elif name == "informe":
            self.screens["informe"].cargar_informe()
        self.stack.setCurrentWidget(self.screens[name])

# -----------------------------
# Ejecutar la aplicación
# -----------------------------
if __name__ == "__main__":
    inicializar_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
