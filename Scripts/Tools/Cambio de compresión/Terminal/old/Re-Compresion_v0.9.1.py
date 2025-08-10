"""
Nombre del Programa: Re-Compresion
Versión: 0.10
Fecha: 25 de julio de 2024
Correo electrónico: carlymx@gmail.com

Descripción:
Este script permite cambiar el tipo de compresión de una lista de archivos comprimidos en un directorio especificado.
1. Detecta el sistema operativo.
2. Pide un directorio a analizar.
3. Analiza el directorio y muestra la cantidad de archivos comprimidos que contiene y en qué formatos (.zip, .7z, .tar.gz, .rar).
4. Pide en qué formato quieres recomprimir los archivos (1: .zip, 2: .7z, 3: .tar.gz, 4: .rar).
5. Pide el nivel de compresión (Entre 0, ninguna compresión y 10, máxima compresión). Por defecto 5.
6. Muestra lo que va a hacer y pide confirmación.
7. Descomprime cada archivo en un directorio temporal dentro del directorio asignado y luego recomprime manteniendo el mismo nombre y propiedades de archivos. Mientras lo hace, muestra al usuario el archivo con el que está trabajando, el % parcial y el % total de los archivos a procesar.
8. Muestra información final del proceso, si ha habido errores y demás información relevante.
9. Pregunta al usuario qué hacer con los archivos originales después de procesarlos (1: Eliminarlos, 2: Moverlos a un directorio "backup", 3: Mantenerlos en su sitio. Por defecto: Moverlos al directorio).
"""

import os
import shutil
import zipfile
import tarfile
import tempfile
import subprocess
import sys
import platform
import logging

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Detección del sistema operativo
OPERATING_SYSTEM = platform.system()
logging.info(f"Sistema operativo detectado: {OPERATING_SYSTEM}")

def check_and_install_dependencies():
    try:
        import py7zr
    except ImportError:
        logging.info("py7zr no está instalado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "py7zr"])

    try:
        import rarfile
    except ImportError:
        logging.info("rarfile no está instalado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rarfile"])

def check_rar_availability():
    if OPERATING_SYSTEM == 'Windows':
        rar_command = r"C:\Program Files\WinRAR\Rar.exe"
    else:
        rar_command = 'rar'

    if shutil.which(rar_command) is None:
        logging.warning("No se encontró el comando RAR. La compresión a formato RAR no estará disponible.")
        logging.warning("Por favor, instala WinRAR (en Windows) o el paquete 'rar' (en Linux) si deseas usar esta función.")
        return False
    return True

def get_compressed_files(directory):
    compressed_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.zip', '.7z', '.tar.gz', '.rar')):
                compressed_files.append(os.path.join(root, file))
    return compressed_files

def decompress_file(file_path, temp_dir):
    import py7zr
    import rarfile

    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
    elif file_path.endswith('.tar.gz'):
        with tarfile.open(file_path, 'r:gz') as tar_ref:
            tar_ref.extractall(temp_dir)
    elif file_path.endswith('.7z'):
        with py7zr.SevenZipFile(file_path, mode='r') as seven_zip:
            seven_zip.extractall(temp_dir)
    elif file_path.endswith('.rar'):
        with rarfile.RarFile(file_path, 'r') as rar_ref:
            rar_ref.extractall(temp_dir)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

def compress_files(temp_dir, output_path, format, compression_level):
    import py7zr
    if format == 'zip':
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zip_ref:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    zip_ref.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir))
    elif format == 'tar.gz':
        with tarfile.open(output_path, 'w:gz') as tar_ref:
            tar_ref.add(temp_dir, arcname=os.path.basename(temp_dir))
    elif format == '7z':
        with py7zr.SevenZipFile(output_path, 'w', filters=[{"id": py7zr.FILTER_LZMA2, "preset": compression_level}]) as seven_zip:
            seven_zip.writeall(temp_dir, os.path.basename(temp_dir))
    elif format == 'rar':
        if OPERATING_SYSTEM == 'Windows':
            rar_command = r"C:\Program Files\WinRAR\Rar.exe"
        else:
            rar_command = 'rar'

        if shutil.which(rar_command) is None:
            raise FileNotFoundError(f"No se pudo encontrar el comando RAR. Asegúrate de que RAR esté instalado y en el PATH del sistema.")

        subprocess.check_call([rar_command, 'a', '-m{}'.format(compression_level), output_path] +
                              [os.path.join(root, file) for root, dirs, files in os.walk(temp_dir) for file in files])
    else:
        raise ValueError(f"Unsupported compression format: {format}")

