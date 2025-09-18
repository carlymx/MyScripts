#!/usr/bin/env python3
##################################################################
#                                                                #
#                   ORGANIZADOR DE FOTOGRAFÍAS                   #
#                    V1.1 (23 AGOSTO 2025)                       #
#             Carlos Hernández - carlymx@gmail.com               #
#                                                                #
##################################################################

import os
import sys
import shutil
import subprocess
import platform
from datetime import datetime
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
import locale
import re

# --- Configuración Inicial y Dependencias ---

# Importante para tener los nombres de los meses en el idioma local (ej: español)
try:
    # Para Linux/macOS
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8') 
except locale.Error:
    try:
        # Para Windows
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
    except locale.Error:
        # Fallback si los locales específicos no están disponibles
        locale.setlocale(locale.LC_TIME, '') 

try:
    from colorama import Fore, Style, init
except ImportError:
    print("Advertencia: 'colorama' no está instalado. Se procederá a instalarlo en un entorno virtual.")
    class EmptyColor:
        def __getattr__(self, name): return ""
    Fore = EmptyColor()
    Style = EmptyColor()
    def init(autoreset=True): pass

init(autoreset=True)

try:
    from PIL import Image
    import piexif
except ImportError:
    print("Advertencia: 'Pillow' o 'piexif' no están instalados. Se instalarán en el entorno virtual.")

VERSION = "1.1"
SCRIPT_NAME = "Organizador Fotográfico"

