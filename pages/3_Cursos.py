import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

# 1. Configuración de la página
st.set_page_config(page_title="Rendimiento del Curso", page_icon="📚", layout="wide")

# 2. Conexión a MongoDB (Usando Secretos)
@st.cache_resource
def iniciar_conexion():
    # Asegúrate de tener .streamlit/secrets.toml configurado
    uri = st.secrets["mongo"]["uri"]
    return MongoClient(uri)

client = iniciar_conexion()
db = client["universidad_horizonte"]

# 3. Interfaz de Búsqueda
st.title("📚 Análisis de Rendimiento por Curso")
st.markdown("Evalúa el desempeño general, asistencia y distribución de notas por asignatura.")

st.divider()

# Columna para el buscador
col_buscar, _ = st.columns([1, 2])
with col_buscar:
    # Usamos un valor por defecto para agilizar pruebas (ej. el curso de tu base de datos)
    course_id_input = st.text_input("Ingrese el ID del Curso (Ej. CS201 o CS301)", value="CS201").strip().upper()

if course_id_input:
    # 4. Consultas a la Base de Datos
    course_data = db.courses.find_one({"course_id": course_id_input})
    
    # Buscamos todas las matrículas asociadas a este curso
    enrollments = list(db.enrollments.find({"course_id": course_id_input}))
    
    if not enrollments and not course_data:
        st.warning(f"No se encontró información ni matrículas para el curso: {course_id_input}")
    elif not enrollments:
         st.info(f"El curso {course_data.get('name', course_id_input)} existe, pero no tiene alumnos matriculados actualmente.")
    else:
        # Si no encontró el curso en 'courses' pero sí hay 'enrollments', mostramos el ID
        nombre_curso = course_data.get('name', 'Nombre no registrado') if course_data else course_id_input
        
        # 5. Sección: Encabezado del Curso y KPIs (Cards)
        st.header(f"Curso: {nombre_curso}")
        st.caption(f"Código: {course_id_input}")
        
        st.markdown("### Indicadores Globales del Curso")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        # Cálculo de KPIs
        total_alumnos = len(enrollments)
        
        # Extraemos las notas y asistencias válidas
        notas = [e.get('final_grade', 0) for e in enrollments if isinstance(e.get('final_grade'), (int, float))]
        asistencias = [e.get('attendance_rate', 0) for e in enrollments if isinstance(e.get('attendance_rate'), (int, float))]
        
        promedio_curso = sum(notas) / len(notas) if notas else 0
        asistencia_promedio = sum(asistencias) / len(asistencias) if asistencias else 0
        
        # Consideramos nota aprobatoria >= 11 (Ajusta según tu escala)
        aprobados = len([n for n in notas if n >= 11])
        tasa_aprobacion = (aprobados / total_alumnos) * 100 if total_alumnos > 0 else 0

        kpi1.metric(label="Total de Matriculados", value=total_alumnos)
        kpi2.metric(label="Promedio del Curso", value=f"{promedio_curso:.1f} / 20")
        kpi3.metric(label="Tasa de Aprobación", value=f"{tasa_aprobacion:.1f}%")
        kpi4.metric(label="Asistencia Promedio", value=f"{asistencia_promedio * 100:.1f}%")

        st.divider()

        # 6. Sección: Gráficos Interactivos con Plotly
        df_enroll = pd.DataFrame(enrollments)
        
        col_graf_1, col_graf_2 = st.columns(2)

        with col_graf_1:
            st.subheader("Distribución de Notas")
            # Histograma para ver la concentración de calificaciones
            fig_dist = px.histogram(
                df_enroll, 
                x="final_grade", 
                nbins=10,
                color_discrete_sequence=['#2E86C1'],
                labels={'final_grade': 'Nota Final', 'count': 'Cantidad de Alumnos'},
                title="Frecuencia de Calificaciones"
            )
            fig_dist.add_vline(x=11, line_dash="dash", line_color="red", annotation_text="Aprobación (11)")
            st.plotly_chart(fig_dist, use_container_width=True)

        with col_graf_2:
            st.subheader("Relación: Asistencia vs. Nota Final")
            # Gráfico de dispersión (Scatter) para ver si ir a clase afecta la nota
            fig_scatter = px.scatter(
                df_enroll, 
                x="attendance_rate", 
                y="final_grade",
                hover_data=['student_id'],
                color='final_grade',
                color_continuous_scale='Viridis',
                labels={'attendance_rate': 'Tasa de Asistencia (0 a 1)', 'final_grade': 'Nota Final'},
                title="Impacto de la Asistencia en el Rendimiento"
            )
            # Formatear el eje X como porcentaje
            fig_scatter.update_layout(xaxis_tickformat='%')
            fig_scatter.add_hline(y=11, line_dash="dot", line_color="red")
            st.plotly_chart(fig_scatter, use_container_width=True)

        # 7. Sección: Listado de Estudiantes del Curso
        st.subheader("Listado de Estudiantes Matriculados")
        
        # Preparar el dataframe para mostrar
        df_mostrar = df_enroll[['student_id', 'term', 'final_grade', 'attendance_rate']].copy()
        
        # Formatear la columna de asistencia a porcentaje para que se vea mejor
        df_mostrar['attendance_rate'] = (df_mostrar['attendance_rate'] * 100).map('{:.1f}%'.format)
        
        # Renombrar columnas
        df_mostrar.rename(columns={
            'student_id': 'ID Estudiante', 
            'term': 'Ciclo', 
            'final_grade': 'Nota Final', 
            'attendance_rate': 'Asistencia'
        }, inplace=True)
        
        # Mostramos la tabla ordenable
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
