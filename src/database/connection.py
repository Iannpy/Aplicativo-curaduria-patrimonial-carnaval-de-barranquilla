"""
Gestión de conexiones a la base de datos
"""
import sqlite3
import logging
from contextlib import contextmanager
from typing import Generator
from src.config import config

# Configurar logger
logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager para gestionar conexiones a la base de datos.
    Garantiza que la conexión se cierre correctamente incluso si hay errores.
    
    Yields:
        Conexión a la base de datos SQLite
        
    Example:
        >>> with get_db_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM usuarios")
    """
    conn = None
    try:
        conn = sqlite3.connect(config.db_path)
        conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
        logger.debug(f"Conexión establecida: {config.db_path}")
        yield conn
        conn.commit()
        logger.debug("Transacción confirmada")
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            logger.error(f"Error en transacción, rollback ejecutado: {e}")
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Error inesperado: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.debug("Conexión cerrada")


def ejecutar_query(query: str, params: tuple = None) -> list:
    """
    Ejecuta una query SELECT y retorna los resultados.
    
    Args:
        query: Query SQL a ejecutar
        params: Parámetros para la query (opcional)
        
    Returns:
        Lista de resultados
        
    Raises:
        sqlite3.Error: Si hay error en la ejecución
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            resultados = cursor.fetchall()
            logger.debug(f"Query ejecutada: {len(resultados)} resultados")
            return resultados
            
    except sqlite3.Error as e:
        logger.error(f"Error ejecutando query: {e}")
        raise


def ejecutar_insert(query: str, params: tuple) -> int:
    """
    Ejecuta una query INSERT y retorna el ID del registro creado.
    
    Args:
        query: Query SQL INSERT
        params: Parámetros para el INSERT
        
    Returns:
        ID del registro insertado
        
    Raises:
        sqlite3.Error: Si hay error en la ejecución
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            last_id = cursor.lastrowid
            logger.info(f"Registro insertado con ID: {last_id}")
            return last_id
            
    except sqlite3.IntegrityError as e:
        logger.warning(f"Violación de integridad: {e}")
        raise
    except sqlite3.Error as e:
        logger.error(f"Error ejecutando INSERT: {e}")
        raise


def ejecutar_script(script: str) -> None:
    """
    Ejecuta un script SQL completo (múltiples statements).
    
    Args:
        script: Script SQL a ejecutar
        
    Raises:
        sqlite3.Error: Si hay error en la ejecución
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(script)
            logger.info("Script ejecutado exitosamente")
            
    except sqlite3.Error as e:
        logger.error(f"Error ejecutando script: {e}")
        raise