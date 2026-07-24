import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from database import db
import config

class PestanaPersonal(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.COLOR_FONDO)
        self.verificar_tablas() 
        self.setup_ui()
        self.cargar_asistencias()
        self.cargar_adeudos()

    def verificar_tablas(self):
        conn = db.conectar()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nomina_empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT, empleado TEXT, periodo TEXT, 
                dias_asistidos INTEGER DEFAULT 6, hora_entrada TEXT DEFAULT '08:00', 
                hora_salida TEXT DEFAULT '15:00', detalles_asistencia TEXT, 
                sueldo_base REAL, monto_pagado REAL, sueldo REAL, 
                estado_pago TEXT, fecha_pago TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deudas_empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT, empleado TEXT, fecha TEXT, 
                concepto TEXT, monto REAL, estado TEXT DEFAULT 'PENDIENTE'
            )
        """)
        conn.commit(); conn.close()

    def verificar_pin(self):
        pin = simpledialog.askstring("Seguridad", "AUTORIZACIÓN REQUERIDA: Ingrese PIN de Administrador:", show='*', parent=self)
        if not pin: return False
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT valor FROM configuracion WHERE clave='pin_admin'")
        res = cursor.fetchone()
        conn.close()
        return (res[0] == pin) if res else (pin == "1234")

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"))
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_nomina = tk.Frame(self.notebook, bg="#ecf0f1")
        self.notebook.add(self.tab_nomina, text=" 🕒 RELOJ CHECADOR Y NÓMINA ")

        self.tab_adeudos = tk.Frame(self.notebook, bg="#ecf0f1")
        self.notebook.add(self.tab_adeudos, text=" 🛒 ADEUDOS Y PRÉSTAMOS ")

        self.construir_pestaña_nomina()
        self.construir_pestaña_adeudos()

    # =======================================================
    # PESTAÑA 1: RELOJ CHECADOR Y NÓMINA
    # =======================================================
    def construir_pestaña_nomina(self):
        f_izq = tk.Frame(self.tab_nomina, bg="#F4F6F7", width=380)
        f_izq.pack(side="left", fill="y", padx=10, pady=10)
        f_izq.pack_propagate(False)

        tk.Label(f_izq, text="⏱️ RELOJ CHECADOR DIARIO", font=("Segoe UI", 13, "bold"), bg="#F4F6F7", fg="#2C3E50").pack(pady=5)
        
        empleados_nomina = [emp for emp in config.LISTA_VENDEDORES if emp.upper() not in ["BARAQUIEL", "ADMIN", "GRAL"]]
        if not empleados_nomina: empleados_nomina = ["Sin empleados registrados"]

        tk.Label(f_izq, text="Empleado:", bg="#F4F6F7", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15)
        self.combo_empleado = ttk.Combobox(f_izq, values=empleados_nomina, state="readonly", font=("Segoe UI", 11))
        self.combo_empleado.pack(fill="x", padx=15, pady=2)
        self.combo_empleado.set(empleados_nomina[0])
        self.combo_empleado.bind("<<ComboboxSelected>>", self.cargar_datos_empleado)

        # Botones Automáticos de Checaje
        f_checador = tk.Frame(f_izq, bg="#F4F6F7")
        f_checador.pack(fill="x", padx=15, pady=10)
        tk.Button(f_checador, text="🟢 MARCAR ENTRADA AHORA", bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), command=lambda: self.checar_hora("entrada")).pack(side="left", expand=True, fill="x", padx=(0,2))
        tk.Button(f_checador, text="🔴 MARCAR SALIDA AHORA", bg="#c0392b", fg="white", font=("Segoe UI", 9, "bold"), command=lambda: self.checar_hora("salida")).pack(side="right", expand=True, fill="x", padx=(2,0))

        self.semana_actual = f"Semana del {datetime.now() - timedelta(days=datetime.now().weekday()):%d/%m}"
        tk.Label(f_izq, text=f"Registro de la {self.semana_actual}", bg="#F4F6F7", font=("Segoe UI", 10, "bold"), fg="#7f8c8d").pack(anchor="w", padx=15, pady=(5,0))

        # Tabla de Asistencia Semanal (Solo Lectura por Defecto)
        f_dias = tk.Frame(f_izq, bg="#F4F6F7")
        f_dias.pack(fill="x", padx=15, pady=5)
        
        tk.Label(f_dias, text="Día", bg="#F4F6F7", font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(f_dias, text="Entrada", bg="#F4F6F7", font=("Segoe UI", 8, "bold")).grid(row=0, column=1)
        tk.Label(f_dias, text="Salida", bg="#F4F6F7", font=("Segoe UI", 8, "bold")).grid(row=0, column=2)

        self.dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        self.inputs_dias = {}

        for i, dia in enumerate(self.dias_semana):
            var_chk = tk.IntVar(value=0) 
            chk = tk.Checkbutton(f_dias, text=dia[:2], variable=var_chk, bg="#F4F6F7", font=("Segoe UI", 9, "bold"), state="disabled")
            chk.grid(row=i+1, column=0, sticky="w")

            ent_in = ttk.Entry(f_dias, width=7, font=("Segoe UI", 9), justify="center", state="disabled")
            ent_in.grid(row=i+1, column=1, padx=2, pady=1)

            ent_out = ttk.Entry(f_dias, width=7, font=("Segoe UI", 9), justify="center", state="disabled")
            ent_out.grid(row=i+1, column=2, padx=2, pady=1)

            self.inputs_dias[dia] = {'chk': var_chk, 'in': ent_in, 'out': ent_out, 'chk_widget': chk}

        # Controles de Pago
        tk.Label(f_izq, text="Sueldo Fijo Semanal ($):", bg="#F4F6F7", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(5,0))
        self.e_sueldo_base = ttk.Entry(f_izq, font=("Segoe UI", 11))
        self.e_sueldo_base.pack(fill="x", padx=15, pady=2)
        self.e_sueldo_base.bind("<KeyRelease>", self.calcular_pago_automatico)

        f_total = tk.Frame(f_izq, bg="#D5F5E3", bd=1, relief="solid")
        f_total.pack(fill="x", padx=15, pady=10)
        tk.Label(f_total, text="PAGO PROPORCIONAL CALCULADO:", bg="#D5F5E3", font=("Segoe UI", 9, "bold")).pack(pady=(5,0))
        self.lbl_pago_final = tk.Label(f_total, text="$0.00", bg="#D5F5E3", fg="#145A32", font=("Segoe UI", 18, "bold"))
        self.lbl_pago_final.pack(pady=(0,5))
        self.pago_calculado = 0.0

        f_admin = tk.Frame(f_izq, bg="#F4F6F7")
        f_admin.pack(fill="x", padx=15, pady=5)
        tk.Button(f_admin, text="✏️ Habilitar Edición Manual", bg="#f39c12", fg="white", font=("Segoe UI", 8, "bold"), command=self.habilitar_edicion).pack(side="left", fill="x", expand=True, padx=(0,2))
        tk.Button(f_admin, text="💾 Guardar Cambios", bg="#2980b9", fg="white", font=("Segoe UI", 8, "bold"), command=lambda: self.guardar_asistencia(silencioso=False)).pack(side="right", fill="x", expand=True, padx=(2,0))

        # Panel Derecho: Historial
        f_der = tk.Frame(self.tab_nomina, bg="white", bd=0, highlightbackground="#D5D8DC", highlightthickness=1)
        f_der.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        f_head_der = tk.Frame(f_der, bg="#34495E", pady=8)
        f_head_der.pack(fill="x")
        tk.Label(f_head_der, text="📜 HISTORIAL DE ASISTENCIAS Y PAGOS", font=("Segoe UI", 11, "bold"), fg="white", bg="#34495E").pack()

        cols = ("ID", "Empleado", "Semana", "Asistencia", "Total Generado", "Pagado", "Por Pagar", "Estado")
        self.tree_nom = ttk.Treeview(f_der, columns=cols, show="headings", style="Premium.Treeview")
        for c, w in zip(cols, [30, 90, 110, 220, 90, 80, 80, 90]):
            self.tree_nom.heading(c, text=c)
            self.tree_nom.column(c, width=w, anchor="center" if c != "Asistencia" else "w") 

        self.tree_nom.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_nom.tag_configure("PENDIENTE", background="#FADBD8", foreground="#78281F") 
        self.tree_nom.tag_configure("PAGADO", background="#D5F5E3", foreground="#145A32") 

        f_btns = tk.Frame(f_der, bg="white", pady=5)
        f_btns.pack(fill="x", padx=10)
        tk.Button(f_btns, text="🗑️ ELIMINAR", bg="#c0392b", fg="white", font=("Segoe UI", 9, "bold"), command=self.eliminar_nomina).pack(side="left", padx=5)
        tk.Button(f_btns, text="💵 ABONAR O LIQUIDAR NÓMINA", bg="#2980b9", fg="white", font=("Segoe UI", 10, "bold"), command=self.registrar_abono_nomina).pack(side="right", padx=5)

    # =======================================================
    # PESTAÑA 2: ADEUDOS Y PRÉSTAMOS
    # =======================================================
    def construir_pestaña_adeudos(self):
        f_izq = tk.Frame(self.tab_adeudos, bg="#F4F6F7", width=380)
        f_izq.pack(side="left", fill="y", padx=10, pady=10)
        f_izq.pack_propagate(False)

        tk.Label(f_izq, text="🛒 REGISTRAR ADEUDO", font=("Segoe UI", 12, "bold"), bg="#F4F6F7", fg="#2C3E50").pack(pady=10)
        
        empleados_nomina = [emp for emp in config.LISTA_VENDEDORES if emp.upper() not in ["BARAQUIEL", "ADMIN", "GRAL"]]
        if not empleados_nomina: empleados_nomina = ["Sin empleados registrados"]

        tk.Label(f_izq, text="Empleado que debe:", bg="#F4F6F7", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15)
        self.c_emp_deuda = ttk.Combobox(f_izq, values=empleados_nomina, state="readonly", font=("Segoe UI", 11))
        self.c_emp_deuda.pack(fill="x", padx=15, pady=2)
        self.c_emp_deuda.set(empleados_nomina[0])
        self.c_emp_deuda.bind("<<ComboboxSelected>>", self.cargar_adeudos)

        tk.Label(f_izq, text="Concepto (Ej: Bulto Nupec, Adelanto):", bg="#F4F6F7", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(10,0))
        self.e_concepto_deuda = ttk.Entry(f_izq, font=("Segoe UI", 11))
        self.e_concepto_deuda.pack(fill="x", padx=15, pady=2)

        tk.Label(f_izq, text="Monto a deber ($):", bg="#F4F6F7", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(10,0))
        self.e_monto_deuda = ttk.Entry(f_izq, font=("Segoe UI", 11))
        self.e_monto_deuda.pack(fill="x", padx=15, pady=2)

        tk.Button(f_izq, text="➕ CARGAR DEUDA A EMPLEADO", bg="#e67e22", fg="white", font=("Segoe UI", 10, "bold"), command=self.guardar_adeudo).pack(fill="x", padx=15, pady=20)

        f_der = tk.Frame(self.tab_adeudos, bg="white", bd=0, highlightbackground="#D5D8DC", highlightthickness=1)
        f_der.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        f_head_der = tk.Frame(f_der, bg="#34495E", pady=8)
        f_head_der.pack(fill="x")
        tk.Label(f_head_der, text="📜 HISTORIAL DE DEUDAS Y ABONOS DEL PERSONAL", font=("Segoe UI", 11, "bold"), fg="white", bg="#34495E").pack()

        cols = ("ID", "Empleado", "Fecha", "Concepto / Detalles", "Deuda Restante", "Estado")
        self.tree_deudas = ttk.Treeview(f_der, columns=cols, show="headings", style="Premium.Treeview")
        for c, w in zip(cols, [40, 120, 90, 250, 100, 100]):
            self.tree_deudas.heading(c, text=c)
            self.tree_deudas.column(c, width=w, anchor="center" if c != "Concepto / Detalles" else "w") 

        self.tree_deudas.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_deudas.tag_configure("PENDIENTE", background="#FADBD8", foreground="#78281F") 
        self.tree_deudas.tag_configure("PAGADO", background="#D5F5E3", foreground="#145A32") 

        f_btns = tk.Frame(f_der, bg="white", pady=5)
        f_btns.pack(fill="x", padx=10)
        tk.Button(f_btns, text="🗑️ ELIMINAR", bg="#c0392b", fg="white", font=("Segoe UI", 9, "bold"), command=self.eliminar_adeudo).pack(side="left", padx=5)
        tk.Button(f_btns, text="💵 RECIBIR ABONO DE EMPLEADO", bg="#8e44ad", fg="white", font=("Segoe UI", 10, "bold"), command=self.abonar_adeudo).pack(side="right", padx=5)

    # =======================================================
    # FUNCIONES LÓGICAS: RELOJ CHECADOR AUTOMÁTICO
    # =======================================================
    def habilitar_edicion(self):
        if self.verificar_pin():
            for dia in self.dias_semana:
                self.inputs_dias[dia]['chk_widget'].config(state="normal")
                self.inputs_dias[dia]['in'].config(state="normal")
                self.inputs_dias[dia]['out'].config(state="normal")
            self.e_sueldo_base.config(state="normal")
            messagebox.showinfo("Desbloqueado", "Las horas y el sueldo han sido desbloqueados para edición manual.")

    def checar_hora(self, tipo):
        hoy_idx = datetime.now().weekday()
        dia_str = self.dias_semana[hoy_idx]
        hora_exacta = datetime.now().strftime("%H:%M")
        
        # Habilitar temporalmente para escribir la hora del sistema
        self.inputs_dias[dia_str]['in'].config(state="normal")
        self.inputs_dias[dia_str]['out'].config(state="normal")
        self.inputs_dias[dia_str]['chk'].set(1)

        if tipo == "entrada":
            self.inputs_dias[dia_str]['in'].delete(0, tk.END)
            self.inputs_dias[dia_str]['in'].insert(0, hora_exacta)
            mensaje = f"✅ ENTRADA registrada a las {hora_exacta}"
        else:
            self.inputs_dias[dia_str]['out'].delete(0, tk.END)
            self.inputs_dias[dia_str]['out'].insert(0, hora_exacta)
            mensaje = f"✅ SALIDA registrada a las {hora_exacta}"

        # Volver a bloquear para evitar alteraciones
        self.inputs_dias[dia_str]['in'].config(state="disabled")
        self.inputs_dias[dia_str]['out'].config(state="disabled")

        self.guardar_asistencia(silencioso=True)
        messagebox.showinfo("Checador", mensaje)

    def cargar_datos_empleado(self, event=None):
        emp = self.combo_empleado.get()
        
        # Resetear UI
        self.e_sueldo_base.config(state="normal")
        self.e_sueldo_base.delete(0, tk.END)
        for dia in self.dias_semana:
            self.inputs_dias[dia]['in'].config(state="normal")
            self.inputs_dias[dia]['out'].config(state="normal")
            self.inputs_dias[dia]['chk'].set(0)
            self.inputs_dias[dia]['in'].delete(0, tk.END)
            self.inputs_dias[dia]['out'].delete(0, tk.END)
            # Bloquear de nuevo
            self.inputs_dias[dia]['in'].config(state="disabled")
            self.inputs_dias[dia]['out'].config(state="disabled")

        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT detalles_asistencia, sueldo_base FROM nomina_empleados WHERE empleado=? AND periodo=? ORDER BY id DESC LIMIT 1", (emp, self.semana_actual.upper()))
        row = cursor.fetchone()
        conn.close()

        if row:
            detalles_str = row[0]
            sueldo_base = row[1] if row[1] else 0
            self.e_sueldo_base.insert(0, str(sueldo_base))
            
            if detalles_str:
                dias_trabajados = [d.strip() for d in detalles_str.split("|")]
                for d_reg in dias_trabajados:
                    if ":" in d_reg and "-" in d_reg:
                        dia_corto = d_reg.split(":")[0].strip()
                        horas = d_reg.split(":")[1].strip()
                        h_in, h_out = horas.split("-")

                        for dia_full in self.dias_semana:
                            if dia_full[:2] == dia_corto:
                                self.inputs_dias[dia_full]['chk'].set(1)
                                self.inputs_dias[dia_full]['in'].config(state="normal")
                                self.inputs_dias[dia_full]['out'].config(state="normal")
                                self.inputs_dias[dia_full]['in'].insert(0, h_in)
                                self.inputs_dias[dia_full]['out'].insert(0, h_out)
                                self.inputs_dias[dia_full]['in'].config(state="disabled")
                                self.inputs_dias[dia_full]['out'].config(state="disabled")

        self.calcular_pago_automatico()
        self.cargar_asistencias()

    def calcular_pago_automatico(self, event=None):
        if getattr(self, 'lbl_pago_final', None) is None: return

        try: base = float(self.e_sueldo_base.get() or 0)
        except ValueError:
            self.lbl_pago_final.config(text="$0.00")
            self.pago_calculado = 0.0
            return

        dias_marcados = sum(1 for dia, data in self.inputs_dias.items() if data['chk'].get() == 1)
        
        if dias_marcados >= 6: pago_final = base 
        else: pago_final = (base / 6.0) * dias_marcados
            
        self.lbl_pago_final.config(text=f"${pago_final:,.2f}")
        self.pago_calculado = pago_final

    def cargar_asistencias(self):
        self.tree_nom.delete(*self.tree_nom.get_children())
        filtro = self.combo_empleado.get()
        conn = db.conectar(); cursor = conn.cursor()
        
        cursor.execute("SELECT id, empleado, periodo, dias_asistidos, hora_entrada, hora_salida, sueldo, estado_pago, fecha_pago, detalles_asistencia, sueldo_base, monto_pagado FROM nomina_empleados WHERE empleado=? ORDER BY id DESC", (filtro,))
            
        for r in cursor.fetchall():
            detalle = r[9] if r[9] else f"{r[3]} días"
            total_generado = r[6] + (r[11] if r[11] else 0) 
            m_pagado = r[11] if r[11] is not None else 0.0
            s_restante = r[6] 
            periodo_limpio = r[2].split(" | ")[0] 
            self.tree_nom.insert("", "end", values=(r[0], r[1], periodo_limpio, detalle, f"${total_generado:,.2f}", f"${m_pagado:,.2f}", f"${s_restante:,.2f}", r[7]), tags=(r[7],))
        conn.close()

    def guardar_asistencia(self, silencioso=False):
        emp = self.combo_empleado.get()
        
        if not silencioso:
            if not self.verificar_pin(): return 
        
        try: sueldo_base_input = float(self.e_sueldo_base.get() or 0)
        except: 
            if not silencioso: messagebox.showwarning("Error", "Ingrese un sueldo base numérico.")
            return

        self.calcular_pago_automatico()
        sueldo_con_descuento = self.pago_calculado

        resumen_dias = []
        dias_count = 0
        for dia, widgets in self.inputs_dias.items():
            if widgets['chk'].get() == 1:
                dias_count += 1
                resumen_dias.append(f"{dia[:2]}: {widgets['in'].get()}-{widgets['out'].get()}")
                
        asistencia_str = " | ".join(resumen_dias)

        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT id, estado_pago, monto_pagado FROM nomina_empleados WHERE empleado=? AND periodo=?", (emp, self.semana_actual.upper()))
        existe = cursor.fetchone()
        
        if existe:
            nid, estado, pagado = existe
            nueva_deuda = sueldo_con_descuento - float(pagado)
            nuevo_estado = "PAGADO" if nueva_deuda <= 0 and estado == "PAGADO" else "PENDIENTE"
            cursor.execute("UPDATE nomina_empleados SET dias_asistidos=?, detalles_asistencia=?, sueldo_base=?, sueldo=?, estado_pago=? WHERE id=?", 
                           (dias_count, asistencia_str, sueldo_base_input, nueva_deuda, nuevo_estado, nid))
        else:
            cursor.execute("INSERT INTO nomina_empleados (empleado, periodo, dias_asistidos, sueldo, estado_pago, detalles_asistencia, sueldo_base, monto_pagado) VALUES (?,?,?,?,?,?,?,?)",
                           (emp, self.semana_actual.upper(), dias_count, sueldo_con_descuento, "PENDIENTE", asistencia_str, sueldo_base_input, 0.0))
                           
        conn.commit(); conn.close()
        self.cargar_asistencias()
        
        if not silencioso:
            messagebox.showinfo("Listo", f"Registro de {emp} guardado exitosamente.")

    def registrar_abono_nomina(self):
        sel = self.tree_nom.selection()
        if not sel: return messagebox.showwarning("Aviso", "Seleccione una semana pendiente de la lista.")
        
        vals = self.tree_nom.item(sel[0])["values"]
        nid, emp, periodo, estado = vals[0], vals[1], vals[2], vals[7]
        deuda_restante = float(vals[6].replace('$', '').replace(',', ''))
        pagado_actual = float(vals[5].replace('$', '').replace(',', ''))

        if estado == "PAGADO" or deuda_restante <= 0: return messagebox.showinfo("Info", "Esta semana ya está liquidada.")

        abono = simpledialog.askfloat("Abonar a Nómina", f"Saldo pendiente para {emp}: ${deuda_restante:,.2f}\n\n¿Cuánto dinero se le está pagando (abonando)?", minvalue=1, maxvalue=deuda_restante, parent=self)
        if not abono: return

        origen_caja = messagebox.askyesno("Origen de los fondos", f"¿Los ${abono:,.2f} se tomarán físicamente de la CAJA DE LA CLÍNICA?\n\n(Diga 'NO' si pagará con fondos externos).", parent=self)
        if origen_caja:
            if not self.verificar_pin(): return 

        nuevo_pagado = pagado_actual + abono
        nueva_deuda = deuda_restante - abono
        nuevo_estado = 'PAGADO' if nueva_deuda <= 0 else 'PENDIENTE'
        fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
        nuevo_periodo = f"{periodo} | Abono: ${abono:,.2f}"

        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("UPDATE nomina_empleados SET sueldo=?, estado_pago=?, periodo=?, fecha_pago=?, monto_pagado=? WHERE id=?", 
                       (nueva_deuda, nuevo_estado, nuevo_periodo, fecha_hoy, nuevo_pagado, nid))
        
        if origen_caja:
            cursor.execute("INSERT INTO movimientos_caja (fecha, tipo, motivo, monto) VALUES (?,?,?,?)",
                           (datetime.now().isoformat(), "RETIRO", f"PAGO NÓMINA: {emp}", abono))
            
        conn.commit(); conn.close()
        self.cargar_asistencias()
        messagebox.showinfo("Éxito", f"Pago de ${abono:,.2f} a {emp} registrado.")

    def eliminar_nomina(self):
        sel = self.tree_nom.selection()
        if not sel: return
        if not self.verificar_pin(): return
        if messagebox.askyesno("Borrar", "¿Eliminar este registro de nómina?"):
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("DELETE FROM nomina_empleados WHERE id=?", (self.tree_nom.item(sel[0])["values"][0],))
            conn.commit(); conn.close()
            self.cargar_asistencias()

    # =======================================================
    # FUNCIONES LÓGICAS: ADEUDOS DEL PERSONAL
    # =======================================================
    def cargar_adeudos(self, event=None):
        self.tree_deudas.delete(*self.tree_deudas.get_children())
        emp = self.c_emp_deuda.get()
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT id, empleado, fecha, concepto, monto, estado FROM deudas_empleados WHERE empleado=? ORDER BY id DESC", (emp,))
        for r in cursor.fetchall():
            self.tree_deudas.insert("", "end", values=(r[0], r[1], r[2], r[3], f"${r[4]:,.2f}", r[5]), tags=(r[5],))
        conn.close()

    def guardar_adeudo(self):
        emp = self.c_emp_deuda.get()
        conc = self.e_concepto_deuda.get().strip()
        try: monto = float(self.e_monto_deuda.get())
        except: return messagebox.showwarning("Error", "Ingrese un monto válido.")

        if not conc or monto <= 0: return messagebox.showwarning("Atención", "Llene el concepto y el monto.")
        if not self.verificar_pin(): return

        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("INSERT INTO deudas_empleados (empleado, fecha, concepto, monto, estado) VALUES (?,?,?,?,?)",
                       (emp, datetime.now().strftime("%d/%m/%Y"), conc.upper(), monto, "PENDIENTE"))
        conn.commit(); conn.close()
        
        self.e_concepto_deuda.delete(0, tk.END); self.e_monto_deuda.delete(0, tk.END)
        self.cargar_adeudos()
        messagebox.showinfo("Listo", f"Deuda de ${monto:,.2f} cargada a {emp}.")

    def abonar_adeudo(self):
        sel = self.tree_deudas.selection()
        if not sel: return messagebox.showwarning("Aviso", "Seleccione un adeudo pendiente.")
        
        vals = self.tree_deudas.item(sel[0])["values"]
        nid, emp, estado = vals[0], vals[1], vals[5]
        deuda_restante = float(vals[4].replace('$', '').replace(',', ''))

        if estado == "PAGADO" or deuda_restante <= 0: return messagebox.showinfo("Info", "Esta deuda ya fue liquidada.")

        abono = simpledialog.askfloat("Abono de Empleado", f"Deuda de {emp}: ${deuda_restante:,.2f}\n\n¿Cuánto dinero está entregando (abonando) a la clínica?", minvalue=1, maxvalue=deuda_restante, parent=self)
        if not abono: return
        if not self.verificar_pin(): return

        nueva_deuda = deuda_restante - abono
        nuevo_estado = 'PAGADO' if nueva_deuda <= 0 else 'PENDIENTE'
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")

        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("UPDATE deudas_empleados SET monto=?, estado=?, concepto = concepto || ? WHERE id=?", 
                       (nueva_deuda, nuevo_estado, f" | Abono ${abono:,.2f} ({fecha_hoy})", nid))
        
        cursor.execute("INSERT INTO movimientos_caja (fecha, tipo, motivo, monto) VALUES (?,?,?,?)",
                       (datetime.now().isoformat(), "INGRESO", f"ABONO DE EMPLEADO: {emp}", abono))
            
        conn.commit(); conn.close()
        self.cargar_adeudos()
        messagebox.showinfo("Éxito", f"Abono de ${abono:,.2f} registrado. El dinero ha ingresado a la caja de Finanzas.")

    def eliminar_adeudo(self):
        sel = self.tree_deudas.selection()
        if not sel: return
        if not self.verificar_pin(): return
        if messagebox.askyesno("Borrar", "¿Eliminar este registro de deuda?"):
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("DELETE FROM deudas_empleados WHERE id=?", (self.tree_deudas.item(sel[0])["values"][0],))
            conn.commit(); conn.close()
            self.cargar_adeudos()