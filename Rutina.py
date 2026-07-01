import streamlit as st
import sqlite3
import pandas as pd
import datetime

# 1. CONFIGURACIÓN DE LA APP
st.set_page_config(page_title="Mi Progreso -9kg", page_icon="💪", layout="centered")

conn = sqlite3.connect('progreso_gimnasio.db', check_same_thread=False)
c = conn.cursor()

# 2. CREACIÓN DE TABLAS (Se añade la tabla de ejercicios dinámicos)
c.execute('''CREATE TABLE IF NOT EXISTS cargas 
             (fecha TEXT, dia TEXT, ejercicio TEXT, variante TEXT, peso REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS peso_corporal 
             (fecha TEXT, peso REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS ejercicios_rutina 
             (dia TEXT, ejercicio TEXT)''')
conn.commit()

# 3. POBLAR LA BASE DE DATOS LA PRIMERA VEZ (Si está vacía)
c.execute("SELECT COUNT(*) FROM ejercicios_rutina")
if c.fetchone()[0] == 0:
    rutina_inicial = [
        ("Lunes (Fuerza A)", "1. Sentadilla"), ("Lunes (Fuerza A)", "2. Press de Pecho"),
        ("Lunes (Fuerza A)", "3. Jalón Espalda"), ("Lunes (Fuerza A)", "4. Elevación Hombro"), ("Lunes (Fuerza A)", "5. Core / Abdomen"),
        ("Martes (Fuerza B)", "1. Peso Muerto"), ("Martes (Fuerza B)", "2. Remo Horizontal"),
        ("Martes (Fuerza B)", "3. Press Hombro"), ("Martes (Fuerza B)", "4. Extensión Pierna"), ("Martes (Fuerza B)", "5. Lumbar / Core"),
        ("Jueves (Fuerza A)", "1. Sentadilla"), ("Jueves (Fuerza A)", "2. Press de Pecho"),
        ("Jueves (Fuerza A)", "3. Jalón Espalda"), ("Jueves (Fuerza A)", "4. Elevación Hombro"), ("Jueves (Fuerza A)", "5. Core / Abdomen"),
        ("Viernes (Fuerza B)", "1. Peso Muerto"), ("Viernes (Fuerza B)", "2. Remo Horizontal"),
        ("Viernes (Fuerza B)", "3. Press Hombro"), ("Viernes (Fuerza B)", "4. Extensión Pierna"), ("Viernes (Fuerza B)", "5. Lumbar / Core")
    ]
    c.executemany("INSERT INTO ejercicios_rutina VALUES (?, ?)", rutina_inicial)
    conn.commit()

DÍAS_OPCIONES = ["Lunes (Fuerza A)", "Martes (Fuerza B)", "Jueves (Fuerza A)", "Viernes (Fuerza B)"]

st.title("💪 Control de Entrenamiento")

# Añadimos la 4ª pestaña: ⚙️ Gestionar Rutina
tab1, tab2, tab3, tab4 = st.tabs(["🏋️‍♂️ Registrar Cargas", "⚖️ Peso Corporal", "📈 Progreso", "⚙️ Gestionar Rutina"])

# --- PESTAÑA 1: REGISTRAR CARGAS (Dinámica) ---
with tab1:
    st.subheader("Registrar Pesos de Hoy")
    hoy = datetime.date.today().strftime("%Y-%m-%d")
    dia_seleccionado = st.selectbox("Selecciona el Día", DÍAS_OPCIONES)
    
    # Leer ejercicios desde la Base de Datos
    c.execute("SELECT ejercicio FROM ejercicios_rutina WHERE dia = ?", (dia_seleccionado,))
    ejercicios_actuales = [row[0] for row in c.fetchall()]
    
    if ejercicios_actuales:
        with st.form("form_cargas"):
            datos_ejercicios = []
            for ej in ejercicios_actuales:
                st.write(f"**{ej}**")
                col1, col2 = st.columns(2)
                with col1:
                    variante = col2.text_input("Variante (ej: Mancuerna)", key=f"var_{ej}", value="Máquina")
                with col2:
                    peso = col1.number_input("Peso (kg)", min_value=0.0, step=0.5, key=f"peso_{ej}")
                datos_ejercicios.append((hoy, dia_seleccionado, ej, variante, peso))
                st.markdown("---")
                
            if st.form_submit_button("💾 Guardar Entrenamiento"):
                for fila in datos_ejercicios:
                    c.execute("INSERT INTO cargas VALUES (?, ?, ?, ?, ?)", fila)
                conn.commit()
                st.success("¡Pesos guardados!")
    else:
        st.warning("No hay ejercicios guardados para este día. Añade alguno en la pestaña de Gestión.")