def handle_original_files(file, action, backup_dir):
    if action == '1':
        os.remove(file)
    elif action == '2':
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        shutil.move(file, backup_dir)
    elif action == '3':
        pass
    else:
        shutil.move(file, backup_dir)

def main():
    # Verificar e instalar dependencias
    check_and_install_dependencies()
    import py7zr  # Importar py7zr después de la instalación
    import rarfile  # Importar rarfile después de la instalación

    # Verificar disponibilidad de RAR
    rar_available = check_rar_availability()

    # 1. Pedir el directorio a analizar
    directory = input("Introduce el directorio a analizar: ")

    # 2. Analizar el directorio y mostrar la cantidad de archivos comprimidos y sus formatos
    compressed_files = get_compressed_files(directory)
    file_formats = {'.zip': 0, '.tar.gz': 0, '.7z': 0, '.rar': 0}

    for file in compressed_files:
        for format in file_formats:
            if file.endswith(format):
                file_formats[format] += 1

    logging.info(f"Archivos encontrados: {len(compressed_files)}")
    for format, count in file_formats.items():
        logging.info(f"{format}: {count}")

    # 3. Pedir el formato de recompresión deseado
    print("Selecciona el formato de recompresión deseado:")
    print("1: .zip")
    print("2: .7z")
    print("3: .tar.gz")
    print("4: .rar")
    format_option = input("Introduce el número correspondiente al formato (1/2/3/4): ")
    format_map = {'1': 'zip', '2': '7z', '3': 'tar.gz', '4': 'rar'}
    recompression_format = format_map.get(format_option, 'zip')

    if recompression_format == 'rar' and not rar_available:
        logging.warning("RAR no está disponible. Por favor, elige otro formato.")
        return

    # 4. Pedir el nivel de compresión
    compression_level = input("Introduce el nivel de compresión (0-10, por defecto 5): ")
    compression_level = int(compression_level) if compression_level else 5

    # 5. Mostrar lo que va a hacer y pedir confirmación
    logging.info(f"Recomprimir {len(compressed_files)} archivos a formato {recompression_format} con nivel de compresión {compression_level}")
    confirm = input("¿Deseas continuar? (s/n): ")
    if confirm.lower() != 's':
        logging.info("Operación cancelada.")
        return

    # 6. Preguntar qué hacer con los archivos originales
    original_action = input("¿Qué quieres hacer con los archivos originales después de procesarlos? (1: Eliminarlos, 2: Moverlos a un directorio 'backup', 3: Mantenerlos en su sitio. Por defecto: 2): ")
    original_action = original_action if original_action in ['1', '2', '3'] else '2'
    backup_dir = os.path.join(directory, "backup")

    # 7. Descomprimir y recomprimir los archivos
    temp_root = tempfile.mkdtemp(dir=directory)
    total_files = len(compressed_files)
    processed_files = 0

    for file in compressed_files:
        logging.info(f"Procesando archivo: {file}")
        temp_dir = tempfile.mkdtemp(dir=temp_root)
        try:
            decompress_file(file, temp_dir)
            base_name = os.path.splitext(file)[0]
            if file.endswith('.tar.gz'):
                base_name = os.path.splitext(base_name)[0]  # Remove .tar part
            output_path = base_name + '.' + recompression_format
            compress_files(temp_dir, output_path, recompression_format, compression_level)
            handle_original_files(file, original_action, backup_dir)
            processed_files += 1
        except Exception as e:
            logging.error(f"Error procesando {file}: {str(e)}")
        finally:
            shutil.rmtree(temp_dir)

        logging.info(f"Progreso: {processed_files}/{total_files} archivos procesados ({(processed_files/total_files) * 100:.2f}%)")

    # 8. Mostrar información final del proceso
    logging.info("Proceso completado.")
    logging.info(f"Archivos procesados: {processed_files}")
    if processed_files != total_files:
        logging.warning(f"Errores encontrados: {total_files - processed_files}")

    shutil.rmtree(temp_root)

if __name__ == "__main__":
    main()
