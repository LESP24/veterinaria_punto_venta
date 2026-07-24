from database import db

def aplicar_parche_personal():
    conn = db.conectar()
    try:
        # Tabla para registrar las semanas trabajadas y estatus de pago
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nomina_empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empleado TEXT NOT NULL,
                periodo TEXT NOT NULL, -- Ej: Semana del 18 al 24 de Mayo
                sueldo REAL DEFAULT 0,
                estado_pago TEXT DEFAULT 'PENDIENTE',
                fecha_pago TEXT
            )
        """)
        print("✅ Parche de Personal aplicado: Tabla de asistencia y nómina lista.")
    except Exception as e:
        print(f"❌ Error al aplicar el parche: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    aplicar_parche_personal()