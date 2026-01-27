"""
Script para asignar ficha_id a grupos basándose en la columna 'Ficha' del Excel
Ejecutar: python scripts/asignar_fichas_a_grupos.py
"""
import pandas as pd
import logging
from pathlib import Path
import sys

# Agregar el directorio raíz al path para importar módulos
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.database.connection import get_db_connection
from src.config import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rutas
EXCEL_PATH = BASE_DIR / "data" / "propuestas_artisticas.xlsx"


def asignar_fichas():
    """Asigna ficha_id a los grupos basándose en el Excel"""
    
    logger.info("="*60)
    logger.info("🔗 ASIGNANDO FICHAS A GRUPOS")
    logger.info("="*60)
    
    # 1. Leer Excel
    logger.info(f"\n📂 Leyendo Excel: {EXCEL_PATH}")
    try:
        df_excel = pd.read_excel(EXCEL_PATH)
        logger.info(f"✅ {len(df_excel)} grupos leídos del Excel")
        
        # Verificar que existe la columna Ficha
        if 'Ficha' not in df_excel.columns:
            logger.error("❌ La columna 'Ficha' no existe en el Excel")
            logger.info("📋 Columnas disponibles: " + ", ".join(df_excel.columns))
            return False
            
    except Exception as e:
        logger.error(f"❌ Error leyendo Excel: {e}")
        return False
    
    # 2. Obtener mapeo de fichas y procesar asignaciones usando context manager
    logger.info(f"\n🔌 Conectando a BD: {config.db_path}")
    
    actualizados = 0
    sin_ficha = 0
    ficha_no_encontrada = 0
    errores = 0
    fichas_no_encontradas_set = set()
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 3. Obtener mapeo de fichas (codigo -> id)
            logger.info("\n🎭 Obteniendo fichas de la BD...")
            cursor.execute("SELECT id, codigo, nombre FROM fichas")
            fichas = cursor.fetchall()
            
            if not fichas:
                logger.error("❌ No hay fichas en la base de datos")
                logger.info("💡 Ejecuta primero: python scripts/migrar_a_fichas.py")
                return False
            
            fichas_map = {codigo.upper(): (id_, nombre) for id_, codigo, nombre in fichas}
            
            logger.info(f"✅ {len(fichas_map)} fichas disponibles:")
            for codigo, (id_, nombre) in fichas_map.items():
                logger.info(f"   • {codigo} (ID: {id_}): {nombre}")
            
            # 4. Procesar y asignar fichas
            logger.info("\n🔄 Asignando fichas a grupos...")
            
            for idx, row in df_excel.iterrows():
                try:
                    codigo_grupo = str(row['Codigo']).strip().upper()
                    ficha_excel = str(row.get('Ficha', '')).strip().upper()
                    
                    if not ficha_excel or ficha_excel == 'NAN' or pd.isna(row.get('Ficha')):
                        sin_ficha += 1
                        continue
                    
                    # Buscar ficha_id
                    if ficha_excel in fichas_map:
                        ficha_id, ficha_nombre = fichas_map[ficha_excel]
                        
                        # Actualizar grupo
                        cursor.execute("""
                            UPDATE grupos 
                            SET ficha_id = ?
                            WHERE codigo = ?
                        """, (ficha_id, codigo_grupo))
                        
                        if cursor.rowcount > 0:
                            actualizados += 1
                        else:
                            logger.warning(f"⚠️ Grupo no encontrado en BD: {codigo_grupo}")
                            errores += 1
                    else:
                        fichas_no_encontradas_set.add(ficha_excel)
                        ficha_no_encontrada += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando fila {idx + 1}: {e}")
                    errores += 1
            
            # El commit se hace automáticamente al salir del context manager
            logger.info("\n✅ Cambios guardados en la base de datos")
            
    except Exception as e:
        logger.error(f"❌ Error en operación de BD: {e}")
        return False
    
    # 5. Resumen
    logger.info("\n" + "="*60)
    logger.info("📊 RESUMEN DE ASIGNACIÓN")
    logger.info("="*60)
    logger.info(f"✅ Grupos actualizados: {actualizados}")
    logger.info(f"⚠️ Grupos sin ficha en Excel: {sin_ficha}")
    logger.info(f"❌ Fichas no encontradas en BD: {ficha_no_encontrada}")
    logger.info(f"❌ Errores: {errores}")
    
    if fichas_no_encontradas_set:
        logger.info("\n⚠️ Fichas en Excel que NO existen en BD:")
        for ficha in fichas_no_encontradas_set:
            logger.info(f"   • {ficha}")
        logger.info("\n💡 Solución: Verifica los códigos o crea las fichas faltantes")
    
    if sin_ficha > 0:
        logger.info(f"\n⚠️ Hay {sin_ficha} grupos sin ficha asignada en el Excel")
        logger.info("💡 Estos grupos NO podrán ser evaluados hasta que tengan ficha")
    
    # 6. Verificar asignación (usando context manager)
    logger.info("\n🔍 Verificando asignación en la BD...")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM grupos WHERE ficha_id IS NOT NULL")
            con_ficha = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM grupos WHERE ficha_id IS NULL")
            sin_ficha_bd = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM grupos")
            total = cursor.fetchone()[0]
            
            logger.info(f"\n📊 Estado actual en BD:")
            logger.info(f"   • Total grupos: {total}")
            if total > 0:
                logger.info(f"   • Con ficha asignada: {con_ficha} ({con_ficha/total*100:.1f}%)")
                logger.info(f"   • Sin ficha: {sin_ficha_bd} ({sin_ficha_bd/total*100:.1f}%)")
            
            # Mostrar algunos ejemplos
            logger.info(f"\n📋 Ejemplos de grupos con ficha asignada:")
            cursor.execute("""
                SELECT g.codigo, g.nombre_propuesta, f.nombre
                FROM grupos g
                JOIN fichas f ON g.ficha_id = f.id
                LIMIT 5
            """)
            
            ejemplos = cursor.fetchall()
            if ejemplos:
                for codigo, nombre, ficha in ejemplos:
                    logger.info(f"   • {codigo}: {nombre[:30]}... → {ficha}")
            else:
                logger.info("   (Ningún grupo con ficha asignada aún)")
        
    except Exception as e:
        logger.error(f"❌ Error verificando: {e}")
    
    logger.info("\n" + "="*60)
    if actualizados > 0:
        logger.info("✅ ASIGNACIÓN COMPLETADA EXITOSAMENTE")
    else:
        logger.info("⚠️ NO SE ASIGNARON FICHAS")
    logger.info("="*60)
    
    if actualizados > 0:
        logger.info("\n📋 PRÓXIMOS PASOS:")
        logger.info("1. Verificar: python -m src.database.init_db")
        logger.info("2. Iniciar aplicación: python main.py")
        logger.info("3. Los curadores ya pueden evaluar grupos")
        
        if sin_ficha_bd > 0:
            logger.info(f"\n⚠️ Atención: {sin_ficha_bd} grupos aún sin ficha")
            logger.info("   Estos grupos NO podrán evaluarse")
    
    return actualizados > 0


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("🔗 ASIGNAR FICHAS A GRUPOS")
    print("="*60)
    print("\nEste script:")
    print("- Lee la columna 'Ficha' del Excel")
    print("- Busca el ID correspondiente en la tabla 'fichas'")
    print("- Actualiza la columna 'ficha_id' en la tabla 'grupos'")
    print("\n⚠️  Asegúrate de que:")
    print("   1. El Excel tiene la columna 'Ficha' con códigos válidos")
    print("   2. Las fichas existen en la BD (CONGO, CUMBIA, etc.)")
    
    respuesta = input("\n¿Continuar? (s/n): ")
    
    if respuesta.lower() != 's':
        print("❌ Operación cancelada")
        sys.exit(0)
    
    exito = asignar_fichas()
    
    if exito:
        print("\n✅ Fichas asignadas exitosamente!")
        sys.exit(0)
    else:
        print("\n❌ La asignación falló o no se asignó ninguna ficha")
        sys.exit(1)