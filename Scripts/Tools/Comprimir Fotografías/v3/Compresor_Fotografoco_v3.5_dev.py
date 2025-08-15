#!/usr/bin/env python3
##################################################################
#                                                                #
#                   COMPRESOR DE FOTOGRAFÍAS                     #
#                    V3.4 (15 AGOSTO 2025)                       #
#             Carlos Hernández - carlymx@gmail.com               #
#                                                                #
##################################################################

"""
===========================================
CHANGE LOG - Compresor Fotográfico
===========================================

Versión 2.0 → 3.0
-----------------
- Añadida detección automática del sistema operativo (Windows / Linux).
- Implementada instalación automática de dependencias:
  - En Linux, crea y usa un entorno virtual (venv) si es necesario (PEP 668).
  - Instala Pillow, piexif y colorama si faltan.
- Integrada limpieza de pantalla y banner ASCII al inicio.
- Escaneo de directorio origen para:
  - Detectar tipos de archivos soportados y su cantidad.
  - Evitar continuar si no se encuentran imágenes compatibles (opción para reintentar o salir).
- Pregunta directorio destino con valor por defecto (subdirectorio junto al origen).
- Selección de formato de salida por número (JPG, JPEG, PNG, TIFF).
- Configuración de opciones de compresión:
  - Calidad en JPG/JPEG (1–100, por defecto 70).
  - Compresión TIFF: None, LZW, ZIP, JPEG.
- Tamaño límite (KB) para decidir qué imágenes procesar (0 = todas).
- Recreación de estructura de directorios y subdirectorios en destino.
- Conserva metadatos EXIF cuando es posible.
- Sistema de logging:
  - Archivo .log con todo el detalle del proceso.
  - Registro de errores y conversiones exitosas.
- Resumen final con:
  - Total encontrados
  - Cuántos superaron el límite
  - Cuántos procesados
  - Errores
  - Ubicación del log.

Versión 3.1
-----------------
- Implementado modo multiproceso:
  - Detecta CPUs disponibles y pregunta cuántos procesos usar (1 por defecto).
  - Si se selecciona 1 → modo secuencial (como antes).
  - Si >1 → usa ProcessPoolExecutor para paralelizar tareas.

Versión 3.2
-----------------
- Solucionado error al convertir PNG → JPG/JPEG:
  - Ahora, si la imagen tiene canal alfa (RGBA, LA), se convierte a RGB antes de guardarla.
  - Evita fallo de Pillow al guardar en formatos que no soportan transparencia.

Versión 3.3
-----------------
- Añadida opción de compresión PNG:
  - Pregunta nivel de compresión (0–9, por defecto 6).
  - 0 = sin compresión (más rápido, archivos más grandes).
  - 9 = máxima compresión (más lento, archivos más pequeños).
  - Compresión siempre sin pérdida.
  - Parámetro aplicado en el guardado: compress_level.

Versión 3.4
-----------------
- Corregida la redundacia de necesitar la librería "Colorama" e instalarla en el entorno virtual.

Versión 3.5
-----------------
- Añadidas opciones para el copiado de archivos no procesables o archivos más grandes que lo estipulado.

"""
import os
import sys
import platform
import subprocess
import logging
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
import shutil
from collections import Counter

# Intentar importar colorama (para colores), si no existe usar versiones dummy
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Dummy:
        def __getattr__(self, attr):
            return ''
    Fore = Style = Dummy()

# Dependencias a instalar en entorno virtual
REQUIRED_LIBS = ["Pillow", "piexif", "colorama"]

