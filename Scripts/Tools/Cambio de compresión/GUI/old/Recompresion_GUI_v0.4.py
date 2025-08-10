import os
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import zipfile
import tarfile
import tempfile
import subprocess
import sys
import shutil
import threading

def check_and_install_dependencies():
    # [Esta función se mantiene igual]
    pass

check_and_install_dependencies()
import py7zr
import rarfile

class ReCompresionApp:
    def __init__(self, master):
        self.master = master
        master.title("Re-Compresión v0.8")
        master.geometry("800x600")
        master.resizable(False, False)  # Tamaño fijo de ventana

        self.directory = tk.StringVar(value=os.path.expanduser("~"))  # Directorio HOME por defecto
        self.compression_format = tk.StringVar(value="zip")
        self.compression_level = tk.IntVar(value=5)
        self.original_action = tk.StringVar(value="2")

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
        actions = ["Eliminar", "Mover a 'OLD'", "Mantener"]
        ttk.Combobox(main_frame, textvariable=self.original_action, values=actions, state="readonly").grid(row=3, column=1, sticky="ew", pady=5)

        # Botón de inicio
        self.start_button = tk.Button(main_frame, text="Iniciar proceso", command=self.start_process)
        self.start_button.grid(row=4, column=0, columnspan=3, pady=10)

        # Barra de progreso
        self.progress = ttk.Progressbar(main_frame, length=400, mode="determinate")
        self.progress.grid(row=5, column=0, columnspan=3, pady=10, sticky="ew")

        # Etiqueta de estado
        self.status_label = tk.Label(main_frame, text="", wraplength=760)
        self.status_label.grid(row=6, column=0, columnspan=3, pady=5)

        # Terminal
        self.terminal = scrolledtext.ScrolledText(main_frame, width=92, height=12)  # 760x200 aproximadamente
        self.terminal.grid(row=7, column=0, columnspan=3, pady=10)

        # Configurar el peso de las columnas
        main_frame.columnconfigure(1, weight=1)

    def select_directory(self):
        directory = filedialog.askdirectory(initialdir=self.directory.get())
        if directory:
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

        self.status_label.config(text=info)
        self.log_to_terminal(info)

    def get_compressed_files(self, directory):
        compressed_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.zip', '.7z', '.tar.gz', '.rar')):
                    compressed_files.append(os.path.join(root, file))
        return compressed_files

    def start_process(self):
        self.start_button.config(state="disabled")
        threading.Thread(target=self.process_files, daemon=True).start()

    def process_files(self):
        self.log_to_terminal("Iniciando proceso de compresión...")
        compressed_files = self.get_compressed_files(self.directory.get())
        total_files = len(compressed_files)
        processed_files = 0

        for file in compressed_files:
            try:
                self.log_to_terminal(f"Procesando archivo: {file}")
                # Aquí iría el código para procesar cada archivo
                # Por ahora, solo simulamos el proceso
                import time
                time.sleep(1)  # Simula el tiempo de procesamiento

                processed_files += 1
                progress = (processed_files / total_files) * 100
                self.update_progress(progress)
            except Exception as e:
                self.log_to_terminal(f"Error al procesar {file}: {str(e)}")

        self.log_to_terminal(f"Proceso completado. {processed_files}/{total_files} archivos procesados.")
        self.start_button.config(state="normal")

    def update_progress(self, value):
        self.progress['value'] = value
        self.master.update_idletasks()

    def log_to_terminal(self, message):
        self.terminal.insert(tk.END, message + "\n")
        self.terminal.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ReCompresionApp(root)
    root.mainloop()