# --- PESTAÑA 2: PESO CORPORAL ---
with tab2:
    st.subheader("Control de Peso Semanal")
    with st.form("form_peso"):
        fecha_peso = st.date_input("Fecha", datetime.date.today()).strftime("%Y-%m-%d")
        peso_actual = st.number_input("Peso actual (kg)", min_value=30.0, step=0.1)
        if st.form_submit_button("💾 Registrar Peso"):
            c.execute("INSERT INTO peso_corporal VALUES (?, ?)", (fecha_peso, peso_actual))
            conn.commit()
            st.success(f"¡{peso_actual} kg registrado!")

# --- PESTAÑA 3: ESTADÍSTICAS ---
with tab3:
    st.subheader("Tu Evolución")
    df_peso = pd.read_sql_query("SELECT fecha, peso FROM peso_corporal ORDER BY fecha ASC", conn)
    if not df_peso.empty:
        df_peso['fecha'] = pd.to_datetime(df_peso['fecha'])
        st.line_chart(df_peso.set_index('fecha'))
    
    st.markdown("---")
    df_cargas = pd.read_sql_query("SELECT fecha, ejercicio, peso FROM cargas ORDER BY fecha ASC", conn)
    if not df_cargas.empty:
        ejercicios_disponibles = df_cargas['ejercicio'].unique()
        ej_filtro = st.selectbox("Evolución de fuerza en:", ejercicios_disponibles)
        df_filtrado = df_cargas[df_cargas['ejercicio'] == ej_filtro]
        df_filtrado['fecha'] = pd.to_datetime(df_filtrado['fecha'])
        st.line_chart(df_filtrado.set_index('fecha')['peso'])

# --- PESTAÑA 4: GESTIONAR RUTINA (¡Tu nueva herramienta!) ---
with tab4:
    st.subheader("⚙️ Configuración de Ejercicios")
    dia_gestion = st.selectbox("Día a modificar", DÍAS_OPCIONES, key="gestion_dia")
    
    # Mostrar ejercicios actuales con opción de borrar
    c.execute("SELECT ejercicio FROM ejercicios_rutina WHERE dia = ?", (dia_gestion,))
    ejercicios_visibles = [row[0] for row in c.fetchall()]
    
    st.markdown("### Ejercicios actuales:")
    for ej in ejercicios_visibles:
        col_ej, col_btn = st.columns([4, 1])
        col_ej.write(f"• {ej}")
        if col_btn.button("🗑️", key=f"del_{dia_gestion}_{ej}"):
            c.execute("DELETE FROM ejercicios_rutina WHERE dia = ? AND ejercicio = ?", (dia_gestion, ej))
            conn.commit()
            st.rerun()
            
    st.markdown("---")
    st.markdown("### ➕ Añadir Nuevo Ejercicio")
    nuevo_ejercicio = st.text_input("Nombre del ejercicio (ej: 6. Curl de Bíceps)")
    if st.button("Agregar a la lista"):
        if nuevo_ejercicio:
            c.execute("INSERT INTO ejercicios_rutina VALUES (?, ?)", (dia_gestion, nuevo_ejercicio))
            conn.commit()
            st.success(f"Añadido: {nuevo_ejercicio}")
            st.rerun()