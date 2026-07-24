import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from database import db
import config
import os
import unicodedata

class PestanaCaja(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.COLOR_FONDO)
        self.venta_items = []
        self.ultimo_ticket = None # Guardará la info para poder reimprimir
        self._migrar_bd()
        self.setup_ui()

    def _migrar_bd(self):
        """
        Agrega la columna 'descripcion' a detalle_venta si no existe.
        Esta columna guarda el NOMBRE REAL del producto/servicio tal como
        se escribió al momento de la venta (antes se perdía y solo quedaba
        el código interno, por eso aparecía como 'VARIOS' en los reportes).
        Es seguro ejecutar esto cada vez que abre la app: si la columna
        ya existe, simplemente no hace nada.
        """
        conn = db.conectar(); cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE detalle_venta ADD COLUMN descripcion TEXT")
            conn.commit()
        except Exception:
            pass  # La columna ya existe, no hay nada que hacer
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
        f_izq = tk.Frame(self, bg="#F4F6F7"); f_izq.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        f_der = tk.Frame(self, bg="#ecf0f1", width=350); f_der.pack(side="right", fill="y"); f_der.pack_propagate(False)

        tk.Label(f_izq, text="Código/Nombre:", font=("Segoe UI", 12, "bold"), bg="#F4F6F7").pack(anchor="w")
        self.barcode_entry = tk.Entry(f_izq, font=("Arial", 22)); self.barcode_entry.pack(fill="x", pady=5)
        self.barcode_entry.bind("<KeyRelease>", self.buscar_producto_evento)
        self.barcode_entry.bind("<Return>", self.agregar_producto_directo)
        self.barcode_entry.focus()

        self.tree_busqueda = ttk.Treeview(f_izq, columns=("Cod", "Nom", "Pre", "Stk"), show="headings", height=5)
        self.tree_busqueda.heading("Cod", text="CODIGO"); self.tree_busqueda.column("Cod", width=80, anchor="center")
        self.tree_busqueda.heading("Nom", text="NOMBRE"); self.tree_busqueda.column("Nom", width=300)
        self.tree_busqueda.heading("Pre", text="PRECIO $"); self.tree_busqueda.column("Pre", width=80, anchor="center")
        self.tree_busqueda.heading("Stk", text="# CANTIDAD"); self.tree_busqueda.column("Stk", width=50, anchor="center")
        self.tree_busqueda.pack(fill="x", pady=5); self.tree_busqueda.bind("<Double-1>", self.agregar_desde_busqueda)

        tk.Label(f_izq, text="CARRITO:", font=("Segoe UI", 12, "bold"), bg="#F4F6F7").pack(anchor="w", pady=(10,0))
        self.tree_venta = ttk.Treeview(f_izq, columns=("Desc", "Cant", "Pre", "Imp"), show="headings")
        self.tree_venta.heading("Desc", text="PRODUCTO / SERVICIO"); self.tree_venta.column("Desc", width=250)
        self.tree_venta.heading("Cant", text="CANTIDAD"); self.tree_venta.column("Cant", width=60, anchor="center")
        self.tree_venta.heading("Pre", text="PRECIO $"); self.tree_venta.column("Pre", width=80, anchor="center")
        self.tree_venta.heading("Imp", text="TOTAL"); self.tree_venta.column("Imp", width=80, anchor="center")
        self.tree_venta.pack(fill="both", expand=True)
        self.tree_venta.bind("<Delete>", lambda e: self.quitar_producto_carrito())
        
        f_ctrl_carro = tk.Frame(f_izq, bg="#F4F6F7"); f_ctrl_carro.pack(fill="x", pady=5)
        tk.Button(f_ctrl_carro, text="🗑️ QUITAR PRODUCTO SELECCIONADO", bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"), command=self.quitar_producto_carrito).pack(fill="x", expand=True)

        tk.Label(f_der, text="TOTAL", font=("Arial", 20, "bold"), bg="#ecf0f1", fg="#2C3E50").pack(pady=(20, 5))
        self.total_label = tk.Label(f_der, text="$0.00", font=("Arial", 40, "bold"), bg="white", fg="#27ae60"); self.total_label.pack(fill="x", padx=10)
        
        tk.Label(f_der, text="Atiende:", font=("Segoe UI", 10, "bold"), bg="#ecf0f1").pack(pady=(15, 5))
        self.combo_medico = ttk.Combobox(f_der, values=config.LISTA_VENDEDORES, font=("Segoe UI", 12), state="readonly"); self.combo_medico.set(config.LISTA_VENDEDORES[0]); self.combo_medico.pack(fill="x", padx=20)
        
        self.tipo_precio = tk.StringVar(value="Público")
        f_radios = tk.Frame(f_der, bg="#ecf0f1"); f_radios.pack(pady=5)
        tk.Radiobutton(f_radios, text="Público", variable=self.tipo_precio, value="Público", bg="#ecf0f1", font=("Segoe UI", 10)).pack(side="left", padx=10)
        tk.Radiobutton(f_radios, text="Colega", variable=self.tipo_precio, value="Mayoreo", bg="#ecf0f1", font=("Segoe UI", 10)).pack(side="left", padx=10)
        
        # --- MENÚ DE SERVICIOS RÁPIDOS ---
        lf_servicios = tk.LabelFrame(f_der, text="🛠️ SERVICIOS RÁPIDOS", bg="#ecf0f1", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        lf_servicios.pack(fill="x", padx=20, pady=10)
        
        tk.Button(lf_servicios, text="✂️ 🧼 ESTÉTICA CANINA", bg="#8e44ad", fg="white", font=("Segoe UI", 10, "bold"), command=self.abrir_menu_estetica).pack(fill="x", pady=2)
        tk.Button(lf_servicios, text="🩺 📋 COBRAR CONSULTA", bg="#2980b9", fg="white", font=("Segoe UI", 10, "bold"), command=lambda: self.agregar_servicio_rapido("CONSULTA MÉDICA", "SERV_CONSULTA")).pack(fill="x", pady=2)
        tk.Button(lf_servicios, text="✨ ➕ OTRO SERVICIO", bg="#7f8c8d", fg="white", font=("Segoe UI", 10, "bold"), command=self.agregar_servicio_personalizado).pack(fill="x", pady=2)

        tk.Button(f_der, text="COBRAR (F12)", command=self.abrir_ventana_cobro, bg="#27ae60", fg="white", font=("Segoe UI", 14, "bold"), height=2).pack(fill="x", padx=20, pady=(10, 5))
        
        # BOTONES DE OPERACIÓN
        tk.Button(f_der, text="RETIRO DE CAJA", command=self.retiro_dinero, bg="#c0392b", fg="white", font=("Segoe UI", 9, "bold")).pack(fill="x", padx=20, pady=5)
        tk.Button(f_der, text="🖨️ REIMPRIMIR ÚLTIMO", command=self.reimprimir_ultimo, bg="#f39c12", fg="white", font=("Segoe UI", 9, "bold")).pack(fill="x", padx=20, pady=5)
        
        self.bind_all("<F12>", self.abrir_ventana_cobro)

    # --- NUEVO MENÚ DE ESTÉTICA ---
    def abrir_menu_estetica(self):
        top = tk.Toplevel(self)
        top.title("Estética Canina y Servicios de Baño")
        top.geometry("300x350")
        top.configure(bg="#F4F6F7")
        top.grab_set()
        
        tk.Label(top, text="SELECCIONE EL SERVICIO:", font=("Segoe UI", 11, "bold"), bg="#F4F6F7").pack(pady=10)
        
        servicios_estetica = [
            "Baño Simple", "Baño Medicado", "Corte y Baño", 
            "Corte de Uñas", "Limpieza de Oídos", "Aseo Glándulas Anales"
        ]
        
        for serv in servicios_estetica:
            tk.Button(top, text=f"🫧 {serv}", bg="#34495e", fg="white", font=("Segoe UI", 10, "bold"), 
                      command=lambda s=serv: [self.agregar_servicio_rapido(s, "SERV_ESTETICA"), top.destroy()]).pack(fill="x", padx=20, pady=5)

    def agregar_servicio_rapido(self, nombre_servicio, codigo_base):
        precio = simpledialog.askfloat("Costo del Servicio", f"Ingrese el costo para [{nombre_servicio}]:", minvalue=0, parent=self)
        if precio is None: return 
        codigo_unico = f"{codigo_base}_{int(datetime.now().timestamp())}_{len(self.venta_items)}"
        self.venta_items.append({"codigo": codigo_unico, "nombre": nombre_servicio.upper(), "cantidad": 1, "precio": precio, "subtotal": precio})
        self.actualizar_carrito()
        self.barcode_entry.focus()

    def agregar_servicio_personalizado(self):
        nombre = simpledialog.askstring("Descripción", "Escriba el nombre del servicio:", parent=self)
        if not nombre: return
        precio = simpledialog.askfloat("Costo del Servicio", f"Ingrese el costo para [{nombre.upper()}]:", minvalue=0, parent=self)
        if precio is None: return
        codigo_unico = f"SERV_VARIOS_{int(datetime.now().timestamp())}_{len(self.venta_items)}"
        self.venta_items.append({"codigo": codigo_unico, "nombre": nombre.upper(), "cantidad": 1, "precio": precio, "subtotal": precio})
        self.actualizar_carrito()
        self.barcode_entry.focus()

    def buscar_producto_evento(self, event):
        q = self.barcode_entry.get().strip()
        self.tree_busqueda.delete(*self.tree_busqueda.get_children())
        if not q: return
        p = "precio_mayoreo" if self.tipo_precio.get() == "Mayoreo" else "precio_publico"
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute(f"SELECT p.codigo, p.nombre, p.{p}, SUM(IFNULL(l.cantidad, 0)) FROM productos p LEFT JOIN lotes l ON p.codigo = l.codigo_producto WHERE p.nombre LIKE ? OR p.codigo LIKE ? GROUP BY p.codigo LIMIT 15", (f"%{q}%", f"%{q}%"))
        for r in cursor.fetchall(): self.tree_busqueda.insert("", "end", values=(r[0], r[1], f"${r[2]:.2f}", r[3] or 0))
        conn.close()

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
        if not codigo: return
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT nombre, precio_publico, precio_mayoreo FROM productos WHERE codigo=?", (codigo,))
        prod = cursor.fetchone()
        if not prod: 
            conn.close(); return messagebox.showerror("Error", "El producto no existe.")
            
        cursor.execute("SELECT SUM(cantidad) FROM lotes WHERE codigo_producto=?", (codigo,))
        stock = cursor.fetchone()[0] or 0
        conn.close()
        
        cant_carro = sum(i["cantidad"] for i in self.venta_items if i["codigo"] == codigo)
        if cant_carro + 1 > stock: return messagebox.showwarning("Stock Insuficiente", f"Solo quedan {stock} disponibles.")
        
        precio = prod[2] if self.tipo_precio.get() == "Mayoreo" else prod[1]
        
        found = False
        for item in self.venta_items:
            if item["codigo"] == codigo: 
                item["cantidad"] += 1; item["subtotal"] = item["cantidad"] * precio; found = True; break
        if not found: self.venta_items.append({"codigo": codigo, "nombre": prod[0], "cantidad": 1, "precio": precio, "subtotal": precio})
        self.actualizar_carrito()

    def actualizar_carrito(self):
        self.tree_venta.delete(*self.tree_venta.get_children())
        for i in self.venta_items: 
            self.tree_venta.insert("", "end", values=(i["nombre"], i["cantidad"], f"${i['precio']:.2f}", f"${i['subtotal']:.2f}"))
        self.total_label.config(text=f"${sum(i['subtotal'] for i in self.venta_items):,.2f}")

    def quitar_producto_carrito(self):
        sel = self.tree_venta.selection()
        if sel: del self.venta_items[self.tree_venta.index(sel[0])]; self.actualizar_carrito()

    def abrir_ventana_cobro(self, event=None):
        if not self.venta_items: return
        top = tk.Toplevel(self.winfo_toplevel()); top.title("Procesar Pago"); top.geometry("320x510")
        top.configure(bg="#F4F6F7"); top.grab_set()
        
        total = sum(i["subtotal"] for i in self.venta_items)
        tk.Label(top, text="SELECCIONE MÉTODO DE PAGO", font=("Segoe UI", 11, "bold"), bg="#F4F6F7", fg="#2C3E50").pack(pady=15)
        tk.Label(top, text=f"Total a Pagar: ${total:,.2f}", font=("Segoe UI", 14, "bold"), fg="#c0392b", bg="#F4F6F7").pack(pady=(0, 10))
        
        def pay(metodo): 
            monto_recibido = total
            cliente_credito = None
            
            if metodo == "EFECTIVO":
                monto_recibido = simpledialog.askfloat("Efectivo", f"Total: ${total:.2f}\n¿Con cuánto paga el cliente?", minvalue=total, parent=top)
                if monto_recibido is None: return 
                cambio = monto_recibido - total
                messagebox.showinfo("Cambio", f"El cambio a entregar es:\n\n${cambio:,.2f}", parent=top)
            
            elif metodo == "TRANSFERENCIA":
                digitos = simpledialog.askstring("Transferencia", "Ingrese los últimos dígitos o referencia de pago:", parent=top)
                if digitos is None: return  
                if digitos.strip():
                    metodo = f"TRANSF. {digitos.strip()}"
                else:
                    metodo = "TRANSFERENCIA"

            elif metodo == "TARJETA":
                digitos = simpledialog.askstring("Tarjeta", "Ingrese los últimos 4 dígitos o folio de autorización:", parent=top)
                if digitos is None: return  
                if digitos.strip():
                    metodo = f"TARJ. {digitos.strip()}"
                else:
                    metodo = "TARJETA"

            elif metodo == "OTROS":
                detalle = simpledialog.askstring("Otros Métodos", "Especifique (ej. Link MercadoPago, Vales, Cheque):", parent=top)
                if detalle is None: return  
                if detalle.strip():
                    metodo = f"OTRO: {detalle.strip().upper()}"
                else:
                    metodo = "OTROS"

            elif metodo == "CRÉDITO":
                if not self.verificar_pin(): return 
                cliente_credito = simpledialog.askstring("Crédito / Fiado", "Nombre completo del cliente a quien se le fía:", parent=top)
                if not cliente_credito: return
                monto_recibido = 0

            elif metodo == "ABONO":
                # Pago parcial: por ejemplo un total de $2000 de hospitalización
                # donde el cliente solo deja $800 hoy y el resto queda pendiente.
                cliente_abono = simpledialog.askstring("Abono / Pago Parcial", "Nombre completo del cliente / paciente:", parent=top)
                if not cliente_abono: return
                if total <= 0.01:
                    messagebox.showwarning("Aviso", "El total debe ser mayor a $0 para registrar un abono.", parent=top)
                    return
                monto_abonado = simpledialog.askfloat(
                    "Abono / Pago Parcial",
                    f"Total del servicio: ${total:,.2f}\n\n¿Cuánto abona el cliente HOY?\n(Debe ser menor al total; el resto quedará pendiente)",
                    minvalue=0.01, maxvalue=round(total - 0.01, 2), parent=top
                )
                if monto_abonado is None: return
                if not self.verificar_pin(): return
                monto_recibido = monto_abonado
                cliente_credito = cliente_abono

            self.finalizar_venta(metodo, monto_recibido, cliente_credito)
            top.destroy()
        
        metodos = [
            ("💵 EFECTIVO", "#27ae60"), 
            ("💳 TARJETA", "#8e44ad"), 
            ("🏦 TRANSFERENCIA", "#3498db"), 
            ("📦 OTROS", "#7f8c8d"),
            ("📝 CRÉDITO (FIAR)", "#e67e22"),
            ("🔖 ABONO (PAGO PARCIAL)", "#16a085"),
        ]
        
        for m, c in metodos: 
            tk.Button(top, text=m, bg=c, fg="white", font=("Segoe UI", 10, "bold"), height=2, command=lambda x=m: pay(x.split()[1])).pack(pady=4, fill="x", padx=25)

    def limpiar_texto_impresora(self, texto):
        # Esta función elimina acentos y asegura que sea texto plano ASCII puro para la Xprinter
        return unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('ASCII')

    def generar_ticket(self, folio, total, metodo, recibido, items_a_imprimir=None, saldo_pendiente=None):
        if items_a_imprimir is None:
            items_a_imprimir = self.venta_items
            
        ticket =  "   CLINICA VETERINARIA BEETHOVEN\n================================\n"
        ticket += f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\nFolio: {folio}\nCajero: {self.limpiar_texto_impresora(self.combo_medico.get()[:15])}\n"
        ticket += "--------------------------------\nCANT DESCRIPCION       IMPORTE\n--------------------------------\n"
        
        for item in items_a_imprimir:
            nom = self.limpiar_texto_impresora(item["nombre"])[:16].ljust(16)
            cant = f"{item['cantidad']}".ljust(4)
            subt = f"${item['subtotal']:.2f}".rjust(9)
            ticket += f"{cant} {nom} {subt}\n"

        ticket += f"================================\nTOTAL:                 ${total:>9.2f}\n"

        if saldo_pendiente is not None:
            # Ticket de ABONO / pago parcial
            ticket += f"ABONADO HOY:            ${recibido:>9.2f}\n"
            ticket += f"SALDO PENDIENTE:        ${saldo_pendiente:>9.2f}\n"
        else:
            # Alineación dinámica inteligente para el método de pago
            metodo_ticket = self.limpiar_texto_impresora(metodo)
            etiqueta_pago = f"PAGADO ({metodo_ticket}):"
            if len(etiqueta_pago) > 23:
                etiqueta_pago = etiqueta_pago[:23]  # Recortamos el texto límite por seguridad de margen
            ticket += f"{etiqueta_pago:<23}${recibido:>9.2f}\n"
            ticket += f"CAMBIO:                ${(recibido - total):>9.2f}\n"

        ticket += "================================\n   Gracias por su preferencia!  \n\n\n\n\n"
        try:
            with open("ticket_temp.txt", "w", encoding="ansi") as f: 
                f.write(ticket)
            os.startfile("ticket_temp.txt", "print")
        except: pass

    def finalizar_venta(self, metodo, monto_recibido, cliente=None):
        total = sum(i["subtotal"] for i in self.venta_items)
        now = datetime.now()
        folio_venta = now.strftime("%Y%m%d%H%M%S")
        
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("INSERT INTO ventas (fecha, folio, total, tipo_precio, metodo_pago, vendedor) VALUES (?,?,?,?,?,?)", 
                       (now.isoformat(), folio_venta, total, self.tipo_precio.get(), metodo, self.combo_medico.get()))
        vid = cursor.lastrowid
        
        for i in self.venta_items:
            req = i["cantidad"]
            if not str(i["codigo"]).startswith("SERV_"):
                cursor.execute("SELECT id, cantidad FROM lotes WHERE codigo_producto=? ORDER BY fecha_caducidad ASC", (i["codigo"],))
                for lid, lcant in cursor.fetchall():
                    if req <= 0: break
                    take = min(req, lcant)
                    cursor.execute("UPDATE lotes SET cantidad = cantidad - ? WHERE id=?", (take, lid))
                    req -= take
            # Guardamos también el NOMBRE REAL en 'descripcion' para que nunca se pierda
            # (antes solo se guardaba el código y por eso servicios personalizados
            # aparecían como "VARIOS" en los reportes).
            cursor.execute("INSERT INTO detalle_venta (venta_id, codigo_producto, cantidad, precio_unitario, subtotal, descripcion) VALUES (?,?,?,?,?,?)", 
                           (vid, i["codigo"], i["cantidad"], i["precio"], i["subtotal"], i["nombre"]))
        
        saldo_pendiente = None

        if metodo == "CRÉDITO" and cliente:
            cursor.execute("INSERT INTO notas_clientes (cliente, fecha, concepto, monto, estado) VALUES (?,?,?,?,?)",
                           (cliente.upper(), now.strftime("%d/%m/%Y"), f"Ticket {folio_venta}", total, "PENDIENTE"))

        elif metodo == "ABONO" and cliente:
            saldo_pendiente = round(total - monto_recibido, 2)
            # Registramos la deuda restante como cuenta por cobrar (igual que en CRÉDITO)
            cursor.execute("INSERT INTO notas_clientes (cliente, fecha, concepto, monto, estado) VALUES (?,?,?,?,?)",
                           (cliente.upper(), now.strftime("%d/%m/%Y"), f"Saldo pendiente Ticket {folio_venta}", saldo_pendiente, "PENDIENTE"))
            # Registramos el dinero que SÍ entró hoy a caja como un ingreso de abono
            # (esto hace que finanzas.py lo sume correctamente al efectivo del día)
            cursor.execute("INSERT INTO movimientos_caja (fecha, tipo, motivo, monto) VALUES (?,?,?,?)",
                           (now.isoformat(), "INGRESO", f"ABONO de {cliente.upper()} (Ticket {folio_venta})", monto_recibido))
                           
        conn.commit(); conn.close()
        
        # Guardamos en memoria por si quieren reimprimir
        self.ultimo_ticket = {
            "folio": folio_venta, "total": total, "metodo": metodo, 
            "recibido": monto_recibido, "items": list(self.venta_items),
            "saldo_pendiente": saldo_pendiente
        }
        
        # PREGUNTAR AL USUARIO SI DESEA IMPRIMIR
        respuesta = messagebox.askyesno("Venta Exitosa", "La venta se guardó correctamente en el sistema.\n\n¿Desea imprimir el ticket de compra?", parent=self)
        if respuesta:
            self.generar_ticket(folio_venta, total, metodo, monto_recibido, saldo_pendiente=saldo_pendiente)
        
        try:
            import serial
            cajon = serial.Serial('COM3', 9600, timeout=1)
            cajon.write(b'\x1B\x70\x00\x19\xFA') 
            cajon.close()
        except: pass
        self.venta_items = []; self.actualizar_carrito()

    def reimprimir_ultimo(self):
        if self.ultimo_ticket:
            self.generar_ticket(
                self.ultimo_ticket["folio"], 
                self.ultimo_ticket["total"], 
                self.ultimo_ticket["metodo"], 
                self.ultimo_ticket["recibido"], 
                self.ultimo_ticket["items"],
                saldo_pendiente=self.ultimo_ticket.get("saldo_pendiente")
            )
            messagebox.showinfo("Imprimiendo", "Se ha enviado el último ticket a la impresora.", parent=self)
        else:
            messagebox.showwarning("Sin datos", "No hay ninguna venta reciente en esta sesión para reimprimir.", parent=self)

    def retiro_dinero(self):
        m = simpledialog.askfloat("Retiro de Efectivo", "Ingrese el monto a retirar de caja:", minvalue=0, parent=self)
        if m is not None:
            mot = simpledialog.askstring("Motivo", "Escriba la razón del retiro:", parent=self)
            if mot: 
                conn = db.conectar(); cursor = conn.cursor()
                cursor.execute("INSERT INTO movimientos_caja (fecha, tipo, motivo, monto) VALUES (?,?,?,?)", (datetime.now().isoformat(), "RETIRO", mot.upper(), m))
                conn.commit(); conn.close()
                messagebox.showinfo("OK", "Retiro de caja registrado correctamente.")