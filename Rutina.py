import streamlit as st
import sqlite3
import pandas as pd
import datetime

# 1. CONFIGURACIÓN DE LA APP (Optimizada para móviles)
st.set_page_config(page_title="Mi Progreso -9kg", page_icon="💪", layout="centered")

# 2. CONEXIÓN A LA BASE DE DATOS LOCAL
conn = sqlite3.connect('progreso_gimnasio.db', check_same_thread=False)
c = conn.cursor()

# Crear tablas si no existen
c.execute('''CREATE TABLE IF NOT EXISTS cargas 
             (fecha TEXT, dia TEXT, ejercicio TEXT, variante TEXT, peso REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS peso_corporal 
             (fecha TEXT, peso REAL)''')
conn.commit()

# 3. DICCIONARIO DE RUTINAS
RUTINAS = {
    "Lunes (Fuerza A)": ["1. Sentadilla", "2. Press de Pecho", "3. Jalón Espalda", "4. Elevación Hombro", "5. Core / Abdomen"],
    "Martes (Fuerza B)": ["1. Peso Muerto", "2. Remo Horizontal", "3. Press Hombro", "4. Extensión Pierna", "5. Lumbar / Core"],
    "Jueves (Fuerza A)": ["1. Sentadilla", "2. Press de Pecho", "3. Jalón Espalda", "4. Elevación Hombro", "5. Core / Abdomen"],
    "Viernes (Fuerza B)": ["1. Peso Muerto", "2. Remo Horizontal", "3. Press Hombro", "4. Extensión Pierna", "5. Lumbar / Core"]
}

# 4. INTERFAZ DE LA APLICACIÓN
st.title("💪 Control de Entrenamiento")
st.write("Objetivo: Recomposición Corporal & Pérdida de 9 kg")

# Pestañas de navegación para el móvil
tab1, tab2, tab3 = st.tabs(["🏋️‍♂️ Registrar Cargas", "⚖️ Peso Corporal", "📈 Progreso"])

# --- PESTAÑA 1: REGISTRAR CARGAS ---
with tab1:
    st.subheader("Registrar Pesos de Hoy")
    
    hoy = datetime.date.today().strftime("%Y-%m-%d")
    dia_seleccionado = st.selectbox("Selecciona el Día", list(RUTINAS.keys()))
    
    st.markdown(f"**Ejercicios para hoy:**")
    
    # Formulario para guardar todos los pesos del día
    with st.form("form_cargas"):
        datos_ejercicios = []
        for ej in RUTINAS[dia_seleccionado]:
            st.write(f"**{ej}**")
            col1, col2 = st.columns(2)
            with col1:
                variante = col2.text_input("Variante (ej: Mancuerna / Máquina)", key=f"var_{ej}", value="Máquina")
            with col2:
                peso = col1.number_input("Peso levantado (kg)", min_value=0.0, step=0.5, key=f"peso_{ej}")
            datos_ejercicios.append((hoy, dia_seleccionado, ej, variante, peso))
            st.markdown("---")
            
        guardar_entrenamiento = st.form_submit_button("💾 Guardar Entrenamiento")
        
        if guardar_entrenamiento:
            for fila in datos_ejercicios:
                c.execute("INSERT INTO cargas VALUES (?, ?, ?, ?, ?)", fila)
            conn.commit()
            st.success("¡Pesos del día guardados correctamente!")

# --- PESTAÑA 2: PESO CORPORAL ---
with tab2:
    st.subheader("Control de Peso Semanal")
    
    with st.form("form_peso"):
        fecha_peso = st.date_input("Fecha del pesaje", datetime.date.today()).strftime("%Y-%m-%d")
        peso_actual = st.number_input("Tu peso actual (kg)", min_value=30.0, max_value=200.0, step=0.1)
        
        guardar_peso = st.form_submit_button("💾 Registrar Peso")
        
        if guardar_peso:
            c.execute("INSERT INTO peso_corporal VALUES (?, ?)", (fecha_peso, peso_actual))
            conn.commit()
            st.success(f"¡Peso de {peso_actual} kg registrado!")

# --- PESTAÑA 3: ESTADÍSTICAS Y PROGRESO ---
with tab3:
    st.subheader("Tu Evolución en el Tiempo")
    
    # Gráfico 1: Evolución del Peso Corporal
    st.markdown("### ⚖️ Pérdida de Peso")
    df_peso = pd.read_sql_query("SELECT fecha, peso FROM peso_corporal ORDER BY fecha ASC", conn)
    
    if not df_peso.empty:
        df_peso['fecha'] = pd.to_datetime(df_peso['fecha'])
        st.line_chart(df_peso.set_index('fecha'))
        
        # Calcular cuánto se ha perdido
        peso_inicial = df_peso['peso'].iloc[0]
        peso_ultimo = df_peso['peso'].iloc[-1]
        perdida_total = peso_inicial - peso_ultimo
        st.metric(label="Total de peso perdido", value=f"{perdida_total:.1f} kg", delta=f"-{9.0 - perdida_total:.1f} kg para la meta", delta_color="inverse")
    else:
        st.info("Registra tu peso en la pestaña anterior para empezar a ver las gráficas.")
        
    st.markdown("---")
    
    # Gráfico 2: Evolución de las Cargas por Ejercicio
    st.markdown("### 🏋️‍♂️ Fuerza en Ejercicios")
    
    # Obtener lista de todos los ejercicios únicos registrados
    df_cargas = pd.read_sql_query("SELECT fecha, ejercicio, peso FROM cargas ORDER BY fecha ASC", conn)
    
    if not df_cargas.empty:
        ejercicios_disponibles = df_cargas['ejercicio'].unique()
        ej_filtro = st.selectbox("Selecciona un ejercicio para ver tu progreso", ejercicios_disponibles)
        
        df_filtrado = df_cargas[df_cargas['ejercicio'] == ej_filtro]
        df_filtrado['fecha'] = pd.to_datetime(df_filtrado['fecha'])
        
        st.line_chart(df_filtrado.set_index('fecha')['peso'])
    else:
        st.info("Cuando guardes tus entrenamientos diarios, aquí verás cómo subes de fuerza.")