# ===================
# Funciones auxiliares
# ===================
def ensure_venv():
    if platform.system() == "Linux":
        venv_dir = os.path.join(os.getcwd(), "venv")
        if not os.path.exists(venv_dir):
            print(Fore.YELLOW + "Creando entorno virtual en el directorio de ejecución..." + Style.RESET_ALL)
            subprocess.run([sys.executable, "-m", "venv", venv_dir])
            pip_path = os.path.join(venv_dir, "bin", "pip")
            subprocess.run([pip_path, "install", "--upgrade", "pip"])
            subprocess.run([pip_path, "install"] + REQUIRED_LIBS)
        sys.path.insert(0, os.path.join(venv_dir, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages"))

ensure_venv()

from PIL import Image, ExifTags
import piexif

def get_input(prompt, default=None):
    val = input(prompt)
    return val.strip() if val.strip() else default

def safe_exif_dump(exif_bytes):
    try:
        return piexif.dump(piexif.load(exif_bytes)) if exif_bytes else None
    except Exception:
        return None

def process_single_image(file_path, output_format, output_dir, size_limit, quality, compression_opts, png_compress):
    try:
        img = Image.open(file_path)
        exif_bytes = img.info.get('exif')

        if output_format in ["JPG", "JPEG"] and img.mode in ('RGBA', 'LA'):
            img = img.convert('RGB')

        rel_path = os.path.relpath(file_path, start=input_dir)
        new_path = os.path.join(output_dir, os.path.splitext(rel_path)[0] + "." + output_format.lower())
        os.makedirs(os.path.dirname(new_path), exist_ok=True)

        if size_limit > 0 and os.path.getsize(file_path) <= size_limit * 1024:
            return False, file_path

        save_params = {}
        if output_format in ["JPG", "JPEG"]:
            save_params['quality'] = quality
            save_params['optimize'] = True
        elif output_format == "TIFF" and compression_opts:
            save_params['compression'] = compression_opts
        elif output_format == "PNG":
            save_params['compress_level'] = png_compress

        exif_for_save = safe_exif_dump(exif_bytes)
        if exif_for_save:
            save_params['exif'] = exif_for_save

        img.save(new_path, output_format, **save_params)
        return True, file_path
    except Exception as e:
        logging.error(f"Error procesando {file_path}: {e}")
        return None, file_path

def main():
    # Configurar logging
    os.makedirs("logs", exist_ok=True)
    log_file = os.path.join("logs", f"image_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    system = platform.system()
    print(Fore.GREEN + f"Sistema operativo detectado: {system}" + Style.RESET_ALL)

    global input_dir
    input_dir = get_input("Ingrese el directorio a procesar: ")
    if not input_dir or not os.path.isdir(input_dir):
        print("Directorio inválido.")
        sys.exit(1)

    # Escaneo de archivos
    valid_exts = [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif", ".raw", ".cr2", ".nef", ".arw"]
    all_files = []
    for root, _, files in os.walk(input_dir):
        for f in files:
            all_files.append(os.path.join(root, f))

    images = [f for f in all_files if os.path.splitext(f)[1].lower() in valid_exts]
    others = [f for f in all_files if f not in images]

    # Contadores por extensión
    counts = Counter([os.path.splitext(f)[1].lower() for f in all_files])

    print("Resumen de archivos encontrados:")
    print(f"{len(images)} archivos de imagen compatibles")
    print(f"{len(others)} archivos no procesables")
    for ext, count in counts.items():
        print(f"  {count} archivos en formato {ext}")
    logging.info("Resumen de archivos por extensión:")
    for ext, count in counts.items():
        logging.info(f"{ext}: {count}")

    # Directorio destino
    default_out = input_dir + "_convertidos"
    output_dir = get_input(f"Ingrese el directorio destino [{default_out}]: ", default_out)

    # Formato de salida
    formats = ["JPG", "JPEG", "PNG", "TIFF"]
    print(Fore.CYAN + "Seleccione el formato de salida:" + Style.RESET_ALL)
    for i, f in enumerate(formats, start=1):
        print(Fore.CYAN + f"{i}. {f}" + Style.RESET_ALL)
    format_choice = int(get_input(f"Seleccione una opción [por defecto {len(formats)}]: ", str(len(formats)))) - 1
    output_format = formats[format_choice]

    # Opciones específicas de compresión
    quality, compression_opts, png_compress = 70, None, 6
    if output_format in ["JPG", "JPEG"]:
        q_in = get_input("Ingrese nivel de calidad (1-100) [70]: ", "70")
        try: quality = max(1, min(100, int(q_in)))
        except: quality = 70
    elif output_format == "TIFF":
        tiff_opts = ["none", "lzw", "zip", "jpeg"]
        print(Fore.CYAN + "Seleccione el tipo de compresión TIFF:" + Style.RESET_ALL)
        for i, t in enumerate(tiff_opts, start=1):
            print(Fore.CYAN + f"{i}. {t}" + Style.RESET_ALL)
        t_choice = int(get_input("Seleccione una opción [por defecto 1]: ", "1")) - 1
        compression_opts = None if tiff_opts[t_choice] == 'none' else tiff_opts[t_choice]
    elif output_format == "PNG":
        p_in = get_input("Nivel de compresión PNG (0-9, 0 = sin compresión) [6]: ", "6")
        try: png_compress = max(0, min(9, int(p_in)))
        except: png_compress = 6

    # Tamaño límite
    size_limit = int(get_input("Tamaño límite en KB (0 para todas) [0]: ", "0"))

    # NUEVAS PREGUNTAS v3.5
    copy_large = get_input("¿Qué hacer con archivos que superan el límite? (1. Copiar  2. No hacer nada) [2]: ", "2")
    copy_large = (copy_large == "1")

    copy_others = get_input("¿Qué hacer con archivos no procesables? (1. Copiar  2. No hacer nada) [2]: ", "2")
    copy_others = (copy_others == "1")

    # Número de procesos
    max_procs = os.cpu_count() or 1
    procs_in = get_input(f"Número de procesos a usar (1 = secuencial, máx {max_procs}) [1]: ", "1")
    try: num_procs = max(1, min(max_procs, int(procs_in)))
    except: num_procs = 1

    # Resumen
    print("\nResumen de opciones elegidas:")
    print(f"Directorio origen: {input_dir}")
    print(f"Directorio destino: {output_dir}")
    print(f"Formato de salida: {output_format}")
    if output_format in ["JPG", "JPEG"]:
        print(f"Calidad JPG: {quality}")
    elif output_format == "TIFF":
        print(f"Compresión TIFF: {compression_opts if compression_opts else 'none'}")
    elif output_format == "PNG":
        print(f"Compresión PNG: {png_compress}")
    print(f"Tamaño límite (KB): {size_limit}")
    print(f"Copiar archivos grandes: {'Sí' if copy_large else 'No'}")
    print(f"Copiar archivos no procesables: {'Sí' if copy_others else 'No'}")
    print(f"Procesos a utilizar: {num_procs}")

    confirm = get_input("¿Desea continuar? (s/n) [s]: ", "s")
    if confirm.lower() != "s":
        print("Proceso cancelado.")
        sys.exit(0)

    # =============
    # Ejecución
    # =============
    start_time = time.time()
    processed, skipped, errors, copied_large, copied_others = 0, 0, 0, 0, 0

    for f in images:
        result, fpath = process_single_image(f, output_format, output_dir, size_limit, quality, compression_opts, png_compress)
        if result is True:
            processed += 1
            logging.info(f"Procesado correctamente: {fpath}")
        elif result is False:
            skipped += 1
            logging.info(f"Saltado por tamaño: {fpath}")
            if copy_large:
                rel_path = os.path.relpath(fpath, start=input_dir)
                new_path = os.path.join(output_dir, rel_path)
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                shutil.copy2(fpath, new_path)
                copied_large += 1
                logging.info(f"Copiado sin procesar (grande): {fpath}")
        else:
            errors += 1
            logging.error(f"Error procesando archivo: {fpath}")

    if copy_others:
        for f in others:
            rel_path = os.path.relpath(f, start=input_dir)
            new_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            shutil.copy2(f, new_path)
            copied_others += 1
            logging.info(f"Copiado archivo no procesable: {f}")

    elapsed = time.time() - start_time
    print(f"Proceso finalizado. Procesados: {processed}, Saltados: {skipped}, Copiados grandes: {copied_large}, Copiados no procesables: {copied_others}, Errores: {errors}. Tiempo: {elapsed:.2f}s")
    print(f"Registro detallado en: {log_file}")

    logging.info(f"Resumen final -> Procesados: {processed}, Saltados: {skipped}, Copiados grandes: {copied_large}, Copiados no procesables: {copied_others}, Errores: {errors}")
    logging.info(f"Tiempo total: {elapsed:.2f}s")

if __name__ == "__main__":
    main()
