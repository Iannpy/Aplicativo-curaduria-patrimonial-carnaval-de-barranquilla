import pandas as pd
import streamlit as st
import altair as alt
import pandas as pd


def mostrar_evaluaciones_detalladas(df_eval: pd.DataFrame) -> None:
    """Tabla detallada de todas las evaluaciones"""

    st.header("📋 Evaluaciones Detalladas")
    st.caption("Vista completa de todas las evaluaciones por aspecto")

    # Opciones de visualización
    col_opt1, col_opt2, col_opt3 = st.columns([3, 1, 1])

    with col_opt1:
        buscar = st.text_input(
            "🔍 Buscar",
            placeholder="Buscar por grupo, curador, dimensión o aspecto...",
        )

    with col_opt2:
        st.markdown("<br>", unsafe_allow_html=True)
        filtro_resultado = st.selectbox(
            "Filtrar por resultado",
            ["Todos", "🟢 Fortaleza (2)", "🟡 Oportunidad (1)", "🔴 Riesgo (0)"]
        )

    with col_opt3:
        st.markdown("<br>", unsafe_allow_html=True)
        # Export placeholder; real export implemented in exports.py if needed

    # Filtrar
    df_mostrar = df_eval.copy()
    if buscar:
        df_mostrar = df_mostrar[
            df_mostrar['nombre_propuesta'].str.contains(buscar, case=False, na=False) |
            df_mostrar['curador'].str.contains(buscar, case=False, na=False) |
            df_mostrar['dimension'].str.contains(buscar, case=False, na=False) |
            df_mostrar['aspecto'].str.contains(buscar, case=False, na=False) |
            df_mostrar['ficha_grupo'].astype(str).str.contains(buscar, case=False, na=False)
        ]

    if filtro_resultado != "Todos":
        resultado_map = {
            "🟢 Fortaleza (2)": 2,
            "🟡 Oportunidad (1)": 1,
            "🔴 Riesgo (0)": 0
        }
        df_mostrar = df_mostrar[df_mostrar['resultado'] == resultado_map[filtro_resultado]]

    # Mapear resultados a emojis
    df_mostrar['resultado_emoji'] = df_mostrar['resultado'].map({2: '🟢', 1: '🟡', 0: '🔴'})

    # Mostrar tabla
    st.dataframe(
        df_mostrar[[
            'curador', 'codigo_grupo', 'nombre_propuesta', 'ficha_grupo',
            'modalidad', 'dimension', 'aspecto', 'resultado_emoji',
            'observacion', 'fecha_registro'
        ]].sort_values('fecha_registro', ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            'resultado_emoji': st.column_config.TextColumn('Resultado')
        }
    )

    _count = len(df_mostrar)
    st.caption(f"Total de registros: {_count}")

    col_exp1, col_exp2, col_exp3 = st.columns([1, 2, 1])
    with col_exp2:
        csv_data = df_mostrar.to_csv(index=False)
        st.download_button(
            label="📥 Exportar CSV",
            data=csv_data,
            file_name=f"evaluaciones_detalladas_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="primary"
        )
