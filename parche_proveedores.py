from database import db

def crear_tablas_proveedores():
    conn = db.conectar()
    try:
        # 1. Tabla de Proveedores
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                contacto TEXT,
                telefono TEXT
            )
        """)
        
        # 2. Tabla de Precios de Proveedores (Historial de PDFs)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS precios_proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER,
                producto_descripcion TEXT NOT NULL,
                precio_compra REAL NOT NULL,
                fecha_actualizacion TEXT,
                FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
            )
        """)
        print("✅ Tablas de proveedores creadas e integradas con éxito.")
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    crear_tablas_proveedores()