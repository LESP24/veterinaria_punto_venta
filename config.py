# config.py - Archivo de configuración global

# Seguridad
SECRET_KEY = "VeterinariaBeethoven2025"

# Listas de Datos (Los vendedores que aparecen en la caja)
LISTA_VENDEDORES = [
    "Ingris", "Paulina", "Alejandra", "Lupita", 
    "Juan", "Pablo", "Baraquiel", "Ada", "Susy"
]

# --- PALETA DE COLORES (Clean Material) ---
# Usamos variables para que si un día quieres cambiar un color, 
# solo lo cambies aquí y se actualice en todas las ventanas.

COLOR_FONDO = "#F4F6F7"       # Gris muy claro para el fondo general
COLOR_HEADER = "#2C3E50"      # Azul oscuro para encabezados
COLOR_TEXTO_HEADER = "white"  # Letra blanca para encabezados
COLOR_SELECCION = "#455A64"   # Gris azulado al seleccionar un producto

# Colores de Semáforo (Alertas del inventario)
COLOR_AGOTADO = "#FFCDD2"     # Rojo pastel (Urgente, 0 stock)
COLOR_CADUCAR = "#FFE0B2"     # Naranja pastel (Atención, pronto a vencer)
COLOR_BAJO = "#FFF9C4"        # Amarillo pastel (Advertencia, poco stock)
COLOR_NORMAL = "white"        # Fila normal