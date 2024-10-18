###############################################################################
##                        QEMU VIRTUAL MACHINE BACKUPS                       ##
##                            version: 0.3.4 Stable                          ##
##                          CaRLyMx - 18 Octubre 2024                        ##
###############################################################################

## DESCRIPCIÓN:
## ESTE SCRIPT DE PYTHON3 ABRE UNA VENTANA CON TKINTER.
## MUESTRA TODAS LAS MAQUINAS VIRTUALES DENTRO DEL SISTEMA ADMINISTRADAS POR QEMU/VIRT MANAGER.
## PERMITE SELECCIONAR DE LA LISTA LAS QUE SE QUIERE CREAR UNA COPIA DE SEGURIDAD Y SU DESTINO LOCAL.
## PERMITE GUARDAR LAS INSTANTANEAS (SOLO XML DE MOMENTO).

## DEPENDENCIAS:
## EN DISTRIBUCIONES DEBIAN (APT):
## sudo apt install libvirt-clients virt-manager virt-viewer python3-tk

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import shutil
import multiprocessing

class BackupVMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QEMU MV Backups")
        self.root.geometry("600x500")

        # Cargar la ruta de backups (antes de crear las pestañas)
        self.backup_dir = self.load_backup_directory()

        # Crear el menú
        self.create_menu()

        # Crear el notebook (pestañas)
        self.notebook = ttk.Notebook(root)
        self.create_tabs()

        # Colocar el notebook
        self.notebook.pack(fill="both", expand=True)

        # Crear los botones de acción
        self.create_action_buttons()

        # Procedimiento para cargar las MVs e instantáneas
        self.load_virtual_machines()

    def create_menu(self):
        """Crear el menú con las opciones Archivo > Salir y Acerca de"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

    def show_about(self):
        """Mostrar la ventana Acerca de"""
        messagebox.showinfo("Acerca de", "QEMU MV Backups\nVersión 0.3.4\nFecha: 15-10-2024")

    def create_tabs(self):
        """Crear las pestañas Crear copia de seguridad y Opciones avanzadas"""
        # Pestaña 1: Crear copia de seguridad
        self.backup_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.backup_tab, text="Crear copia de seguridad")

        # Ruta de backups (selección de carpeta)
        self.backup_dir_label = tk.Label(self.backup_tab, text="Directorio de Backups:")
        self.backup_dir_label.pack(pady=5)

        self.backup_dir_entry = tk.Entry(self.backup_tab, width=50)
        self.backup_dir_entry.pack(pady=5)
        self.backup_dir_entry.insert(0, self.backup_dir)  # Mostrar ruta predeterminada

        self.browse_button = tk.Button(self.backup_tab, text="Seleccionar Carpeta", command=self.browse_backup_directory)
        self.browse_button.pack(pady=5)

        # Treeview para mostrar MVs y sus instantáneas en columnas
        self.vm_tree = ttk.Treeview(self.backup_tab, columns=("VM", "Internas", "Externas"), show="headings")
        self.vm_tree.heading("VM", text="Máquina Virtual")
        self.vm_tree.heading("Internas", text="Insts Inter")
        self.vm_tree.column("Internas", width=25, anchor=tk.CENTER)
        self.vm_tree.heading("Externas", text="Insts Ext")
        self.vm_tree.column("Externas", width=25, anchor=tk.CENTER)
        self.vm_tree.pack(pady=20, padx=20, fill="both", expand=True)

    def create_action_buttons(self):
        """Crear los botones Crear Copia de Seguridad, Cancelar y Salir"""
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, pady=10)

        # Botón Crear Copia de Seguridad
        tk.Button(button_frame, text="Crear Copia de Seguridad", command=self.start_backup_process).pack(side=tk.LEFT, padx=5)

        # Botón Cancelar
        tk.Button(button_frame, text="Cancelar", command=self.cancel_backup_process).pack(side=tk.LEFT, padx=5)

        # Botón Salir
        tk.Button(button_frame, text="Salir", command=self.root.quit).pack(side=tk.LEFT, padx=5)

    def browse_backup_directory(self):
        """Abrir el diálogo de selección de carpeta y actualizar la entrada"""
        directory = filedialog.askdirectory(initialdir=self.backup_dir)
        if directory:
            self.backup_dir_entry.delete(0, tk.END)
            self.backup_dir_entry.insert(0, directory)
            self.save_backup_directory(directory)  # Guardar la selección

    def load_backup_directory(self):
        """Cargar la última ruta de backup usada desde un archivo o asignar la ruta predeterminada"""
        default_dir = os.path.expanduser("~/Maquinas Virtuales/backups")
        config_file = "backup_config.json"

        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
                return config.get("backup_directory", default_dir)
        return default_dir

    def save_backup_directory(self, directory):
        """Guardar la ruta de backup seleccionada en un archivo para futuras ejecuciones"""
        config_file = "backup_config.json"
        with open(config_file, "w") as f:
            json.dump({"backup_directory": directory}, f)

    def load_virtual_machines(self):
        """Cargar las máquinas virtuales y sus instantáneas"""
        self.vms_data = self.get_vms_with_snapshots()
        self.populate_vm_tree()

    def get_vms_with_snapshots(self):
        """Buscar todas las MVs y sus instantáneas (internas y externas)"""
        vms = {}
        try:
            # Obtener lista de MVs
            result = subprocess.run(['virsh', 'list', '--all'], stdout=subprocess.PIPE)
            lines = result.stdout.decode('utf-8').splitlines()
            for line in lines[2:]:
                cols = line.split()
                if len(cols) > 1:
                    vm_name = cols[1]
                    vms[vm_name] = {
                        "snapshots": self.get_snapshots(vm_name)
                    }
        except Exception as e:
            self.handle_error(f"Error obteniendo las MVs: {e}")
        return vms

    def get_snapshots(self, vm_name):
        """Obtener las instantáneas internas y externas de una MV"""
        snapshots = {"internas": [], "externas": []}
        try:
            # Verificar instantáneas internas (dentro del QCOW2)
            disk_path = self.get_disk_path(vm_name)
            if disk_path:
                result = subprocess.run(['qemu-img', 'snapshot', '-l', disk_path], stdout=subprocess.PIPE)
                lines = result.stdout.decode('utf-8').splitlines()[2:]  # Ignorar encabezados
                snapshots["internas"] = [line.split()[1] for line in lines]

            # Verificar instantáneas externas (archivos vinculados)
            chain = self.follow_snapshot_chain(disk_path)
            snapshots["externas"] = chain[1:]  # El primero es el archivo principal

        except Exception as e:
            self.handle_error(f"Error obteniendo instantáneas para {vm_name}: {e}")
        return snapshots

    def follow_snapshot_chain(self, qcow2_file):
        """Seguir la cadena de archivos QCOW2 (instantáneas externas)"""
        chain = []
        current_file = qcow2_file
        while current_file:
            info = subprocess.run(['qemu-img', 'info', '--output=json', current_file], stdout=subprocess.PIPE)
            data = json.loads(info.stdout.decode('utf-8'))
            chain.append(current_file)
            backing_file = data.get('backing-filename')
            if backing_file:
                current_file = backing_file
            else:
                current_file = None
        return chain

    def get_disk_path(self, vm_name):
        """Obtener la ruta del disco virtual usando el archivo XML de la MV"""
        result = subprocess.run(['virsh', 'dumpxml', vm_name], stdout=subprocess.PIPE)
        xml_data = result.stdout.decode('utf-8')
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_data)
        disk_source = root.find(".//disk[@device='disk']/source")
        if disk_source is not None:
            return disk_source.attrib.get('file')
        return None

    def populate_vm_tree(self):
        """Mostrar la lista de MVs y sus instantáneas en columnas"""
        for vm_name, data in self.vms_data.items():
            internas = len(data['snapshots']['internas'])
            externas = len(data['snapshots']['externas'])
            self.vm_tree.insert("", tk.END, values=(vm_name, internas, externas))

    def start_backup_process(self):
        """Iniciar un proceso separado para la copia de seguridad"""
        self.backup_process = multiprocessing.Process(target=self.create_backup)
        self.backup_process.start()

    def create_backup(self):
        """Realiza la copia de seguridad de las MVs seleccionadas"""
        selected_items = self.vm_tree.selection()  # Obtener las MVs seleccionadas en el Treeview

        if not selected_items:
            messagebox.showwarning("Advertencia", "No se ha seleccionado ninguna MV.")
            return

        backup_dir = self.backup_dir_entry.get()

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)  # Crear el directorio si no existe

        for item in selected_items:
            vm_name = self.vm_tree.item(item, "values")[0]  # Obtener el nombre de la MV
            self.log(f"Creando copia de seguridad para {vm_name}")

            try:
                # Copiar el archivo XML de la MV
                xml_path = os.path.join(backup_dir, f"{vm_name}.xml")
                with open(xml_path, "w") as xml_file:
                    subprocess.run(['virsh', 'dumpxml', vm_name], stdout=xml_file)
                self.log(f"Archivo XML de {vm_name} copiado a {xml_path}")

                # Copiar el archivo QCOW2 asociado
                disk_path = self.get_disk_path(vm_name)
                if disk_path and os.path.exists(disk_path):
                    disk_backup_path = os.path.join(backup_dir, os.path.basename(disk_path))
                    shutil.copy2(disk_path, disk_backup_path)
                    self.log(f"Archivo QCOW2 de {vm_name} copiado a {disk_backup_path}")
                else:
                    self.log(f"Error: No se encontró el disco para {vm_name}")

            except Exception as e:
                self.log(f"Error creando la copia de seguridad para {vm_name}: {str(e)}")

        self.log("Copia de seguridad completada.")

    def cancel_backup_process(self):
        """Terminar el proceso de copia de seguridad si está corriendo"""
        if self.backup_process.is_alive():
            self.backup_process.terminate()
            self.log("Proceso de copia cancelado.")

    def handle_error(self, message):
        """Gestionar errores"""
        messagebox.showerror("Error", message)

    def log(self, message):
        """Escribe mensajes de log en la consola o terminal"""
        print(message)

# Crear la ventana principal
if __name__ == "__main__":
    root = tk.Tk()
    app = BackupVMApp(root)
    root.mainloop()
