import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import config            
from database import db  

class PestanaAgenda(tk.Frame):
    def __init__(self, parent):
        # Iniciamos el Frame usando el color de tu config
        super().__init__(parent, bg=config.COLOR_FONDO)
        
        # Al nacer esta clase, dibujamos la interfaz y cargamos las citas
        self.setup_ui()
        self.cargar_citas()

    def setup_ui(self):
        """ Aquí dibujamos todos los botones y tablas de la pestaña """
        
        f_left = tk.Frame(self, bg="#ecf0f1", width=300, padx=10, pady=10)
        f_left.pack(side="left", fill="y")
        
        tk.Label(f_left, text="NUEVA CITA", font=("Segoe UI", 14, "bold"), bg="#ecf0f1").pack(pady=10)
        
        tk.Label(f_left, text="Fecha (DD/MM/AAAA):", bg="#ecf0f1").pack(anchor="w")
        self.e_cita_fecha = tk.Entry(f_left, font=("Segoe UI", 11)); self.e_cita_fecha.pack(fill="x", pady=5)
        # Aquí cambiamos el orden para que por defecto ponga el Día primero
        self.e_cita_fecha.insert(0, (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y"))

        tk.Label(f_left, text="Hora:", bg="#ecf0f1").pack(anchor="w")
        horas = [f"{h:02d}:00" for h in range(8, 21)] + [f"{h:02d}:30" for h in range(8, 20)]; horas.sort()
        self.c_cita_hora = ttk.Combobox(f_left, values=horas, font=("Segoe UI", 11)); self.c_cita_hora.set("09:00"); self.c_cita_hora.pack(fill="x", pady=5)

        tk.Label(f_left, text="Paciente / Dueño:", bg="#ecf0f1").pack(anchor="w")
        self.e_cita_paciente = tk.Entry(f_left, font=("Segoe UI", 11)); self.e_cita_paciente.pack(fill="x", pady=5)

        tk.Label(f_left, text="Motivo:", bg="#ecf0f1").pack(anchor="w")
        self.e_cita_motivo = tk.Entry(f_left, font=("Segoe UI", 11)); self.e_cita_motivo.pack(fill="x", pady=5)
        
        tk.Button(f_left, text="📅 AGENDAR", bg="#27ae60", fg="white", font=("Segoe UI", 11, "bold"), command=self.agendar_cita).pack(pady=20, fill="x")
        tk.Button(f_left, text="🗑️ BORRAR", bg="#c0392b", fg="white", font=("Segoe UI", 11, "bold"), command=self.eliminar_cita).pack(side="bottom", fill="x", pady=20)

        f_right = tk.Frame(self, bg="#F4F6F7"); f_right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        f_filtros = tk.Frame(f_right, bg="#F4F6F7"); f_filtros.pack(fill="x", pady=5)
        
        def btn_f(txt, cmd): tk.Button(f_filtros, text=txt, command=cmd, bg="#BDC3C7", relief="flat").pack(side="left", padx=5)
        btn_f("HOY", lambda: self.filtrar_citas("hoy"))
        btn_f("MAÑANA", lambda: self.filtrar_citas("manana"))
        btn_f("TODO", lambda: self.filtrar_citas("todo"))

        cols = ("Fecha", "Hora", "Paciente", "Motivo")
        self.tree_citas = ttk.Treeview(f_right, columns=cols, show="headings")
        for col in cols:
            self.tree_citas.heading(col, text=col.upper())
            self.tree_citas.column(col, anchor="center")
        
        self.tree_citas.column("Paciente", width=250); self.tree_citas.column("Motivo", width=250)
        self.tree_citas.pack(fill="both", expand=True)
        self.tree_citas.tag_configure("hoy", background="#D1F2EB")


    # --- LÓGICA DE LA AGENDA ---
    
    def formatear_fecha_mx(self, fecha_iso):
        """ Esta función formatea la fecha para que se vea bonita en la pantalla """
        try:
            if not fecha_iso or fecha_iso == "N/A": return ""
            obj = datetime.strptime(fecha_iso, "%Y-%m-%d")
            return obj.strftime("%d/%m/%Y")
        except: return fecha_iso

    def agendar_cita(self):
        # 1. Obtenemos lo que el usuario escribió
        fecha_humano = self.e_cita_fecha.get().strip()
        h = self.c_cita_hora.get().strip()
        p = self.e_cita_paciente.get().strip()
        m = self.e_cita_motivo.get().strip()
        
        # 2. Revisamos si faltan datos
        if not fecha_humano or not h or not p: 
            messagebox.showwarning("!", "Faltan datos")
            return
            
        # --- EL TRADUCTOR ---
        try:
            # Intentamos voltear la fecha bonita al formato de la máquina
            f_maquina = datetime.strptime(fecha_humano, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            # Si el usuario escribió la fecha mal (ej. "hola" o "30-02-26"), lanzamos error
            messagebox.showerror("Error", "Formato de fecha incorrecto. Usa DD/MM/AAAA")
            return
            
        # 3. Abrimos la conexión
        conn = db.conectar() 
        cursor = conn.cursor()
        
        # 4. Revisamos si el horario está ocupado (¡Ojo! Aquí ya usamos f_maquina)
        cursor.execute("SELECT id FROM citas WHERE fecha=? AND hora=?", (f_maquina, h))
        if cursor.fetchone(): 
            conn.close() 
            messagebox.showerror("!", "Horario ocupado")
            return 
            
        # 5. Guardamos y cerramos (¡Usamos f_maquina!)
        cursor.execute("INSERT INTO citas (fecha, hora, paciente, motivo) VALUES (?,?,?,?)", (f_maquina, h, p, m))
        conn.commit()
        messagebox.showinfo("OK", "Cita agendada")
        self.cargar_citas()
        conn.close()

    def cargar_citas(self, filtro_sql=None, params=None):
        hoy_iso = datetime.now().strftime("%Y-%m-%d")
        
        conn = db.conectar()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM citas WHERE fecha < ?", (hoy_iso,))
        conn.commit()
        
        for i in self.tree_citas.get_children(): 
            self.tree_citas.delete(i)
            
        sql = "SELECT fecha, hora, paciente, motivo, id FROM citas " + (filtro_sql if filtro_sql else "") + " ORDER BY fecha ASC, hora ASC"
        cursor.execute(sql, params if params else ())
        
        for row in cursor.fetchall():
            vals = (self.formatear_fecha_mx(row[0]), row[1], row[2], row[3], row[4])
            item = self.tree_citas.insert("", "end", values=vals)
            if row[0] == hoy_iso: 
                self.tree_citas.item(item, tags=("hoy",))
                
        conn.close()
        
    def filtrar_citas(self, modo):
        hoy = datetime.now().strftime("%Y-%m-%d")
        if modo == "hoy": self.cargar_citas("WHERE fecha = ?", (hoy,))
        elif modo == "manana": self.cargar_citas("WHERE fecha = ?", ((datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),))
        else: self.cargar_citas("WHERE fecha >= ?", (hoy,))

    def eliminar_cita(self):
        sel = self.tree_citas.selection()
        if not sel: return
        
        # Primero abrimos la conexión
        conn = db.conectar() 
        cursor = conn.cursor()
        
        # Si el usuario dice que "sí" quiere borrar, borramos
        if messagebox.askyesno("Borrar", "¿Eliminar cita?"):
            cursor.execute("DELETE FROM citas WHERE id=?", (self.tree_citas.item(sel[0])["values"][4],))
            conn.commit()
            self.cargar_citas()
            
        # Siempre cerramos la conexión (haya dicho sí o no)
        conn.close()