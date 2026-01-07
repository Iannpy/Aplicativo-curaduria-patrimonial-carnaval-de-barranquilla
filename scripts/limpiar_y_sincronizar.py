"""
Script para eliminar duplicados y sincronizar BD con Excel
Ejecutar: python limpiar_y_sincronizar.py
"""
import pandas as pd
import sqlite3
from datetime import datetime
import sys
import os

# Agregar directorio raíz al path para importar src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config
from src.utils.validators import validar_codigo_grupo

print("="*60)
print("LIMPIEZA Y SINCRONIZACIÓN DE BASE DE DATOS")
print("="*60)

# 1. Cargar datos actuales
print("\n1️⃣ Cargando datos...")

try:
    df_excel = pd.read_excel(config.excel_path)
    print(f"   ✅ Excel cargado: {len(df_excel)} grupos")
except Exception as e:
    print(f"   ❌ Error cargando Excel: {e}")
    exit(1)

conn = sqlite3.connect(config.db_path)
cursor = conn.cursor()

# Grupos en BD
cursor.execute("SELECT codigo, nombre_propuesta FROM grupos")
grupos_bd = cursor.fetchall()
print(f"   ✅ BD cargada: {len(grupos_bd)} grupos")

# Evaluaciones existentes
cursor.execute("SELECT COUNT(*) FROM evaluaciones")
total_eval = cursor.fetchone()[0]
print(f"   📝 Evaluaciones registradas: {total_eval}")

# 2. Análisis de duplicados
print("\n2️⃣ Analizando duplicados...")

cursor.execute("""
    SELECT codigo, COUNT(*) as cantidad
    FROM grupos
    GROUP BY codigo
    HAVING COUNT(*) > 1
""")
duplicados = cursor.fetchall()

if duplicados:
    print(f"   ⚠️  Duplicados encontrados: {len(duplicados)}")
    for codigo, cantidad in duplicados[:5]:
        print(f"      - {codigo}: aparece {cantidad} veces")
else:
    print(f"   ✅ No hay códigos duplicados")

# 3. Comparar con Excel
print("\n3️⃣ Comparando con Excel...")

codigos_excel = set(str(c).strip().upper() for c in df_excel['Codigo'])
codigos_bd = {row[0] for row in grupos_bd}

solo_bd = codigos_bd - codigos_excel
solo_excel = codigos_excel - codigos_bd

print(f"   📊 En Excel: {len(codigos_excel)}")
print(f"   📊 En BD: {len(codigos_bd)}")
print(f"   ⚠️  Solo en BD (serán eliminados): {len(solo_bd)}")
print(f"   ➕ Solo en Excel (serán agregados): {len(solo_excel)}")

if solo_bd:
    print(f"\n   📋 Grupos que serán ELIMINADOS (primeros 10):")
    for i, codigo in enumerate(list(solo_bd)[:10], 1):
        print(f"      {i}. {codigo}")

# 4. Confirmar acción
print("\n" + "="*60)
print("⚠️  IMPORTANTE:")
print("="*60)
print("Esta operación hará lo siguiente:")
print(f"   1. Eliminará TODOS los grupos actuales ({len(grupos_bd)})")
print(f"   2. Recargará SOLO los del Excel ({len(codigos_excel)})")
print(f"   3. Las evaluaciones de grupos eliminados también se borrarán")
print("="*60)

if total_eval > 0:
    print(f"\n⚠️  ADVERTENCIA: Hay {total_eval} evaluaciones registradas")
    print("   Las evaluaciones de grupos que no estén en el Excel se perderán")

respuesta = input("\n¿Desea continuar? Escriba 'SI' para confirmar: ").strip().upper()

if respuesta != "SI":
    print("\n❌ Operación cancelada")
    conn.close()
    exit(0)

# 5. Crear backup antes de proceder
print("\n4️⃣ Creando backup de seguridad...")

backup_path = f"backups/backup_antes_limpieza_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

import shutil
from pathlib import Path
backup_dir = config.BASE_DIR / "backups"
backup_dir.mkdir(exist_ok=True)

