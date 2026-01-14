"""
Vista de la interfaz para Curadores
ACTUALIZADO: Evaluación por aspectos individuales
"""
import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from src.config import config
from src.database.models import GrupoModel, EvaluacionModel, DimensionModel, LogModel, AspectoModel
from src.utils.validators import validar_codigo_grupo, validar_observacion

logger = logging.getLogger(__name__)


@st.cache_data
def cargar_grupos_excel():
    """Carga el catálogo de grupos desde Excel con cache"""
    try:
        df = pd.read_excel(config.excel_path)
        logger.info(f"Grupos cargados desde Excel: {len(df)}")
        return df
    except FileNotFoundError:
        st.error(f"⚠️ Archivo no encontrado: {config.excel_path}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error cargando Excel: {e}")
        st.error(f"❌ Error cargando datos: {str(e)}")
        return pd.DataFrame()


def bloque_aspecto(dimension_nombre: str, aspecto_nombre: str, key_prefix: str):
    """
    Renderiza un bloque de evaluación para un aspecto individual
    
    Args:
        dimension_nombre: Nombre de la dimensión padre
        aspecto_nombre: Nombre del aspecto a evaluar
        key_prefix: Prefijo único para las claves de widgets
        
    Returns:
        Tupla (resultado, observacion)
    """
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
        <p style="margin: 0; color: #666; font-size: 13px;"><b>{dimension_nombre}</b></p>
        <p style="margin: 5px 0 0 0; font-size: 16px; font-weight: bold;">{aspecto_nombre}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_resultado, col_obs = st.columns([1, 3])
    
    # Columna 1: Resultado
    with col_resultado:
        st.markdown("**Calificación:**")
        resultado = st.selectbox(
            "Seleccione",
            [2, 1, 0],
            key=f"res_{key_prefix}",
            format_func=lambda x: {
                2: "🟢",
                1: "🟡",
                0: "🔴"
            }[x],
            label_visibility="collapsed"
        )
    
    # Columna 2: Observación
    with col_obs:
        st.markdown("**Observación cualitativa:**")
        observacion = st.text_area(
            "",
            height=50,
            key=f"obs_{key_prefix}",
            placeholder=f"Describa lo observado específicamente para '{aspecto_nombre}'...",
            label_visibility="collapsed"
        )
        
        # Validación en tiempo real
        if observacion:
            valido, error = validar_observacion(observacion)
            if not valido:
                st.error(f"⚠️ {error}")
            else:
                st.success(f"✓ {len(observacion)} caracteres")
    
    return resultado, observacion


