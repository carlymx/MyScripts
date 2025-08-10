import os
import tkinter as tk
from tkinter import filedialog, ttk
import zipfile
import tarfile
import tempfile
import subprocess
import sys
import shutil
import threading

def check_and_install_dependencies():
    try:
        import py7zr
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "py7zr"])

    try:
        import rarfile
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rarfile"])

check_and_install_dependencies()
import py7zr
import rarfile

class ReCompresionApp:
    def __init__(self, master):
        self.master = master
        master.title("Re-Compresión v0.8")
        master.geometry("600x400")

        self.directory = tk.StringVar()
        self.compression_format = tk.StringVar(value="zip")
        self.compression_level = tk.IntVar(value=5)
        self.original_action = tk.StringVar(value="2")

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.master, text="Directorio:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(self.master, textvariable=self.directory, width=50).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self.master, text="Seleccionar", command=self.select_directory).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(self.master, text="Formato de compresión:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        formats = [("ZIP", "zip"), ("7Z", "7z"), ("TAR.GZ", "tar.gz"), ("RAR", "rar")]
        for i, (text, value) in enumerate(formats):
            tk.Radiobutton(self.master, text=text, variable=self.compression_format, value=value).grid(row=1, column=i+1, padx=5, pady=5)

        tk.Label(self.master, text="Nivel de compresión:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        tk.Scale(self.master, from_=0, to=10, orient="horizontal", variable=self.compression_level).grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="we")

        tk.Label(self.master, text="Acción con archivos originales:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        actions = [("Eliminar", "1"), ("Mover a 'OLD'", "2"), ("Mantener", "3")]
        for i, (text, value) in enumerate(actions):
            tk.Radiobutton(self.master, text=text, variable=self.original_action, value=value).grid(row=3, column=i+1, padx=5, pady=5)

        self.start_button = tk.Button(self.master, text="Iniciar proceso", command=self.start_process)
        self.start_button.grid(row=4, column=0, columnspan=3, pady=10)

        self.progress = ttk.Progressbar(self.master, length=400, mode="determinate")
        self.progress.grid(row=5, column=0, columnspan=3, pady=10, padx=10)

        self.status_label = tk.Label(self.master, text="")
        self.status_label.grid(row=6, column=0, columnspan=3, pady=5)

    def select_directory(self):
        directory = filedialog.askdirectory()
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
        # Aquí iría el código para procesar los archivos
        # Deberías adaptar las funciones existentes para que funcionen con la interfaz gráfica
        # Por ejemplo, actualizar la barra de progreso y el estado
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ReCompresionApp(root)
    root.mainloop()
