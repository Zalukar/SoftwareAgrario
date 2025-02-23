import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta
from PIL import Image, ImageTk  # Requiere instalar Pillow (pip install Pillow)

# -----------------------------
# Configuración y Base de Datos
# -----------------------------
conn = sqlite3.connect("cultivos.db")
cursor = conn.cursor()

# Asegurar que la columna 'email' exista en la tabla usuarios
cursor.execute("PRAGMA table_info(usuarios)")
columns = [col[1] for col in cursor.fetchall()]
if "email" not in columns:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN email TEXT")

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT CHECK(role IN ('admin', 'usuario')),
    email TEXT
)
""")
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
# Por defecto, solo se inserta el usuario admin (sin correo)
cursor.execute("""
INSERT OR IGNORE INTO usuarios (username, password, role, email) VALUES
('admin', 'admin123', 'admin', NULL)
""")
conn.commit()
conn.close()

# -----------------------------
# Clase Hectarea (para el programa de cultivos)
# -----------------------------
class Hectarea:
    def __init__(self, numero, tipo_de_cultivo, siembra, primera_cosecha=None, cosecha_rutinaria=None):
        self.numero = numero
        self.tipo_de_cultivo = tipo_de_cultivo
        self.siembra = datetime.strptime(siembra, "%Y-%m-%d")
        if tipo_de_cultivo.lower() == "limones":
            self.primeracosecha = self.siembra.replace(year=self.siembra.year + 5)
            self.cosecha_rutinaria = (self.primeracosecha + timedelta(days=180)).strftime("%Y-%m-%d")
        else:
            self.primeracosecha = datetime.strptime(primera_cosecha, "%Y-%m-%d")
            self.cosecha_rutinaria = cosecha_rutinaria

    def guardar_en_bd(self):
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hectareas (numero, tipo_de_cultivo, siembra, primera_cosecha, cosecha_rutinaria) 
            VALUES (?, ?, ?, ?, ?)
        """, (self.numero, self.tipo_de_cultivo, self.siembra.strftime("%Y-%m-%d"), 
              self.primeracosecha.strftime("%Y-%m-%d"), self.cosecha_rutinaria))
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
    def actualizar(numero, tipo, siembra, primera, rutinaria):
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE hectareas 
            SET tipo_de_cultivo = ?, siembra = ?, primera_cosecha = ?, cosecha_rutinaria = ?
            WHERE numero = ?
        """, (tipo, siembra, primera, rutinaria, numero))
        conn.commit()
        conn.close()

# -----------------------------
# Aplicación con múltiples frames
# -----------------------------
class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Sistema de Cultivos")
        # Ventana 15% más ancha (600px -> 690px)
        self.geometry("690x500")
        self.resizable(True, True)
        
        # Imagen de fondo en la ventana raíz
        self.bg_image = Image.open("background.jpg")
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.background_label = tk.Label(self, image=self.bg_photo)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.background_label.lower()  # Envía la imagen al fondo
        
        # Variables para el usuario actual
        self.current_user = None
        self.user_role = None
        self.current_email = None  # Se guarda el correo para usuarios normales
        
        # Contenedor para los frames (sin color de fondo para que se vea la imagen)
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        self.frames = {}
        for F in (LoginFrame, CultivosMainFrame, UserManagementFrame, GestionarHectareasFrame):
            # No especificamos bg para que se herede el fondo (o se vea el fondo raíz)
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
        frame.tkraise()

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
    
    def refresh_users(self):
        for widget in self.users_frame.winfo_children():
            widget.destroy()
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM usuarios")
        users = [u[0] for u in cursor.fetchall()]
        conn.close()
        for username in users:
            tk.Button(self.users_frame, text=username, width=20,
                      font=("Helvetica", 12),
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

# -----------------------------
# Frame: Interfaz Principal de Cultivos
# -----------------------------
class CultivosMainFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        # Encabezado
        header_frame = tk.Frame(self)
        header_frame.pack(side="top", fill="x", pady=10)
        self.header_label = tk.Label(header_frame, text="", font=("Helvetica", 16, "bold"), fg="#333333")
        self.header_label.pack(side="left")
        self.email_label = tk.Label(header_frame, text="")
        
        # Menú de navegación
        self.menu_frame = tk.Frame(self)
        self.menu_frame.pack(side="top", fill="x", pady=10)
        
        # Área de contenido
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.show_mostrar_view()
    
    def refresh_menu(self):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        tk.Button(self.menu_frame, text="Registrar Hectárea", font=("Helvetica", 12), command=self.show_registrar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Mostrar Hectáreas", font=("Helvetica", 12), command=self.show_mostrar_view).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Buscar Hectárea", font=("Helvetica", 12), command=self.show_buscar_view).pack(side="left", padx=5)
        if self.controller.user_role == "admin":
            tk.Button(self.menu_frame, text="Gestionar Hectáreas", font=("Helvetica", 12), command=lambda: self.controller.show_frame(GestionarHectareasFrame)).pack(side="left", padx=5)
            tk.Button(self.menu_frame, text="Gestionar Usuarios", font=("Helvetica", 12), command=lambda: self.controller.show_frame(UserManagementFrame)).pack(side="left", padx=5)
        tk.Button(self.menu_frame, text="Logout", font=("Helvetica", 12), command=lambda: self.controller.show_frame(LoginFrame)).pack(side="left", padx=5)
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_registrar_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Registrar Hectárea", font=("Helvetica", 14, "bold"), fg="#333333").pack(pady=10)
        tk.Label(self.content_frame, text="Seleccione Tipo de Cultivo:", font=("Helvetica", 12), fg="#333333").pack()
        crop_types = ["Limones", "Maíz", "Trigo", "Tomate"]
        self.selected_crop_type = tk.StringVar(value=crop_types[0])
        crop_frame = tk.Frame(self.content_frame)
        crop_frame.pack(pady=5)
        for crop in crop_types:
            tk.Radiobutton(crop_frame, text=crop, variable=self.selected_crop_type, value=crop,
                           command=self.toggle_additional_fields,
                           font=("Helvetica", 10)).pack(side="left", padx=5)
        tk.Label(self.content_frame, text="Fecha de Siembra (YYYY-MM-DD):", font=("Helvetica", 12), fg="#333333").pack()
        self.siembra_entry = tk.Entry(self.content_frame, font=("Helvetica", 12))
        self.siembra_entry.pack(pady=5)
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
        crop = self.selected_crop_type.get()
        if crop.lower() == "limones":
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
                messagebox.showerror("Error", "Ingrese la fecha de primera cosecha y la cosecha rutinaria.")
                return
        else:
            primera = None
            rutinaria = None
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(numero) FROM hectareas")
        max_num = cursor.fetchone()[0]
        conn.close()
        numero = 1 if max_num is None else max_num + 1
        try:
            hectarea = Hectarea(numero, crop, siembra, primera, rutinaria)
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
        output = tk.Text(text_frame, wrap="none",
                         yscrollcommand=v_scroll.set,
                         xscrollcommand=h_scroll.set, font=("Courier New", 10))
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
                    f"Hectárea {h[1]}:\n"
                    f"  Tipo: {h[2]}\n"
                    f"  Siembra: {h[3]}\n"
                    f"  1ra Cosecha: {h[4]}\n"
                    f"  Cosecha Rutinaria: {h[5]}\n\n"
                )
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
        self.result_text = tk.Text(result_frame, wrap="none",
                                    yscrollcommand=v_scroll_r.set,
                                    xscrollcommand=h_scroll_r.set, font=("Courier New", 10))
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
                f"Hectárea {hectarea[1]}:\n"
                f"  Tipo: {hectarea[2]}\n"
                f"  Siembra: {hectarea[3]}\n"
                f"  1ra Cosecha: {hectarea[4]}\n"
                f"  Cosecha Rutinaria: {hectarea[5]}\n"
            )
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
        tk.Button(self, text="Volver", font=("Helvetica", 12),
                  command=lambda: self.controller.show_frame(CultivosMainFrame)).pack(pady=10)
    
    def refresh_hectareas(self):
        self.hectareas_list.delete(0, tk.END)
        conn = sqlite3.connect("cultivos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT numero, tipo_de_cultivo, siembra, primera_cosecha, cosecha_rutinaria FROM hectareas")
        hectareas = cursor.fetchall()
        conn.close()
        for h in hectareas:
            self.hectareas_list.insert(tk.END, f"N° {h[0]}: {h[1]} | Siembra: {h[2]} | 1ra: {h[3]} | Rutinaria: {h[4]}")
    
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
        cursor.execute("SELECT tipo_de_cultivo, siembra, primera_cosecha, cosecha_rutinaria FROM hectareas WHERE numero = ?", (numero,))
        data = cursor.fetchone()
        conn.close()
        if not data:
            messagebox.showerror("Error", "No se encontraron datos para la hectárea seleccionada.")
            return
        tipo_actual, siembra_actual, primera_actual, rutinaria_actual = data
        new_tipo = simpledialog.askstring("Editar", "Nuevo tipo de cultivo:", initialvalue=tipo_actual, parent=self)
        new_siembra = simpledialog.askstring("Editar", "Nueva fecha de siembra (YYYY-MM-DD):", initialvalue=siembra_actual, parent=self)
        new_primera = simpledialog.askstring("Editar", "Nueva fecha de primera cosecha (YYYY-MM-DD):", initialvalue=primera_actual, parent=self)
        new_rutinaria = simpledialog.askstring("Editar", "Nueva cosecha rutinaria:", initialvalue=rutinaria_actual, parent=self)
        if not (new_tipo and new_siembra and new_primera and new_rutinaria):
            messagebox.showerror("Error", "Todos los campos son requeridos para editar.")
            return
        try:
            Hectarea.actualizar(numero, new_tipo, new_siembra, new_primera, new_rutinaria)
            messagebox.showinfo("Éxito", "Hectárea actualizada.")
            self.refresh_hectareas()
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = Application()
    app.mainloop()
