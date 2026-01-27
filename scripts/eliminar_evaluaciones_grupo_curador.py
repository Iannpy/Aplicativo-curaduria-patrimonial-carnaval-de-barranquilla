"""
Script para eliminar evaluaciones de la base de datos.
Se solicitará el código del grupo y el nombre de usuario del curador.
"""
import logging
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.database.connection import get_db_connection
from src.database.models import UsuarioModel, LogModel

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def eliminar_evaluaciones_grupo_curador():
    """Elimina las evaluaciones de un grupo específico realizadas por un curador."""
    logger.info("="*60)
    logger.info("🗑️ ELIMINAR EVALUACIONES ESPECÍFICAS")
    logger.info("="*60)

    # 1. Solicitar código de grupo
    codigo_grupo = input("Ingrese el CÓDIGO DEL GRUPO a eliminar (ej. P123): ").strip().upper()
    if not codigo_grupo:
        logger.error("❌ El código de grupo no puede estar vacío.")
        return False

    # 2. Solicitar nombre de usuario del curador
    username_curador = input("Ingrese el NOMBRE DE USUARIO DEL CURADOR (ej. curador1): ").strip()
    if not username_curador:
        logger.error("❌ El nombre de usuario del curador no puede estar vacío.")
        return False

    # 3. Obtener usuario_id
    usuario_obj = UsuarioModel.obtener_por_username(username_curador)
    if not usuario_obj:
        logger.error(f"❌ Usuario '{username_curador}' no encontrado o inactivo.")
        return False
    usuario_id = usuario_obj['id']

    logger.info(f"\n🔎 Buscando evaluaciones para el grupo '{codigo_grupo}' del curador '{username_curador}'...")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Contar evaluaciones antes de eliminar
            cursor.execute("""
                SELECT COUNT(*) FROM evaluaciones
                WHERE usuario_id = ? AND codigo_grupo = ?
            """, (usuario_id, codigo_grupo))
            num_evaluaciones = cursor.fetchone()[0]

            if num_evaluaciones == 0:
                logger.info("ℹ️ No se encontraron evaluaciones que coincidan con los criterios.")
                return True

            logger.warning(f"⚠️ Se encontraron {num_evaluaciones} evaluaciones para el grupo '{codigo_grupo}' del curador '{username_curador}'.")
            confirmacion = input("¿Está seguro que desea ELIMINAR estas evaluaciones? (s/N): ").strip().lower()

            if confirmacion == 's':
                cursor.execute("""
                    DELETE FROM evaluaciones
                    WHERE usuario_id = ? AND codigo_grupo = ?
                """, (usuario_id, codigo_grupo))
                evaluaciones_eliminadas = cursor.rowcount

                if evaluaciones_eliminadas > 0:
                    logger.info(f"✅ Se eliminaron {evaluaciones_eliminadas} evaluaciones del grupo '{codigo_grupo}' del curador '{username_curador}'.")
                    LogModel.registrar_log(
                        usuario="ScriptAdmin",
                        accion="ELIMINACION_EVAL_INDIVIDUAL",
                        detalle=f"Eliminadas {evaluaciones_eliminadas} evaluaciones de grupo {codigo_grupo} por curador {username_curador}"
                    )
                    # En un entorno de Streamlit, aquí se podría limpiar el caché
                    # st.cache_data.clear() # Esto no funciona en un script standalone
                    return True
                else:
                    logger.error("❌ Error inesperado: No se eliminaron evaluaciones.")
                    return False
            else:
                logger.info("❌ Operación cancelada por el usuario.")
                return False

    except Exception as e:
        logger.exception(f"❌ Error al intentar eliminar evaluaciones: {e}")
        return False

if __name__ == "__main__":
    if eliminar_evaluaciones_grupo_curador():
        logger.info("Script finalizado.")
        sys.exit(0)
    else:
        logger.error("Script finalizado con errores.")
        sys.exit(1)