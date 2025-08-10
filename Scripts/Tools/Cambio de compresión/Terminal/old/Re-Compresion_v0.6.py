"""
Nombre del Programa: Re-Compresion
Versión: 0.6
Fecha: 24 de julio de 2024
Correo electrónico: carlymx@gmail.com

Descripción:
Este script permite cambiar el tipo de compresión de una lista de archivos comprimidos en un directorio especificado.
1. Pide un directorio a analizar.
2. Analiza el directorio y muestra la cantidad de archivos comprimidos que contiene y en qué formatos (.zip, .7z, .tar.gz).
3. Pide en qué formato quieres recomprimir los archivos (1: .zip, 2: .7z, 3: .tar.gz).
4. Pide el nivel de compresión (Entre 0, ninguna compresión y 10, máxima compresión). Por defecto 5.
5. Muestra lo que va a hacer y pide confirmación.
6. Descomprime cada archivo en un directorio temporal dentro del directorio asignado y luego recomprime manteniendo el mismo nombre y propiedades de archivos. Mientras lo hace, muestra al usuario el archivo con el que está trabajando, el % parcial y el % total de los archivos a procesar.
7. Muestra información final del proceso, si ha habido errores y demás información relevante.
8. Pregunta al usuario qué hacer con los archivos originales después de procesarlos (1: Eliminarlos, 2: Moverlos a un directorio "OLD", 3: Mantenerlos en su sitio. Por defecto: Moverlos al directorio).
"""

import os
import shutil
import zipfile
import tarfile
import tempfile
import subprocess
import sys

def check_and_install_dependencies():
    try:
        import py7zr
    except ImportError:
        print("py7zr no está instalado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "py7zr"])

def get_compressed_files(directory):
    compressed_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.zip', '.7z', '.tar.gz')):
                compressed_files.append(os.path.join(root, file))
    return compressed_files

def decompress_file(file_path, temp_dir):
    import py7zr
    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
    elif file_path.endswith('.tar.gz'):
        with tarfile.open(file_path, 'r:gz') as tar_ref:
            tar_ref.extractall(temp_dir)
    elif file_path.endswith('.7z'):
        with py7zr.SevenZipFile(file_path, mode='r') as seven_zip:
            seven_zip.extractall(temp_dir)
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
    else:
        raise ValueError(f"Unsupported compression format: {format}")

def handle_original_files(file, action, old_dir):
    if action == '1':
        os.remove(file)
    elif action == '2':
        if not os.path.exists(old_dir):
            os.makedirs(old_dir)
        shutil.move(file, old_dir)
    elif action == '3':
        pass
    else:
        shutil.move(file, old_dir)

def main():
    # Verificar e instalar dependencias
    check_and_install_dependencies()
    import py7zr  # Importar py7zr después de la instalación

    # 1. Pedir el directorio a analizar
    directory = input("Introduce el directorio a analizar: ")

    # 2. Analizar el directorio y mostrar la cantidad de archivos comprimidos y sus formatos
    compressed_files = get_compressed_files(directory)
    file_formats = {'.zip': 0, '.tar.gz': 0, '.7z': 0}

    for file in compressed_files:
        for format in file_formats:
            if file.endswith(format):
                file_formats[format] += 1

    print(f"Archivos encontrados: {len(compressed_files)}")
    for format, count in file_formats.items():
        print(f"{format}: {count}")

    # 3. Pedir el formato de recompresión deseado
    print("Selecciona el formato de recompresión deseado:")
    print("1: .zip")
    print("2: .7z")
    print("3: .tar.gz")
    format_option = input("Introduce el número correspondiente al formato (1/2/3): ")
    format_map = {'1': 'zip', '2': '7z', '3': 'tar.gz'}
    recompression_format = format_map.get(format_option, 'zip')

    # 4. Pedir el nivel de compresión
    compression_level = input("Introduce el nivel de compresión (0-10, por defecto 5): ")
    compression_level = int(compression_level) if compression_level else 5

    # 5. Mostrar lo que va a hacer y pedir confirmación
    print(f"Recomprimir {len(compressed_files)} archivos a formato {recompression_format} con nivel de compresión {compression_level}")
    confirm = input("¿Deseas continuar? (s/n): ")
    if confirm.lower() != 's':
        print("Operación cancelada.")
        return

    # 6. Preguntar qué hacer con los archivos originales
    original_action = input("¿Qué quieres hacer con los archivos originales después de procesarlos? (1: Eliminarlos, 2: Moverlos a un directorio 'OLD', 3: Mantenerlos en su sitio. Por defecto: 2): ")
    original_action = original_action if original_action in ['1', '2', '3'] else '2'
    old_dir = os.path.join(directory, "OLD")

    # 7. Descomprimir y recomprimir los archivos
    temp_root = tempfile.mkdtemp(dir=directory)
    total_files = len(compressed_files)
    processed_files = 0

    for file in compressed_files:
        print(f"Procesando archivo: {file}")
        temp_dir = tempfile.mkdtemp(dir=temp_root)
        decompress_file(file, temp_dir)
        base_name = os.path.splitext(file)[0]
        output_path = base_name + '.' + recompression_format
        compress_files(temp_dir, output_path, recompression_format, compression_level)
        shutil.rmtree(temp_dir)

        handle_original_files(file, original_action, old_dir)

        processed_files += 1
        print(f"Progreso: {processed_files}/{total_files} archivos procesados ({(processed_files/total_files) * 100:.2f}%)")

    # 8. Mostrar información final del proceso
    print("Proceso completado.")
    print(f"Archivos procesados: {processed_files}")
    if processed_files != total_files:
        print(f"Errores encontrados: {total_files - processed_files}")

    shutil.rmtree(temp_root)

if __name__ == "__main__":
    main()
