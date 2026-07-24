import tkinter as tk
from tkinter import ttk, messagebox
import config
from database import db
import uuid
import os
import hashlib
import shutil
from datetime import datetime

# --- IMPORTAMOS A LOS MÓDULOS ESPECIALISTAS ---
from modulos.configuracion import PestanaConfiguracion
from modulos.caja import PestanaCaja
from modulos.pacientes import PestanaPacientes
from modulos.inventario import PestanaInventario
from modulos.agenda import PestanaAgenda
from modulos.finanzas import PestanaFinanzas
from modulos.proveedores import PestanaProveedores
from modulos.personal import PestanaPersonal

class VeterinariaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CLÍNICA VETERINARIA BEETHOVEN - v39.0 (Paleta Profesional)")
        self.root.state('zoomed')
        self.root.configure(bg="#F4F6F7") 
        
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_y_respaldar)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#F4F6F7")
        style.configure("TLabel", background="#F4F6F7", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 9, "bold"), cursor="hand2")
        
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30, background="white", fieldbackground="white", foreground="#2C3E50")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#2C3E50", foreground="white", relief="flat")
        style.map("Treeview.Heading", background=[('active', '#34495E')])
        style.map("Treeview", background=[('selected', '#455A64')], foreground=[('selected', 'white')])

        self.machine_uuid = str(uuid.getnode())

        if not self.verificar_licencia():
            self.mostrar_ventana_activacion()
            return

        db.inicializa_db()
        self.setup_gui()
        
        # --- LANZAR ALERTA MEDIO SEGUNDO DESPUÉS DE ABRIR EL SISTEMA ---
        self.root.after(500, self.mostrar_alertas_inicio)

    # --- ALERTA DE INVENTARIO (DASHBOARD) ---
    def mostrar_alertas_inicio(self):
        conn = db.conectar(); cursor = conn.cursor()
        alertas_inv = []

        # Buscar Inventario Bajo (Agrupado para evitar duplicados)
        try:
            cursor.execute("""
                SELECT p.nombre, SUM(l.cantidad)
                FROM lotes l 
                JOIN productos p ON l.codigo_producto = p.codigo
                GROUP BY p.nombre 
                HAVING SUM(l.cantidad) <= 5 
                ORDER BY SUM(l.cantidad) ASC
            """)
            for prod, cant in cursor.fetchall(): 
                alertas_inv.append((prod, cant))
        except: pass

        conn.close()

        # Si no hay productos bajos, no mostramos la ventana y entran directo a la caja
        if not alertas_inv: return

        # Diseño de la Alerta de Inventario
        top = tk.Toplevel(self.root)
        top.title("Alerta de Inventario")
        top.geometry("550x500")
        top.configure(bg="white")
        top.grab_set()

        f_head = tk.Frame(top, bg="#e74c3c", pady=15)
        f_head.pack(fill="x")
        tk.Label(f_head, text="🔔 ALERTA DE INVENTARIO", font=("Segoe UI", 16, "bold"), bg="#e74c3c", fg="white").pack()
        tk.Label(f_head, text="Productos que requieren reabastecimiento", font=("Segoe UI", 10), bg="#e74c3c", fg="#fadbd8").pack()

        f_body = tk.Frame(top, bg="white", padx=20, pady=20)
        f_body.pack(fill="both", expand=True)

        # Barra de desplazamiento por si hay muchos productos
        scrollbar = ttk.Scrollbar(f_body)
        scrollbar.pack(side="right", fill="y")

        txt = tk.Text(f_body, font=("Segoe UI", 11), bg="white", relief="flat", yscrollcommand=scrollbar.set, padx=10)
        txt.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=txt.yview)

        # Configuración de los colores y tipografías
        txt.tag_configure("titulo_inv", foreground="#d35400", font=("Segoe UI", 12, "bold"), spacing1=5, spacing3=10)
        txt.tag_configure("item_rojo", foreground="#c0392b", font=("Segoe UI", 11, "bold"), lmargin1=20, spacing3=5)
        txt.tag_configure("item_naranja", foreground="#d68910", font=("Segoe UI", 11), lmargin1=20, spacing3=5)

        # Pintar Inventario
        txt.insert(tk.END, "📦 LISTA DE COMPRAS SUGERIDA:\n", "titulo_inv")
        for prod, cant in alertas_inv:
            if cant <= 0:
                txt.insert(tk.END, f"• ¡AGOTADO! (0 pzas) - {prod}\n", "item_rojo")
            else:
                txt.insert(tk.END, f"• Quedan {cant} pzas - {prod}\n", "item_naranja")

        txt.config(state="disabled") # Bloquear edición

        tk.Button(top, text="👍 ENTENDIDO", bg="#27ae60", fg="white", font=("Segoe UI", 11, "bold"), command=top.destroy, height=2).pack(fill="x", padx=40, pady=20)

    # --- SEGURIDAD Y LICENCIA ---
    def verificar_licencia(self):
        if os.path.exists("licencia.dat"):
            try:
                with open("licencia.dat", "r") as f: stored_key = f.read().strip()
                combined = self.machine_uuid + config.SECRET_KEY
                hash_obj = hashlib.sha256(combined.encode('utf-8'))
                hash_hex = hash_obj.hexdigest()[:16]
                formatted = '-'.join([hash_hex[i:i+4] for i in range(0, 16, 4)])
                return stored_key == formatted
            except: return False
        return False

    def mostrar_ventana_activacion(self):
        activation_win = tk.Toplevel(self.root)
        activation_win.title("ACTIVACIÓN DEL SISTEMA")
        activation_win.geometry("500x300")
        activation_win.configure(bg="#2c3e50")
        activation_win.grab_set()
        
        tk.Label(activation_win, text="ID SISTEMA:", font=("Arial", 14), bg="#2c3e50", fg="white").pack(pady=10)
        entry_uuid = tk.Entry(activation_win, font=("Arial", 14), justify="center")
        entry_uuid.insert(0, self.machine_uuid)
        entry_uuid.pack(pady=5, fill="x", padx=40)
        
        tk.Label(activation_win, text="LICENCIA:", font=("Arial", 14), bg="#2c3e50", fg="white").pack(pady=10)
        license_entry = tk.Entry(activation_win, font=("Arial", 14), justify="center")
        license_entry.pack(pady=5, fill="x", padx=40)
        
        def activar():
            entered_key = license_entry.get().strip()
            combined = self.machine_uuid + config.SECRET_KEY
            hash_obj = hashlib.sha256(combined.encode('utf-8'))
            hash_hex = hash_obj.hexdigest()[:16]
            expected = '-'.join([hash_hex[i:i+4] for i in range(0, 16, 4)])
            
            if entered_key == expected:
                with open("licencia.dat", "w") as f: f.write(entered_key)
                messagebox.showinfo("Éxito", "Sistema Activado Correctamente.")
                activation_win.destroy()
                db.inicializa_db()
                self.setup_gui()
            else: 
                messagebox.showerror("Error", "Licencia Inválida.", parent=activation_win)

        tk.Button(activation_win, text="ACTIVAR SISTEMA", command=activar, bg="#27ae60", fg="white", font=("Segoe UI", 11, "bold")).pack(pady=20)

    # --- GUI PRINCIPAL ---
    def setup_gui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_caja = PestanaCaja(self.notebook)
        self.tab_pacientes = PestanaPacientes(self.notebook)
        self.tab_inventario = PestanaInventario(self.notebook)
        self.tab_agenda = PestanaAgenda(self.notebook)
        self.tab_finanzas = PestanaFinanzas(self.notebook)
        self.tab_proveedores = PestanaProveedores(self.notebook) 
        self.tab_personal = PestanaPersonal(self.notebook) 
        self.tab_config = PestanaConfiguracion(self.notebook)

        self.notebook.add(self.tab_caja, text=" 🛒 CAJA ")
        self.notebook.add(self.tab_pacientes, text=" 🐶 PACIENTES ")
        self.notebook.add(self.tab_inventario, text=" 📦 INVENTARIO ")
        self.notebook.add(self.tab_agenda, text=" 📅 AGENDA ")
        self.notebook.add(self.tab_finanzas, text=" 💰 FINANZAS ")
        self.notebook.add(self.tab_proveedores, text=" 🤝 PROVEEDORES ") 
        self.notebook.add(self.tab_personal, text=" PERSONAL ")
        self.notebook.add(self.tab_config, text=" ⚙️ CONFIGURACIÓN ")

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event):
        selected_tab = self.notebook.index(self.notebook.select())
        tab_text = self.notebook.tab(selected_tab, "text").strip()
        
        if "INVENTARIO" in tab_text: 
            self.tab_inventario.cargar_inventario_completo()
        elif "FINANZAS" in tab_text: 
            self.tab_finanzas.cargar_fechas_historial()
            self.tab_finanzas.cargar_finanzas()
        elif "AGENDA" in tab_text: 
            self.tab_agenda.cargar_citas()
        elif "PACIENTES" in tab_text: 
            self.tab_pacientes.buscar_pacientes()
        elif "PROVEEDORES" in tab_text: 
            self.tab_proveedores.cargar_proveedores() 

    # --- RESPALDO AUTOMÁTICO EN USB AL CERRAR ---
    def cerrar_y_respaldar(self):
        db_original = "veterinaria.db"
        
        if not os.path.exists(db_original):
            self.root.destroy()
            return
            
        unidades_usb = []
        for letra in range(ord('D'), ord('Z') + 1):
            ruta_letra = f"{chr(letra)}:\\"
            if os.path.exists(ruta_letra):
                unidades_usb.append(ruta_letra)
                
        if unidades_usb:
            carpeta_backup = os.path.join(unidades_usb[0], "Respaldos_Beethoven")
            if not os.path.exists(carpeta_backup):
                try: os.makedirs(carpeta_backup)
                except: pass
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_backup = f"veterinaria_backup_{timestamp}.db"
            ruta_destino = os.path.join(carpeta_backup, nombre_backup)
            
            try:
                shutil.copy2(db_original, ruta_destino)
                limite_respaldos = 10
                archivos_backup = [os.path.join(carpeta_backup, f) for f in os.listdir(carpeta_backup) if f.startswith("veterinaria_backup_") and f.endswith(".db")]
                archivos_backup.sort(key=os.path.getmtime)
                
                if len(archivos_backup) > limite_respaldos:
                    archivos_a_borrar = archivos_backup[:-limite_respaldos]
                    for archivo_viejo in archivos_a_borrar: os.remove(archivo_viejo)
                
            except Exception as e:
                pass # Silenciar errores si falla para no asustar al empleado
        else:
            pass # Silenciar advertencias si no hay USB para que cierre rápido
            
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VeterinariaApp(root)
    root.mainloop()