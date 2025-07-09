# app.py
import streamlit as st
import pandas as pd
import datetime
import os
import io
from fpdf import FPDF

st.set_page_config(page_title="Chilotitos Fitness - Red Social", layout="wide")

st.title("💪 Chilotitos Fitness - Comunidad de Entrenamiento")

# Archivos de base de datos
USERS_FILE = "usuarios.xlsx"
DATA_FILE = "datos_alumnos.xlsx"

# Crear archivos si no existen
if not os.path.exists(USERS_FILE):
    pd.DataFrame(columns=["Usuario", "Contraseña"]).to_excel(USERS_FILE, index=False)

if os.path.exists(DATA_FILE):
    df = pd.read_excel(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Usuario", "Nombre", "Edad", "Fecha de Nacimiento", "Peso (kg)", "Estatura (cm)",
        "Enfermedad", "Días por semana", "Fecha", "Rutina", "Ejercicio",
        "Repeticiones", "Series", "Peso utilizado (kg)"
    ])

# Función para autenticar (sin cache)
def autenticar(usuario, clave):
    usuarios = pd.read_excel(USERS_FILE)
    match = usuarios[(usuarios["Usuario"] == usuario) & (usuarios["Contraseña"] == clave)]
    return not match.empty

# Página de inicio de sesión
if "usuario" not in st.session_state:
    st.sidebar.subheader("Iniciar Sesión")
    usuario = st.sidebar.text_input("Usuario")
    clave = st.sidebar.text_input("Contraseña", type="password")
    login = st.sidebar.button("Ingresar")

    if login:
        if autenticar(usuario, clave):
            st.session_state.usuario = usuario
            st.success(f"Bienvenido/a, {usuario}")
        else:
            st.error("Usuario o contraseña incorrectos")

    st.sidebar.markdown("¿No tienes cuenta?")
    if st.sidebar.button("Crear cuenta"):
        with st.form("form_crear_cuenta"):
            nuevo_usuario = st.text_input("Nuevo usuario")
            nueva_clave = st.text_input("Nueva contraseña", type="password")
            crear = st.form_submit_button("Crear cuenta")

            if crear:
                usuarios = pd.read_excel(USERS_FILE)
                if nuevo_usuario in usuarios["Usuario"].values:
                    st.warning("El usuario ya existe")
                else:
                    nuevo_df = pd.DataFrame([[nuevo_usuario, nueva_clave]], columns=["Usuario", "Contraseña"])
                    usuarios = pd.concat([usuarios, nuevo_df], ignore_index=True)
                    usuarios.to_excel(USERS_FILE, index=False)
                    st.success("Cuenta creada con éxito. Ahora puedes iniciar sesión arriba. ✅")

else:
    # Mostrar logo si existe
    if os.path.exists("assets/logo.png"):
        st.sidebar.image("assets/logo.png", width=200)

    menu = st.sidebar.radio("Navegación", [
        "Registrar Alumno", "Registrar Entrenamiento", "Dashboard",
        "Exportar a Excel", "Generar PDF Alumno"
    ])

    usuario_activo = st.session_state.usuario

    if menu == "Registrar Alumno":
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
                nueva_fila = {
                    "Usuario": usuario_activo, "Nombre": nombre, "Edad": edad, "Fecha de Nacimiento": fecha_nac,
                    "Peso (kg)": peso, "Estatura (cm)": estatura,
                    "Enfermedad": enfermedad, "Días por semana": dias,
                    "Fecha": datetime.date.today(), "Rutina": "", "Ejercicio": "",
                    "Repeticiones": "", "Series": "", "Peso utilizado (kg)": ""
                }
                df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
                df.to_excel(DATA_FILE, index=False)
                st.success("Alumno registrado con éxito ✅")

    elif menu == "Registrar Entrenamiento":
        st.subheader("🏃 Registro de Entrenamiento")
        alumnos = df[df["Usuario"] == usuario_activo]["Nombre"].unique().tolist()
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
                            "Peso utilizado (kg)": peso_util
                        })
                        st.session_state.ejercicios_temp = ejercicios
                    else:
                        st.warning("Debes escribir un ejercicio")

            if ejercicios:
                st.write("#### Ejercicios agregados:")
                for i, ej in enumerate(ejercicios):
                    st.write(f"{i+1}. {ej['Ejercicio']} – {ej['Repeticiones']} reps, {ej['Series']} series, {ej['Peso utilizado (kg)']} kg")

                if st.button("✅ Guardar entrenamiento completo"):
                    datos_alumno = df[(df["Nombre"] == alumno_sel) & (df["Usuario"] == usuario_activo)].iloc[0]
                    for ej in ejercicios:
                        nueva_fila = {
                            "Usuario": usuario_activo,
                            "Nombre": alumno_sel,
                            "Edad": datos_alumno["Edad"],
                            "Fecha de Nacimiento": datos_alumno["Fecha de Nacimiento"],
                            "Peso (kg)": datos_alumno["Peso (kg)"],
                            "Estatura (cm)": datos_alumno["Estatura (cm)"],
                            "Enfermedad": datos_alumno["Enfermedad"],
                            "Días por semana": datos_alumno["Días por semana"],
                            "Fecha": datetime.date.today(),
                            "Rutina": rutina,
                            "Ejercicio": ej["Ejercicio"],
                            "Repeticiones": ej["Repeticiones"],
                            "Series": ej["Series"],
                            "Peso utilizado (kg)": ej["Peso utilizado (kg)"]
                        }
                        df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)

                    df.to_excel(DATA_FILE, index=False)
                    st.success("Entrenamiento completo guardado ✅")
                    st.session_state.ejercicios_temp = []

    elif menu == "Dashboard":
        st.subheader("📊 Dashboard por Alumno")
        alumnos = df[df["Usuario"] == usuario_activo]["Nombre"].unique().tolist()
        alumno_sel = st.selectbox("Selecciona un alumno", alumnos)
        datos = df[(df["Nombre"] == alumno_sel) & (df["Usuario"] == usuario_activo)]
        st.dataframe(datos)

    elif menu == "Exportar a Excel":
        st.subheader("📥 Exportar Datos")
        datos_usuario = df[df["Usuario"] == usuario_activo]
        excel_buffer = io.BytesIO()
        datos_usuario.to_excel(excel_buffer, index=False, engine="openpyxl")
        excel_buffer.seek(0)
        st.download_button(
            label="Descargar Excel",
            data=excel_buffer,
            file_name="registro_alumnos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    elif menu == "Generar PDF Alumno":
        st.subheader("📄 Generar Reporte PDF")
        alumnos = df[df["Usuario"] == usuario_activo]["Nombre"].unique().tolist()
        alumno_sel = st.selectbox("Seleccionar alumno", alumnos)
        if alumno_sel:
            datos = df[(df["Nombre"] == alumno_sel) & (df["Usuario"] == usuario_activo)]
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
