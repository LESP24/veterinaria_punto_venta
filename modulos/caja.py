import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from database import db
import config

class PestanaCaja(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.COLOR_FONDO)
        self.venta_items = []
        self.setup_ui()

    def setup_ui(self):
        f_izq = tk.Frame(self, bg="#F4F6F7"); f_izq.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        f_der = tk.Frame(self, bg="#ecf0f1", width=350); f_der.pack(side="right", fill="y"); f_der.pack_propagate(False)

        tk.Label(f_izq, text="Código/Nombre:", font=("Segoe UI", 12, "bold"), bg="#F4F6F7").pack(anchor="w")
        self.barcode_entry = tk.Entry(f_izq, font=("Arial", 22)); self.barcode_entry.pack(fill="x", pady=5)
        self.barcode_entry.bind("<KeyRelease>", self.buscar_producto_evento)
        self.barcode_entry.bind("<Return>", self.agregar_producto_directo)
        self.barcode_entry.focus()

        self.tree_busqueda = ttk.Treeview(f_izq, columns=("Cod", "Nom", "Pre", "Stk"), show="headings", height=5)
        self.tree_busqueda.heading("Cod", text="COD"); self.tree_busqueda.column("Cod", width=80, anchor="center")
        self.tree_busqueda.heading("Nom", text="NOMBRE"); self.tree_busqueda.column("Nom", width=300)
        self.tree_busqueda.heading("Pre", text="$"); self.tree_busqueda.column("Pre", width=80, anchor="center")
        self.tree_busqueda.heading("Stk", text="#"); self.tree_busqueda.column("Stk", width=50, anchor="center")
        self.tree_busqueda.pack(fill="x", pady=5); self.tree_busqueda.bind("<Double-1>", self.agregar_desde_busqueda)

        tk.Label(f_izq, text="CARRITO:", font=("Segoe UI", 12, "bold"), bg="#F4F6F7").pack(anchor="w", pady=(10,0))
        self.tree_venta = ttk.Treeview(f_izq, columns=("Desc", "Cant", "Pre", "Imp"), show="headings")
        self.tree_venta.heading("Desc", text="PRODUCTO"); self.tree_venta.column("Desc", width=250)
        self.tree_venta.heading("Cant", text="CANT"); self.tree_venta.column("Cant", width=50, anchor="center")
        self.tree_venta.heading("Pre", text="$"); self.tree_venta.column("Pre", width=80, anchor="center")
        self.tree_venta.heading("Imp", text="TOTAL"); self.tree_venta.column("Imp", width=80, anchor="center")
        self.tree_venta.pack(fill="both", expand=True); self.tree_venta.bind("<Delete>", lambda e: self.quitar_producto_carrito())
        tk.Button(f_izq, text="🗑️ QUITAR (SUPR)", bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"), command=self.quitar_producto_carrito).pack(fill="x", pady=5)

        tk.Label(f_der, text="TOTAL", font=("Arial", 20, "bold"), bg="#ecf0f1", fg="#2C3E50").pack(pady=(40, 10))
        self.total_label = tk.Label(f_der, text="$0.00", font=("Arial", 40, "bold"), bg="white", fg="#27ae60"); self.total_label.pack(fill="x", padx=10)
        
        tk.Label(f_der, text="Atiende:", font=("Segoe UI", 10, "bold"), bg="#ecf0f1").pack(pady=(20, 5))
        self.combo_medico = ttk.Combobox(f_der, values=config.LISTA_VENDEDORES, font=("Segoe UI", 12)); self.combo_medico.set(config.LISTA_VENDEDORES[0]); self.combo_medico.pack(fill="x", padx=20)
        
        self.tipo_precio = tk.StringVar(value="Público")
        tk.Radiobutton(f_der, text="Público", variable=self.tipo_precio, value="Público", bg="#ecf0f1", font=("Segoe UI", 11)).pack(pady=5)
        tk.Radiobutton(f_der, text="Colega", variable=self.tipo_precio, value="Mayoreo", bg="#ecf0f1", font=("Segoe UI", 11)).pack(pady=5)
        
        tk.Button(f_der, text="COBRAR (F12)", command=self.abrir_ventana_cobro, bg="#27ae60", fg="white", font=("Segoe UI", 14, "bold"), height=3).pack(fill="x", padx=20, pady=20)
        tk.Button(f_der, text="RETIRO", command=self.retiro_dinero, bg="#c0392b", fg="white").pack(fill="x", padx=20, pady=5)
        
        self.winfo_toplevel().bind("<F12>", self.abrir_ventana_cobro)

    def buscar_producto_evento(self, event):
        q = self.barcode_entry.get().strip()
        self.tree_busqueda.delete(*self.tree_busqueda.get_children())
        if not q: return
        p = "precio_mayoreo" if self.tipo_precio.get() == "Mayoreo" else "precio_publico"
        
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute(f"SELECT p.codigo, p.nombre, p.{p}, SUM(IFNULL(l.cantidad, 0)) FROM productos p LEFT JOIN lotes l ON p.codigo = l.codigo_producto WHERE p.nombre LIKE ? OR p.codigo LIKE ? GROUP BY p.codigo LIMIT 15", (f"%{q}%", f"%{q}%"))
        rows = cursor.fetchall()
        conn.close()
        
        for r in rows: self.tree_busqueda.insert("", "end", values=(r[0], r[1], f"${r[2]:.2f}", r[3] or 0))

    def agregar_desde_busqueda(self, event):
        sel = self.tree_busqueda.selection()
        if sel: 
            self.procesar_agregar(str(self.tree_busqueda.item(sel[0])["values"][0]))
            self.barcode_entry.delete(0, tk.END)
            self.tree_busqueda.delete(*self.tree_busqueda.get_children())

    def agregar_producto_directo(self, event):
        self.procesar_agregar(self.barcode_entry.get().strip())
        self.barcode_entry.delete(0, tk.END)
        self.tree_busqueda.delete(*self.tree_busqueda.get_children())

    def procesar_agregar(self, codigo):
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT nombre, precio_publico, precio_mayoreo FROM productos WHERE codigo=?", (codigo,))
        prod = cursor.fetchone()
        if not prod: 
            conn.close()
            return messagebox.showerror("Error", "No existe")
            
        cursor.execute("SELECT SUM(cantidad) FROM lotes WHERE codigo_producto=?", (codigo,))
        stock = cursor.fetchone()[0] or 0
        conn.close()
        
        cant_carro = sum(i["cantidad"] for i in self.venta_items if i["codigo"] == codigo)
        if cant_carro + 1 > stock: return messagebox.showwarning("Stock", f"Solo hay {stock}")
        
        precio = prod[2] if self.tipo_precio.get() == "Mayoreo" else prod[1]
        
        found = False
        for item in self.venta_items:
            if item["codigo"] == codigo: 
                item["cantidad"] += 1; item["subtotal"] = item["cantidad"] * precio; found = True; break
        if not found: self.venta_items.append({"codigo": codigo, "nombre": prod[0], "cantidad": 1, "precio": precio, "subtotal": precio})
        self.actualizar_carrito()

    def actualizar_carrito(self):
        self.tree_venta.delete(*self.tree_venta.get_children())
        for i in self.venta_items: self.tree_venta.insert("", "end", values=(i["nombre"], i["cantidad"], f"${i['precio']:.2f}", f"${i['subtotal']:.2f}"))
        self.total_label.config(text=f"${sum(i['subtotal'] for i in self.venta_items):,.2f}")

    def quitar_producto_carrito(self):
        sel = self.tree_venta.selection()
        if sel: del self.venta_items[self.tree_venta.index(sel[0])]; self.actualizar_carrito()

    def abrir_ventana_cobro(self, event=None):
        if not self.venta_items: return
        top = tk.Toplevel(self.winfo_toplevel()); top.title("Pago"); top.geometry("300x350")
        tk.Label(top, text="Método:", font=("Arial", 14)).pack(pady=10)
        tk.Label(top, text=f"Atiende: {self.combo_medico.get()}", fg="gray").pack()
        
        def pay(m): self.finalizar_venta(m); top.destroy()
        
        for m, c in [("EFECTIVO", "#27ae60"), ("TRANSFERENCIA", "#3498db"), ("SMART POINT", "#8e44ad")]: 
            tk.Button(top, text=m, bg=c, fg="white", command=lambda x=m: pay(x)).pack(pady=5, fill="x", padx=20)

    def finalizar_venta(self, metodo):
        total = sum(i["subtotal"] for i in self.venta_items)
        now = datetime.now()
        
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("INSERT INTO ventas (fecha, folio, total, tipo_precio, metodo_pago, vendedor) VALUES (?,?,?,?,?,?)", 
                       (now.isoformat(), now.strftime("%Y%m%d%H%M%S"), total, self.tipo_precio.get(), metodo, self.combo_medico.get()))
        vid = cursor.lastrowid
        
        for i in self.venta_items:
            req = i["cantidad"]
            cursor.execute("SELECT id, cantidad FROM lotes WHERE codigo_producto=? ORDER BY fecha_caducidad ASC", (i["codigo"],))
            for lid, lcant in cursor.fetchall():
                if req <= 0: break
                take = min(req, lcant)
                cursor.execute("UPDATE lotes SET cantidad = cantidad - ? WHERE id=?", (take, lid))
                req -= take
            cursor.execute("INSERT INTO detalle_venta (venta_id, codigo_producto, cantidad, precio_unitario, subtotal) VALUES (?,?,?,?,?)", 
                           (vid, i["codigo"], i["cantidad"], i["precio"], i["subtotal"]))
                           
        conn.commit(); conn.close()
        
        self.venta_items = []; self.actualizar_carrito(); messagebox.showinfo("OK", "Venta Lista")

    def retiro_dinero(self):
        m = simpledialog.askfloat("Retiro", "Monto:")
        mot = simpledialog.askstring("Motivo", "Razón")
        if m and mot: 
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("INSERT INTO movimientos_caja (fecha, tipo, motivo, monto) VALUES (?,?,?,?)", (datetime.now().isoformat(), "RETIRO", mot, m))
            conn.commit(); conn.close()
            messagebox.showinfo("OK", "Retiro registrado")