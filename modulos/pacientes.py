import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import config
from database import db

class PestanaPacientes(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.COLOR_FONDO)
        self.setup_ui()
        self.buscar_pacientes() # Cargamos la lista al iniciar

    def setup_ui(self):
        # --- ESTE ES EL DISEÑO REAL DE LA PESTAÑA ---
        # (Fíjate cómo todo dice 'self' como papá, no 'self.tab_pacientes')
        
        f_bus = tk.Frame(self, bg="#F4F6F7", pady=10)
        f_bus.pack(fill="x", padx=10)
        
        tk.Label(f_bus, text="Buscar:", bg="#F4F6F7").pack(side="left")
        self.e_buscar_pac = tk.Entry(f_bus)
        self.e_buscar_pac.pack(side="left", fill="x", expand=True, padx=5)
        
        tk.Button(f_bus, text="BUSCAR", command=self.buscar_pacientes, bg="#3498db", fg="white").pack(side="left")
        tk.Button(f_bus, text="NUEVO PACIENTE", command=self.agregar_paciente, bg="#27ae60", fg="white").pack(side="left", padx=5)

        self.tree_pacientes = ttk.Treeview(self, columns=("ID", "Nom", "Esp", "Raz", "Due", "Tel"), show="headings", height=8)
        for c in ("ID", "Nom", "Esp", "Raz", "Due", "Tel"): 
            self.tree_pacientes.heading(c, text=c)
            self.tree_pacientes.column(c, anchor="center")
            
        self.tree_pacientes.pack(fill="x", padx=10)
        self.tree_pacientes.bind("<<TreeviewSelect>>", self.mostrar_historial)

        tk.Label(self, text="HISTORIAL CLÍNICO:", bg="#F4F6F7", font=("Segoe UI", 12, "bold")).pack(pady=(10,0))
        
        self.tree_hist = ttk.Treeview(self, columns=("Fecha", "Mot", "Diag", "Peso"), show="headings")
        for c in ("Fecha", "Mot", "Diag", "Peso"): 
            self.tree_hist.heading(c, text=c)
            self.tree_hist.column(c, anchor="center")
            
        self.tree_hist.column("Diag", width=300)
        self.tree_hist.pack(fill="both", expand=True, padx=10, pady=5)
        
        tk.Button(self, text="+ NUEVA CONSULTA", command=self.nueva_consulta, bg="#2980b9", fg="white").pack(pady=10)

    # --- UTILIDADES ---
    def formatear_fecha_mx(self, fecha_iso):
        """Necesitamos esta función aquí también para que las fechas del historial se vean bien"""
        try:
            if not fecha_iso or fecha_iso == "N/A": return ""
            obj = datetime.strptime(fecha_iso, "%Y-%m-%d")
            return obj.strftime("%d/%m/%Y")
        except: return fecha_iso

    # --- FUNCIONES DE BASE DE DATOS ---

    def agregar_paciente(self):
        # SOLUCIÓN AL ERROR 3: Usamos winfo_toplevel() para que la ventana salga por encima
        w = tk.Toplevel(self.winfo_toplevel()) 
        w.title("Nuevo")
        w.geometry("300x400")
        
        tk.Label(w, text="Nombre:").pack(); e_nm = tk.Entry(w); e_nm.pack()
        tk.Label(w, text="Especie:").pack(); e_sp = ttk.Combobox(w, values=["Perro", "Gato"]); e_sp.pack()
        tk.Label(w, text="Raza:").pack(); e_rz = tk.Entry(w); e_rz.pack()
        tk.Label(w, text="Dueño:").pack(); e_du = tk.Entry(w); e_du.pack()
        tk.Label(w, text="Tel:").pack(); e_tl = tk.Entry(w); e_tl.pack()
        
        def save():
            conn = db.conectar() # Abrimos puerta
            cursor = conn.cursor()
            
            cursor.execute("INSERT INTO pacientes (nombre, especie, raza, dueno, telefono, fecha_registro) VALUES (?,?,?,?,?,?)", 
                           (e_nm.get(), e_sp.get(), e_rz.get(), e_du.get(), e_tl.get(), datetime.now().strftime("%Y-%m-%d")))
            
            conn.commit() # Guardamos cambios
            conn.close()  # Cerramos puerta
            
            w.destroy()
            self.buscar_pacientes() # Refrescamos la tabla
            
        tk.Button(w, text="GUARDAR", command=save, bg="#27ae60", fg="white").pack(pady=20)

    def buscar_pacientes(self):
        # Esta función corre al iniciar, por eso debe abrir y cerrar la base de datos limpio.
        q = ""
        # Revisamos si la cajita de búsqueda ya existe (porque esto corre al iniciar la app)
        if hasattr(self, 'e_buscar_pac'):
            q = self.e_buscar_pac.get()
            
        self.tree_pacientes.delete(*self.tree_pacientes.get_children())
        
        conn = db.conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, nombre, especie, raza, dueno, telefono FROM pacientes WHERE nombre LIKE ? OR dueno LIKE ?", (f"%{q}%", f"%{q}%"))
        
        for r in cursor.fetchall(): 
            self.tree_pacientes.insert("", "end", values=r)
            
        conn.close()

    def mostrar_historial(self, event):
        sel = self.tree_pacientes.selection()
        if not sel: return
        
        self.tree_hist.delete(*self.tree_hist.get_children())
        paciente_id = self.tree_pacientes.item(sel[0])["values"][0]
        
        conn = db.conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT fecha, motivo, diagnostico, peso FROM historial_clinico WHERE paciente_id=? ORDER BY fecha DESC", (paciente_id,))
        
        for r in cursor.fetchall(): 
            self.tree_hist.insert("", "end", values=(self.formatear_fecha_mx(r[0].split()[0]), r[1], r[2], r[3]))
            
        conn.close()

    def nueva_consulta(self):
        sel = self.tree_pacientes.selection()
        if not sel: return
        
        pid = self.tree_pacientes.item(sel[0])["values"][0]
        
        # SOLUCIÓN AL ERROR 3: winfo_toplevel()
        w = tk.Toplevel(self.winfo_toplevel()) 
        w.title("Consulta")
        
        tk.Label(w, text="Motivo:").pack(); e_mot = tk.Entry(w); e_mot.pack()
        tk.Label(w, text="Diagnóstico:").pack(); t_dia = tk.Text(w, height=5); t_dia.pack()
        tk.Label(w, text="Peso:").pack(); e_pes = tk.Entry(w); e_pes.pack()
        
        def save():
            conn = db.conectar()
            cursor = conn.cursor()
            
            cursor.execute("INSERT INTO historial_clinico (paciente_id, fecha, motivo, diagnostico, peso) VALUES (?,?,?,?,?)", 
                           (pid, datetime.now().strftime("%Y-%m-%d %H:%M"), e_mot.get(), t_dia.get("1.0", tk.END), e_pes.get()))
            conn.commit()
            conn.close()
            
            w.destroy()
            self.mostrar_historial(None) # Refrescamos la tablita de abajo
            
        tk.Button(w, text="GUARDAR", command=save, bg="#2980b9", fg="white").pack(pady=10)