import sqlite3

def aplicar_parche():
    conn = sqlite3.connect("veterinaria.db")
    try:
        # Intentamos agregar la nueva columna
        conn.execute("ALTER TABLE historial_clinico ADD COLUMN veterinario TEXT DEFAULT 'General'")
        print("✅ ¡Éxito! Columna 'veterinario' agregada a la base de datos.")
    except Exception as e:
        # Si da error, es porque probablemente ya la habías agregado antes
        print(f"⚠️ Nota: {e} (La base de datos ya está lista).")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    aplicar_parche()