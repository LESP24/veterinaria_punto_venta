from database import db

def aplicar_parche_cuentas():
    conn = db.conectar()
    try:
        # Creamos la tabla para el control de deudas y notas
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notas_proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER,
                fecha TEXT,
                concepto TEXT NOT NULL,
                monto REAL DEFAULT 0,
                estado TEXT DEFAULT 'PENDIENTE',
                FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
            )
        """)
        print("✅ ¡Éxito! Tabla 'notas_proveedores' creada e integrada con éxito.")
    except Exception as e:
        print(f"⚠️ Nota o Error: {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    aplicar_parche_cuentas()