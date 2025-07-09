# Nueva versión mejorada de la app de Chilotitos Fitness
# Incluye: contraseñas encriptadas, separación de perfiles, dashboard visual, mejoras de UI

import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import datetime
import io
import plotly.express as px
from fpdf import FPDF

# Config
st.set_page_config(page_title="Chilotitos Fitness", layout="wide")
st.title("💪 Chilotitos Fitness - Comunidad de Entrenamiento")

# DB setup
conn = sqlite3.connect("usuarios.db", check_same_thread=False)
cursor = conn.cursor()

# Hashing de contraseña

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# DB creation
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

# Autenticación y creación de usuarios

def autenticar(usuario, clave):
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND contrasena = ?", (usuario, hash_password(clave)))
    return cursor.fetchone()

def crear_usuario(usuario, clave, tipo):
    try:
        cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?)", (usuario, hash_password(clave), tipo))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Sesiones y login
if "usuario" not in st.session_state:
    st.sidebar.subheader("Iniciar Sesión")
    user = st.sidebar.text_input("Usuario")
    pw = st.sidebar.text_input("Contraseña", type="password")
    login = st.sidebar.button("Ingresar")

    if login:
        datos = autenticar(user, pw)
        if datos:
            st.session_state.usuario = datos[0]
            st.session_state.tipo = datos[2]
            st.success("Bienvenido/a " + datos[0])
            st.experimental_rerun()
        else:
            st.error("Credenciales incorrectas")

    if st.sidebar.button("Crear cuenta"):
        with st.form("registro"):
            new_user = st.text_input("Nuevo usuario")
            new_pw = st.text_input("Nueva contraseña", type="password")
            tipo = st.selectbox("Tipo de cuenta", ["alumno", "admin"])
            nombre = st.text_input("Nombre completo")
            edad = st.number_input("Edad", min_value=5, max_value=100)
            nac = st.date_input("Fecha de nacimiento")
            peso = st.number_input("Peso (kg)", min_value=0.0)
            est = st.number_input("Estatura (cm)", min_value=0.0)
            enf = st.text_input("Enfermedad")
            dias = st.selectbox("Días por semana", [1,2,3,4,5,6])
            submit = st.form_submit_button("Registrar cuenta")

            if submit:
                creado = crear_usuario(new_user, new_pw, tipo)
                if creado:
                    cursor.execute("INSERT INTO perfiles VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                   (new_user, nombre, edad, nac.isoformat(), peso, est, enf, dias))
                    conn.commit()
                    st.success("Cuenta creada exitosamente")
                else:
                    st.warning("Usuario ya existe")

else:
    tipo = st.session_state.tipo
    usuario = st.session_state.usuario

    st.sidebar.markdown(f"**Usuario:** `{usuario}`")
    st.sidebar.markdown(f"**Tipo:** `{tipo}`")

    opciones_admin = ["🏷 Perfiles", "📊 Dashboard", "📤 Exportar"]
    opciones_alumno = ["🏃 Entrenamientos", "📅 Mi Calendario", "📊 Mi Progreso"]
    menu = st.sidebar.radio("Menú", opciones_admin if tipo == "admin" else opciones_alumno + ["📤 Exportar"])

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.experimental_rerun()

    if menu == "🏷 Perfiles" and tipo == "admin":
        df = pd.read_sql("SELECT * FROM perfiles", conn)
        st.subheader("Perfiles de Alumnos")
        st.dataframe(df, use_container_width=True)

    elif menu == "🏃 Entrenamientos":
        st.subheader("Registrar Entrenamiento")
        with st.form("entreno"):
            rutina = st.text_input("Rutina")
            ej = st.text_input("Ejercicio")
            rep = st.number_input("Repeticiones", min_value=1)
            ser = st.number_input("Series", min_value=1)
            pes = st.number_input("Peso utilizado (kg)", min_value=0.0)
            guardar = st.form_submit_button("Guardar")
            if guardar:
                hoy = datetime.date.today().isoformat()
                cursor.execute("""
                    INSERT INTO entrenamientos (usuario, fecha, rutina, ejercicio, repeticiones, series, peso_utilizado)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (usuario, hoy, rutina, ej, rep, ser, pes))
                conn.commit()
                st.success("Entrenamiento guardado")

    elif menu == "📅 Mi Calendario":
        df = pd.read_sql_query("SELECT * FROM entrenamientos WHERE usuario = ?", conn, params=(usuario,))
        if df.empty:
            st.info("Sin entrenamientos registrados")
        else:
            df["fecha"] = pd.to_datetime(df["fecha"])
            fechas = df["fecha"].dt.date.unique()
            for f in sorted(fechas):
                st.markdown(f"### {f}")
                st.dataframe(df[df["fecha"].dt.date == f])

    elif menu == "📊 Dashboard" or menu == "📊 Mi Progreso":
        df = pd.read_sql("SELECT * FROM entrenamientos" + ("" if tipo == "admin" else " WHERE usuario = ?"), conn, params=None if tipo == "admin" else (usuario,))
        if not df.empty:
            df["fecha"] = pd.to_datetime(df["fecha"])
            st.subheader("Progreso de Rutinas")
            fig = px.histogram(df, x="fecha", color="usuario" if tipo == "admin" else None, nbins=30, title="Entrenamientos por día")
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "📤 Exportar":
        df = pd.read_sql_query("SELECT * FROM entrenamientos" + ("" if tipo == "admin" else " WHERE usuario = ?"), conn, params=None if tipo == "admin" else (usuario,))
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        st.download_button("Descargar Excel", buffer, file_name="entrenamientos.xlsx")
