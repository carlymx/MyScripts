"""
###############################################################################
##                        QEMU VIRTUAL MACHINE BACKUPS                       ##
##                              version: 0.3.6 dev                           ##
##                          CaRLyMx - 18 Octubre 2024                        ##
###############################################################################

## DESCRIPCIÓN:
## ESTE SCRIPT DE PYTHON3 ABRE UNA VENTANA CON TKINTER.
## MUESTRA TODAS LAS MAQUINAS VIRTUALES DENTRO DEL SISTEMA ADMINISTRADAS POR QEMU/VIRT MANAGER.
## PERMITE SELECCIONAR DE LA LISTA LAS QUE SE QUIERE CREAR UNA COPIA DE SEGURIDAD Y SU DESTINO LOCAL.
## PERMITE GUARDAR LAS INSTANTANEAS TANTO INTERNAS COMO EXTERNAS Y SUS ARCHIVOS XML DE CONFIGURACIÓN.

## DEPENDENCIAS:
## EN DISTRIBUCIONES DEBIAN (APT):
## sudo apt install libvirt-clients virt-manager virt-viewer python3-tk
"""


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
        self.root.geometry("550x650")

        # Crear la cola para pasar mensajes desde el proceso al hilo principal
        self.log_queue = multiprocessing.Queue()

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

        # Iniciar la actualización de la terminal en el hilo principal
        self.update_terminal()

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
        messagebox.showinfo("Acerca de", "QEMU MV Backups\nVersión 0.3.6\nFecha: 19-10-2024")

    def create_tabs(self):
        """Crear las pestañas Crear copia de seguridad y Opciones avanzadas"""
        # Pestaña 1: Crear copia de seguridad
        self.backup_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.backup_tab, text="Crear copia de seguridad")

        # Ruta de backups (selección de carpeta)
        self.backup_dir_label = tk.Label(self.backup_tab, text="Directorio de Backups:")
        self.backup_dir_label.pack(pady=5)

        path_frame = tk.Frame(self.backup_tab)
        path_frame.pack(pady=5)

        self.backup_dir_entry = tk.Entry(path_frame, width=50)
        self.backup_dir_entry.pack(side=tk.LEFT, padx=5)
        self.backup_dir_entry.insert(0, self.backup_dir)  # Mostrar ruta predeterminada

        self.browse_button = tk.Button(path_frame, text="Seleccionar Destino", command=self.browse_backup_directory)
        self.browse_button.pack(side=tk.LEFT)

        # Treeview para mostrar MVs y sus instantáneas en columnas
        self.vm_tree = ttk.Treeview(self.backup_tab, columns=("VM", "Internas", "Externas"), show="headings")
        self.vm_tree.heading("VM", text="Máquina Virtual")
        self.vm_tree.heading("Internas", text="snap Inter")
        self.vm_tree.column("Internas", width=25, anchor=tk.CENTER)
        self.vm_tree.heading("Externas", text="snap Ext")
        self.vm_tree.column("Externas", width=25, anchor=tk.CENTER)
        self.vm_tree.pack(pady=20, padx=20, fill="both", expand=True)

        # Terminal de progreso
        self.progress_terminal = tk.Text(self.backup_tab, height=10, state='disabled', bg='black', fg='#00FF00', font=("Courier", 10))
        self.progress_terminal.pack(pady=10, padx=20, fill="both", expand=True)

        # Habilitar el terminal temporalmente para insertar el texto
        self.progress_terminal.config(state='normal')
        self.progress_terminal.insert(tk.END, " QEMU Virtual Machine Backups - v0.3.6 Stable\n")
        self.progress_terminal.config(state='disabled')  # Deshabilitar de nuevo para evitar que el usuario edite

        # Pestaña 2: Opciones avanzadas
        self.advanced_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.advanced_tab, text="Opciones Avanzadas")

        # Opción "Copiar Instantáneas" en la pestaña "Opciones Avanzadas"
        advanced_frame = tk.Frame(self.advanced_tab)
        advanced_frame.pack(pady=20, padx=20, anchor="w")  # Añadir margen y justificar a la izquierda

        self.copy_snapshots = tk.BooleanVar()
        self.copy_snapshots_check = tk.Checkbutton(advanced_frame, text="Copiar Instantáneas", variable=self.copy_snapshots)
        self.copy_snapshots_check.pack(side=tk.LEFT)

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
        self.backup_process = multiprocessing.Process(target=self.create_backup, args=(self.log_queue,))
        self.backup_process.start()


    def create_backup(self, log_queue):
        """Realiza la copia de seguridad de las MVs seleccionadas y copia instantáneas si está seleccionado"""
        selected_items = self.vm_tree.selection()  # Obtener las MVs seleccionadas en el Treeview

        if not selected_items:
            log_queue.put("Advertencia: No se ha seleccionado ninguna MV.")
            return

        backup_dir = self.backup_dir_entry.get()

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)  # Crear el directorio si no existe

        for item in selected_items:
            vm_name = self.vm_tree.item(item, "values")[0]  # Obtener el nombre de la MV
            log_queue.put(f"Creando copia de seguridad para {vm_name}")

            try:
                # Copiar el archivo XML de la MV
                xml_path = os.path.join(backup_dir, f"{vm_name}.xml")
                with open(xml_path, "w") as xml_file:
                    subprocess.run(['virsh', 'dumpxml', vm_name], stdout=xml_file)
                log_queue.put(f"Archivo XML de {vm_name} copiado a {xml_path}")

                # Copiar el archivo QCOW2 asociado
                disk_path = self.get_disk_path(vm_name)
                if disk_path and os.path.exists(disk_path):
                    disk_backup_path = os.path.join(backup_dir, os.path.basename(disk_path))
                    shutil.copy2(disk_path, disk_backup_path)
                    log_queue.put(f"Archivo QCOW2 de {vm_name} copiado a {disk_backup_path}")
                else:
                    log_queue.put(f"Error: No se encontró el disco para {vm_name}")

                # Si está seleccionada la opción de "Copiar Instantáneas"
                if self.copy_snapshots.get():
                    snapshots = self.get_snapshots(vm_name)
                    if snapshots["internas"]:
                        log_queue.put(f"Copiando instantáneas internas de {vm_name}")
                        # Copiar los XML de las instantáneas internas
                        self.copy_internal_snapshots(vm_name, backup_dir, log_queue)

                    if snapshots["externas"]:
                        log_queue.put(f"Copiando instantáneas externas de {vm_name}")
                        # Copiar los archivos y XML de las instantáneas externas
                        self.copy_external_snapshots(snapshots["externas"], backup_dir, log_queue)

            except Exception as e:
                log_queue.put(f"Error creando la copia de seguridad para {vm_name}: {str(e)}")

        log_queue.put("Copia de seguridad completada.")


    def copy_internal_snapshots(self, vm_name, backup_dir, log_queue):
        """Copiar los XML de las instantáneas internas de una MV usando virsh"""
        try:
            # Ejecutar virsh snapshot-list para obtener las instantáneas internas
            result = subprocess.run(['virsh', 'snapshot-list', vm_name], capture_output=True, text=True)
            snapshot_list = result.stdout.splitlines()

            if len(snapshot_list) > 2:  # Si hay más de dos líneas (cabecera + al menos una instantánea)
                for line in snapshot_list[2:]:
                    # Verificar si la línea no está vacía o tiene contenido válido
                    columns = line.split()
                    if len(columns) > 0:  # Solo procesar si hay al menos un campo (nombre de instantánea)
                        snapshot_name = columns[0]  # El primer campo es el nombre de la instantánea

                        # Obtener el XML de la instantánea interna usando virsh snapshot-dumpxml
                        snapshot_xml = subprocess.run(
                            ['virsh', 'snapshot-dumpxml', vm_name, snapshot_name],
                            capture_output=True, text=True
                        ).stdout

                        # Guardar el archivo XML en el directorio de backups
                        snapshot_xml_file = os.path.join(backup_dir, f"{snapshot_name}.xml")
                        with open(snapshot_xml_file, 'w') as f:
                            f.write(snapshot_xml)
                        log_queue.put(f"Archivo XML de instantánea interna {snapshot_name} copiado a {snapshot_xml_file}")
            else:
                log_queue.put(f"No se encontraron instantáneas internas para {vm_name}")
        except Exception as e:
            log_queue.put(f"Error al copiar instantáneas internas: {e}")



    def copy_external_snapshots(self, external_snapshots, backup_dir, log_queue):
        """Copiar los archivos QCOW2 y los XML asociados a las instantáneas externas"""
        for qcow2_file in external_snapshots:
            # Copiar el archivo QCOW2
            qcow2_backup_path = os.path.join(backup_dir, os.path.basename(qcow2_file))
            shutil.copy2(qcow2_file, qcow2_backup_path)
            log_queue.put(f"Archivo QCOW2 de instantánea externa copiado a {qcow2_backup_path}")

            # Buscar el archivo XML de la instantánea externa (mismo nombre que el QCOW2 pero con extensión .xml)
            xml_file = qcow2_file.replace(".qcow2", ".xml")
            if os.path.exists(xml_file):
                xml_backup_path = os.path.join(backup_dir, os.path.basename(xml_file))
                shutil.copy2(xml_file, xml_backup_path)
                log_queue.put(f"Archivo XML de instantánea externa copiado a {xml_backup_path}")
            else:
                log_queue.put(f"No se encontró archivo XML para la instantánea externa {qcow2_file}")



    def cancel_backup_process(self):
        """Terminar el proceso de copia de seguridad si está corriendo"""
        if self.backup_process.is_alive():
            self.backup_process.terminate()
            self.log("Proceso de copia cancelado.")

    def handle_error(self, message):
        """Gestionar errores"""
        messagebox.showerror("Error", message)

    def update_terminal(self):
        """Actualizar la terminal de progreso leyendo la cola"""
        try:
            # Obtener el mensaje de la cola (si lo hay)
            message = self.log_queue.get_nowait()
        except multiprocessing.queues.Empty:
            self.root.after(100, self.update_terminal)  # Reintentar después de 100ms
        else:
            # Si hay un mensaje, actualizar la terminal
            self.progress_terminal.config(state='normal')
            self.progress_terminal.insert(tk.END, message + '\n')
            self.progress_terminal.config(state='disabled')
            self.progress_terminal.see(tk.END)
            self.root.after(100, self.update_terminal)  # Continuar escuchando


    def log(self, message):
        """Escribe mensajes de log en la terminal y consola"""
        self.progress_terminal.config(state='normal')
        self.progress_terminal.insert(tk.END, message + '\n')
        self.progress_terminal.config(state='disabled')
        self.progress_terminal.see(tk.END)  # Desplazar al final
        print(message)  # También imprimir en la consola

# Crear la ventana principal
if __name__ == "__main__":
    root = tk.Tk()
    app = BackupVMApp(root)
    root.mainloop()
