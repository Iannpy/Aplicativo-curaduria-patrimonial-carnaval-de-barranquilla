"""
Inicialización y creación de la base de datos
"""
import logging
import os
from src.database.connection import ejecutar_script, get_db_connection
from src.config import config

logger = logging.getLogger(__name__)


SCHEMA_SQL = """
-- =====================================================
-- TABLA: usuarios
-- Gestión de curadores y miembros del comité
-- =====================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol TEXT CHECK(rol IN ('curador', 'comite')) NOT NULL,
    activo INTEGER DEFAULT 1,
    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
    
    CHECK(length(username) >= 3)
);

CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);
CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios(rol);


-- =====================================================
-- TABLA: grupos
-- Catálogo de grupos participantes
-- =====================================================
CREATE TABLE IF NOT EXISTS grupos (
    codigo TEXT PRIMARY KEY,
    nombre_propuesta TEXT NOT NULL,
    modalidad TEXT NOT NULL,
    tipo TEXT NOT NULL,
    tamano TEXT,
    naturaleza TEXT,
    ano_evento INTEGER NOT NULL,
    
    CHECK(length(codigo) > 0 AND length(codigo) <= 50),
    CHECK(length(nombre_propuesta) >= 3)
);

CREATE INDEX IF NOT EXISTS idx_grupos_modalidad ON grupos(modalidad);
CREATE INDEX IF NOT EXISTS idx_grupos_ano ON grupos(ano_evento);


-- =====================================================
-- TABLA: dimensiones
-- Catálogo de dimensiones patrimoniales
-- =====================================================
CREATE TABLE IF NOT EXISTS dimensiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    orden INTEGER NOT NULL,
    
    CHECK(orden > 0)
);

CREATE INDEX IF NOT EXISTS idx_dimensiones_orden ON dimensiones(orden);


-- =====================================================
-- TABLA: evaluaciones
-- Registro de evaluaciones realizadas
-- =====================================================
CREATE TABLE IF NOT EXISTS evaluaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    codigo_grupo TEXT NOT NULL,
    dimension_id INTEGER NOT NULL,
    resultado INTEGER CHECK(resultado IN (0, 1, 2)) NOT NULL,
    observacion TEXT NOT NULL,
    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (codigo_grupo) REFERENCES grupos(codigo) ON DELETE CASCADE,
    FOREIGN KEY (dimension_id) REFERENCES dimensiones(id) ON DELETE CASCADE,
    
    UNIQUE(usuario_id, codigo_grupo, dimension_id),
    CHECK(length(observacion) >= 20)
);

CREATE INDEX IF NOT EXISTS idx_evaluaciones_usuario ON evaluaciones(usuario_id);
CREATE INDEX IF NOT EXISTS idx_evaluaciones_grupo ON evaluaciones(codigo_grupo);
CREATE INDEX IF NOT EXISTS idx_evaluaciones_fecha ON evaluaciones(fecha_registro);
CREATE INDEX IF NOT EXISTS idx_evaluaciones_dimension ON evaluaciones(dimension_id);


-- =====================================================
-- TABLA: logs_sistema
-- Auditoría de acciones importantes
-- =====================================================
CREATE TABLE IF NOT EXISTS logs_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    accion TEXT NOT NULL,
    detalle TEXT,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_logs_fecha ON logs_sistema(fecha);
CREATE INDEX IF NOT EXISTS idx_logs_usuario ON logs_sistema(usuario);
"""


DIMENSIONES_INICIALES = [
    ('DIM1', 'Dimensión 1 – Rigor en la ejecución tradicional', 
     'Evaluación de aspectos técnicos y tradicionales de la presentación', 1),
    ('DIM2', 'Dimensión 2 – Transmisión del sentido cultural', 
     'Evaluación de la transmisión de identidad y valores culturales', 2),
    ('DIM3', 'Dimensión 3 – Vitalidad e innovación con pertinencia', 
     'Evaluación de creatividad manteniendo pertinencia cultural', 3),
    ('DIM4', 'Dimensión 4 – Participación comunitaria y relevo', 
     'Evaluación de participación comunitaria y transmisión generacional', 4),
    ('DIM5', 'Dimensión 5 – Sostenibilidad de la práctica', 
     'Evaluación de sostenibilidad organizacional y cultural', 5),
]


def inicializar_base_datos() -> bool:
    """
    Crea las tablas e inicializa datos básicos si no existen.
    
    Returns:
        True si se inicializó correctamente, False en caso contrario
    """
    try:
        logger.info("Inicializando base de datos...")
        
        # Crear esquema
        ejecutar_script(SCHEMA_SQL)
        logger.info("Esquema de base de datos creado")
        
        # Insertar dimensiones si no existen
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM dimensiones")
            count = cursor.fetchone()[0]
            
            if count == 0:
                cursor.executemany(
                    """INSERT INTO dimensiones (codigo, nombre, descripcion, orden)
                       VALUES (?, ?, ?, ?)""",
                    DIMENSIONES_INICIALES
                )
                logger.info(f"Dimensiones iniciales insertadas: {len(DIMENSIONES_INICIALES)}")
            else:
                logger.info(f"Dimensiones ya existen: {count} registros")
        
        logger.info("Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        logger.exception(f"Error inicializando base de datos: {e}")
        return False


def verificar_integridad_bd() -> bool:
    """
    Verifica que la base de datos tenga la estructura correcta.
    
    Returns:
        True si la estructura es válida, False en caso contrario
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar tablas requeridas
            tablas_requeridas = ['usuarios', 'grupos', 'dimensiones', 'evaluaciones']
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tablas_existentes = [row[0] for row in cursor.fetchall()]
            
            for tabla in tablas_requeridas:
                if tabla not in tablas_existentes:
                    logger.error(f"Tabla faltante: {tabla}")
                    return False
            
            logger.info("Integridad de base de datos verificada")
            return True
            
    except Exception as e:
        logger.exception(f"Error verificando integridad: {e}")
        return False


if __name__ == "__main__":
    # Configurar logging para ejecución directa
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Inicializar base de datos
    if inicializar_base_datos():
        print("✅ Base de datos inicializada correctamente")
        
        if verificar_integridad_bd():
            print("✅ Integridad verificada")
        else:
            print("❌ Error en la integridad de la base de datos")
    else:
        print("❌ Error inicializando base de datos")