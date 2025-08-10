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
    recompression_format = input("Introduce el formato de recompresión deseado (.zip .7z .tar.gz): ")

    # 4. Pedir el nivel de compresión
    compression_level = input("Introduce el nivel de compresión (0-10, por defecto 5): ")
    compression_level = int(compression_level) if compression_level else 5

    # 5. Mostrar lo que va a hacer y pedir confirmación
    print(f"Recomprimir {len(compressed_files)} archivos a formato {recompression_format} con nivel de compresión {compression_level}")
    confirm = input("¿Deseas continuar? (s/n): ")
    if confirm.lower() != 's':
        print("Operación cancelada.")
        return

    # 6. Descomprimir y recomprimir los archivos
    temp_root = tempfile.mkdtemp(dir=directory)
    total_files = len(compressed_files)
    processed_files = 0

    for file in compressed_files:
        print(f"Procesando archivo: {file}")
        temp_dir = tempfile.mkdtemp(dir=temp_root)
        decompress_file(file, temp_dir)
        output_path = os.path.splitext(file)[0] + recompression_format
        compress_files(temp_dir, output_path, recompression_format, compression_level)
        shutil.rmtree(temp_dir)

        processed_files += 1
        print(f"Progreso: {processed_files}/{total_files} archivos procesados ({(processed_files/total_files) * 100:.2f}%)")

    # 7. Mostrar información final del proceso
    print("Proceso completado.")
    print(f"Archivos procesados: {processed_files}")
    if processed_files != total_files:
        print(f"Errores encontrados: {total_files - processed_files}")

    shutil.rmtree(temp_root)

if __name__ == "__main__":
    main()
