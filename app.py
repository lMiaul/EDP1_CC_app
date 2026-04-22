import streamlit as st

# 1. Configuración de la página (Solo se define aquí)
st.set_page_config(
    page_title="Portal de Transformación Digital | Universidad Horizonte",
    page_icon="🎓",
    layout="wide"
)

# Estilos básicos para mejorar la presentación
st.markdown("""
    <style>
    .main-title { font-size: 45px; font-weight: bold; color: #2E4053; }
    .subtitle { font-size: 20px; color: #5D6D7E; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Encabezado institucional
st.markdown('<p class="main-title">UNIVERSIDAD HORIZONTE</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Estrategia de Transformación Digital - Horizonte 2029</p>', unsafe_allow_html=True)

st.divider()

# 3. Visión del Proyecto
col_vision, col_img = st.columns([2, 1])

with col_vision:
    st.header("Nuestra Visión")
    st.info("""
    Evolucionar hacia un modelo educativo donde la tecnología facilite el aprendizaje 
    y elimine las barreras administrativas, garantizando una experiencia fluida tanto 
    para el estudiante como para el docente.
    """)

# 4. Los Pilares Estratégicos (Basado en tu documento)
st.header("Los 3 Pilares del Cambio")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🎯 Estudiante en el Centro")
    st.write("Simplificar trámites (pagos y matrículas) para que sean tan fáciles como usar una app bancaria.")

with col2:
    st.subheader("💡 Aprendizaje Inteligente")
    st.write("Usar datos para detectar a tiempo quién está en riesgo de abandonar y ofrecer apoyo personalizado.")

with col3:
    st.subheader("👨‍🏫 Docente Digital")
    st.write("Capacitar al profesorado para crear clases que motiven y enganchen a los estudiantes.")

st.divider()

# 5. Instrucciones de Navegación
st.subheader("¿Cómo utilizar esta plataforma?")
st.markdown("""
Utiliza el menú lateral para explorar las distintas dimensiones del proyecto:
* **Global:** Indicadores macro de la institución.
* **Estudiante:** Gestión individual, historial de pagos e interacciones.
* **Curso:** Análisis de rendimiento por asignatura.
* **Predictor:** Herramienta de IA para la prevención de deserción.
""")
