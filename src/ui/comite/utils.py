"""
Utilidades compartidas para las vistas del comité
"""

from src.config import config


def estado_patrimonial(promedio: float) -> str:
    """
    Determina el estado patrimonial según el promedio

    Args:
        promedio: Promedio de calificaciones

    Returns:
        String con emoji y texto del estado
    """
    if promedio < config.umbrales.riesgo_max:
        return f"{config.umbrales.emoji_riesgo}"
    elif promedio < config.umbrales.mejora_max:
        return f"{config.umbrales.emoji_mejora}"
    else:
        return f"{config.umbrales.emoji_fortalecimiento}"


def estado_patrimonial_texto(promedio: float) -> str:
    """
    Determina el estado patrimonial según el promedio (versión texto para PDF)

    Args:
        promedio: Promedio de calificaciones

    Returns:
        String descriptivo del estado
    """
    promedio_num = float(promedio)
    if promedio_num >= config.umbrales.mejora_max:
        return "Fortalecimiento Patrimonial"
    elif promedio_num >= config.umbrales.riesgo_max:
        return "Oportunidad de Mejora"
    else:
        return "Riesgo Patrimonial"