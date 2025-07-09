# Nueva versión mejorada de la app de Chilotitos Fitness
# Incluye: contraseñas encriptadas, dashboard visual, mejoras de UI, red social básica, control de administrador

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
st.markdown("""
<style>
    .main { background-color: #f5f5f5; }
    .stButton > button {
        background-color: #01bf71;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)
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
    tipo TEXT NOT NULL DEFAULT 'alumno'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS perfiles (
    usuario TEXT PRIMARY KEY,
    nombre TEXT,
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS publicaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    contenido TEXT,
    fecha TEXT
)
""")

conn.commit()

# Autenticación y creación de usuarios
def autenticar(usuario, clave):
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND contrasena = ?", (usuario, hash_password(clave)))
    return cursor.fetchone()

def crear_usuario(usuario, clave):
    try:
        cursor.execute("INSERT INTO usuarios (usuario, contrasena) VALUES (?, ?)", (usuario, hash_password(clave)))
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
            nombre = st.text_input("Nombre completo")
            nac = st.date_input("Fecha de nacimiento",min_value=datetime.date(1900, 1, 1),max_value=datetime.date.today())
            peso = st.number_input("Peso (kg)", min_value=0.0)
            est = st.number_input("Estatura (cm)", min_value=0.0)
            enf = st.text_input("Enfermedad")
            dias = st.selectbox("Días por semana", [1,2,3,4,5,6])
            submit = st.form_submit_button("Registrar cuenta")

            if submit:
                creado = crear_usuario(new_user, new_pw)
                if creado:
                    cursor.execute("INSERT INTO perfiles VALUES (?, ?, ?, ?, ?, ?, ?)",
                                   (new_user, nombre, nac.isoformat(), peso, est, enf, dias))
                    conn.commit()
                    st.success("Cuenta creada exitosamente")
                else:
                    st.warning("Usuario ya existe")

else:
    tipo = st.session_state.tipo
    usuario = st.session_state.usuario

    st.sidebar.markdown(f"**Usuario:** `{usuario}`")
    st.sidebar.markdown(f"**Tipo:** `{tipo}`")

    menu = st.sidebar.radio("Menú", ["📢 Muro", "🏃 Entrenamientos", "📅 Calendario", "📊 Progreso", "📤 Exportar"] + (["🔑 Asignar Admin", "🏷 Perfiles"] if tipo == "admin" else []))

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.experimental_rerun()

    if menu == "📢 Muro":
        st.subheader("🗣 Publicaciones del gimnasio")
        with st.form("nueva_pub"):
            contenido = st.text_area("¿Qué quieres compartir hoy?")
            publicar = st.form_submit_button("Publicar")
            if publicar and contenido:
                cursor.execute("INSERT INTO publicaciones (usuario, contenido, fecha) VALUES (?, ?, ?)",
                               (usuario, contenido, datetime.date.today().isoformat()))
                conn.commit()
                st.success("Publicado")

        publicaciones = pd.read_sql("SELECT * FROM publicaciones ORDER BY id DESC", conn)
        for _, row in publicaciones.iterrows():
            st.markdown(f"**{row['usuario']}** ({row['fecha']}):\n\n{row['contenido']}")
            st.markdown("---")

    elif menu == "🏷 Perfiles":
        df = pd.read_sql("SELECT * FROM perfiles", conn)
        st.subheader("Perfiles de Alumnos")
        st.dataframe(df, use_container_width=True)

    elif menu == "🔑 Asignar Admin":
        st.subheader("👑 Otorgar permisos de administrador")
        usuarios = pd.read_sql("SELECT usuario FROM usuarios WHERE tipo = 'alumno'", conn)
        seleccionar = st.selectbox("Selecciona un usuario", usuarios["usuario"])
        if st.button("Convertir en administrador"):
            cursor.execute("UPDATE usuarios SET tipo = 'admin' WHERE usuario = ?", (seleccionar,))
            conn.commit()
            st.success(f"{seleccionar} ahora es administrador")

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

    elif menu == "📅 Calendario":
        df = pd.read_sql_query("SELECT * FROM entrenamientos WHERE usuario = ?", conn, params=(usuario,))
        if df.empty:
            st.info("Sin entrenamientos registrados")
        else:
            df["fecha"] = pd.to_datetime(df["fecha"])
            fechas = df["fecha"].dt.date.unique()
            for f in sorted(fechas):
                with st.expander(f"Entrenamientos del {f}"):
                    st.dataframe(df[df["fecha"].dt.date == f])

    elif menu == "📊 Progreso":
        df = pd.read_sql("SELECT * FROM entrenamientos WHERE usuario = ?", conn, params=(usuario,))
        if not df.empty:
            df["fecha"] = pd.to_datetime(df["fecha"])
            st.subheader("Progreso de Rutinas")
            fig = px.histogram(df, x="fecha", nbins=30, title="Entrenamientos por día")
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "📤 Exportar":
        df = pd.read_sql_query("SELECT * FROM entrenamientos WHERE usuario = ?", conn, params=(usuario,))
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        st.download_button("Descargar Excel", buffer, file_name="entrenamientos.xlsx")
