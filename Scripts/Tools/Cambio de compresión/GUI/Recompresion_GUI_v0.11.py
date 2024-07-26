"""
 ____                                               _              ____ _   _ ___
|  _ \ ___  ___ ___  _ __ ___  _ __  _ __ ___  ___ (_) ___  _ __  / ___| | | |_ _|
| |_) / _ \/ __/ _ \| '_ ` _ \| '_ \| '__/ _ \/ __|| |/ _ \| '_ \| |  _| | | || |
|  _ <  __/ (_| (_) | | | | | | |_) | | |  __/\__ \| | (_) | | | | |_| | |_| || |
|_| \_\___|\___\___/|_| |_| |_| .__/|_|  \___||___/|_|\___/|_| |_|\____|\___/|___|
                              |_|

Fecha: 26 de julio de 2024
Versión: v0.11
Email: carlymx@gmail.com
"""

import os
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import zipfile
import tarfile
import tempfile
import subprocess
import sys
import shutil
import threading
import platform
import logging

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Detección del sistema operativo
OPERATING_SYSTEM = platform.system()
logging.info(f"Sistema operativo detectado: {OPERATING_SYSTEM}")

# Variables globales para las rutas de RAR
RAR_PATH_WINDOWS = r"C:\Program Files\WinRAR\Rar.exe"
RAR_PATH_LINUX = None

def find_rar_linux():
    common_paths = [
        '/usr/bin/rar',
        '/usr/local/bin/rar',
        '/opt/rar/rar',
        '/usr/share/rar/rar'
    ]
    for path in common_paths:
        if os.path.isfile(path):
            return path
    return None

def check_rar_availability():
    global RAR_PATH_LINUX
    if OPERATING_SYSTEM == 'Windows':
        rar_command = RAR_PATH_WINDOWS
    else:
        RAR_PATH_LINUX = find_rar_linux()
        rar_command = RAR_PATH_LINUX or 'rar'
    
    if shutil.which(rar_command) is None:
        logging.warning("No se encontró el comando RAR. La compresión y descompresión en formato RAR no estarán disponibles.")
        if OPERATING_SYSTEM == 'Windows':
            logging.warning("Por favor, instala WinRAR y asegúrate de que esté en la ruta: " + RAR_PATH_WINDOWS)
        else:
            logging.warning("Por favor, instala el paquete 'rar' en tu sistema Linux.")
            logging.warning("Puedes hacerlo con: sudo apt-get install rar (para sistemas basados en Debian/Ubuntu)")
            logging.warning("O busca el paquete equivalente para tu distribución Linux.")
        return False
    logging.info(f"RAR encontrado en: {rar_command}")
    return True

