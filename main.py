import tkinter as tk
from tkinter import ttk, messagebox
import config
from database import db
import uuid
import os
import hashlib

# --- IMPORTAMOS A TUS ESPECIALISTAS ---
from modulos.caja import PestanaCaja
from modulos.pacientes import PestanaPacientes
from modulos.inventario import PestanaInventario
from modulos.agenda import PestanaAgenda
from modulos.finanzas import PestanaFinanzas

class VeterinariaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CLÍNICA VETERINARIA BEETHOVEN - v38.0 (Paleta Profesional)")
        self.root.state('zoomed')
        self.root.configure(bg="#F4F6F7") 
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#F4F6F7")
        style.configure("TLabel", background="#F4F6F7", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 9, "bold"), cursor="hand2")
        
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30, background="white", fieldbackground="white", foreground="#2C3E50")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#2C3E50", foreground="white", relief="flat")
        style.map("Treeview.Heading", background=[('active', '#34495E')])
        style.map("Treeview", background=[('selected', '#455A64')], foreground=[('selected', 'white')])

        self.machine_uuid = str(uuid.getnode())

        if not self.verificar_licencia():
            self.mostrar_ventana_activacion()
            return

        db.inicializa_db()
        self.setup_gui()

    # --- SEGURIDAD ---
    def verificar_licencia(self):
        if os.path.exists("licencia.dat"):
            try:
                with open("licencia.dat", "r") as f: stored_key = f.read().strip()
                combined = self.machine_uuid + config.SECRET_KEY
                hash_obj = hashlib.sha256(combined.encode('utf-8'))
                hash_hex = hash_obj.hexdigest()[:16]
                formatted = '-'.join([hash_hex[i:i+4] for i in range(0, 16, 4)])
                return stored_key == formatted
            except: return False
        return False

    def mostrar_ventana_activacion(self):
        activation_win = tk.Toplevel(self.root)
        activation_win.title("ACTIVACIÓN")
        activation_win.geometry("500x300")
        activation_win.configure(bg="#2c3e50")
        tk.Label(activation_win, text="ID SISTEMA:", font=("Arial", 14), bg="#2c3e50", fg="white").pack(pady=10)
        entry_uuid = tk.Entry(activation_win, font=("Arial", 14), justify="center")
        entry_uuid.insert(0, self.machine_uuid)
        entry_uuid.pack(pady=5)
        tk.Label(activation_win, text="LICENCIA:", font=("Arial", 14), bg="#2c3e50", fg="white").pack(pady=10)
        license_entry = tk.Entry(activation_win, font=("Arial", 14), justify="center")
        license_entry.pack(pady=5)
        
        def activar():
            entered_key = license_entry.get().strip()
            combined = self.machine_uuid + config.SECRET_KEY
            hash_obj = hashlib.sha256(combined.encode('utf-8'))
            hash_hex = hash_obj.hexdigest()[:16]
            expected = '-'.join([hash_hex[i:i+4] for i in range(0, 16, 4)])
            
            if entered_key == expected:
                with open("licencia.dat", "w") as f: f.write(entered_key)
                messagebox.showinfo("Éxito", "Activado.")
                activation_win.destroy()
                db.inicializa_db()
                self.setup_gui()
            else: messagebox.showerror("Error", "Licencia Inválida.")

        tk.Button(activation_win, text="ACTIVAR", command=activar, bg="#27ae60", fg="white").pack(pady=20)


    # --- GUI PRINCIPAL (EL DIRECTOR TÉCNICO) ---
    def setup_gui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # CADA PESTAÑA AHORA ES UN MÓDULO INDEPENDIENTE
        self.tab_caja = PestanaCaja(self.notebook)
        self.tab_pacientes = PestanaPacientes(self.notebook)
        self.tab_inventario = PestanaInventario(self.notebook)
        self.tab_agenda = PestanaAgenda(self.notebook)
        self.tab_finanzas = PestanaFinanzas(self.notebook)

        self.notebook.add(self.tab_caja, text=" 🛒 CAJA ")
        self.notebook.add(self.tab_pacientes, text=" 🐶 PACIENTES ")
        self.notebook.add(self.tab_inventario, text=" 📦 INVENTARIO ")
        self.notebook.add(self.tab_agenda, text=" 📅 AGENDA ")
        self.notebook.add(self.tab_finanzas, text=" 💰 FINANZAS ")

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event):
        selected_tab = self.notebook.index(self.notebook.select())
        tab_text = self.notebook.tab(selected_tab, "text").strip()
        
        # EL DT AHORA SOLO DELEGA LAS TAREAS
        if "INVENTARIO" in tab_text: self.tab_inventario.cargar_inventario_completo()
        elif "FINANZAS" in tab_text: 
            self.tab_finanzas.cargar_fechas_historial()
            self.tab_finanzas.cargar_finanzas()
        elif "AGENDA" in tab_text: self.tab_agenda.cargar_citas()
        elif "PACIENTES" in tab_text: self.tab_pacientes.buscar_pacientes()

if __name__ == "__main__":
    root = tk.Tk()
    app = VeterinariaApp(root)
    root.mainloop()