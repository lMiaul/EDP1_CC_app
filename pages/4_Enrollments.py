import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

# 1. Configuración de la página
st.set_page_config(page_title="Gestión de Matrículas", page_icon="📑", layout="wide")

# 2. Conexión a MongoDB (Uso de secretos y caché)
@st.cache_resource
def iniciar_conexion():
    uri = st.secrets["mongo"]["uri"]
    return MongoClient(uri)

client = iniciar_conexion()
db = client["universidad_horizonte"]

# 3. Interfaz Principal
st.title("📑 Gestión de Matrículas y Grupos")
st.markdown("Filtra estudiantes por curso y ciclo para analizar el rendimiento grupal.")

st.divider()

# 4. Selectores de Filtro (Sidebar o Columnas)
col_f1, col_f2 = st.columns(2)

with col_f1:
    # Obtenemos la lista de cursos para el selector
    cursos = list(db.courses.find({}, {"course_id": 1, "name": 1}))
    lista_cursos = {c['course_id']: f"{c['course_id']} - {c['name']}" for c in cursos}
    curso_seleccionado = st.selectbox("Seleccione el Curso", options=list(lista_cursos.keys()), format_func=lambda x: lista_cursos[x])

with col_f2:
    # Obtenemos los ciclos (terms) disponibles en la base de datos
    ciclos = db.enrollments.distinct("term")
    ciclo_seleccionado = st.selectbox("Seleccione el Ciclo Académico", options=sorted(ciclos, reverse=True))

if curso_seleccionado and ciclo_seleccionado:
    # 5. Obtención de Datos de Matrícula
    query_enroll = {"course_id": curso_seleccionado, "term": ciclo_seleccionado}
    registros_matrícula = list(db.enrollments.find(query_enroll))
    
    if not registros_matrícula:
        st.info(f"No hay estudiantes matriculados en {curso_seleccionado} durante el periodo {ciclo_seleccionado}.")
    else:
        # Extraemos los IDs de los estudiantes para buscar sus nombres
        student_ids = [r['student_id'] for r in registros_matrícula]
        info_estudiantes = list(db.students.find({"student_id": {"$in": student_ids}}, {"student_id": 1, "first_name": 1, "last_name": 1}))
        
        # Mapeamos los nombres a sus IDs para unirlos fácilmente
        mapa_nombres = {e['student_id']: f"{e['first_name']} {e['last_name']}" for e in info_estudiantes}
        mapa_apellidos = {e['student_id']: e['last_name'] for e in info_estudiantes}
        mapa_nombres_solo = {e['student_id']: e['first_name'] for e in info_estudiantes}

        # 6. Construcción del DataFrame solicitado
        data = []
        for reg in registros_matrícula:
            s_id = reg['student_id']
            # Para "Cursos actuales", buscamos cuántos cursos lleva ese alumno en ese ciclo
            otros_cursos = db.enrollments.distinct("course_id", {"student_id": s_id, "term": ciclo_seleccionado})
            
            data.append({
                "Código": s_id,
                "Nombres": mapa_nombres_solo.get(s_id, "N/A"),
                "Apellidos": mapa_apellidos.get(s_id, "N/A"),
                "Cursos actuales": ", ".join(otros_cursos),
                "Ciclo": reg['term'],
                "Nota": reg.get('final_grade', 0),
                "Asistencia": reg.get('attendance_rate', 0)
            })

        df_final = pd.DataFrame(data)

        # 7. KPIs Rápidos del Grupo
        st.subheader(f"Resumen del Grupo: {lista_cursos[curso_seleccionado]}")
        k1, k2, k3 = st.columns(3)
        k1.metric("Estudiantes en Clase", len(df_final))
        k2.metric("Promedio Grupal", f"{df_final['Nota'].mean():.2f}")
        k3.metric("Asistencia Promedio", f"{df_final['Asistencia'].mean()*100:.1f}%")

        st.divider()

        # 8. Dataframe Principal
        st.subheader("Lista de Estudiantes")
        st.dataframe(df_final, use_container_width=True, hide_index=True)

        st.divider()

        # 9. Diagramas de Utilidad (Plotly)
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("Estado Académico del Grupo")
            # Clasificación de aprobados vs reprobados (basado en nota 11)
            df_final['Estado'] = df_final['Nota'].apply(lambda x: 'Aprobado' if x >= 11 else 'Reprobado')
            fig_pie = px.pie(
                df_final, 
                names='Estado', 
                title='Distribución de Aprobación',
                color='Estado',
                color_discrete_map={'Aprobado':'#2ecc71', 'Reprobado':'#e74c3c'},
                hole=0.3
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_g2:
            st.subheader("Relación Nota vs. Carga Académica")
            # Ver si llevar muchos cursos afecta la nota en este curso
            df_final['Cantidad Cursos'] = df_final['Cursos actuales'].apply(lambda x: len(x.split(", ")))
            fig_scatter = px.scatter(
                df_final, 
                x="Cantidad Cursos", 
                y="Nota", 
                size="Nota", 
                hover_name="Nombres",
                title="¿Afecta la carga académica al rendimiento?",
                labels={"Cantidad Cursos": "Número de Cursos Matriculados", "Nota": "Nota Final"}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
