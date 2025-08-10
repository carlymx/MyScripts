##################################################################
#                   COMPRESOR DE FOTOGRAFÍAS                     #
#                    V2.2 (10 AGOSTO 2025)                       #
#             Carlos Hernández - carlymx@gmail.com               #
#                                                                #
#                                                                #
##################################################################

import os
import shutil
import sys
import subprocess
import platform
from datetime import datetime
import logging

def setup_virtualenv_and_install():
    if not os.path.exists("venv"):
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
    python_exec = os.path.join("venv", "Scripts" if platform.system() == "Windows" else "bin", "python")
    subprocess.check_call([python_exec, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([python_exec, "-m", "pip", "install", "Pillow", "piexif"])
    return python_exec

def ensure_dependencies():
    # Fuerza entorno virtual en Linux para evitar PEP 668
    if platform.system() == "Linux" and not os.path.exists("venv"):
        print("Creando entorno virtual en el directorio de ejecución...")
        python_exec = setup_virtualenv_and_install()
        os.execv(python_exec, [python_exec] + sys.argv)
    try:
        import PIL
        import piexif
    except ImportError:
        print("Instalando dependencias en un entorno virtual (venv)...")
        python_exec = setup_virtualenv_and_install()
        os.execv(python_exec, [python_exec] + sys.argv)

def setup_logger(log_file):
    logger = logging.getLogger('image_processor')
    logger.setLevel(logging.INFO)
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
    value = input(prompt)
    return value if value else default

def safe_exif_dump(exif_dict):
    import piexif
    new_exif = {}
    for ifd in exif_dict:
        if ifd == "thumbnail":
            new_exif[ifd] = exif_dict[ifd]
            continue
        new_exif[ifd] = {}
        for tag, value in exif_dict[ifd].items():
            try:
                piexif.dump({ifd: {tag: value}})
                new_exif[ifd][tag] = value
            except:
                if isinstance(value, int):
                    new_exif[ifd][tag] = str(value).encode()
    return piexif.dump(new_exif)

def detect_os():
    os_name = platform.system()
    print(f"Sistema operativo detectado: {os_name}")
    return os_name

def scan_directory(src_dir):
    file_types = {}
    for root, _, files in os.walk(src_dir):
        for file in files:
            ext = file.lower().split('.')[-1]
            file_types[ext] = file_types.get(ext, 0) + 1
    return file_types

def choose_option(prompt, options, default_index=0):
    print(prompt)
    for idx, opt in enumerate(options, start=1):
        print(f"{idx}. {opt}")
    choice = get_input(f"Seleccione una opción [por defecto {default_index+1}]: ", str(default_index+1))
    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(options):
            return options[choice_idx]
    except ValueError:
        pass
    return options[default_index]

def process_images(src_dir, dest_dir, size_limit, output_format, compression_opts, logger):
    from PIL import Image
    import piexif
    valid_exts = tuple(["." + e for e in ["jpg", "jpeg", "png", "tiff", "bmp", "gif", "raw", "nef", "cr2", "arw"]])
    files_list = [os.path.join(root, f) for root, _, files in os.walk(src_dir) for f in files if f.lower().endswith(valid_exts)]
    total_files = len(files_list)
    processed_files = 0
    large_files = 0
    errors = 0

    logger.info(f"Archivos totales encontrados: {total_files}")

    for idx, file_path in enumerate(files_list, start=1):
        try:
            file_size = os.path.getsize(file_path) / 1024
            if file_size > size_limit:
                large_files += 1

            rel_path = os.path.relpath(os.path.dirname(file_path), src_dir)
            dest_subdir = os.path.join(dest_dir, rel_path)
            os.makedirs(dest_subdir, exist_ok=True)

            new_filename = os.path.splitext(os.path.basename(file_path))[0] + "." + output_format.lower()
            dest_path = os.path.join(dest_subdir, new_filename)

            with Image.open(file_path) as img:
                exif_data = piexif.load(img.info.get("exif", b"")) if "exif" in img.info else {}
                safe_exif = safe_exif_dump(exif_data) if exif_data else None

                save_params = {}
                if output_format.lower() == "tiff":
                    if compression_opts:
                        save_params["compression"] = compression_opts
                    else:
                        save_params["compression"] = None
                elif output_format.lower() in ["jpeg", "jpg"]:
                    save_params["quality"] = 90

                if safe_exif:
                    img.save(dest_path, format=output_format.upper(), exif=safe_exif, **save_params)
                else:
                    img.save(dest_path, format=output_format.upper(), **save_params)

            shutil.copystat(file_path, dest_path)
            processed_files += 1
            logger.info(f"Convertido: {file_path} -> {dest_path}")
        except Exception as e:
            logger.error(f"Error procesando {file_path}: {str(e)}")
            errors += 1
        print(f"\rProgreso: {idx}/{total_files} archivos procesados", end="")

    print("\nProceso finalizado.")
    logger.info(f"Total: {total_files}, Grandes: {large_files}, Procesados: {processed_files}, Errores: {errors}")
    return total_files, large_files, processed_files, errors

if __name__ == "__main__":
    detect_os()
    ensure_dependencies()

    src_dir = get_input("Ingrese el directorio a procesar: ")
    file_summary = scan_directory(src_dir)
    print("Resumen de archivos encontrados:")
    for ext, count in file_summary.items():
        print(f"{count} archivos en formato {ext.upper()}")

    default_dest = os.path.join(src_dir, "convertidos")
    dest_dir = get_input(f"Ingrese el directorio destino [{default_dest}]: ", default_dest)

    output_format = choose_option("Seleccione el formato de salida:", ["JPG", "JPEG", "PNG", "TIFF"], default_index=3)

    compression_opts = None
    if output_format == "TIFF":
        compression_opts = choose_option("Seleccione el tipo de compresión TIFF:", ["none", "lzw", "zip", "jpeg"], default_index=0)
        if compression_opts == "none":
            compression_opts = None
        else:
            compression_opts = compression_opts.upper()

    size_limit = float(get_input("Tamaño límite en KB (0 para todas) [0]: ", "0"))

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"image_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logger = setup_logger(log_file)

    total_files, large_files, processed_files, errors = process_images(src_dir, dest_dir, size_limit, output_format, compression_opts, logger)

    print(f"Total encontrados: {total_files}")
    print(f"Superan {size_limit} KB: {large_files}")
    print(f"Procesados: {processed_files}")
    print(f"Errores: {errors}")
    print(f"Registro en: {log_file}")

