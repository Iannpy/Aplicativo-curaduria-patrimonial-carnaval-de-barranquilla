"""
Script para sincronizar dimensiones y aspectos desde el archivo de configuración
a la base de datos, manteniendo la integridad de las evaluaciones existentes.

Ejecutar: python -m src.database.sync_dimensiones
"""

import logging
from src.database.connection import get_db_connection
from src.utils.dimensiones_iniciales import (
    DIMENSIONES_INICIALES, 
    FICHAS_INICIALES, 
    FICHA_DIMENSIONES_MAP
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sincronizar_dimensiones_aspectos():
    """
    Sincroniza dimensiones y aspectos desde el archivo de configuración.
    
    Estrategia:
    1. Mantiene dimensiones existentes si tienen evaluaciones
    2. Actualiza nombres y descripciones de dimensiones existentes
    3. Agrega nuevas dimensiones que no existen
    4. Actualiza aspectos de cada dimensión
    5. Elimina aspectos que ya no están en la configuración
    """
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            print("\n" + "="*70)
            print("🔄 SINCRONIZACIÓN DE DIMENSIONES Y ASPECTOS")
            print("="*70 + "\n")
            
            # ============================================
            # PASO 1: Sincronizar DIMENSIONES
            # ============================================
            
            logger.info("📊 Sincronizando dimensiones...")
            
            dimensiones_actualizadas = 0
            dimensiones_nuevas = 0
            
            for dim_config in DIMENSIONES_INICIALES:
                # Verificar si la dimensión existe
                cursor.execute(
                    "SELECT id, nombre FROM dimensiones WHERE codigo = ?",
                    (dim_config['codigo'],)
                )
                resultado = cursor.fetchone()
                
                if resultado:
                    # ACTUALIZAR dimensión existente
                    dimension_id, nombre_actual = resultado
                    
                    cursor.execute("""
                        UPDATE dimensiones 
                        SET nombre = ?, orden = ?
                        WHERE codigo = ?
                    """, (
                        dim_config['nombre'],
                        dim_config['orden'],
                        dim_config['codigo']
                    ))
                    
                    if nombre_actual != dim_config['nombre']:
                        logger.info(f"  ✏️  Actualizada: {dim_config['codigo']} - '{nombre_actual}' → '{dim_config['nombre']}'")
                    else:
                        logger.info(f"  ✓  Mantenida: {dim_config['codigo']} - {dim_config['nombre']}")
                    
                    dimensiones_actualizadas += 1
                    
                else:
                    # INSERTAR nueva dimensión
                    cursor.execute("""
                        INSERT INTO dimensiones (codigo, nombre, orden)
                        VALUES (?, ?, ?)
                    """, (
                        dim_config['codigo'],
                        dim_config['nombre'],
                        dim_config['orden']
                    ))
                    
                    dimension_id = cursor.lastrowid
                    logger.info(f"  ➕ Nueva: {dim_config['codigo']} - {dim_config['nombre']}")
                    dimensiones_nuevas += 1
                
                # ============================================
                # PASO 2: Sincronizar ASPECTOS de esta dimensión
                # ============================================
                
                # Obtener aspectos actuales de la BD
                cursor.execute("""
                    SELECT id, nombre FROM aspectos 
                    WHERE dimension_id = ?
                """, (dimension_id,))
                aspectos_bd = {nombre: id_ for id_, nombre in cursor.fetchall()}
                
                # Aspectos del archivo de configuración
                aspectos_config = set(dim_config['aspectos'])
                
                # Aspectos a AGREGAR (están en config pero no en BD)
                aspectos_nuevos = aspectos_config - set(aspectos_bd.keys())
                
                # Aspectos a ELIMINAR (están en BD pero no en config)
                aspectos_eliminar = set(aspectos_bd.keys()) - aspectos_config
                
                # AGREGAR nuevos aspectos
                for orden, nombre_aspecto in enumerate(dim_config['aspectos'], start=1):
                    if nombre_aspecto in aspectos_nuevos:
                        cursor.execute("""
                            INSERT INTO aspectos (dimension_id, nombre, orden)
                            VALUES (?, ?, ?)
                        """, (dimension_id, nombre_aspecto, orden))
                        logger.info(f"      ➕ Aspecto nuevo: {nombre_aspecto}")
                    else:
                        # Actualizar orden del aspecto existente
                        cursor.execute("""
                            UPDATE aspectos 
                            SET orden = ?
                            WHERE dimension_id = ? AND nombre = ?
                        """, (orden, dimension_id, nombre_aspecto))
                
                # ELIMINAR aspectos obsoletos (verificar que no tengan evaluaciones)
                for nombre_aspecto in aspectos_eliminar:
                    aspecto_id = aspectos_bd[nombre_aspecto]
                    
                    # Verificar si tiene evaluaciones
                    cursor.execute("""
                        SELECT COUNT(*) FROM evaluaciones 
                        WHERE aspecto_id = ?
                    """, (aspecto_id,))
                    num_evaluaciones = cursor.fetchone()[0]
                    
                    if num_evaluaciones > 0:
                        logger.warning(f"      ⚠️  NO eliminado (tiene {num_evaluaciones} evaluaciones): {nombre_aspecto}")
                    else:
                        cursor.execute("DELETE FROM aspectos WHERE id = ?", (aspecto_id,))
                        logger.info(f"      🗑️  Eliminado: {nombre_aspecto}")
            
            # ============================================
            # PASO 3: Sincronizar FICHAS
            # ============================================
            
            logger.info("\n🎭 Sincronizando fichas...")
            
            fichas_actualizadas = 0
            fichas_nuevas = 0
            
            for ficha_config in FICHAS_INICIALES:
                cursor.execute(
                    "SELECT id, nombre FROM fichas WHERE codigo = ?",
                    (ficha_config['codigo'],)
                )
                resultado = cursor.fetchone()
                
                if resultado:
                    # ACTUALIZAR ficha existente
                    ficha_id, nombre_actual = resultado
                    
                    cursor.execute("""
                        UPDATE fichas 
                        SET nombre = ?, descripcion = ?
                        WHERE codigo = ?
                    """, (
                        ficha_config['nombre'],
                        ficha_config['descripcion'],
                        ficha_config['codigo']
                    ))
                    
                    logger.info(f"  ✓  Actualizada: {ficha_config['codigo']} - {ficha_config['nombre']}")
                    fichas_actualizadas += 1
                    
                else:
                    # INSERTAR nueva ficha
                    cursor.execute("""
                        INSERT INTO fichas (codigo, nombre, descripcion)
                        VALUES (?, ?, ?)
                    """, (
                        ficha_config['codigo'],
                        ficha_config['nombre'],
                        ficha_config['descripcion']
                    ))
                    
                    logger.info(f"  ➕ Nueva: {ficha_config['codigo']} - {ficha_config['nombre']}")
                    fichas_nuevas += 1
            
            # ============================================
            # PASO 4: Sincronizar RELACIONES FICHA-DIMENSIONES
            # ============================================
            
            logger.info("\n🔗 Sincronizando relaciones ficha-dimensiones...")
            
            for ficha_codigo, dim_codigos in FICHA_DIMENSIONES_MAP.items():
                # Obtener ID de la ficha
                cursor.execute("SELECT id FROM fichas WHERE codigo = ?", (ficha_codigo,))
                resultado = cursor.fetchone()
                
                if not resultado:
                    logger.warning(f"  ⚠️  Ficha no encontrada: {ficha_codigo}")
                    continue
                
                ficha_id = resultado[0]
                
                # Obtener relaciones actuales
                cursor.execute("""
                    SELECT fd.id, d.codigo 
                    FROM ficha_dimensiones fd
                    JOIN dimensiones d ON fd.dimension_id = d.id
                    WHERE fd.ficha_id = ?
                """, (ficha_id,))
                
                relaciones_actuales = {codigo: id_ for id_, codigo in cursor.fetchall()}
                
                # Dimensiones que deben estar (según config)
                dim_config_set = set(dim_codigos)
                
                # Dimensiones a AGREGAR
                dims_agregar = dim_config_set - set(relaciones_actuales.keys())
                
                # Dimensiones a ELIMINAR
                dims_eliminar = set(relaciones_actuales.keys()) - dim_config_set
                
                # AGREGAR nuevas relaciones
                for orden, dim_codigo in enumerate(dim_codigos, start=1):
                    cursor.execute("SELECT id FROM dimensiones WHERE codigo = ?", (dim_codigo,))
                    dim_result = cursor.fetchone()
                    
                    if not dim_result:
                        logger.warning(f"    ⚠️  Dimensión no encontrada: {dim_codigo}")
                        continue
                    
                    dimension_id = dim_result[0]
                    
                    if dim_codigo in dims_agregar:
                        cursor.execute("""
                            INSERT INTO ficha_dimensiones (ficha_id, dimension_id, orden)
                            VALUES (?, ?, ?)
                        """, (ficha_id, dimension_id, orden))
                        logger.info(f"    ➕ Agregada relación: {ficha_codigo} → {dim_codigo}")
                    else:
                        # Actualizar orden
                        cursor.execute("""
                            UPDATE ficha_dimensiones 
                            SET orden = ?
                            WHERE ficha_id = ? AND dimension_id = ?
                        """, (orden, ficha_id, dimension_id))
                
                # ELIMINAR relaciones obsoletas
                for dim_codigo in dims_eliminar:
                    relacion_id = relaciones_actuales[dim_codigo]
                    cursor.execute("DELETE FROM ficha_dimensiones WHERE id = ?", (relacion_id,))
                    logger.info(f"    🗑️  Eliminada relación: {ficha_codigo} → {dim_codigo}")
            
            # Confirmar cambios
            conn.commit()
            
            # ============================================
            # RESUMEN FINAL
            # ============================================
            
            print("\n" + "="*70)
            print("✅ SINCRONIZACIÓN COMPLETADA")
            print("="*70)
            
            # Contar totales actuales
            cursor.execute("SELECT COUNT(*) FROM dimensiones")
            total_dims = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM aspectos")
            total_aspectos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM fichas")
            total_fichas = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ficha_dimensiones")
            total_relaciones = cursor.fetchone()[0]
            
            print(f"\n📊 ESTADÍSTICAS:")
            print(f"  • Dimensiones: {total_dims} ({dimensiones_nuevas} nuevas, {dimensiones_actualizadas} actualizadas)")
            print(f"  • Aspectos: {total_aspectos}")
            print(f"  • Fichas: {total_fichas} ({fichas_nuevas} nuevas, {fichas_actualizadas} actualizadas)")
            print(f"  • Relaciones ficha-dimensión: {total_relaciones}")
            
            print("\n" + "="*70 + "\n")
            
            return True
            
    except Exception as e:
        logger.exception(f"❌ Error en sincronización: {e}")
        return False


def verificar_integridad_post_sync():
    """Verifica que la sincronización mantuvo la integridad de los datos"""
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            print("\n🔍 Verificando integridad post-sincronización...\n")
            
            # Verificar evaluaciones huérfanas
            cursor.execute("""
                SELECT COUNT(*) FROM evaluaciones e
                WHERE NOT EXISTS (
                    SELECT 1 FROM aspectos a WHERE a.id = e.aspecto_id
                )
            """)
            eval_huerfanas = cursor.fetchone()[0]
            
            if eval_huerfanas > 0:
                logger.error(f"❌ Encontradas {eval_huerfanas} evaluaciones con aspectos inexistentes")
                return False
            
            # Verificar relaciones ficha-dimensiones
            cursor.execute("""
                SELECT COUNT(*) FROM ficha_dimensiones fd
                WHERE NOT EXISTS (
                    SELECT 1 FROM fichas f WHERE f.id = fd.ficha_id
                ) OR NOT EXISTS (
                    SELECT 1 FROM dimensiones d WHERE d.id = fd.dimension_id
                )
            """)
            rel_huerfanas = cursor.fetchone()[0]
            
            if rel_huerfanas > 0:
                logger.error(f"❌ Encontradas {rel_huerfanas} relaciones huérfanas")
                return False
            
            logger.info("✅ Integridad verificada correctamente")
            return True
            
    except Exception as e:
        logger.exception(f"❌ Error verificando integridad: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 Iniciando sincronización de dimensiones y aspectos...\n")
    
    if sincronizar_dimensiones_aspectos():
        if verificar_integridad_post_sync():
            print("✅ Proceso completado exitosamente")
        else:
            print("⚠️ Sincronización completada pero hay problemas de integridad")
    else:
        print("❌ Error en la sincronización")
