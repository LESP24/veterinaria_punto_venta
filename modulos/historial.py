import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
from database import db

# Colores basados en el formato físico
BG_AZUL_CLARO = "#D4E6F1"
BG_AZUL_OSCURO = "#2471A3"
FG_BLANCO = "#FFFFFF"
FG_NEGRO = "#000000"

class VentanaConsultaMedica(tk.Toplevel):
    def __init__(self, parent, paciente_id, nombre_paciente, medico_atiende):
        super().__init__(parent)
        self.paciente_id = paciente_id
        self.nombre_paciente = nombre_paciente
        self.medico_atiende = medico_atiende
        
        self.title(f"HOSPITAL VETERINARIO BEETHOVEN - Ficha Clínica: {nombre_paciente}")
        self.geometry("1200x800") # Ventana más ancha para simular el papel
        self.configure(bg=BG_AZUL_CLARO)
        self.grab_set()

        # Diccionarios maestros para recolectar TODA la información al guardar
        self.vars_check = {}  # Para Checkboxes y Radiobuttons
        self.vars_entry = {}  # Para Entradas de texto corto
        self.vars_text = {}   # Para Áreas de texto grandes

        self.setup_ui()

    def setup_ui(self):
        # --- ENCABEZADO ESTILO PAPEL ---
        f_header = tk.Frame(self, bg=BG_AZUL_CLARO, pady=10)
        f_header.pack(fill="x", padx=20)
        
        tk.Label(f_header, text="Hospital Veterinario\nBeethoven", font=("Arial", 24, "bold"), bg=BG_AZUL_CLARO, fg=FG_NEGRO).pack(side="left")
        
        f_datos_top = tk.Frame(f_header, bg=BG_AZUL_CLARO)
        f_datos_top.pack(side="right")
        tk.Label(f_datos_top, text=f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", font=("Arial", 12, "bold"), bg=BG_AZUL_CLARO).pack(anchor="e")
        tk.Label(f_datos_top, text=f"Paciente: {self.nombre_paciente}", font=("Arial", 12), bg=BG_AZUL_CLARO).pack(anchor="e")
        tk.Label(f_datos_top, text=f"Atiende: {self.medico_atiende}", font=("Arial", 12), bg=BG_AZUL_CLARO).pack(anchor="e")

        # --- SISTEMA DE PESTAÑAS ---
        style = ttk.Style()
        style.configure("TNotebook", background=BG_AZUL_CLARO)
        style.configure("TNotebook.Tab", font=("Arial", 10, "bold"), padding=[15, 5])
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        hoja1 = tk.Frame(self.notebook, bg=BG_AZUL_CLARO); self.notebook.add(hoja1, text=" PÁGINA 1: Anamnesis ")
        hoja2 = tk.Frame(self.notebook, bg=BG_AZUL_CLARO); self.notebook.add(hoja2, text=" PÁGINA 2: Revisión ")
        hoja3 = tk.Frame(self.notebook, bg=BG_AZUL_CLARO); self.notebook.add(hoja3, text=" PÁGINA 3: Alteraciones ")
        hoja4 = tk.Frame(self.notebook, bg=BG_AZUL_CLARO); self.notebook.add(hoja4, text=" PÁGINA 4: Diagnóstico ")

        self.construir_hoja_1(hoja1)
        self.construir_hoja_2(hoja2)
        self.construir_hoja_3(hoja3)
        self.construir_hoja_4(hoja4)

        # --- BOTÓN DE GUARDADO GLOBAL ---
        f_footer = tk.Frame(self, bg=BG_AZUL_CLARO, pady=10)
        f_footer.pack(fill="x")
        tk.Button(f_footer, text="💾 GUARDAR FICHA CLÍNICA COMPLETA", bg="#27ae60", fg="white", font=("Arial", 12, "bold"), height=2, command=self.guardar_consulta).pack(fill="x", padx=20)

    # ==========================================
    # HERRAMIENTAS DE CONSTRUCCIÓN VISUAL
    # ==========================================
    def _crear_scroll(self, parent):
        canvas = tk.Canvas(parent, bg=BG_AZUL_CLARO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG_AZUL_CLARO)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y"); canvas.pack(side="left", fill="both", expand=True)
        return scrollable_frame

    def _titulo_seccion(self, parent, texto):
        lbl = tk.Label(parent, text=texto, font=("Arial", 11, "bold"), bg=BG_AZUL_OSCURO, fg=FG_BLANCO, anchor="w", padx=10, pady=5)
        lbl.pack(fill="x", pady=(15, 5))
        return lbl

    def _crear_area_texto(self, parent, key, altura=4):
        t = tk.Text(parent, height=altura, font=("Arial", 10), bd=0, bg="#EAF2F8")
        t.pack(fill="x", padx=10, pady=2)
        self.vars_text[key] = t
        return t

    def _crear_grid_checks(self, parent, titulo, opciones, prefijo_key, col_count=1):
        f_main = tk.Frame(parent, bg=BG_AZUL_CLARO)
        tk.Label(f_main, text=titulo, font=("Arial", 10, "bold"), bg=BG_AZUL_CLARO).pack(anchor="w")
        f_grid = tk.Frame(f_main, bg=BG_AZUL_CLARO)
        f_grid.pack(fill="x", padx=5)
        
        for i, op in enumerate(opciones):
            var = tk.IntVar()
            key = f"{prefijo_key}_{op.replace(' ', '_').lower()}"
            self.vars_check[key] = var
            cb = tk.Checkbutton(f_grid, text=op, variable=var, bg=BG_AZUL_CLARO, font=("Arial", 9), activebackground=BG_AZUL_CLARO)
            cb.grid(row=i // col_count, column=i % col_count, sticky="w")
        return f_main

    def _crear_tabla_dinamica(self, parent, columnas, filas, prefijo_key):
        f_tabla = tk.Frame(parent, bg=BG_AZUL_CLARO)
        f_tabla.pack(fill="x", padx=10, pady=5)
        
        # Encabezados
        for col, nombre in enumerate(columnas):
            tk.Label(f_tabla, text=nombre, font=("Arial", 9, "bold"), bg=BG_AZUL_CLARO).grid(row=0, column=col, padx=2)
            
        # Filas de Entries
        for f in range(1, filas + 1):
            for c, _ in enumerate(columnas):
                ent = tk.Entry(f_tabla, font=("Arial", 10), bg="#EAF2F8", bd=0, justify="center")
                ent.grid(row=f, column=c, padx=2, pady=2, sticky="ew")
                f_tabla.columnconfigure(c, weight=1)
                self.vars_entry[f"{prefijo_key}_f{f}_c{c}"] = ent

    # ==========================================
    # HOJA 1: ANAMNESIS (Foto 1)
    # ==========================================
    def construir_hoja_1(self, parent):
        sf = self._crear_scroll(parent)

        self._titulo_seccion(sf, "Historia Reciente")
        self._crear_area_texto(sf, "historia_reciente", 5)

        self._titulo_seccion(sf, "Anamnesis")
        tk.Label(sf, text="Motivo de Consulta", font=("Arial", 10, "bold"), bg=BG_AZUL_CLARO).pack(anchor="w", padx=10)
        self._crear_area_texto(sf, "motivo_consulta", 3)
        
        tk.Label(sf, text="Tiempo de Evolución", font=("Arial", 10, "bold"), bg=BG_AZUL_CLARO).pack(anchor="w", padx=10)
        ent_tiempo = tk.Entry(sf, font=("Arial", 10), bg="#EAF2F8", bd=0)
        ent_tiempo.pack(fill="x", padx=10, pady=2)
        self.vars_entry["tiempo_evolucion"] = ent_tiempo

        tk.Label(sf, text="Tratamiento Anterior", font=("Arial", 10, "bold"), bg=BG_AZUL_CLARO).pack(anchor="w", padx=10, pady=(10,0))
        self._crear_tabla_dinamica(sf, ["Nombre", "Concentración", "Dosis", "Frecuencia", "Tiempo Dado"], 4, "tratamiento_ant")

        tk.Label(sf, text="Enfermedades Anteriores", font=("Arial", 10, "bold"), bg=BG_AZUL_CLARO).pack(anchor="w", padx=10, pady=(10,0))
        self._crear_tabla_dinamica(sf, ["Nombre de la Enfermedad", "Secuelas"], 3, "enfermedades_ant")

        # Fila final de hoja 1
        f_bot = tk.Frame(sf, bg=BG_AZUL_CLARO)
        f_bot.pack(fill="x", padx=10, pady=10)
        
        self._crear_grid_checks(f_bot, "Alimentación Acostumbrada", ["Seco", "Humedo", "Enlatado", "Miscelanea Casera", "Otro"], "alimentacion").grid(row=0, column=0, sticky="nw")
        
        f_extra = tk.Frame(f_bot, bg=BG_AZUL_CLARO)
        f_extra.grid(row=0, column=1, sticky="nw", padx=20)
        self._crear_grid_checks(f_extra, "Fue con Diagnostico", ["Formal", "Informal"], "diag_previo").pack(anchor="w")
        self._crear_grid_checks(f_extra, "Contacto Animales Enfermos", ["Si", "No"], "contacto_enfermos").pack(anchor="w", pady=(10,0))
        
        self._crear_grid_checks(f_bot, "Forma de Administración", ["Libre Acceso", "Restringido"], "admin_alimento").grid(row=0, column=2, sticky="nw")

    # ==========================================
    # HOJA 2: REVISIÓN (Foto 2)
    # ==========================================
    def construir_hoja_2(self, parent):
        sf = self._crear_scroll(parent)
        
        f_grid = tk.Frame(sf, bg=BG_AZUL_CLARO)
        f_grid.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Columna 1
        c1 = tk.Frame(f_grid, bg=BG_AZUL_CLARO); c1.grid(row=0, column=0, sticky="nw", padx=10)
        self._crear_grid_checks(c1, "Vacunación Vigentes (Perros)", ["Parvovirus", "Distemper", "Hepatitis", "Traqueobronquitis", "Coronavirus", "Leptospira", "Rabia"], "vac_perro").pack(anchor="w", pady=5)
        self._crear_grid_checks(c1, "Vacunación Vigentes (Gatos)", ["Panleucopenia", "Rinotraqueitis", "Calcivirus", "Leucemia", "Peritonitis", "Rabia"], "vac_gato").pack(anchor="w", pady=5)
        self._crear_grid_checks(c1, "Emisión de Orina", ["Normal", "Poliuria", "Oliguria", "Poliaquiuria", "Color Normal", "Con Sangre", "Con Pus", "Pegajoza", "Arenilla", "Olor Fuerte", "Disuria", "Anuria"], "orina", col_count=2).pack(anchor="w", pady=5)
        self._crear_grid_checks(c1, "Defecación", ["Normal", "No Defeca", "Diarrea", "Con Moco", "Con Sangre", "Estreñimiento", "Sin Digerir", "Con Objetos", "Flatulencias"], "defecacion", col_count=2).pack(anchor="w", pady=5)

        # Columna 2
        c2 = tk.Frame(f_grid, bg=BG_AZUL_CLARO); c2.grid(row=0, column=1, sticky="nw", padx=10)
        self._crear_grid_checks(c2, "Desparasitación Reciente", ["Si", "No", "Expulsión Parásitos", "Sin Examen", "Con Examen"], "desparasitacion").pack(anchor="w", pady=5)
        self._crear_grid_checks(c2, "Cambios de Actitud", ["Depresión", "Inquietud", "Agresividad Espontanea", "Agresivo Defensivo", "Extremadamente Afectuoso"], "actitud").pack(anchor="w", pady=5)
        self._crear_grid_checks(c2, "Presencia Parásitos Externos", ["Pulgas", "Garrapatas", "Piojos", "Liendres", "Moscas/Moscos", "Miasis"], "parasitos_ext", col_count=2).pack(anchor="w", pady=5)
        
        # Columna 3
        c3 = tk.Frame(f_grid, bg=BG_AZUL_CLARO); c3.grid(row=0, column=2, sticky="nw", padx=10)
        self._crear_grid_checks(c3, "Ingesta de Agua", ["Aumentada", "Normal", "Disminuida", "Purificada", "De Llave"], "agua").pack(anchor="w", pady=5)
        self._crear_grid_checks(c3, "Apetito", ["Normal", "Reducido", "Aumentado", "Coprofagia", "Reducido Selectivo", "Alotriofagia (Pica)", "Apetito Voraz"], "apetito", col_count=2).pack(anchor="w", pady=5)
        self._crear_grid_checks(c3, "Cambios Tono de Voz", ["Afonia", "Ronquera", "No Ladra"], "voz").pack(anchor="w", pady=5)
        self._crear_grid_checks(c3, "Ha presentado Vomito", ["Con Alimento", "Sin Alimento", "Con Ingesta", "Sin Ingesta"], "vomito").pack(anchor="w", pady=5)

    # ==========================================
    # HOJA 3: ALTERACIONES (Foto 3)
    # ==========================================
    def construir_hoja_3(self, parent):
        sf = self._crear_scroll(parent)
        
        f_top = tk.Frame(sf, bg=BG_AZUL_CLARO)
        f_top.pack(fill="x", padx=10, pady=10)
        
        self._crear_grid_checks(f_top, "Alteraciones Neurológicas", ["Convulsiones", "Mioclonias", "Paralisis", "Incoordinación", "Nistagmo", "Babeo", "Ceguera", "Torticolis"], "alt_neuro", 2).pack(side="left", padx=10)
        self._crear_grid_checks(f_top, "Alteraciones Respiratorias", ["Flujo Nasal", "Respiración Dificil", "Tos", "Estornudos", "Estornudos Inversos"], "alt_resp").pack(side="left", padx=10)
        self._crear_grid_checks(f_top, "Plurito", ["Constante", "Alternado", "Relacionado con Comidas"], "plurito").pack(side="left", padx=10)

        f_mid = tk.Frame(sf, bg=BG_AZUL_CLARO)
        f_mid.pack(fill="x", padx=10, pady=10)
        
        self._crear_grid_checks(f_mid, "Alteraciones Locomotoras", ["Convulsiones", "Mioclonias", "Paralisis", "Incoordinación", "Claudicación", "Ceguera"], "alt_loco", 2).pack(side="left", padx=10)
        
        f_fisio = tk.Frame(f_mid, bg=BG_AZUL_CLARO)
        f_fisio.pack(side="right", fill="both", expand=True, padx=20)
        tk.Label(f_fisio, text="Parámetros Fisiológicos", font=("Arial", 12, "bold"), bg=BG_AZUL_CLARO).pack()
        
        params = ["Temperatura", "Frecuencia Cardiaca", "Frecuencia Respiratoria", "Llenado Capilar", "Hidratación", "Movimientos Gastrointestinales"]
        for p in params:
            f_p = tk.Frame(f_fisio, bg=BG_AZUL_CLARO)
            f_p.pack(fill="x", pady=2)
            tk.Label(f_p, text=p, bg=BG_AZUL_CLARO, font=("Arial", 9, "bold"), width=25, anchor="w").pack(side="left")
            ent = tk.Entry(f_p, font=("Arial", 10), bg="#EAF2F8", bd=0)
            ent.pack(side="left", fill="x", expand=True)
            self.vars_entry[f"fisio_{p.replace(' ', '_').lower()}"] = ent

        self._titulo_seccion(sf, "Observaciones")
        self._crear_area_texto(sf, "observaciones_hoja3", 6)

    # ==========================================
    # HOJA 4: DIAGNÓSTICO (Foto 4)
    # ==========================================
    def construir_hoja_4(self, parent):
        sf = self._crear_scroll(parent)

        f_diags = tk.Frame(sf, bg=BG_AZUL_CLARO)
        f_diags.pack(fill="x", padx=10, pady=10)
        
        f_diff = tk.Frame(f_diags, bg=BG_AZUL_CLARO)
        f_diff.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(f_diff, text="Diagnósticos Diferenciales", font=("Arial", 11, "bold"), bg=BG_AZUL_CLARO, anchor="w").pack(fill="x")
        self._crear_area_texto(f_diff, "diag_diferencial", 6)
        
        f_def = tk.Frame(f_diags, bg=BG_AZUL_CLARO)
        f_def.pack(side="right", fill="both", expand=True, padx=5)
        tk.Label(f_def, text="Diagnóstico Definitivo", font=("Arial", 11, "bold"), bg=BG_AZUL_CLARO, anchor="w").pack(fill="x")
        self._crear_area_texto(f_def, "diag_definitivo", 6)

        self._titulo_seccion(sf, "Tratamiento")
        self._crear_tabla_dinamica(sf, ["Medicamento", "Dosis", "Horario"], 6, "tratamiento_final")

        self._titulo_seccion(sf, "Preescripción")
        self._crear_area_texto(sf, "prescripcion_final", 5)

        # Fila final de firmas
        f_firmas = tk.Frame(sf, bg=BG_AZUL_CLARO)
        f_firmas.pack(fill="x", padx=20, pady=20)
        
        def crear_firma(parent, texto):
            f = tk.Frame(parent, bg=BG_AZUL_CLARO)
            tk.Label(f, text=texto, font=("Arial", 10, "bold"), bg=BG_AZUL_CLARO).pack()
            tk.Frame(f, bg=FG_NEGRO, height=2, width=200).pack(pady=(30, 0)) # Línea de firma
            return f
            
        crear_firma(f_firmas, "Total ($)").pack(side="left", expand=True)
        crear_firma(f_firmas, "Firma MVZ Encargado").pack(side="left", expand=True)
        crear_firma(f_firmas, "Firma Dueño o Encargado").pack(side="left", expand=True)

    # ==========================================
    # LÓGICA DE GUARDADO EN BASE DE DATOS
    # ==========================================
    def guardar_consulta(self):
        # 1. Recuperar los datos críticos para las columnas principales
        motivo = self.vars_text.get("motivo_consulta").get("1.0", "end-1c").strip()
        anamnesis = self.vars_text.get("historia_reciente").get("1.0", "end-1c").strip()
        diag = self.vars_text.get("diag_definitivo").get("1.0", "end-1c").strip()
        
        if not motivo or not diag:
            messagebox.showwarning("Faltan Datos", "Por favor llene el 'Motivo de Consulta' (Pág 1) y el 'Diagnóstico Definitivo' (Pág 4).")
            return

        def safe_float(key):
            try: return float(self.vars_entry.get(key).get() or 0)
            except: return 0.0

        temp = safe_float("fisio_temperatura")
        fc = safe_float("fisio_frecuencia_cardiaca")
        fr = safe_float("fisio_frecuencia_respiratoria")

        # 2. Empacar CIENTOS de variables en un solo archivo JSON limpio
        datos_completos = {}
        
        # Checkboxes (Guardar solo los que están marcados con 1)
        for key, var in self.vars_check.items():
            if var.get() == 1:
                datos_completos[key] = "Marcado"
                
        # Textos cortos (Tablas y parámetros)
        for key, ent in self.vars_entry.items():
            val = ent.get().strip()
            if val: datos_completos[key] = val
            
        # Áreas de texto grandes
        for key, txt in self.vars_text.items():
            if key not in ["motivo_consulta", "historia_reciente", "diag_definitivo"]: # Excluir los que ya van a columna propia
                val = txt.get("1.0", "end-1c").strip()
                if val: datos_completos[key] = val

        json_extra = json.dumps(datos_completos, ensure_ascii=False)
        fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 3. Guardar en SQLite
        conn = db.conectar(); cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO historial_clinico 
                (paciente_id, fecha, motivo, anamnesis, peso, temperatura, fc, fr, diagnostico_definitivo, tratamiento, vendedor_atiende, datos_extra)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (self.paciente_id, fecha_hoy, motivo, anamnesis, 0.0, temp, fc, fr, diag, "Ver JSON", self.medico_atiende, json_extra))
            
            conn.commit()
            messagebox.showinfo("Consulta Exitosa", "Ficha Clínica Beethoven guardada a la perfección.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar:\n{e}")
        finally:
            conn.close()