def setup_virtualenv_and_install():
    """Crea un entorno virtual e instala las dependencias necesarias."""
    if not os.path.exists("venv"):
        print(Fore.CYAN + "Creando entorno virtual 'venv'..." + Style.RESET_ALL)
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
    
    python_exec = os.path.join("venv", "Scripts" if platform.system() == "Windows" else "bin", "python")
    
    print(Fore.CYAN + "Instalando dependencias (Pillow, piexif, colorama)..." + Style.RESET_ALL)
    subprocess.check_call([python_exec, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([python_exec, "-m", "pip", "install", "Pillow", "piexif", "colorama"])
    return python_exec

def ensure_dependencies():
    """Asegura que las dependencias estén disponibles y reinicia el script en el venv si es necesario."""
    try:
        import PIL
        import piexif
        import colorama
    except ImportError:
        python_exec = setup_virtualenv_and_install()
        print(Fore.GREEN + "Dependencias instaladas. Reiniciando el script dentro del entorno virtual..." + Style.RESET_ALL)
        os.execv(python_exec, [python_exec] + sys.argv)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# text 2 ascii-art (big) url: https://patorjk.com/software/taag/
def print_banner():
    banner = r"""
   ____  _____   _____          _   _ _____ ______         
  / __ \|  __ \ / ____|   /\   | \ | |_   _|___  /   /\    
 | |  | | |__) | |  __   /  \  |  \| | | |    / /   /  \   
 | |  | |  _  /| | |_ | / /\ \ | . ` | | |   / /   / /\ \  
 | |__| | | \ \| |__| |/ ____ \| |\  |_| |_ / /__ / ____ \ 
  \____/|_| _\_\\_____/_/____\_\_|_\_|_____/_____/_/____\_\
 |_   _|  \/  |   /\   / ____|  ____| \ | |  ____|/ ____|  
   | | | \  / |  /  \ | |  __| |__  |  \| | |__  | (___    
   | | | |\/| | / /\ \| | |_ |  __| | . ` |  __|  \___ \   
  _| |_| |  | |/ ____ \ |__| | |____| |\  | |____ ____) |  
 |_____|_|  |_/_/    \_\_____|______|_| \_|______|_____/   
    """
    print(Fore.CYAN + banner)
    print(Fore.YELLOW + f"Versión {VERSION} - {SCRIPT_NAME} (Multiproceso)")
    print(Fore.YELLOW + f"      {__import__('datetime').date.today().strftime('%d de %B de %Y')}")
    print(Fore.YELLOW + "-------------------------------------------------\n" + Style.RESET_ALL)

# --- Lógica de Procesamiento ---

def get_date_from_filename(filename):
    """
    Intenta obtener la fecha de creación desde el nombre del archivo.
    Busca patrones como: IMG-20230811-WA0001.jpg, DSC_20230811_123456.jpg
    """
    basename = os.path.splitext(filename)[0]
    
    # Patrones para encontrar fechas YYYYMMDD o YYMMDD en nombres de archivo
    patterns = [
        # Busca YYYYMMDD (4 dígitos año + 2 mes + 2 día)
        r'(?:[A-Za-z0-9_-]*)(\d{4})(\d{2})(\d{2})(?:[A-Za-z0-9_-]*)',
        
        # También busca YYMMDD (2 dígitos año + 2 mes + 2 día)  
        r'(?:[A-Za-z0-9_-]*)(\d{2})(\d{2})(\d{2})(?:[A-Za-z0-9_-]*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, basename)
        if match:
            try:
                groups = match.groups()
                if len(groups) == 3:
                    # Verificar si es YYYYMMDD o YYMMDD
                    if len(groups[0]) == 4:  # YYYYMMDD
                        year, month, day = map(int, groups)
                    else:  # YYMMDD (2 dígitos para año)
                        year = int(groups[0]) + 2000  # Suponemos 2000-2099
                        month, day = map(int, groups[1:])
                    
                    # Validar que la fecha sea razonable
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        return datetime(year, month, day)
            except ValueError:
                continue
    
    return None

def organize_single_file(args):
    """
    Procesa un único archivo para obtener su fecha y copiarlo a la carpeta destino.
    """
    file_path, base_dest_dir = args
    result = {'src': file_path, 'dest': None, 'ok': False, 'error': None, 'date_source': None}
    
    file_date = None
    
    # 1. INTENTO 1: OBTENER FECHA DE METADATOS EXIF
    try:
        img = Image.open(file_path)
        exif_dict = piexif.load(img.info['exif'])
        date_str = exif_dict['Exif'][36867].decode('utf-8') # 36867 = DateTimeOriginal
        file_date = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        result['date_source'] = 'EXIF'
    except (AttributeError, KeyError, ValueError, IOError, SyntaxError):
        # Fallos comunes: no es imagen, no tiene EXIF, etiqueta no existe, etc.
        pass

    # 2. INTENTO 2: OBTENER FECHA DEL NOMBRE DEL ARCHIVO
    if not file_date:
        try:
            filename_date = get_date_from_filename(os.path.basename(file_path))
            if filename_date:
                file_date = filename_date
                result['date_source'] = 'Nombre'
        except Exception as e:
            pass  # Si falla, seguimos con el siguiente intento

    # 3. INTENTO 3: OBTENER FECHA DE MODIFICACIÓN DEL ARCHIVO (FALLBACK)
    if not file_date:
        try:
            mod_time = os.path.getmtime(file_path)
            file_date = datetime.fromtimestamp(mod_time)
            result['date_source'] = 'Archivo'
        except Exception as e:
            result['error'] = f"No se pudo obtener la fecha del archivo: {e}"
            return result

    # 4. CONSTRUIR RUTA DE DESTINO
    year = str(file_date.year)
    month_name = file_date.strftime('%m - %B').capitalize() # Ej: "08 - Agosto"
    dest_subdir = os.path.join(base_dest_dir, year, month_name)
    
    # 5. CREAR DIRECTORIOS
    os.makedirs(dest_subdir, exist_ok=True)
    
    # 6. COPIAR ARCHIVO
    try:
        dest_path = os.path.join(dest_subdir, os.path.basename(file_path))
        if os.path.exists(dest_path):
            result['error'] = "El archivo ya existe en el destino"
            return result
        
        shutil.copy2(file_path, dest_path) # copy2 preserva metadatos
        result['dest'] = dest_path
        result['ok'] = True
    except Exception as e:
        result['error'] = f"Error al copiar el archivo: {e}"
        
    return result

def run_organizer(files_list, dest_dir, workers, logger):
    """
    Ejecuta el proceso de organización de forma secuencial o en paralelo.
    """
    total = len(files_list)
    processed, errors, exif_count, file_date_count, filename_count = 0, 0, 0, 0, 0
    tasks = [(fp, dest_dir) for fp in files_list]

    if workers == 1:
        print(Fore.CYAN + "Iniciando proceso en modo secuencial..." + Style.RESET_ALL)
        for i, task in enumerate(tasks, 1):
            res = organize_single_file(task)
            if res['ok']:
                processed += 1
                logger.info(f"OK ({res['date_source']}): {res['src']} -> {res['dest']}")
                if res['date_source'] == 'EXIF': exif_count += 1
                elif res['date_source'] == 'Nombre': filename_count += 1
                else: file_date_count += 1
            else:
                errors += 1
                logger.error(f"Error procesando {res['src']}: {res['error']}")
            print(Fore.GREEN + f"\rProgreso: {i}/{total} archivos procesados" + Style.RESET_ALL, end='')
    else:
        print(Fore.CYAN + f"Iniciando proceso en paralelo con {workers} trabajadores..." + Style.RESET_ALL)
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(organize_single_file, t): t for t in tasks}
            completed = 0
            for future in as_completed(futures):
                completed += 1
                res = future.result()
                if res['ok']:
                    processed += 1
                    logger.info(f"OK ({res['date_source']}): {res['src']} -> {res['dest']}")
                    if res['date_source'] == 'EXIF': exif_count += 1
                    elif res['date_source'] == 'Nombre': filename_count += 1
                    else: file_date_count += 1
                else:
                    errors += 1
                    logger.error(f"Error procesando {res['src']}: {res['error']}")
                print(Fore.GREEN + f"\rProgreso: {completed}/{total} archivos procesados" + Style.RESET_ALL, end='')

    print('\n' + Fore.GREEN + 'Proceso finalizado.' + Style.RESET_ALL)
    return total, processed, errors, exif_count, file_date_count, filename_count

# --- Funciones de Utilidad y Principal ---

def setup_logger(log_file):
    logger = logging.getLogger('file_organizer')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

def get_input(prompt, default=None):
    value = input(Fore.YELLOW + prompt + Style.RESET_ALL)
    return value if value else default

def main():
    ensure_dependencies()
    clear_screen()
    print_banner()

    # 1. Directorio Origen
    while True:
        src_dir = get_input("Ingrese el directorio a organizar: ")
        if not os.path.isdir(src_dir):
            print(Fore.RED + "El directorio no existe. Intente nuevamente." + Style.RESET_ALL)
            continue
        
        print(Fore.CYAN + "Escaneando archivos, por favor espere..." + Style.RESET_ALL)
        files_list = [os.path.join(r, f) for r, _, fs in os.walk(src_dir) for f in fs]
        
        if not files_list:
            retry = get_input(Fore.RED + "No se encontraron archivos. ¿Probar con otro directorio? (S/n): " + Style.RESET_ALL, "S").lower()
            if retry != 's': sys.exit("Saliendo del programa.")
            else: continue
        break

    # 2. Directorio Destino
    default_dest = os.path.join(os.path.dirname(src_dir) or src_dir, f"{os.path.basename(os.path.abspath(src_dir))}_organizado")
    dest_dir = get_input(f"Ingrese el directorio destino [{default_dest}]: ", default_dest)

    # 3. Número de procesos
    cpu_count = os.cpu_count() or 1
    prompt = f"CPUs detectadas: {cpu_count}. ¿Cuántos procesos desea usar? (1 = secuencial, máx {cpu_count}) [1]: "
    try:
        n_procs = int(get_input(prompt, "1"))
        n_procs = max(1, min(cpu_count, n_procs))
    except ValueError:
        n_procs = 1

    # 4. Resumen y Confirmación
    clear_screen()
    print_banner()
    print(Fore.YELLOW + "--- Resumen de la Configuración ---" + Style.RESET_ALL)
    print(f"Directorio origen:    {src_dir}")
    print(f"Directorio destino:   {dest_dir}")
    print(f"Total de archivos:    {len(files_list)}")
    print(f"Procesos a utilizar:  {n_procs}")
    print(Fore.YELLOW + "-----------------------------------\n" + Style.RESET_ALL)
    
    confirm = get_input(Fore.GREEN + "¿La configuración es correcta? (S/n): " + Style.RESET_ALL, "S").lower()
    if confirm != "s":
        sys.exit("Proceso cancelado por el usuario.")

    # 5. Preparar Logger y Ejecutar
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"organizer_v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logger = setup_logger(log_file)
    
    total, processed, errors, exif, fallback, filename = run_organizer(files_list, dest_dir, n_procs, logger)

    # 6. Resultado Final
    print("\n" + Fore.GREEN + "--- Resultados Finales ---" + Style.RESET_ALL)
    print(f"Total de archivos encontrados: {total}")
    print(f"Procesados con éxito:        {processed}")
    print(f"  - Con fecha EXIF:          {exif}")
    print(f"  - Con fecha del nombre:    {filename}")
    print(f"  - Con fecha de archivo:    {fallback}")
    print(Fore.RED + f"Errores (ver log):           {errors}" + Style.RESET_ALL)
    print(Fore.CYAN + f"Registro detallado en:       {log_file}" + Style.RESET_ALL)

if __name__ == '__main__':
    main()