def mostrar_vista_curador():
    """Renderiza la vista completa del curador"""
    # ============================================================
    # Encabezado
    # ============================================================
    col1, col2, col3 = st.columns([0.8, 4, 1])
    with col1:
        st.image("assets/CDB_EMPRESA_ASSETS.svg", width=200, clamp=True)
    with col2:
        st.markdown(f"""
            <div>
                <h1 style="font-size:24px;">Ficha de Observación Cualitativa 2026</h1>
                <p style=" padding: 0; margin: 0;">
                    <b>Evento:</b> {config.nombre_evento}
                </p>
            </div>
            """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div>  
                <p style="text-align:center; padding: 20px; margin: 0;">
                    <b>Curador:</b> {st.session_state.usuario}
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="gradient-bar"></div>', unsafe_allow_html=True) 
    st.markdown("<div style='margin:0;'>" \
    "<p style='text-align:right; font-size:14px; color: gray; margin: 0;'>" \
    "Fecha de acceso: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + \
    "</p></div>", unsafe_allow_html=True)
    
    col1_global, col2_global, col3_global = st.columns([1, 6, 1])
    with col2_global:
        # Cargar catálogo de grupos
        df_grupos = cargar_grupos_excel()
        
        if df_grupos.empty:
            st.warning("⚠️ No se pudo cargar el catálogo de grupos. Contacte al administrador.")
            st.stop()
        
        # Sección: Búsqueda de grupo
        st.subheader("🔍 Búsqueda de Grupo")
        
        col_busq1, col_busq2 = st.columns([2, 1])
        
        with col_busq1:
            id_busqueda = st.text_input(
                "Ingrese el código del grupo:",
                placeholder="P123",
                help="Ingrese el código tal como aparece en su listado"
            )
        
        with col_busq2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Buscar", type="primary", use_container_width=True):
                if id_busqueda:
                    st.rerun()
        
        # Buscar grupo
        grupo = None
        if id_busqueda:
            # Validar código
            valido, codigo_limpio, error = validar_codigo_grupo(id_busqueda)
            
            if not valido:
                st.error(f"❌ {error}")
                st.stop()
            
            # Buscar en el dataframe
            resultado = df_grupos[df_grupos['Codigo'].astype(str).str.upper() == codigo_limpio]
            
            # Si no encuentra, intentar búsqueda parcial
            if resultado.empty:
                resultado = df_grupos[df_grupos['Codigo'].astype(str).str.contains(codigo_limpio, case=False, na=False)]
            
            if resultado.empty:
                st.error(f"❌ Grupo no encontrado: {codigo_limpio}")
                st.info("💡 Verifique que el código sea correcto")
                
                # Mostrar sugerencias
                with st.expander("Ver todos los códigos disponibles"):
                    st.dataframe(
                        df_grupos[['Codigo', 'Nombre_Propuesta']],
                        use_container_width=True
                    )
                st.stop()
            else:
                grupo = resultado.iloc[0]
                st.success(f"✅ Grupo encontrado: {grupo['Nombre_Propuesta']}")
        else:
            st.info("👆 Ingrese un código de grupo para comenzar la evaluación")
            st.stop()
        
        # Verificar si ya evaluó este grupo
        if EvaluacionModel.evaluacion_existe(st.session_state.usuario_id, str(grupo['Codigo'])):
            st.error(f"⚠️ Ya evaluó este grupo anteriormente")
            st.info("No puede evaluar el mismo grupo más de una vez")
            st.stop()
        
        st.markdown("---")
        
        # Datos del grupo
        st.subheader("📋 Datos del Grupo")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.text_input("Código", value=grupo['Codigo'], disabled=True)
            st.text_input("Modalidad", value=grupo['Modalidad'], disabled=True)
        
        with col2:
            st.text_input("Tipo", value=grupo['Tipo'], disabled=True)
            st.text_input("Tamaño", value=grupo.get('Tamaño', 'N/A'), disabled=True)
        
        with col3:
            st.text_input("Naturaleza", value=grupo['Naturaleza'], disabled=True)
            st.text_input("Nombre de la Propuesta", value=grupo['Nombre_Propuesta'], disabled=True)
        
        st.info(f"🎭 **Ahora se presenta:** '{grupo['Nombre_Propuesta']}'")
        
        st.markdown("---")
        
        # Formulario de evaluación
        st.subheader("📝 Evaluación por Aspectos")
        
        # Obtener aspectos agrupados por dimensión
        aspectos_por_dimension = AspectoModel.obtener_agrupados_por_dimension()
        
        if not aspectos_por_dimension:
            st.error("❌ No se pudieron cargar los aspectos de evaluación")
            st.stop()
        
        with st.form("formulario_evaluacion", clear_on_submit=False):
            evaluaciones = []  # Lista de tuplas (aspecto_id, resultado, observacion)
            
            # Iterar sobre cada dimensión
            for dim_id, dim_data in sorted(aspectos_por_dimension.items(), key=lambda x: x[1]['dimension']['orden']):
                dimension = dim_data['dimension']
                aspectos = dim_data['aspectos']
                
                # Mostrar título de dimensión
                st.markdown(f"""
                <div class="dimension-box" style="background: linear-gradient(135deg, #FCAB60 0%, #08A114 100%); 
                     color: white; padding: 15px; border-radius: 10px; margin: 20px 0 15px 0;">
                    <h3 style="margin: 0; font-size: 18px;">{dimension['nombre']}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Evaluar cada aspecto de esta dimensión
                for aspecto in aspectos:
                    resultado, observacion = bloque_aspecto(
                        dimension_nombre=dimension['nombre'],
                        aspecto_nombre=aspecto['nombre'],
                        key_prefix=f"asp_{aspecto['id']}"
                    )
                    evaluaciones.append((aspecto['id'], resultado, observacion))
            
            st.markdown("---")
            
            # Botones
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            
            with col_btn2:
                submitted = st.form_submit_button(
                    "✅ REGISTRAR EVALUACIÓN",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted:
                # Validar que todas las observaciones estén completas
                errores = []
                
                for i, (aspecto_id, resultado, observacion) in enumerate(evaluaciones):
                    valido, error = validar_observacion(observacion)
                    if not valido:
                        # Obtener nombre del aspecto para el mensaje
                        aspecto_nombre = None
                        for dim_data in aspectos_por_dimension.values():
                            for asp in dim_data['aspectos']:
                                if asp['id'] == aspecto_id:
                                    aspecto_nombre = asp['nombre']
                                    break
                            if aspecto_nombre:
                                break
                        
                        errores.append(f"**{aspecto_nombre}:** {error}")
                
                if errores:
                    st.error("❌ Complete correctamente todas las observaciones:")
                    for error in errores:
                        st.markdown(f"• {error}")
                else:
                    # Guardar evaluaciones
                    try:
                        exito = True
                        evaluaciones_guardadas = 0
                        
                        for aspecto_id, resultado, observacion in evaluaciones:
                            eval_id = EvaluacionModel.crear_evaluacion(
                                usuario_id=st.session_state.usuario_id,
                                codigo_grupo=str(grupo['Codigo']),
                                aspecto_id=aspecto_id,
                                resultado=resultado,
                                observacion=observacion
                            )
                            
                            if eval_id:
                                evaluaciones_guardadas += 1
                            else:
                                exito = False
                                break
                        
                        if exito:
                            # Registrar log
                            LogModel.registrar_log(
                                usuario=st.session_state.usuario,
                                accion="EVALUACION_CREADA",
                                detalle=f"Grupo: {grupo['Codigo']} - {grupo['Nombre_Propuesta']} ({evaluaciones_guardadas} aspectos)"
                            )
                            
                            st.success(f"✅ Evaluación guardada exitosamente ({evaluaciones_guardadas} aspectos evaluados)")
                            st.balloons()
                            st.session_state.evaluacion_guardada = True
                        else:
                            st.error("❌ Error al guardar la evaluación")
                            
                    except Exception as e:
                        logger.exception(f"Error guardando evaluación: {e}")
                        st.error(f"❌ Error: {str(e)}")
        
        # Botón para evaluar otro grupo (FUERA del formulario)
        if 'evaluacion_guardada' in st.session_state and st.session_state.evaluacion_guardada:
            st.markdown("---")
            if st.button("➡️ Evaluar otro grupo", type="primary", use_container_width=True):
                st.session_state.evaluacion_guardada = False
                st.rerun()
        
        # Información adicional
        with st.expander("ℹ️ Guía de Evaluación"):
            st.markdown("""
            ### 🎯 Criterios de Calificación
            
            **🟢 Fortaleza Patrimonial**
            - Cumplimiento sobresaliente del aspecto evaluado
            - Evidencia clara y consistente
            - Práctica consolidada y pertinente
            
            **🟡 Oportunidad de Mejora**
            - Cumplimiento parcial del aspecto
            - Evidencia de intención pero con elementos por fortalecer
            - Práctica en proceso de consolidación
            
            **🔴 Riesgo Patrimonial**
            - Incumplimiento del aspecto evaluado
            - Ausencia de elementos fundamentales
            - Práctica que requiere intervención urgente
            
            ---
            
            ### 📝 Guía para Observaciones
            
            Las observaciones deben ser:
            - **Específicas:** Mencione qué observó concretamente en este aspecto
            - **Descriptivas:** Describa la situación sin juicios de valor excesivos
            - **Constructivas:** Oriente sobre qué mantener o mejorar
            - **Enfocadas:** Cada observación debe referirse únicamente al aspecto que está evaluando
            
            **Mínimo:** 20 caracteres por observación
            """)