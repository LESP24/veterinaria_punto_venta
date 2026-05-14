import hashlib

SECRET_KEY = "VeterinariaBeethoven2025"

def generar_licencia(uuid_str):
    # Combinar UUID + SECRET_KEY
    combined = uuid_str + SECRET_KEY
    # Generar hash SHA256
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    # Truncar a 16 caracteres
    truncated = hash_hex[:16]
    # Formatear como XXXX-XXXX-XXXX-XXXX
    formatted = '-'.join([truncated[i:i+4] for i in range(0, 16, 4)])
    return formatted

if __name__ == "__main__":
    uuid_input = input("Ingrese el Hardware ID (UUID) del cliente: ")
    codigo_activacion = generar_licencia(uuid_input)
    print(f"Código de Activación: {codigo_activacion}")