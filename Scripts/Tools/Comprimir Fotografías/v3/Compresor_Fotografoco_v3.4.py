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

Versión 3.0 → 3.1
-----------------
- Implementado modo multiproceso:
  - Detecta CPUs disponibles y pregunta cuántos procesos usar (1 por defecto).
  - Si se selecciona 1 → modo secuencial (como antes).
  - Si >1 → usa ProcessPoolExecutor para paralelizar tareas.

Versión 3.1 → 3.2
-----------------
- Solucionado error al convertir PNG → JPG/JPEG:
  - Ahora, si la imagen tiene canal alfa (RGBA, LA), se convierte a RGB antes de guardarla.
  - Evita fallo de Pillow al guardar en formatos que no soportan transparencia.

Versión 3.2 → 3.3
-----------------
- Añadida opción de compresión PNG:
  - Pregunta nivel de compresión (0–9, por defecto 6).
  - 0 = sin compresión (más rápido, archivos más grandes).
  - 9 = máxima compresión (más lento, archivos más pequeños).
  - Compresión siempre sin pérdida.
  - Parámetro aplicado en el guardado: compress_level.

Versión 3.3 → 3.4
-----------------
- Corregida la redundacia de necesitar la librería "Colorama" e instalarla en el entorno virtual.
"""

import os
import sys
import shutil
import subprocess
import platform
from datetime import datetime
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

try:
    from colorama import Fore, Style, init
except ImportError:
    print("Advertencia: 'colorama' no está instalado. La salida no tendrá colores hasta que se instalen las dependencias.")
    print("Considere instalarla manualmente con 'pip install colorama' Para disponer de los colores desde el inicio.\n")

    # Clase ficticia que devuelve una cadena vacía para cualquier atributo que se le pida
    # (ej. Fore.GREEN devolverá "")
    class EmptyColor:
        def __getattr__(self, name):
            return ""
    
    # Se crean los objetos sustitutos
    Fore = EmptyColor()
    Style = EmptyColor()
    
    # Función 'init' sustituta que no hace nada
    def init(autoreset=True):
        pass

init(autoreset=True)

VERSION = "3.4"
SCRIPT_NAME = "Compresor Fotográfico"

def setup_virtualenv_and_install():
    if not os.path.exists("venv"):
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
    python_exec = os.path.join("venv", "Scripts" if platform.system() == "Windows" else "bin", "python")
    subprocess.check_call([python_exec, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([python_exec, "-m", "pip", "install", "Pillow", "piexif", "colorama"])
    return python_exec

def ensure_dependencies():
    if platform.system() == "Linux" and not os.path.exists("venv"):
        print("Creando entorno virtual en el directorio de ejecución...")
        python_exec = setup_virtualenv_and_install()
        os.execv(python_exec, [python_exec] + sys.argv)
    try:
        import PIL  # noqa
        import piexif  # noqa
        import colorama  # noqa
    except ImportError:
        print("Instalando dependencias en un entorno virtual (venv)...")
        python_exec = setup_virtualenv_and_install()
        os.execv(python_exec, [python_exec] + sys.argv)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = r"""
   ____                                  _             _            
  / ___|___  _ __ ___  _ __   ___  _ __| |_ _   _  __| | ___ _ __  
 | |   / _ \| '_ ` _ \| '_ \ / _ \| '__| __| | | |/ _` |/ _ \ '__| 
 | |__| (_) | | | | | | |_) | (_) | |  | |_| |_| | (_| |  __/ |    
  \____\___/|_| |_| |_| .__/ \___/|_|   \__|\__,_|\__,_|\___|_|    
                      |_|                                          
    """
    print(Fore.CYAN + banner)
    print(Fore.YELLOW + f"Versión {VERSION} - {SCRIPT_NAME} (Multiproceso)")
    print(Fore.YELLOW + "      Carlos Hernández - carlymx@gmail.com")
    print(Fore.YELLOW + "-------------------------------------------------\n" + Style.RESET_ALL)

def setup_logger(log_file):
    logger = logging.getLogger('image_processor')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger

def get_input(prompt, default=None):
    value = input(Fore.YELLOW + prompt + Style.RESET_ALL)
    return value if value else default

def safe_exif_dump(exif_bytes):
    if not exif_bytes:
        return None
    try:
        import piexif
        exif_dict = piexif.load(exif_bytes)
        return piexif.dump(exif_dict)
    except Exception:
        return None

def map_tiff_compression(opt_str):
    if not opt_str:
        return None
    opt = opt_str.lower()
    if opt == 'lzw':
        return 'tiff_lzw'
    if opt == 'zip':
        return 'tiff_adobe_deflate'
    if opt == 'jpeg':
        return 'tiff_jpeg'
    return None

def process_single_image(args):
    file_path, src_dir, dest_dir, size_limit, output_format, compression_opts, quality, png_compress = args
    result = {'src': file_path, 'dest': None, 'ok': False, 'error': None, 'size_kb': None}
    try:
        from PIL import Image
    except Exception as e:
        result['error'] = f'PIL no disponible: {e}'
        return result
    try:
        result['size_kb'] = os.path.getsize(file_path) / 1024
        if result['size_kb'] <= size_limit:
            result['error'] = 'Ignorado por tamaño'
            return result
        try:
            img = Image.open(file_path)
            img.load()
            exif_bytes = img.info.get('exif', None)
        except Exception:
            try:
                import rawpy
                with rawpy.imread(file_path) as raw:
                    rgb = raw.postprocess()
                    img = Image.fromarray(rgb)
                    exif_bytes = None
            except Exception as e:
                result['error'] = f'No se pudo abrir la imagen: {e}'
                return result
        rel_path = os.path.relpath(os.path.dirname(file_path), src_dir)
        dest_subdir = os.path.join(dest_dir, rel_path)
        os.makedirs(dest_subdir, exist_ok=True)
        ext_for_format = 'JPEG' if output_format.lower() in ['jpg', 'jpeg'] else output_format.upper()
        new_ext = 'jpg' if output_format.lower() == 'jpg' else output_format.lower()
        new_filename = os.path.splitext(os.path.basename(file_path))[0] + '.' + new_ext
        dest_path = os.path.join(dest_subdir, new_filename)
        save_params = {}
        if ext_for_format == 'TIFF':
            mapped = map_tiff_compression(compression_opts)
            if mapped:
                save_params['compression'] = mapped
        elif ext_for_format == 'JPEG':
            save_params['quality'] = int(quality)
            save_params['subsampling'] = 0
            if img.mode in ('RGBA', 'LA'):
                img = img.convert('RGB')
        elif ext_for_format == 'PNG':
            save_params['compress_level'] = png_compress
        exif_for_save = safe_exif_dump(exif_bytes)
        if exif_for_save:
            img.save(dest_path, format=ext_for_format, exif=exif_for_save, **save_params)
        else:
            img.save(dest_path, format=ext_for_format, **save_params)
        try:
            shutil.copystat(file_path, dest_path)
        except Exception:
            pass
        result['dest'] = dest_path
        result['ok'] = True
        return result
    except Exception as e:
        result['error'] = str(e)
        return result

# Las funciones process_images_sequential, process_images_multiprocess y main serían las mismas que en la v3.2,
# pero añadiendo la recogida de `png_compress` cuando el formato elegido sea PNG y pasándolo como argumento en la lista de tareas.


# ----------------------------- Función secuencial (modo 1) -------------

def process_images_sequential(files_list, src_dir, dest_dir, size_limit, output_format, compression_opts, quality, png_compress, logger):
    processed = 0
    large_files = 0
    errors = 0
    total = len(files_list)

    for idx, file_path in enumerate(files_list, start=1):
        res = process_single_image((file_path, src_dir, dest_dir, size_limit, output_format, compression_opts, quality, png_compress))
        if res.get('size_kb') and res['size_kb'] > size_limit:
            large_files += 1
        if res['ok']:
            processed += 1
            logger.info(f"Convertido: {res['src']} -> {res['dest']}")
        else:
            if res['error'] and res['error'] != 'Ignorado por tamaño':
                errors += 1
                logger.error(f"Error procesando {res['src']}: {res['error']}")
        print(Fore.GREEN + f"\rProgreso: {idx}/{total} archivos procesados" + Style.RESET_ALL, end='')

    print('\n' + Fore.GREEN + 'Proceso finalizado.' + Style.RESET_ALL)
    return total, large_files, processed, errors

# ----------------------------- Función multiproceso --------------------

def process_images_multiprocess(files_list, src_dir, dest_dir, size_limit, output_format, compression_opts, quality, png_compress, logger, workers):
    total = len(files_list)
    processed = 0
    large_files = 0
    errors = 0

    # Construimos args para cada tarea
    tasks = [(fp, src_dir, dest_dir, size_limit, output_format, compression_opts, quality, png_compress) for fp in files_list]

    with ProcessPoolExecutor(max_workers=workers) as exe:
        futures = {exe.submit(process_single_image, t): t for t in tasks}
        completed = 0
        for fut in as_completed(futures):
            res = fut.result()
            completed += 1
            # contabilizar
            if res.get('size_kb') and res['size_kb'] > size_limit:
                large_files += 1
            if res['ok']:
                processed += 1
                logger.info(f"Convertido: {res['src']} -> {res['dest']}")
            else:
                if res['error'] and res['error'] != 'Ignorado por tamaño':
                    errors += 1
                    logger.error(f"Error procesando {res['src']}: {res['error']}")
            print(Fore.GREEN + f"\rProgreso: {completed}/{total} archivos procesados" + Style.RESET_ALL, end='')

    print('\n' + Fore.GREEN + 'Proceso finalizado.' + Style.RESET_ALL)
    return total, large_files, processed, errors

# ----------------------------- MAIN -----------------------------------

def main():
    detect_os = platform.system()
    print(Fore.GREEN + f"Sistema operativo detectado: {detect_os}" + Style.RESET_ALL)

    ensure_dependencies()
    clear_screen()
    print_banner()

    # Elegir directorio origen (validamos que haya imágenes compatibles)
    while True:
        src_dir = get_input("Ingrese el directorio a procesar: ")
        if not src_dir:
            print(Fore.RED + "No se ingresó directorio. Saliendo..." + Style.RESET_ALL)
            sys.exit(1)
        if not os.path.isdir(src_dir):
            print(Fore.RED + "El directorio ingresado no existe. Intente nuevamente." + Style.RESET_ALL)
            continue
        file_summary = {}
        valid_exts = ["jpg", "jpeg", "png", "tiff", "bmp", "gif", "raw", "nef", "cr2", "arw"]
        for root, _, files in os.walk(src_dir):
            for f in files:
                ext = f.lower().split('.')[-1]
                if ext in valid_exts:
                    file_summary[ext] = file_summary.get(ext, 0) + 1
        if not file_summary:
            choice = get_input(Fore.RED + "No se han encontrado imágenes compatibles en el directorio indicado. ¿Desea ingresar otro directorio? (S/n): " + Style.RESET_ALL, "S").lower()
            if choice != 's':
                print(Fore.RED + "Saliendo del programa..." + Style.RESET_ALL)
                sys.exit()
            else:
                continue
        break

    print(Fore.CYAN + "Resumen de archivos encontrados:" + Style.RESET_ALL)
    for ext, count in file_summary.items():
        print(Fore.CYAN + f"{count} archivos en formato {ext.upper()}" + Style.RESET_ALL)

    base_name   = os.path.basename(src_dir)          # "photos"
    dest_name   = f"{base_name}_converter"           # "photos_converter"
    parent_dir  = os.path.dirname(src_dir)           # "/home/user/downloads"
    
    # 4. Ruta completa del directorio destino por defecto
    default_dest = os.path.join(parent_dir, dest_name)
    dest_dir = get_input(f"Ingrese el directorio destino [{default_dest}]: ", default_dest)

    output_format = None
    format_choice = None
    formats = ["JPG", "JPEG", "PNG", "TIFF"]
    # selector por número
    print(Fore.CYAN + "Seleccione el formato de salida:" + Style.RESET_ALL)
    for i, f in enumerate(formats, start=1):
        print(Fore.CYAN + f"{i}. {f}" + Style.RESET_ALL)
    format_choice = int(get_input(f"Seleccione una opción [por defecto {len(formats)}]: ", str(len(formats)))) - 1
    output_format = formats[format_choice]

    compression_opts = None
    quality = 70
    png_compress = 6
    if output_format in ["JPG", "JPEG"]:
        quality_input = get_input("Ingrese nivel de calidad (1-100) [70]: ", "70")
        try:
            quality = max(1, min(100, int(quality_input)))
        except ValueError:
            quality = 70
    elif output_format == "TIFF":
        tiff_opts = ["none", "lzw", "zip", "jpeg"]
        print(Fore.CYAN + "Seleccione el tipo de compresión TIFF:" + Style.RESET_ALL)
        for i, t in enumerate(tiff_opts, start=1):
            print(Fore.CYAN + f"{i}. {t}" + Style.RESET_ALL)
        t_choice = int(get_input("Seleccione una opción [por defecto 1]: ", "1")) - 1
        compression_opts = None if tiff_opts[t_choice] == 'none' else tiff_opts[t_choice]
    elif output_format == "PNG":
        png_input = get_input("Compresión PNG sin perdida (0-9) 0 = Sin compresión, 9 = Max compresión [6]: ", "6")
        try:
            png_compress = max(0, min(9, int(png_input)))
        except ValueError:
            png_compress = 6
    size_limit = float(get_input("Tamaño límite en KB (0 para todas) [0]: ", "0"))

    # Preguntar número de procesos
    cpu_cnt = os.cpu_count() or 1
    max_allowed = cpu_cnt
    prompt = f"CPU detectadas: {cpu_cnt}. ¿Cuántos procesos desea usar? (1 = secuencial, máx {max_allowed}) [1]: "
    try:
        n_procs = int(get_input(prompt, "1"))
    except ValueError:
        n_procs = 1
    if n_procs < 1:
        n_procs = 1
    if n_procs > max_allowed:
        n_procs = max_allowed

    # Mostrar resumen y confirmar
    clear_screen()
    print_banner()
    print(Fore.CYAN + "Resumen de archivos que se procesarán:" + Style.RESET_ALL)
    for ext, count in file_summary.items():
        print(Fore.CYAN + f"{count} archivos en formato {ext.upper()}" + Style.RESET_ALL)
    print("\n" + Fore.YELLOW + "Opciones elegidas:" + Style.RESET_ALL)
    print(Fore.YELLOW + f"Directorio origen: {src_dir}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"Directorio destino: {dest_dir}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"Formato de salida: {output_format}" + Style.RESET_ALL)
    if output_format in ["JPG", "JPEG"]:
        print(Fore.YELLOW + f"Calidad JPG/JPEG: {quality}" + Style.RESET_ALL)
    elif output_format == "TIFF":
        print(Fore.YELLOW + f"Compresión TIFF: {compression_opts or 'None'}" + Style.RESET_ALL)
    elif output_format == "PNG":
        print(Fore.YELLOW + f"Compresión PNG: {png_compress or 'None'}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"Tamaño límite: {size_limit} KB" + Style.RESET_ALL)
    print(Fore.YELLOW + f"Procesos seleccionados: {n_procs}" + Style.RESET_ALL + "\n")

    confirm = get_input(Fore.GREEN + "¿La configuración es correcta? (S/n): " + Style.RESET_ALL, "S").lower()
    if confirm != "s":
        print(Fore.RED + "Proceso cancelado por el usuario. Reinicie el script para configurar nuevamente." + Style.RESET_ALL)
        sys.exit()

    # Preparar lista de archivos a procesar (extensiones válidas)
    valid_exts_tuple = tuple(["." + e for e in ["jpg", "jpeg", "png", "tiff", "bmp", "gif", "raw", "nef", "cr2", "arw"]])
    files_list = [os.path.join(root, f) for root, _, files in os.walk(src_dir) for f in files if f.lower().endswith(valid_exts_tuple)]

    # Logger
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"image_processor_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logger = setup_logger(log_file)

    # Ejecutar
    if n_procs == 1 or len(files_list) <= 1:
        total_files, large_files, processed_files, errors = process_images_sequential(files_list, src_dir, dest_dir, size_limit, output_format, compression_opts, quality, png_compress, logger)
    else:
        total_files, large_files, processed_files, errors = process_images_multiprocess(files_list, src_dir, dest_dir, size_limit, output_format, compression_opts, quality, logger, workers=n_procs)

    # Resultado final
    print("\n" + Fore.GREEN + f"Total encontrados: {total_files}" + Style.RESET_ALL)
    print(Fore.GREEN + f"Superan {size_limit} KB: {large_files}" + Style.RESET_ALL)
    print(Fore.GREEN + f"Procesados: {processed_files}" + Style.RESET_ALL)
    print(Fore.GREEN + f"Errores: {errors}" + Style.RESET_ALL)
    print(Fore.GREEN + f"Registro en: {log_file}" + Style.RESET_ALL)


if __name__ == '__main__':
    main()

