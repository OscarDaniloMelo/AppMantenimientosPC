import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os
import io

# CONFIGURACION Y CARGA DE DATOS

st.set_page_config(page_title="Mantenimientos", layout="centered")

# Inicializar memoria
if "memoria" not in st.session_state:
    st.session_state.memoria = {
        "tareas_seleccionadas": [],
        "fotos_antes": {},
        "fotos_despues": {},
        "observaciones": ""
    }

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

query_params = st.query_params
empresa_url = query_params.get("empresa")
if empresa_url:
    sede_buscada = empresa_url[0] if isinstance(empresa_url, list) else empresa_url
    sede_buscada = str(sede_buscada).strip()
    df_filtrado = df_equipos[df_equipos['empresa'].str.lower() == sede_buscada.lower()]

    if not df_filtrado.empty:
        st.success(f"Filtrado por: {sede_buscada.upper()}")
        df_final = df_filtrado
        
    else:
        st.warning(f"No se encontraron equipos para la empresa: {sede_buscada}. Se mostrarán todos.")
        df_final = df_equipos
else:
    df_final = df_equipos

st.title("Mantenimientos")

if df_final.empty:
    st.error("No hay equipos disponibles para mostrar.")
    st.stop() # Detiene la ejecución si no hay datos

# IMPORTANTE: Usamos df_final['placa'] para que el selectbox solo muestre los equipos filtrados
placa_input = st.selectbox("Seleccione la Placa o ID del Equipo", df_final['placa'])

# Traer datos automáticamente basados en la selección
info = df_final[df_final['placa'] == placa_input].iloc[0]
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
    check = st.checkbox(opcion, value=opcion in st.session_state.memoria["tareas_seleccionadas"])
    if check:
        tareas.append(opcion)

st.session_state.memoria["tareas_seleccionadas"] = tareas

evidencias = {}

for tarea in tareas:
    st.write(f"### Evidencia: {tarea}")
    col1,col2 = st.columns(2)
    with col1:
        archivo_ant = st.file_uploader(f"Antes: {tarea}", type=["jpg", "jpeg", "png"], key=f"antes_{tarea}")
        if archivo_ant:
            st.session_state.memoria["fotos_antes"][tarea] = archivo_ant.getvalue()
        if tarea in st.session_state.memoria["fotos_antes"]:
            st.image(st.session_state.memoria["fotos_antes"][tarea], caption=f"Imagen {tarea} Antes", width=300)
    
    with col2:
        archivo_des = st.file_uploader(f"Despues: {tarea}", type=['jpg', 'png', 'jpeg'], key=f"despues_{tarea}")
        if archivo_des:
            st.session_state.memoria["fotos_despues"][tarea] = archivo_des.getvalue()
        if tarea in st.session_state.memoria["fotos_despues"]:
            st.image(st.session_state.memoria["fotos_despues"][tarea], caption=f"Imagen {tarea} Despues", width=300)

st.session_state.memoria["observaciones"] = st.text_area("Notas Adicionales", value=st.session_state.memoria["observaciones"])

