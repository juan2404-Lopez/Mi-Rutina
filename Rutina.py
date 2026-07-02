import streamlit as st
import sqlite3
import pandas as pd
import datetime

# 1. CONFIGURACIÓN DE LA APP (Optimizada para visualización móvil)
st.set_page_config(page_title="Mi Progreso -9kg", page_icon="💪", layout="centered")

# Conexión a la base de datos local del servidor
conn = sqlite3.connect('progreso_gimnasio.db', check_same_thread=False)
c = conn.cursor()

# 2. CREACIÓN DE TABLAS
c.execute('''CREATE TABLE IF NOT EXISTS cargas 
             (fecha TEXT, dia TEXT, ejercicio TEXT, variante TEXT, peso REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS peso_corporal 
             (fecha TEXT, peso REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS ejercicios_rutina 
             (dia TEXT, ejercicio TEXT)''')
conn.commit()

# Limpieza de nombres de días antiguos si existieran (Migración defensiva)
c.execute("SELECT COUNT(*) FROM ejercicios_rutina WHERE dia LIKE '%Fuerza%'")
if c.fetchone()[0] > 0:
    c.execute("DELETE FROM ejercicios_rutina")
    conn.commit()

# 3. POBLAR LA BASE DE DATOS CON LOS 7 DÍAS LIMPIOS (Si está vacía)
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

# Todos los días de la semana disponibles para el futuro
TODOS_LOS_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

st.title("💪 Control de Entrenamiento")
st.write("Objetivo: Recomposición Corporal & Pérdida de 9 kg")

# Pestañas de navegación
tab1, tab2, tab3, tab4 = st.tabs(["🏋️‍♂️ Cargas", "⚖️ Peso Corporal", "📈 Progreso", "⚙️ Gestionar Rutina"])

# --- PESTAÑA 1: REGISTRAR / MODIFICAR CARGAS ---
with tab1:
    st.subheader("Registrar Pesos")
    
    # Selección de fecha con formato dd/mm/aaaa nativo
    fecha_entreno = st.date_input("Fecha del entrenamiento", datetime.date.today(), format="DD/MM/YYYY")
    fecha_str = fecha_entreno.strftime("%Y-%m-%d")
    
    dia_seleccionado = st.selectbox("Selecciona el Día de la Semana", TODOS_LOS_DIAS)
    
    # Leer ejercicios dinámicamente desde la BD para ese día
    c.execute("SELECT ejercicio FROM ejercicios_rutina WHERE dia = ?", (dia_seleccionado,))
    ejercicios_actuales = [row[0] for row in c.fetchall()]
    
    if ejercicios_actuales:
        st.markdown(f"**Ejercicios programados:**")
        
        with st.form("form_cargas"):
            datos_ejercicios = []
            for ej in ejercicios_actuales:
                st.write(f"**{ej}**")
                col_var, col_peso = st.columns(2)
                
                with col_var:
                    # Menú desplegable para la variante del ejercicio
                    variante = st.selectbox("Variante", ["Máquina", "Mancuerna", "Polea"], key=f"var_{ej}_{dia_seleccionado}")
                with col_peso:
                    peso = st.number_input("Peso levantado (kg)", min_value=0.0, step=0.5, key=f"peso_{ej}_{dia_seleccionado}")
                
                datos_ejercicios.append((fecha_str, dia_seleccionado, ej, variante, peso))
                st.markdown("---")
            
            if st.form_submit_button("💾 Guardar / Modificar Registro"):
                # Borramos registros previos de este mismo día y fecha si vas a modificarlos
                c.execute("DELETE FROM cargas WHERE fecha = ? AND dia = ?", (fecha_str, dia_seleccionado))
                
                # Insertamos los nuevos datos
                c.executemany("INSERT INTO cargas VALUES (?, ?, ?, ?, ?)", datos_ejercicios)
                conn.commit()
                st.success(f"¡Datos guardados correctamente para la fecha {fecha_entreno.strftime('%d/%m/%Y')}!")
    else:
        st.info(f"No tienes ejercicios asignados para el {dia_seleccionado}. Puedes añadirlos en la pestaña 'Gestionar Rutina'.")

