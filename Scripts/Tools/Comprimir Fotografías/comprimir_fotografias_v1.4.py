##################################################################
#                   COMPRESOR DE FOTOGRAFÍAS                     #
#                     V1.4 (10 jULIO 2024)                       #
#                                                                #
# v1.4 (10 Julio 2024):                                          #
#   Agregada Función de Registro (LOG)                           #
# v1.3 (08 Julio 2024):                                          #
#   Agregado Progeso al procesar las Imagenes.                   #
#                                                                #
##################################################################

import os
import shutil
from PIL import Image
import piexif
import logging
from datetime import datetime

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

def process_images(src_dir, dest_dir, size_limit, compression_rate, logger):
    total_files = sum(len(files) for _, _, files in os.walk(src_dir) if any(f.lower().endswith(('.jpg', '.jpeg')) for f in files))
    processed_files = 0
    large_files = 0
    errors = 0

    logger.info(f"Iniciando procesamiento. Total de archivos: {total_files}")

    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg')):
                processed_files += 1
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path) / 1024  # Size in KB

                progress = (processed_files / total_files) * 100
                print(f"\rProgreso: {progress:.2f}% | Total: {total_files} | Procesados: {processed_files} | Errores: {errors}", end="")

                if file_size > size_limit:
                    large_files += 1
                    if compress_images:
                        try:
                            rel_path = os.path.relpath(root, src_dir)
                            dest_subdir = os.path.join(dest_dir, rel_path)
                            os.makedirs(dest_subdir, exist_ok=True)

                            new_filename = f"{os.path.splitext(file)[0]}_low{os.path.splitext(file)[1]}"
                            dest_path = os.path.join(dest_subdir, new_filename)

                            with Image.open(file_path) as img:
                                exif_data = piexif.load(img.info.get("exif", b""))
                                safe_exif = safe_exif_dump(exif_data)
                                img.save(dest_path, quality=compression_rate, exif=safe_exif)

                            shutil.copystat(file_path, dest_path)
                            logger.info(f"Archivo procesado: {file_path} -> {dest_path}")
                        except Exception as e:
                            logger.error(f"Error processing {file_path}: {str(e)}")
                            errors += 1

    print("\n")  # Nueva línea después de la barra de progreso
    logger.info(f"Procesamiento completado. Total: {total_files}, Procesados: {processed_files}, Errores: {errors}")
    return total_files, large_files, processed_files, errors

# Configuración del logger
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"image_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logger = setup_logger(log_file)

# Obtener entradas del usuario
src_dir = get_input("Ingrese el directorio a procesar: ")
dest_dir = get_input("Ingrese el directorio destino: ")
size_limit = float(get_input("Ingrese el tamaño límite en KB (por defecto 2048): ", "2048"))
compression_rate = int(get_input("Ingrese la tasa de compresión en % (por defecto 70): ", "70"))

# Preguntar si el usuario quiere comprimir las imágenes
compress_images = input("¿Desea guardar una copia comprimida de los archivos que superan el tamaño indicado? (s/n): ").lower() == 's'

# Procesar imágenes
print("\nIniciando procesamiento...")
logger.info("Iniciando procesamiento de imágenes")
total_files, large_files, processed_files, errors = process_images(src_dir, dest_dir, size_limit, compression_rate, logger)

# Imprimir resultados
print(f"Proceso terminado.")
print(f"Total de archivos encontrados: {total_files}")
print(f"Archivos que superan {size_limit} KB: {large_files}")
if compress_images:
    print(f"Archivos procesados: {processed_files}")
    print(f"Errores durante el procesamiento: {errors}")

logger.info(f"Proceso terminado. Total: {total_files}, Grandes: {large_files}, Procesados: {processed_files}, Errores: {errors}")
print(f"El registro completo está disponible en: {log_file}")
