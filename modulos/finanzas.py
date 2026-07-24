import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import calendar
from database import db
import config

class PestanaFinanzas(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.COLOR_FONDO)
        self.datos_corte = {} 
        self._migrar_bd()
        self.setup_ui()

    def _migrar_bd(self):
        """Agrega la columna 'descripcion' a detalle_venta si no existe (mismo fix que en caja.py)."""
        conn = db.conectar(); cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE detalle_venta ADD COLUMN descripcion TEXT")
            conn.commit()
        except Exception:
            pass
        conn.close()

    def resolver_nombre_item(self, cursor, codigo, descripcion=None):
        """
        Devuelve el nombre real de un producto/servicio para mostrar en reportes.
        1. Si existe 'descripcion' guardada (ventas nuevas) se usa esa, es el nombre exacto.
        2. Si no (ventas viejas antes de este fix), se reconstruye lo mejor posible
           a partir del código o del catálogo de productos.
        """
        if descripcion:
            return descripcion
        if str(codigo).startswith("SERV_"):
            partes = str(codigo).split('_')
            return partes[1] if len(partes) > 1 else "SERVICIO"
        cursor.execute("SELECT nombre FROM productos WHERE codigo=?", (codigo,))
        p = cursor.fetchone()
        return p[0] if p else "Eliminado"

    def formatear_fecha_mx(self, fecha_iso):
        try:
            if not fecha_iso or fecha_iso == "N/A": return ""
            obj = datetime.strptime(fecha_iso, "%Y-%m-%d")
            return obj.strftime("%d/%m/%Y")
        except: return fecha_iso

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
        f_top = tk.Frame(self, bg="#F4F6F7", pady=10); f_top.pack(fill="x")
        tk.Label(f_top, text="Fecha:", bg="#F4F6F7", font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)
        self.combo_fechas = ttk.Combobox(f_top, state="readonly", font=("Segoe UI", 10)); self.combo_fechas.pack(side="left")
        self.combo_fechas.bind("<<ComboboxSelected>>", lambda e: self.cargar_finanzas(self.combo_fechas.get()))
        
        tk.Button(f_top, text="📒 CUENTAS POR COBRAR E HISTORIAL DE ABONOS", bg="#e67e22", fg="white", font=("Segoe UI", 9, "bold"), command=self.abrir_cuentas_cobrar).pack(side="right", padx=20)
        
        self.f_fin_body = tk.Frame(self, bg="#F4F6F7"); self.f_fin_body.pack(fill="both", expand=True, padx=20)
        
        self.cargar_fechas_historial()
        self.cargar_finanzas()

    def cargar_fechas_historial(self):
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT date(fecha) FROM ventas UNION SELECT DISTINCT date(fecha) FROM movimientos_caja ORDER BY 1 DESC")
        self.combo_fechas['values'] = [r[0] for r in cursor.fetchall()]
        conn.close()
        if self.combo_fechas['values']: self.combo_fechas.current(0)

    def editar_fondo(self, fecha_iso, actual_fondo):
        nuevo_fondo = simpledialog.askfloat("Fondo Inicial", f"Ingresa el fondo de caja con el que iniciaste el {self.formatear_fecha_mx(fecha_iso)}:", initialvalue=actual_fondo)
        if nuevo_fondo is not None:
            fecha_corta = fecha_iso[:10]
            clave_fondo = f"fondo_{fecha_corta}"
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("SELECT clave FROM configuracion WHERE clave=?", (clave_fondo,))
            if cursor.fetchone(): cursor.execute("UPDATE configuracion SET valor=? WHERE clave=?", (nuevo_fondo, clave_fondo))
            else: cursor.execute("INSERT INTO configuracion (clave, valor) VALUES (?, ?)", (clave_fondo, nuevo_fondo))
            conn.commit(); conn.close()
            self.cargar_finanzas(fecha_iso)

    def cargar_finanzas(self, fecha=None):
        if not fecha: fecha = datetime.now().strftime("%Y-%m-%d")
        fecha_mx = self.formatear_fecha_mx(fecha)
        for w in self.f_fin_body.winfo_children(): w.destroy()
        
        conn = db.conectar(); cursor = conn.cursor()
        
        cursor.execute("SELECT SUM(total) FROM ventas WHERE date(fecha)=? AND metodo_pago='EFECTIVO'", (fecha,))
        efvo = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(total) FROM ventas WHERE date(fecha)=? AND metodo_pago IN ('TARJETA', 'SMART POINT')", (fecha,))
        tarjeta = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(total) FROM ventas WHERE date(fecha)=? AND metodo_pago='TRANSFERENCIA'", (fecha,))
        trans = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(total) FROM ventas WHERE date(fecha)=? AND metodo_pago='OTROS'", (fecha,))
        otros = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(monto) FROM movimientos_caja WHERE date(fecha)=? AND tipo='INGRESO' AND motivo LIKE 'ABONO%'", (fecha,))
        ingresos_abonos = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(monto) FROM movimientos_caja WHERE date(fecha)=? AND tipo='RETIRO'", (fecha,))
        retiros = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT valor FROM configuracion WHERE clave=?", (f"fondo_{fecha[:10]}",))
        res_fondo = cursor.fetchone()
        fondo_fijo = float(res_fondo[0]) if res_fondo else 500.00
        
        ingresos_efectivo_total = efvo + ingresos_abonos
        gastos_retiros = retiros
        total_en_cajon = ingresos_efectivo_total - gastos_retiros + fondo_fijo
        ganancia_a_retirar = ingresos_efectivo_total - gastos_retiros 
        cochinito_total = ganancia_a_retirar + tarjeta + trans + otros

        cursor.execute("""
            SELECT dv.codigo_producto, dv.cantidad, dv.subtotal, p.costo_referencia
            FROM detalle_venta dv
            JOIN ventas v ON dv.venta_id = v.id
            LEFT JOIN productos p ON dv.codigo_producto = p.codigo
            WHERE date(v.fecha)=?
        """, (fecha,))
        
        utilidad_neta = 0.0
        for cod, cant, sub, costo in cursor.fetchall():
            if str(cod).startswith("SERV_"): utilidad_neta += float(sub) 
            else:
                c_unit = float(costo) if costo else 0.0
                utilidad_neta += (float(sub) - (c_unit * float(cant)))

        # Guardamos los datos para la ventana del ticket visual
        self.datos_corte = {
            "fecha": fecha_mx,
            "fondo": fondo_fijo,
            "ingresos_efvo": ingresos_efectivo_total,
            "retiros": gastos_retiros,
            "cajon": total_en_cajon,
            "tarjeta": tarjeta,
            "trans": trans,
            "otros": otros,
            "utilidad": utilidad_neta,
            "a_retirar": ganancia_a_retirar,
            "total_ingresado": cochinito_total
        }

        f_dia = tk.Frame(self.f_fin_body, bg="#F4F6F7")
        f_dia.pack(fill="x", pady=5)
        
        tk.Label(f_dia, text=f"📊 RESUMEN FINANCIERO DEL {fecha_mx}", font=("Segoe UI", 16, "bold"), bg="#F4F6F7", fg="#2C3E50").pack(pady=(0, 10))
        f_cards = tk.Frame(f_dia, bg="#F4F6F7"); f_cards.pack()

        def crear_tarjeta(parent, titulo, monto, color_monto, btn_cmd=None, btn_text=""):
            tarjeta = tk.Frame(parent, bg="white", bd=0, highlightbackground="#D5D8DC", highlightthickness=1, padx=20, pady=10)
            tk.Label(tarjeta, text=titulo, font=("Segoe UI", 9, "bold"), bg="white", fg="#7f8c8d").pack()
            tk.Label(tarjeta, text=monto, font=("Segoe UI", 16, "bold"), bg="white", fg=color_monto).pack(pady=(5,0))
            if btn_cmd: tk.Button(tarjeta, text=btn_text, command=btn_cmd, font=("Segoe UI", 8, "bold"), bg="#f39c12", fg="white", cursor="hand2", relief="flat").pack(pady=(5,0), fill="x")
            return tarjeta

        crear_tarjeta(f_cards, "FONDO INICIAL", f"${fondo_fijo:,.2f}", "#7f8c8d", btn_cmd=lambda: self.editar_fondo(fecha, fondo_fijo), btn_text="✏️ EDITAR").grid(row=0, column=0, padx=10)
        crear_tarjeta(f_cards, "VENTAS+ABONOS (EFVO)", f"+${ingresos_efectivo_total:,.2f}", "#27ae60").grid(row=0, column=1, padx=10)
        crear_tarjeta(f_cards, "RETIROS/GASTOS", f"-${gastos_retiros:,.2f}", "#e74c3c").grid(row=0, column=2, padx=10)
        crear_tarjeta(f_cards, "EN CAJÓN (FÍSICO)", f"${total_en_cajon:,.2f}", "#2980b9").grid(row=0, column=3, padx=10)

        f_retirar = tk.Frame(f_dia, bg="#F4F6F7"); f_retirar.pack(pady=10)
        if ganancia_a_retirar > 0: tk.Label(f_retirar, text=f"💰 DINERO A RETIRAR DE CAJA (EFECTIVO): ${ganancia_a_retirar:,.2f}", fg="#c0392b", font=("Segoe UI", 12, "bold"), bg="#F4F6F7").pack()
        elif ganancia_a_retirar < 0: tk.Label(f_retirar, text=f"⚠️ FALTANTE EN FONDO: ${abs(ganancia_a_retirar):,.2f}", fg="red", font=("Segoe UI", 12, "bold"), bg="#F4F6F7").pack()
        else: tk.Label(f_retirar, text="✅ CAJA EN CEROS (NO RETIRAR NADA)", fg="gray", font=("Segoe UI", 12, "bold"), bg="#F4F6F7").pack()
            
        tk.Label(f_dia, text=f"Ingresos en Banco ➔ TERMINAL (Tarjeta): ${tarjeta:,.2f}  |  TRANSFERENCIA: ${trans:,.2f}  |  OTROS: ${otros:,.2f}", fg="#8e44ad", bg="#F4F6F7", font=("Segoe UI", 11, "bold")).pack(pady=(0, 5))
        
        f_ganancias = tk.Frame(f_dia, bg="#F4F6F7")
        f_ganancias.pack(pady=5)
        tk.Label(f_ganancias, text=f"💰 TOTAL INGRESADO HOY (Efectivo + Banco): ${cochinito_total:,.2f}", fg="#d35400", bg="#F4F6F7", font=("Segoe UI", 14, "bold")).pack(side="left", padx=20)
        tk.Label(f_ganancias, text=f"📈 UTILIDAD NETA (Ganancia Libre): ${utilidad_neta:,.2f}", fg="#27ae60", bg="#F4F6F7", font=("Segoe UI", 18, "bold")).pack(side="left", padx=20)

        # --- BOTONES DE CORTE Z Y RESUMEN DE PRODUCTOS ---
        f_botones_resumen = tk.Frame(f_dia, bg="#F4F6F7")
        f_botones_resumen.pack(pady=10)
        tk.Button(f_botones_resumen, text="📋 VER RESUMEN DE CORTE Z (CIERRE DE DÍA)", bg="#27ae60", fg="white", font=("Segoe UI", 11, "bold"), command=self.ver_corte_z).pack(side="left", padx=5)
        tk.Button(f_botones_resumen, text="📦 VER PRODUCTOS Y SERVICIOS VENDIDOS HOY", bg="#2980b9", fg="white", font=("Segoe UI", 11, "bold"), command=self.ver_productos_vendidos_hoy).pack(side="left", padx=5)

        f_split = tk.Frame(self.f_fin_body, bg="#F4F6F7")
        f_split.pack(fill="both", expand=True, pady=(5, 10))
        
        f_rank = tk.Frame(f_split, bg="white", bd=0, highlightbackground="#D5D8DC", highlightthickness=1)
        f_rank.pack(side="left", fill="both", expand=True, padx=(0, 5))
        f_hist = tk.Frame(f_split, bg="white", bd=0, highlightbackground="#D5D8DC", highlightthickness=1)
        f_hist.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.construir_ranking(f_rank, cursor)

        lbl_hist_head = tk.Label(f_hist, text=f"📜 DETALLES DE MOVIMIENTOS ({fecha_mx})", font=("Segoe UI", 11, "bold"), bg="#34495E", fg="white", pady=8)
        lbl_hist_head.pack(fill="x")
        
        cols = ("ID", "Hora", "Atiende", "Tipo", "Detalle", "Monto")
        self.tree_h = ttk.Treeview(f_hist, columns=cols, show="headings", style="Premium.Treeview")
        self.tree_h.heading("ID", text="ID"); self.tree_h.column("ID", width=0, stretch=False) 
        self.tree_h.heading("Hora", text="Hora"); self.tree_h.column("Hora", width=60, anchor="center", stretch=False)
        self.tree_h.heading("Atiende", text="Atiende"); self.tree_h.column("Atiende", width=80, anchor="center", stretch=False)
        self.tree_h.heading("Tipo", text="Tipo"); self.tree_h.column("Tipo", width=110, anchor="center", stretch=False)
        self.tree_h.heading("Detalle", text="Detalle"); self.tree_h.column("Detalle", width=160, anchor="w", stretch=True) 
        self.tree_h.heading("Monto", text="Monto"); self.tree_h.column("Monto", width=90, anchor="center", stretch=False)
        
        self.tree_h.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree_h.tag_configure("in", background="#EAFAF1", foreground="#145A32", font=("Segoe UI", 10)) 
        self.tree_h.tag_configure("out", background="#FDEDEC", foreground="#78281F", font=("Segoe UI", 10))
        self.tree_h.tag_configure("abono", background="#E8F8F5", foreground="#0E6655", font=("Segoe UI", 10, "bold"))
        self.tree_h.bind("<Double-1>", self.ver_detalles_venta)

        cursor.execute("SELECT id, time(fecha), folio, total, vendedor, metodo_pago FROM ventas WHERE date(fecha)=?", (fecha,))
        for vid, h, f, t, vend, pago in cursor.fetchall():
            cursor.execute("SELECT codigo_producto, cantidad, descripcion FROM detalle_venta WHERE venta_id=?", (vid,))
            lista_articulos = []
            for cod, cant, desc in cursor.fetchall():
                nombre = self.resolver_nombre_item(cursor, cod, desc)
                lista_articulos.append(f"{cant:g}x {nombre}")
            
            if pago == "SMART POINT": pago = "TARJETA"
            self.tree_h.insert("", "end", values=(vid, h, vend or "Gral", pago, ", ".join(lista_articulos), f"+${t:,.2f}"), tags=("in",))
        
        cursor.execute("SELECT time(fecha), motivo, monto, tipo FROM movimientos_caja WHERE date(fecha)=?", (fecha,))
        for h, m, mt, tipo_mov in cursor.fetchall(): 
            quien = "Caja"
            if "PAGO NÓMINA:" in m: quien = m.split("PAGO NÓMINA:")[1].split("(")[0].strip()
            elif "ABONO PROVEEDOR:" in m: quien = "Dueño"
            elif "ABONO de" in m: quien = "Cliente"

            if tipo_mov == 'RETIRO': self.tree_h.insert("", "end", values=("CAJA", h, quien, "RETIRO", m, f"-${mt:,.2f}"), tags=("out",))
            else: self.tree_h.insert("", "end", values=("CAJA", h, quien, "ABONO", m, f"+${mt:,.2f}"), tags=("abono",))
        
        conn.close()
        tk.Button(f_hist, text="❌ CANCELAR VENTA SELECCIONADA", bg="#c0392b", fg="white", font=("Segoe UI", 9, "bold"), command=self.cancelar_venta).pack(fill="x", padx=10, pady=5)

    def ver_corte_z(self):
        d = self.datos_corte
        
        # Crear ventana emergente estilo Ticket
        top = tk.Toplevel(self)
        top.title("Corte Z - Resumen del Día")
        top.geometry("450x650")
        top.configure(bg="white")
        top.grab_set() 
        
        tk.Label(top, text="CLÍNICA VETERINARIA\nCORTE DE CAJA Z", font=("Courier", 14, "bold"), bg="white").pack(pady=10)
        
        # Diseño limpio y claro
        ticket = f"Fecha: {d.get('fecha')}\n"
        ticket += f"Hora : {datetime.now().strftime('%H:%M:%S')}\n"
        ticket += f"----------------------------------------\n"
        ticket += f"FONDO INICIAL:             ${d.get('fondo',0):,.2f}\n"
        ticket += f"VENTAS+ABONOS EFVO:       +${d.get('ingresos_efvo',0):,.2f}\n"
        ticket += f"RETIROS/GASTOS:           -${d.get('retiros',0):,.2f}\n"
        ticket += f"----------------------------------------\n"
        ticket += f"TOTAL EN CAJÓN (FÍSICO):\n"
        ticket += f"                           ${d.get('cajon',0):,.2f}\n\n"
        ticket += f"DINERO A RETIRAR (GANANCIA): ${d.get('a_retirar',0):,.2f}\n"
        ticket += f"----------------------------------------\n"
        ticket += f"INGRESOS EN BANCO (DIGITALES):\n"
        ticket += f" TERMINAL (Tarjeta):       ${d.get('tarjeta',0):,.2f}\n"
        ticket += f" TRANSFERENCIA:            ${d.get('trans',0):,.2f}\n"
        ticket += f" OTROS:                    ${d.get('otros',0):,.2f}\n"
        ticket += f"----------------------------------------\n"
        ticket += f"TOTAL INGRESADO HOY:       ${d.get('total_ingresado',0):,.2f}\n"
        ticket += f"UTILIDAD NETA (Ganancia):  ${d.get('utilidad',0):,.2f}\n"
        ticket += f"----------------------------------------\n"
        ticket += f"         REVISIÓN COMPLETADA            \n"

        txt_widget = tk.Text(top, font=("Courier", 11), bg="#F9E79F", fg="#2C3E50", relief="flat", padx=20, pady=20)
        txt_widget.insert("1.0", ticket)
        txt_widget.config(state="disabled") 
        txt_widget.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Button(top, text="CERRAR VENTANA", bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"), command=top.destroy).pack(pady=10)

    def cancelar_venta(self):
        sel = self.tree_h.selection()
        if not sel: return messagebox.showwarning("Aviso", "Seleccione una VENTA para cancelarla.")
        valores = self.tree_h.item(sel[0])["values"]
        
        if valores[3] not in ["EFECTIVO", "TARJETA", "TRANSFERENCIA", "CRÉDITO", "OTROS", "SMART POINT"]: 
            return messagebox.showwarning("Aviso", "Solo puede seleccionar ingresos/ventas para cancelar.")
        
        if not self.verificar_pin(): return

        if messagebox.askyesno("Confirmar Cancelación", "Se anulará el ingreso y los productos regresarán al inventario.\n¿Estás seguro?"):
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("SELECT codigo_producto, cantidad FROM detalle_venta WHERE venta_id=?", (valores[0],))
            for cod, cant in cursor.fetchall():
                if not str(cod).startswith("SERV_"):
                    cursor.execute("SELECT id FROM lotes WHERE codigo_producto=? LIMIT 1", (cod,))
                    lote = cursor.fetchone()
                    if lote: cursor.execute("UPDATE lotes SET cantidad = cantidad + ? WHERE id=?", (cant, lote[0]))
                    else: cursor.execute("INSERT INTO lotes (codigo_producto, cantidad, fecha_caducidad) VALUES (?,?,?)", (cod, cant, "2030-01-01"))
            cursor.execute("DELETE FROM detalle_venta WHERE venta_id=?", (valores[0],))
            cursor.execute("DELETE FROM ventas WHERE id=?", (valores[0],))
            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", "Venta cancelada."); self.cargar_finanzas(self.combo_fechas.get())

    # --- VER DETALLES DE UNA VENTA (CON DEVOLUCIÓN DE PRODUCTOS) ---
    def ver_detalles_venta(self, event):
        seleccion = self.tree_h.selection()
        if not seleccion: return

        item = self.tree_h.item(seleccion[0])
        valores = item['values']
        tags = item['tags']

        # Solo se pueden ver detalles de VENTAS (no de retiros/abonos de caja)
        if "in" not in tags:
            return messagebox.showwarning("Aviso", "Solo puede ver el detalle de una VENTA.\nLos abonos/retiros no tienen productos asociados.")

        folio_venta = valores[0]  # ID de la venta (columna oculta)
        fecha_mx = self.formatear_fecha_mx(self.combo_fechas.get())

        top = tk.Toplevel(self)
        top.title(f"Detalles de la Venta #{folio_venta}")
        top.geometry("650x500")
        top.configure(bg="#F4F6F7")
        top.grab_set()

        tk.Label(top, text=f"🧾 PRODUCTOS Y SERVICIOS - VENTA #{folio_venta}", font=("Segoe UI", 13, "bold"), bg="#F4F6F7", fg="#2C3E50").pack(pady=10)
        tk.Label(top, text=f"Fecha: {fecha_mx}", font=("Segoe UI", 9), bg="#F4F6F7", fg="#7f8c8d").pack()

        columnas = ("ID", "Producto/Servicio", "Cant", "Precio Unit.", "Subtotal")
        tabla_detalles = ttk.Treeview(top, columns=columnas, show="headings")
        tabla_detalles.heading("ID", text="ID"); tabla_detalles.column("ID", width=0, stretch=False)
        tabla_detalles.heading("Producto/Servicio", text="Producto/Servicio"); tabla_detalles.column("Producto/Servicio", width=250, anchor="w")
        tabla_detalles.heading("Cant", text="Cant"); tabla_detalles.column("Cant", width=60, anchor="center")
        tabla_detalles.heading("Precio Unit.", text="Precio Unit."); tabla_detalles.column("Precio Unit.", width=100, anchor="center")
        tabla_detalles.heading("Subtotal", text="Subtotal"); tabla_detalles.column("Subtotal", width=100, anchor="center")

        def cargar_detalles():
            tabla_detalles.delete(*tabla_detalles.get_children())
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("SELECT dv.id, dv.codigo_producto, dv.cantidad, dv.subtotal, dv.precio_unitario, dv.descripcion FROM detalle_venta dv WHERE dv.venta_id=?", (folio_venta,))
            filas = cursor.fetchall()
            for did, cod, cant, sub, precio_u, desc in filas:
                nombre = self.resolver_nombre_item(cursor, cod, desc)
                precio_unit = precio_u if precio_u is not None else ((sub / cant) if cant else 0)
                tabla_detalles.insert("", "end", values=(did, nombre, f"{cant:g}", f"${precio_unit:,.2f}", f"${sub:,.2f}"))
            conn.close()
            
            if not filas:
                top.after(100, top.destroy)  # si ya no quedan productos, cerramos la ventana

        def procesar_devolucion():
            sel = tabla_detalles.selection()
            if not sel: return messagebox.showwarning("Aviso", "Seleccione un producto para devolver.", parent=top)

            item_sel = tabla_detalles.item(sel[0])['values']
            id_detalle = item_sel[0]
            prod_nombre = item_sel[1]
            
            cant_actual = float(item_sel[2]) 
            subtotal_actual = float(str(item_sel[4]).replace('$', '').replace(',', ''))
            precio_unitario = subtotal_actual / cant_actual  # Calculamos el precio real sin redondeos de texto

            # --- LÓGICA DE DEVOLUCIÓN PARCIAL ---
            cant_a_devolver = cant_actual
            if cant_actual > 1:
                respuesta = simpledialog.askfloat("Devolución Parcial", 
                                                  f"Se detectaron {cant_actual:g} unidades de '{prod_nombre}'.\n¿Cuántas unidades deseas devolver?", 
                                                  initialvalue=cant_actual, minvalue=0.1, maxvalue=cant_actual, parent=top)
                if not respuesta: return # El usuario cerró la ventana o canceló
                cant_a_devolver = respuesta

            monto_reembolso = cant_a_devolver * precio_unitario

            if not messagebox.askyesno("Confirmar Devolución", f"¿Devolver {cant_a_devolver:g}x {prod_nombre} y reembolsar ${monto_reembolso:,.2f}?", parent=top):
                return

            if not self.verificar_pin(): return

            conn = db.conectar(); cursor = conn.cursor()

            # Recuperamos el código real del producto para regresarlo al inventario
            cursor.execute("SELECT codigo_producto FROM detalle_venta WHERE id=?", (id_detalle,))
            res_cod = cursor.fetchone()
            cod_real = res_cod[0] if res_cod else None

            # A. Regresar al inventario si es producto (no servicio)
            if cod_real and not str(cod_real).startswith("SERV_"):
                cursor.execute("SELECT id FROM lotes WHERE codigo_producto=? LIMIT 1", (cod_real,))
                lote = cursor.fetchone()
                if lote:
                    cursor.execute("UPDATE lotes SET cantidad = cantidad + ? WHERE id=?", (cant_a_devolver, lote[0]))
                else:
                    cursor.execute("INSERT INTO lotes (codigo_producto, cantidad, fecha_caducidad) VALUES (?,?,?)", (cod_real, cant_a_devolver, "2030-01-01"))

            # B. Restar el subtotal devuelto del total de la venta
            cursor.execute("UPDATE ventas SET total = total - ? WHERE id=?", (monto_reembolso, folio_venta))

            # C. Registrar el retiro en movimientos_caja
            cursor.execute("INSERT INTO movimientos_caja (fecha, tipo, motivo, monto) VALUES (?,?,?,?)",
                           (datetime.now().isoformat(), "RETIRO", f"DEVOLUCIÓN: {cant_a_devolver:g}x {prod_nombre} (Venta #{folio_venta})", monto_reembolso))

            # D. Actualizar o eliminar el item de detalle_venta
            if cant_a_devolver == cant_actual:
                cursor.execute("DELETE FROM detalle_venta WHERE id=?", (id_detalle,))
            else:
                cursor.execute("UPDATE detalle_venta SET cantidad = cantidad - ?, subtotal = subtotal - ? WHERE id=?", 
                               (cant_a_devolver, monto_reembolso, id_detalle))
            
            # Limpieza profunda. Si la venta se quedó sin artículos, borrar el registro huérfano.
            cursor.execute("SELECT COUNT(*) FROM detalle_venta WHERE venta_id=?", (folio_venta,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("DELETE FROM ventas WHERE id=?", (folio_venta,))

            conn.commit(); conn.close()
            
            messagebox.showinfo("Éxito", f"Devolución de {cant_a_devolver:g}x {prod_nombre} procesada.\nSe generó un retiro de ${monto_reembolso:,.2f} en caja.", parent=top)
            
            # Refrescar UI general
            self.cargar_finanzas(self.combo_fechas.get())
            cargar_detalles()

        tk.Button(top, text="🔄 DEVOLVER PRODUCTO SELECCIONADO", bg="#e74c3c", fg="white", font=("Segoe UI", 11, "bold"), height=2, command=procesar_devolucion).pack(side="bottom", pady=15, fill="x", padx=20)
        
        tabla_detalles.pack(fill="both", expand=True, padx=15, pady=10)
        
        cargar_detalles()

    # --- RESUMEN DE PRODUCTOS Y SERVICIOS VENDIDOS EN EL DÍA (CON COSTO/GANANCIA) ---
    def ver_productos_vendidos_hoy(self):
        fecha = self.combo_fechas.get() or datetime.now().strftime("%Y-%m-%d")
        fecha_mx = self.formatear_fecha_mx(fecha)

        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("""
            SELECT dv.codigo_producto, dv.cantidad, dv.subtotal, p.costo_referencia, dv.descripcion
            FROM detalle_venta dv
            JOIN ventas v ON dv.venta_id = v.id
            LEFT JOIN productos p ON dv.codigo_producto = p.codigo
            WHERE date(v.fecha)=?
        """, (fecha,))
        filas = cursor.fetchall()

        # resumen[(nombre, tipo)] = [cantidad_total, subtotal_total, ganancia_total]
        resumen = {}
        for cod, cant, sub, costo, desc in filas:
            nombre = self.resolver_nombre_item(cursor, cod, desc)
            if str(cod).startswith("SERV_"):
                tipo = "Servicio"
                ganancia = float(sub)  # los servicios se consideran 100% ganancia (sin costo de insumo)
            else:
                tipo = "Producto"
                c_unit = float(costo) if costo else 0.0
                ganancia = float(sub) - (c_unit * float(cant))

            clave = (nombre, tipo)
            if clave not in resumen: resumen[clave] = [0.0, 0.0, 0.0]
            resumen[clave][0] += float(cant)
            resumen[clave][1] += float(sub)
            resumen[clave][2] += ganancia
        conn.close()

        top = tk.Toplevel(self)
        top.title(f"Productos y Servicios Vendidos - {fecha_mx}")
        top.geometry("700x520")
        top.configure(bg="#F4F6F7")
        top.grab_set()

        tk.Label(top, text=f"📦 PRODUCTOS Y SERVICIOS VENDIDOS EL {fecha_mx}", font=("Segoe UI", 13, "bold"), bg="#F4F6F7", fg="#2C3E50").pack(pady=10)

        cols = ("Nombre", "Tipo", "Cantidad", "Total Generado", "Ganancia")
        tree = ttk.Treeview(top, columns=cols, show="headings")
        tree.heading("Nombre", text="Nombre"); tree.column("Nombre", width=220, anchor="w")
        tree.heading("Tipo", text="Tipo"); tree.column("Tipo", width=90, anchor="center")
        tree.heading("Cantidad", text="Cantidad"); tree.column("Cantidad", width=80, anchor="center")
        tree.heading("Total Generado", text="Total Generado"); tree.column("Total Generado", width=120, anchor="center")
        tree.heading("Ganancia", text="Ganancia"); tree.column("Ganancia", width=110, anchor="center")
        tree.pack(fill="both", expand=True, padx=15, pady=10)

        tree.tag_configure("prod", background="white", foreground="#2C3E50", font=("Segoe UI", 10))
        tree.tag_configure("serv", background="#EAF2F8", foreground="#1B4F72", font=("Segoe UI", 10, "bold"))

        total_vendido = 0.0
        total_ganancia = 0.0

        for (nombre, tipo), (cant_total, sub_total, gan_total) in sorted(resumen.items(), key=lambda x: -x[1][1]):
            tree.insert("", "end", values=(nombre, tipo, f"{cant_total:g}", f"${sub_total:,.2f}", f"${gan_total:,.2f}"), tags=("serv" if tipo == "Servicio" else "prod",))
            total_vendido += sub_total
            total_ganancia += gan_total

        if not resumen:
            tk.Label(top, text="No hay productos ni servicios vendidos en esta fecha.", bg="#F4F6F7", fg="gray", font=("Segoe UI", 10, "italic")).pack(pady=20)
        else:
            f_totales = tk.Frame(top, bg="#F4F6F7"); f_totales.pack(pady=5)
            tk.Label(f_totales, text=f"TOTAL VENDIDO: ${total_vendido:,.2f}", font=("Segoe UI", 11, "bold"), fg="#d35400", bg="#F4F6F7").pack(side="left", padx=15)
            tk.Label(f_totales, text=f"GANANCIA TOTAL: ${total_ganancia:,.2f}", font=("Segoe UI", 11, "bold"), fg="#27ae60", bg="#F4F6F7").pack(side="left", padx=15)

        tk.Button(top, text="CERRAR", bg="#7f8c8d", fg="white", font=("Segoe UI", 10, "bold"), command=top.destroy).pack(pady=10)

    # --- CONTROL DE CUENTAS POR COBRAR (DEUDORES) ---
    def abrir_cuentas_cobrar(self):
        top = tk.Toplevel(self.winfo_toplevel()); top.title("Control de Cuentas por Cobrar"); top.geometry("850x550")
        top.configure(bg="#F4F6F7"); top.grab_set()
        
        tk.Label(top, text="📒 DEUDORES Y ABONOS (CUENTAS POR COBRAR)", font=("Segoe UI", 14, "bold"), bg="#F4F6F7", fg="#2C3E50").pack(pady=10)

        f_reg = tk.Frame(top, bg="#ecf0f1", pady=10, padx=10, bd=1, relief="solid")
        f_reg.pack(fill="x", padx=15, pady=5)
        
        tk.Label(f_reg, text="➕ REGISTRAR DEUDA MANUALMENTE (Si no pasó por la Caja):", font=("Segoe UI", 10, "bold"), bg="#ecf0f1").pack(anchor="w", pady=(0, 5))
        
        f_inputs = tk.Frame(f_reg, bg="#ecf0f1")
        f_inputs.pack(fill="x")
        
        tk.Label(f_inputs, text="Cliente:", bg="#ecf0f1", font=("Segoe UI", 9)).pack(side="left")
        e_cliente = ttk.Entry(f_inputs, width=25, font=("Segoe UI", 10)); e_cliente.pack(side="left", padx=5)
        
        tk.Label(f_inputs, text="Detalle/Motivo:", bg="#ecf0f1", font=("Segoe UI", 9)).pack(side="left")
        e_detalle = ttk.Entry(f_inputs, width=30, font=("Segoe UI", 10)); e_detalle.pack(side="left", padx=5)
        
        tk.Label(f_inputs, text="Monto a deber ($):", bg="#ecf0f1", font=("Segoe UI", 9)).pack(side="left")
        e_monto = ttk.Entry(f_inputs, width=10, font=("Segoe UI", 10)); e_monto.pack(side="left", padx=5)

        def registrar_deuda_manual():
            cli = e_cliente.get().strip()
            det = e_detalle.get().strip()
            try: m = float(e_monto.get())
            except: return messagebox.showwarning("Error", "El monto debe ser un número (Ej: 200.50).", parent=top)
            
            if not cli or m <= 0: return messagebox.showwarning("Error", "El nombre del cliente y el monto son obligatorios.", parent=top)
            
            if not self.verificar_pin(): return
            
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("INSERT INTO notas_clientes (cliente, fecha, concepto, monto, estado) VALUES (?,?,?,?,?)",
                           (cli.upper(), datetime.now().strftime("%d/%m/%Y"), det, m, "PENDIENTE"))
            conn.commit(); conn.close()
            
            messagebox.showinfo("Guardado", f"Deuda de {cli.upper()} guardada correctamente.", parent=top)
            e_cliente.delete(0, tk.END); e_detalle.delete(0, tk.END); e_monto.delete(0, tk.END)
            cargar_deudas()

        tk.Button(f_inputs, text="AGREGAR DEUDA", bg="#e67e22", fg="white", font=("Segoe UI", 9, "bold"), command=registrar_deuda_manual).pack(side="left", padx=10)

        cols = ("ID", "Cliente", "Fecha", "Detalle", "Deuda Restante", "Estado")
        tree_cred = ttk.Treeview(top, columns=cols, show="headings", height=10)
        for c, w in zip(cols, [40, 200, 80, 220, 100, 100]):
            tree_cred.heading(c, text=c); tree_cred.column(c, width=w, anchor="w" if w>100 else "center")
        tree_cred.pack(fill="both", expand=True, padx=15, pady=10)
        
        tree_cred.tag_configure("PENDIENTE", background="#fdadad", foreground="#7c0000")
        tree_cred.tag_configure("PAGADO", background="#d4efdf", foreground="#196f3d")

        def cargar_deudas():
            tree_cred.delete(*tree_cred.get_children())
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("SELECT id, cliente, fecha, concepto, monto, estado FROM notas_clientes ORDER BY id DESC")
            for r in cursor.fetchall(): tree_cred.insert("", "end", values=(r[0], r[1], r[2], r[3], f"${r[4]:,.2f}", r[5]), tags=(r[5],))
            conn.close()

        def registrar_abono():
            sel = tree_cred.selection()
            if not sel: return messagebox.showwarning("Atención", "Seleccione a un cliente de la lista de arriba para registrar su abono.", parent=top)
            vals = tree_cred.item(sel[0])["values"]
            nid, nom, deuda = vals[0], vals[1], float(vals[4].replace('$', '').replace(',', ''))
            
            if deuda <= 0: return messagebox.showinfo("Info", "Esta cuenta ya está liquidada.", parent=top)
            
            abono = simpledialog.askfloat("Registrar Abono", f"Deuda actual de {nom}: ${deuda:.2f}\n\n¿Cuánto dinero en EFECTIVO está abonando hoy el cliente?", minvalue=1, maxvalue=deuda, parent=top)
            if not abono: return
            
            nueva_deuda = deuda - abono
            nuevo_estado = 'PAGADO' if nueva_deuda <= 0 else 'PENDIENTE'
            fecha_hoy_txt = datetime.now().strftime("%d/%m/%y")
            
            conn = db.conectar(); cursor = conn.cursor()
            
            cursor.execute("UPDATE notas_clientes SET monto=?, estado=?, concepto = concepto || ? WHERE id=?", 
                           (nueva_deuda, nuevo_estado, f" | Abono ${abono} ({fecha_hoy_txt})", nid))
                           
            cursor.execute("INSERT INTO movimientos_caja (fecha, tipo, motivo, monto) VALUES (?,?,?,?)", 
                           (datetime.now().isoformat(), "INGRESO", f"ABONO de {nom}", abono))
                           
            conn.commit(); conn.close()
            messagebox.showinfo("Éxito", f"Abono de ${abono} registrado.\nEse dinero ya se sumó a las ganancias en efectivo del corte de hoy.", parent=top)
            cargar_deudas(); self.cargar_finanzas(self.combo_fechas.get())

        f_btns = tk.Frame(top, bg="#F4F6F7"); f_btns.pack(fill="x", padx=15, pady=10)
        tk.Button(f_btns, text="💵 REGISTRAR ABONO PARCIAL O PAGO TOTAL", bg="#2980b9", fg="white", font=("Segoe UI", 10, "bold"), command=registrar_abono, height=2).pack(side="right")
        
        cargar_deudas()

    def construir_ranking(self, frame, cursor):
        lbl_rank_head = tk.Label(frame, text="🏆 RANKING MENSUAL", font=("Segoe UI", 11, "bold"), bg="#34495E", fg="white", pady=8)
        lbl_rank_head.pack(fill="x")
        
        hoy = datetime.now()
        ini_str = hoy.replace(day=1).strftime("%Y-%m-%d")
        ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
        fin_str = hoy.replace(day=ultimo_dia).strftime("%Y-%m-%d")
        
        meses_es = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        tk.Label(frame, text=f"Ventas de {meses_es[hoy.month]} {hoy.year}", font=("Segoe UI", 9, "bold"), fg="#7F8C8D", bg="white").pack(pady=5)

        cols = ("Atiende", "Ventas", "Total Generado")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c); tree.column(c, anchor="center")
        tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        tree.tag_configure("win", background="#FCF3CF", foreground="#9C640C", font=("Segoe UI", 10, "bold"))
        tree.tag_configure("normal", background="white", foreground="#2C3E50", font=("Segoe UI", 10))

        cursor.execute("SELECT vendedor, COUNT(*), SUM(total) FROM ventas WHERE date(fecha) >= ? AND date(fecha) <= ? GROUP BY vendedor ORDER BY SUM(total) DESC", (ini_str, fin_str))
        rank = 1
        for row in cursor.fetchall():
            tree.insert("", "end", values=(row[0] or "Gral", row[1], f"${row[2]:,.2f}"), tags=("win" if rank==1 else "normal",))
            rank += 1