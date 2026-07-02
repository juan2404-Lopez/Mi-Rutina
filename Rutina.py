import streamlit as st
import sqlite3
import pandas as pd
import datetime

# 1. CONFIGURACIÓN DE LA APP
st.set_page_config(page_title="Mi Progreso -9kg", page_icon="💪", layout="centered")

conn = sqlite3.connect('progreso_gimnasio.db', check_same_thread=False)
c = conn.cursor()

# 2. CREACIÓN DE TABLAS ACTUALIZADAS
c.execute('''CREATE TABLE IF NOT EXISTS cargas 
             (fecha TEXT, dia TEXT, ejercicio TEXT, variante TEXT, peso REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS peso_corporal 
             (fecha TEXT, peso REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS ejercicios_rutina 
             (dia TEXT, ejercicio TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS cardio 
             (fecha TEXT, tipo TEXT, tiempo INTEGER, Kcal INTEGER)''')
conn.commit()

# MIGRACIÓN AUTOMÁTICA: Añadir columna 'reps' a la tabla cargas si no existe
try:
    c.execute("ALTER TABLE cargas ADD COLUMN reps INTEGER DEFAULT 10")
    conn.commit()
except sqlite3.OperationalError:
    pass  # La columna ya existe

# 3. POBLAR EJERCICIOS INICIALES (Si la BD está vacía)
c.execute("SELECT COUNT(*) FROM ejercicios_rutina")
if c.fetchone()[0] == 0:
    rutina_inicial = [
        ("Lunes", "1. Sentadilla"), ("Lunes", "2. Press de Pecho"),
        ("Lunes", "3. Jalón Espalda"), ("Lunes", "4. Elevación Hombro"), ("Lunes", "5. Core / Abdomen"),
        ("Martes", "1. Peso Muerto"), ("Martes", "2. Remo Horizontal"),
        ("Martes", "3. Press Hombro"), ("Martes", "4. Extensión Pierna"), ("Martes", "5. Lumbar / Core"),
        ("Jueves", "1. Sentadilla"), ("Jueves", "2. Press de Pecho"),
        ("Jueves", "3. Jalón Espalda"), ("Jueves", "4. Elevación Hombro"), ("Jueves", "5. Core / Abdomen"),
        ("Viernes", "1. Peso Muerto"), ("Viernes", "2. Remo Horizontal"),
        ("Viernes", "3. Press Hombro"), ("Viernes", "4. Extensión Pierna"), ("Viernes", "5. Lumbar / Core")
    ]
    c.executemany("INSERT INTO ejercicios_rutina VALUES (?, ?)", rutina_inicial)
    conn.commit()

TODOS_LOS_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

st.title("💪 Control de Entrenamiento")
st.write("Objetivo: Recomposición Corporal & Pérdida de 9 kg")

# Ahora manejamos 5 pestañas organizadas
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏋️‍♂️ Cargas", "🏃‍♂️ Cardio Tarde", "⚖️ Peso", "📈 Progreso", "⚙️ Gestión"])

