################################################################################
#                _________ _____   _____ _____  _    _ _____                   #
#               |___  /_ _|  __ \ /  _  |  ___\| |  | |  __ \                  #
#                  / / | || |__) |\/  ) | |    | |__| | |  | |                 #
#                 / /  | ||  ___/    / /| |    |  __  | |  | |                 #
#                / /_ _| || |       / /_| |____| |  | | |__| |                 #
#               /____|____|_|      /____/_____/|_|  |_|_____/                  #
#                                                                              #
#                                    Zip2CHD                                   #
#                                Version: v0.2                                 #
#                                                                              #
#                           Date: 28 de julio de 2024                          #
#                           Email: carlymx@gmail.com                           #
#                                                                              #
################################################################################

import os
import sys
import platform
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import threading
import shutil
import tempfile
import zipfile

def check_and_install_dependencies():
    dependencies = ['py7zr']
    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            print(f"{dep} no está instalado. Instalando...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

check_and_install_dependencies()
import py7zr

class CHDConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("Zip2CHD Converter v0.2")
        master.geometry("800x600")
        master.resizable(False, False)

        self.os_type = platform.system()
        print(f"Sistema operativo detectado: {self.os_type}")

        self.input_directory = tk.StringVar(value=os.path.expanduser("~"))
        self.output_directory = tk.StringVar()
        self.original_action = tk.StringVar(value="Mover a 'ORIGINAL'")

        self.processing = False
        self.temp_dir = None

        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.master, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Input Directory
        tk.Label(main_frame, text="Directorio de entrada:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(main_frame, textvariable=self.input_directory, width=50).grid(row=0, column=1, pady=5)
        tk.Button(main_frame, text="Seleccionar", command=self.select_input_directory).grid(row=0, column=2, pady=5, padx=(10, 0))

        # Output Directory
        tk.Label(main_frame, text="Directorio de salida:").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(main_frame, textvariable=self.output_directory, width=50).grid(row=1, column=1, pady=5)
        tk.Button(main_frame, text="Seleccionar", command=self.select_output_directory).grid(row=1, column=2, pady=5, padx=(10, 0))

        # Action for original files
        tk.Label(main_frame, text="Archivos originales:").grid(row=2, column=0, sticky="w", pady=5)
        actions = ["Eliminar", "Mover a 'ORIGINAL'", "Mantener"]
        ttk.Combobox(main_frame, textvariable=self.original_action, values=actions, state="readonly").grid(row=2, column=1, sticky="ew", pady=5)

        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)

        self.start_button = tk.Button(button_frame, text="Iniciar proceso", command=self.start_process)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = tk.Button(button_frame, text="Cancelar", command=self.cancel_process, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.exit_button = tk.Button(button_frame, text="Salir", command=self.exit_program)
        self.exit_button.pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=400, mode="determinate")
        self.progress.grid(row=4, column=0, columnspan=3, pady=10, sticky="ew")

        # Terminal
        self.terminal = scrolledtext.ScrolledText(main_frame, width=105, height=20, font=("Courier New", 8), bg="#252525", fg="#24bc26")
        self.terminal.grid(row=5, column=0, columnspan=3, pady=10)


    def select_input_directory(self):
        directory = filedialog.askdirectory(initialdir=self.input_directory.get())
        if directory:
            self.input_directory.set(directory)
            self.output_directory.set(os.path.join(directory, "CHD"))
            self.temp_dir = os.path.join(directory, "temp")
            os.makedirs(self.temp_dir, exist_ok=True)
            self.show_cue_files()

    def select_output_directory(self):
        directory = filedialog.askdirectory(initialdir=self.output_directory.get())
        if directory:
            self.output_directory.set(directory)

    def show_cue_files(self):
        cue_files = self.get_cue_files(self.input_directory.get())
        info = f"Archivos .cue encontrados: {len(cue_files)}\n"
        for file in cue_files[:10]:  # Mostrar solo los primeros 10 archivos
            info += f"{file}\n"
        if len(cue_files) > 10:
            info += "...\n"
        self.log_to_terminal(info)

    def get_cue_files(self, directory):
        cue_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.cue'):
                    cue_files.append(os.path.join(root, file))
                elif file.endswith('.zip'):
                    cue_files.extend(self.list_cue_in_zip(os.path.join(root, file)))
                elif file.endswith('.7z'):
                    cue_files.extend(self.list_cue_in_7z(os.path.join(root, file)))
        return cue_files

    def list_cue_in_zip(self, zip_path):
        cue_files = []
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith('.cue'):
                    cue_files.append(f"{zip_path}:{file}")
        return cue_files

    def list_cue_in_7z(self, seven_zip_path):
        cue_files = []
        with py7zr.SevenZipFile(seven_zip_path, mode='r') as z:
            for file in z.getnames():
                if file.endswith('.cue'):
                    cue_files.append(f"{seven_zip_path}:{file}")
        return cue_files

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
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            self.master.quit()

    def process_files(self):
        self.log_to_terminal("Iniciando proceso de conversión a CHD...")
        cue_files = self.get_cue_files(self.input_directory.get())
        total_files = len(cue_files)
        processed_files = 0

        for cue_file in cue_files:
            if not self.processing:
                break
            try:
                self.log_to_terminal(f"Procesando archivo: {cue_file}")

                # Crear el directorio de salida si no existe
                os.makedirs(self.output_directory.get(), exist_ok=True)

                # Extraer el archivo .cue si está en un archivo comprimido
                if ':' in cue_file:
                    archive_path, internal_path = cue_file.split(':', 1)
                    cue_file = self.extract_file(archive_path, internal_path)

                # Generar el nombre del archivo de salida
                output_file = os.path.join(self.output_directory.get(), os.path.splitext(os.path.basename(cue_file))[0] + ".chd")

                # Convertir a CHD usando chdman
                chdman_path = self.get_chdman_path()
                result = subprocess.run([chdman_path, 'createcd', '-i', cue_file, '-o', output_file], capture_output=True, text=True)

                if result.returncode != 0:
                    raise Exception(f"Error en chdman: {result.stderr}")

                self.handle_original_files(cue_file)

                processed_files += 1
                progress = (processed_files / total_files) * 100
                self.update_progress(progress)
                self.log_to_terminal(f"Progreso: {processed_files}/{total_files} archivos procesados ({progress:.2f}%)")
            except Exception as e:
                self.log_to_terminal(f"Error al procesar {cue_file}: {str(e)}")

        # Limpiar directorio temporal
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def get_chdman_path(self):
        if self.os_type == "Windows":
            return "./MAME_tools/win/chdman.exe"
        else:  # Linux y otros sistemas
            return "./MAME_tools/linux/chdman"

    def extract_file(self, archive_path, internal_path):
        temp_file = os.path.join(self.temp_dir, os.path.basename(internal_path))
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extract(internal_path, self.temp_dir)
        elif archive_path.endswith('.7z'):
            with py7zr.SevenZipFile(archive_path, mode='r') as z:
                z.extract(self.temp_dir, [internal_path])
        return temp_file

    def update_progress(self, value):
        self.progress['value'] = value
        self.master.update_idletasks()

    def log_to_terminal(self, message):
        self.terminal.insert(tk.END, message + "\n")
        self.terminal.see(tk.END)

    def handle_original_files(self, file):
        action = self.original_action.get()
        if action == "Eliminar":
            os.remove(file)
            # También eliminar los archivos .bin asociados
            bin_files = [f for f in os.listdir(os.path.dirname(file)) if f.startswith(os.path.splitext(os.path.basename(file))[0]) and f.endswith('.bin')]
            for bin_file in bin_files:
                os.remove(os.path.join(os.path.dirname(file), bin_file))
        elif action == "Mover a 'ORIGINAL'":
            original_dir = os.path.join(os.path.dirname(file), "ORIGINAL")
            if not os.path.exists(original_dir):
                os.makedirs(original_dir)
            shutil.move(file, original_dir)
            # También mover los archivos .bin asociados
            bin_files = [f for f in os.listdir(os.path.dirname(file)) if f.startswith(os.path.splitext(os.path.basename(file))[0]) and f.endswith('.bin')]
            for bin_file in bin_files:
                shutil.move(os.path.join(os.path.dirname(file), bin_file), original_dir)
        elif action == "Mantener":
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = CHDConverterApp(root)
    root.mainloop()