try:
    shutil.copy2(config.db_path, str(backup_dir / Path(backup_path).name))
    print(f"   ✅ Backup creado: {backup_path}")
except Exception as e:
    print(f"   ❌ Error creando backup: {e}")
    print("   Operación cancelada por seguridad")
    conn.close()
    exit(1)

# 6. Limpiar base de datos
print("\n5️⃣ Limpiando base de datos...")

try:
    # Eliminar evaluaciones de grupos que no están en Excel
    if solo_bd:
        placeholders = ','.join('?' * len(solo_bd))
        cursor.execute(f"""
            DELETE FROM evaluaciones 
            WHERE codigo_grupo IN ({placeholders})
        """, tuple(solo_bd))
        eval_eliminadas = cursor.rowcount
        print(f"   🗑️  Evaluaciones eliminadas: {eval_eliminadas}")
    
    # Eliminar todos los grupos
    cursor.execute("DELETE FROM grupos")
    print(f"   🗑️  Grupos eliminados: {len(grupos_bd)}")
    
    conn.commit()
    print(f"   ✅ Base de datos limpiada")

except Exception as e:
    conn.rollback()
    print(f"   ❌ Error en limpieza: {e}")
    print(f"   💡 Puedes restaurar desde: {backup_path}")
    conn.close()
    exit(1)

# 7. Recargar desde Excel
print("\n6️⃣ Recargando grupos desde Excel...")

insertados = 0
errores = 0

for _, row in df_excel.iterrows():
    valido, codigo_limpio, error = validar_codigo_grupo(str(row['Codigo']))
    
    if not valido:
        print(f"   ⚠️  Código inválido: {row['Codigo']} - {error}")
        errores += 1
        continue
    
    try:
        cursor.execute("""
            INSERT INTO grupos (codigo, nombre_propuesta, modalidad, tipo, tamano, naturaleza, ano_evento)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            codigo_limpio,
            row['Nombre_Propuesta'],
            row['Modalidad'],
            row['Tipo'],
            row.get('Tamaño', 'N/A'),
            row['Naturaleza'],
            config.ano_evento
        ))
        insertados += 1
    except Exception as e:
        print(f"   ⚠️  Error insertando {codigo_limpio}: {e}")
        errores += 1

conn.commit()

print(f"   ✅ Grupos insertados: {insertados}")
if errores > 0:
    print(f"   ⚠️  Errores: {errores}")

# 8. Verificación final
print("\n7️⃣ Verificación final...")

cursor.execute("SELECT COUNT(*) FROM grupos")
total_final = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM evaluaciones")
eval_final = cursor.fetchone()[0]

cursor.execute("""
    SELECT codigo, COUNT(*) as cantidad
    FROM grupos
    GROUP BY codigo
    HAVING COUNT(*) > 1
""")
duplicados_final = cursor.fetchall()

print(f"   📊 Total grupos en BD: {total_final}")
print(f"   📝 Total evaluaciones: {eval_final}")
print(f"   🔍 Duplicados: {len(duplicados_final)}")

if total_final == len(codigos_excel):
    print(f"   ✅ SINCRONIZACIÓN PERFECTA")
else:
    print(f"   ⚠️  Diferencia detectada:")
    print(f"      Excel: {len(codigos_excel)}")
    print(f"      BD: {total_final}")

conn.close()

print("\n" + "="*60)
print("✅ PROCESO COMPLETADO")
print("="*60)

print(f"\n📋 Resumen:")
print(f"   Grupos antes: {len(grupos_bd)}")
print(f"   Grupos ahora: {total_final}")
print(f"   Evaluaciones antes: {total_eval}")
print(f"   Evaluaciones ahora: {eval_final}")
print(f"   Backup guardado en: {backup_path}")

print("\n💡 Próximos pasos:")
print("   1. Reinicia Streamlit: streamlit run main.py")
print("   2. Presiona 'C' para limpiar caché")
print("   3. Verifica que todo esté correcto")
print(f"   4. Si hay problemas, restaura desde: {backup_path}")

print()
