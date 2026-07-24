import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# --- CONFIGURACIÓN DE CORS (El pase VIP para React) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite que React (o cualquier otro) se conecte
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, PUT, DELETE
    allow_headers=["*"],
)

DB_PATH = "veterinaria.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    return conn

@app.get("/")
def leer_raiz():
    return {"mensaje": "¡El servidor del Punto de Venta Veterinario está vivo!"}

@app.get("/estado-licencia")
def verificar_licencia():
    return {"estado": "activa", "cliente": "Veterinaria Demo"}

@app.get("/api/productos")
def obtener_productos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos") 
    productos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return productos

@app.get("/api/debug/tablas")
def listar_tablas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tablas