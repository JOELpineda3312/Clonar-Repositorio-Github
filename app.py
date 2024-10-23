import os
import git
import shutil
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Ruta para la carpeta donde se guardarán los repositorios descargados
BASE_DIR = os.path.expanduser("~/Desktop/Archivos Clonados Git")
ORIGINAL_DIR = os.path.join(BASE_DIR, "Archivos Con Extension Original")
TXT_DIR = os.path.join(BASE_DIR, "Archivos Convertidos a .txt")

# Crear las carpetas principales si no existen
os.makedirs(ORIGINAL_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)

def clonar_repositorio(url_github, nombre_proyecto):
    """Clona el repositorio desde GitHub."""
    destino = os.path.join(ORIGINAL_DIR, nombre_proyecto)
    
    # Verifica si el repositorio ya ha sido clonado
    if os.path.exists(destino):
        return destino, True  # Devuelve el destino y un indicador de que ya existe

    try:
        git.Repo.clone_from(url_github, destino)
        return destino, False  # Devuelve el destino y un indicador de que no existía
    except Exception as e:
        return str(e), None  # En caso de error, devuelve el mensaje de error


def convertir_a_txt(carpeta):
    """Convierte archivos de texto a .txt y copia imágenes/videos sin cambiar su formato."""
    txt_carpeta = os.path.join(TXT_DIR, os.path.basename(carpeta) + "_txt")
    
    if os.path.exists(txt_carpeta):
        shutil.rmtree(txt_carpeta)

    os.makedirs(txt_carpeta)

    for root, dirs, files in os.walk(carpeta):
        for file in files:
            origen = os.path.join(root, file)
            relative_path = os.path.relpath(origen, carpeta)

            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.mp4', '.avi', '.mov')):
                # Si es una imagen o video, copiar el archivo tal cual
                destino = os.path.join(txt_carpeta, relative_path)
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                shutil.copy2(origen, destino)
            else:
                # Si es un archivo de texto, convertirlo a .txt
                nuevo_nombre = relative_path.replace(".", "_") + ".txt"
                destino = os.path.join(txt_carpeta, nuevo_nombre)

                try:
                    with open(origen, 'rb') as f_origen:
                        contenido = f_origen.read()
                        try:
                            contenido.decode('utf-8')  # Solo para archivos de texto
                            with open(destino, 'w', encoding='utf-8') as f_destino:
                                f_destino.write(contenido.decode('utf-8'))
                        except (UnicodeDecodeError, ValueError):
                            print(f"Omitiendo archivo no texto: {origen}")
                except Exception as e:
                    print(f"Error al procesar el archivo {origen}: {e}")

    return txt_carpeta


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/descargar', methods=['POST'])
def descargar():
    url_github = request.form['url_github']
    nombre_proyecto = url_github.split('/')[-1].replace('.git', '')

    # Verificar el tipo de descarga
    tipo_descarga = request.form['tipo_descarga']

    if tipo_descarga == "original":
        # Clonamos el repositorio y descargamos solo originales
        resultado_clonacion, ya_existe = clonar_repositorio(url_github, nombre_proyecto)
        
        if ya_existe:
            return jsonify({'mensaje': f"Archivo ya descargado en: {resultado_clonacion}", 'tipo': 'original'})

        return jsonify({'mensaje': f"Archivos originales descargados en: {resultado_clonacion}", 'tipo': 'original'})

    elif tipo_descarga == "txt":
        # Clonamos el repositorio y convertimos los archivos a .txt (con imágenes y videos)
        resultado_clonacion, ya_existe = clonar_repositorio(url_github, nombre_proyecto)

        if not ya_existe:
            txt_carpeta = convertir_a_txt(resultado_clonacion)
            return jsonify({'mensaje': f"Archivos convertidos a .txt y guardados en: {txt_carpeta}", 'tipo': 'txt'})

        return jsonify({'mensaje': f"Archivo ya descargado en formato original: {resultado_clonacion}. Convierte los archivos manualmente si deseas.", 'tipo': 'txt'})

    return jsonify({'error': 'Opción de descarga no válida.'})


if __name__ == '__main__':
    app.run(debug=True)
