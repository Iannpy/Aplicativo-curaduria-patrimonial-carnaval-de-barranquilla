"""
Diagnóstico de la base de datos
Ejecutar: python diagnostico_bd.py
"""
import sqlite3
import os
from pathlib import Path
from src.config import config

print("="*60)
print("DIAGNÓSTICO DE BASE DE DATOS")
print("="*60)

# 1. Verificar ruta
print(f"\n1️⃣ Verificando ruta de BD...")
print(f"   Ruta configurada: {config.db_path}")

db_path = Path(config.db_path)

if db_path.exists():
    print(f"   ✅ Archivo existe")
    
    # Tamaño
    size_kb = db_path.stat().st_size / 1024
    print(f"   📦 Tamaño: {size_kb:.2f} KB")
    
    # Última modificación
    import datetime
    mtime = datetime.datetime.fromtimestamp(db_path.stat().st_mtime)
    print(f"   🕐 Última modificación: {mtime}")
else:
    print(f"   ❌ Archivo NO existe")
    print(f"   💡 Ejecuta: python -m src.database.init_db")
    exit(1)

# 2. Conectar y verificar contenido
print(f"\n2️⃣ Verificando contenido...")

try:
    conn = sqlite3.connect(config.db_path)
    cursor = conn.cursor()
    
    # Tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = [row[0] for row in cursor.fetchall()]
    print(f"   ✅ Tablas encontradas: {', '.join(tablas)}")
    
    # Grupos
    cursor.execute("SELECT COUNT(*) FROM grupos")
    total_grupos = cursor.fetchone()[0]
    print(f"\n   📊 Total grupos: {total_grupos}")
    
    if total_grupos > 0:
        cursor.execute("SELECT codigo, nombre_propuesta FROM grupos LIMIT 5")
        print(f"   📋 Primeros 5 grupos:")
        for codigo, nombre in cursor.fetchall():
            print(f"      - {codigo}: {nombre}")
    
    # Evaluaciones
    cursor.execute("SELECT COUNT(*) FROM evaluaciones")
    total_eval = cursor.fetchone()[0]
    print(f"\n   📝 Total evaluaciones: {total_eval}")
    
    # Usuarios
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    total_usuarios = cursor.fetchone()[0]
    print(f"   👥 Total usuarios: {total_usuarios}")
    
    # Dimensiones
    cursor.execute("SELECT COUNT(*) FROM dimensiones")
    total_dim = cursor.fetchone()[0]
    print(f"   📐 Total dimensiones: {total_dim}")
    
    conn.close()
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# 3. Verificar Excel
print(f"\n3️⃣ Verificando archivo Excel...")
print(f"   Ruta configurada: {config.excel_path}")

excel_path = Path(config.excel_path)

if excel_path.exists():
    print(f"   ✅ Archivo existe")
    
    import pandas as pd
    try:
        df = pd.read_excel(config.excel_path)
        print(f"   📊 Grupos en Excel: {len(df)}")
        print(f"   📋 Columnas: {', '.join(df.columns)}")
        
        print(f"\n   📋 Primeros 5 códigos en Excel:")
        for i, codigo in enumerate(df['Codigo'].head(5), 1):
            print(f"      {i}. {codigo}")
            
    except Exception as e:
        print(f"   ❌ Error leyendo Excel: {e}")
else:
    print(f"   ❌ Archivo NO existe")

# 4. Comparar BD vs Excel
print(f"\n4️⃣ Comparación BD vs Excel...")

if excel_path.exists() and db_path.exists():
    try:
        import pandas as pd
        df_excel = pd.read_excel(config.excel_path)
        
        conn = sqlite3.connect(config.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT codigo FROM grupos")
        codigos_bd = {row[0] for row in cursor.fetchall()}
        conn.close()
        
        codigos_excel = {str(c).strip().upper() for c in df_excel['Codigo']}
        
        solo_excel = codigos_excel - codigos_bd
        solo_bd = codigos_bd - codigos_excel
        en_ambos = codigos_excel & codigos_bd
        
        print(f"   📊 En Excel: {len(codigos_excel)}")
        print(f"   📊 En BD: {len(codigos_bd)}")
        print(f"   ✅ En ambos: {len(en_ambos)}")
        print(f"   ⚠️  Solo en Excel (falta cargar): {len(solo_excel)}")
        print(f"   ⚠️  Solo en BD (ya no existe): {len(solo_bd)}")
        
        if solo_excel:
            print(f"\n   📋 Grupos que faltan cargar (primeros 5):")
            for i, codigo in enumerate(list(solo_excel)[:5], 1):
                print(f"      {i}. {codigo}")
        
        if solo_bd:
            print(f"\n   ⚠️  Grupos en BD que ya no están en Excel:")
            for i, codigo in enumerate(list(solo_bd)[:5], 1):
                print(f"      {i}. {codigo}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

# 5. Verificar archivos múltiples
print(f"\n5️⃣ Buscando archivos .db en el proyecto...")

base_dir = Path.cwd()
db_files = list(base_dir.rglob("*.db"))

if len(db_files) > 1:
    print(f"   ⚠️  ENCONTRADOS MÚLTIPLES ARCHIVOS .db:")
    for db_file in db_files:
        size = db_file.stat().st_size / 1024
        print(f"      - {db_file} ({size:.2f} KB)")
    print(f"\n   💡 Puede que estés actualizando el archivo equivocado")
else:
    print(f"   ✅ Solo un archivo .db encontrado")

print("\n" + "="*60)
print("FIN DEL DIAGNÓSTICO")
print("="*60)

print("\n💡 PRÓXIMOS PASOS:")
print("   1. Si 'falta cargar' > 0, ejecuta: python cargar_grupos_bd.py")
print("   2. Si hay múltiples .db, verifica cuál usa la app")
print("   3. Si todo está OK pero no ves cambios, limpia caché de Streamlit")
print()