def check_and_install_dependencies():
    # Verificar e instalar tkinter
    try:
        import tkinter
    except ImportError:
        print("Tkinter no está instalado. Intentando instalar...")
        if sys.platform.startswith('linux'):
            try:
                subprocess.check_call(["sudo", "apt-get", "install", "-y", "python3-tk"])
                print("Tkinter instalado correctamente.")
            except subprocess.CalledProcessError:
                print("No se pudo instalar Tkinter. Por favor, instálelo manualmente.")
                sys.exit(1)
        else:
            print("No se puede instalar Tkinter automáticamente en este sistema operativo. Por favor, instálelo manualmente.")
            sys.exit(1)

    # Verificar e instalar otras dependencias
    dependencies = ['py7zr', 'rarfile']
    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            print(f"{dep} no está instalado. Instalando...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

check_and_install_dependencies()
import py7zr
import rarfile

class ReCompresionApp:
    def __init__(self, master):
        self.master = master
        master.title("Re-Compresión v0.11")
        master.geometry("800x600")
        master.resizable(False, False)  # Tamaño fijo de ventana

        self.directory = tk.StringVar(value=os.path.expanduser("~"))  # Directorio HOME por defecto
        self.compression_format = tk.StringVar(value="zip")
        self.compression_level = tk.IntVar(value=5)
        self.original_action = tk.StringVar(value="Mover a 'BACKUP'")
        self.backup_dir_name = "BACKUP"  # Nombre del directorio de respaldo

        self.processing = False  # Flag para controlar si el proceso está en marcha

        self.create_widgets()

    def create_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self.master, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Directorio
        tk.Label(main_frame, text="Directorio:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(main_frame, textvariable=self.directory, width=50).grid(row=0, column=1, pady=5)
        tk.Button(main_frame, text="Seleccionar", command=self.select_directory).grid(row=0, column=2, pady=5, padx=(10, 0))

        # Formato de compresión
        tk.Label(main_frame, text="Formato de compresión:").grid(row=1, column=0, sticky="w", pady=5)
        formats = ["zip", "7z", "tar.gz", "rar"]
        ttk.Combobox(main_frame, textvariable=self.compression_format, values=formats, state="readonly").grid(row=1, column=1, sticky="ew", pady=5)

        # Nivel de compresión
        tk.Label(main_frame, text="Nivel de compresión:").grid(row=2, column=0, sticky="w", pady=5)
        tk.Scale(main_frame, from_=0, to=10, orient="horizontal", variable=self.compression_level).grid(row=2, column=1, columnspan=2, sticky="ew", pady=5)

        # Acción con archivos originales
        tk.Label(main_frame, text="Archivos originales:").grid(row=3, column=0, sticky="w", pady=5)
        actions = ["Eliminar", "Mover a 'BACKUP'", "Mantener"]
        ttk.Combobox(main_frame, textvariable=self.original_action, values=actions, state="readonly").grid(row=3, column=1, sticky="ew", pady=5)

        # Frame para botones
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)

        # Botones
        self.start_button = tk.Button(button_frame, text="Iniciar proceso", command=self.start_process)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = tk.Button(button_frame, text="Cancelar", command=self.cancel_process, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.exit_button = tk.Button(button_frame, text="Salir", command=self.exit_program)
        self.exit_button.pack(side=tk.LEFT, padx=5)

        # Barra de progreso
        self.progress = ttk.Progressbar(main_frame, length=400, mode="determinate")
        self.progress.grid(row=5, column=0, columnspan=3, pady=10, sticky="ew")

        # Terminal
        self.terminal = scrolledtext.ScrolledText(main_frame, width=92, height=15)
        self.terminal.grid(row=6, column=0, columnspan=3, pady=10)

        # Configurar el peso de las columnas
        main_frame.columnconfigure(1, weight=1)

    def select_directory(self):
        directory = filedialog.askdirectory(initialdir=self.directory.get())
        if directory:
            backup_dir = os.path.join(directory, self.backup_dir_name)
            if os.path.exists(backup_dir):
                self.handle_existing_backup_dir(directory, backup_dir)
            else:
                self.set_directory(directory)

    def handle_existing_backup_dir(self, directory, backup_dir):
        popup = tk.Toplevel(self.master)
        popup.title("Directorio de respaldo existente")
        popup.geometry("300x250")

        label = tk.Label(popup, text=f"El directorio '{self.backup_dir_name}' ya existe.\n¿Qué desea hacer?")
        label.pack(pady=10)

        def eliminate_dir():
            shutil.rmtree(backup_dir)
            popup.destroy()
            self.set_directory(directory)

        def rename_dir():
            suffix = 1
            while os.path.exists(f"{backup_dir}_{suffix:03d}"):
                suffix += 1
            os.rename(backup_dir, f"{backup_dir}_{suffix:03d}")
            popup.destroy()
            self.set_directory(directory)

        def cancel_selection():
            popup.destroy()

        tk.Button(popup, text="Eliminar Directorio", command=eliminate_dir).pack(fill='x', padx=50, pady=5)
        tk.Button(popup, text="Renombrar Directorio", command=rename_dir).pack(fill='x', padx=50, pady=5)
        tk.Button(popup, text="Seleccionar otro Directorio", command=cancel_selection).pack(fill='x', padx=50, pady=5)

    def set_directory(self, directory):
        self.directory.set(directory)
        self.show_compressed_files()

    def show_compressed_files(self):
        compressed_files = self.get_compressed_files(self.directory.get())
        file_formats = {'.zip': 0, '.tar.gz': 0, '.7z': 0, '.rar': 0}
        for file in compressed_files:
            for format in file_formats:
                if file.endswith(format):
                    file_formats[format] += 1

        info = f"Archivos encontrados: {len(compressed_files)}\n"
        for format, count in file_formats.items():
            info += f"{format}: {count}\n"

        self.log_to_terminal(info)

    def get_compressed_files(self, directory):
        compressed_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.zip', '.7z', '.tar.gz', '.rar')):
                    compressed_files.append(os.path.join(root, file))
        return compressed_files

    def start_process(self):
        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.exit_button.config(state=tk.DISABLED)
        threading.Thread(target=self.process_files, daemon=True).start()

    def cancel_process(self):
        self.processing = False
        self.log_to_terminal("Cancelando proceso...")
        self.cancel_button.config(state=tk.DISABLED)

    def exit_program(self):
        if messagebox.askokcancel("Salir", "¿Estás seguro de que quieres salir?"):
            self.master.quit()

    def process_files(self):
        self.log_to_terminal("Iniciando proceso de compresión...")
        compressed_files = self.get_compressed_files(self.directory.get())
        total_files = len(compressed_files)
        processed_files = 0

        temp_root = tempfile.mkdtemp(dir=self.directory.get())
        old_dir = os.path.join(self.directory.get(), self.backup_dir_name)

        for file in compressed_files:
            if not self.processing:
                break
            try:
                self.log_to_terminal(f"Procesando archivo: {file}")

                temp_dir = tempfile.mkdtemp(dir=temp_root)
                self.decompress_file(file, temp_dir)

                base_name = os.path.splitext(file)[0]
                if file.endswith('.tar.gz'):
                    base_name = os.path.splitext(base_name)[0]  # Remove .tar part

                output_path = base_name + '.' + self.compression_format.get()
                self.compress_files(temp_dir, output_path, self.compression_format.get(), self.compression_level.get())

                shutil.rmtree(temp_dir)

                self.handle_original_files(file, self.original_action.get(), old_dir)

                processed_files += 1
                progress = (processed_files / total_files) * 100
                self.update_progress(progress)
                self.log_to_terminal(f"Progreso: {processed_files}/{total_files} archivos procesados ({progress:.2f}%)")
            except Exception as e:
                self.log_to_terminal(f"Error al procesar {file}: {str(e)}")

        shutil.rmtree(temp_root)

        if self.processing:
            self.log_to_terminal(f"Proceso completado. {processed_files}/{total_files} archivos procesados.")
        else:
            self.log_to_terminal(f"Proceso cancelado. {processed_files}/{total_files} archivos procesados.")

        self.processing = False
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.exit_button.config(state=tk.NORMAL)

    def update_progress(self, value):
        self.progress['value'] = value
        self.master.update_idletasks()

    def log_to_terminal(self, message):
        self.terminal.insert(tk.END, message + "\n")
        self.terminal.see(tk.END)

    def decompress_file(self, file_path, temp_dir):
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
            if not check_rar_availability():
                raise ValueError("RAR no está disponible en el sistema. No se puede descomprimir el archivo.")
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(temp_dir)
        else:
            raise ValueError(f"Formato de archivo no soportado: {file_path}")

    def compress_files(self, temp_dir, output_path, format, compression_level):
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
            if not check_rar_availability():
                raise ValueError("RAR no está disponible en el sistema. No se puede comprimir en formato RAR.")
            
            rar_command = RAR_PATH_WINDOWS if OPERATING_SYSTEM == 'Windows' else (RAR_PATH_LINUX or 'rar')
            subprocess.check_call([rar_command, 'a', '-m{}'.format(compression_level), output_path] + 
                                  [os.path.join(root, file) for root, dirs, files in os.walk(temp_dir) for file in files])
        else:
            raise ValueError(f"Formato de compresión no soportado: {format}")

    def handle_original_files(self, file, action, old_dir):
        if action == "Eliminar":
            os.remove(file)
        elif action == "Mover a 'BACKUP'":
            if not os.path.exists(old_dir):
                os.makedirs(old_dir)
            shutil.move(file, old_dir)
        elif action == "Mantener":
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ReCompresionApp(root)
    root.mainloop()