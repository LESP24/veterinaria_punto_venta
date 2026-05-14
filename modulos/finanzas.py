import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import db
import config

class PestanaFinanzas(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.COLOR_FONDO)
        self.setup_ui()

    def formatear_fecha_mx(self, fecha_iso):
        try:
            if not fecha_iso or fecha_iso == "N/A": return ""
            obj = datetime.strptime(fecha_iso, "%Y-%m-%d")
            return obj.strftime("%d/%m/%Y")
        except: return fecha_iso

    def setup_ui(self):
        f_top = tk.Frame(self, bg="#F4F6F7", pady=10); f_top.pack(fill="x")
        tk.Label(f_top, text="Fecha:", bg="#F4F6F7").pack(side="left", padx=10)
        self.combo_fechas = ttk.Combobox(f_top, state="readonly"); self.combo_fechas.pack(side="left")
        self.combo_fechas.bind("<<ComboboxSelected>>", lambda e: self.cargar_finanzas(self.combo_fechas.get()))
        self.f_fin_body = tk.Frame(self, bg="#F4F6F7"); self.f_fin_body.pack(fill="both", expand=True, padx=20)
        
        self.cargar_fechas_historial()
        self.cargar_finanzas()

    def cargar_fechas_historial(self):
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT date(fecha) FROM ventas UNION SELECT DISTINCT date(fecha) FROM movimientos_caja ORDER BY 1 DESC")
        self.combo_fechas['values'] = [r[0] for r in cursor.fetchall()]
        conn.close()
        
        if self.combo_fechas['values']: self.combo_fechas.current(0)

    def cargar_finanzas(self, fecha=None):
        if not fecha: fecha = datetime.now().strftime("%Y-%m-%d")
        fecha_mx = self.formatear_fecha_mx(fecha)
        for w in self.f_fin_body.winfo_children(): w.destroy()
        
        conn = db.conectar(); cursor = conn.cursor()
        
        cursor.execute("SELECT SUM(total) FROM ventas WHERE date(fecha)=? AND metodo_pago='EFECTIVO'", (fecha,))
        efvo = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(total) FROM ventas WHERE date(fecha)=? AND metodo_pago='TRANSFERENCIA'", (fecha,))
        trans = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(total) FROM ventas WHERE date(fecha)=? AND metodo_pago='SMART POINT'", (fecha,))
        smart = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(monto) FROM movimientos_caja WHERE date(fecha)=?", (fecha,))
        retiros = cursor.fetchone()[0] or 0
        
        en_caja = (efvo - retiros) + 500
        a_retirar = en_caja - 500
        
        f_dia = tk.Frame(self.f_fin_body, bg="#F4F6F7"); f_dia.pack(fill="x", pady=10)
        tk.Label(f_dia, text=f"CORTE DEL {fecha_mx}", font=("Segoe UI", 18, "bold"), bg="#F4F6F7").pack()
        tk.Label(f_dia, text=f"EFECTIVO EN CAJA: ${(efvo - retiros + 500):,.2f}", fg="green", font=("Segoe UI", 14), bg="#F4F6F7").pack()
        if a_retirar > 0: tk.Label(f_dia, text=f"🚨 RETIRAR: ${a_retirar:,.2f}", fg="#e74c3c", font=("Segoe UI", 14, "bold"), bg="#F4F6F7").pack()
        else: tk.Label(f_dia, text="✅ FONDO OK", fg="gray", bg="#F4F6F7").pack()
        tk.Label(f_dia, text=f"BANCO: ${trans:,.2f} | SMART: ${smart:,.2f}", fg="blue", bg="#F4F6F7").pack()

        f_split = tk.Frame(self.f_fin_body, bg="#F4F6F7"); f_split.pack(fill="both", expand=True)
        f_rank = tk.Frame(f_split, bg="white", bd=1, relief="solid"); f_rank.pack(side="left", fill="both", expand=True, padx=5)
        f_hist = tk.Frame(f_split, bg="white", bd=1, relief="solid"); f_hist.pack(side="right", fill="both", expand=True, padx=5)

        self.construir_ranking(f_rank, cursor)

        tk.Label(f_hist, text=f"📜 DETALLES {fecha_mx}", font=("Segoe UI", 10, "bold"), bg="white").pack(pady=5)
        cols = ("Hora", "Tipo", "Detalle", "Monto")
        tree_h = ttk.Treeview(f_hist, columns=cols, show="headings")
        for c in cols: tree_h.heading(c, text=c); tree_h.column(c, anchor="center")
        tree_h.column("Detalle", width=300)
        tree_h.pack(fill="both", expand=True)
        tree_h.tag_configure("in", foreground="green"); tree_h.tag_configure("out", foreground="red")

        cursor.execute("SELECT id, time(fecha), folio, total FROM ventas WHERE date(fecha)=?", (fecha,))
        ventas = cursor.fetchall()
        for vid, h, f, t in ventas:
            cursor.execute("SELECT p.nombre FROM detalle_venta d JOIN productos p ON d.codigo_producto=p.codigo WHERE d.venta_id=?", (vid,))
            prods = ", ".join([p[0] for p in cursor.fetchall()])
            tree_h.insert("", "end", values=(h, "VENTA", f"{prods} ({f})", f"+${t:,.2f}"), tags=("in",))
        
        cursor.execute("SELECT time(fecha), motivo, monto FROM movimientos_caja WHERE date(fecha)=?", (fecha,))
        for h, m, mt in cursor.fetchall(): tree_h.insert("", "end", values=(h, "RETIRO", m, f"-${mt:,.2f}"), tags=("out",))
        
        conn.close()

    def construir_ranking(self, frame, cursor):
        f_h = tk.Frame(frame, bg="white"); f_h.pack(fill="x")
        tk.Label(f_h, text="🏆 RANKING", font=("Segoe UI", 12, "bold"), bg="white").pack(side="left")
        tk.Button(f_h, text="REINICIAR", command=self.reiniciar_ranking, bg="orange", fg="white", relief="flat").pack(side="right")
        
        cursor.execute("SELECT valor FROM configuracion WHERE clave='inicio_ranking'")
        res = cursor.fetchone(); ini = res[0] if res else "2024-01-01"
        tk.Label(frame, text=f"Desde: {self.formatear_fecha_mx(ini[:10])}", fg="gray", bg="white").pack()

        cols = ("Vend", "Ventas", "Total")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c); tree.column(c, anchor="center")
        tree.pack(fill="both", expand=True, pady=5)
        tree.tag_configure("win", background="#f1c40f")

        cursor.execute("SELECT vendedor, COUNT(*), SUM(total) FROM ventas WHERE fecha >= ? GROUP BY vendedor ORDER BY COUNT(*) DESC", (ini,))
        rank = 1
        for row in cursor.fetchall():
            tree.insert("", "end", values=(row[0] or "Gral", row[1], f"${row[2]:,.2f}"), tags=("win" if rank==1 else "",))
            rank += 1

    def reiniciar_ranking(self):
        if messagebox.askyesno("?", "Reiniciar competencia?"):
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('inicio_ranking', ?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
            conn.commit(); conn.close()
            self.cargar_finanzas(self.combo_fechas.get())
            
    def cargar_ranking_semanal(self): pass