# --- PESTAÑA 2: PESO CORPORAL ---
with tab2:
    st.subheader("Control de Peso Semanal")
    
    with st.form("form_peso"):
        # Selección de fecha con formato dd/mm/aaaa nativo
        fecha_peso = st.date_input("Fecha del pesaje", datetime.date.today(), format="DD/MM/YYYY")
        fecha_p_str = fecha_peso.strftime("%Y-%m-%d")
        
        peso_actual = st.number_input("Tu peso actual (kg)", min_value=30.0, max_value=200.0, step=0.1)
        
        if st.form_submit_button("💾 Registrar Peso"):
            # Evitar duplicados eliminando si ya existe registro en esa fecha exacta
            c.execute("DELETE FROM peso_corporal WHERE fecha = ?", (fecha_p_str,))
            
            c.execute("INSERT INTO peso_corporal VALUES (?, ?)", (fecha_p_str, peso_actual))
            conn.commit()
            st.success(f"¡Peso de {peso_actual} kg registrado para el día {fecha_peso.strftime('%d/%m/%Y')}!")

# --- PESTAÑA 3: ESTADÍSTICAS Y PROGRESO ---
with tab3:
    st.subheader("Tu Evolución")
    
    st.markdown("### ⚖️ Historial de Peso Corporal")
    df_peso = pd.read_sql_query("SELECT fecha, peso FROM peso_corporal ORDER BY fecha ASC", conn)
    
    if not df_peso.empty:
        df_peso['fecha_dt'] = pd.to_datetime(df_peso['fecha'])
        # Formateamos la fecha para que se lea dd/mm/aaaa en las tablas informativas
        df_peso['Fecha'] = df_peso['fecha_dt'].dt.strftime('%d/%m/%Y')
        
        st.line_chart(df_peso.set_index('fecha_dt')['peso'])
        st.dataframe(df_peso[['Fecha', 'peso']].rename(columns={'peso': 'Peso (kg)'}), use_container_width=True, hide_index=True)
    else:
        st.info("Registra tus pesajes para ver las gráficas de evolución.")
        
    st.markdown("---")
    st.markdown("### 🏋️‍♂️ Progreso de Fuerza")
    
    df_cargas = pd.read_sql_query("SELECT fecha, ejercicio, peso FROM cargas ORDER BY fecha ASC", conn)
    if not df_cargas.empty:
        ejercicios_disponibles = df_cargas['ejercicio'].unique()
        ej_filtro = st.selectbox("Selecciona un ejercicio para auditar tu fuerza", ejercicios_disponibles)
        
        df_filtrado = df_cargas[df_cargas['ejercicio'] == ej_filtro].copy()
        df_filtrado['fecha_dt'] = pd.to_datetime(df_filtrado['fecha'])
        df_filtrado['Fecha'] = df_filtrado['fecha_dt'].dt.strftime('%d/%m/%Y')
        
        st.line_chart(df_filtrado.set_index('fecha_dt')['peso'])
        st.dataframe(df_filtrado[['Fecha', 'peso']].rename(columns={'peso': 'Carga (kg)'}), use_container_width=True, hide_index=True)
    else:
        st.info("Guarda entrenamientos en la primera pestaña para generar métricas de fuerza.")

# --- PESTAÑA 4: GESTIONAR RUTINA (Completa con los 7 días) ---
with tab4:
    st.subheader("⚙️ Configuración y Edición de la Rutina")
    dia_gestion = st.selectbox("Selecciona el día que quieres editar/configurar", TODOS_LOS_DIAS, key="gestion_dia")
    
    c.execute("SELECT ejercicio FROM ejercicios_rutina WHERE dia = ?", (dia_gestion,))
    ejercicios_visibles = [row[0] for row in c.fetchall()]
    
    st.markdown(f"#### Ejercicios del {dia_gestion}:")
    if ejercicios_visibles:
        for ej in ejercicios_visibles:
            col_ej, col_btn = st.columns([5, 1])
            col_ej.write(f"• {ej}")
            # Botón rápido para eliminar un ejercicio si cambia tu rutina
            if col_btn.button("🗑️", key=f"del_{dia_gestion}_{ej}"):
                c.execute("DELETE FROM ejercicios_rutina WHERE dia = ? AND ejercicio = ?", (dia_gestion, ej))
                conn.commit()
                st.rerun()
    else:
        st.caption("Día de descanso o sin ejercicios programados actualmente.")
            
    st.markdown("---")
    st.markdown("### ➕ Añadir o Modificar Ejercicios")
    nuevo_ejercicio = st.text_input("Escribe el nombre del ejercicio (ej: 6. Curl de Bíceps)")
    
    if st.button("Añadir a la lista de este día"):
        if nuevo_ejercicio:
            c.execute("INSERT INTO ejercicios_rutina VALUES (?, ?)", (dia_gestion, nuevo_ejercicio))
            conn.commit()
            st.success(f"¡{nuevo_ejercicio} añadido al {dia_gestion}!")
            st.rerun()