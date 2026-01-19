"""
Funciones de exportación para las vistas del comité
Incluye PDF, Excel, CSV y backups
"""

import pandas as pd
from io import BytesIO
import zipfile
import os
from fpdf import FPDF
from src.config import config
from .utils import estado_patrimonial_texto


def generar_pdf_grupo(df_grupo: pd.DataFrame) -> bytes:
    """Genera un PDF con el informe detallado del grupo"""

    grupo_info = df_grupo.iloc[0]
    codigo_grupo = grupo_info['codigo_grupo']
    nombre_grupo = grupo_info['nombre_propuesta']

    pdf = FPDF()
    pdf.add_page()

    # Título
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Informe de Evaluacion Patrimonial", ln=True, align="C")
    pdf.cell(0, 10, f"Grupo: {nombre_grupo} ({codigo_grupo})", ln=True, align="C")
    pdf.cell(0, 10, f"Evento: {config.nombre_evento}", ln=True, align="C")
    pdf.ln(10)

    # Métricas principales
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Metricas Principales", ln=True)
    pdf.set_font("Arial", "", 10)

    promedio_grupo = df_grupo['resultado'].mean()
    evaluaciones_total = len(df_grupo)
    curadores_unicos = df_grupo['curador'].nunique()
    aspectos_evaluados = df_grupo['aspecto'].nunique()

    pdf.cell(0, 8, f"Promedio General: {promedio_grupo:.2f}", ln=True)
    pdf.cell(0, 8, f"Total Evaluaciones: {evaluaciones_total}", ln=True)
    pdf.cell(0, 8, f"Curadores Participantes: {curadores_unicos}", ln=True)
    pdf.cell(0, 8, f"Aspectos Evaluados: {aspectos_evaluados}", ln=True)

    estado_texto = estado_patrimonial_texto(promedio_grupo)
    pdf.cell(0, 8, f"Estado Patrimonial: {estado_texto}", ln=True)
    pdf.ln(5)

    # Desempeño por dimensión
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Desempeno por Dimension", ln=True)
    pdf.set_font("Arial", "", 10)

    df_dim_grupo = (df_grupo
        .groupby('dimension', as_index=False)
        .agg(
            promedio=('resultado', 'mean'),
            evaluaciones=('resultado', 'count')
        )
        .sort_values('promedio', ascending=False)
    )

    for _, row in df_dim_grupo.iterrows():
        pdf.cell(0, 8, f"{row['dimension']}: {row['promedio']:.2f} ({int(row['evaluaciones'])} evaluaciones)", ln=True)

    pdf.ln(5)

    # Desempeño por aspecto
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Detalle por Aspecto", ln=True)
    pdf.set_font("Arial", "", 9)

    df_aspecto_grupo = (df_grupo
        .groupby(['dimension', 'aspecto'], as_index=False)
        .agg(promedio=('resultado', 'mean'))
        .sort_values(['dimension', 'promedio'], ascending=[True, False])
    )

    for _, row in df_aspecto_grupo.iterrows():
        emoji = 'Fortaleza' if row['promedio'] >= 1.5 else 'Oportunidad' if row['promedio'] >= 0.5 else 'Riesgo'
        pdf.cell(0, 6, f"{row['dimension']} - {row['aspecto']}: {row['promedio']:.2f} ({emoji})", ln=True)

    pdf.ln(5)

    # Observaciones
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Observaciones Cualitativas", ln=True)
    pdf.set_font("Arial", "", 9)

    # Obtener UNA observación por curador (la más reciente o primera disponible)
    observaciones_unicas = (df_grupo[df_grupo['observacion'].notna() & (df_grupo['observacion'].str.strip() != "")]
        .drop_duplicates(subset=['curador'], keep='first')
        .sort_values('fecha_registro', ascending=False)
    )
    
    if not observaciones_unicas.empty:
        for _, row in observaciones_unicas.iterrows():
            pdf.multi_cell(0, 6, f"{row['curador']}: {row['observacion']}")
            pdf.ln(2)
    else:
        pdf.cell(0, 6, "No hay observaciones cualitativas registradas", ln=True)

    # Retornar bytes directamente
    return pdf.output(dest='S').encode('latin-1')

def crear_backup_zip() -> bytes:
    """Crea un archivo ZIP con backup de la base de datos y archivos relacionados"""
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Agregar la base de datos
        db_path = config.db_path
        if os.path.exists(db_path):
            zip_file.write(db_path, os.path.basename(db_path))
        else:
            raise FileNotFoundError("Archivo de base de datos no encontrado")

        # Agregar archivo de configuración si existe
        excel_path = config.excel_path
        if os.path.exists(excel_path):
            zip_file.write(excel_path, os.path.basename(excel_path))

    zip_buffer.seek(0)
    return zip_buffer.getvalue()