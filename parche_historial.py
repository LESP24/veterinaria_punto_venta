from database import db

def aplicar_parche_historial():
    conn = db.conectar()
    try:
        # Tabla para guardar cada consulta médica
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historial_clinico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER,
                fecha TEXT,
                motivo TEXT,
                anamnesis TEXT,
                peso REAL,
                temperatura REAL,
                fc REAL, -- Frecuencia Cardiaca
                fr REAL, -- Frecuencia Respiratoria
                diagnostico_definitivo TEXT,
                tratamiento TEXT,
                vendedor_atiende TEXT,
                datos_extra TEXT, -- Aquí guardaremos todos los checkboxes en formato JSON
                FOREIGN KEY(paciente_id) REFERENCES pacientes(id)
            )
        """)
        print("✅ Tabla de Historial Clínico Beethoven instalada.")
    except Exception as e:
        print(f"❌ Error: {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    aplicar_parche_historial()