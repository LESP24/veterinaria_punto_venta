import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import db
import config

# Importamos la ventana gigante de la Historia Clínica
from modulos.historial import VentanaConsultaMedica

class PestanaPacientes(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.COLOR_FONDO)
        self.setup_ui()
        self.buscar_pacientes()

    def setup_ui(self):
        # --- BARRA SUPERIOR DE BÚSQUEDA ---
        f_top = tk.Frame(self, bg="#F4F6F7", pady=10, padx=15)
        f_top.pack(fill="x")

        tk.Label(f_top, text="Buscar:", font=("Segoe UI", 10, "bold"), bg="#F4F6F7", fg="#2C3E50").pack(side="left")
        self.e_buscar = ttk.Entry(f_top, font=("Segoe UI", 11), width=40)
        self.e_buscar.pack(side="left", padx=10, fill="x", expand=True)
        self.e_buscar.bind("<KeyRelease>", lambda e: self.buscar_pacientes())

        tk.Button(f_top, text="🔍 BUSCAR", bg="#2980b9", fg="white", font=("Segoe UI", 9, "bold"), command=self.buscar_pacientes).pack(side="left", padx=5)
        tk.Button(f_top, text="➕ NUEVO PACIENTE", bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), command=self.nuevo_paciente).pack(side="left", padx=5)
        tk.Button(f_top, text="🗑️ ELIMINAR", bg="#e74c3c", fg="white", font=("Segoe UI", 9, "bold"), command=self.eliminar_paciente).pack(side="left", padx=5)

        # --- TABLA SUPERIOR (LISTA DE PACIENTES) ---
        f_tabla_pac = tk.Frame(self, bg="#F4F6F7", padx=15)
        f_tabla_pac.pack(fill="both", expand=True)

        cols_pac = ("ID", "Mascota", "Especie", "Raza", "Dueño", "Telefono")
        self.tree_pac = ttk.Treeview(f_tabla_pac, columns=cols_pac, show="headings", height=8, style="Premium.Treeview")

        for col in cols_pac:
            self.tree_pac.heading(col, text=col)
            self.tree_pac.column(col, anchor="center") 
        
        self.tree_pac.column("ID", width=50)
        self.tree_pac.column("Mascota", width=150)
        self.tree_pac.column("Dueño", width=200)

        self.tree_pac.pack(fill="both", expand=True)
        self.tree_pac.bind("<<TreeviewSelect>>", self.cargar_historial_paciente)

        # --- TABLA INFERIOR (HISTORIAL CLÍNICO) ---
        f_historial = tk.Frame(self, bg="#F4F6F7", padx=15, pady=10)
        f_historial.pack(fill="both", expand=True)

        tk.Label(f_historial, text="HISTORIAL CLÍNICO DEL PACIENTE (Consultas Anteriores):", font=("Segoe UI", 11, "bold"), bg="#F4F6F7", fg="#2C3E50").pack(pady=5, anchor="w")

        # Se agregó la columna ID_Consulta oculta para poder buscar los datos para imprimir
        cols_hist = ("ID_Consulta", "Fecha", "Motivo", "Diagnostico", "Peso", "Atendió")
        self.tree_hist = ttk.Treeview(f_historial, columns=cols_hist, show="headings", height=6)

        for col in cols_hist:
            self.tree_hist.heading(col, text=col)
            self.tree_hist.column(col, anchor="center")
        
        self.tree_hist.column("ID_Consulta", width=0, stretch=tk.NO) # Columna oculta
        self.tree_hist.column("Motivo", width=200)
        self.tree_hist.column("Diagnostico", width=250)

        self.tree_hist.pack(fill="both", expand=True)

        # --- BOTONES INFERIORES ---
        f_btn_bot = tk.Frame(self, bg="#F4F6F7", pady=10)
        f_btn_bot.pack(fill="x")
        
        tk.Button(f_btn_bot, text="📝 CREAR NUEVA CONSULTA (HOY)", bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"), pady=5, padx=15, command=self.abrir_nueva_consulta).pack(side="left", padx=20)
        tk.Button(f_btn_bot, text="🖨️ VER / IMPRIMIR CONSULTA SELECCIONADA", bg="#8e44ad", fg="white", font=("Segoe UI", 10, "bold"), pady=5, padx=15, command=self.imprimir_consulta).pack(side="right", padx=20)

    def buscar_pacientes(self):
        q = self.e_buscar.get().strip()
        self.tree_pac.delete(*self.tree_pac.get_children())
        
        conn = db.conectar(); cursor = conn.cursor()
        try:
            if q:
                cursor.execute("SELECT id, nombre, especie, raza, dueno, telefono FROM pacientes WHERE nombre LIKE ? OR dueno LIKE ?", (f"%{q}%", f"%{q}%"))
            else:
                cursor.execute("SELECT id, nombre, especie, raza, dueno, telefono FROM pacientes")
            
            for row in cursor.fetchall():
                self.tree_pac.insert("", "end", values=row)
        except:
            try:
                if q:
                    cursor.execute("SELECT id, nombre_mascota, especie, raza, nombre_dueno, telefono FROM pacientes WHERE nombre_mascota LIKE ? OR nombre_dueno LIKE ?", (f"%{q}%", f"%{q}%"))
                else:
                    cursor.execute("SELECT id, nombre_mascota, especie, raza, nombre_dueno, telefono FROM pacientes")
                for row in cursor.fetchall():
                    self.tree_pac.insert("", "end", values=row)
            except Exception as e:
                pass
        finally:
            conn.close()

        self.tree_hist.delete(*self.tree_hist.get_children())

    def cargar_historial_paciente(self, event=None):
        sel = self.tree_pac.selection()
        if not sel: return
        
        p_id = self.tree_pac.item(sel[0])["values"][0]
        self.tree_hist.delete(*self.tree_hist.get_children())
        
        conn = db.conectar(); cursor = conn.cursor()
        try:
            # Traemos el ID de la consulta (row[0]) para poder imprimirla después
            cursor.execute("SELECT id, fecha, motivo, diagnostico_definitivo, peso, vendedor_atiende FROM historial_clinico WHERE paciente_id=? ORDER BY id DESC", (p_id,))
            for row in cursor.fetchall():
                fecha_str = str(row[1])[:16] 
                peso_str = f"{row[4]} kg" if row[4] else "N/A"
                self.tree_hist.insert("", "end", values=(row[0], fecha_str, row[2], row[3], peso_str, row[5]))
        except Exception as e:
            pass
        conn.close()

    def nuevo_paciente(self):
        top = tk.Toplevel(self)
        top.title("Nuevo Paciente")
        top.geometry("400x400")
        top.configure(bg="#F4F6F7")
        top.grab_set()

        campos = ["Nombre Mascota:", "Especie (Perro/Gato):", "Raza:", "Nombre Dueño:", "Teléfono:"]
        entradas = {}
        for c in campos:
            tk.Label(top, text=c, bg="#F4F6F7", font=("Segoe UI", 9, "bold")).pack(pady=(10, 0))
            ent = tk.Entry(top, font=("Segoe UI", 10), width=35)
            ent.pack(pady=5)
            entradas[c] = ent

        def guardar():
            vals = [entradas[c].get().strip() for c in campos]
            if not vals[0] or not vals[3]:
                messagebox.showwarning("Atención", "El nombre de la mascota y del dueño son obligatorios.")
                return
            conn = db.conectar(); cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO pacientes (nombre, especie, raza, dueno, telefono) VALUES (?,?,?,?,?)", vals)
                conn.commit(); messagebox.showinfo("Éxito", "Paciente registrado.")
                top.destroy(); self.buscar_pacientes()
            except:
                try:
                    cursor.execute("INSERT INTO pacientes (nombre_mascota, especie, raza, nombre_dueno, telefono) VALUES (?,?,?,?,?)", vals)
                    conn.commit(); messagebox.showinfo("Éxito", "Paciente registrado.")
                    top.destroy(); self.buscar_pacientes()
                except Exception as e2:
                    messagebox.showerror("Error", f"No se pudo guardar: {e2}")
            conn.close()

        tk.Button(top, text="GUARDAR PACIENTE", bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"), command=guardar).pack(pady=20)

    def eliminar_paciente(self):
        sel = self.tree_pac.selection()
        if not sel: return messagebox.showwarning("Atención", "Seleccione un paciente de la lista.")
        
        p_id = self.tree_pac.item(sel[0])["values"][0]
        p_nom = self.tree_pac.item(sel[0])["values"][1]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar a {p_nom} y TODO su historial médico permanentemente?"):
            conn = db.conectar(); cursor = conn.cursor()
            try: cursor.execute("DELETE FROM historial_clinico WHERE paciente_id=?", (p_id,))
            except: pass
            try: cursor.execute("DELETE FROM pacientes WHERE id=?", (p_id,))
            except: pass
            conn.commit(); conn.close()
            self.buscar_pacientes()

    def abrir_nueva_consulta(self):
        sel = self.tree_pac.selection()
        if not sel: return messagebox.showwarning("Atención", "Seleccione un paciente de la lista de arriba para iniciar la consulta.")
            
        vals = self.tree_pac.item(sel[0])["values"]
        p_id = vals[0]
        p_nom = vals[1]
        
        # Abrimos la ventana de 4 páginas
        vent = VentanaConsultaMedica(self.winfo_toplevel(), p_id, p_nom, config.LISTA_VENDEDORES[0])
        self.wait_window(vent)
        
        # Al cerrar/guardar, refrescamos la tabla para que aparezca la nueva consulta
        self.cargar_historial_paciente()

    # --- NUEVA FUNCIÓN PARA IMPRIMIR CONSULTAS ANTERIORES ---
    def imprimir_consulta(self):
        sel_pac = self.tree_pac.selection()
        if not sel_pac: return messagebox.showwarning("Aviso", "Primero seleccione un paciente.")
        
        sel_hist = self.tree_hist.selection()
        if not sel_hist: return messagebox.showwarning("Aviso", "Seleccione una consulta de la tabla 'HISTORIAL CLÍNICO' para imprimir.")
        
        paciente_nom = self.tree_pac.item(sel_pac[0])["values"][1]
        dueno_nom = self.tree_pac.item(sel_pac[0])["values"][4]
        id_consulta = self.tree_hist.item(sel_hist[0])["values"][0]
        fecha_consulta = self.tree_hist.item(sel_hist[0])["values"][1]

        conn = db.conectar(); cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM historial_clinico WHERE id=?", (id_consulta,))
            row = cursor.fetchone()
            col_names = [desc[0] for desc in cursor.description]
        except Exception as e:
            conn.close()
            return messagebox.showerror("Error", f"No se pudo leer la consulta: {e}")
        conn.close()

        if not row: return

        # Construcción del reporte/ticket
        ticket = f"==================================================\n"
        ticket += f"       HOSPITAL VETERINARIO BEETHOVEN\n"
        ticket += f"             REPORTE CLÍNICO\n"
        ticket += f"==================================================\n"
        ticket += f" PACIENTE: {paciente_nom}\n"
        ticket += f" DUEÑO:    {dueno_nom}\n"
        ticket += f" FECHA:    {fecha_consulta}\n"
        ticket += f"==================================================\n\n"

        # Leemos todas las columnas de la base de datos mágicamente sin importar cuántas sean
        for nombre_col, valor in zip(col_names, row):
            if nombre_col.lower() in ['id', 'paciente_id', 'fecha']: continue # Nos saltamos las columnas técnicas
            if not valor or str(valor).strip() == "": continue # Nos saltamos lo que se dejó en blanco
            
            titulo_limpio = nombre_col.replace("_", " ").upper()
            ticket += f"[{titulo_limpio}]:\n"
            ticket += f"  {valor}\n\n"

        ticket += f"==================================================\n"
        ticket += f"               FIRMA DEL MÉDICO\n\n\n"
        ticket += f"            ______________________\n"

        # Crear carpeta de tickets si no existe
        if not os.path.exists("tickets"): os.makedirs("tickets")
            
        nombre_archivo = f"tickets/Consulta_{paciente_nom}_{str(id_consulta)}.txt"
        
        try:
            with open(nombre_archivo, "w", encoding="utf-8") as archivo:
                archivo.write(ticket)
            
            # Abre el bloc de notas para que tu papá lo vea y lo imprima si quiere
            os.startfile(nombre_archivo)
            messagebox.showinfo("Listo", "El expediente ha sido generado. Puedes imprimirlo desde la ventana que acaba de abrirse.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte: {e}")