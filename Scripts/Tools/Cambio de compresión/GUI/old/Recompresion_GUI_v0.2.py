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
        master.title("Re-Compresión v0.8")
        master.geometry("800x600")

        self.directory = tk.StringVar()
        self.compression_format = tk.StringVar(value="zip")
        self.compression_level = tk.IntVar(value=5)
        self.original_action = tk.StringVar(value="2")

        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 5))

        # Configurar filas y columnas del top_frame
        for i in range(7):
            top_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):
            top_frame.grid_columnconfigure(i, weight=1)

        tk.Label(top_frame, text="Directorio:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(top_frame, textvariable=self.directory, width=50).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(top_frame, text="Seleccionar", command=self.select_directory).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(top_frame, text="Formato de compresión:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        formats = [("ZIP", "zip"), ("7Z", "7z"), ("TAR.GZ", "tar.gz"), ("RAR", "rar")]
        for i, (text, value) in enumerate(formats):
            tk.Radiobutton(top_frame, text=text, variable=self.compression_format, value=value).grid(row=1, column=i+1, padx=5, pady=5)

        tk.Label(top_frame, text="Nivel de compresión:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        tk.Scale(top_frame, from_=0, to=10, orient="horizontal", variable=self.compression_level).grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="we")

        tk.Label(top_frame, text="Acción con archivos originales:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        actions = [("Eliminar", "1"), ("Mover a 'OLD'", "2"), ("Mantener", "3")]
        for i, (text, value) in enumerate(actions):
            tk.Radiobutton(top_frame, text=text, variable=self.original_action, value=value).grid(row=3, column=i+1, padx=5, pady=5)

        self.start_button = tk.Button(top_frame, text="Iniciar proceso", command=self.start_process)
        self.start_button.grid(row=4, column=0, columnspan=3, pady=10)

        self.progress = ttk.Progressbar(top_frame, length=400, mode="determinate")
        self.progress.grid(row=5, column=0, columnspan=3, pady=10, padx=10)

        self.status_label = tk.Label(top_frame, text="")
        self.status_label.grid(row=6, column=0, columnspan=3, pady=5)

        # Terminal en la parte inferior (15% de la altura)
        terminal_frame = tk.Frame(main_frame, height=int(self.master.winfo_height() * 0.15))
        terminal_frame.pack(fill=tk.BOTH, expand=False, pady=(5, 10), padx=10)
        terminal_frame.pack_propagate(False)  # Evita que el frame se ajuste al tamaño de su contenido

        self.terminal = scrolledtext.ScrolledText(terminal_frame)
        self.terminal.pack(fill=tk.BOTH, expand=True)

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
