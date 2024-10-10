###############################################################################
##                        QEMU VIRTUAL MACHINE BACKUPS                       ##
##                                version: 0.1a                              ##
##                          CaRLyMx - 10 Octubre 2024                        ##
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
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET

class BackupVMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Copia de Seguridad de MV")
        self.root.geometry("600x700")

        # Lista de MVs
        self.mvs = self.get_active_vms()
        self.selected_vms = tk.StringVar(value=self.mvs)

        # Título
        tk.Label(root, text="Selecciona las MV para hacer la copia de seguridad", font=("Arial", 12)).pack(pady=10)

        # Caja de selección de MVs
        self.vm_listbox = tk.Listbox(root, listvariable=self.selected_vms, selectmode=tk.MULTIPLE, height=8)
        self.vm_listbox.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        # Botón para elegir ruta de destino
        self.backup_path = tk.StringVar()
        tk.Label(root, text="Ruta de Copia de Seguridad (local o red):").pack(pady=5)
        path_frame = tk.Frame(root)
        path_frame.pack(pady=5)
        self.path_entry = tk.Entry(path_frame, textvariable=self.backup_path, width=50)
        self.path_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(path_frame, text="Examinar", command=self.browse_directory).pack(side=tk.LEFT)

        # Checkbox para incluir instantáneas en la copia de seguridad
        self.include_snapshots = tk.BooleanVar()
        self.include_snapshots.set(False)  # Por defecto no hacer copia de instantáneas
        tk.Checkbutton(root, text="Incluir instantáneas en la copia de seguridad", variable=self.include_snapshots).pack(pady=10)

        # Terminal para mostrar el progreso de la copia
        self.terminal = tk.Text(root, height=12, state='disabled', bg='black', fg='white')
        self.terminal.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Botones de acción
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Hacer Copia de Seguridad", command=self.backup_selected_vms).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Salir", command=root.quit).pack(side=tk.LEFT, padx=10)

    def get_active_vms(self):
        """Obtiene las MVs activas usando virsh list"""
        try:
            result = subprocess.run(['virsh', 'list', '--all'], stdout=subprocess.PIPE)
            lines = result.stdout.decode('utf-8').splitlines()
            mvs = []
            for line in lines[2:]:
                cols = line.split()
                if len(cols) > 1:
                    mvs.append(cols[1])  # La segunda columna es el nombre de la MV
            return mvs
        except Exception as e:
            self.log_terminal(f"Error obteniendo las MVs: {e}")
            return []

    def browse_directory(self):
        """Seleccionar directorio de copia de seguridad"""
        directory = filedialog.askdirectory()
        if directory:
            self.backup_path.set(directory)

    def log_terminal(self, message):
        """Escribe en la terminal embebida"""
        self.terminal.config(state='normal')
        self.terminal.insert(tk.END, message + '\n')
        self.terminal.config(state='disabled')
        self.terminal.see(tk.END)

    def get_vm_status(self, vm_name):
        """Obtiene el estado de la MV (apagada o en ejecución)"""
        result = subprocess.run(['virsh', 'domstate', vm_name], stdout=subprocess.PIPE)
        return result.stdout.decode('utf-8').strip()

    def get_disk_path(self, vm_name):
        """Obtiene la ruta del disco virtual usando el archivo XML de la MV"""
        result = subprocess.run(['virsh', 'dumpxml', vm_name], stdout=subprocess.PIPE)
        xml_data = result.stdout.decode('utf-8')
        root = ET.fromstring(xml_data)
        disk_source = root.find(".//disk[@device='disk']/source")
        if disk_source is not None:
            return disk_source.attrib.get('file')  # Ruta del disco virtual
        return None

    def get_snapshots(self, vm_name):
        """Obtiene la lista de instantáneas para una MV"""
        result = subprocess.run(['virsh', 'snapshot-list', vm_name], stdout=subprocess.PIPE)
        lines = result.stdout.decode('utf-8').splitlines()[2:]  # Ignorar las dos primeras líneas
        snapshots = [line.split()[0] for line in lines if line]  # Primera columna es el nombre de la instantánea
        return snapshots

    def backup_snapshots(self, vm_name, backup_dir):
        """Copia de seguridad de las instantáneas de una MV"""
        snapshots = self.get_snapshots(vm_name)
        if snapshots:
            for snapshot in snapshots:
                snapshot_file = os.path.join(backup_dir, f"{vm_name}_snapshot_{snapshot}.xml")
                with open(snapshot_file, 'w') as f:
                    subprocess.run(['virsh', 'snapshot-dumpxml', vm_name, snapshot], stdout=f)
                self.log_terminal(f"Instantánea {snapshot} de {vm_name} guardada en {snapshot_file}")
        else:
            self.log_terminal(f"No se encontraron instantáneas para {vm_name}")

    def backup_selected_vms(self):
        """Hace copia de seguridad de las MVs seleccionadas"""
        selected_indices = self.vm_listbox.curselection()
        selected_vms = [self.vm_listbox.get(i) for i in selected_indices]
        backup_dir = self.backup_path.get()
        include_snapshots = self.include_snapshots.get()

        if not selected_vms:
            messagebox.showwarning("Advertencia", "Debes seleccionar al menos una MV.")
            return

        if not backup_dir:
            messagebox.showwarning("Advertencia", "Debes seleccionar una ruta de copia de seguridad.")
            return

        for vm in selected_vms:
            self.log_terminal(f"Iniciando copia de seguridad de {vm}...")
            try:
                # Verificar estado de la MV
                vm_status = self.get_vm_status(vm)
                self.log_terminal(f"Estado de {vm}: {vm_status}")

                if vm_status.lower() == "running":
                    self.log_terminal(f"Advertencia: {vm} está en ejecución. No se recomienda hacer copia de seguridad en caliente.")
                    continue

                # Exportar configuración XML
                xml_backup_path = os.path.join(backup_dir, f"{vm}.xml")
                subprocess.run(['virsh', 'dumpxml', vm], stdout=open(xml_backup_path, 'w'))
                self.log_terminal(f"Configuración de {vm} guardada en {xml_backup_path}")

                # Obtener la ruta del disco virtual desde el XML
                disk_path = self.get_disk_path(vm)
                if disk_path and os.path.exists(disk_path):
                    disk_backup_path = os.path.join(backup_dir, os.path.basename(disk_path))
                    subprocess.run(['cp', disk_path, disk_backup_path])
                    self.log_terminal(f"Disco virtual de {vm} copiado a {disk_backup_path}")
                else:
                    self.log_terminal(f"No se pudo encontrar el disco virtual de {vm} o la ruta no existe.")

                # Copia de seguridad de las instantáneas si se selecciona la opción
                if include_snapshots:
                    self.backup_snapshots(vm, backup_dir)

            except Exception as e:
                self.log_terminal(f"Error al hacer la copia de seguridad de {vm}: {e}")

        self.log_terminal("Copia de seguridad completada.")

# Crear la ventana principal
if __name__ == "__main__":
    root = tk.Tk()
    app = BackupVMApp(root)
    root.mainloop()