# Generar Reporte
if st.button("Finalizar Mantenimiento y Crear PDF"):
    mem = st.session_state.memoria
    if not mem["fotos_antes"] or not mem["fotos_despues"]:
        st.error("Por Favor Sube Las Evidencias Antes De Finalizar")
    else:
        try:
            def agregar_pagina_con_fondo(pdf_obj):
                pdf_obj.add_page()
                try:
                    pdf_obj.image("plantilla_fondo.jpg", x=0, y=0, w=210, h=297) 
                except:
                    st.warning("No se encontró la imagen 'plantilla_fondo.jpg', el PDF saldrá blanco.")

            pdf = FPDF ()
            pdf.set_auto_page_break(auto=False)
            agregar_pagina_con_fondo(pdf)

            # Encabezado
            pdf.set_y(50)
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='R')
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, f"Reporte De Mantenimiento: ", ln=True, align='C')
            pdf.cell(0, 10, f"{info['empresa']}", ln=True, align='C')
            pdf.ln(5)

            # Datos del Equipo

            pdf.set_fill_color(230, 230, 230)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Datos Del Equipo", ln=True, fill=True)
            pdf.set_font("Arial", size=11)
            pdf.cell(0, 8, f"Usuario: {info['usuario']}", ln=True)
            pdf.cell(0, 8, f"Placa/ID: {info['placa']} | Hostname: {info['hostname']}", ln=True)
            pdf.ln(5)

            # Evidencia Fotografica
            pdf.set_fill_color(230, 230, 230)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Evidencia Fotografica (Antes vs Despues)", ln=True, fill=True)

            # Validar Memoria Guardada
            ALTO_REQUERIDO = 82.0 
            
            for tarea in mem["tareas_seleccionadas"]:                
                if tarea in mem["fotos_antes"] and tarea in mem["fotos_despues"]:
                    
                    # --- LÓGICA DE SALTO DE PÁGINA ---
                    if pdf.get_y() + ALTO_REQUERIDO > 270:
                        agregar_pagina_con_fondo(pdf)
                        pdf.set_y(50)

                    pdf.set_font("Arial", 'B', 12)
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(0, 10, f"{tarea}: ", ln=True)

                    y_etiquetas = pdf.get_y() 
                    y_marcos = y_etiquetas + 5 

                    pos_x = [10, 110]
                    fotos_data = [mem["fotos_antes"][tarea], mem["fotos_despues"][tarea]]
                    etiquetas = ["ANTES", "DESPUÉS"]

                    for i in range(2):
                        pdf.set_font("Arial", 'B', 9)
                        pdf.set_text_color(50, 50, 50)
                        pdf.set_xy(pos_x[i], y_etiquetas)
                        pdf.cell(90, 5, etiquetas[i], align='C', ln=False)
                        
                        # --- PROCESAR E INSERTAR IMAGEN ---
                        img = Image.open(io.BytesIO(fotos_data[i]))
                        if img.height > img.width:
                            img = img.rotate(90, expand=True)

                        # Dibujar el marco gris
                        pdf.set_draw_color(180, 180, 180)
                        pdf.rect(pos_x[i], y_marcos, 90, 60)

                        # Cálculo de escalado
                        ancho_orig, alto_orig = img.size
                        ratio = min(90 / ancho_orig, 60 / alto_orig)
                        w_f, h_f = ancho_orig * ratio, alto_orig * ratio

                        # Centrado
                        off_x = (90 - w_f) / 2
                        off_y = (60 - h_f) / 2

                        temp_path = f"temp_{i}_{tarea.replace('/', '_')}.jpg"
                        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                        img.save(temp_path, "JPEG", quality=80)

                        pdf.image(temp_path, x=pos_x[i] + off_x, y=y_marcos + off_y, w=w_f, h=h_f)
                        os.remove(temp_path)

                    pdf.set_y(y_marcos + 65)

            if st.session_state.memoria["observaciones"]:
                pdf.ln(5)
                pdf.set_font("Arial", "B", 11)
                pdf.cell(0, 10, "Notas Adicionales", ln=True)
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 8, st.session_state.memoria["observaciones"])

            # Generar Descarga
            pdf_bytes = pdf.output(dest="S").encode("latin-1")
            st.success("Reporte Generado Con Exito")
            st.download_button(label = "Descargar PDF", data=pdf_bytes, file_name=f"Reporte_{info['placa']}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
            if st.button("Empezar nuevo mantenimiento"):
                st.session_state.memoria = {
                    "tareas_seleccionadas": [],
                    "fotos_antes": {},
                    "fotos_despues": {},
                    "observaciones": ""
                }
                st.rerun()
        except Exception as e:
            st.error(f"Ocurrio Un Error: {e}")
