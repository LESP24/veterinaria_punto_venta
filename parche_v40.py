from database import db

def aplicar_parche():
    conn = db.conectar()
    try:
        # Tabla para las cuentas de clientes (Fiados)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notas_clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                fecha TEXT,
                concepto TEXT NOT NULL,
                monto REAL DEFAULT 0,
                estado TEXT DEFAULT 'PENDIENTE'
            )
        """)
        
        # Configuración del PIN de seguridad (Buscamos por 'clave' en vez de 'id')
        cursor = conn.cursor()
        cursor.execute("SELECT clave FROM configuracion WHERE clave='pin_admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO configuracion (clave, valor) VALUES ('pin_admin', '1234')")
            
        print("✅ Parche v40.0 aplicado: Tabla de créditos y PIN de seguridad instalados.")
    except Exception as e:
        print(f"❌ Error: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    aplicar_parche()