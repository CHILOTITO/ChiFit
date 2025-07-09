# app.py
import streamlit as st
import sqlite3
import datetime
import pandas as pd
import io
from fpdf import FPDF
import os

st.set_page_config(page_title="Chilotitos Fitness - Red Social", layout="wide")
st.title("💪 Chilotitos Fitness - Comunidad de Entrenamiento")

# Conexión a la base de datos SQLite
conn = sqlite3.connect("usuarios.db", check_same_thread=False)
cursor = conn.cursor()

# Crear tablas si no existen
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        contrasena TEXT NOT NULL
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS alumnos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        nombre TEXT,
        edad INTEGER,
        fecha_nacimiento TEXT,
        peso REAL,
        estatura REAL,
        enfermedad TEXT,
        dias_semana INTEGER,
        fecha TEXT,
        rutina TEXT,
        ejercicio TEXT,
        repeticiones INTEGER,
        series INTEGER,
        peso_utilizado REAL
    )
""")
conn.commit()

# Funciones de autenticación y usuarios
def autenticar(usuario, clave):
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND contrasena = ?", (usuario, clave))
    return cursor.fetchone() is not None

def crear_usuario(nuevo_usuario, nueva_clave):
    try:
        cursor.execute("INSERT INTO usuarios (usuario, contrasena) VALUES (?, ?)", (nuevo_usuario, nueva_clave))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Estado para formulario
if "mostrar_formulario" not in st.session_state:
    st.session_state.mostrar_formulario = False

# Inicio de sesión
if "usuario" not in st.session_state:
    st.sidebar.subheader("Iniciar Sesión")
    usuario = st.sidebar.text_input("Usuario")
    clave = st.sidebar.text_input("Contraseña", type="password")
    login = st.sidebar.button("Ingresar")

    if login:
        if autenticar(usuario, clave):
            st.session_state.usuario = usuario
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

    st.sidebar.markdown("¿No tienes cuenta?")
    if st.sidebar.button("Crear cuenta"):
        st.session_state.mostrar_formulario = True

    if st.session_state.mostrar_formulario:
        with st.form("form_crear_cuenta"):
            nuevo_usuario = st.text_input("Nuevo usuario")
            nueva_clave = st.text_input("Nueva contraseña", type="password")
            crear = st.form_submit_button("Crear cuenta")

            if crear:
                if crear_usuario(nuevo_usuario, nueva_clave):
                    st.success("✅ Cuenta creada con éxito. Ahora puedes iniciar sesión.")
                    st.session_state.mostrar_formulario = False
                else:
                    st.warning("⚠️ El usuario ya existe. Elige otro.")
else:
    if os.path.exists("assets/logo.png"):
        st.sidebar.image("assets/logo.png", width=200)

    menu = st.sidebar.radio("Navegación", [
        "Registrar Alumno", "Registrar Entrenamiento", "Dashboard",
        "Exportar a Excel", "Generar PDF Alumno", "Cerrar Sesión"
    ])

    usuario_activo = st.session_state.usuario

    if menu == "Cerrar Sesión":
        st.session_state.pop("usuario")
        st.experimental_rerun()

    elif menu == "Registrar Alumno":
        st.subheader("📋 Registro de Información Personal")
        with st.form("form_registro"):
            nombre = st.text_input("Nombre")
            edad = st.number_input("Edad", min_value=5, max_value=100)
            fecha_nac = st.date_input("Fecha de Nacimiento", min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today())
            peso = st.number_input("Peso corporal (kg)", min_value=0.0)
            estatura = st.number_input("Estatura (cm)", min_value=0.0)
            enfermedad = st.text_input("¿Tiene alguna enfermedad?")
            dias = st.selectbox("¿Cuántos días asistirá por semana?", [1, 2, 3, 4, 5, 6])
            enviar = st.form_submit_button("Guardar")

            if enviar:
                cursor.execute("""
                    INSERT INTO alumnos (usuario, nombre, edad, fecha_nacimiento, peso, estatura, enfermedad, dias_semana, fecha, rutina, ejercicio, repeticiones, series, peso_utilizado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', NULL, NULL, NULL)
                """, (usuario_activo, nombre, edad, fecha_nac.isoformat(), peso, estatura, enfermedad, dias, datetime.date.today().isoformat()))
                conn.commit()
                st.success("Alumno registrado con éxito ✅")

    elif menu == "Registrar Entrenamiento":
        st.subheader("🏃 Registro de Entrenamiento")
        cursor.execute("SELECT DISTINCT nombre FROM alumnos WHERE usuario = ?", (usuario_activo,))
        alumnos = [row[0] for row in cursor.fetchall()]
        alumno_sel = st.selectbox("Seleccionar Alumno", alumnos)

        if alumno_sel:
            rutina = st.text_input("Nombre de la Rutina")
            st.markdown("### Ejercicios del día")

            ejercicios = st.session_state.get("ejercicios_temp", [])

            with st.form("form_nuevo_ejercicio"):
                col1, col2 = st.columns(2)
                with col1:
                    nuevo_ejercicio = st.text_input("Ejercicio realizado", key="nuevo_ejercicio")
                    repes = st.number_input("Repeticiones", min_value=1, key="nuevo_repes")
                with col2:
                    series = st.number_input("Series", min_value=1, key="nuevo_series")
                    peso_util = st.number_input("Peso utilizado (kg)", min_value=0.0, key="nuevo_peso")

                add = st.form_submit_button("➕ Agregar ejercicio")

                if add:
                    if nuevo_ejercicio:
                        ejercicios.append({
                            "Ejercicio": nuevo_ejercicio,
                            "Repeticiones": repes,
                            "Series": series,
                            "Peso utilizado": peso_util
                        })
                        st.session_state.ejercicios_temp = ejercicios
                    else:
                        st.warning("Debes escribir un ejercicio")

            if ejercicios:
                st.write("#### Ejercicios agregados:")
                for i, ej in enumerate(ejercicios):
                    st.write(f"{i+1}. {ej['Ejercicio']} – {ej['Repeticiones']} reps, {ej['Series']} series, {ej['Peso utilizado']} kg")

                if st.button("✅ Guardar entrenamiento completo"):
                    cursor.execute("SELECT * FROM alumnos WHERE nombre = ? AND usuario = ? ORDER BY id DESC LIMIT 1", (alumno_sel, usuario_activo))
                    alumno = cursor.fetchone()
                    if alumno:
                        for ej in ejercicios:
                            cursor.execute("""
                                INSERT INTO alumnos (usuario, nombre, edad, fecha_nacimiento, peso, estatura, enfermedad, dias_semana, fecha, rutina, ejercicio, repeticiones, series, peso_utilizado)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                usuario_activo, alumno_sel, alumno[3], alumno[4], alumno[5], alumno[6], alumno[7],
                                alumno[8], datetime.date.today().isoformat(), rutina,
                                ej["Ejercicio"], ej["Repeticiones"], ej["Series"], ej["Peso utilizado"]
                            ))
                        conn.commit()
                        st.success("Entrenamiento completo guardado ✅")
                        st.session_state.ejercicios_temp = []

    elif menu == "Dashboard":
        st.subheader("📊 Dashboard por Alumno")
        cursor.execute("SELECT DISTINCT nombre FROM alumnos WHERE usuario = ?", (usuario_activo,))
        alumnos = [row[0] for row in cursor.fetchall()]
        alumno_sel = st.selectbox("Selecciona un alumno", alumnos)
        df = pd.read_sql_query("SELECT * FROM alumnos WHERE nombre = ? AND usuario = ?", conn, params=(alumno_sel, usuario_activo))
        st.dataframe(df)

    elif menu == "Exportar a Excel":
        st.subheader("📥 Exportar Datos")
        df = pd.read_sql_query("SELECT * FROM alumnos WHERE usuario = ?", conn, params=(usuario_activo,))
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        st.download_button(
            label="Descargar Excel",
            data=buffer,
            file_name="registro_alumnos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    elif menu == "Generar PDF Alumno":
        st.subheader("📄 Generar Reporte PDF")
        cursor.execute("SELECT DISTINCT nombre FROM alumnos WHERE usuario = ?", (usuario_activo,))
        alumnos = [row[0] for row in cursor.fetchall()]
        alumno_sel = st.selectbox("Seleccionar alumno", alumnos)

        if alumno_sel:
            datos = pd.read_sql_query("SELECT * FROM alumnos WHERE nombre = ? AND usuario = ?", conn, params=(alumno_sel, usuario_activo))
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Reporte de {alumno_sel}", ln=True, align="C")
            for index, row in datos.iterrows():
                for col in datos.columns:
                    pdf.cell(200, 8, txt=f"{col}: {row[col]}", ln=True)
                pdf.ln()
            pdf.output("reporte_alumno.pdf")
            with open("reporte_alumno.pdf", "rb") as f:
                st.download_button("Descargar PDF", f, file_name=f"{alumno_sel}_reporte.pdf")
