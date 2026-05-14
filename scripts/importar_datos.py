import sqlite3
import csv
import os

# --- CONFIGURACIÓN ---
ARCHIVO_ORIGEN = "inventario.txt"
DB_DESTINO = "veterinaria.db"

def limpiar_precio(texto):
    """Convierte '$1,200.00' a 1200.0"""
    if not texto: return 0.0
    limpio = str(texto).replace("$", "").replace(",", "").replace('"', "").strip()
    try:
        return float(limpio)
    except ValueError:
        return 0.0

def reparar_codigo(texto):
    """Arregla códigos científicos (7.50E+12 -> 75000...)"""
    texto = str(texto).strip()
    if "E+" in texto or "e+" in texto:
        try:
            return str(int(float(texto)))
        except:
            return texto
    return texto

def importar_correctamente():
    if not os.path.exists(ARCHIVO_ORIGEN):
        print(f"❌ ERROR: No encuentro el archivo {ARCHIVO_ORIGEN}")
        return

    if not os.path.exists(DB_DESTINO):
        print(f"❌ ERROR: No encuentro la base de datos nueva. Ejecuta main.py primero.")
        return

    print("--- INICIANDO IMPORTACIÓN LIMPIA ---")
    
    conn = sqlite3.connect(DB_DESTINO)
    cursor = conn.cursor()
    
    # Limpiamos para evitar duplicados en esta carga inicial
    cursor.execute("DELETE FROM lotes")
    cursor.execute("DELETE FROM productos")
    print("🧹 Base de datos lista para recibir datos...")

    count = 0
    try:
        with open(ARCHIVO_ORIGEN, "r", encoding="latin-1") as f:
            lector = csv.reader(f, delimiter="\t") # Asumimos tabulaciones
            next(lector, None) # Saltar encabezado

            for fila in lector:
                if len(fila) < 8: continue

                # === MAPEO CORRECTO (AQUI OCURRE LA MAGIA) ===
                # El script toma tus columnas desordenadas del TXT 
                # y las ordena para la BASE DE DATOS v22.0
                
                try:
                    # DATOS DEL ARCHIVO TXT
                    txt_codigo = reparar_codigo(fila[0])
                    txt_nombre = fila[1].strip()
                    txt_costo  = limpiar_precio(fila[2])  # Col 2 es Costo
                    txt_publico = limpiar_precio(fila[3]) # Col 3 es Público
                    txt_colega  = limpiar_precio(fila[4]) # Col 4 es Colega
                    
                    try: txt_stock = int(float(fila[5]))
                    except: txt_stock = 0
                    
                    try: txt_minimo = int(float(fila[6]))
                    except: txt_minimo = 1
                    
                    txt_laboratorio = fila[7].strip() # Col 7 es Laboratorio

                    # INSERTAR EN LA BASE DE DATOS (ORDEN v22.0)
                    # (codigo, nombre, categoria, laboratorio, costo, publico, mayoreo, min)
                    cursor.execute("""
                        INSERT OR REPLACE INTO productos 
                        (codigo, nombre, categoria, laboratorio, costo_referencia, precio_publico, precio_mayoreo, stock_minimo)
                        VALUES (?, ?, 'General', ?, ?, ?, ?, ?)
                    """, (txt_codigo, txt_nombre, txt_laboratorio, txt_costo, txt_publico, txt_colega, txt_minimo))

                    # CREAR STOCK
                    if txt_stock > 0:
                        cursor.execute("""
                            INSERT INTO lotes (codigo_producto, cantidad, fecha_caducidad)
                            VALUES (?, ?, ?)
                        """, (txt_codigo, txt_stock, "2030-01-01"))
                    
                    count += 1
                except Exception as e:
                    print(f"⚠️ Error en fila: {e}")

        conn.commit()
        print(f"✅ ¡ÉXITO! Se importaron {count} productos.")
        print("   Ahora abre tu sistema y verás todo ordenado.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    importar_correctamente()
    input("Presiona ENTER para salir...")