# --- PESTAÑA 1: REGISTRAR CARGAS (Con memoria de última sesión) ---
with tab1:
    st.subheader("Fuerza por la Mañana")
    fecha_entreno = st.date_input("Fecha del entrenamiento", datetime.date.today(), format="DD/MM/YYYY")
    fecha_str = fecha_entreno.strftime("%Y-%m-%d")
    dia_seleccionado = st.selectbox("Selecciona el Día", TODOS_LOS_DIAS)
    
    c.execute("SELECT ejercicio FROM ejercicios_rutina WHERE dia = ?", (dia_seleccionado,))
    ejercicios_actuales = [row[0] for row in c.fetchall()]
    
    if ejercicios_actuales:
        with st.form("form_cargas"):
            datos_ejercicios = []
            for ej in ejercicios_actuales:
                st.markdown(f"#### {ej}")
                
                # FUNCIÓN MEMORIA: Buscar el último peso registrado para este ejercicio
                c.execute("SELECT peso, reps, variante FROM cargas WHERE ejercicio = ? ORDER BY fecha DESC LIMIT 1", (ej,))
                ultimo_registro = c.fetchone()
                if ultimo_registro:
                    st.caption(f"🔄 **Última sesión:** {ultimo_registro[0]} kg x {ultimo_registro[1]} reps ({ultimo_registro[2]})")
                else:
                    st.caption("🆕 Sin registros previos para este ejercicio.")
                
                col_var, col_peso, col_reps = st.columns(3)
                with col_var:
                    variante = st.selectbox("Variante", ["Máquina", "Mancuerna", "Polea"], key=f"var_{ej}_{dia_seleccionado}")
                with col_peso:
                    peso = st.number_input("Peso (kg)", min_value=0.0, step=0.5, key=f"peso_{ej}_{dia_seleccionado}")
                with col_reps:
                    reps = st.number_input("Reps", min_value=1, max_value=100, value=10, step=1, key=f"reps_{ej}_{dia_seleccionado}")
                
                datos_ejercicios.append((fecha_str, dia_seleccionado, ej, variante, peso, reps))
                st.markdown("---")
            
            if st.form_submit_button("💾 Guardar / Modificar Fuerza"):
                c.execute("DELETE FROM cargas WHERE fecha = ? AND dia = ?", (fecha_str, dia_seleccionado))
                c.executemany("INSERT INTO cargas VALUES (?, ?, ?, ?, ?, ?)", datos_ejercicios)
                conn.commit()
                st.success(f"¡Sesión de fuerza guardada!")
    else:
        st.info(f"No hay ejercicios para el {dia_seleccionado}.")

# --- PESTAÑA 2: REGISTRAR CARDIO (¡Nueva!) ---
with tab2:
    st.subheader("Cardio por la Tarde")
    fecha_cardio = st.date_input("Fecha del bloque de cardio", datetime.date.today(), format="DD/MM/YYYY")
    fecha_c_str = fecha_cardio.strftime("%Y-%m-%d")
    
    with st.form("form_cardio"):
        tipo_cardio = st.selectbox("Tipo de Cardio", ["Cinta de correr", "Máquina de Remo", "Bicicleta Estática", "Bicicleta Elíptica", "Otro"])
        tiempo_min = st.number_input("Tiempo total (Minutos)", min_value=1, max_value=180, value=45, step=1)
        kcal_quemadas = st.number_input("Calorías estimadas por la máquina (Opcional)", min_value=0, value=0, step=5)
        
        if st.form_submit_button("💾 Registrar Cardio"):
            c.execute("DELETE FROM cardio WHERE fecha = ? AND tipo = ?", (fecha_c_str, tipo_cardio))
            c.execute("INSERT INTO cardio VALUES (?, ?, ?, ?)", (fecha_c_str, tipo_cardio, tiempo_min, kcal_quemadas))
            conn.commit()
            st.success(f"¡Cardio guardado correctamente!")

# --- PESTAÑA 3: PESO CORPORAL ---
with tab3:
    st.subheader("Peso Semanal")
    with st.form("form_peso"):
        fecha_peso = st.date_input("Fecha del pesaje", datetime.date.today(), format="DD/MM/YYYY")
        fecha_p_str = fecha_peso.strftime("%Y-%m-%d")
        peso_actual = st.number_input("Tu peso (kg)", min_value=30.0, step=0.1)
        
        if st.form_submit_button("💾 Registrar Peso"):
            c.execute("DELETE FROM peso_corporal WHERE fecha = ?", (fecha_p_str,))
            c.execute("INSERT INTO peso_corporal VALUES (?, ?)", (fecha_p_str, peso_actual))
            conn.commit()
            st.success(f"¡Peso guardado!")

