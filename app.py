# app.py
import streamlit as st
import sqlite3
import datetime
import pandas as pd
import io
from fpdf import FPDF
import os
import calendar

st.set_page_config(page_title="Chilotitos Fitness - Red Social", layout="wide")
st.title("💪 Chilotitos Fitness - Comunidad de Entrenamiento")

# Conexión a la base de datos SQLite
conn = sqlite3.connect("usuarios.db", check_same_thread=False)
cursor = conn.cursor()

# Crear tablas si no existen
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        contrasena TEXT NOT NULL,
        tipo TEXT NOT NULL
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS perfiles (
        usuario TEXT PRIMARY KEY,
        nombre TEXT,
        edad INTEGER,
        fecha_nacimiento TEXT,
        peso REAL,
        estatura REAL,
        enfermedad TEXT,
        dias_semana INTEGER
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS entrenamientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        fecha TEXT,
        rutina TEXT,
        ejercicio TEXT,
        repeticiones INTEGER,
        series INTEGER,
        peso_utilizado REAL
    )
""")
conn.commit()

# Funciones

def autenticar(usuario, clave):
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND contrasena = ?", (usuario, clave))
    return cursor.fetchone()

def crear_usuario(nuevo_usuario, nueva_clave, tipo):
    try:
        cursor.execute("INSERT INTO usuarios (usuario, contrasena, tipo) VALUES (?, ?, ?)", (nuevo_usuario, nueva_clave, tipo))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Estado para formulario
if "mostrar_formulario" not in st.session_state:
    st.session_state.mostrar_formulario = False

# INICIO DE SESIÓN
if "usuario" not in st.session_state:
    st.sidebar.subheader("Iniciar Sesión")
    usuario = st.sidebar.text_input("Usuario")
    clave = st.sidebar.text_input("Contraseña", type="password")
    login = st.sidebar.button("Ingresar")

    if login:
        datos_usuario = autenticar(usuario, clave)
        if datos_usuario:
            st.session_state.usuario = datos_usuario[0]
            st.session_state.tipo = datos_usuario[2]
            st.session_state.logged_in = True

    if st.session_state.get("logged_in", False):
        st.session_state.logged_in = False
        st.experimental_rerun()

    st.sidebar.markdown("¿No tienes cuenta?")
    if st.sidebar.button("Crear cuenta"):
        st.session_state.mostrar_formulario = True

    if st.session_state.mostrar_formulario:
        with st.form("form_crear_cuenta"):
            nuevo_usuario = st.text_input("Nuevo usuario")
            nueva_clave = st.text_input("Nueva contraseña", type="password")
            tipo = st.selectbox("Tipo de cuenta", ["alumno", "admin"])
            nombre = st.text_input("Nombre")
            edad = st.number_input("Edad", min_value=5, max_value=100)
            fecha_nac = st.date_input("Fecha de Nacimiento")
            peso = st.number_input("Peso corporal (kg)", min_value=0.0)
            estatura = st.number_input("Estatura (cm)", min_value=0.0)
            enfermedad = st.text_input("¿Tiene alguna enfermedad?")
            dias = st.selectbox("¿Cuántos días asistirá por semana?", [1, 2, 3, 4, 5, 6])
            crear = st.form_submit_button("Crear cuenta")

            if crear:
                if crear_usuario(nuevo_usuario, nueva_clave, tipo):
                    cursor.execute("""
                        INSERT INTO perfiles (usuario, nombre, edad, fecha_nacimiento, peso, estatura, enfermedad, dias_semana)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (nuevo_usuario, nombre, edad, fecha_nac.isoformat(), peso, estatura, enfermedad, dias))
                    conn.commit()
                    st.success("✅ Cuenta creada con éxito. Ahora puedes iniciar sesión.")
                    st.session_state.mostrar_formulario = False
                else:
                    st.warning("⚠️ El usuario ya existe. Elige otro.")
