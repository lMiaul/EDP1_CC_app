import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

# 1. Configuración de la página
st.set_page_config(page_title="Rendimiento del Curso", page_icon="📚", layout="wide")

# 2. Conexión a MongoDB
@st.cache_resource
def iniciar_conexion():
    uri = st.secrets["mongo"]["uri"]
    return MongoClient(uri)

client = iniciar_conexion()
db = client["universidad_horizonte"]

# 3. Interfaz de Búsqueda
st.title("📚 Análisis de Rendimiento por Curso")
st.markdown("Evalúa el desempeño general, asistencia y distribución de notas mediante filtros interactivos.")

st.divider()

col_buscar, _ = st.columns([1, 2])
with col_buscar:
    course_id_input = st.text_input("Ingrese el ID del Curso (Ej. CS201 o CS301)", value="CS201").strip().upper()

if course_id_input:
    # 4. Consultas a la Base de Datos
    course_data = db.courses.find_one({"course_id": course_id_input})
    enrollments_data = list(db.enrollments.find({"course_id": course_id_input}))
    
    if not enrollments_data and not course_data:
        st.warning(f"No se encontró información ni matrículas para el curso: {course_id_input}")
    elif not enrollments_data:
         st.info(f"El curso {course_data.get('name', course_id_input)} existe, pero no tiene alumnos matriculados actualmente.")
    else:
        nombre_curso = course_data.get('name', 'Nombre no registrado') if course_data else course_id_input
        st.header(f"Curso: {nombre_curso} ({course_id_input})")
        
        # --- NUEVA SECCIÓN: CONVERSIÓN Y FILTROS EN PANDAS ---
        # Convertimos la lista de diccionarios a un DataFrame para filtrarlo fácilmente
        df_enroll = pd.DataFrame(enrollments_data)
        
        # Asegurarnos de que las notas sean numéricas para poder filtrarlas
        df_enroll['final_grade'] = pd.to_numeric(df_enroll['final_grade'], errors='coerce')
        
        st.markdown("### 🔍 Filtros de Análisis")
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            # Filtro por Ciclo (Term)
            ciclos_disponibles = df_enroll['term'].dropna().unique().tolist()
            ciclos_seleccionados = st.multiselect(
                "Seleccionar Ciclo(s)", 
                options=ciclos_disponibles, 
                default=ciclos_disponibles
            )

        with col_f2:
            # Tipo de operador para la nota
            tipo_filtro_nota = st.selectbox(
                "Condición de Nota", 
                ["Mostrar Todas", "Mayor o igual a (>=)", "Menor o igual a (<=)", "Entre (Rango)"]
            )

        with col_f3:
            # Valor(es) para el filtro de nota dependiendo de la selección anterior
            if tipo_filtro_nota == "Mayor o igual a (>=)":
                val_min = st.number_input("Nota mínima", min_value=0, max_value=20, value=11)
            elif tipo_filtro_nota == "Menor o igual a (<=)":
                val_max = st.number_input("Nota máxima", min_value=0, max_value=20, value=10)
            elif tipo_filtro_nota == "Entre (Rango)":
                val_rango = st.slider("Rango de notas", min_value=0, max_value=20, value=(10, 15))
            else:
                st.write("*(Sin restricción de notas)*")

        # Aplicamos la lógica de filtrado al DataFrame original
        df_filtrado = df_enroll[df_enroll['term'].isin(ciclos_seleccionados)].copy()

        if tipo_filtro_nota == "Mayor o igual a (>=)":
            df_filtrado = df_filtrado[df_filtrado['final_grade'] >= val_min]
        elif tipo_filtro_nota == "Menor o igual a (<=)":
            df_filtrado = df_filtrado[df_filtrado['final_grade'] <= val_max]
        elif tipo_filtro_nota == "Entre (Rango)":
            df_filtrado = df_filtrado[(df_filtrado['final_grade'] >= val_rango[0]) & (df_filtrado['final_grade'] <= val_rango[1])]

        st.divider()

        # Validación en caso de que los filtros dejen la tabla vacía
        if df_filtrado.empty:
            st.warning("No hay estudiantes que coincidan con los filtros aplicados.")
        else:
            # 5. KPIs Dinámicos (Basados en df_filtrado)
            st.markdown("### Indicadores del Segmento Filtrado")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            total_alumnos = len(df_filtrado)
            promedio_curso = df_filtrado['final_grade'].mean()
            asistencia_promedio = df_filtrado['attendance_rate'].mean()
            aprobados = len(df_filtrado[df_filtrado['final_grade'] >= 11])
            tasa_aprobacion = (aprobados / total_alumnos) * 100
            
            # Usamos fillna(0) en el display por si el promedio es NaN (ej. si no hay notas registradas)
            kpi1.metric(label="Estudiantes Filtrados", value=total_alumnos)
            kpi2.metric(label="Promedio de Notas", value=f"{promedio_curso:.1f} / 20" if pd.notna(promedio_curso) else "N/A")
            kpi3.metric(label="Tasa de Aprobación", value=f"{tasa_aprobacion:.1f}%")
            kpi4.metric(label="Asistencia Promedio", value=f"{asistencia_promedio * 100:.1f}%" if pd.notna(asistencia_promedio) else "N/A")

            st.write("") # Espacio en blanco

            # 6. Gráficos Actualizados (Basados en df_filtrado)
            col_graf_1, col_graf_2 = st.columns(2)

            with col_graf_1:
                st.subheader("Distribución de Notas")
                fig_dist = px.histogram(
                    df_filtrado, 
                    x="final_grade", 
                    nbins=10,
                    color_discrete_sequence=['#2E86C1'],
                    labels={'final_grade': 'Nota Final', 'count': 'Frecuencia'},
                    title="Frecuencia de Calificaciones"
                )
                fig_dist.add_vline(x=11, line_dash="dash", line_color="red", annotation_text="Aprobación (11)")
                st.plotly_chart(fig_dist, use_container_width=True)

            with col_graf_2:
                st.subheader("Relación: Asistencia vs. Nota Final")
                fig_scatter = px.scatter(
                    df_filtrado, 
                    x="attendance_rate", 
                    y="final_grade",
                    hover_data=['student_id'],
                    color='final_grade',
                    color_continuous_scale='Viridis',
                    labels={'attendance_rate': 'Tasa de Asistencia', 'final_grade': 'Nota Final'},
                    title="Impacto de la Asistencia"
                )
                fig_scatter.update_layout(xaxis_tickformat='%')
                fig_scatter.add_hline(y=11, line_dash="dot", line_color="red")
                st.plotly_chart(fig_scatter, use_container_width=True)

            # 7. Tabla Dinámica final
            st.subheader("Detalle de Estudiantes Filtrados")
            df_mostrar = df_filtrado[['student_id', 'term', 'final_grade', 'attendance_rate']].copy()
            df_mostrar['attendance_rate'] = (df_mostrar['attendance_rate'] * 100).map('{:.1f}%'.format)
            df_mostrar.rename(columns={
                'student_id': 'ID Estudiante', 
                'term': 'Ciclo', 
                'final_grade': 'Nota Final', 
                'attendance_rate': 'Asistencia'
            }, inplace=True)
            
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)