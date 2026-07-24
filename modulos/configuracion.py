import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
from database import db
import config

class PestanaConfiguracion(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.COLOR_FONDO)
        # En lugar de pedir el PIN al arrancar, mostramos una pantalla bloqueada silenciosa
        self.pantalla_bloqueo()

    def pantalla_bloqueo(self):
        # Limpiamos todo lo que haya en la pestaña
        for w in self.winfo_children(): w.destroy()
        
        f_lock = tk.Frame(self, bg=config.COLOR_FONDO)
        f_lock.pack(expand=True)
        
        tk.Label(f_lock, text="🔒 ÁREA RESTRINGIDA", font=("Segoe UI", 24, "bold"), bg=config.COLOR_FONDO, fg="#c0392b").pack(pady=10)
        tk.Label(f_lock, text="Solo el Administrador puede modificar estos ajustes y realizar respaldos.", font=("Segoe UI", 12), bg=config.COLOR_FONDO, fg="#7f8c8d").pack(pady=10)
        
        tk.Button(f_lock, text="🔑 INGRESAR PIN PARA DESBLOQUEAR", bg="#2980b9", fg="white", font=("Segoe UI", 12, "bold"), command=self.verificar_pin_y_cargar, padx=20, pady=10).pack(pady=20)

    def verificar_pin_y_cargar(self):
        pin = simpledialog.askstring("Seguridad", "Ingrese PIN de Administrador para acceder a Configuración:", show='*', parent=self)
        if not pin: return # Si le da a cancelar, no hace nada
        
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT valor FROM configuracion WHERE clave='pin_admin'")
        res = cursor.fetchone()
        conn.close()
        
        pin_real = res[0] if res else "1234"
        if pin == pin_real:
            # Si el PIN es correcto, quitamos el candado y dibujamos las opciones
            for w in self.winfo_children(): w.destroy() 
            self.setup_ui()
            self.cargar_datos()
        else:
            messagebox.showerror("Acceso Denegado", "El PIN ingresado es incorrecto.")

    # A partir de aquí todo está protegido. Los empleados jamás verán esto sin el PIN.
    def setup_ui(self):
        f_main = tk.Frame(self, bg=config.COLOR_FONDO)
        f_main.pack(fill="both", expand=True, padx=40, pady=20)

        # Botón para volver a bloquear la pantalla y que no se quede abierta si el admin se va
        f_head = tk.Frame(f_main, bg=config.COLOR_FONDO)
        f_head.pack(fill="x", pady=(0, 20))
        tk.Label(f_head, text="⚙️ CONFIGURACIÓN GENERAL DEL SISTEMA", font=("Segoe UI", 16, "bold"), bg=config.COLOR_FONDO, fg="#2C3E50").pack(side="left")
        tk.Button(f_head, text="🔒 BLOQUEAR PANTALLA", bg="#c0392b", fg="white", font=("Segoe UI", 9, "bold"), command=self.pantalla_bloqueo).pack(side="right")

        # --- PANEL IZQUIERDO: DATOS DE LA CLÍNICA (MARCA BLANCA) ---
        f_izq = tk.LabelFrame(f_main, text=" Datos del Negocio (Para Tickets y Reportes) ", bg="white", font=("Segoe UI", 11, "bold"), padx=20, pady=20)
        f_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))

        campos = [("Nombre de la Clínica:", "nombre_clinica"), 
                  ("Dirección:", "direccion_clinica"), 
                  ("Teléfono:", "telefono_clinica"), 
                  ("Mensaje al final del Ticket:", "mensaje_ticket")]
        
        self.entradas = {}
        for texto, clave in campos:
            tk.Label(f_izq, text=texto, bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))
            ent = ttk.Entry(f_izq, font=("Segoe UI", 11))
            ent.pack(fill="x")
            self.entradas[clave] = ent

        tk.Button(f_izq, text="💾 GUARDAR DATOS DEL NEGOCIO", bg="#2980b9", fg="white", font=("Segoe UI", 10, "bold"), command=self.guardar_datos).pack(pady=20, fill="x")

        # --- PANEL DERECHO: RESPALDOS Y SEGURIDAD ---
        f_der = tk.LabelFrame(f_main, text=" Seguridad y Respaldos Automáticos ", bg="white", font=("Segoe UI", 11, "bold"), padx=20, pady=20)
        f_der.pack(side="right", fill="both", expand=True, padx=(10, 0))

        tk.Label(f_der, text="Carpeta / Memoria USB para Respaldos:", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))
        
        f_ruta = tk.Frame(f_der, bg="white")
        f_ruta.pack(fill="x")
        self.e_ruta_usb = ttk.Entry(f_ruta, font=("Segoe UI", 10))
        self.e_ruta_usb.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(f_ruta, text="📁 SELECCIONAR USB", bg="#f39c12", fg="white", font=("Segoe UI", 9, "bold"), command=self.seleccionar_ruta).pack(side="right")

        tk.Label(f_der, text="* El sistema hará una copia automática a esta USB al cerrarse.", bg="white", fg="#7f8c8d", font=("Segoe UI", 8, "italic")).pack(anchor="w", pady=5)

        tk.Button(f_der, text="🔄 HACER RESPALDO MANUAL AHORA", bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"), command=self.respaldo_manual).pack(pady=20, fill="x")

        tk.Label(f_der, text="Cambiar PIN de Administrador:", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))
        self.e_nuevo_pin = ttk.Entry(f_der, font=("Segoe UI", 11), show="*")
        self.e_nuevo_pin.pack(fill="x")
        tk.Button(f_der, text="🔑 ACTUALIZAR PIN", bg="#c0392b", fg="white", font=("Segoe UI", 10, "bold"), command=self.cambiar_pin).pack(pady=10, fill="x")

    def cargar_datos(self):
        conn = db.conectar(); cursor = conn.cursor()
        claves = ["nombre_clinica", "direccion_clinica", "telefono_clinica", "mensaje_ticket", "ruta_respaldo_usb"]
        
        for clave in claves:
            cursor.execute("SELECT valor FROM configuracion WHERE clave=?", (clave,))
            res = cursor.fetchone()
            if res:
                if clave in self.entradas:
                    self.entradas[clave].insert(0, res[0])
                elif clave == "ruta_respaldo_usb":
                    self.e_ruta_usb.insert(0, res[0])
        conn.close()

    def guardar_datos(self):
        conn = db.conectar(); cursor = conn.cursor()
        for clave, ent in self.entradas.items():
            valor = ent.get().strip()
            cursor.execute("SELECT clave FROM configuracion WHERE clave=?", (clave,))
            if cursor.fetchone():
                cursor.execute("UPDATE configuracion SET valor=? WHERE clave=?", (valor, clave))
            else:
                cursor.execute("INSERT INTO configuracion (clave, valor) VALUES (?, ?)", (clave, valor))
        conn.commit(); conn.close()
        messagebox.showinfo("Éxito", "Los datos del negocio se han actualizado. Aparecerán en los próximos tickets.")

    def seleccionar_ruta(self):
        ruta = filedialog.askdirectory(title="Selecciona la memoria USB o carpeta de respaldo")
        if ruta:
            self.e_ruta_usb.delete(0, tk.END)
            self.e_ruta_usb.insert(0, ruta)
            conn = db.conectar(); cursor = conn.cursor()
            cursor.execute("SELECT clave FROM configuracion WHERE clave='ruta_respaldo_usb'")
            if cursor.fetchone(): cursor.execute("UPDATE configuracion SET valor=? WHERE clave='ruta_respaldo_usb'", (ruta,))
            else: cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('ruta_respaldo_usb', ?)", (ruta,))
            conn.commit(); conn.close()
            messagebox.showinfo("Ruta Guardada", "Las copias de seguridad automáticas se guardarán en esta ruta.")

    def respaldo_manual(self):
        ruta_usb = self.e_ruta_usb.get().strip()
        if not ruta_usb or not os.path.exists(ruta_usb):
            return messagebox.showerror("Error", "La ruta de la memoria USB no existe o no está conectada.")
        
        try:
            fecha_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nombre_respaldo = f"Respaldo_Vet_{fecha_str}.db"
            ruta_destino = os.path.join(ruta_usb, nombre_respaldo)
            
            shutil.copy2("veterinaria.db", ruta_destino)
            messagebox.showinfo("Respaldo Exitoso", f"Se ha guardado una copia exacta de la base de datos en:\n\n{ruta_destino}")
        except Exception as e:
            messagebox.showerror("Error de Respaldo", f"Hubo un problema al copiar el archivo: {e}")

    def cambiar_pin(self):
        nuevo_pin = self.e_nuevo_pin.get().strip()
        if not nuevo_pin: return
        conn = db.conectar(); cursor = conn.cursor()
        cursor.execute("SELECT clave FROM configuracion WHERE clave='pin_admin'")
        if cursor.fetchone(): cursor.execute("UPDATE configuracion SET valor=? WHERE clave='pin_admin'", (nuevo_pin,))
        else: cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('pin_admin', ?)", (nuevo_pin,))
        conn.commit(); conn.close()
        self.e_nuevo_pin.delete(0, tk.END)
        messagebox.showinfo("PIN Actualizado", "El PIN de Administrador ha sido cambiado con éxito.")