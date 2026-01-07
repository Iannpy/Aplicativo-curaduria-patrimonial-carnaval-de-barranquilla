"""
Configuración centralizada de la aplicación
"""
import datetime
import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen
for directory in [DATA_DIR, ASSETS_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)


@dataclass
class UmbralesPatrimoniales:
    """Umbrales para clasificación patrimonial"""
    riesgo_max: float = 0.8
    mejora_max: float = 1.59
    
    emoji_riesgo: str = "🔴"
    emoji_mejora: str = "🟡"
    emoji_fortalecimiento: str = "🟢"
    
    texto_riesgo: str = "En riesgo"
    texto_mejora: str = "Por mejorar"
    texto_fortalecimiento: str = "Fortalecimiento"
    
    def __post_init__(self):
        """Cargar valores desde variables de entorno si existen"""
        self.riesgo_max = float(os.getenv("UMBRAL_RIESGO", str(self.riesgo_max)))
        self.mejora_max = float(os.getenv("UMBRAL_MEJORA", str(self.mejora_max)))


@dataclass
class ConfiguracionApp:
    """Configuración general de la aplicación"""
    
    # Información del evento
    nombre_evento: str = field(default_factory=lambda: os.getenv("NOMBRE_EVENTO", "Fin de Semana de la Tradición"))
    ano_evento: int = field(default_factory=lambda: int(os.getenv("ANO_EVENTO", "30000")))
    fecha_evento: str = field(default_factory=lambda: os.getenv("FECHA_EVENTO", str(datetime.datetime.today().strftime("%d/%m/%Y"))))
    # Rutas de archivos
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", str(DATA_DIR / "curaduria.db")))
    excel_path: str = field(default_factory=lambda: os.getenv("EXCEL_PATH", str(DATA_DIR / "propuestas_artisticas.xlsx")))
    logo_path: str = field(default_factory=lambda: os.getenv("LOGO_PATH", str(ASSETS_DIR / "CDB_EMPRESA_ASSETS.svg")))
    
    # Parámetros de validación
    min_caracteres_observacion: int = field(default_factory=lambda: int(os.getenv("MIN_CARACTERES_OBSERVACION", "5")))
    max_grupos_por_curador: int = field(default_factory=lambda: int(os.getenv("MAX_GRUPOS_POR_CURADOR", "500")))
    
    # Umbrales patrimoniales
    umbrales: UmbralesPatrimoniales = field(default_factory=UmbralesPatrimoniales)
    
    # Dimensiones de evaluación
    dimensiones: list = field(default_factory=lambda: [
        (
            "Dimensión 1 – Rigor en la ejecución tradicional",
            [
                "Coreografía / pasos básicos",
                "Expresión dancística",
                "Relación música – danza",
                "Vestuario apropiado (incluye parafernalia)",
                "Marcación del ritmo"
            ]
        ),
        (
            "Dimensión 2 – Transmisión del sentido cultural",
            [
                "Su identidad",
                "Su narrativa",
                "Su historia",
                "El valor simbólico",
            ]
        ),
        (
            "Dimensión 3 – Vitalidad e innovación con pertinencia",
            [
                "Creatividad con respeto",
                "Adaptaciones pertinentes",
                "Renovación generacional o estética sin perder esencia",
            ]
        )
        
    ])


# Instancia global de configuración
config = ConfiguracionApp()