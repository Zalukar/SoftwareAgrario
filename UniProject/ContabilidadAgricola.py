import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta
from PIL import Image, ImageTk  # Requiere instalar Pillow (pip install Pillow)

# -----------------------------
# Funciones auxiliares para consultar datos
# -----------------------------
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
# Configuración y Base de Datos
# -----------------------------
conn = sqlite3.connect("cultivos.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON")

# Tabla Usuarios (Persona)
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT CHECK(role IN ('admin', 'usuario')),
    email TEXT
)
""")
cursor.execute("PRAGMA table_info(usuarios)")
cols = [col[1] for col in cursor.fetchall()]
if "email" not in cols:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN email TEXT")

# Tabla Hectareas (datos de la parcela)
cursor.execute("""
CREATE TABLE IF NOT EXISTS hectareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero INTEGER,
    tipo_de_cultivo TEXT,
    siembra TEXT,
    primera_cosecha TEXT,
    cosecha_rutinaria TEXT
)
""")
# Agregar columnas adicionales: tipo_suelo y temperatura
cursor.execute("PRAGMA table_info(hectareas)")
existing = [col[1] for col in cursor.fetchall()]
if "tipo_suelo" not in existing:
    cursor.execute("ALTER TABLE hectareas ADD COLUMN tipo_suelo TEXT")
if "temperatura" not in existing:
    cursor.execute("ALTER TABLE hectareas ADD COLUMN temperatura REAL")
conn.commit()

# Insertar por defecto el usuario admin
cursor.execute("""
INSERT OR IGNORE INTO usuarios (username, password, role, email) VALUES
('admin', 'admin123', 'admin', NULL)
""")

# Tabla Tipo de Suelo
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
    conn.commit()

# Tabla Tipo de Hortaliza
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
    conn.commit()

# Tabla Clima
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
    conn.commit()

# Tabla Gestión Cultivo (relaciona a la persona con tipos, suelo y clima)
cursor.execute("DROP TABLE IF EXISTS gestion_cultivo")
cursor.execute("""
CREATE TABLE gestion_cultivo (
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
conn.commit()
conn.close()

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
# Frame: Gestión Cultivo
# -----------------------------
class GestionCultivoFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        tk.Label(self, text="Gestión Cultivo", font=("Helvetica", 18, "bold"), fg="#333333").pack(pady=20)
        tk.Button(self, text="Registrar Gestión Cultivo", font=("Helvetica", 12), command=self.registrar_gestion).pack(pady=5)
        self.gestion_list = tk.Listbox(self, width=80, font=("Helvetica", 12))
        self.gestion_list.pack(pady=10, fill="both", expand=True)
        tk.Button(self, text="Editar Seleccionada", font=("Helvetica", 12), command=self.editar_gestion).pack(pady=5)
        tk.Button(self, text="Eliminar Seleccionada", font=("Helvetica", 12), command=self.eliminar_gestion).pack(pady=5)
        tk.Button(self, text="Volver", font=("Helvetica", 12), command=lambda: controller.show_frame(CultivosMainFrame)).pack(pady=10)
        self.cargar_gestiones()

    def cargar_gestiones(self):
        self.gestion_list.delete(0, tk.END)
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, id_persona, id_tipo_hortaliza, id_tipo_suelo, id_clima, video, observaciones FROM gestion_cultivo")
        gestiones = cursor.fetchall()
        conn.close()
        for g in gestiones:
            self.gestion_list.insert(tk.END, f"Código: {g[0]} | Persona ID: {g[1]} | Hortaliza ID: {g[2]} | Suelo ID: {g[3]} | Clima ID: {g[4]} | Video: {g[5]} | Obs: {g[6]}")

    def registrar_gestion(self):
        reg_win = tk.Toplevel(self)
        reg_win.title("Registrar Gestión Cultivo")

        # Seleccionar Persona
        tk.Label(reg_win, text="Seleccione Persona:").grid(row=0, column=0, padx=5, pady=5)
        personas = obtener_personas()
        if personas:
            personas_dict = {f"{p[0]}: {p[1]}": p[0] for p in personas}
            var_persona = tk.StringVar(value=list(personas_dict.keys())[0])
            tk.OptionMenu(reg_win, var_persona, *personas_dict.keys()).grid(row=0, column=1, padx=5, pady=5)
        else:
            messagebox.showerror("Error", "No hay usuarios registrados.", parent=reg_win)
            reg_win.destroy()
            return

        # Seleccionar Tipo de Hortaliza
        tk.Label(reg_win, text="Seleccione Tipo de Hortaliza:").grid(row=1, column=0, padx=5, pady=5)
        hort_data = obtener_tipo_hortaliza()
        if hort_data:
            hort_dict = {f"{h[0]}: {h[1]}": h[0] for h in hort_data}
            var_hortaliza = tk.StringVar(value=list(hort_dict.keys())[0])
            tk.OptionMenu(reg_win, var_hortaliza, *hort_dict.keys()).grid(row=1, column=1, padx=5, pady=5)
        else:
            messagebox.showerror("Error", "No hay tipos de hortaliza registrados.", parent=reg_win)
            reg_win.destroy()
            return

        # Seleccionar Tipo de Suelo
        tk.Label(reg_win, text="Seleccione Tipo de Suelo:").grid(row=2, column=0, padx=5, pady=5)
        suelo_data = obtener_tipo_suelo()
        if suelo_data:
            suelo_dict = {f"{s[0]}: {s[1]}": s[0] for s in suelo_data}
            var_suelo = tk.StringVar(value=list(suelo_dict.keys())[0])
            tk.OptionMenu(reg_win, var_suelo, *suelo_dict.keys()).grid(row=2, column=1, padx=5, pady=5)
        else:
            messagebox.showerror("Error", "No hay tipos de suelo registrados.", parent=reg_win)
            reg_win.destroy()
            return

        # Seleccionar Clima
        tk.Label(reg_win, text="Seleccione Clima:").grid(row=3, column=0, padx=5, pady=5)
        clima_data = obtener_climas()
        if clima_data:
            clima_dict = {f"{c[0]}: {c[1]}": c[0] for c in clima_data}
            var_clima = tk.StringVar(value=list(clima_dict.keys())[0])
            tk.OptionMenu(reg_win, var_clima, *clima_dict.keys()).grid(row=3, column=1, padx=5, pady=5)
        else:
            messagebox.showerror("Error", "No hay climas registrados.", parent=reg_win)
            reg_win.destroy()
            return

        # Video y Observaciones
        tk.Label(reg_win, text="Video (URL o ruta):").grid(row=4, column=0, padx=5, pady=5)
        entry_video = tk.Entry(reg_win)
        entry_video.grid(row=4, column=1, padx=5, pady=5)
        tk.Label(reg_win, text="Observaciones:").grid(row=5, column=0, padx=5, pady=5)
        entry_obs = tk.Entry(reg_win)
        entry_obs.grid(row=5, column=1, padx=5, pady=5)

        def guardar_registro():
            try:
                id_persona = personas_dict[var_persona.get()]
                id_hortaliza = hort_dict[var_hortaliza.get()]
                id_suelo = suelo_dict[var_suelo.get()]
                id_clima = clima_dict[var_clima.get()]
            except Exception as e:
                messagebox.showerror("Error", f"Error al obtener valores: {e}", parent=reg_win)
                return
            video = entry_video.get().strip()
            observaciones = entry_obs.get().strip()
            conn = sqlite3.connect("cultivos.db")
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO gestion_cultivo (id_persona, id_tipo_hortaliza, id_tipo_suelo, id_clima, video, observaciones)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (id_persona, id_hortaliza, id_suelo, id_clima, video, observaciones))
            conn.commit()
            conn.close()
            messagebox.showinfo("Registro", "Gestión cultivo registrada.", parent=reg_win)
            reg_win.destroy()
            self.cargar_gestiones()

        tk.Button(reg_win, text="Registrar", command=guardar_registro).grid(row=6, column=0, columnspan=2, pady=10)

    def editar_gestion(self):
        selected = self.gestion_list.curselection()
        if not selected:
            messagebox.showerror("Error", "Seleccione una gestión para editar.")
            return
        line = self.gestion_list.get(selected[0])
        codigo = int(line.split("|")[0].split(":")[1].strip())
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id_persona, id_tipo_hortaliza, id_tipo_suelo, id_clima, video, observaciones FROM gestion_cultivo WHERE codigo = ?", (codigo,))
        data = cursor.fetchone()
        conn.close()
        if not data:
            messagebox.showerror("Error", "No se encontró la gestión seleccionada.")
            return

        edit_win = tk.Toplevel(self)
        edit_win.title("Editar Gestión Cultivo")
        
        # Persona
        tk.Label(edit_win, text="Seleccione Persona:").grid(row=0, column=0, padx=5, pady=5)
        personas = obtener_personas()
        if personas:
            personas_dict = {f"{p[0]}: {p[1]}": p[0] for p in personas}
            persona_ini = [k for k, v in personas_dict.items() if v == data[0]][0]
            var_persona = tk.StringVar(value=persona_ini)
            tk.OptionMenu(edit_win, var_persona, *personas_dict.keys()).grid(row=0, column=1, padx=5, pady=5)
        else:
            messagebox.showerror("Error", "No hay usuarios registrados.", parent=edit_win)
            edit_win.destroy()
            return

        # Tipo de Hortaliza
        tk.Label(edit_win, text="Seleccione Tipo de Hortaliza:").grid(row=1, column=0, padx=5, pady=5)
        hort_data = obtener_tipo_hortaliza()
        if hort_data:
            hort_dict = {f"{h[0]}: {h[1]}": h[0] for h in hort_data}
            hort_ini = [k for k, v in hort_dict.items() if v == data[1]][0]
            var_hortaliza = tk.StringVar(value=hort_ini)
            tk.OptionMenu(edit_win, var_hortaliza, *hort_dict.keys()).grid(row=1, column=1, padx=5, pady=5)
        else:
            messagebox.showerror("Error", "No hay tipos de hortaliza registrados.", parent=edit_win)
            edit_win.destroy()
            return

        # Tipo de Suelo
        tk.Label(edit_win, text="Seleccione Tipo de Suelo:").grid(row=2, column=0, padx=5, pady=5)
        suelo_data = obtener_tipo_suelo()
        if suelo_data:
            suelo_dict = {f"{s[0]}: {s[1]}": s[0] for s in suelo_data}
            suelo_ini = [k for k, v in suelo_dict.items() if v == data[2]][0]
            var_suelo = tk.StringVar(value=suelo_ini)
            tk.OptionMenu(edit_win, var_suelo, *suelo_dict.keys()).grid(row=2, column=1, padx=5, pady=5)
        else:
            messagebox.showerror("Error", "No hay tipos de suelo registrados.", parent=edit_win)
            edit_win.destroy()
            return

        # Clima
        tk.Label(edit_win, text="Seleccione Clima:").grid(row=3, column=0, padx=5, pady=5)
        clima_data = obtener_climas()
        if clima_data:
            clima_dict = {f"{c[0]}: {c[1]}": c[0] for c in clima_data}
            clima_ini = [k for k, v in clima_dict.items() if v == data[3]][0]
            var_clima = tk.StringVar(value=clima_ini)
            tk.OptionMenu(edit_win, var_clima, *clima_dict.keys()).grid(row=3, column=1, padx=5, pady=5)
        else:
            messagebox.showerror("Error", "No hay climas registrados.", parent=edit_win)
            edit_win.destroy()
            return

        # Video
        tk.Label(edit_win, text="Video (URL o ruta):").grid(row=4, column=0, padx=5, pady=5)
        entry_video = tk.Entry(edit_win)
        entry_video.insert(0, data[4])
        entry_video.grid(row=4, column=1, padx=5, pady=5)

        # Observaciones
        tk.Label(edit_win, text="Observaciones:").grid(row=5, column=0, padx=5, pady=5)
        entry_obs = tk.Entry(edit_win)
        entry_obs.insert(0, data[5])
        entry_obs.grid(row=5, column=1, padx=5, pady=5)

        def guardar_edicion():
            try:
                id_persona = personas_dict[var_persona.get()]
                id_hortaliza = hort_dict[var_hortaliza.get()]
                id_suelo = suelo_dict[var_suelo.get()]
                id_clima = clima_dict[var_clima.get()]
            except Exception as e:
                messagebox.showerror("Error", f"Error al obtener valores: {e}", parent=edit_win)
                return
            video = entry_video.get().strip()
            observaciones = entry_obs.get().strip()
            conn = sqlite3.connect("cultivos.db")
            cur = conn.cursor()
            cur.execute("""
                UPDATE gestion_cultivo
                SET id_persona = ?, id_tipo_hortaliza = ?, id_tipo_suelo = ?, id_clima = ?, video = ?, observaciones = ?
                WHERE codigo = ?
            """, (id_persona, id_hortaliza, id_suelo, id_clima, video, observaciones, codigo))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Gestión cultivo actualizada.", parent=edit_win)
            edit_win.destroy()
            self.cargar_gestiones()

        tk.Button(edit_win, text="Guardar cambios", command=guardar_edicion).grid(row=6, column=0, columnspan=2, pady=10)

    def eliminar_gestion(self):
        selected = self.gestion_list.curselection()
        if not selected:
            messagebox.showerror("Error", "Seleccione una gestión para eliminar.")
            return
        line = self.gestion_list.get(selected[0])
        codigo = int(line.split("|")[0].split(":")[1].strip())
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la gestión con código {codigo}?"):
            conn = sqlite3.connect("cultivos.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gestion_cultivo WHERE codigo = ?", (codigo,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Gestión cultivo eliminada.")
            self.cargar_gestiones()

# -----------------------------
# Frame: Informe de Gestión Cultivo
# -----------------------------
class InformeGestionCultivoFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        tk.Label(self, text="Informe de Gestión Cultivo", font=("Helvetica", 18, "bold"), fg="#333333").pack(pady=20)
        self.informe_text = tk.Text(self, wrap="word", font=("Helvetica", 12))
        self.informe_text.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Button(self, text="Volver", font=("Helvetica", 12), command=lambda: controller.show_frame(CultivosMainFrame)).pack(pady=10)
    
    def cargar_informe(self):
        self.informe_text.delete("1.0", tk.END)
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
            for r in registros:
                self.informe_text.insert(tk.END, f"Código: {r[0]}\nUsuario: {r[1]}\nTipo Hortaliza: {r[2]}\nTipo Suelo: {r[3]}\nClima: {r[4]}\nVideo: {r[5]}\nObservaciones: {r[6]}\n{'-'*40}\n")
        else:
            self.informe_text.insert(tk.END, "No hay registros de gestión cultivo.")

# -----------------------------
# Frame: Consulta sobre Tipo de Cultivo
# -----------------------------
class ConsultaCultivoFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        tk.Label(self, text="Consulta Tipo de Cultivo", font=("Helvetica", 18, "bold"), fg="#333333").pack(pady=20)
        tk.Label(self, text="Ingrese el nombre del tipo de hortaliza:", font=("Helvetica", 12)).pack(pady=5)
        self.consulta_entry = tk.Entry(self, font=("Helvetica", 12))
        self.consulta_entry.pack(pady=5)
        tk.Button(self, text="Buscar", font=("Helvetica", 12), command=self.buscar_tipo).pack(pady=5)
        self.result_text = tk.Text(self, wrap="word", font=("Helvetica", 12))
        self.result_text.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Button(self, text="Volver", font=("Helvetica", 12), command=lambda: controller.show_frame(CultivosMainFrame)).pack(pady=10)
    
    def cargar_consulta(self):
        self.consulta_entry.delete(0, tk.END)
        self.result_text.delete("1.0", tk.END)
    
    def buscar_tipo(self):
        nombre = self.consulta_entry.get().strip()
        if not nombre:
            messagebox.showerror("Error", "Ingrese un nombre para consultar.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, nombre, descripcion, imagen FROM tipo_hortaliza WHERE nombre LIKE ?", ('%' + nombre + '%',))
        registros = cursor.fetchall()
        conn.close()
        self.result_text.delete("1.0", tk.END)
        if registros:
            for r in registros:
                self.result_text.insert(tk.END, f"Código: {r[0]}\nNombre: {r[1]}\nDescripción: {r[2]}\nImagen: {r[3]}\n{'-'*30}\n")
        else:
            self.result_text.insert(tk.END, "No se encontró el tipo de cultivo.")

# -----------------------------
# Frame: Interfaz Principal de Cultivos
# -----------------------------
class CultivosMainFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        header_frame = tk.Frame(self)
        header_frame.pack(side="top", fill="x", pady=10)
        self.header_label = tk.Label(header_frame, text="", font=("Helvetica", 16, "bold"), fg="#333333")
        self.header_label.pack(side="left")
        self.email_label = tk.Label(header_frame, text="")
        
        self.menu_frame = tk.Frame(self)
        self.menu_frame.pack(side="top", fill="x", pady=10)
        
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.show_mostrar_view()
    
    def refresh_menu(self):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        tk.Button(self.menu_frame, text="Registrar Hectárea", font=("Helvetica", 12), command=self.show_registrar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Mostrar Hectáreas", font=("Helvetica", 12), command=self.show_mostrar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Buscar Hectárea", font=("Helvetica", 12), command=self.show_buscar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Perfil", font=("Helvetica", 12), command=lambda: self.controller.show_frame(PerfilFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Informe Cultivo", font=("Helvetica", 12), command=lambda: self.controller.show_frame(InformeGestionCultivoFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Consulta Cultivo", font=("Helvetica", 12), command=lambda: self.controller.show_frame(ConsultaCultivoFrame)).pack(side="left", padx=5)
        if self.controller.user_role == "admin":
            tk.Button(self.menu_frame, text="Gestionar Hectáreas", font=("Helvetica", 12), command=lambda: self.controller.show_frame(GestionarHectareasFrame)).pack(side="left", padx=5)
            tk.Button(self.menu_frame, text="Gestión Cultivo", font=("Helvetica", 12), command=lambda: self.controller.show_frame(GestionCultivoFrame)).pack(side="left", padx=5)
            tk.Button(self.menu_frame, text="Gestionar Usuarios", font=("Helvetica", 12), command=lambda: self.controller.show_frame(UserManagementFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Logout", font=("Helvetica", 12), command=lambda: self.controller.show_frame(LoginFrame)).pack(side="left", padx=5)
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_registrar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Registrar Hectárea", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        tk.Label(self.content_frame, text="Seleccione Tipo de Cultivo:", font=("Helvetica", 12), fg="#333333").pack()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM tipo_hortaliza")
        rows = cursor.fetchall()
        conn.close()
        if rows:
            crop_types = [r[0] for r in rows]
        else:
            crop_types = ["limones", "maíz", "trigo", "tomate"]
        self.selected_crop_type = tk.StringVar(value=crop_types[0])
        crop_frame = tk.Frame(self.content_frame)
        crop_frame.pack(pady=5)
        for crop in crop_types:
            tk.Radiobutton(crop_frame, text=crop, variable=self.selected_crop_type, value=crop,
                           command=self.toggle_additional_fields, font=("Helvetica", 10)).pack(side="left", padx=5)
        tk.Label(self.content_frame, text="Fecha de Siembra (YYYY-MM-DD):", font=("Helvetica", 12), fg="#333333").pack()
        self.siembra_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.siembra_entry.pack(pady=5)
        # NUEVO: Seleccionar Tipo de Suelo
        tk.Label(self.content_frame, text="Seleccione Tipo de Suelo:", font=("Helvetica", 12), fg="#333333").pack()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM tipo_suelo")
        suelos = cursor.fetchall()
        conn.close()
        if suelos:
            suelo_types = [s[0] for s in suelos]
        else:
            suelo_types = ["Sin suelo registrado"]
        self.selected_suelo = tk.StringVar(value=suelo_types[0])
        tk.OptionMenu(self.content_frame, self.selected_suelo, *suelo_types).pack(pady=5)
        # NUEVO: Ingresar Temperatura
        tk.Label(self.content_frame, text="Temperatura (°C):", font=("Helvetica", 12), fg="#333333").pack()
        self.temperatura_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.temperatura_entry.pack(pady=5)
        
        self.additional_frame = tk.Frame(self.content_frame)
        self.additional_frame.pack(pady=5)
        tk.Label(self.additional_frame, text="Fecha de Primera Cosecha (YYYY-MM-DD):", font=("Helvetica", 10)).grid(row=0, column=0, padx=5, pady=5)
        self.primera_entry = tk.Entry(self.additional_frame, font=("Helvetica", 10))
        self.primera_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.additional_frame, text="Cosecha Rutinaria:", font=("Helvetica", 10)).grid(row=1, column=0, padx=5, pady=5)
        self.rutinaria_entry = tk.Entry(self.additional_frame, font=("Helvetica", 10))
        self.rutinaria_entry.grid(row=1, column=1, padx=5, pady=5)
        self.toggle_additional_fields()
        tk.Button(self.content_frame, text="Registrar", font=("Helvetica", 12), command=self.registrar_hectarea).pack(pady=10)
        tk.Button(self.content_frame, text="Volver", font=("Helvetica", 12), command=self.show_mostrar_view).pack(pady=5)
    
    def toggle_additional_fields(self):
        crop = self.selected_crop_type.get().lower()
        if crop == "limones":
            self.additional_frame.pack_forget()
        else:
            self.additional_frame.pack(pady=5)
    
    def registrar_hectarea(self):
        siembra = self.siembra_entry.get().strip()
        crop = self.selected_crop_type.get()
        if not siembra:
            messagebox.showerror("Error", "Ingrese la fecha de siembra.")
            return
        if crop.lower() != "limones":
            primera = self.primera_entry.get().strip()
            rutinaria = self.rutinaria_entry.get().strip()
            if not primera or not rutinaria:
                primera = None
                rutinaria = None
        else:
            primera = None
            rutinaria = None
        suelo = self.selected_suelo.get()
        temperatura = self.temperatura_entry.get().strip()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(numero) FROM hectareas")
        max_num = cursor.fetchone()[0]
        conn.close()
        numero = 1 if max_num is None else max_num + 1
        try:
            hectarea = Hectarea(numero, crop, siembra, primera, rutinaria, suelo, temperatura)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        hectarea.guardar_en_bd()
        messagebox.showinfo("Registro", "Hectárea registrada con éxito.")
        self.show_mostrar_view()
    
    def show_mostrar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Hectáreas Registradas", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        text_frame = tk.Frame(self.content_frame)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        v_scroll = tk.Scrollbar(text_frame, orient="vertical")
        h_scroll = tk.Scrollbar(text_frame, orient="horizontal")
        output = tk.Text(text_frame, wrap="none", yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set, font=("Courier New", 10))
        v_scroll.config(command=output.yview)
        h_scroll.config(command=output.xview)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        output.pack(side="left", fill="both", expand=True)
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hectareas")
        hectareas = cursor.fetchall()
        conn.close()
        if hectareas:
            for h in hectareas:
                output.insert(tk.END,
                              f"Hectárea {h[1]}:\n  Tipo: {h[2]}\n  Siembra: {h[3]}\n  1ra Cosecha: {h[4]}\n  Cosecha Rutinaria: {h[5]}\n  Tipo de Suelo: {h[6]}\n  Temperatura: {h[7]}\n\n")
        else:
            output.insert(tk.END, "No hay hectáreas registradas.")
        tk.Button(self.content_frame, text="Volver", font=("Helvetica", 12), command=self.show_mostrar_view).pack(pady=10)
    
    def show_buscar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Buscar Hectárea", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        tk.Label(self.content_frame, text="Número de Hectárea:", font=("Helvetica", 12)).pack()
        self.num_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.num_entry.pack(pady=5)
        result_frame = tk.Frame(self.content_frame)
        result_frame.pack(fill="both", expand=True, padx=10, pady=10)
        v_scroll_r = tk.Scrollbar(result_frame, orient="vertical")
        h_scroll_r = tk.Scrollbar(result_frame, orient="horizontal")
        self.result_text = tk.Text(result_frame, wrap="none", yscrollcommand=v_scroll_r.set, xscrollcommand=h_scroll_r.set, font=("Courier New", 10))
        v_scroll_r.config(command=self.result_text.yview)
        h_scroll_r.config(command=self.result_text.xview)
        v_scroll_r.pack(side="right", fill="y")
        h_scroll_r.pack(side="bottom", fill="x")
        self.result_text.pack(side="left", fill="both", expand=True)
        tk.Button(self.content_frame, text="Buscar", font=("Helvetica", 12), command=self.buscar_hectarea).pack(pady=5)
        tk.Button(self.content_frame, text="Volver", font=("Helvetica", 12), command=self.show_mostrar_view).pack(pady=5)
    
    def buscar_hectarea(self):
        num = self.num_entry.get().strip()
        if not num.isdigit():
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "Ingrese un número válido.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hectareas WHERE numero = ?", (int(num),))
        hectarea = cursor.fetchone()
        conn.close()
        self.result_text.delete("1.0", tk.END)
        if hectarea:
            self.result_text.insert(tk.END,
                                    f"Hectárea {hectarea[1]}:\n  Tipo: {hectarea[2]}\n  Siembra: {hectarea[3]}\n  1ra Cosecha: {hectarea[4]}\n  Cosecha Rutinaria: {hectarea[5]}\n  Tipo de Suelo: {hectarea[6]}\n  Temperatura: {hectarea[7]}\n")
        else:
            self.result_text.insert(tk.END, f"No se encontró la Hectárea {num}.")

# -----------------------------
# Frame: Gestión de Usuarios (solo para admin)
# -----------------------------
class UserManagementFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#E2E2E2")
        self.controller = controller
        tk.Label(self, text="Gestión de Usuarios", font=("Helvetica", 18, "bold"), fg="#333333", bg="#E2E2E2").pack(pady=20)
        self.user_list = tk.Listbox(self, width=50, font=("Helvetica", 12))
        self.user_list.pack(pady=10)
        self.refresh_user_list()
        tk.Label(self, text="Nuevo Usuario", font=("Helvetica", 14, "bold"), fg="#333333", bg="#E2E2E2").pack(pady=10)
        tk.Label(self, text="Username:", font=("Helvetica", 12), bg="#E2E2E2").pack()
        self.new_username = tk.Entry(self, font=("Helvetica", 12))
        self.new_username.pack(pady=5)
        tk.Label(self, text="Password:", font=("Helvetica", 12), bg="#E2E2E2").pack()
        self.new_password = tk.Entry(self, font=("Helvetica", 12), show="*")
        self.new_password.pack(pady=5)
        tk.Label(self, text="Email:", font=("Helvetica", 12), bg="#E2E2E2").pack()
        self.new_email = tk.Entry(self, font=("Helvetica", 12))
        self.new_email.pack(pady=5)
        tk.Label(self, text="Rol: usuario", font=("Helvetica", 12), bg="#E2E2E2").pack(pady=5)
        tk.Button(self, text="Crear Usuario", font=("Helvetica", 12), command=self.create_user).pack(pady=5)
        tk.Button(self, text="Eliminar Usuario", font=("Helvetica", 12), command=self.delete_user).pack(pady=5)
        tk.Button(self, text="Editar Usuario", font=("Helvetica", 12), command=self.edit_user).pack(pady=5)
        tk.Button(self, text="Volver", font=("Helvetica", 12), command=lambda: controller.show_frame(CultivosMainFrame)).pack(pady=10)
    
    def refresh_user_list(self):
        self.user_list.delete(0, tk.END)
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, email FROM usuarios")
        users = cursor.fetchall()
        conn.close()
        for user in users:
            self.user_list.insert(tk.END, f"{user[0]} - {user[1] if user[1] is not None else ''}")
    
    def create_user(self):
        username = self.new_username.get().strip()
        password = self.new_password.get().strip()
        email = self.new_email.get().strip()
        if not username or not password or not email:
            messagebox.showerror("Error", "Todos los campos son requeridos para crear un usuario.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (username, password, role, email) VALUES (?, ?, 'usuario', ?)",
                           (username, password, email))
            conn.commit()
            messagebox.showinfo("Éxito", "Usuario creado correctamente.")
            self.refresh_user_list()
            self.new_username.delete(0, tk.END)
            self.new_password.delete(0, tk.END)
            self.new_email.delete(0, tk.END)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "El usuario ya existe.")
        conn.close()
    
    def delete_user(self):
        selected = self.user_list.curselection()
        if not selected:
            messagebox.showerror("Error", "Seleccione un usuario para eliminar.")
            return
        user_info = self.user_list.get(selected[0])
        username = user_info.split(" - ")[0]
        if username == "admin":
            messagebox.showerror("Error", "No se puede eliminar el usuario admin.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Éxito", "Usuario eliminado.")
        self.refresh_user_list()
    
    def edit_user(self):
        selected = self.user_list.curselection()
        if not selected:
            messagebox.showerror("Error", "Seleccione un usuario para editar.")
            return
        user_info = self.user_list.get(selected[0])
        username = user_info.split(" - ")[0]
        if username == "admin":
            messagebox.showerror("Error", "No se puede editar el usuario admin.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, email FROM usuarios WHERE username = ?", (username,))
        data = cursor.fetchone()
        conn.close()
        if not data:
            messagebox.showerror("Error", "No se encontró información del usuario.")
            return
        current_username, current_password, current_email = data
        new_username = simpledialog.askstring("Editar Usuario", "Nuevo username:", initialvalue=current_username, parent=self)
        new_password = simpledialog.askstring("Editar Usuario", "Nueva contraseña:", initialvalue=current_password, show="*", parent=self)
        new_email = simpledialog.askstring("Editar Usuario", "Nuevo email:", initialvalue=current_email, parent=self)
        if not (new_username and new_password and new_email):
            messagebox.showerror("Error", "Todos los campos son requeridos para editar el usuario.")
            return
        try:
            conn = sqlite3.connect("cultivos.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE usuarios SET username = ?, password = ?, email = ? WHERE username = ?",
                           (new_username, new_password, new_email, username))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Usuario actualizado correctamente.")
            self.refresh_user_list()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "El nuevo username ya existe.")

# -----------------------------
# Frame: Gestión de Hectáreas (solo para admin)
# -----------------------------
class GestionarHectareasFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#E8F0F7")
        self.controller = controller
        tk.Label(self, text="Gestionar Hectáreas", font=("Helvetica", 18, "bold"), fg="#333333", bg="#E8F0F7").pack(pady=20)
        self.hectareas_list = tk.Listbox(self, width=70, font=("Helvetica", 12))
        self.hectareas_list.pack(fill="both", expand=True, pady=10)
        self.refresh_hectareas()
        tk.Button(self, text="Editar Seleccionada", font=("Helvetica", 12), command=self.edit_hectarea).pack(pady=5)
        tk.Button(self, text="Eliminar Seleccionada", font=("Helvetica", 12), command=self.delete_hectarea).pack(pady=5)
        tk.Button(self, text="Volver", font=("Helvetica", 12), command=lambda: self.controller.show_frame(CultivosMainFrame)).pack(pady=10)
    
    def refresh_hectareas(self):
        self.hectareas_list.delete(0, tk.END)
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT numero, tipo_de_cultivo, siembra, primera_cosecha, cosecha_rutinaria, tipo_suelo, temperatura FROM hectareas")
        hectareas = cursor.fetchall()
        conn.close()
        for h in hectareas:
            self.hectareas_list.insert(tk.END, f"N° {h[0]}: {h[1]} | Siembra: {h[2]} | 1ra: {h[3]} | Rutinaria: {h[4]} | Suelo: {h[5]} | Temp: {h[6]}")
    
    def delete_hectarea(self):
        selected = self.hectareas_list.curselection()
        if not selected:
            messagebox.showerror("Error", "Seleccione una hectárea para eliminar.")
            return
        line = self.hectareas_list.get(selected[0])
        numero = int(line.split(":")[0].replace("N°", "").strip())
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la hectárea {numero}?"):
            Hectarea.eliminar(numero)
            messagebox.showinfo("Éxito", "Hectárea eliminada.")
            self.refresh_hectareas()
    
    def edit_hectarea(self):
        selected = self.hectareas_list.curselection()
        if not selected:
            messagebox.showerror("Error", "Seleccione una hectárea para editar.")
            return
        line = self.hectareas_list.get(selected[0])
        numero = int(line.split(":")[0].replace("N°", "").strip())
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT tipo_de_cultivo, siembra, primera_cosecha, cosecha_rutinaria, tipo_suelo, temperatura FROM hectareas WHERE numero = ?", (numero,))
        data = cursor.fetchone()
        conn.close()
        if not data:
            messagebox.showerror("Error", "No se encontraron datos para la hectárea seleccionada.")
            return
        tipo_actual, siembra_actual, primera_actual, rutinaria_actual, suelo_actual, temperatura_actual = data
        new_tipo = simpledialog.askstring("Editar", "Nuevo tipo de cultivo:", initialvalue=tipo_actual, parent=self)
        new_siembra = simpledialog.askstring("Editar", "Nueva fecha de siembra (YYYY-MM-DD):", initialvalue=siembra_actual, parent=self)
        new_primera = simpledialog.askstring("Editar", "Nueva fecha de primera cosecha (YYYY-MM-DD):", initialvalue=primera_actual, parent=self)
        new_rutinaria = simpledialog.askstring("Editar", "Nueva cosecha rutinaria:", initialvalue=rutinaria_actual, parent=self)
        new_suelo = simpledialog.askstring("Editar", "Nuevo tipo de suelo:", initialvalue=suelo_actual, parent=self)
        new_temp = simpledialog.askstring("Editar", "Nueva temperatura (°C):", initialvalue=str(temperatura_actual) if temperatura_actual is not None else "", parent=self)
        if not (new_tipo and new_siembra and new_primera and new_rutinaria and new_suelo):
            messagebox.showerror("Error", "Todos los campos (excepto temperatura) son requeridos para editar.")
            return
        try:
            Hectarea.actualizar(numero, new_tipo, new_siembra, new_primera, new_rutinaria, new_suelo, new_temp)
            messagebox.showinfo("Éxito", "Hectárea actualizada.")
            self.refresh_hectareas()
        except Exception as e:
            messagebox.showerror("Error", str(e))

# -----------------------------
# Frame: Perfil (datos del usuario logueado)
# -----------------------------
class PerfilFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        tk.Label(self, text="Perfil de Usuario", font=("Helvetica", 18, "bold"), fg="#333333").pack(pady=20)
        self.info_label = tk.Label(self, text="", font=("Helvetica", 14))
        self.info_label.pack(pady=10)
        tk.Button(self, text="Volver", font=("Helvetica", 12), command=lambda: controller.show_frame(CultivosMainFrame)).pack(pady=10)
    
    def cargar_perfil(self):
        user = self.controller.current_user
        email = self.controller.current_email
        role = self.controller.user_role
        self.info_label.config(text=f"Usuario: {user}\nEmail: {email}\nRol: {role}")

# -----------------------------
# Frame: Informe de Gestión Cultivo
# -----------------------------
class InformeGestionCultivoFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        tk.Label(self, text="Informe de Gestión Cultivo", font=("Helvetica", 18, "bold"), fg="#333333").pack(pady=20)
        self.informe_text = tk.Text(self, wrap="word", font=("Helvetica", 12))
        self.informe_text.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Button(self, text="Volver", font=("Helvetica", 12), command=lambda: controller.show_frame(CultivosMainFrame)).pack(pady=10)
    
    def cargar_informe(self):
        self.informe_text.delete("1.0", tk.END)
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
            for r in registros:
                self.informe_text.insert(tk.END, f"Código: {r[0]}\nUsuario: {r[1]}\nTipo Hortaliza: {r[2]}\nTipo Suelo: {r[3]}\nClima: {r[4]}\nVideo: {r[5]}\nObservaciones: {r[6]}\n{'-'*40}\n")
        else:
            self.informe_text.insert(tk.END, "No hay registros de gestión cultivo.")

# -----------------------------
# Frame: Consulta sobre Tipo de Cultivo
# -----------------------------
class ConsultaCultivoFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        tk.Label(self, text="Consulta Tipo de Cultivo", font=("Helvetica", 18, "bold"), fg="#333333").pack(pady=20)
        tk.Label(self, text="Ingrese el nombre del tipo de hortaliza:", font=("Helvetica", 12)).pack(pady=5)
        self.consulta_entry = tk.Entry(self, font=("Helvetica", 12))
        self.consulta_entry.pack(pady=5)
        tk.Button(self, text="Buscar", font=("Helvetica", 12), command=self.buscar_tipo).pack(pady=5)
        self.result_text = tk.Text(self, wrap="word", font=("Helvetica", 12))
        self.result_text.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Button(self, text="Volver", font=("Helvetica", 12), command=lambda: controller.show_frame(CultivosMainFrame)).pack(pady=10)
    
    def cargar_consulta(self):
        self.consulta_entry.delete(0, tk.END)
        self.result_text.delete("1.0", tk.END)
    
    def buscar_tipo(self):
        nombre = self.consulta_entry.get().strip()
        if not nombre:
            messagebox.showerror("Error", "Ingrese un nombre para consultar.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, nombre, descripcion, imagen FROM tipo_hortaliza WHERE nombre LIKE ?", ('%' + nombre + '%',))
        registros = cursor.fetchall()
        conn.close()
        self.result_text.delete("1.0", tk.END)
        if registros:
            for r in registros:
                self.result_text.insert(tk.END, f"Código: {r[0]}\nNombre: {r[1]}\nDescripción: {r[2]}\nImagen: {r[3]}\n{'-'*30}\n")
        else:
            self.result_text.insert(tk.END, "No se encontró el tipo de cultivo.")

# -----------------------------
# Frame: Interfaz Principal de Cultivos
# -----------------------------
class CultivosMainFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        header_frame = tk.Frame(self)
        header_frame.pack(side="top", fill="x", pady=10)
        self.header_label = tk.Label(header_frame, text="", font=("Helvetica", 16, "bold"), fg="#333333")
        self.header_label.pack(side="left")
        self.email_label = tk.Label(header_frame, text="")
        
        self.menu_frame = tk.Frame(self)
        self.menu_frame.pack(side="top", fill="x", pady=10)
        
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.show_mostrar_view()
    
    def refresh_menu(self):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        tk.Button(self.menu_frame, text="Registrar Hectárea", font=("Helvetica", 12), command=self.show_registrar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Mostrar Hectáreas", font=("Helvetica", 12), command=self.show_mostrar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Buscar Hectárea", font=("Helvetica", 12), command=self.show_buscar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Perfil", font=("Helvetica", 12), command=lambda: self.controller.show_frame(PerfilFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Informe Cultivo", font=("Helvetica", 12), command=lambda: self.controller.show_frame(InformeGestionCultivoFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Consulta Cultivo", font=("Helvetica", 12), command=lambda: self.controller.show_frame(ConsultaCultivoFrame)).pack(side="left", padx=5)
        if self.controller.user_role == "admin":
            tk.Button(self.menu_frame, text="Gestionar Hectáreas", font=("Helvetica", 12), command=lambda: self.controller.show_frame(GestionarHectareasFrame)).pack(side="left", padx=5)
            tk.Button(self.menu_frame, text="Gestión Cultivo", font=("Helvetica", 12), command=lambda: self.controller.show_frame(GestionCultivoFrame)).pack(side="left", padx=5)
            tk.Button(self.menu_frame, text="Gestionar Usuarios", font=("Helvetica", 12), command=lambda: self.controller.show_frame(UserManagementFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Logout", font=("Helvetica", 12), command=lambda: self.controller.show_frame(LoginFrame)).pack(side="left", padx=5)
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_registrar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Registrar Hectárea", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        tk.Label(self.content_frame, text="Seleccione Tipo de Cultivo:", font=("Helvetica", 12), fg="#333333").pack()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM tipo_hortaliza")
        rows = cursor.fetchall()
        conn.close()
        if rows:
            crop_types = [r[0] for r in rows]
        else:
            crop_types = ["limones", "maíz", "trigo", "tomate"]
        self.selected_crop_type = tk.StringVar(value=crop_types[0])
        crop_frame = tk.Frame(self.content_frame)
        crop_frame.pack(pady=5)
        for crop in crop_types:
            tk.Radiobutton(crop_frame, text=crop, variable=self.selected_crop_type, value=crop,
                           command=self.toggle_additional_fields, font=("Helvetica", 10)).pack(side="left", padx=5)
        tk.Label(self.content_frame, text="Fecha de Siembra (YYYY-MM-DD):", font=("Helvetica", 12), fg="#333333").pack()
        self.siembra_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.siembra_entry.pack(pady=5)
        # NUEVO: Seleccionar Tipo de Suelo
        tk.Label(self.content_frame, text="Seleccione Tipo de Suelo:", font=("Helvetica", 12), fg="#333333").pack()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM tipo_suelo")
        suelos = cursor.fetchall()
        conn.close()
        if suelos:
            suelo_types = [s[0] for s in suelos]
        else:
            suelo_types = ["Sin suelo registrado"]
        self.selected_suelo = tk.StringVar(value=suelo_types[0])
        tk.OptionMenu(self.content_frame, self.selected_suelo, *suelo_types).pack(pady=5)
        # NUEVO: Ingresar Temperatura
        tk.Label(self.content_frame, text="Temperatura (°C):", font=("Helvetica", 12), fg="#333333").pack()
        self.temperatura_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.temperatura_entry.pack(pady=5)
        
        self.additional_frame = tk.Frame(self.content_frame)
        self.additional_frame.pack(pady=5)
        tk.Label(self.additional_frame, text="Fecha de Primera Cosecha (YYYY-MM-DD):", font=("Helvetica", 10)).grid(row=0, column=0, padx=5, pady=5)
        self.primera_entry = tk.Entry(self.additional_frame, font=("Helvetica", 10))
        self.primera_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.additional_frame, text="Cosecha Rutinaria:", font=("Helvetica", 10)).grid(row=1, column=0, padx=5, pady=5)
        self.rutinaria_entry = tk.Entry(self.additional_frame, font=("Helvetica", 10))
        self.rutinaria_entry.grid(row=1, column=1, padx=5, pady=5)
        self.toggle_additional_fields()
        tk.Button(self.content_frame, text="Registrar", font=("Helvetica", 12), command=self.registrar_hectarea).pack(pady=10)
        tk.Button(self.content_frame, text="Volver", font=("Helvetica", 12), command=self.show_mostrar_view).pack(pady=5)
    
    def toggle_additional_fields(self):
        crop = self.selected_crop_type.get().lower()
        if crop == "limones":
            self.additional_frame.pack_forget()
        else:
            self.additional_frame.pack(pady=5)
    
    def registrar_hectarea(self):
        siembra = self.siembra_entry.get().strip()
        crop = self.selected_crop_type.get()
        if not siembra:
            messagebox.showerror("Error", "Ingrese la fecha de siembra.")
            return
        if crop.lower() != "limones":
            primera = self.primera_entry.get().strip()
            rutinaria = self.rutinaria_entry.get().strip()
            if not primera or not rutinaria:
                primera = None
                rutinaria = None
        else:
            primera = None
            rutinaria = None
        suelo = self.selected_suelo.get()
        temperatura = self.temperatura_entry.get().strip()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(numero) FROM hectareas")
        max_num = cursor.fetchone()[0]
        conn.close()
        numero = 1 if max_num is None else max_num + 1
        try:
            hectarea = Hectarea(numero, crop, siembra, primera, rutinaria, suelo, temperatura)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        hectarea.guardar_en_bd()
        messagebox.showinfo("Registro", "Hectárea registrada con éxito.")
        self.show_mostrar_view()
    
    def show_mostrar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Hectáreas Registradas", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        text_frame = tk.Frame(self.content_frame)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        v_scroll = tk.Scrollbar(text_frame, orient="vertical")
        h_scroll = tk.Scrollbar(text_frame, orient="horizontal")
        output = tk.Text(text_frame, wrap="none", yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set, font=("Courier New", 10))
        v_scroll.config(command=output.yview)
        h_scroll.config(command=output.xview)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        output.pack(side="left", fill="both", expand=True)
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hectareas")
        hectareas = cursor.fetchall()
        conn.close()
        if hectareas:
            for h in hectareas:
                output.insert(tk.END,
                              f"Hectárea {h[1]}:\n  Tipo: {h[2]}\n  Siembra: {h[3]}\n  1ra Cosecha: {h[4]}\n  Cosecha Rutinaria: {h[5]}\n  Tipo de Suelo: {h[6]}\n  Temperatura: {h[7]}\n\n")
        else:
            output.insert(tk.END, "No hay hectáreas registradas.")
        tk.Button(self.content_frame, text="Volver", font=("Helvetica", 12), command=self.show_mostrar_view).pack(pady=10)
    
    def show_buscar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Buscar Hectárea", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        tk.Label(self.content_frame, text="Número de Hectárea:", font=("Helvetica", 12)).pack()
        self.num_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.num_entry.pack(pady=5)
        result_frame = tk.Frame(self.content_frame)
        result_frame.pack(fill="both", expand=True, padx=10, pady=10)
        v_scroll_r = tk.Scrollbar(result_frame, orient="vertical")
        h_scroll_r = tk.Scrollbar(result_frame, orient="horizontal")
        self.result_text = tk.Text(result_frame, wrap="none", yscrollcommand=v_scroll_r.set, xscrollcommand=h_scroll_r.set, font=("Courier New", 10))
        v_scroll_r.config(command=self.result_text.yview)
        h_scroll_r.config(command=self.result_text.xview)
        v_scroll_r.pack(side="right", fill="y")
        h_scroll_r.pack(side="bottom", fill="x")
        self.result_text.pack(side="left", fill="both", expand=True)
        tk.Button(self.content_frame, text="Buscar", font=("Helvetica", 12), command=self.buscar_hectarea).pack(pady=5)
        tk.Button(self.content_frame, text="Volver", font=("Helvetica", 12), command=self.show_mostrar_view).pack(pady=5)
    
    def buscar_hectarea(self):
        num = self.num_entry.get().strip()
        if not num.isdigit():
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "Ingrese un número válido.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hectareas WHERE numero = ?", (int(num),))
        hectarea = cursor.fetchone()
        conn.close()
        self.result_text.delete("1.0", tk.END)
        if hectarea:
            self.result_text.insert(tk.END,
                                    f"Hectárea {hectarea[1]}:\n  Tipo: {hectarea[2]}\n  Siembra: {hectarea[3]}\n  1ra Cosecha: {hectarea[4]}\n  Cosecha Rutinaria: {hectarea[5]}\n  Tipo de Suelo: {hectarea[6]}\n  Temperatura: {hectarea[7]}\n")
        else:
            self.result_text.insert(tk.END, f"No se encontró la Hectárea {num}.")

# -----------------------------
# Frame: Consulta sobre Tipo de Cultivo
# -----------------------------
class ConsultaCultivoFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        tk.Label(self, text="Consulta Tipo de Cultivo", font=("Helvetica", 18, "bold"), fg="#333333").pack(pady=20)
        tk.Label(self, text="Ingrese el nombre del tipo de hortaliza:", font=("Helvetica", 12)).pack(pady=5)
        self.consulta_entry = tk.Entry(self, font=("Helvetica", 12))
        self.consulta_entry.pack(pady=5)
        tk.Button(self, text="Buscar", font=("Helvetica", 12), command=self.buscar_tipo).pack(pady=5)
        self.result_text = tk.Text(self, wrap="word", font=("Helvetica", 12))
        self.result_text.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Button(self, text="Volver", font=("Helvetica", 12), command=lambda: controller.show_frame(CultivosMainFrame)).pack(pady=10)
    
    def cargar_consulta(self):
        self.consulta_entry.delete(0, tk.END)
        self.result_text.delete("1.0", tk.END)
    
    def buscar_tipo(self):
        nombre = self.consulta_entry.get().strip()
        if not nombre:
            messagebox.showerror("Error", "Ingrese un nombre para consultar.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, nombre, descripcion, imagen FROM tipo_hortaliza WHERE nombre LIKE ?", ('%' + nombre + '%',))
        registros = cursor.fetchall()
        conn.close()
        self.result_text.delete("1.0", tk.END)
        if registros:
            for r in registros:
                self.result_text.insert(tk.END, f"Código: {r[0]}\nNombre: {r[1]}\nDescripción: {r[2]}\nImagen: {r[3]}\n{'-'*30}\n")
        else:
            self.result_text.insert(tk.END, "No se encontró el tipo de cultivo.")

# -----------------------------
# Frame: Login
# -----------------------------
class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        tk.Label(self, text="Acceso al Sistema de Cultivos", font=("Helvetica", 18, "bold"), fg="#333333").pack(pady=20)
        tk.Label(self, text="Seleccione un usuario:", font=("Helvetica", 14), fg="#333333").pack(pady=10)
        self.users_frame = tk.Frame(self)
        self.users_frame.pack()
        self.refresh_users()
        tk.Button(self, text="Recuperar Contraseña", font=("Helvetica", 12), command=self.recuperar_contrasena).pack(pady=10)
    
    def refresh_users(self):
        for widget in self.users_frame.winfo_children():
            widget.destroy()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM usuarios")
        users = [u[0] for u in cursor.fetchall()]
        conn.close()
        for username in users:
            tk.Button(self.users_frame, text=username, width=20, font=("Helvetica", 12),
                      command=lambda u=username: self.do_login(u)).pack(pady=5)
    
    def do_login(self, username):
        password = simpledialog.askstring("Contraseña", f"Ingrese la contraseña para {username}:", show="*", parent=self)
        if password is None:
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
            self.controller.show_frame(CultivosMainFrame)
        else:
            messagebox.showerror("Error", "Contraseña incorrecta.")
    
    def recuperar_contrasena(self):
        email = simpledialog.askstring("Recuperar Contraseña", "Ingrese su correo electrónico:", parent=self)
        if not email:
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM usuarios WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        if result:
            messagebox.showinfo("Recuperación", f"Usuario: {result[0]}\nContraseña: {result[1]}\n(Se simula envío de correo)")
        else:
            messagebox.showerror("Error", "No se encontró un usuario con ese correo.")

# -----------------------------
# Frame: Interfaz Principal de Cultivos
# -----------------------------
class CultivosMainFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        header_frame = tk.Frame(self)
        header_frame.pack(side="top", fill="x", pady=10)
        self.header_label = tk.Label(header_frame, text="", font=("Helvetica", 16, "bold"), fg="#333333")
        self.header_label.pack(side="left")
        self.email_label = tk.Label(header_frame, text="")
        
        self.menu_frame = tk.Frame(self)
        self.menu_frame.pack(side="top", fill="x", pady=10)
        
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.show_mostrar_view()
    
    def refresh_menu(self):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        tk.Button(self.menu_frame, text="Registrar Hectárea", font=("Helvetica", 12), command=self.show_registrar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Mostrar Hectáreas", font=("Helvetica", 12), command=self.show_mostrar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Buscar Hectárea", font=("Helvetica", 12), command=self.show_buscar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Perfil", font=("Helvetica", 12), command=lambda: self.controller.show_frame(PerfilFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Informe Cultivo", font=("Helvetica", 12), command=lambda: self.controller.show_frame(InformeGestionCultivoFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Consulta Cultivo", font=("Helvetica", 12), command=lambda: self.controller.show_frame(ConsultaCultivoFrame)).pack(side="left", padx=5)
        if self.controller.user_role == "admin":
            tk.Button(self.menu_frame, text="Gestionar Hectáreas", font=("Helvetica", 12), command=lambda: self.controller.show_frame(GestionarHectareasFrame)).pack(side="left", padx=5)
            tk.Button(self.menu_frame, text="Gestión Cultivo", font=("Helvetica", 12), command=lambda: self.controller.show_frame(GestionCultivoFrame)).pack(side="left", padx=5)
            tk.Button(self.menu_frame, text="Gestionar Usuarios", font=("Helvetica", 12), command=lambda: self.controller.show_frame(UserManagementFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Logout", font=("Helvetica", 12), command=lambda: self.controller.show_frame(LoginFrame)).pack(side="left", padx=5)
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_registrar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Registrar Hectárea", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        tk.Label(self.content_frame, text="Seleccione Tipo de Cultivo:", font=("Helvetica", 12), fg="#333333").pack()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM tipo_hortaliza")
        rows = cursor.fetchall()
        conn.close()
        if rows:
            crop_types = [r[0] for r in rows]
        else:
            crop_types = ["limones", "maíz", "trigo", "tomate"]
        self.selected_crop_type = tk.StringVar(value=crop_types[0])
        crop_frame = tk.Frame(self.content_frame)
        crop_frame.pack(pady=5)
        for crop in crop_types:
            tk.Radiobutton(crop_frame, text=crop, variable=self.selected_crop_type, value=crop,
                           command=self.toggle_additional_fields, font=("Helvetica", 10)).pack(side="left", padx=5)
        tk.Label(self.content_frame, text="Fecha de Siembra (YYYY-MM-DD):", font=("Helvetica", 12), fg="#333333").pack()
        self.siembra_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.siembra_entry.pack(pady=5)
        # NUEVO: Seleccionar Tipo de Suelo
        tk.Label(self.content_frame, text="Seleccione Tipo de Suelo:", font=("Helvetica", 12), fg="#333333").pack()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM tipo_suelo")
        suelos = cursor.fetchall()
        conn.close()
        if suelos:
            suelo_types = [s[0] for s in suelos]
        else:
            suelo_types = ["Sin suelo registrado"]
        self.selected_suelo = tk.StringVar(value=suelo_types[0])
        tk.OptionMenu(self.content_frame, self.selected_suelo, *suelo_types).pack(pady=5)
        # NUEVO: Ingresar Temperatura
        tk.Label(self.content_frame, text="Temperatura (°C):", font=("Helvetica", 12), fg="#333333").pack()
        self.temperatura_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.temperatura_entry.pack(pady=5)
        
        self.additional_frame = tk.Frame(self.content_frame)
        self.additional_frame.pack(pady=5)
        tk.Label(self.additional_frame, text="Fecha de Primera Cosecha (YYYY-MM-DD):", font=("Helvetica", 10)).grid(row=0, column=0, padx=5, pady=5)
        self.primera_entry = tk.Entry(self.additional_frame, font=("Helvetica", 10))
        self.primera_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.additional_frame, text="Cosecha Rutinaria:", font=("Helvetica", 10)).grid(row=1, column=0, padx=5, pady=5)
        self.rutinaria_entry = tk.Entry(self.additional_frame, font=("Helvetica", 10))
        self.rutinaria_entry.grid(row=1, column=1, padx=5, pady=5)
        self.toggle_additional_fields()
        tk.Button(self.content_frame, text="Registrar", font=("Helvetica", 12), command=self.registrar_hectarea).pack(pady=10)
        tk.Button(self.content_frame, text="Volver", font=("Helvetica", 12), command=self.show_mostrar_view).pack(pady=5)
    
    def toggle_additional_fields(self):
        crop = self.selected_crop_type.get().lower()
        if crop == "limones":
            self.additional_frame.pack_forget()
        else:
            self.additional_frame.pack(pady=5)
    
    def registrar_hectarea(self):
        siembra = self.siembra_entry.get().strip()
        crop = self.selected_crop_type.get()
        if not siembra:
            messagebox.showerror("Error", "Ingrese la fecha de siembra.")
            return
        if crop.lower() != "limones":
            primera = self.primera_entry.get().strip()
            rutinaria = self.rutinaria_entry.get().strip()
            if not primera or not rutinaria:
                primera = None
                rutinaria = None
        else:
            primera = None
            rutinaria = None
        suelo = self.selected_suelo.get()
        temperatura = self.temperatura_entry.get().strip()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(numero) FROM hectareas")
        max_num = cursor.fetchone()[0]
        conn.close()
        numero = 1 if max_num is None else max_num + 1
        try:
            hectarea = Hectarea(numero, crop, siembra, primera, rutinaria, suelo, temperatura)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        hectarea.guardar_en_bd()
        messagebox.showinfo("Registro", "Hectárea registrada con éxito.")
        self.show_mostrar_view()
    
    def show_mostrar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Hectáreas Registradas", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        text_frame = tk.Frame(self.content_frame)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        v_scroll = tk.Scrollbar(text_frame, orient="vertical")
        h_scroll = tk.Scrollbar(text_frame, orient="horizontal")
        output = tk.Text(text_frame, wrap="none", yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set, font=("Courier New", 10))
        v_scroll.config(command=output.yview)
        h_scroll.config(command=output.xview)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        output.pack(side="left", fill="both", expand=True)
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hectareas")
        hectareas = cursor.fetchall()
        conn.close()
        if hectareas:
            for h in hectareas:
                output.insert(tk.END,
                              f"Hectárea {h[1]}:\n  Tipo: {h[2]}\n  Siembra: {h[3]}\n  1ra Cosecha: {h[4]}\n  Cosecha Rutinaria: {h[5]}\n  Tipo de Suelo: {h[6]}\n  Temperatura: {h[7]}\n\n")
        else:
            output.insert(tk.END, "No hay hectáreas registradas.")
        tk.Button(self.content_frame, text="Volver", font=("Helvetica", 12), command=self.show_mostrar_view).pack(pady=10)
    
    def show_buscar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Buscar Hectárea", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        tk.Label(self.content_frame, text="Número de Hectárea:", font=("Helvetica", 12)).pack()
        self.num_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.num_entry.pack(pady=5)
        result_frame = tk.Frame(self.content_frame)
        result_frame.pack(fill="both", expand=True, padx=10, pady=10)
        v_scroll_r = tk.Scrollbar(result_frame, orient="vertical")
        h_scroll_r = tk.Scrollbar(result_frame, orient="horizontal")
        self.result_text = tk.Text(result_frame, wrap="none", yscrollcommand=v_scroll_r.set, xscrollcommand=h_scroll_r.set, font=("Courier New", 10))
        v_scroll_r.config(command=self.result_text.yview)
        h_scroll_r.config(command=self.result_text.xview)
        v_scroll_r.pack(side="right", fill="y")
        h_scroll_r.pack(side="bottom", fill="x")
        self.result_text.pack(side="left", fill="both", expand=True)
        tk.Button(self.content_frame, text="Buscar", font=("Helvetica", 12), command=self.buscar_hectarea).pack(pady=5)
        tk.Button(self.content_frame, text="Volver", font=("Helvetica", 12), command=self.show_mostrar_view).pack(pady=5)
    
    def buscar_hectarea(self):
        num = self.num_entry.get().strip()
        if not num.isdigit():
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "Ingrese un número válido.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hectareas WHERE numero = ?", (int(num),))
        hectarea = cursor.fetchone()
        conn.close()
        self.result_text.delete("1.0", tk.END)
        if hectarea:
            self.result_text.insert(tk.END,
                                    f"Hectárea {hectarea[1]}:\n  Tipo: {hectarea[2]}\n  Siembra: {hectarea[3]}\n  1ra Cosecha: {hectarea[4]}\n  Cosecha Rutinaria: {hectarea[5]}\n  Tipo de Suelo: {hectarea[6]}\n  Temperatura: {hectarea[7]}\n")
        else:
            self.result_text.insert(tk.END, f"No se encontró la Hectárea {num}.")

# -----------------------------
# Frame: Consulta sobre Tipo de Cultivo
# -----------------------------
class ConsultaCultivoFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        tk.Label(self, text="Consulta Tipo de Cultivo", font=("Helvetica", 18, "bold"), fg="#333333").pack(pady=20)
        tk.Label(self, text="Ingrese el nombre del tipo de hortaliza:", font=("Helvetica", 12)).pack(pady=5)
        self.consulta_entry = tk.Entry(self, font=("Helvetica", 12))
        self.consulta_entry.pack(pady=5)
        tk.Button(self, text="Buscar", font=("Helvetica", 12), command=self.buscar_tipo).pack(pady=5)
        self.result_text = tk.Text(self, wrap="word", font=("Helvetica", 12))
        self.result_text.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Button(self, text="Volver", font=("Helvetica", 12), command=lambda: controller.show_frame(CultivosMainFrame)).pack(pady=10)
    
    def cargar_consulta(self):
        self.consulta_entry.delete(0, tk.END)
        self.result_text.delete("1.0", tk.END)
    
    def buscar_tipo(self):
        nombre = self.consulta_entry.get().strip()
        if not nombre:
            messagebox.showerror("Error", "Ingrese un nombre para consultar.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT codigo, nombre, descripcion, imagen FROM tipo_hortaliza WHERE nombre LIKE ?", ('%' + nombre + '%',))
        registros = cursor.fetchall()
        conn.close()
        self.result_text.delete("1.0", tk.END)
        if registros:
            for r in registros:
                self.result_text.insert(tk.END, f"Código: {r[0]}\nNombre: {r[1]}\nDescripción: {r[2]}\nImagen: {r[3]}\n{'-'*30}\n")
        else:
            self.result_text.insert(tk.END, "No se encontró el tipo de cultivo.")

# -----------------------------
# Frame: Login
# -----------------------------
class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        tk.Label(self, text="Acceso al Sistema de Cultivos", font=("Helvetica", 18, "bold"), fg="#333333").pack(pady=20)
        tk.Label(self, text="Seleccione un usuario:", font=("Helvetica", 14), fg="#333333").pack(pady=10)
        self.users_frame = tk.Frame(self)
        self.users_frame.pack()
        self.refresh_users()
        tk.Button(self, text="Recuperar Contraseña", font=("Helvetica", 12), command=self.recuperar_contrasena).pack(pady=10)
    
    def refresh_users(self):
        for widget in self.users_frame.winfo_children():
            widget.destroy()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM usuarios")
        users = [u[0] for u in cursor.fetchall()]
        conn.close()
        for username in users:
            tk.Button(self.users_frame, text=username, width=20, font=("Helvetica", 12),
                      command=lambda u=username: self.do_login(u)).pack(pady=5)
    
    def do_login(self, username):
        password = simpledialog.askstring("Contraseña", f"Ingrese la contraseña para {username}:", show="*", parent=self)
        if password is None:
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
            self.controller.show_frame(CultivosMainFrame)
        else:
            messagebox.showerror("Error", "Contraseña incorrecta.")
    
    def recuperar_contrasena(self):
        email = simpledialog.askstring("Recuperar Contraseña", "Ingrese su correo electrónico:", parent=self)
        if not email:
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM usuarios WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        if result:
            messagebox.showinfo("Recuperación", f"Usuario: {result[0]}\nContraseña: {result[1]}\n(Se simula envío de correo)")
        else:
            messagebox.showerror("Error", "No se encontró un usuario con ese correo.")

# -----------------------------
# Frame: Interfaz Principal de Cultivos
# -----------------------------
class CultivosMainFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        header_frame = tk.Frame(self)
        header_frame.pack(side="top", fill="x", pady=10)
        self.header_label = tk.Label(header_frame, text="", font=("Helvetica", 16, "bold"), fg="#333333")
        self.header_label.pack(side="left")
        self.email_label = tk.Label(header_frame, text="")
        
        self.menu_frame = tk.Frame(self)
        self.menu_frame.pack(side="top", fill="x", pady=10)
        
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.show_mostrar_view()
    
    def refresh_menu(self):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        tk.Button(self.menu_frame, text="Registrar Hectárea", font=("Helvetica", 12), command=self.show_registrar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Mostrar Hectáreas", font=("Helvetica", 12), command=self.show_mostrar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Buscar Hectárea", font=("Helvetica", 12), command=self.show_buscar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Perfil", font=("Helvetica", 12), command=lambda: self.controller.show_frame(PerfilFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Informe Cultivo", font=("Helvetica", 12), command=lambda: self.controller.show_frame(InformeGestionCultivoFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Consulta Cultivo", font=("Helvetica", 12), command=lambda: self.controller.show_frame(ConsultaCultivoFrame)).pack(side="left", padx=5)
        if self.controller.user_role == "admin":
            tk.Button(self.menu_frame, text="Gestionar Hectáreas", font=("Helvetica", 12), command=lambda: self.controller.show_frame(GestionarHectareasFrame)).pack(side="left", padx=5)
            tk.Button(self.menu_frame, text="Gestión Cultivo", font=("Helvetica", 12), command=lambda: self.controller.show_frame(GestionCultivoFrame)).pack(side="left", padx=5)
            tk.Button(self.menu_frame, text="Gestionar Usuarios", font=("Helvetica", 12), command=lambda: self.controller.show_frame(UserManagementFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Logout", font=("Helvetica", 12), command=lambda: self.controller.show_frame(LoginFrame)).pack(side="left", padx=5)
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_mostrar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Hectáreas Registradas", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        text_frame = tk.Frame(self.content_frame)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        v_scroll = tk.Scrollbar(text_frame, orient="vertical")
        h_scroll = tk.Scrollbar(text_frame, orient="horizontal")
        output = tk.Text(text_frame, wrap="none", yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set, font=("Courier New", 10))
        v_scroll.config(command=output.yview)
        h_scroll.config(command=output.xview)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        output.pack(side="left", fill="both", expand=True)
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hectareas")
        hectareas = cursor.fetchall()
        conn.close()
        if hectareas:
            for h in hectareas:
                output.insert(tk.END,
                              f"Hectárea {h[1]}:\n  Tipo: {h[2]}\n  Siembra: {h[3]}\n  1ra Cosecha: {h[4]}\n  Cosecha Rutinaria: {h[5]}\n  Tipo de Suelo: {h[6]}\n  Temperatura: {h[7]}\n\n")
        else:
            output.insert(tk.END, "No hay hectáreas registradas.")
        tk.Button(self.content_frame, text="Volver", font=("Helvetica", 12), command=self.show_mostrar_view).pack(pady=10)
    
    def show_registrar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Registrar Hectárea", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        tk.Label(self.content_frame, text="Seleccione Tipo de Cultivo:", font=("Helvetica", 12), fg="#333333").pack()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM tipo_hortaliza")
        rows = cursor.fetchall()
        conn.close()
        if rows:
            crop_types = [r[0] for r in rows]
        else:
            crop_types = ["limones", "maíz", "trigo", "tomate"]
        self.selected_crop_type = tk.StringVar(value=crop_types[0])
        crop_frame = tk.Frame(self.content_frame)
        crop_frame.pack(pady=5)
        for crop in crop_types:
            tk.Radiobutton(crop_frame, text=crop, variable=self.selected_crop_type, value=crop,
                           command=self.toggle_additional_fields, font=("Helvetica", 10)).pack(side="left", padx=5)
        tk.Label(self.content_frame, text="Fecha de Siembra (YYYY-MM-DD):", font=("Helvetica", 12), fg="#333333").pack()
        self.siembra_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.siembra_entry.pack(pady=5)
        # NUEVO: Seleccionar Tipo de Suelo
        tk.Label(self.content_frame, text="Seleccione Tipo de Suelo:", font=("Helvetica", 12), fg="#333333").pack()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM tipo_suelo")
        suelos = cursor.fetchall()
        conn.close()
        if suelos:
            suelo_types = [s[0] for s in suelos]
        else:
            suelo_types = ["Sin suelo registrado"]
        self.selected_suelo = tk.StringVar(value=suelo_types[0])
        tk.OptionMenu(self.content_frame, self.selected_suelo, *suelo_types).pack(pady=5)
        # NUEVO: Ingresar Temperatura
        tk.Label(self.content_frame, text="Temperatura (°C):", font=("Helvetica", 12), fg="#333333").pack()
        self.temperatura_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.temperatura_entry.pack(pady=5)
        
        self.additional_frame = tk.Frame(self.content_frame)
        self.additional_frame.pack(pady=5)
        tk.Label(self.additional_frame, text="Fecha de Primera Cosecha (YYYY-MM-DD):", font=("Helvetica", 10)).grid(row=0, column=0, padx=5, pady=5)
        self.primera_entry = tk.Entry(self.additional_frame, font=("Helvetica", 10))
        self.primera_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.additional_frame, text="Cosecha Rutinaria:", font=("Helvetica", 10)).grid(row=1, column=0, padx=5, pady=5)
        self.rutinaria_entry = tk.Entry(self.additional_frame, font=("Helvetica", 10))
        self.rutinaria_entry.grid(row=1, column=1, padx=5, pady=5)
        self.toggle_additional_fields()
        tk.Button(self.content_frame, text="Registrar", font=("Helvetica", 12), command=self.registrar_hectarea).pack(pady=10)
        tk.Button(self.content_frame, text="Volver", font=("Helvetica", 12), command=self.show_mostrar_view).pack(pady=5)
    
    def toggle_additional_fields(self):
        crop = self.selected_crop_type.get().lower()
        if crop == "limones":
            self.additional_frame.pack_forget()
        else:
            self.additional_frame.pack(pady=5)
    
    def registrar_hectarea(self):
        siembra = self.siembra_entry.get().strip()
        crop = self.selected_crop_type.get()
        if not siembra:
            messagebox.showerror("Error", "Ingrese la fecha de siembra.")
            return
        if crop.lower() != "limones":
            primera = self.primera_entry.get().strip()
            rutinaria = self.rutinaria_entry.get().strip()
            if not primera or not rutinaria:
                primera = None
                rutinaria = None
        else:
            primera = None
            rutinaria = None
        suelo = self.selected_suelo.get()
        temperatura = self.temperatura_entry.get().strip()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(numero) FROM hectareas")
        max_num = cursor.fetchone()[0]
        conn.close()
        numero = 1 if max_num is None else max_num + 1
        try:
            hectarea = Hectarea(numero, crop, siembra, primera, rutinaria, suelo, temperatura)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        hectarea.guardar_en_bd()
        messagebox.showinfo("Registro", "Hectárea registrada con éxito.")
        self.show_mostrar_view()
    
    def show_buscar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Buscar Hectárea", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        tk.Label(self.content_frame, text="Número de Hectárea:", font=("Helvetica", 12)).pack()
        self.num_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.num_entry.pack(pady=5)
        result_frame = tk.Frame(self.content_frame)
        result_frame.pack(fill="both", expand=True, padx=10, pady=10)
        v_scroll_r = tk.Scrollbar(result_frame, orient="vertical")
        h_scroll_r = tk.Scrollbar(result_frame, orient="horizontal")
        self.result_text = tk.Text(result_frame, wrap="none", yscrollcommand=v_scroll_r.set, xscrollcommand=h_scroll_r.set, font=("Courier New", 10))
        v_scroll_r.config(command=self.result_text.yview)
        h_scroll_r.config(command=self.result_text.xview)
        v_scroll_r.pack(side="right", fill="y")
        h_scroll_r.pack(side="bottom", fill="x")
        self.result_text.pack(side="left", fill="both", expand=True)
        tk.Button(self.content_frame, text="Buscar", font=("Helvetica", 12), command=self.buscar_hectarea).pack(pady=5)
        tk.Button(self.content_frame, text="Volver", font=("Helvetica", 12), command=self.show_mostrar_view).pack(pady=5)
    
    def buscar_hectarea(self):
        num = self.num_entry.get().strip()
        if not num.isdigit():
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "Ingrese un número válido.")
            return
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hectareas WHERE numero = ?", (int(num),))
        hectarea = cursor.fetchone()
        conn.close()
        self.result_text.delete("1.0", tk.END)
        if hectarea:
            self.result_text.insert(tk.END,
                                    f"Hectárea {hectarea[1]}:\n  Tipo: {hectarea[2]}\n  Siembra: {hectarea[3]}\n  1ra Cosecha: {hectarea[4]}\n  Cosecha Rutinaria: {hectarea[5]}\n  Tipo de Suelo: {hectarea[6]}\n  Temperatura: {hectarea[7]}\n")
        else:
            self.result_text.insert(tk.END, f"No se encontró la Hectárea {num}.")

# -----------------------------
# Clase Aplicación
# -----------------------------
class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Sistema de Cultivos")
        self.geometry("690x500")
        self.resizable(True, True)
        
        self.bg_image = Image.open("background.jpg")
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.background_label = tk.Label(self, image=self.bg_photo)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.background_label.lower()
        
        self.current_user = None
        self.user_role = None
        self.current_email = None
        
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        self.frames = {}
        for F in (LoginFrame, CultivosMainFrame, UserManagementFrame, GestionarHectareasFrame,
                  PerfilFrame, GestionCultivoFrame, InformeGestionCultivoFrame, ConsultaCultivoFrame):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(LoginFrame)
    
    def show_frame(self, cont):
        frame = self.frames[cont]
        if cont == LoginFrame:
            frame.refresh_users()
        elif cont == CultivosMainFrame:
            frame.refresh_menu()
            if self.user_role == "usuario":
                frame.header_label.config(text=f"Bienvenido {self.current_user}", font=("Helvetica", 16))
                frame.email_label.config(text=f"({self.current_email})", font=("Helvetica", 10), fg="#555555")
                frame.email_label.pack(side="left", padx=5)
            else:
                frame.header_label.config(text=f"Bienvenido {self.current_user} ({self.user_role})", font=("Helvetica", 16))
                frame.email_label.forget()
        elif cont == GestionarHectareasFrame:
            frame.refresh_hectareas()
        elif cont == PerfilFrame:
            frame.cargar_perfil()
        elif cont == InformeGestionCultivoFrame:
            frame.cargar_informe()
        elif cont == ConsultaCultivoFrame:
            frame.cargar_consulta()
        frame.tkraise()

if __name__ == "__main__":
    app = Application()
    app.mainloop()
