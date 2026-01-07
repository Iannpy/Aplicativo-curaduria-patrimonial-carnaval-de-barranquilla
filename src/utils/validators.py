"""
Módulo de validaciones
"""
import re
from typing import Optional, Tuple
from src.config import config


def validar_codigo_grupo(codigo: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Valida el código de grupo (versión flexible - acepta cualquier formato).
    
    Args:
        codigo: Código del grupo a validar
        
    Returns:
        Tupla (es_valido, codigo_limpio, mensaje_error)
        
    Examples:
        >>> validar_codigo_grupo("P00012")
        (True, "P00012", None)
        >>> validar_codigo_grupo("115")
        (True, "115", None)
        >>> validar_codigo_grupo("GRUPO-A-001")
        (True, "GRUPO-A-001", None)
    """
    if not codigo:
        return False, None, "El código no puede estar vacío"
    
    # Convertir a string y limpiar espacios
    codigo_limpio = str(codigo).strip().upper()
    
    # Validación mínima: que tenga al menos un carácter alfanumérico
    if not re.search(r'[A-Z0-9]', codigo_limpio):
        return False, None, "El código debe contener al menos un carácter alfanumérico"
    
    # Limitar longitud máxima razonable
    if len(codigo_limpio) > 50:
        return False, None, "El código es demasiado largo (máximo 50 caracteres)"
    
    return True, codigo_limpio, None


def validar_observacion(texto: str, min_chars: int = None) -> Tuple[bool, Optional[str]]:
    """
    Valida que la observación sea sustancial y no genérica.
    
    Args:
        texto: Texto de la observación
        min_chars: Mínimo de caracteres (por defecto usa config)
        
    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if min_chars is None:
        min_chars = config.min_caracteres_observacion
    
    if not texto or not texto.strip():
        return False, "La observación no puede estar vacía"
    
    texto_limpio = texto.strip()
    
    # Validar longitud mínima
    if len(texto_limpio) < min_chars:
        return False, f"La observación debe tener al menos {min_chars} caracteres"
    
    # Detectar observaciones genéricas no permitidas
    frases_prohibidas = [
        "bien", "ok", "regular", "malo", "bueno",
        "n/a", "na", "ninguna", "sin observaciones",
        "todo bien", "todo ok", "todo correcto"
    ]
    
    if texto_limpio.lower() in frases_prohibidas:
        return False, "La observación es demasiado genérica. Sea más específico"
    
    # Validar que tenga al menos 3 palabras
    palabras = texto_limpio.split()
    if len(palabras) < 3:
        return False, "La observación debe contener al menos 3 palabras"
    
    return True, None


def validar_resultado(resultado: int) -> Tuple[bool, Optional[str]]:
    """
    Valida que el resultado esté en el rango permitido.
    
    Args:
        resultado: Valor numérico del resultado (0, 1, 2)
        
    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if resultado not in [0, 1, 2]:
        return False, "El resultado debe ser 0, 1 o 2"
    
    return True, None


def validar_datos_completos(resultados: list, dimensiones: list) -> Tuple[bool, Optional[str]]:
    """
    Valida que todos los datos de evaluación estén completos.
    
    Args:
        resultados: Lista de tuplas (resultado, observacion)
        dimensiones: Lista de dimensiones a evaluar
        
    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if len(resultados) != len(dimensiones):
        return False, "Debe evaluar todas las dimensiones"
    
    for i, (resultado, observacion) in enumerate(resultados):
        # Validar resultado
        valido, error = validar_resultado(resultado)
        if not valido:
            return False, f"Dimensión {i+1}: {error}"
        
        # Validar observación
        valido, error = validar_observacion(observacion)
        if not valido:
            return False, f"Dimensión {i+1}: {error}"
    
    return True, None