from database import db

def arreglar_tablas():
    conn = db.conectar()
    try:
        # 1. Borramos cualquier rastro de tablas viejas que estén causando conflicto
        conn.execute("DROP TABLE IF EXISTS precios_proveedores")
        conn.execute("DROP TABLE IF EXISTS notas_proveedores")
        conn.execute("DROP TABLE IF EXISTS proveedores")
        
        # 2. Creamos la tabla Proveedores desde cero (CON la columna 'nombre')
        conn.execute("""
            CREATE TABLE proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                contacto TEXT,
                telefono TEXT
            )
        """)
        
        # 3. Creamos la tabla de Precios (PDFs)
        conn.execute("""
            CREATE TABLE precios_proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER,
                producto_descripcion TEXT NOT NULL,
                precio_compra REAL NOT NULL,
                fecha_actualizacion TEXT,
                FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
            )
        """)
        
        # 4. Creamos la tabla de Cuentas y Notas
        conn.execute("""
            CREATE TABLE notas_proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER,
                fecha TEXT,
                concepto TEXT NOT NULL,
                monto REAL DEFAULT 0,
                estado TEXT DEFAULT 'PENDIENTE',
                FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
            )
        """)
        print("✅ ¡ÉXITO! Las tablas de proveedores se han reiniciado y configurado correctamente.")
    except Exception as e:
        print(f"❌ Error al resetear las tablas: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    arreglar_tablas()