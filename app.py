import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os
import io
from streamlit_drawable_canvas import st_canvas
import numpy as np

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
        'empresa': ['Empresa A', 'Empresa A', 'Empresa B'],
        'modelo': ['Dell OptiPlex 3080', 'HP ProDesk 400', 'Lenovo ThinkPad E14']
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
    st.info(f"**Modelo:** {info['modelo']}")
    st.info(f"**Empresa:** {info['empresa']}")

st.divider()

# Limpieza Antes y despues

st.subheader ("Tareas del Mantenimiento")
st.write("¿Que Componentes vas a Limpiar?")
opciones = ["Chasis/Torre", "Pantalla", "Teclado", "Mouse"]
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

# Validaciones Tecnicas
st.subheader("Validaciones Técnicas")
col_c1, col_c2 = st.columns(2)
with col_c1:
    soplado = st.checkbox("Soplado Interno (Limpieza de polvo)")
    pasta = st.checkbox("Aplicación de Pasta Térmica")
with col_c2:
    ventiladores = st.checkbox("Validación de Ventiladores/Coolers")
    estado_disco = st.selectbox("Estado del Disco Duro", ["Óptimo", "En Observación", "Crítico / Requiere Cambio"])

st.divider()

# Observaciones
st.session_state.memoria["observaciones"] = st.text_area("Notas Adicionales", value=st.session_state.memoria["observaciones"])

st.divider()

# RESPONSABLES Y FIRMA
st.subheader("Finalización")
col_f1, col_f2 = st.columns(2)
with col_f1:
    st.write("**Firma del Técnico:**")
    # El canvas crea un recuadro de dibujo
    firma_tecnico_canvas = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Color de relleno (no se usa para firmas)
        stroke_width=2,                       # Grosor del lápiz
        stroke_color="#000000",               # Color negro
        background_color="#FFFFFF",           # Fondo blanco
        height=150,                           # Alto del recuadro
        width=300,                            # Ancho del recuadro
        drawing_mode="freedraw",              # Modo dibujo libre
        key="canvas_tecnico",
    )
    tecnico = st.text_input("Técnico que realiza el mantenimiento", placeholder="Nombre del técnico")

with col_f2:
    st.write("**Firma del Usuario (Aceptación):**")
    firma_usuario_canvas = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=150,
        width=300,
        drawing_mode="freedraw",
        key="canvas_usuario",
    )
    confirmacion_usuario = st.text_input("Aceptación del Usuario", placeholder="Nombre de quien recibe")

st.divider()

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
            ancho_col = 95
            pdf.cell(ancho_col, 8, f"Usuario: {info['usuario']}", ln=0, border=0) # ln=0 -> Se queda en la linea
            pdf.cell(ancho_col, 8, f"Hostname: {info['hostname']}", ln=1, border=0) # ln=1 -> Salta linea
            pdf.cell(ancho_col, 8, f"Placa/ID: {info['placa']}", ln=0, border=0)
            pdf.cell(ancho_col, 8, f"Modelo: {info.get('modelo', 'Genérico')}", ln=1, border=0)
            pdf.ln(2)

            # Validacion Componentes Intervenidos
            pdf.set_fill_color(230, 230, 230)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Alcance del Mantenimiento (Limpieza)", ln=True, fill=True)
            pdf.set_font("Arial", size=11)
            
            # Creamos una cadena de texto con los componentes seleccionados
            if mem["tareas_seleccionadas"]:
                componentes_limpios = ", ".join(mem["tareas_seleccionadas"])
                pdf.multi_cell(0, 8, f"{componentes_limpios}.")
            else:
                pdf.cell(0, 8, "No se seleccionaron componentes específicos.", ln=True)
            pdf.ln(2)

            # Bloque de Validaciones Técnicas
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 10, "Validaciones Tecnicas Realizadas", ln=True, fill=True)

            pdf.set_font("Arial", size=10)
            # Mostramos los resultados de los checks
            res_soplado = "SÍ" if soplado else "NO"
            res_pasta = "SÍ" if pasta else "NO"
            res_vent = "SÍ" if ventiladores else "NO"

            pdf.cell(0, 8, f"Soplado Interno: {res_soplado} | Pasta Térmica: {res_pasta} | Validacion Ventiladores: {res_vent}", ln=True)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 8, f"Diagnóstico del Disco: {estado_disco.upper()}", ln=True)
            pdf.ln(2)

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
                if pdf.get_y() + 50 > 270:
                        agregar_pagina_con_fondo(pdf)
                        pdf.set_y(50)
                pdf.ln(5)
                pdf.set_font("Arial", "B", 11)
                pdf.cell(0, 10, "Notas Adicionales", ln=True)
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 8, st.session_state.memoria["observaciones"])

            if pdf.get_y() + 50 > 270:
                agregar_pagina_con_fondo(pdf)
                pdf.set_y(50)
            else:
                pdf.ln(10)

            y_firmas = pdf.get_y()
            
            # Títulos de las firmas
            pdf.set_font("Arial", 'B', 10)
            pdf.set_xy(10, y_firmas)
            pdf.cell(90, 5, "Firma del Técnico:", ln=0, align='L')
            
            pdf.set_xy(110, y_firmas)
            pdf.cell(90, 5, "Firma del Usuario:", ln=1, align='L')
            
            # --- PROCESAR FIRMA TÉCNICO ---
            if firma_tecnico_canvas.image_data is not None:
                # Convertir matriz numpy a imagen PIL
                img_tec = Image.fromarray(firma_tecnico_canvas.image_data.astype('uint8'), 'RGBA')
                # Convertir a RGB (Fondo blanco) para que FPDF no falle
                background = Image.new("RGB", img_tec.size, (255, 255, 255))
                background.paste(img_tec, mask=img_tec.split()[3]) # Usar canal alpha como máscara
                
                background.save("temp_firma_tec.jpg", "JPEG")
                pdf.image("temp_firma_tec.jpg", x=10, y=y_firmas + 5, w=60, h=30)
                os.remove("temp_firma_tec.jpg")
            
            # --- PROCESAR FIRMA USUARIO ---
            if firma_usuario_canvas.image_data is not None:
                img_user = Image.fromarray(firma_usuario_canvas.image_data.astype('uint8'), 'RGBA')
                background = Image.new("RGB", img_user.size, (255, 255, 255))
                background.paste(img_user, mask=img_user.split()[3])
                
                background.save("temp_firma_user.jpg", "JPEG")
                pdf.image("temp_firma_user.jpg", x=110, y=y_firmas + 5, w=60, h=30)
                os.remove("temp_firma_user.jpg")

            # Líneas y Nombres debajo de la firma
            pdf.set_y(y_firmas + 35) # Bajamos después de la imagen
            pdf.set_font("Arial", size=9)
            
            pdf.cell(95, 5, "__________________________", ln=0, align='L')
            pdf.set_xy(110, pdf.get_y())
            pdf.cell(95, 5, "__________________________", ln=1, align='L')
            
            pdf.cell(95, 5, f"Nombre: {tecnico}", ln=0, align='L')
            pdf.set_xy(110, pdf.get_y())
            pdf.cell(95, 5, f"Nombre: {confirmacion_usuario}", ln=1, align='L')

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
