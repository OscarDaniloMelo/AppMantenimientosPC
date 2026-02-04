import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image

# CONFIGURACION Y CARGA DE DATOS

st.set_page_config(page_title="Mantenimientos", layout="centered")

#carga de base de datos
@st.cache_data
def cargar_datos():
    # En el futuro: df = pd.read_csv('equipos.csv')
    data = {
        'placa': ['ABC-001', 'ABC-002', 'XYZ-999'],
        'hostname': ['WS-SERV-01', 'WS-SERV-02', 'LAPTOP-10'],
        'usuario': ['Juan Pérez', 'Ana García', 'Carlos Ruiz'],
        'empresa': ['Empresa A', 'Empresa A', 'Empresa B']
    }

    return pd.DataFrame(data)

df_equipos=cargar_datos()

st.title("Mantenimientos")

# seleccion de equipo

st.subheader ("Identificacion del Equipo")
placa_input = st.selectbox("Selecione la Placa o ID del Equipo", df_equipos['placa'])

# traer datos automaticamente

info = df_equipos[df_equipos['placa'] == placa_input].iloc[0]
col_a, col_b, = st.columns(2)
with col_a:
    st.info(f"**Usuario:** {info['usuario']}")
    st.info(f"**Hostname:** {info['hostname']}")
with col_b:
    st.info(f"**Empresa:** {info['empresa']}")

st.divider()

# Limpieza Antes y despues

st.subheader ("Tareas del Mantenimiento")
st.write("¿Que Componentes vas a Limpiar?")
opciones = ["Chasis/Torre", "Pantalla", "Tecaldo", "Mouse"]
tareas= []
for opcion in opciones:
    if st.checkbox(opcion):
        tareas.append(opcion)

f_antes={}
f_despues={}
evidencias = {}

for tarea in tareas:
    st.write(f"### Evidencia: {tarea}")
    col1,col2 = st.columns(2)
    with col1:
        f_antes[tarea] = st.file_uploader(f"Antes: {tarea}", type=["jpg", "jpeg", "png"], key=f"antes_{tarea}")
        if f_antes[tarea] is not None:
            imagen = Image.open(f_antes[tarea])
            st.image(imagen, caption=f"Imagen {tarea} Antes", width=300)
    
    with col2:
        f_despues[tarea] = st.file_uploader(f"Despues: {tarea}", type=['jpg', 'png', 'jpeg'], key=f"despues_{tarea}")
        if f_despues[tarea] is not None:
            imagen = Image.open(f_despues[tarea])
            st.image(imagen, caption=f"Imagen {tarea} Despues", width=300)

    if f_antes and f_despues:
        evidencias[tarea] = {'antes': f_antes, 'despues': f_despues} 

observaciones = st.text_area("Notas Adicionales")

# Generar Reporte
if st.button("Finalizar Manteniiento y Crear PDF"):
    st.success(f"Reporte listo para {df_equipos['usuario']} de {df_equipos['empresa']}")