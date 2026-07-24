import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import os
from database import db
import config

class PestanaProveedores(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.COLOR_FONDO)
        self.verificar_tablas()
        self.proveedor_seleccionado_id = None
        self.proveedor_seleccionado_nombre = ""
        self.setup_ui()
        self.cargar_proveedores()

    def verificar_tablas(self):
        # Aseguramos que las tablas existan para evitar errores
        conn = db.conectar()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            )
        """)
        # Agregamos la columna para guardar la ruta del PDF del proveedor sin borrar datos
        try:
            conn.execute("ALTER TABLE proveedores ADD COLUMN ruta_pdf TEXT")
        except:
            pass

        conn.execute("""
            CREATE TABLE IF NOT EXISTS notas_proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER,
                fecha TEXT,
                concepto TEXT,
                monto REAL,
                estado TEXT DEFAULT 'PENDIENTE',
                FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
            )
        """)
        conn.commit()
        conn.close()

    def verificar_pin(self):
        pin = simpledialog.askstring("Seguridad", "Ingrese el PIN de Administrador:", show='*', parent=self)
        if not pin: return False
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT valor FROM configuracion WHERE clave='pin_admin'")
        res = cursor.fetchone()
        conn.close()
        pin_real = res[0] if res else "1234"
        if pin == pin_real: return True
        else:
            messagebox.showerror("Acceso Denegado", "El PIN ingresado es incorrecto.")
            return False

    def setup_ui(self):
        # --- PANEL IZQUIERDO (LISTA DE PROVEEDORES) ---
        f_izq = tk.Frame(self, bg="#F4F6F7", width=250)
        f_izq.pack(side="left", fill="y", padx=10, pady=10)
        f_izq.pack_propagate(False)

        tk.Label(f_izq, text="PROVEEDORES", font=("Segoe UI", 14, "bold"), bg="#F4F6F7", fg="#2C3E50").pack(pady=10)
        
        cols_prov = ("ID", "PROVEEDOR")
        self.tree_prov = ttk.Treeview(f_izq, columns=cols_prov, show="headings")
        self.tree_prov.heading("ID", text="ID"); self.tree_prov.column("ID", width=40, anchor="center")
        self.tree_prov.heading("PROVEEDOR", text="PROVEEDOR"); self.tree_prov.column("PROVEEDOR", width=180, anchor="w")
        self.tree_prov.pack(fill="both", expand=True, pady=5)
        self.tree_prov.bind("<<TreeviewSelect>>", self.seleccionar_proveedor)

        tk.Button(f_izq, text="➕ AGREGAR PROVEEDOR", bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"), command=self.agregar_proveedor).pack(fill="x", pady=5)
        tk.Button(f_izq, text="🗑️ ELIMINAR PROVEEDOR", bg="#c0392b", fg="white", font=("Segoe UI", 10, "bold"), command=self.eliminar_proveedor).pack(fill="x", pady=5)

        # --- PANEL DERECHO (PESTAÑAS) ---
        f_der = tk.Frame(self, bg="#ecf0f1")
        f_der.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"))
        self.notebook = ttk.Notebook(f_der)
        self.notebook.pack(fill="both", expand=True)

        # Pestaña 1: Precios y PDF
        self.tab_precios = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.tab_precios, text=" 📄 LISTA DE PRECIOS / COMPARADOR ")
        
        # --- SECCIÓN RECUPERADA DE PDFs ---
        f_pdf = tk.Frame(self.tab_precios, bg="white")
        f_pdf.pack(fill="x", padx=10, pady=15)
        
        tk.Label(f_pdf, text="Catálogo y Precios del Proveedor:", font=("Segoe UI", 11, "bold"), bg="white", fg="#2C3E50").pack(side="left")
        
        tk.Button(f_pdf, text="📄 ABRIR PDF DE PRECIOS", bg="#e67e22", fg="white", font=("Segoe UI", 9, "bold"), command=self.abrir_pdf).pack(side="right", padx=5)
        tk.Button(f_pdf, text="🔗 VINCULAR NUEVO PDF", bg="#7f8c8d", fg="white", font=("Segoe UI", 9, "bold"), command=self.adjuntar_pdf).pack(side="right", padx=5)

        tk.Label(self.tab_precios, text="Productos registrados en el inventario asociados a este laboratorio:", bg="white", fg="gray", font=("Segoe UI", 10, "italic")).pack(pady=5)
        
        self.tree_comparador = ttk.Treeview(self.tab_precios, columns=("Cod", "Nom", "Costo", "Pub", "Col"), show="headings")
        for c, t in zip(["Cod", "Nom", "Costo", "Pub", "Col"], ["CÓDIGO", "PRODUCTO", "COSTO", "P. PÚBLICO", "P. COLEGA"]):
            self.tree_comparador.heading(c, text=t)
        self.tree_comparador.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestaña 2: Cuentas y Notas
        self.tab_cuentas = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.tab_cuentas, text=" 💰 CUENTAS Y NOTAS (DEBE / PAGADO) ")

        f_reg = tk.Frame(self.tab_cuentas, bg="#F4F6F7", pady=10, padx=10)
        f_reg.pack(fill="x")
        tk.Label(f_reg, text="📄 REGISTRAR NUEVA CUENTA / DEUDA", font=("Segoe UI", 11, "bold"), bg="#F4F6F7", fg="#2C3E50").pack(anchor="w", pady=(0,10))
        
        f_reg_inputs = tk.Frame(f_reg, bg="#F4F6F7")
        f_reg_inputs.pack(fill="x")
        
        tk.Label(f_reg_inputs, text="Concepto / Factura:", bg="#F4F6F7", font=("Segoe UI", 10)).pack(side="left")
        self.e_concepto = ttk.Entry(f_reg_inputs, width=40, font=("Segoe UI", 10)); self.e_concepto.pack(side="left", padx=10)
        
        tk.Label(f_reg_inputs, text="Monto ($):", bg="#F4F6F7", font=("Segoe UI", 10)).pack(side="left")
        self.e_monto = ttk.Entry(f_reg_inputs, width=15, font=("Segoe UI", 10)); self.e_monto.pack(side="left", padx=10)
        
        tk.Button(f_reg_inputs, text="➕ REGISTRAR DEUDA", bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), command=self.registrar_deuda).pack(side="left", padx=10)

        f_totales = tk.Frame(self.tab_cuentas, bg="white", pady=10)
        f_totales.pack(fill="x", padx=10)
        
        self.lbl_total_prov = tk.Label(f_totales, text="Total Pendiente con este Proveedor: $0.00", font=("Segoe UI", 12, "bold"), bg="white", fg="#c0392b")
        self.lbl_total_prov.pack(side="left")

        tk.Button(f_totales, text="🗑️ ELIMINAR NOTA", bg="#e74c3c", fg="white", font=("Segoe UI", 9, "bold"), command=self.eliminar_nota).pack(side="right", padx=5)
        tk.Button(f_totales, text="💵 REGISTRAR ABONO", bg="#8e44ad", fg="white", font=("Segoe UI", 9, "bold"), command=self.registrar_abono_proveedor).pack(side="right", padx=5)
        tk.Button(f_totales, text="☑ MARCAR COMO PAGADO", bg="#2980b9", fg="white", font=("Segoe UI", 9, "bold"), command=self.liquidar_nota).pack(side="right", padx=5)

        cols_notas = ("ID", "FECHA", "CONCEPTO / DETALLE DE LA CUENTA", "MONTO", "ESTADO")
        self.tree_notas = ttk.Treeview(self.tab_cuentas, columns=cols_notas, show="headings", style="Premium.Treeview")
        for c, w in zip(cols_notas, [40, 100, 350, 100, 100]):
            self.tree_notas.heading(c, text=c); self.tree_notas.column(c, width=w, anchor="center" if w<200 else "w")
        self.tree_notas.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree_notas.tag_configure("PENDIENTE", background="#fadbd8", foreground="#78281f") 
        self.tree_notas.tag_configure("PAGADO", background="#d5f5e3", foreground="#145a32") 

    # --- LÓGICA DE PDF ---
    def adjuntar_pdf(self):
        if not self.proveedor_seleccionado_id:
            return messagebox.showwarning("Aviso", "Seleccione un proveedor de la lista de la izquierda primero.")
            
        ruta = filedialog.askopenfilename(title="Seleccionar Lista de Precios en PDF", filetypes=[("Archivos PDF", "*.pdf")])
        if ruta:
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("UPDATE proveedores SET ruta_pdf=? WHERE id=?", (ruta, self.proveedor_seleccionado_id))
            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", "El PDF ha sido vinculado correctamente a este proveedor.")

    def abrir_pdf(self):
        if not self.proveedor_seleccionado_id:
            return messagebox.showwarning("Aviso", "Seleccione un proveedor primero.")
            
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT ruta_pdf FROM proveedores WHERE id=?", (self.proveedor_seleccionado_id,))
        res = cursor.fetchone()
        conn.close()
        
        if res and res[0] and os.path.exists(res[0]):
            os.startfile(res[0])
        else:
            messagebox.showwarning("No encontrado", "No se encontró ningún archivo asociado.\n\nPosibles causas:\n1. Aún no has vinculado un PDF.\n2. El archivo PDF fue movido a otra carpeta o eliminado de tu computadora.")

    # --- LÓGICA PROVEEDORES ---
    def cargar_proveedores(self):
        self.tree_prov.delete(*self.tree_prov.get_children())
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM proveedores ORDER BY nombre ASC")
        for r in cursor.fetchall(): self.tree_prov.insert("", "end", values=r)
        conn.close()

    def agregar_proveedor(self):
        nom = simpledialog.askstring("Nuevo Proveedor", "Nombre del Laboratorio o Proveedor:", parent=self)
        if nom:
            try:
                conn = db.conectar(); cursor = conn.cursor()
                cursor.execute("INSERT INTO proveedores (nombre) VALUES (?)", (nom.upper(),))
                conn.commit(); conn.close()
                self.cargar_proveedores()
            except: messagebox.showerror("Error", "El proveedor ya existe.")

    def eliminar_proveedor(self):
        sel = self.tree_prov.selection()
        if not sel: return
        pid = self.tree_prov.item(sel[0])["values"][0]
        if not self.verificar_pin(): return
        if messagebox.askyesno("Borrar", "Se eliminará el proveedor y su historial de cuentas. ¿Continuar?"):
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("DELETE FROM notas_proveedores WHERE proveedor_id=?", (pid,))
            cursor.execute("DELETE FROM proveedores WHERE id=?", (pid,))
            conn.commit(); conn.close()
            self.cargar_proveedores(); self.proveedor_seleccionado_id = None; self.cargar_datos_proveedor()

    def seleccionar_proveedor(self, event):
        sel = self.tree_prov.selection()
        if sel:
            self.proveedor_seleccionado_id = self.tree_prov.item(sel[0])["values"][0]
            self.proveedor_seleccionado_nombre = self.tree_prov.item(sel[0])["values"][1]
            self.cargar_datos_proveedor()

    def cargar_datos_proveedor(self):
        self.tree_notas.delete(*self.tree_notas.get_children())
        self.tree_comparador.delete(*self.tree_comparador.get_children())
        if not self.proveedor_seleccionado_id:
            self.lbl_total_prov.config(text="Total Pendiente con este Proveedor: $0.00")
            return

        conn = db.conectar(); cursor = conn.cursor()
        
        cursor.execute("SELECT codigo, nombre, costo_referencia, precio_publico, precio_mayoreo FROM productos WHERE laboratorio=?", (self.proveedor_seleccionado_nombre,))
        for p in cursor.fetchall():
            self.tree_comparador.insert("", "end", values=(p[0], p[1], f"${p[2]:.2f}", f"${p[3]:.2f}", f"${p[4]:.2f}"))

        cursor.execute("SELECT id, fecha, concepto, monto, estado FROM notas_proveedores WHERE proveedor_id=? ORDER BY id DESC", (self.proveedor_seleccionado_id,))
        total_deuda = 0
        for r in cursor.fetchall():
            if r[4] == "PENDIENTE": total_deuda += float(r[3])
            self.tree_notas.insert("", "end", values=(r[0], r[1], r[2], f"${r[3]:,.2f}", r[4]), tags=(r[4],))
        
        self.lbl_total_prov.config(text=f"Total Pendiente con {self.proveedor_seleccionado_nombre}: ${total_deuda:,.2f}")
        conn.close()

    # --- LÓGICA DE CUENTAS Y ABONOS ---
    def registrar_deuda(self):
        if not self.proveedor_seleccionado_id: return messagebox.showwarning("Aviso", "Seleccione un proveedor primero.")
        conc = self.e_concepto.get().strip()
        try: monto = float(self.e_monto.get())
        except: return messagebox.showwarning("Error", "El monto debe ser un número válido.")
        
        if not conc or monto <= 0: return
        
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("INSERT INTO notas_proveedores (proveedor_id, fecha, concepto, monto, estado) VALUES (?,?,?,?,?)",
                       (self.proveedor_seleccionado_id, datetime.now().strftime("%d/%m/%Y"), conc.upper(), monto, "PENDIENTE"))
        conn.commit(); conn.close()
        
        self.e_concepto.delete(0, tk.END); self.e_monto.delete(0, tk.END)
        self.cargar_datos_proveedor()

    def registrar_abono_proveedor(self):
        sel = self.tree_notas.selection()
        if not sel: return messagebox.showwarning("Aviso", "Seleccione una cuenta PENDIENTE de la lista.")
        
        vals = self.tree_notas.item(sel[0])["values"]
        nid, estado = vals[0], vals[4]
        deuda = float(vals[3].replace('$', '').replace(',', ''))
        
        if estado == "PAGADO" or deuda <= 0: 
            return messagebox.showinfo("Info", "Esta cuenta ya está liquidada completamente.")
            
        abono = simpledialog.askfloat("Abono a Proveedor", f"Deuda actual de la nota: ${deuda:,.2f}\n\n¿Cuánto dinero está entregando (abonando) al proveedor?", minvalue=1, maxvalue=deuda, parent=self)
        if not abono: return
        
        origen_caja = messagebox.askyesno("Origen de los fondos", f"¿Los ${abono:,.2f} se están tomando físicamente de la CAJA DE LA CLÍNICA?\n\n(Diga 'NO' si se pagó con dinero de otros negocios o cuenta personal externa).", parent=self)
        
        if origen_caja:
            if not self.verificar_pin(): return 

        nueva_deuda = deuda - abono
        nuevo_estado = 'PAGADO' if nueva_deuda <= 0 else 'PENDIENTE'
        fecha_hoy = datetime.now().strftime("%d/%m/%y")
        
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("UPDATE notas_proveedores SET monto=?, estado=?, concepto = concepto || ? WHERE id=?", 
                       (nueva_deuda, nuevo_estado, f" | Abono ${abono:,.2f} ({fecha_hoy})", nid))
                       
        if origen_caja:
            motivo_retiro = f"ABONO PROVEEDOR: {self.proveedor_seleccionado_nombre} (Nota #{nid})"
            cursor.execute("INSERT INTO movimientos_caja (fecha, tipo, motivo, monto) VALUES (?,?,?,?)", 
                           (datetime.now().isoformat(), "RETIRO", motivo_retiro, abono))
            msg_final = f"Abono de ${abono:,.2f} aplicado.\n\nSe ha registrado un RETIRO en la caja de Finanzas de la clínica."
        else:
            msg_final = f"Abono de ${abono:,.2f} aplicado a la deuda.\n\n(Como se pagó con fondos externos, la caja de la veterinaria quedó intacta)."
            
        conn.commit(); conn.close()
        
        messagebox.showinfo("Éxito", msg_final)
        self.cargar_datos_proveedor()

    def liquidar_nota(self):
        sel = self.tree_notas.selection()
        if not sel: return
        nid = self.tree_notas.item(sel[0])["values"][0]
        if messagebox.askyesno("Liquidar", "¿Marcar esta cuenta como PAGADA sin registrar retiro de caja?\n(Útil si se pagó desde cuenta de banco personal y no de caja física)"):
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("UPDATE notas_proveedores SET estado='PAGADO' WHERE id=?", (nid,))
            conn.commit(); conn.close()
            self.cargar_datos_proveedor()

    def eliminar_nota(self):
        sel = self.tree_notas.selection()
        if not sel: return
        nid = self.tree_notas.item(sel[0])["values"][0]
        if not self.verificar_pin(): return
        if messagebox.askyesno("Borrar", "¿Eliminar este registro de deuda?"):
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("DELETE FROM notas_proveedores WHERE id=?", (nid,))
            conn.commit(); conn.close()
            self.cargar_datos_proveedor()