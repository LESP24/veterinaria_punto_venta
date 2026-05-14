import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import os
import shutil
from database import db
import config

class PestanaInventario(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.COLOR_FONDO)
        self.setup_ui()

    def normalizar_fecha_db(self, texto_fecha):
        if not texto_fecha or texto_fecha.strip() == "": return "2030-01-01"
        texto_fecha = texto_fecha.strip().replace('/', '-')
        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"]:
            try: return datetime.strptime(texto_fecha, fmt).strftime("%Y-%m-%d")
            except ValueError: continue
        return "2030-01-01"

    def formatear_fecha_mx(self, fecha_iso):
        try:
            if not fecha_iso or fecha_iso == "N/A": return ""
            obj = datetime.strptime(fecha_iso, "%Y-%m-%d")
            return obj.strftime("%d/%m/%Y")
        except: return fecha_iso

    def setup_ui(self):
        f_top = tk.Frame(self, bg="#F4F6F7", pady=10, padx=10)
        f_top.pack(fill="x")
        f_top.columnconfigure(1, weight=1) 

        campos = [
            ("Código", 12), ("Nombre del Producto", 0), ("Laboratorio", 18),
            ("Costo", 8), ("P. Público", 8), ("P. Colega", 8),
            ("Mín", 5), ("Actual", 5), ("Caducidad", 11)
        ]
        
        self.entries = {}
        for i, (texto, ancho) in enumerate(campos):
            tk.Label(f_top, text=texto, bg="#F4F6F7", font=("Segoe UI", 9, "bold"), fg="#2C3E50").grid(row=0, column=i, padx=5, sticky="w")
            if ancho == 0: ent = tk.Entry(f_top, font=("Segoe UI", 10), bd=1, relief="solid"); ent.grid(row=1, column=i, padx=5, pady=5, sticky="ew")
            else: ent = tk.Entry(f_top, width=ancho, font=("Segoe UI", 10), bd=1, relief="solid"); ent.grid(row=1, column=i, padx=5, pady=5, sticky="w")

            if "Código" in texto: self.e_cod = ent
            elif "Nombre" in texto: self.e_nom = ent
            elif "Laboratorio" in texto: self.e_lab = ent
            elif "Costo" in texto: self.e_cost = ent
            elif "P. Público" in texto: self.e_pub = ent
            elif "P. Colega" in texto: self.e_col = ent
            elif "Mín" in texto: self.e_min = ent
            elif "Actual" in texto: self.e_stock = ent
            elif "Caducidad" in texto: self.e_cad = ent

        f_btns = tk.Frame(f_top, bg="#F4F6F7")
        f_btns.grid(row=1, column=len(campos), padx=15, sticky="e")
        
        def mk_btn(txt, col, cmd): tk.Button(f_btns, text=txt, bg=col, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, command=cmd).pack(side="left", padx=2)
        mk_btn("GUARDAR", "#27AE60", self.guardar_producto)
        mk_btn("LIMPIAR", "#2980B9", self.limpiar_form_manual)
        mk_btn("ELIMINAR", "#C0392B", self.eliminar_producto)
        mk_btn("USB", "#8E44AD", self.respaldar_usb)

        cols_inv = ("Cod", "Nom", "Lab", "Costo", "Pub", "Col", "Stock", "Cad")
        self.tree_inv = ttk.Treeview(self, columns=cols_inv, show="headings")
        headers = ["CÓDIGO", "NOMBRE DEL PRODUCTO", "LABORATORIO", "COSTO", "P. PÚBLICO", "P. COLEGA", "STOCK", "CADUCIDAD"]
        widths = [90, 400, 150, 80, 80, 80, 60, 100]
        
        for i, col in enumerate(cols_inv):
            self.tree_inv.heading(col, text=headers[i])
            self.tree_inv.column(col, width=widths[i], anchor="center")
        
        self.tree_inv.column("Nom", anchor="w")
        self.tree_inv.pack(fill="both", expand=True, padx=15, pady=5)
        
        self.tree_inv.tag_configure("agotado", background="#FFCDD2", foreground="black") 
        self.tree_inv.tag_configure("por_caducar", background="#FFE0B2", foreground="black") 
        self.tree_inv.tag_configure("bajo", background="#FFF9C4", foreground="black") 
        self.tree_inv.tag_configure("caducado", background="#D32F2F", foreground="white") 
        self.tree_inv.tag_configure("normal", background="white", foreground="#2C3E50") 
        
        self.tree_inv.bind("<Double-1>", self.llenar_form_inv)
        
        f_legend = tk.Frame(self, bg="#2C3E50", pady=5)
        f_legend.pack(fill="x")
        
        def mk_leg(txt, col, fg="black"):
            lbl = tk.Label(f_legend, text=f"  {txt}  ", bg=col, fg=fg, font=("Segoe UI", 9, "bold"))
            lbl.pack(side="left", padx=10)
            
        tk.Label(f_legend, text="SIGNIFICADO DE COLORES:", bg="#2C3E50", fg="white", font=("Segoe UI", 10)).pack(side="left", padx=10)
        mk_leg("AGOTADO (0 STOCK)", "#FFCDD2")
        mk_leg("POR CADUCAR (60 DÍAS)", "#FFE0B2")
        mk_leg("STOCK BAJO", "#FFF9C4")
        mk_leg("¡YA CADUCÓ!", "#D32F2F", "white")

        self.cargar_inventario_completo()

    def cargar_inventario_completo(self):
        for i in self.tree_inv.get_children(): self.tree_inv.delete(i)
        hoy = datetime.now().date()
        limite = hoy + timedelta(days=60)

        conn = db.conectar(); cursor = conn.cursor()
        sql = """SELECT p.codigo, p.nombre, p.laboratorio, p.costo_referencia, p.precio_publico, p.precio_mayoreo, SUM(IFNULL(l.cantidad, 0)), p.stock_minimo, MIN(l.fecha_caducidad)
            FROM productos p LEFT JOIN lotes l ON p.codigo = l.codigo_producto GROUP BY p.codigo"""
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            stock = row[6]
            try: st_min = int(row[7])
            except: st_min = 1
            cad_str = row[8]
            
            tag = "normal"
            fecha_prod = None
            if cad_str and cad_str != "N/A":
                try: fecha_prod = datetime.strptime(cad_str, "%Y-%m-%d").date()
                except: pass

            if stock == 0: tag = "agotado"
            elif fecha_prod:
                if fecha_prod < hoy: tag = "caducado"
                elif fecha_prod <= limite: tag = "por_caducar"
                elif stock <= st_min: tag = "bajo"
            elif stock <= st_min: tag = "bajo"
            
            try: cost = f"${float(row[3]):.2f}"; pub = f"${float(row[4]):.2f}"; col = f"${float(row[5]):.2f}"
            except: cost=pub=col="$0.00"
            
            vals = (row[0], row[1], row[2], cost, pub, col, stock, self.formatear_fecha_mx(cad_str))
            self.tree_inv.insert("", "end", values=vals, tags=(tag,))

    def llenar_form_inv(self, event):
        sel = self.tree_inv.selection()
        if not sel: return
        vals = self.tree_inv.item(sel[0])["values"]
        cod = vals[0]
        
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos WHERE codigo=?", (str(cod),))
        p = cursor.fetchone()
        conn.close()

        if p:
            self.limpiar_form_manual()
            self.e_cod.insert(0, p[0]); self.e_nom.insert(0, p[1]); self.e_lab.insert(0, p[3] or "")
            self.e_cost.insert(0, p[4]); self.e_pub.insert(0, p[5]); self.e_col.insert(0, p[6])
            self.e_min.insert(0, p[7]); self.e_stock.insert(0, vals[6])
            
            fecha_mx = vals[7]
            if fecha_mx and fecha_mx != "N/A":
                try: self.e_cad.insert(0, datetime.strptime(fecha_mx, "%d/%m/%Y").strftime("%Y-%m-%d"))
                except: self.e_cad.insert(0, "")
            else: self.e_cad.insert(0, "")

    def limpiar_form_manual(self):
        for e in [self.e_cod, self.e_nom, self.e_lab, self.e_cost, self.e_pub, self.e_col, self.e_min, self.e_cad, self.e_stock]: e.delete(0, tk.END)

    def guardar_producto(self):
        try:
            try: cost=float(self.e_cost.get()); col=float(self.e_col.get()); pub=float(self.e_pub.get()); st_min=int(self.e_min.get())
            except: cost=0; col=0; pub=0; st_min=1
            
            if col < cost * 1.5:
                if not messagebox.askyesno("Alerta", f"Precio Colega bajo.\nCosto: {cost}\nSugerido: {cost*1.5}\n¿Guardar?"): return

            vals = (self.e_cod.get(), self.e_nom.get(), 'General', self.e_lab.get(), cost, pub, col, st_min)
            
            try: n_st = int(self.e_stock.get())
            except: n_st = 0
            
            fecha_final = self.normalizar_fecha_db(self.e_cad.get())
            
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO productos VALUES (?,?,?,?,?,?,?,?)", vals)
            cursor.execute("DELETE FROM lotes WHERE codigo_producto=?", (vals[0],))
            cursor.execute("INSERT INTO lotes (codigo_producto, cantidad, fecha_caducidad) VALUES (?, ?, ?)", (vals[0], n_st, fecha_final))
            conn.commit(); conn.close()

            self.cargar_inventario_completo()
            self.limpiar_form_manual()
        except Exception as e: messagebox.showerror("Error", str(e))

    def eliminar_producto(self):
        if messagebox.askyesno("Borrar", "¿Eliminar?"):
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("DELETE FROM lotes WHERE codigo_producto=?", (self.e_cod.get(),))
            cursor.execute("DELETE FROM productos WHERE codigo=?", (self.e_cod.get(),))
            conn.commit(); conn.close()
            
            self.cargar_inventario_completo()
            self.limpiar_form_manual()

    def respaldar_usb(self):
        path = filedialog.askdirectory()
        if path: shutil.copy("veterinaria.db", os.path.join(path, f"respaldo_{datetime.now().strftime('%Y%m%d')}.db")); messagebox.showinfo("OK", "Respaldo listo")