else:
    if os.path.exists("assets/logo.png"):
        st.sidebar.image("assets/logo.png", width=200)

    usuario_activo = st.session_state.usuario
    tipo_usuario = st.session_state.tipo

    opciones_admin = ["Editar Perfiles", "Ver Entrenamientos", "Exportar a Excel", "Cerrar Sesión"]
    opciones_alumno = ["Registrar Entrenamiento", "Calendario de Entrenamientos", "Exportar a Excel", "Cerrar Sesión"]

    menu = st.sidebar.radio("Navegación", opciones_admin if tipo_usuario == "admin" else opciones_alumno)

    if menu == "Cerrar Sesión":
        st.session_state.clear()
        st.success("Sesión cerrada correctamente")
        st.stop()

    elif menu == "Registrar Entrenamiento":
        st.subheader("🏃 Registrar Entrenamiento")
        rutina = st.text_input("Nombre de la Rutina")
        ejercicio = st.text_input("Ejercicio")
        repes = st.number_input("Repeticiones", min_value=1)
        series = st.number_input("Series", min_value=1)
        peso_util = st.number_input("Peso utilizado (kg)", min_value=0.0)
        enviar = st.button("Guardar")

        if enviar:
            hoy = datetime.date.today().isoformat()
            cursor.execute("""
                INSERT INTO entrenamientos (usuario, fecha, rutina, ejercicio, repeticiones, series, peso_utilizado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (usuario_activo, hoy, rutina, ejercicio, repes, series, peso_util))
            conn.commit()
            st.success("Entrenamiento guardado ✅")

    elif menu == "Calendario de Entrenamientos":
        st.subheader("📅 Calendario de Entrenamientos")
        df = pd.read_sql_query("SELECT * FROM entrenamientos WHERE usuario = ?", conn, params=(usuario_activo,))
        df["fecha"] = pd.to_datetime(df["fecha"])
        fechas = df["fecha"].dt.date.unique()
        for fecha in sorted(fechas):
            st.markdown(f"### {fecha}")
            st.dataframe(df[df["fecha"].dt.date == fecha])

    elif menu == "Exportar a Excel":
        st.subheader("📥 Exportar Datos")
        df = pd.read_sql_query("SELECT * FROM entrenamientos WHERE usuario = ?", conn, params=(usuario_activo,))
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        st.download_button(
            label="Descargar Excel",
            data=buffer,
            file_name="registro_entrenamientos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    elif menu == "Editar Perfiles" and tipo_usuario == "admin":
        st.subheader("👥 Editar Perfiles de Alumnos")
        alumnos = pd.read_sql_query("SELECT * FROM perfiles", conn)
        alumno_sel = st.selectbox("Seleccionar alumno", alumnos["usuario"].unique())
        datos = alumnos[alumnos["usuario"] == alumno_sel].iloc[0]

        with st.form("editar_perfil"):
            nombre = st.text_input("Nombre", value=datos["nombre"])
            edad = st.number_input("Edad", min_value=5, max_value=100, value=int(datos["edad"]))
            fecha_nac = st.date_input("Fecha de Nacimiento", value=pd.to_datetime(datos["fecha_nacimiento"]))
            peso = st.number_input("Peso corporal (kg)", min_value=0.0, value=float(datos["peso"]))
            estatura = st.number_input("Estatura (cm)", min_value=0.0, value=float(datos["estatura"]))
            enfermedad = st.text_input("¿Tiene alguna enfermedad?", value=datos["enfermedad"])
            dias = st.selectbox("Días por semana", [1,2,3,4,5,6], index=int(datos["dias_semana"])-1)
            actualizar = st.form_submit_button("Actualizar")

            if actualizar:
                cursor.execute("""
                    UPDATE perfiles SET nombre=?, edad=?, fecha_nacimiento=?, peso=?, estatura=?, enfermedad=?, dias_semana=?
                    WHERE usuario = ?
                """, (nombre, edad, fecha_nac.isoformat(), peso, estatura, enfermedad, dias, alumno_sel))
                conn.commit()
                st.success("Perfil actualizado ✅")
