import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import config            
from database import db  
import webbrowser
import urllib.parse

class PestanaAgenda(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.COLOR_FONDO)
        self.verificar_tablas()
        self.setup_ui()
        self.cargar_citas()
        self.cargar_pendientes()

    def verificar_tablas(self):
        conn = db.conectar()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT, hora TEXT, paciente TEXT, motivo TEXT, atiende TEXT
            )
        """)
        try: conn.execute("ALTER TABLE citas ADD COLUMN atiende TEXT DEFAULT 'General'")
        except: pass
        try: conn.execute("ALTER TABLE citas ADD COLUMN telefono TEXT DEFAULT ''")
        except: pass
        try: conn.execute("ALTER TABLE citas ADD COLUMN estado TEXT DEFAULT 'PENDIENTE'")
        except: pass
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pendientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT, fecha_creacion TEXT, estado TEXT DEFAULT 'PENDIENTE'
            )
        """)
        conn.commit(); conn.close()

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"))
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_citas = tk.Frame(self.notebook, bg="#ecf0f1")
        self.notebook.add(self.tab_citas, text=" 📅 AGENDA DE CITAS ")

        self.tab_pendientes = tk.Frame(self.notebook, bg="#ecf0f1")
        self.notebook.add(self.tab_pendientes, text=" 📌 LISTA DE PENDIENTES (Tareas) ")

        self.construir_pestaña_citas()
        self.construir_pestaña_pendientes()

    def construir_pestaña_citas(self):
        f_left = tk.Frame(self.tab_citas, bg="#ecf0f1", width=320, padx=20, pady=20)
        f_left.pack(side="left", fill="y")
        f_left.pack_propagate(False)

        tk.Label(f_left, text="📅 NUEVA CITA", font=("Segoe UI", 14, "bold"), bg="#ecf0f1", fg="#2C3E50").pack(pady=(0, 10))

        tk.Label(f_left, text="Fecha:", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.cal_fecha = DateEntry(f_left, selectmode='day', date_pattern='dd/mm/yyyy', font=("Segoe UI", 10), background='darkblue', foreground='white', borderwidth=2)
        self.cal_fecha.pack(fill="x", pady=(0, 10))

        tk.Label(f_left, text="Hora (Hasta 9 PM):", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        # --- AQUÍ ESTÁ LA CORRECCIÓN DEL HORARIO HASTA LAS 21:30 ---
        horas = [f"{h:02d}:00" for h in range(8, 22)] + [f"{h:02d}:30" for h in range(8, 22)]; horas.sort()
        self.c_cita_hora = ttk.Combobox(f_left, values=horas, font=("Segoe UI", 10), state="readonly")
        self.c_cita_hora.set("09:00")
        self.c_cita_hora.pack(fill="x", pady=(0, 10))

        tk.Label(f_left, text="Paciente / Dueño:", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.e_cita_paciente = ttk.Entry(f_left, font=("Segoe UI", 10))
        self.e_cita_paciente.pack(fill="x", pady=(0, 10))

        tk.Label(f_left, text="Teléfono (Opcional):", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.e_cita_telefono = ttk.Entry(f_left, font=("Segoe UI", 10))
        self.e_cita_telefono.pack(fill="x", pady=(0, 10))

        tk.Label(f_left, text="Motivo:", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.e_cita_motivo = ttk.Entry(f_left, font=("Segoe UI", 10))
        self.e_cita_motivo.pack(fill="x", pady=(0, 10))
        
        tk.Label(f_left, text="Atiende (Doctor/Estilista):", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.c_cita_atiende = ttk.Combobox(f_left, values=config.LISTA_VENDEDORES, font=("Segoe UI", 10), state="readonly")
        if config.LISTA_VENDEDORES: self.c_cita_atiende.set(config.LISTA_VENDEDORES[0])
        self.c_cita_atiende.pack(fill="x", pady=(0, 20))
        
        tk.Button(f_left, text="💾 AGENDAR CITA", bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"), command=self.agendar_cita, height=2).pack(fill="x")

        f_right = tk.Frame(self.tab_citas, bg="#F4F6F7", padx=15, pady=15)
        f_right.pack(side="right", fill="both", expand=True)
        
        f_toolbar = tk.Frame(f_right, bg="white", bd=0, highlightbackground="#D5D8DC", highlightthickness=1)
        f_toolbar.pack(fill="x", pady=(0, 12))

        # --- Fila 1: filtros de fecha ---
        f_fila1 = tk.Frame(f_toolbar, bg="white")
        f_fila1.pack(fill="x", padx=15, pady=(12, 6))

        tk.Label(f_fila1, text="📆 VER:", bg="white", font=("Segoe UI", 10, "bold"), fg="#2C3E50").pack(side="left", padx=(0, 12))

        def btn_filtro(parent, txt, cmd, color):
            return tk.Button(parent, text=txt, command=cmd, bg=color, fg="white",
                              font=("Segoe UI", 9, "bold"), relief="flat", padx=16, pady=6,
                              cursor="hand2", activebackground=color)

        btn_filtro(f_fila1, "HOY", lambda: self.filtrar_citas("hoy"), "#3498db").pack(side="left", padx=4)
        btn_filtro(f_fila1, "MAÑANA", lambda: self.filtrar_citas("manana"), "#7f8c8d").pack(side="left", padx=4)
        btn_filtro(f_fila1, "TODO", lambda: self.filtrar_citas("todo"), "#7f8c8d").pack(side="left", padx=4)

        tk.Frame(f_toolbar, bg="#ECF0F1", height=1).pack(fill="x", padx=15)

        # --- Fila 2: acciones sobre la cita seleccionada + avisos de WhatsApp ---
        f_fila2 = tk.Frame(f_toolbar, bg="white")
        f_fila2.pack(fill="x", padx=15, pady=(6, 12))

        tk.Label(f_fila2, text="⚙️ ACCIÓN:", bg="white", font=("Segoe UI", 10, "bold"), fg="#2C3E50").pack(side="left", padx=(0, 12))

        btn_filtro(f_fila2, "✅ COMPLETADA", self.completar_cita, "#27ae60").pack(side="left", padx=4)
        btn_filtro(f_fila2, "❌ CANCELAR", self.cancelar_cita, "#e74c3c").pack(side="left", padx=4)
        btn_filtro(f_fila2, "📲 RECORDATORIO", self.enviar_whatsapp_cita, "#25D366").pack(side="left", padx=4)

        btn_filtro(f_fila2, "📋 RESUMEN DEL DÍA AL GRUPO", self.compartir_resumen_dia, "#128C7E").pack(side="right", padx=4)

        cols = ("Fecha", "Hora", "Paciente", "Teléfono", "Motivo", "Atiende", "Estado", "ID")
        self.tree_citas = ttk.Treeview(f_right, columns=cols, show="headings", style="Premium.Treeview")
        
        for col, w in zip(cols, [80, 50, 150, 100, 150, 100, 100, 0]):
            self.tree_citas.heading(col, text=col.upper())
            self.tree_citas.column(col, width=w, anchor="center" if col not in ["Paciente", "Motivo"] else "w")
            
        self.tree_citas.column("ID", stretch=tk.NO) 
        self.tree_citas.pack(fill="both", expand=True)
        
        self.tree_citas.tag_configure("PENDIENTE", background="white", foreground="black") 
        self.tree_citas.tag_configure("COMPLETADA", background="#d5f5e3", foreground="#145a32") 
        self.tree_citas.tag_configure("CANCELADA", background="#fadbd8", foreground="#7f8c8d", font=("Segoe UI", 9, "overstrike")) 

    def construir_pestaña_pendientes(self):
        f_top = tk.Frame(self.tab_pendientes, bg="#F4F6F7", pady=15, padx=20)
        f_top.pack(fill="x")
        
        tk.Label(f_top, text="📌 NUEVO PENDIENTE / TAREA:", bg="#F4F6F7", font=("Segoe UI", 11, "bold"), fg="#2C3E50").pack(side="left")
        self.e_nuevo_pendiente = ttk.Entry(f_top, font=("Segoe UI", 12))
        self.e_nuevo_pendiente.pack(side="left", fill="x", expand=True, padx=15)
        self.e_nuevo_pendiente.bind("<Return>", lambda e: self.agregar_pendiente())
        
        tk.Button(f_top, text="➕ AGREGAR", bg="#f39c12", fg="white", font=("Segoe UI", 10, "bold"), command=self.agregar_pendiente).pack(side="left")

        f_body = tk.Frame(self.tab_pendientes, bg="white", bd=1, relief="solid")
        f_body.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        cols = ("ID", "Fecha Creación", "Descripción de la Tarea", "Estado")
        self.tree_pendientes = ttk.Treeview(f_body, columns=cols, show="headings", style="Premium.Treeview")
        for c, w in zip(cols, [40, 120, 500, 120]):
            self.tree_pendientes.heading(c, text=c)
            self.tree_pendientes.column(c, width=w, anchor="center" if c != "Descripción de la Tarea" else "w")

        self.tree_pendientes.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree_pendientes.tag_configure("PENDIENTE", background="#FCF3CF", font=("Segoe UI", 11))
        self.tree_pendientes.tag_configure("COMPLETADO", background="#D5F5E3", foreground="gray", font=("Segoe UI", 11, "overstrike"))

        f_btns = tk.Frame(f_body, bg="white", pady=10)
        f_btns.pack(fill="x", padx=10)
        tk.Button(f_btns, text="🗑️ ELIMINAR", bg="#c0392b", fg="white", font=("Segoe UI", 9, "bold"), command=self.eliminar_pendiente).pack(side="left")
        tk.Button(f_btns, text="✅ MARCAR COMO COMPLETADO", bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"), command=self.completar_pendiente).pack(side="right")

    def formatear_fecha_mx(self, fecha_iso):
        try:
            if not fecha_iso or fecha_iso == "N/A": return ""
            obj = datetime.strptime(fecha_iso, "%Y-%m-%d")
            return obj.strftime("%d/%m/%Y")
        except: return fecha_iso

    # =========================================================
    #   INTEGRACIÓN CON WHATSAPP (wa.me)
    # =========================================================
    def limpiar_telefono(self, telefono):
        """
        Limpia un número de teléfono y le agrega la lada de México (52) si hace
        falta, dejándolo listo para usarse en un enlace wa.me.
        Devuelve None si no hay un teléfono utilizable (vacío, 'None', etc).
        """
        if not telefono or str(telefono).strip().lower() in ("none", "n/a", ""):
            return None
        digitos = "".join(c for c in str(telefono) if c.isdigit())
        if len(digitos) < 10:
            return None
        if len(digitos) == 10:  # número local sin lada de país
            digitos = "52" + digitos
        return digitos

    def abrir_whatsapp(self, mensaje, telefono=None):
        """
        Abre WhatsApp (app o web, según lo que tenga instalado Windows) con el
        mensaje ya escrito.
        - Si se pasa un teléfono, abre el chat directo con esa persona.
        - Si no, abre el selector de chats de WhatsApp para elegir a quién
          mandárselo (perfecto para elegir el grupo de la clínica).
        """
        texto = urllib.parse.quote(mensaje)
        if telefono:
            url = f"https://wa.me/{telefono}?text={texto}"
        else:
            url = f"https://wa.me/?text={texto}"
        webbrowser.open(url)

    def enviar_whatsapp_cita(self):
        """
        Comparte un recordatorio de la cita seleccionada por WhatsApp.
        Como normalmente no se guarda el teléfono del cliente, se abre
        directo el selector de chats de WhatsApp para elegir con quién
        compartirlo (el cliente si lo tienen agregado, o el grupo).
        """
        sel = self.tree_citas.selection()
        if not sel: return messagebox.showwarning("Atención", "Selecciona una cita de la tabla.")

        fecha_mx, hora, paciente, telefono, motivo, atiende, estado, cid = self.tree_citas.item(sel[0])["values"]

        mensaje = (
            f"Hola {paciente}, le recordamos su cita en la Clínica Veterinaria Beethoven 🐾\n"
            f"🗓️ Fecha: {fecha_mx}\n"
            f"🕐 Hora: {hora}\n"
            f"📋 Motivo: {motivo or 'Consulta'}\n"
            f"👨‍⚕️ Atiende: {atiende}\n\n"
            f"¡Le esperamos!"
        )

        # Si por algún caso especial sí hay un teléfono guardado, se usa directo
        # para abrir el chat de esa persona. Si no (lo más común), se abre
        # el selector de chats de WhatsApp sin preguntar nada de más.
        tel_limpio = self.limpiar_telefono(telefono)
        self.abrir_whatsapp(mensaje, telefono=tel_limpio)

    def compartir_resumen_dia(self):
        """
        Arma un mensaje con todas las citas PENDIENTES de hoy y abre WhatsApp
        para elegir el grupo y mandarlo de un solo click (para el briefing
        de la mañana).
        """
        hoy = datetime.now().strftime("%Y-%m-%d")
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute(
            "SELECT hora, paciente, motivo, atiende FROM citas WHERE fecha=? AND estado='PENDIENTE' ORDER BY hora ASC",
            (hoy,)
        )
        citas_hoy = cursor.fetchall()
        conn.close()

        if not citas_hoy:
            return messagebox.showinfo("Sin citas", "No hay citas pendientes para el día de hoy.")

        fecha_mx = self.formatear_fecha_mx(hoy)
        mensaje = f"📅 *CITAS DE HOY {fecha_mx}*\n\n"
        for h, p, m, a in citas_hoy:
            mensaje += f"🕐 {h} - {p} ({m or 'Consulta'}) - Atiende: {a}\n"
        mensaje += f"\nTotal: {len(citas_hoy)} cita(s)"

        self.abrir_whatsapp(mensaje)

    def agendar_cita(self):
        f_maquina = self.cal_fecha.get_date().strftime("%Y-%m-%d")
        h = self.c_cita_hora.get().strip()
        p = self.e_cita_paciente.get().strip()
        t = self.e_cita_telefono.get().strip()
        m = self.e_cita_motivo.get().strip()
        a = self.c_cita_atiende.get().strip()
        
        if not h or not p: 
            return messagebox.showwarning("Faltan datos", "Completa la hora y el nombre del paciente.")
            
        conn = db.conectar(); cursor = conn.cursor()
        # Modificado para que te deje agendar a la misma hora SÓLO si la cita anterior se canceló
        cursor.execute("SELECT id FROM citas WHERE fecha=? AND hora=? AND atiende=? AND estado='PENDIENTE'", (f_maquina, h, a))
        if cursor.fetchone(): 
            conn.close(); return messagebox.showerror("Ocupado", f"El horario ya está ocupado para {a}.")
            
        cursor.execute("INSERT INTO citas (fecha, hora, paciente, telefono, motivo, atiende, estado) VALUES (?,?,?,?,?,?,?)", 
                       (f_maquina, h, p, t, m, a, 'PENDIENTE'))
        conn.commit(); conn.close()
        
        messagebox.showinfo("Éxito", "Cita agendada correctamente.")

        fecha_mx = self.formatear_fecha_mx(f_maquina)

        # --- AVISO AUTOMÁTICO AL GRUPO DE WHATSAPP ---
        if messagebox.askyesno("Avisar al grupo", "¿Quieres avisar esta cita en el grupo de WhatsApp?"):
            mensaje = (
                f"📅 *NUEVA CITA AGENDADA*\n"
                f"🐾 Paciente/Dueño: {p}\n"
                f"🗓️ Fecha: {fecha_mx} - {h}\n"
                f"📋 Motivo: {m or 'No especificado'}\n"
                f"👨‍⚕️ Atiende: {a}"
            )
            self.abrir_whatsapp(mensaje)  # abre el selector de chats para elegir el grupo

        self.e_cita_paciente.delete(0, tk.END)
        self.e_cita_telefono.delete(0, tk.END)
        self.e_cita_motivo.delete(0, tk.END)
        self.cargar_citas()

    def cargar_citas(self, filtro_sql=None, params=None):
        conn = db.conectar(); cursor = conn.cursor()
        for i in self.tree_citas.get_children(): self.tree_citas.delete(i)
            
        sql = "SELECT fecha, hora, paciente, telefono, motivo, atiende, estado, id FROM citas " + (filtro_sql if filtro_sql else "") + " ORDER BY fecha ASC, hora ASC"
        cursor.execute(sql, params if params else ())
        
        for row in cursor.fetchall():
            vals = (self.formatear_fecha_mx(row[0]), row[1], row[2], row[3], row[4], row[5], row[6], row[7])
            self.tree_citas.insert("", "end", values=vals, tags=(row[6],))
        conn.close()
        
    def filtrar_citas(self, modo):
        hoy = datetime.now().strftime("%Y-%m-%d")
        if modo == "hoy": self.cargar_citas("WHERE fecha = ?", (hoy,))
        elif modo == "manana": self.cargar_citas("WHERE fecha = ?", ((datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),))
        else: self.cargar_citas() 

    def cancelar_cita(self):
        sel = self.tree_citas.selection()
        if not sel: return messagebox.showwarning("Atención", "Selecciona una cita de la tabla para cancelarla.")
        
        valores = self.tree_citas.item(sel[0])["values"]
        if valores[6] == "CANCELADA": return messagebox.showinfo("Info", "Esta cita ya está cancelada.")
        
        if messagebox.askyesno("Confirmar", f"¿Marcar la cita de {valores[2]} como CANCELADA?"):
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("UPDATE citas SET estado='CANCELADA' WHERE id=?", (valores[7],))
            conn.commit(); conn.close()
            self.cargar_citas()

    def completar_cita(self):
        sel = self.tree_citas.selection()
        if not sel: return messagebox.showwarning("Atención", "Selecciona una cita de la tabla.")
        
        valores = self.tree_citas.item(sel[0])["values"]
        if valores[6] == "COMPLETADA": return messagebox.showinfo("Info", "Esta cita ya fue completada.")
        if valores[6] == "CANCELADA": return messagebox.showerror("Error", "No puedes completar una cita cancelada.")
        
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("UPDATE citas SET estado='COMPLETADA' WHERE id=?", (valores[7],))
        conn.commit(); conn.close()
        self.cargar_citas()

    def cargar_pendientes(self):
        for i in self.tree_pendientes.get_children(): self.tree_pendientes.delete(i)
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT id, fecha_creacion, descripcion, estado FROM pendientes ORDER BY estado DESC, id DESC")
        for r in cursor.fetchall(): self.tree_pendientes.insert("", "end", values=r, tags=(r[3],))
        conn.close()

    def agregar_pendiente(self):
        desc = self.e_nuevo_pendiente.get().strip()
        if not desc: return
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("INSERT INTO pendientes (descripcion, fecha_creacion, estado) VALUES (?,?,?)", (desc, datetime.now().strftime("%d/%m/%Y %H:%M"), "PENDIENTE"))
        conn.commit(); conn.close()
        self.e_nuevo_pendiente.delete(0, tk.END)
        self.cargar_pendientes()

    def completar_pendiente(self):
        sel = self.tree_pendientes.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecciona un pendiente.")
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("UPDATE pendientes SET estado='COMPLETADO' WHERE id=?", (self.tree_pendientes.item(sel[0])["values"][0],))
        conn.commit(); conn.close()
        self.cargar_pendientes()

    def eliminar_pendiente(self):
        sel = self.tree_pendientes.selection()
        if not sel: return
        if messagebox.askyesno("Borrar", "¿Eliminar esta tarea de la lista?"):
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("DELETE FROM pendientes WHERE id=?", (self.tree_pendientes.item(sel[0])["values"][0],))
            conn.commit(); conn.close()
            self.cargar_pendientes()