# --- PESTAÑA 4: ESTADÍSTICAS Y PROGRESO ---
with tab4:
    st.subheader("Tu Evolución")
    
    # Progreso de Peso
    st.markdown("### ⚖️ Pérdida de Peso Corporal")
    df_peso = pd.read_sql_query("SELECT fecha, peso FROM peso_corporal ORDER BY fecha ASC", conn)
    if not df_peso.empty:
        df_peso['fecha_dt'] = pd.to_datetime(df_peso['fecha'])
        df_peso['Fecha'] = df_peso['fecha_dt'].dt.strftime('%d/%m/%Y')
        st.line_chart(df_peso.set_index('fecha_dt')['peso'])
        st.dataframe(df_peso[['Fecha', 'peso']].rename(columns={'peso': 'Peso (kg)'}), use_container_width=True, hide_index=True)
    
    # Progreso de Fuerza
    st.markdown("---")
    st.markdown("### 🏋️‍♂️ Progreso en Ejercicios")
    df_cargas = pd.read_sql_query("SELECT fecha, ejercicio, peso, reps, variante FROM cargas ORDER BY fecha ASC", conn)
    if not df_cargas.empty:
        ejercicios_disponibles = df_cargas['ejercicio'].unique()
        ej_filtro = st.selectbox("Selecciona Ejercicio", ejercicios_disponibles)
        df_filtrado = df_cargas[df_cargas['ejercicio'] == ej_filtro].copy()
        df_filtrado['fecha_dt'] = pd.to_datetime(df_filtrado['fecha'])
        df_filtrado['Fecha'] = df_filtrado['fecha_dt'].dt.strftime('%d/%m/%Y')
        st.line_chart(df_filtrado.set_index('fecha_dt')['peso'])
        st.dataframe(df_filtrado[['Fecha', 'peso', 'reps', 'variante']].rename(columns={'peso': 'Carga (kg)', 'reps': 'Reps', 'variante': 'Tipo'}), use_container_width=True, hide_index=True)

    # Historial de Cardio
    st.markdown("---")
    st.markdown("### 🏃‍♂️ Historial de Cardio Acumulado")
    df_cardio = pd.read_sql_query("SELECT fecha, tipo, tiempo, Kcal FROM cardio ORDER BY fecha DESC", conn)
    if not df_cardio.empty:
        df_cardio['fecha_dt'] = pd.to_datetime(df_cardio['fecha'])
        df_cardio['Fecha'] = df_cardio['fecha_dt'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_cardio[['Fecha', 'tipo', 'tiempo', 'Kcal']].rename(columns={'tipo': 'Actividad', 'tiempo': 'Duración (min)', 'Kcal': 'Calorías'}), use_container_width=True, hide_index=True)

# --- PESTAÑA 5: GESTIONAR RUTINA ---
with tab5:
    st.subheader("⚙️ Configuración de Ejercicios")
    dia_gestion = st.selectbox("Día a editar", TODOS_LOS_DIAS, key="gestion_dia")
    
    c.execute("SELECT ejercicio FROM ejercicios_rutina WHERE dia = ?", (dia_gestion,))
    ejercicios_visibles = [row[0] for row in c.fetchall()]
    
    st.markdown(f"#### Ejercicios del {dia_gestion}:")
    if ejercicios_visibles:
        for ej in ejercicios_visibles:
            col_ej, col_btn = st.columns([5, 1])
            col_ej.write(f"• {ej}")
            if col_btn.button("🗑️", key=f"del_{dia_gestion}_{ej}"):
                c.execute("DELETE FROM ejercicios_rutina WHERE dia = ? AND ejercicio = ?", (dia_gestion, ej))
                conn.commit()
                st.rerun()
            
    st.markdown("---")
    nuevo_ejercicio = st.text_input("Nombre del nuevo ejercicio")
    if st.button("Añadir a este día"):
        if nuevo_ejercicio:
            c.execute("INSERT INTO ejercicios_rutina VALUES (?, ?)", (dia_gestion, nuevo_ejercicio))
            conn.commit()
            st.success(f"¡Añadido!")
            st.rerun()