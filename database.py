import sqlite3

class DatabaseManager:
    
    # 1. El constructor (nota el espacio y los dos puntos al final)
    def __init__(self, db_name="veterinaria.db"):
        self.db_name = db_name
        
    # 2. Método para abrir la conexión 
    def conectar(self):
        return sqlite3.connect(self.db_name)
    
    # 3. Método para actualizar tablas y crearlas
    def inicializa_db(self):
        # Abrimos la conexión
        conn = self.conectar()
        cursor = conn.cursor()
        
        # --- CREACIÓN DE TABLAS ---
        # (Nota: usamos 'cursor.execute' sin el 'self.')
        cursor.execute('''CREATE TABLE IF NOT EXISTS productos (codigo TEXT PRIMARY KEY, nombre TEXT, categoria TEXT, laboratorio TEXT, costo_referencia REAL, precio_publico REAL, precio_mayoreo REAL, stock_minimo INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS lotes (id INTEGER PRIMARY KEY, codigo_producto TEXT, cantidad INTEGER, fecha_caducidad TEXT, FOREIGN KEY (codigo_producto) REFERENCES productos (codigo))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY, fecha TEXT, folio TEXT, total REAL, tipo_precio TEXT, metodo_pago TEXT, vendedor TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS detalle_venta (id INTEGER PRIMARY KEY, venta_id INTEGER, codigo_producto TEXT, cantidad INTEGER, precio_unitario REAL, subtotal REAL, FOREIGN KEY (venta_id) REFERENCES ventas (id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS pacientes (id INTEGER PRIMARY KEY, nombre TEXT, especie TEXT, raza TEXT, dueno TEXT, telefono TEXT, fecha_registro TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS historial_clinico (id INTEGER PRIMARY KEY, paciente_id INTEGER, fecha TEXT, motivo TEXT, diagnostico TEXT, peso REAL, FOREIGN KEY (paciente_id) REFERENCES pacientes (id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS movimientos_caja (id INTEGER PRIMARY KEY, fecha TEXT, tipo TEXT, motivo TEXT, monto REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS proveedores (id INTEGER PRIMARY KEY, empresa TEXT, telefono TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS costos_proveedores (id INTEGER PRIMARY KEY, codigo_producto TEXT, proveedor_id INTEGER, costo_ofrecido REAL, FOREIGN KEY (proveedor_id) REFERENCES proveedores (id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS citas (id INTEGER PRIMARY KEY, fecha TEXT, hora TEXT, paciente TEXT, motivo TEXT, telefono TEXT)''')
        
        # --- MIGRACIONES (Actualizaciones) ---
        try: 
            cursor.execute("ALTER TABLE productos ADD COLUMN laboratorio TEXT")
        except: 
            pass 
            
        try: 
            cursor.execute("ALTER TABLE ventas ADD COLUMN metodo_pago TEXT")
        except: 
            pass
            
        try: 
            cursor.execute("ALTER TABLE ventas ADD COLUMN vendedor TEXT")
        except: 
            pass
        
        # Guardamos cambios y cerramos (usamos 'conn' sin el 'self.')
        conn.commit()
        conn.close()

# Db Listo para ser importado 
db = DatabaseManager()