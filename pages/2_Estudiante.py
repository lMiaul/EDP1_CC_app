import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import datetime

# 1. Configuración de la página
st.set_page_config(page_title="Perfil del Estudiante", page_icon="👤", layout="wide")

# 2. Conexión a MongoDB (Usando Secretos)
@st.cache_resource
def iniciar_conexion():
    # Streamlit leerá automáticamente el secreto del archivo de configuración
    uri = st.secrets["mongo"]["uri"]
    return MongoClient(uri)

client = iniciar_conexion()
db = client["universidad_horizonte"]

# 3. Interfaz de Búsqueda
st.title("👤 Perfil 360° del Estudiante")
st.markdown("Consulta el historial académico, financiero y de interacciones digitales.")

st.divider()

# Columna para el buscador
col_buscar, _ = st.columns([1, 2])
with col_buscar:
    # Usamos un valor por defecto para agilizar las pruebas
    student_id_input = st.text_input("Ingrese el ID del Estudiante (Ej. U20231499)", value="U20231499").strip()

if student_id_input:
    # 4. Consultas a la Base de Datos
    student_data = db.students.find_one({"student_id": student_id_input})
    
    if not student_data:
        st.warning(f"No se encontró ningún estudiante con el ID: {student_id_input}")
    else:
        # Extraer resto de datos si el estudiante existe
        enrollments = list(db.enrollments.find({"student_id": student_id_input}))
        payments = list(db.payments.find({"student_id": student_id_input}))
        interactions = list(db.interactions.find({"student_id": student_id_input}))
        dropout_flag = db.dropout_flags.find_one({"student_id": student_id_input})

        # 5. Sección: Encabezado del Perfil y KPIs (Cards)
        st.header(f"Estudiante: {student_data.get('first_name', '')} {student_data.get('last_name', '')}")
        st.caption(f"Programa: {student_data.get('program', 'N/A')} | Estado: {student_data.get('status', 'N/A').upper()}")
        
        # Alerta de Riesgo (Conecta con tu tabla de predicción)
        if dropout_flag and dropout_flag.get("dropout") == True:
            st.error(f"⚠️ ESTUDIANTE EN RIESGO DE DESERCIÓN. Motivo principal: {dropout_flag.get('reason', 'Desconocido').capitalize()}")
        else:
            st.success("✅ Estudiante sin riesgo de deserción detectado.")

        st.markdown("### Indicadores Clave")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        # Cálculo de KPIs básicos
        total_cursos = len(enrollments)
        promedio_notas = sum([e.get('final_grade', 0) for e in enrollments]) / total_cursos if total_cursos > 0 else 0
        asistencia_promedio = sum([e.get('attendance_rate', 0) for e in enrollments]) / total_cursos if total_cursos > 0 else 0
        pagos_pendientes = len([p for p in payments if p.get('status') != 'pagado'])

        kpi1.metric(label="Cursos Matriculados", value=total_cursos)
        kpi2.metric(label="Promedio Acumulado", value=f"{promedio_notas:.1f} / 20")
        kpi3.metric(label="Asistencia Global", value=f"{asistencia_promedio * 100:.1f}%")
        kpi4.metric(label="Pagos Pendientes", value=pagos_pendientes, delta="-Morosidad" if pagos_pendientes == 0 else "Alerta", delta_color="inverse")

        st.divider()

        # 6. Sección: Gráficos Interactivos con Plotly
        col_graf_1, col_graf_2 = st.columns(2)

        with col_graf_1:
            st.subheader("Rendimiento por Curso")
            if enrollments:
                df_enroll = pd.DataFrame(enrollments)
                # Gráfico de barras para las notas
                fig_notas = px.bar(
                    df_enroll, 
                    x='course_id', 
                    y='final_grade', 
                    color='final_grade',
                    color_continuous_scale='Blues',
                    labels={'course_id': 'Código de Curso', 'final_grade': 'Nota Final'},
                    title="Calificaciones Finales"
                )
                fig_notas.add_hline(y=11, line_dash="dot", annotation_text="Nota Mínima Aprobatoria", line_color="red")
                fig_notas.update_layout(yaxis_range=[0, 20])
                st.plotly_chart(fig_notas, use_container_width=True)
            else:
                st.info("No hay historial académico para mostrar.")

        with col_graf_2:
            st.subheader("Interacciones Digitales (LMS)")
            if interactions:
                df_inter = pd.DataFrame(interactions)
                # Contar acciones por plataforma/acción
                resumen_interacciones = df_inter['action'].value_counts().reset_index()
                resumen_interacciones.columns = ['action', 'count']
                
                # Gráfico de dona para ver qué hace el alumno en la plataforma
                fig_inter = px.pie(
                    resumen_interacciones, 
                    names='action', 
                    values='count', 
                    hole=0.4,
                    title="Distribución de Actividad en Plataforma",
                    color_discrete_sequence=px.colors.sequential.Teal
                )
                fig_inter.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_inter, use_container_width=True)
            else:
                st.info("No hay registro de interacciones en el campus virtual.")

        # 7. Sección: Historial de Pagos (Tabla)
        st.subheader("Historial Financiero")
        if payments:
            df_pagos = pd.DataFrame(payments)
            # Limpiamos las columnas para mostrar en Streamlit
            df_pagos = df_pagos[['term', 'payment_date', 'amount', 'status']]
            df_pagos.rename(columns={'term': 'Ciclo', 'payment_date': 'Fecha', 'amount': 'Monto ($)', 'status': 'Estado'}, inplace=True)
            st.dataframe(df_pagos, use_container_width=True, hide_index=True)
        else:
            st.info("No hay registros de pagos para este estudiante.")
