
# Respaldos de Máquinas Virtuales QEMU

**Introducción**

Este script en Python automatiza la creación de copias de seguridad para tus máquinas virtuales (VMs) QEMU y sus instantáneas, garantizando la seguridad y recuperabilidad de tus entornos virtuales.

**Características**

* **Interfaz Gráfica de Usuario (GUI) intuitiva:** Ofrece una interfaz fácil de usar para seleccionar VMs, gestionar instantáneas e iniciar respaldos.
* **Proceso de respaldo completo:** Crea respaldos tanto de los archivos de configuración XML de las VMs como de las imágenes de disco asociadas (formato QCOW2).
* **Manejo de instantáneas:** Detecta e incluye tanto las instantáneas internas (dentro del archivo QCOW2) como las externas (archivos vinculados) en los respaldos.
* **Soporte multiprocesamiento:** Optimiza el rendimiento de los respaldos aprovechando múltiples núcleos de CPU.
* **Registro:** Proporciona mensajes informativos sobre el proceso de respaldo, incluyendo éxitos, errores y advertencias.

**Instalación**

1. **Prerrequisitos:**
   * Python 3.x (https://www.python.org/downloads/)
   * Biblioteca `tkinter` (generalmente incluida por defecto en las instalaciones de Python)
   * Biblioteca `subprocess` (incluida en la biblioteca estándar de Python)
   * Herramienta de línea de comandos `qemu-img` (parte del paquete QEMU)
   * Biblioteca `multiprocessing` (incluida en la biblioteca estándar de Python)

2. **Clona o descarga el script:**
  
  > git clone [https://github.com/carlymx/MyScripts.git](https://github.com/carlymx/MyScripts.git)

  Navega al directorio del script:
  > Scripts/Tools/Virtual Machine Backups/

