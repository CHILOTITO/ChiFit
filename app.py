# app.py
import streamlit as st
import pandas as pd
import datetime
import os
import io
from fpdf import FPDF

st.set_page_config(page_title="Control de Alumnos - Gimnasio", layout="wide")

st.title("🏋️ Control de Alumnos - Chilotitos Fitness")

# Cargar o crear base de datos
DB_FILE = "datos_alumnos.xlsx"
if os.path.exists(DB_FILE):
    df = pd.read_excel(DB_FILE)
else:
    df = pd.DataFrame(columns=[
        "Nombre", "Edad", "Fecha de Nacimiento", "Peso (kg)", "Estatura (cm)",
        "Enfermedad", "Días por semana", "Fecha", "Rutina", "Ejercicio",
        "Repeticiones", "Series", "Peso utilizado (kg)"
    ])

# Mostrar logo si existe
if os.path.exists("assets/logo.png"):
    st.sidebar.image("assets/logo.png", width=200)

# Menú de navegación
menu = st.sidebar.radio("Navegación", [
    "Registrar Alumno", "Registrar Entrenamiento", "Dashboard",
    "Exportar a Excel", "Generar PDF Alumno"
])

# Registrar alumno
if menu == "Registrar Alumno":
    st.subheader("📋 Registro de Información Personal")
    with st.form("form_registro"):
        nombre = st.text_input("Nombre")
        edad = st.number_input("Edad", min_value=5, max_value=100)
        fecha_nac = st.date_input(
            "Fecha de Nacimiento",
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today()
        )
        peso = st.number_input("Peso corporal (kg)", min_value=0.0)
        estatura = st.number_input("Estatura (cm)", min_value=0.0)
        enfermedad = st.text_input("¿Tiene alguna enfermedad?")
        dias = st.selectbox("¿Cuántos días asistirá por semana?", [1, 2, 3, 4, 5, 6])
        enviar = st.form_submit_button("Guardar")

        if enviar:
            nueva_fila = {
                "Nombre": nombre, "Edad": edad, "Fecha de Nacimiento": fecha_nac,
                "Peso (kg)": peso, "Estatura (cm)": estatura,
                "Enfermedad": enfermedad, "Días por semana": dias,
                "Fecha": datetime.date.today(), "Rutina": "", "Ejercicio": "",
                "Repeticiones": "", "Series": "", "Peso utilizado (kg)": ""
            }
            df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
            df.to_excel(DB_FILE, index=False)
            st.success("Alumno registrado con éxito ✅")

# Registrar entrenamiento
elif menu == "Registrar Entrenamiento":
    st.subheader("🏃 Registro de Entrenamiento")
    alumnos = df["Nombre"].unique().tolist()
    alumno_sel = st.selectbox("Seleccionar Alumno", alumnos)
    if alumno_sel:
        rutina = st.text_input("Nombre de la Rutina")

        st.markdown("### Ejercicios del día")

        ejercicios = st.session_state.get("ejercicios_temp", [])

        # Agregar nuevo ejercicio temporalmente
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
                datos_alumno = df[df.Nombre == alumno_sel].iloc[0]
                for ej in ejercicios:
                    nueva_fila = {
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

                df.to_excel(DB_FILE, index=False)
                st.success("Entrenamiento completo guardado ✅")

                # Reset lista temporal
                st.session_state.ejercicios_temp = []

# Dashboard
elif menu == "Dashboard":
    st.subheader("📊 Dashboard por Alumno")
    alumnos = df["Nombre"].unique().tolist()
    alumno_sel = st.selectbox("Selecciona un alumno", alumnos)
    datos = df[df["Nombre"] == alumno_sel]
    st.dataframe(datos)

# Exportar a Excel
elif menu == "Exportar a Excel":
    st.subheader("📅 Exportar Datos")
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)

    st.download_button(
        label="Descargar Excel",
        data=excel_buffer,
        file_name="registro_alumnos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Generar PDF
elif menu == "Generar PDF Alumno":
    st.subheader("📄 Generar Reporte PDF")
    alumnos = df["Nombre"].unique().tolist()
    alumno_sel = st.selectbox("Seleccionar alumno", alumnos)
    if alumno_sel:
        datos = df[df["Nombre"] == alumno_sel]
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
