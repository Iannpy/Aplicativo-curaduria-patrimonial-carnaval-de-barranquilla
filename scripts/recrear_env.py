"""
Script para recrear el archivo .env con hashes correctos usando bcrypt
Ejecutar: python recrear_env.py
"""
import bcrypt
from pathlib import Path

print("="*60)
print("RECREANDO ARCHIVO .env CON BCRYPT")
print("="*60)

# Generar hashes usando bcrypt directamente
print("\n🔐 Generando hashes con bcrypt...")

password_curador = "1234".encode('utf-8')
password_comite = "admin123".encode('utf-8')

hash_curador = bcrypt.hashpw(password_curador, bcrypt.gensalt()).decode('utf-8')
hash_comite = bcrypt.hashpw(password_comite, bcrypt.gensalt()).decode('utf-8')

print("   ✅ Hash curador generado")
print("   ✅ Hash comité generado")

# Contenido del .env
env_content = f"""# Configuración de Base de Datos
DB_PATH=data/curaduria.db

# Configuración de Archivos
EXCEL_PATH=data/propuestas_artisticas.xlsx
LOGO_PATH=assets/CDB_EMPRESA_ASSETS.svg

# Configuración del Evento
NOMBRE_EVENTO=Fin de Semana de la Tradición
ANO_EVENTO=2025

# Credenciales de Usuarios (generadas con bcrypt)
CURADOR1_HASH={hash_curador}
CURADOR2_HASH={hash_curador}
CURADOR3_HASH={hash_curador}
CURADOR4_HASH={hash_curador}
CURADOR5_HASH={hash_curador}
COMITE_HASH={hash_comite}

# Configuración de Umbrales
UMBRAL_RIESGO=1.0
UMBRAL_MEJORA=1.6

# Configuración de Validaciones
MIN_CARACTERES_OBSERVACION=20
MAX_GRUPOS_POR_CURADOR=50
"""

# Definir ruta raíz (un nivel arriba de scripts/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Guardar archivo en la raíz
env_path = BASE_DIR / ".env"

# Hacer backup si existe
if env_path.exists():
    backup_path = BASE_DIR / ".env.backup"
    print(f"\n📦 Backup del .env anterior: {backup_path}")
    with open(env_path, "r", encoding="utf-8") as f:
        old_content = f.read()
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(old_content)

# Escribir nuevo .env
with open(env_path, "w", encoding="utf-8") as f:
    f.write(env_content)

print(f"\n✅ Archivo .env recreado exitosamente con bcrypt nativo")
print("\n📋 Credenciales:")
print("   Curadores (curador1-5): 1234")
print("   Comité: admin123")

# Verificar que funciona
print("\n🧪 Verificando hashes...")
try:
    test_password = "1234".encode('utf-8')
    test_hash = hash_curador.encode('utf-8')
    
    if bcrypt.checkpw(test_password, test_hash):
        print("   ✅ Verificación exitosa - Los hashes funcionan correctamente")
    else:
        print("   ❌ Error en verificación")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n👉 Próximos pasos:")
print("   1. Ejecuta: streamlit run main.py")
print("   2. Ingresa como curador1 con contraseña 1234")
print()