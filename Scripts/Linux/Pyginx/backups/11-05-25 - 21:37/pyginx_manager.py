#!/usr/bin/env python3
##################################################################
#                                                                #
#                PYGINX - Nginx GUI Manager                      #
#                   V1.0 (04 NOV 2025)                           #
#               CaRLyMx - carlymx@gmail.com                      #
#                                                                #
##################################################################

"""
Pyginx - GUI para gestión de servidores Nginx

Este script proporciona una interfaz gráfica para gestionar servidores Nginx
en Linux, permitiendo encender/apagar el servidor, verificar estado y puertos,
ver logs, editar archivos de configuración y manejar perfiles de configuración.
"""

# Importación de bibliotecas estándar
import os
import sys
import platform
import subprocess
import logging
import threading
from datetime import datetime
from pathlib import Path
from getpass import getuser

# Importación de bibliotecas GUI
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QTextEdit, QLabel, QLineEdit,
                               QTabWidget, QMenuBar, QMenu, QAction, QGroupBox,
                               QFormLayout, QCheckBox, QSpinBox, QFileDialog,
                               QMessageBox, QComboBox, QScrollArea)
    from PyQt5.QtCore import QThread, pyqtSignal, Qt
    from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
except ImportError:
    print("Error: PyQt5 no está instalado. Instala con 'pip install PyQt5'")
    sys.exit(1)


def check_and_setup_virtual_env():
    """Crear y activar un entorno virtual si no existe, e instalar dependencias"""
    venv_dir = Path(".pyginx_env")
    
    # Verificar si estamos en el entorno virtual
    in_venv = sys.prefix != sys.base_prefix or hasattr(sys, 'real_prefix')
    
    if not in_venv:
        # Verificar si el entorno virtual ya existe
        if not venv_dir.exists():
            print("Creando entorno virtual...")
            try:
                subprocess.check_call([sys.executable, '-m', 'venv', str(venv_dir)])
                print("Entorno virtual creado exitosamente.")
            except subprocess.CalledProcessError:
                print("Error al crear el entorno virtual.")
                sys.exit(1)
        else:
            print("Entorno virtual ya existe.")
        
        # Determinar la ruta del ejecutable de Python en el entorno virtual
        if platform.system() == "Windows":
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
        
        # Instalar paquetes necesarios
        required_packages = ['PyQt5', 'colorama']
        print("Instalando paquetes en el entorno virtual...")
        
        try:
            subprocess.check_call([str(python_exe), '-m', 'pip', 'install'] + required_packages)
            print("Paquetes instalados correctamente en el entorno virtual.")
        except subprocess.CalledProcessError:
            print("Error al instalar paquetes en el entorno virtual.")
            sys.exit(1)
        
        # Reiniciar el script en el entorno virtual
        print("Reiniciando en el entorno virtual...")
        subprocess.call([str(python_exe), __file__] + sys.argv[1:])
        sys.exit(0)
    else:
        print("Ejecutando en entorno virtual.")
        return sys.executable


def check_dependencies():
    """Verificar e instalar dependencias si es necesario"""
    required_packages = {
        'PyQt5': 'PyQt5',
        'colorama': 'colorama',
        'pexpect': 'pexpect'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        # Importar colorama si está disponible para usar colores
        try:
            from colorama import Fore
            print(f"{Fore.YELLOW}Instalando paquetes faltantes: {', '.join(missing_packages)}")
        except ImportError:
            print(f"Instalando paquetes faltantes: {', '.join(missing_packages)}")
        
        try:
            # Si estamos en el entorno virtual, usar el python del entorno
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            try:
                from colorama import Fore
                print(f"{Fore.GREEN}Paquetes instalados correctamente.")
            except ImportError:
                print("Paquetes instalados correctamente.")
        except subprocess.CalledProcessError:
            try:
                from colorama import Fore
                print(f"{Fore.RED}Error al instalar paquetes. Por favor instale manualmente:")
            except ImportError:
                print("Error al instalar paquetes. Por favor instale manualmente:")
            for pkg in missing_packages:
                print(f"  pip install {pkg}")
            sys.exit(1)


def clear_screen():
    """Limpiar la pantalla según el sistema operativo"""
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')


def setup_logger(log_file_path=None):
    """Configurar sistema de logging"""
    if log_file_path is None:
        log_file_path = f".log/pyginx_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Crear directorio de logs si no existe
    log_dir = Path(log_file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar logger
    logger = logging.getLogger('pyginx_logger')
    logger.setLevel(logging.INFO)
    
    # Evitar duplicados de handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Handler para archivo
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato de logs
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Agregar handlers al logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Verificar dependencias y configurar logging después de que estemos en el entorno virtual
# Estos se llamarán desde la función main()


class NginxManager:
    """Clase para manejar operaciones de Nginx"""
    def __init__(self, logger=None):
        self.nginx_process = None
        self.is_running = False
        self.config_dir = "/etc/nginx"
        self.config_file = f"{self.config_dir}/nginx.conf"
        self.log_dir = "/var/log/nginx"
        self.access_log = f"{self.log_dir}/access.log"
        self.error_log = f"{self.log_dir}/error.log"
        self.root_password = None
        self.encrypted_password = None
        self.logger = logger

    def encrypt_password(self, password):
        """Ofuscar la contraseña de forma simple"""
        import base64
        # Codificar como base64 - no es seguro para producción pero cumple el propósito de ofuscación
        encoded_bytes = base64.b64encode(password.encode('utf-8'))
        return encoded_bytes.decode('utf-8')

    def decrypt_password(self, encrypted_password):
        """Desofuscar la contraseña"""
        import base64
        try:
            # Decodificar desde base64
            decoded_bytes = base64.b64decode(encrypted_password.encode('utf-8'))
            return decoded_bytes.decode('utf-8')
        except:
            return None

    def store_password(self, password):
        """Almacenar contraseña ofuscada temporalmente"""
        self.encrypted_password = self.encrypt_password(password)
        self.root_password = password  # también mantener en memoria durante la sesión

    def get_stored_password(self):
        """Obtener la contraseña almacenada"""
        if self.encrypted_password:
            return self.decrypt_password(self.encrypted_password)
        return self.root_password

    def check_system(self):
        """Verificar si el sistema es Linux"""
        system = platform.system()
        if system != "Linux":
            try:
                from colorama import Fore
                print(f"{Fore.RED}Este script está diseñado para funcionar en Linux.")
                print(f"{Fore.RED}Sistema detectado: {system}")
            except ImportError:
                print("Este script está diseñado para funcionar en Linux.")
                print(f"Sistema detectado: {system}")
            return False
        return True

    def check_user_permissions(self):
        """Verificar si el usuario tiene permisos adecuados"""
        return os.geteuid() == 0  # Verificar si es root

    def check_nginx_installed(self):
        """Verificar si Nginx está instalado"""
        try:
            result = subprocess.run(["which", "nginx"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def start_nginx(self):
        """Iniciar el servidor Nginx"""
        try:
            # Determinar si usar sudo basado en permisos
            if not self.check_user_permissions():
                # Si no somos root, usar la función run_command_with_password
                command = "sudo systemctl start nginx"
                success, result = self.run_command_with_password(command)
                if success:
                    if self.logger:
                        self.logger.info("Nginx iniciado exitosamente")
                    self.is_running = True
                    return True, "Nginx iniciado exitosamente"
                else:
                    if self.logger:
                        self.logger.error(f"Error al iniciar Nginx: {result}")
                    return False, f"Error al iniciar Nginx: {result}"
            else:
                # Si ya somos root, ejecutar directamente
                result = subprocess.run(["systemctl", "start", "nginx"], capture_output=True, text=True)
                if result.returncode == 0:
                    if self.logger:
                        self.logger.info("Nginx iniciado exitosamente")
                    self.is_running = True
                    return True, "Nginx iniciado exitosamente"
                else:
                    if self.logger:
                        self.logger.error(f"Error al iniciar Nginx: {result.stderr}")
                    return False, f"Error al iniciar Nginx: {result.stderr}"
        except Exception as e:
            if self.logger:
                self.logger.error(f"Excepción al iniciar Nginx: {str(e)}")
            return False, f"Excepción al iniciar Nginx: {str(e)}"

    def stop_nginx(self):
        """Detener el servidor Nginx"""
        try:
            # Determinar si usar sudo basado en permisos
            if not self.check_user_permissions():
                # Si no somos root, usar la función run_command_with_password
                command = "sudo systemctl stop nginx"
                success, result = self.run_command_with_password(command)
                if success:
                    if self.logger:
                        self.logger.info("Nginx detenido exitosamente")
                    self.is_running = False
                    return True, "Nginx detenido exitosamente"
                else:
                    if self.logger:
                        self.logger.error(f"Error al detener Nginx: {result}")
                    return False, f"Error al detener Nginx: {result}"
            else:
                # Si ya somos root, ejecutar directamente
                result = subprocess.run(["systemctl", "stop", "nginx"], capture_output=True, text=True)
                if result.returncode == 0:
                    if self.logger:
                        self.logger.info("Nginx detenido exitosamente")
                    self.is_running = False
                    return True, "Nginx detenido exitosamente"
                else:
                    if self.logger:
                        self.logger.error(f"Error al detener Nginx: {result.stderr}")
                    return False, f"Error al detener Nginx: {result.stderr}"
        except Exception as e:
            if self.logger:
                self.logger.error(f"Excepción al detener Nginx: {str(e)}")
            return False, f"Excepción al detener Nginx: {str(e)}"

    def restart_nginx(self):
        """Reiniciar el servidor Nginx"""
        try:
            # Determinar si usar sudo basado en permisos
            if not self.check_user_permissions():
                # Si no somos root, usar la función run_command_with_password
                command = "sudo systemctl restart nginx"
                success, result = self.run_command_with_password(command)
                if success:
                    if self.logger:
                        self.logger.info("Nginx reiniciado exitosamente")
                    self.is_running = True
                    return True, "Nginx reiniciado exitosamente"
                else:
                    if self.logger:
                        self.logger.error(f"Error al reiniciar Nginx: {result}")
                    return False, f"Error al reiniciar Nginx: {result}"
            else:
                # Si ya somos root, ejecutar directamente
                result = subprocess.run(["systemctl", "restart", "nginx"], capture_output=True, text=True)
                if result.returncode == 0:
                    if self.logger:
                        self.logger.info("Nginx reiniciado exitosamente")
                    self.is_running = True
                    return True, "Nginx reiniciado exitosamente"
                else:
                    if self.logger:
                        self.logger.error(f"Error al reiniciar Nginx: {result.stderr}")
                    return False, f"Error al reiniciar Nginx: {result.stderr}"
        except Exception as e:
            if self.logger:
                self.logger.error(f"Excepción al reiniciar Nginx: {str(e)}")
            return False, f"Excepción al reiniciar Nginx: {str(e)}"

    def check_nginx_status(self):
        """Verificar estado del servidor Nginx"""
        try:
            # Determinar si usar sudo basado en permisos
            if not self.check_user_permissions():
                # Si no somos root, usar la función run_command_with_password
                command = "sudo systemctl status nginx"
                success, result = self.run_command_with_password(command)
                
                if success:
                    # Aseguramos que el resultado sea una cadena de texto
                    output = result if isinstance(result, str) else str(result)
                    # Incluso si el código de retorno no es 0, el comando puede haber ejecutado con éxito
                    # systemctl devuelve 3 si el servicio está detenido
                    self.is_running = "active (running)" in output
                    status_msg = "Nginx está corriendo" if self.is_running else "Nginx no está corriendo"
                    if self.logger:
                        self.logger.info(f"Estado de Nginx: {status_msg}")
                    return True, status_msg, self.is_running
                else:
                    if self.logger:
                        self.logger.error(f"Error al verificar estado de Nginx: {result}")
                    return False, f"Error al verificar estado: {result}", False
            else:
                # Si ya somos root, ejecutar directamente
                result = subprocess.run(["systemctl", "status", "nginx"], capture_output=True, text=True)
                # Incluso si el código de retorno no es 0, el comando puede haber ejecutado con éxito
                # systemctl devuelve 3 si el servicio está detenido
                if result.returncode == 0 or result.returncode == 3:  # 0 = corriendo, 3 = detenido
                    # Verificar si realmente está corriendo
                    self.is_running = "active (running)" in result.stdout
                    status_msg = "Nginx está corriendo" if self.is_running else "Nginx no está corriendo"
                    if self.logger:
                        self.logger.info(f"Estado de Nginx: {status_msg}")
                    return True, status_msg, self.is_running
                else:
                    # Otros códigos de error indican problemas reales
                    if self.logger:
                        self.logger.error(f"Error al verificar estado de Nginx: {result.stderr}")
                    return False, f"Error al verificar estado: {result.stderr}", False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Excepción al verificar estado de Nginx: {str(e)}")
            return False, f"Excepción al verificar estado: {str(e)}", False

    def get_nginx_ports(self):
        """Obtener los puertos en los que Nginx está escuchando"""
        try:
            import re
            all_ports = []
            
            # Directorio específico de sitios habilitados que mencionaste
            sites_enabled_dir = f"{self.config_dir}/sites-enabled/"
            
            # Solo leer archivos del directorio de sitios habilitados
            if os.path.exists(sites_enabled_dir):
                # Si es directorio, leer todos los archivos .conf
                if os.path.isdir(sites_enabled_dir):
                    for filename in os.listdir(sites_enabled_dir):
                        if filename.endswith('.conf') or filename.endswith('.config'):
                            file_path = os.path.join(sites_enabled_dir, filename)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    # Buscar patrones de 'listen' con puertos numéricos
                                    listen_patterns = re.findall(r'listen\s+(\d+)(?:\s+ssl)?;', content)
                                    all_ports.extend(listen_patterns)
                            except Exception as e:
                                if self.logger:
                                    self.logger.info(f"Error al leer archivo de sitio habilitado {file_path}: {str(e)}")
                                continue
                # Si es archivo, leerlo directamente
                elif os.path.isfile(sites_enabled_dir):
                    try:
                        with open(sites_enabled_dir, 'r', encoding='utf-8') as f:
                            content = f.read()
                            listen_patterns = re.findall(r'listen\s+(\d+)(?:\s+ssl)?;', content)
                            all_ports.extend(listen_patterns)
                    except Exception as e:
                        if self.logger:
                            self.logger.info(f"Error al leer archivo de sitio habilitado {sites_enabled_dir}: {str(e)}")
            
            # Eliminar duplicados y filtrar puertos vacíos
            ports = list(set([port for port in all_ports if port and port.strip()]))
            
            if ports:
                if self.logger:
                    self.logger.info(f"Puertos de sitios habilitados de Nginx detectados: {', '.join(ports)}")
                return True, f"Puertos: {', '.join(ports)}", ports
            else:
                # Intentar detectar puertos usando ss/lsof si nginx está corriendo
                if self.is_running:
                    running_ports = self.get_running_nginx_ports()
                    if running_ports:
                        if self.logger:
                            self.logger.info(f"Puertos de Nginx en ejecución: {', '.join(running_ports)}")
                        return True, f"Puertos: {', '.join(running_ports)}", running_ports
                    else:
                        if self.logger:
                            self.logger.info("No se encontraron puertos definidos en sitios habilitados ni en ejecución")
                        return True, "No se encontraron puertos definidos en sitios habilitados", []
                else:
                    if self.logger:
                        self.logger.info("No se encontraron puertos definidos en sitios habilitados")
                    return True, "No se encontraron puertos definidos en sitios habilitados", []
        except Exception as e:
            if self.logger:
                self.logger.error(f"Excepción al obtener puertos de Nginx: {str(e)}")
            return False, f"Excepción al obtener puertos: {str(e)}", []

    def get_running_nginx_ports(self):
        """Obtener los puertos en los que Nginx está actualmente escuchando"""
        try:
            import re
            # Usar lsof para encontrar los puertos en los que nginx está escuchando
            lsof_result = subprocess.run(["lsof", "-i", "-P", "-n", "-c", "nginx"], 
                                       capture_output=True, text=True)
            
            if lsof_result.returncode == 0 and lsof_result.stdout:
                # Extraer puertos desde la salida de lsof
                lines = lsof_result.stdout.split('\n')
                listening_ports = []
                
                for line in lines:
                    # Buscar líneas que indican escucha (LISTEN)
                    if 'LISTEN' in line and 'nginx' in line.lower():
                        # Extraer el puerto de la línea (formato típico: nginx  PID ... TCP *:PORT o IP:PORT)
                        port_matches = re.findall(r':(\d+)\s+\(LISTEN\)', line)
                        listening_ports.extend([port for port in port_matches if port])
                        
                        # También capturar el formato tipo 0.0.0.0:PORT
                        alt_matches = re.findall(r'0\.0\.0\.0:(\d+)\s+|:::(\d+)\s+', line)
                        for match in alt_matches:
                            if isinstance(match, tuple):
                                port = next((p for p in match if p), None)
                            else:
                                port = match
                            if port:
                                listening_ports.append(port)
                
                # Eliminar duplicados
                unique_ports = list(set(listening_ports))
                
                # Filtrar para incluir solo puertos comunes de Nginx
                valid_ports = []
                for port in unique_ports:
                    if port.isdigit():
                        port_num = int(port)
                        # Considerar puertos estándar y comunes para Nginx
                        if port_num < 65536:  # Puerto válido
                            # Puertos comunes de Nginx o rango de servidores web
                            if port_num == 80 or port_num == 443 or (port_num >= 8000 and port_num <= 9000) or (port_num >= 80 and port_num <= 90):
                                valid_ports.append(port)
                
                return valid_ports
            else:
                return []
        except Exception as e:
            if self.logger:
                self.logger.error(f"Excepción al obtener puertos de Nginx en ejecución: {str(e)}")
            return []

    def check_port_status(self, port):
        """Verificar si un puerto específico está en uso"""
        try:
            # Usar ss o netstat para verificar el puerto
            result = subprocess.run(["ss", "-tuln"], capture_output=True, text=True)
            if result.returncode != 0:
                # Si ss no está disponible, probar con netstat
                result = subprocess.run(["netstat", "-tuln"], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Verificar si el puerto está en la salida
                if f":{port}" in result.stdout or f".{port}" in result.stdout:
                    if self.logger:
                        self.logger.info(f"Puerto {port} está en uso")
                    return True
                else:
                    if self.logger:
                        self.logger.info(f"Puerto {port} no está en uso")
                    return False
            else:
                if self.logger:
                    self.logger.error("No se pudo verificar el estado de los puertos")
                return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Excepción al verificar puerto {port}: {str(e)}")
            return False

    def run_command_with_password(self, command):
        """Ejecutar comando que requiere contraseña root"""
        if not self.check_user_permissions():
            password = self.get_stored_password()
            if not password:
                # Si no hay contraseña almacenada, solicitarla
                from PyQt5.QtWidgets import QInputDialog
                password, ok = QInputDialog.getText(None, 'Contraseña Root', 
                                                  'Ingrese la contraseña de root:', 
                                                  echo=QLineEdit.Password)
                if ok and password:
                    self.store_password(password)
                else:
                    return False, "Se requiere contraseña de root"

            try:
                # Enviar la contraseña directamente a sudo usando -S (stdin)
                import shlex
                # Separar el comando en partes para evitar problemas con los argumentos
                cmd_parts = shlex.split(command)
                # El comando sudo con -S lee la contraseña desde stdin
                full_cmd = ["sudo", "-S"] + cmd_parts
                # Enviar la contraseña como input al proceso
                result = subprocess.run(full_cmd, input=password + "\n", capture_output=True, text=True)
                
                # Para comandos de systemctl status, el código de retorno no es indicativo de error
                # El comando puede ejecutarse correctamente aunque el servicio esté inactivo
                if "systemctl status" in command:
                    # Si el comando es de status, devolver éxito siempre que no haya error real
                    if result.returncode == 0 or result.stdout:
                        return True, result.stdout
                    else:
                        return False, result.stderr if result.stderr else "Error desconocido"
                elif result.returncode == 0:
                    # Para otros comandos, devolver éxito solo si el código es 0
                    return True, result.stdout
                else:
                    # Para otros comandos, si el código no es 0, es error
                    return False, result.stderr if result.stderr else result.stdout
            except Exception as e:
                return False, f"Error al ejecutar comando: {str(e)}"
        else:
            # Si ya somos root, ejecutar directamente
            try:
                result = subprocess.run(command.split(), capture_output=True, text=True)
                if result.returncode == 0:
                    return True, result.stdout
                else:
                    return False, result.stderr
            except Exception as e:
                return False, f"Error al ejecutar comando: {str(e)}"

    def enable_nginx_autostart(self):
        """Habilitar el inicio automático de Nginx con el sistema"""
        try:
            if not self.check_user_permissions():
                # Si no somos root, usar la función run_command_with_password
                command = "sudo systemctl enable nginx"
                success, result = self.run_command_with_password(command)
                if success:
                    if self.logger:
                        self.logger.info("Inicio automático de Nginx habilitado")
                    return True, "Inicio automático de Nginx habilitado exitosamente"
                else:
                    if self.logger:
                        self.logger.error(f"Error al habilitar inicio automático de Nginx: {result}")
                    return False, f"Error al habilitar inicio automático: {result}"
            else:
                # Si ya somos root, ejecutar directamente
                result = subprocess.run(["systemctl", "enable", "nginx"], capture_output=True, text=True)
                if result.returncode == 0:
                    if self.logger:
                        self.logger.info("Inicio automático de Nginx habilitado")
                    return True, "Inicio automático de Nginx habilitado exitosamente"
                else:
                    if self.logger:
                        self.logger.error(f"Error al habilitar inicio automático de Nginx: {result.stderr}")
                    return False, f"Error al habilitar inicio automático: {result.stderr}"
        except Exception as e:
            if self.logger:
                self.logger.error(f"Excepción al habilitar inicio automático de Nginx: {str(e)}")
            return False, f"Excepción al habilitar inicio automático: {str(e)}"

    def disable_nginx_autostart(self):
        """Deshabilitar el inicio automático de Nginx con el sistema"""
        try:
            if not self.check_user_permissions():
                # Si no somos root, usar la función run_command_with_password
                command = "sudo systemctl disable nginx"
                success, result = self.run_command_with_password(command)
                if success:
                    if self.logger:
                        self.logger.info("Inicio automático de Nginx deshabilitado")
                    return True, "Inicio automático de Nginx deshabilitado exitosamente"
                else:
                    if self.logger:
                        self.logger.error(f"Error al deshabilitar inicio automático de Nginx: {result}")
                    return False, f"Error al deshabilitar inicio automático: {result}"
            else:
                # Si ya somos root, ejecutar directamente
                result = subprocess.run(["systemctl", "disable", "nginx"], capture_output=True, text=True)
                if result.returncode == 0:
                    if self.logger:
                        self.logger.info("Inicio automático de Nginx deshabilitado")
                    return True, "Inicio automático de Nginx deshabilitado exitosamente"
                else:
                    if self.logger:
                        self.logger.error(f"Error al deshabilitar inicio automático de Nginx: {result.stderr}")
                    return False, f"Error al deshabilitar inicio automático: {result.stderr}"
        except Exception as e:
            if self.logger:
                self.logger.error(f"Excepción al deshabilitar inicio automático de Nginx: {str(e)}")
            return False, f"Excepción al deshabilitar inicio automático: {str(e)}"

    def check_nginx_autostart_status(self):
        """Verificar el estado del inicio automático de Nginx"""
        try:
            if not self.check_user_permissions():
                # Si no somos root, usar la función run_command_with_password
                command = "sudo systemctl is-enabled nginx"
                success, result = self.run_command_with_password(command)
                
                if success:
                    # El resultado indica el estado del inicio automático
                    output = result if isinstance(result, str) else str(result)
                    # is-enabled devuelve "enabled" o "disabled"
                    is_enabled = "enabled" in output
                    status_msg = "Inicio automático habilitado" if is_enabled else "Inicio automático deshabilitado"
                    if self.logger:
                        self.logger.info(f"Estado del inicio automático de Nginx: {status_msg}")
                    return True, status_msg, is_enabled
                else:
                    # Puede que el servicio no esté instalado o haya otro problema
                    if "disabled" in result.lower():
                        # Caso especial donde is-enabled puede devolver un código de error
                        # pero aún así indicar que está deshabilitado
                        if self.logger:
                            self.logger.info("Inicio automático de Nginx: deshabilitado (verificado con error)")
                        return True, "Inicio automático deshabilitado", False
                    else:
                        if self.logger:
                            self.logger.error(f"Error al verificar estado del inicio automático: {result}")
                        return False, f"Error al verificar estado del inicio automático: {result}", False
            else:
                # Si ya somos root, ejecutar directamente
                result = subprocess.run(["systemctl", "is-enabled", "nginx"], capture_output=True, text=True)
                # systemctl is-enabled devuelve 0 si está habilitado, no 0 si está deshabilitado
                if result.returncode == 0 and "enabled" in result.stdout:
                    is_enabled = True
                    status_msg = "Inicio automático habilitado"
                elif result.returncode == 1 or "disabled" in result.stdout or "not-found" in result.stdout:
                    is_enabled = False
                    status_msg = "Inicio automático deshabilitado"
                else:
                    # Otro estado
                    is_enabled = None
                    status_msg = f"Estado del inicio automático: {result.stdout.strip()}"
                
                if self.logger:
                    self.logger.info(f"Estado del inicio automático de Nginx: {status_msg}")
                return True, status_msg, is_enabled
        except Exception as e:
            if self.logger:
                self.logger.error(f"Excepción al verificar estado del inicio automático: {str(e)}")
            return False, f"Excepción al verificar estado del inicio automático: {str(e)}", False


class PyginxApp(QMainWindow):
    """Clase principal de la aplicación"""
    def __init__(self, logger=None):
        super().__init__()
        self.setWindowTitle("Pyginx - Nginx GUI Manager v1.0")
        self.setGeometry(100, 100, 1000, 700)
        
        # Inicializar el gestor de Nginx (el logger se asignará después)
        self.nginx_manager = NginxManager()
        self.logger = logger
        
        # Crear la interfaz de usuario
        self.init_ui()
        # Inicializar los indicadores de estado a desconocido (amarillo)
        if hasattr(self, 'status_indicator'):
            self.update_status_indicator('unknown')
        if hasattr(self, 'autostart_indicator'):
            self.update_autostart_indicator('unknown')
        
    def init_ui(self):
        """Inicializar la interfaz de usuario"""
        # Crear widget principal y layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Crear pestañas
        self.tabs = QTabWidget()
        
        # Agregar pestañas vacías por ahora
        self.create_main_tab()
        self.create_config_tab()
        self.create_logs_tab()
        self.create_permissions_tab()
        
        main_layout.addWidget(self.tabs)
        self.setCentralWidget(main_widget)
        
        # Crear menú
        self.create_menu()
        
    def create_main_tab(self):
        """Crear pestaña principal con controles de Nginx"""
        main_tab = QWidget()
        layout = QVBoxLayout(main_tab)
        
        # Grupo para controles principales
        controls_group = QGroupBox("Controles de Nginx")
        controls_layout = QFormLayout(controls_group)
        
        # Botones para iniciar/detener/reiniciar
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Iniciar Nginx")
        self.stop_btn = QPushButton("Detener Nginx")
        self.restart_btn = QPushButton("Reiniciar Nginx")
        self.status_btn = QPushButton("Verificar Estado")
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.restart_btn)
        btn_layout.addWidget(self.status_btn)
        
        controls_layout.addRow(btn_layout)
        
        # Botones para inicio automático
        autostart_layout = QHBoxLayout()
        
        self.enable_autostart_btn = QPushButton("Activar Inicio Automático con el Sistema")
        self.disable_autostart_btn = QPushButton("Desactivar Inicio Automático con el Sistema")
        
        autostart_layout.addWidget(self.enable_autostart_btn)
        autostart_layout.addWidget(self.disable_autostart_btn)
        
        controls_layout.addRow(autostart_layout)
        
        # Layout para estado visual y texto
        status_layout = QHBoxLayout()
        
        # Indicador visual de estado (cuadro de color)
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(20, 20)  # Cuadro de 20x20 píxeles
        self.status_indicator.setStyleSheet("background-color: yellow; border: 1px solid black;")  # Estado desconocido en amarillo
        
        # Etiquetas de texto de estado y puerto
        self.status_label = QLabel("Estado: Desconocido")
        
        # Indicador visual de inicio automático (cuadro de color)
        self.autostart_indicator = QLabel()
        self.autostart_indicator.setFixedSize(20, 20)  # Cuadro de 20x20 píxeles
        self.autostart_indicator.setStyleSheet("background-color: yellow; border: 1px solid black;")  # Estado desconocido en amarillo
        
        # Etiqueta de texto de inicio automático
        self.autostart_status_label = QLabel("Inicio Auto: Desconocido")
        self.port_label = QLabel("Puerto: -")
        
        # Añadir los indicadores y las etiquetas al layout horizontal
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.autostart_indicator)
        status_layout.addWidget(self.autostart_status_label)
        status_layout.addStretch()  # Para empujar las etiquetas hacia la izquierda y dejar espacio
        
        # Agregar la fila al layout del formulario
        controls_layout.addRow("Estado:", status_layout)
        controls_layout.addRow("Puerto:", self.port_label)
        
        layout.addWidget(controls_group)
        layout.addStretch()
        
        # Conectar eventos de botones
        self.start_btn.clicked.connect(self.start_nginx_server)
        self.stop_btn.clicked.connect(self.stop_nginx_server)
        self.restart_btn.clicked.connect(self.restart_nginx_server)
        self.status_btn.clicked.connect(self.check_nginx_status_server)
        self.enable_autostart_btn.clicked.connect(self.enable_nginx_autostart)
        self.disable_autostart_btn.clicked.connect(self.disable_nginx_autostart)
        
        # Añadir pestaña
        self.tabs.addTab(main_tab, "Principal")
        
    def update_status_indicator(self, status):
        """Actualizar el indicador visual de estado
        status puede ser: 'online' (verde), 'offline' (rojo), 'unknown' (amarillo)
        """
        if status == 'online':
            color = 'green'
            tooltip = 'Nginx está corriendo'
        elif status == 'offline':
            color = 'red'
            tooltip = 'Nginx está detenido'
        else:  # unknown
            color = 'yellow'
            tooltip = 'Estado de Nginx desconocido'
        
        self.status_indicator.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
        self.status_indicator.setToolTip(tooltip)
        
    def update_autostart_indicator(self, status):
        """Actualizar el indicador visual de inicio automático
        status puede ser: 'enabled' (verde), 'disabled' (rojo), 'unknown' (amarillo)
        """
        if status == 'enabled':
            color = 'green'
            tooltip = 'Inicio automático habilitado'
        elif status == 'disabled':
            color = 'red'
            tooltip = 'Inicio automático deshabilitado'
        else:  # unknown
            color = 'yellow'
            tooltip = 'Estado de inicio automático desconocido'
        
        self.autostart_indicator.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
        self.autostart_indicator.setToolTip(tooltip)
        
    def start_nginx_server(self):
        """Iniciar Nginx"""
        success, message = self.nginx_manager.start_nginx()
        self.status_label.setText(f"Estado: {'Corriendo' if success else 'Detenido'}")
        
        if success:
            # Actualizar puerto
            _, port_info, ports = self.nginx_manager.get_nginx_ports()
            if ports:
                self.port_label.setText(f"Puerto: {', '.join(ports)}")
            else:
                self.port_label.setText("Puerto: Desconocido")
            QMessageBox.information(self, "Nginx", message)
            # Actualizar indicador visual a verde (en línea)
            self.update_status_indicator('online')
        else:
            QMessageBox.critical(self, "Error", message)
            # Actualizar indicador visual a rojo (fuera de línea) si falla
            self.update_status_indicator('offline')

    def stop_nginx_server(self):
        """Detener Nginx"""
        success, message = self.nginx_manager.stop_nginx()
        self.status_label.setText("Estado: Detenido")
        
        if success:
            QMessageBox.information(self, "Nginx", message)
            # Actualizar indicador visual a rojo (fuera de línea)
            self.update_status_indicator('offline')
        else:
            QMessageBox.critical(self, "Error", message)
            # Actualizar indicador visual a rojo (fuera de línea) si falla
            self.update_status_indicator('offline')

    def restart_nginx_server(self):
        """Reiniciar Nginx"""
        success, message = self.nginx_manager.restart_nginx()
        
        if success:
            # Actualizar puerto después de reiniciar
            _, port_info, ports = self.nginx_manager.get_nginx_ports()
            if ports:
                self.port_label.setText(f"Puerto: {', '.join(ports)}")
            else:
                self.port_label.setText("Puerto: Desconocido")
            QMessageBox.information(self, "Nginx", message)
            # Actualizar indicador visual a verde (en línea)
            self.update_status_indicator('online')
        else:
            QMessageBox.critical(self, "Error", message)
            # Actualizar indicador visual a rojo (fuera de línea) si falla
            self.update_status_indicator('offline')

    def check_nginx_status_server(self):
        """Verificar estado de Nginx"""
        success, message, is_running = self.nginx_manager.check_nginx_status()
        self.status_label.setText(f"Estado: {'Corriendo' if is_running else 'Detenido'}")
        
        if success:
            # Actualizar puerto
            _, port_info, ports = self.nginx_manager.get_nginx_ports()
            if ports:
                self.port_label.setText(f"Puerto: {', '.join(ports)}")
            else:
                self.port_label.setText("Puerto: Desconocido")
            QMessageBox.information(self, "Nginx", message)
            # Actualizar indicador visual según el estado real
            if is_running:
                self.update_status_indicator('online')  # Verde si está corriendo
            else:
                self.update_status_indicator('offline')  # Rojo si está detenido
        else:
            self.port_label.setText("Puerto: Error")
            QMessageBox.critical(self, "Error", message)
            # Actualizar indicador visual a amarillo (desconocido) si hay error
            self.update_status_indicator('unknown')
        
    def enable_nginx_autostart(self):
        """Habilitar el inicio automático de Nginx con el sistema"""
        success, message = self.nginx_manager.enable_nginx_autostart()
        if success:
            QMessageBox.information(self, "Inicio Automático", message)
        else:
            QMessageBox.critical(self, "Error", message)
        
        # Actualizar el estado del inicio automático
        self.update_autostart_status()
    
    def disable_nginx_autostart(self):
        """Deshabilitar el inicio automático de Nginx con el sistema"""
        success, message = self.nginx_manager.disable_nginx_autostart()
        if success:
            QMessageBox.information(self, "Inicio Automático", message)
        else:
            QMessageBox.critical(self, "Error", message)
        
        # Actualizar el estado del inicio automático
        self.update_autostart_status()
    
    def update_autostart_status(self):
        """Actualizar el estado del inicio automático"""
        success, message, is_enabled = self.nginx_manager.check_nginx_autostart_status()
        if success:
            self.autostart_status_label.setText(f"Inicio Auto: {'Habilitado' if is_enabled else 'Deshabilitado'}")
            # Actualizar indicador visual según el estado real
            if is_enabled:
                self.update_autostart_indicator('enabled')  # Verde si está habilitado
            else:
                self.update_autostart_indicator('disabled')  # Rojo si está deshabilitado
        else:
            self.autostart_status_label.setText("Inicio Auto: Error")
            # Actualizar indicador visual a amarillo (desconocido) si hay error
            self.update_autostart_indicator('unknown')
    
    def check_nginx_status_server(self):
        """Verificar estado de Nginx"""
        # Verificar estado del servidor
        success, message, is_running = self.nginx_manager.check_nginx_status()
        self.status_label.setText(f"Estado: {'Corriendo' if is_running else 'Detenido'}")
        
        if success:
            # Actualizar puerto
            _, port_info, ports = self.nginx_manager.get_nginx_ports()
            if ports:
                self.port_label.setText(f"Puerto: {', '.join(ports)}")
            else:
                self.port_label.setText("Puerto: Desconocido")
            QMessageBox.information(self, "Nginx", message)
            # Actualizar indicador visual según el estado real
            if is_running:
                self.update_status_indicator('online')  # Verde si está corriendo
            else:
                self.update_status_indicator('offline')  # Rojo si está detenido
        else:
            self.port_label.setText("Puerto: Error")
            QMessageBox.critical(self, "Error", message)
            # Actualizar indicador visual a amarillo (desconocido) si hay error
            self.update_status_indicator('unknown')
        
        # También verificar y actualizar el estado del inicio automático
        self.update_autostart_status()
        
    def create_config_tab(self):
        """Crear pestaña para gestión de configuración"""
        config_tab = QWidget()
        layout = QVBoxLayout(config_tab)
        
        # Grupo para perfiles de configuración
        profiles_group = QGroupBox("Perfiles de Configuración")
        profiles_layout = QVBoxLayout(profiles_group)
        
        profile_layout = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Simple", "Seguro", "A Prueba de Fallos", "HTTP", "HTTPS"])
        self.load_profile_btn = QPushButton("Cargar Perfil")
        self.save_profile_btn = QPushButton("Guardar Perfil")
        
        profile_layout.addWidget(QLabel("Perfil:"))
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addWidget(self.load_profile_btn)
        profile_layout.addWidget(self.save_profile_btn)
        
        profiles_layout.addLayout(profile_layout)
        
        layout.addWidget(profiles_group)
        
        # Editor de configuración
        config_editor_group = QGroupBox("Editor de Configuración")
        editor_layout = QVBoxLayout(config_editor_group)
        
        # Caja de direcciones para mostrar el archivo actual
        self.current_config_file = self.nginx_manager.config_file  # Variable para almacenar la ruta actual
        self.config_path_label = QLabel(f"Archivo: {self.current_config_file}")
        self.config_path_label.setFont(QFont("Courier", 10))
        self.config_path_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid gray;")
        editor_layout.addWidget(self.config_path_label)
        
        self.config_editor = QTextEdit()
        self.config_editor.setFont(QFont("Courier", 12))
        editor_layout.addWidget(self.config_editor)
        
        # Botones para archivo de configuración
        file_btn_layout = QHBoxLayout()
        self.load_config_btn = QPushButton("Cargar Configuración")
        self.save_config_btn = QPushButton("Guardar Configuración")
        self.test_config_btn = QPushButton("Probar Configuración")
        self.backup_config_btn = QPushButton("Crear Backup")
        self.select_config_btn = QPushButton("Seleccionar Archivo")
        
        file_btn_layout.addWidget(self.load_config_btn)
        file_btn_layout.addWidget(self.save_config_btn)
        file_btn_layout.addWidget(self.test_config_btn)
        file_btn_layout.addWidget(self.backup_config_btn)
        file_btn_layout.addWidget(self.select_config_btn)
        
        editor_layout.addLayout(file_btn_layout)
        
        # Grupo para configuración de puerto
        port_group = QGroupBox("Configuración de Puerto")
        port_layout = QHBoxLayout(port_group)
        
        port_layout.addWidget(QLabel("Puerto:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(80)  # Valor predeterminado
        self.port_input.setToolTip("Puerto en el que Nginx escuchará conexiones")
        
        self.update_port_btn = QPushButton("Actualizar Puerto")
        self.update_port_btn.setToolTip("Actualizar el puerto en la configuración actual y reiniciar Nginx si está en marcha")
        
        port_layout.addWidget(self.port_input)
        port_layout.addWidget(self.update_port_btn)
        port_layout.addStretch()
        
        editor_layout.addWidget(port_group)
        
        # Conectar el botón de actualización de puerto
        self.update_port_btn.clicked.connect(self.update_port_in_config)
        
        layout.addWidget(config_editor_group)
        
        # Añadir pestaña
        self.tabs.addTab(config_tab, "Configuración")
        
        # Conectar eventos de botones
        self.load_config_btn.clicked.connect(self.load_config_file)
        self.save_config_btn.clicked.connect(self.save_config_file)
        self.test_config_btn.clicked.connect(self.test_config)
        self.backup_config_btn.clicked.connect(self.backup_config)
        self.load_profile_btn.clicked.connect(self.load_profile)
        self.save_profile_btn.clicked.connect(self.save_profile)
        self.select_config_btn.clicked.connect(self.select_config_file)

    def load_config_file(self):
        """Cargar archivo de configuración principal de Nginx"""
        try:
            with open(self.nginx_manager.config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.config_editor.setPlainText(content)
            
            # Actualizar la variable y la caja de direcciones con la ruta del archivo
            self.current_config_file = self.nginx_manager.config_file
            self.config_path_label.setText(f"Archivo: {self.current_config_file}")
            
            if self.logger:
                self.logger.info(f"Configuración cargada desde {self.current_config_file}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo de configuración:\n{str(e)}")

    def save_config_file(self):
        """Guardar archivo de configuración"""
        try:
            # Usar la variable de instancia que almacena la ruta del archivo actual
            current_file_path = self.current_config_file
            
            # Verificar si necesitamos permisos elevados para este archivo
            if current_file_path.startswith('/etc/') or current_file_path.startswith('/usr/') or current_file_path.startswith('/var/'):
                # Este archivo está en un directorio protegido, necesitamos usar sudo
                # Primero, crear backup si el archivo existe
                if os.path.exists(current_file_path):
                    success, result = self.nginx_manager.run_command_with_password(f"sudo cp {current_file_path} {current_file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    if success:
                        if self.logger:
                            self.logger.info(f"Backup creado: {current_file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    else:
                        if self.logger:
                            self.logger.warning(f"Error al crear backup: {result}")
                        # Continuar aunque el backup falle
                
                # Guardar el contenido en un archivo temporal
                temp_config = f"/tmp/temp_nginx_config_{int(datetime.now().timestamp())}"
                with open(temp_config, 'w', encoding='utf-8') as f:
                    f.write(self.config_editor.toPlainText())
                
                # Copiar con permisos elevados
                success, result = self.nginx_manager.run_command_with_password(f"sudo cp {temp_config} {current_file_path}")
                # Eliminar archivo temporal
                try:
                    os.remove(temp_config)
                except:
                    pass  # No hacer nada si no se puede eliminar el archivo temporal
                
                if success:
                    if self.logger:
                        self.logger.info(f"Configuración guardada en {current_file_path}")
                    QMessageBox.information(self, "Éxito", "Configuración guardada correctamente")
                else:
                    QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo de configuración:\n{result}")
                    if self.logger:
                        self.logger.error(f"Error al guardar configuración: {result}")
            else:
                # Archivo está en directorio que no requiere permisos elevados
                # Antes de guardar, hacer backup si existe el archivo
                if os.path.exists(current_file_path):
                    backup_path = f"{current_file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    import shutil
                    shutil.copy2(current_file_path, backup_path)
                    if self.logger:
                        self.logger.info(f"Backup creado: {backup_path}")
                
                # Guardar el contenido actual
                with open(current_file_path, 'w', encoding='utf-8') as f:
                    f.write(self.config_editor.toPlainText())
                
                if self.logger:
                    self.logger.info(f"Configuración guardada en {current_file_path}")
                QMessageBox.information(self, "Éxito", "Configuración guardada correctamente")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo de configuración:\n{str(e)}")

    def select_config_file(self):
        """Seleccionar archivo de configuración personalizado"""
        config_file, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de configuración", 
            "/etc/nginx", "Archivos de configuración (*.conf *.config);;Todos los archivos (*)"
        )
        
        if config_file:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.config_editor.setPlainText(content)
                
                # Actualizar la variable y la caja de direcciones con la ruta del archivo
                self.current_config_file = config_file
                self.config_path_label.setText(f"Archivo: {self.current_config_file}")
                
                if self.logger:
                    self.logger.info(f"Configuración cargada desde {self.current_config_file}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo leer el archivo de configuración:\n{str(e)}")

    def test_config(self):
        """Probar la configuración de Nginx"""
        try:
            # Guardar temporalmente la configuración actual para probarla
            temp_config = f"/tmp/nginx_test_config_{int(datetime.now().timestamp())}"
            with open(temp_config, 'w', encoding='utf-8') as f:
                f.write(self.config_editor.toPlainText())
            
            # Probar la configuración usando el comando de nginx con comprobación de sintaxis
            # Primero intentamos con privilegios normales, y si falla por permisos, usamos sudo
            result = subprocess.run(["nginx", "-t", "-c", temp_config], 
                                  capture_output=True, text=True)
            
            # Si falla por permisos, intentamos con sudo
            if result.returncode != 0 and ("Permission denied" in result.stderr or "failed (13: Permission denied)" in result.stderr):
                # Usar el sistema de contraseñas de la aplicación para probar con sudo
                success, output = self.nginx_manager.run_command_with_password(f"sudo nginx -t -c {temp_config}")
                if success:
                    result = subprocess.CompletedProcess(args=["nginx", "-t", "-c", temp_config], returncode=0, stdout=output, stderr="")
                else:
                    result = subprocess.CompletedProcess(args=["nginx", "-t", "-c", temp_config], returncode=1, stdout="", stderr=output)
            
            # Eliminar archivo temporal
            try:
                os.remove(temp_config)
            except:
                pass  # No hacer nada si no se puede eliminar el archivo temporal
            
            if result.returncode == 0:
                QMessageBox.information(self, "Prueba de Configuración", 
                                      "La configuración es válida. ¡No se detectaron errores!")
                if self.logger:
                    self.logger.info("Configuración de Nginx probada y válida")
            else:
                # Si la salida de error contiene warnings, los mostramos como información adicional
                error_msg = result.stderr
                if "warn" in error_msg.lower():
                    QMessageBox.information(self, "Prueba de Configuración", 
                                          f"La configuración es sintácticamente válida pero con advertencias:\n{error_msg}")
                    if self.logger:
                        self.logger.info(f"Configuración con advertencias: {error_msg}")
                else:
                    QMessageBox.critical(self, "Error en Configuración", 
                                       f"Errores encontrados en la configuración:\n{error_msg}")
                    if self.logger:
                        self.logger.error(f"Errores en configuración de Nginx: {error_msg}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al probar la configuración:\n{str(e)}")

    def backup_config(self):
        """Crear backup del archivo de configuración"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.nginx_manager.config_file}.backup_{timestamp}"
            
            # Verificar si necesitamos permisos elevados para este archivo
            if self.nginx_manager.config_file.startswith('/etc/') or self.nginx_manager.config_file.startswith('/usr/') or self.nginx_manager.config_file.startswith('/var/'):
                # Este archivo está en un directorio protegido, necesitamos usar sudo
                success, result = self.nginx_manager.run_command_with_password(f"sudo cp {self.nginx_manager.config_file} {backup_path}")
                
                if success:
                    if self.logger:
                        self.logger.info(f"Backup de configuración creado: {backup_path}")
                    QMessageBox.information(self, "Backup", f"Backup creado exitosamente:\n{backup_path}")
                else:
                    QMessageBox.critical(self, "Error", f"No se pudo crear el backup:\n{result}")
                    if self.logger:
                        self.logger.error(f"Error al crear backup: {result}")
            else:
                # Archivo está en directorio que no requiere permisos elevados
                import shutil
                shutil.copy2(self.nginx_manager.config_file, backup_path)
                
                if self.logger:
                    self.logger.info(f"Backup de configuración creado: {backup_path}")
                QMessageBox.information(self, "Backup", f"Backup creado exitosamente:\n{backup_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el backup:\n{str(e)}")

    def update_port_in_config(self):
        """Actualizar el puerto en el archivo de configuración"""
        new_port = str(self.port_input.value())
        
        # Obtener el contenido actual del editor
        current_config = self.config_editor.toPlainText()
        
        # Expresión regular para encontrar líneas con 'listen' y puertos
        # Busca patrones como 'listen 80;' o 'listen *:80;'
        import re
        # Patrón para 'listen' con puerto numérico
        pattern = r'(listen\s+[^;]*:)?(\d+)(\s*ssl)?(\s*;|;)'
        
        # Reemplazar todos los puertos numéricos después de 'listen' con el nuevo puerto
        def replace_port(match):
            prefix = match.group(1) or "listen "
            # Mantener 'ssl' si estaba presente
            ssl_part = match.group(3) or ""
            end_part = match.group(4) or ";"
            # Si el prefijo incluye dirección IP, mantenerla
            if prefix and ':' in prefix and not prefix.endswith(':'):
                return f"{prefix}{new_port}{ssl_part}{end_part}"
            else:
                return f"listen {new_port}{ssl_part}{end_part}"
        
        updated_config = re.sub(pattern, replace_port, current_config)
        
        # Si no se encontraron coincidencias, agregar una configuración de listen al inicio
        if updated_config == current_config:
            # Buscar sección 'server' y agregar listen justo después de '{'
            server_pattern = r'(server\s*{)'
            def add_listen_after_server(match):
                return f"{match.group(1)}\n    listen {new_port};"
            
            updated_config = re.sub(server_pattern, add_listen_after_server, current_config, count=1)
        
        # Actualizar el editor con la configuración actualizada
        self.config_editor.setPlainText(updated_config)
        
        # Mostrar mensaje de confirmación
        QMessageBox.information(self, "Puerto Actualizado", 
                               f"El puerto ha sido actualizado a {new_port} en la configuración.\n"
                               f"Recuerda guardar la configuración y reiniciar Nginx para que los cambios surtan efecto.")
        
        if self.logger:
            self.logger.info(f"Puerto actualizado a {new_port} en la configuración")

    def load_profile(self):
        """Cargar perfil de configuración"""
        profile = self.profile_combo.currentText()
        profile_path = os.path.join(self.nginx_manager.config_dir, f"profiles/{profile.lower()}.conf")
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.config_editor.setPlainText(content)
            
            # Actualizar la variable y la caja de direcciones con la ruta del perfil
            self.current_config_file = profile_path
            self.config_path_label.setText(f"Archivo: {self.current_config_file}")
            
            if self.logger:
                self.logger.info(f"Perfil {profile} cargado desde {self.current_config_file}")
            QMessageBox.information(self, "Perfil Cargado", f"Perfil {profile} cargado correctamente")
        except FileNotFoundError:
            # Si no existe el perfil específico, cargar uno predeterminado
            self.load_default_profile(profile)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el perfil:\n{str(e)}")

    def save_profile(self):
        """Guardar perfil de configuración"""
        profile = self.profile_combo.currentText()
        profile_path = os.path.join(self.nginx_manager.config_dir, f"profiles/{profile.lower()}.conf")
        
        try:
            # Verificar si necesitamos permisos elevados para este archivo
            if profile_path.startswith('/etc/') or profile_path.startswith('/usr/') or profile_path.startswith('/var/'):
                # Este archivo está en un directorio protegido, necesitamos usar sudo
                # Crear directorio de perfiles si no existe usando sudo
                success, result = self.nginx_manager.run_command_with_password(f"sudo mkdir -p {os.path.dirname(profile_path)}")
                if not success and "File exists" not in result:
                    if self.logger:
                        self.logger.warning(f"Error al crear directorio de perfiles: {result}")
                    # Continuar intentando guardar de todas formas
                
                # Guardar el contenido en un archivo temporal
                temp_config = f"/tmp/temp_profile_config_{int(datetime.now().timestamp())}"
                with open(temp_config, 'w', encoding='utf-8') as f:
                    f.write(self.config_editor.toPlainText())
                
                # Copiar con permisos elevados
                success, result = self.nginx_manager.run_command_with_password(f"sudo cp {temp_config} {profile_path}")
                # Eliminar archivo temporal
                try:
                    os.remove(temp_config)
                except:
                    pass  # No hacer nada si no se puede eliminar el archivo temporal
                
                if success:
                    # No cambiar la ruta del archivo actual cuando se guarda como perfil
                    # Solo se guarda el contenido en el archivo de perfil
                    
                    if self.logger:
                        self.logger.info(f"Perfil {profile} guardado en {profile_path}")
                    QMessageBox.information(self, "Perfil Guardado", f"Perfil {profile} guardado correctamente")
                else:
                    QMessageBox.critical(self, "Error", f"No se pudo guardar el perfil:\n{result}")
                    if self.logger:
                        self.logger.error(f"Error al guardar perfil: {result}")
            else:
                # Archivo está en directorio que no requiere permisos elevados
                # Crear directorio de perfiles si no existe
                os.makedirs(os.path.dirname(profile_path), exist_ok=True)
                
                with open(profile_path, 'w', encoding='utf-8') as f:
                    f.write(self.config_editor.toPlainText())
                
                # No cambiar la ruta del archivo actual cuando se guarda como perfil
                # Solo se guarda el contenido en el archivo de perfil
                
                if self.logger:
                    self.logger.info(f"Perfil {profile} guardado en {profile_path}")
                QMessageBox.information(self, "Perfil Guardado", f"Perfil {profile} guardado correctamente")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el perfil:\n{str(e)}")

    def load_default_profile(self, profile):
        """Cargar perfil predeterminado"""
        # Crear contenido predeterminado según el perfil
        profiles_content = {
            "Simple": """# Configuración simple de Nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    sendfile        on;
    keepalive_timeout  65;
    
    server {
        listen       80;
        server_name  localhost;
        
        location / {
            root   /usr/share/nginx/html;
            index  index.html index.htm;
        }
        
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   /usr/share/nginx/html;
        }
    }
}
""",
            "Seguro": """# Configuración segura de Nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Seguridad
    server_tokens off;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    sendfile        on;
    tcp_nopush     on;
    tcp_nodelay    on;
    keepalive_timeout  65;
    types_hash_max_size 2048;
    
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
""",
            "A Prueba de Fallos": """# Configuración a prueba de fallos de Nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Configuración robusta
    sendfile        on;
    tcp_nopush     on;
    tcp_nodelay    on;
    keepalive_timeout  65;
    types_hash_max_size 2048;
    
    # Valores conservadores para entornos con alta carga
    client_max_body_size 16M;
    client_body_timeout 120s;
    client_header_timeout 120s;
    send_timeout 120s;
    
    # Configuración de buffers
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
""",
            "HTTP": """# Configuración para HTTP de Nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    sendfile        on;
    keepalive_timeout  65;
    
    server {
        listen       80;
        server_name  _;
        
        location / {
            root   /usr/share/nginx/html;
            index  index.html index.htm;
        }
        
        # Redirección HTTPS
        location /secure/ {
            return 301 https://$server_name$request_uri;
        }
    }
}
""",
            "HTTPS": """# Configuración para HTTPS de Nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    sendfile        on;
    keepalive_timeout  65;
    
    # Configuración SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    server {
        listen       80;
        server_name  _;
        
        # Redirigir HTTP a HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen       443 ssl http2;
        server_name  _;
        
        ssl_certificate /path/to/certificate.crt;
        ssl_certificate_key /path/to/private.key;
        
        root /usr/share/nginx/html;
        index index.html index.htm;
        
        location / {
            try_files $uri $uri/ =404;
        }
    }
}
"""
        }
        
        if profile in profiles_content:
            self.config_editor.setPlainText(profiles_content[profile])
            # No cambiar la ruta del archivo cuando se carga un perfil predeterminado
            if self.logger:
                self.logger.info(f"Perfil predeterminado {profile} cargado")
            QMessageBox.information(self, "Perfil Cargado", 
                                  f"Perfil predeterminado {profile} cargado")
        
    def create_logs_tab(self):
        """Crear pestaña para visualización de logs"""
        logs_tab = QWidget()
        layout = QVBoxLayout(logs_tab)
        
        # Selector de tipo de log
        log_selector_layout = QHBoxLayout()
        log_selector_layout.addWidget(QLabel("Tipo de Log:"))
        self.log_type_combo = QComboBox()
        self.log_type_combo.addItems(["Acceso", "Error", "Personalizado"])
        log_selector_layout.addWidget(self.log_type_combo)
        
        self.load_log_btn = QPushButton("Cargar Log")
        self.load_log_btn.clicked.connect(self.load_log_file)
        log_selector_layout.addWidget(self.load_log_btn)
        
        self.follow_log_checkbox = QCheckBox("Seguir log (tail -f)")
        log_selector_layout.addWidget(self.follow_log_checkbox)
        
        layout.addLayout(log_selector_layout)
        
        # Visualizador de logs
        self.logs_viewer = QTextEdit()
        self.logs_viewer.setFont(QFont("Courier", 11))
        self.logs_viewer.setReadOnly(True)
        layout.addWidget(self.logs_viewer)
        
        # Controles adicionales para logs
        log_controls_layout = QHBoxLayout()
        
        self.clear_log_btn = QPushButton("Limpiar")
        self.clear_log_btn.clicked.connect(self.clear_logs)
        log_controls_layout.addWidget(self.clear_log_btn)
        
        self.refresh_log_btn = QPushButton("Actualizar")
        self.refresh_log_btn.clicked.connect(self.refresh_log_display)
        log_controls_layout.addWidget(self.refresh_log_btn)
        
        # Botón para seleccionar archivo de log personalizado
        self.select_custom_log_btn = QPushButton("Archivo Personalizado")
        self.select_custom_log_btn.clicked.connect(self.select_custom_log_file)
        log_controls_layout.addWidget(self.select_custom_log_btn)
        
        layout.addLayout(log_controls_layout)
        
        # Añadir pestaña
        self.tabs.addTab(logs_tab, "Logs")

    def load_log_file(self):
        """Cargar archivo de log según selección"""
        log_type = self.log_type_combo.currentText()
        
        if log_type == "Acceso":
            log_file = self.nginx_manager.access_log
        elif log_type == "Error":
            log_file = self.nginx_manager.error_log
        else:
            # Para tipo personalizado, pedir al usuario que seleccione el archivo
            log_file, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar archivo de log", 
                "/var/log", "Archivos de log (*.log);;Todos los archivos (*)"
            )
            if not log_file:
                return
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                self.logs_viewer.setPlainText(content)
            
            # Si está activado seguir log, iniciar thread
            if self.follow_log_checkbox.isChecked():
                self.start_following_log(log_file)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo de log:\n{str(e)}")

    def select_custom_log_file(self):
        """Seleccionar archivo de log personalizado"""
        log_file, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de log personalizado", 
            "/var/log", "Archivos de log (*.log);;Todos los archivos (*)"
        )
        
        if log_file:
            self.custom_log_path = log_file
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    self.logs_viewer.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo leer el archivo de log:\n{str(e)}")

    def clear_logs(self):
        """Limpiar el visor de logs"""
        self.logs_viewer.clear()

    def refresh_log_display(self):
        """Actualizar la visualización de logs"""
        self.load_log_file()

    def start_following_log(self, log_file):
        """Iniciar seguimiento de log en tiempo real"""
        # Detener cualquier thread de seguimiento anterior
        if hasattr(self, 'log_follow_thread') and self.log_follow_thread.is_alive():
            self.log_follow_thread.stop()
        
        # Iniciar nuevo thread para seguir el log
        self.log_follow_thread = LogFollowThread(log_file)
        self.log_follow_thread.log_signal.connect(self.append_to_log_viewer)
        self.log_follow_thread.start()

    def append_to_log_viewer(self, text):
        """Añadir texto al visor de logs"""
        cursor = self.logs_viewer.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.logs_viewer.setTextCursor(cursor)
        self.logs_viewer.ensureCursorVisible()

    def create_permissions_tab(self):
        """Crear pestaña para gestión de permisos"""
        perms_tab = QWidget()
        layout = QVBoxLayout(perms_tab)
        
        # Grupo para directorio de archivos servidos
        dir_group = QGroupBox("Directorio de Archivos Servidos")
        dir_layout = QFormLayout(dir_group)
        
        self.dir_path_input = QLineEdit("/var/www/html")  # Ruta predeterminada
        self.browse_dir_btn = QPushButton("Examinar")
        self.browse_dir_btn.clicked.connect(self.browse_directory)
        
        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.dir_path_input)
        browse_layout.addWidget(self.browse_dir_btn)
        
        dir_layout.addRow("Directorio:", browse_layout)
        
        # Botones para comprobación y ajuste de permisos
        perms_btn_layout = QHBoxLayout()
        self.check_perms_btn = QPushButton("Verificar Permisos")
        self.fix_perms_btn = QPushButton("Corregir Permisos")
        self.check_perms_btn.clicked.connect(self.check_permissions)
        self.fix_perms_btn.clicked.connect(self.fix_permissions)
        
        perms_btn_layout.addWidget(self.check_perms_btn)
        perms_btn_layout.addWidget(self.fix_perms_btn)
        
        dir_layout.addRow(perms_btn_layout)
        
        layout.addWidget(dir_group)
        
        # Resultados de verificación de permisos
        results_group = QGroupBox("Resultados de Verificación")
        results_layout = QVBoxLayout(results_group)
        
        self.perms_results = QTextEdit()
        self.perms_results.setFont(QFont("Courier", 11))
        self.perms_results.setReadOnly(True)
        results_layout.addWidget(self.perms_results)
        
        layout.addWidget(results_group)
        
        # Opciones avanzadas
        advanced_group = QGroupBox("Opciones Avanzadas")
        advanced_layout = QFormLayout(advanced_group)
        
        # Usuario propietario
        self.owner_user_input = QLineEdit("www-data")
        owner_layout = QHBoxLayout()
        owner_layout.addWidget(QLabel("Usuario propietario:"))
        owner_layout.addWidget(self.owner_user_input)
        advanced_layout.addRow(owner_layout)
        
        # Permisos para directorios
        self.dir_perms_input = QLineEdit("755")
        dir_perms_layout = QHBoxLayout()
        dir_perms_layout.addWidget(QLabel("Permisos para directorios:"))
        dir_perms_layout.addWidget(self.dir_perms_input)
        advanced_layout.addRow(dir_perms_layout)
        
        # Permisos para archivos
        self.file_perms_input = QLineEdit("644")
        file_perms_layout = QHBoxLayout()
        file_perms_layout.addWidget(QLabel("Permisos para archivos:"))
        file_perms_layout.addWidget(self.file_perms_input)
        advanced_layout.addRow(file_perms_layout)
        
        layout.addWidget(advanced_group)
        
        # Añadir pestaña
        self.tabs.addTab(perms_tab, "Permisos")

    def browse_directory(self):
        """Abrir diálogo para seleccionar directorio"""
        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar directorio de archivos servidos", 
            "/var/www"
        )
        if directory:
            self.dir_path_input.setText(directory)

    def check_permissions(self):
        """Verificar permisos de archivos en el directorio"""
        directory = self.dir_path_input.text()
        
        if not directory or not os.path.isdir(directory):
            QMessageBox.warning(self, "Error", "Por favor seleccione un directorio válido.")
            return
        
        try:
            self.perms_results.clear()
            self.perms_results.append(f"Verificando permisos en: {directory}\n")
            
            # Información del usuario propietario
            owner_user = self.owner_user_input.text() or "www-data"
            
            # Verificar si el usuario existe
            import pwd
            try:
                pwd.getpwnam(owner_user)
            except KeyError:
                self.perms_results.append(f"Advertencia: El usuario '{owner_user}' no existe en el sistema.\n")
            
            incorrect_perms = []
            
            # Recorrer directorio recursivamente
            for root, dirs, files in os.walk(directory):
                # Verificar permisos de directorios
                dir_stat = os.stat(root)
                dir_mode = oct(dir_stat.st_mode)[-3:]
                if dir_mode != self.dir_perms_input.text():
                    incorrect_perms.append({
                        'path': root,
                        'type': 'directorio',
                        'current': dir_mode,
                        'expected': self.dir_perms_input.text()
                    })
                
                # Verificar propietario de directorio
                dir_uid = dir_stat.st_uid
                dir_owner = pwd.getpwuid(dir_uid).pw_name if dir_uid else "unknown"
                if dir_owner != owner_user:
                    incorrect_perms.append({
                        'path': root,
                        'type': 'directorio (propietario)',
                        'current': dir_owner,
                        'expected': owner_user
                    })
                    
                # Verificar permisos y propietario de archivos
                for file in files:
                    file_path = os.path.join(root, file)
                    file_stat = os.stat(file_path)
                    file_mode = oct(file_stat.st_mode)[-3:]
                    
                    if file_mode != self.file_perms_input.text():
                        incorrect_perms.append({
                            'path': file_path,
                            'type': 'archivo',
                            'current': file_mode,
                            'expected': self.file_perms_input.text()
                        })
                    
                    # Verificar propietario de archivo
                    file_uid = file_stat.st_uid
                    file_owner = pwd.getpwuid(file_uid).pw_name if file_uid else "unknown"
                    if file_owner != owner_user:
                        incorrect_perms.append({
                            'path': file_path,
                            'type': 'archivo (propietario)',
                            'current': file_owner,
                            'expected': owner_user
                        })
            
            if incorrect_perms:
                self.perms_results.append(f"Se encontraron {len(incorrect_perms)} discrepancias:\n")
                for item in incorrect_perms:
                    self.perms_results.append(
                        f"- {item['type']}: {item['path']}\n" +
                        f"  Actual: {item['current']} | Esperado: {item['expected']}\n"
                    )
            else:
                self.perms_results.append("✓ Todos los permisos y propietarios son correctos.")
            
            if self.logger:
                self.logger.info(f"Verificación de permisos completada para {directory}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al verificar permisos:\n{str(e)}")
            if self.logger:
                self.logger.error(f"Error al verificar permisos: {str(e)}")

    def fix_permissions(self):
        """Corregir permisos de archivos en el directorio"""
        directory = self.dir_path_input.text()
        
        if not directory or not os.path.isdir(directory):
            QMessageBox.warning(self, "Error", "Por favor seleccione un directorio válido.")
            return
        
        reply = QMessageBox.question(self, "Confirmar", 
                                   f"¿Está seguro de corregir los permisos en:\n{directory}?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            self.perms_results.append(f"\nCorrigiendo permisos en: {directory}\n")
            
            # Información de propietario y permisos
            owner_user = self.owner_user_input.text() or "www-data"
            dir_perms = self.dir_perms_input.text() or "755"
            file_perms = self.file_perms_input.text() or "644"
            
            # Recorrer directorio recursivamente
            fixed_count = 0
            
            for root, dirs, files in os.walk(directory):
                # Arreglar permisos de directorio
                try:
                    # Cambiar propietario
                    subprocess.run(["sudo", "chown", "-R", f"{owner_user}:{owner_user}", root], 
                                 capture_output=True, text=True)
                    
                    # Cambiar permisos
                    subprocess.run(["sudo", "chmod", dir_perms, root], 
                                 capture_output=True, text=True)
                    
                    fixed_count += 1
                except Exception as e:
                    self.perms_results.append(f"Error en directorio {root}: {str(e)}\n")
                
                # Arreglar permisos de archivos
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # Cambiar propietario
                        subprocess.run(["sudo", "chown", f"{owner_user}:{owner_user}", file_path], 
                                     capture_output=True, text=True)
                        
                        # Cambiar permisos
                        subprocess.run(["sudo", "chmod", file_perms, file_path], 
                                     capture_output=True, text=True)
                        
                        fixed_count += 1
                    except Exception as e:
                        self.perms_results.append(f"Error en archivo {file_path}: {str(e)}\n")
            
            self.perms_results.append(f"\n✓ {fixed_count} permisos corregidos exitosamente.")
            if self.logger:
                self.logger.info(f"Corrección de permisos completada para {directory}. {fixed_count} elementos corregidos.")
            
            QMessageBox.information(self, "Éxito", 
                                  f"Permisos corregidos exitosamente en {directory}\n{fixed_count} elementos actualizados.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al corregir permisos:\n{str(e)}")
            if self.logger:
                self.logger.error(f"Error al corregir permisos: {str(e)}")
        
    def create_menu(self):
        """Crear barra de menú"""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu('Archivo')
        
        exit_action = QAction('Salir', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Herramientas
        tools_menu = menubar.addMenu('Herramientas')
        
        # Submenú para cambiar tema
        theme_menu = tools_menu.addMenu('Cambiar Tema')
        self.light_theme_action = QAction('Tema Claro', self)
        self.dark_theme_action = QAction('Tema Oscuro', self)
        
        self.light_theme_action.setCheckable(True)
        self.dark_theme_action.setCheckable(True)
        
        self.light_theme_action.triggered.connect(lambda: self.set_theme('light'))
        self.dark_theme_action.triggered.connect(lambda: self.set_theme('dark'))
        
        # Por defecto, seleccionar tema claro
        self.light_theme_action.setChecked(True)
        
        theme_menu.addAction(self.light_theme_action)
        theme_menu.addAction(self.dark_theme_action)
        
        # Acción para credenciales en el menú de herramientas
        set_root_password_action = QAction('Establecer contraseña Root', self)
        set_root_password_action.triggered.connect(self.set_root_password)
        tools_menu.addAction(set_root_password_action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu('Ayuda')
        about_action = QAction('Acerca de', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def show_about(self):
        """Mostrar información de la aplicación"""
        QMessageBox.about(self, "Acerca de Pyginx", 
                         "Pyginx - GUI para gestión de servidores Nginx\n\nVersión: 1.0\nFecha: 2025")

    def set_root_password(self):
        """Solicitar y almacenar contraseña root"""
        from PyQt5.QtWidgets import QInputDialog
        password, ok = QInputDialog.getText(self, 'Contraseña Root', 
                                          'Ingrese la contraseña de root\n(Se almacenará temporalmente ofuscada):', 
                                          echo=QLineEdit.Password)
        
        if ok and password:
            self.nginx_manager.store_password(password)
            QMessageBox.information(self, "Contraseña Almacenada", 
                                  "La contraseña de root se ha almacenado temporalmente.")
            if self.logger:
                self.logger.info("Contraseña root almacenada temporalmente")
        else:
            QMessageBox.information(self, "Cancelado", 
                                  "No se ha almacenado ninguna contraseña.")

    def set_theme(self, theme):
        """Configurar el tema claro u oscuro"""
        app = QApplication.instance()
        
        if theme == 'dark':
            # Aplicar tema oscuro
            dark_palette = QPalette()
            
            # Colores para el tema oscuro
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
            dark_palette.setColor(QPalette.ToolTipText, Qt.white)
            dark_palette.setColor(QPalette.Text, Qt.white)
            dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white)
            dark_palette.setColor(QPalette.BrightText, Qt.red)
            dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, Qt.black)
            
            app.setPalette(dark_palette)
            app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a2a2a; border: 1px solid white; }")
            
            # Actualizar estado de los menús
            self.light_theme_action.setChecked(False)
            self.dark_theme_action.setChecked(True)
            
        elif theme == 'light':
            # Reiniciar al tema claro por defecto
            app.setPalette(app.style().standardPalette())
            app.setStyleSheet("")
            
            # Actualizar estado de los menús
            self.light_theme_action.setChecked(True)
            self.dark_theme_action.setChecked(False)


class LogFollowThread(QThread):
    """Thread para seguir un archivo de log en tiempo real"""
    log_signal = pyqtSignal(str)

    def __init__(self, log_file):
        super().__init__()
        self.log_file = log_file
        self.running = True

    def run(self):
        """Ejecutar el seguimiento del log"""
        import time
        try:
            # Obtener tamaño inicial del archivo
            file_size = os.path.getsize(self.log_file)
            
            while self.running:
                current_size = os.path.getsize(self.log_file)
                
                if current_size != file_size:
                    with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(file_size)  # Ir al final del archivo desde donde se quedó
                        new_content = f.read()
                        if new_content:
                            self.log_signal.emit(new_content)
                    
                    file_size = current_size
                
                time.sleep(0.5)  # Esperar medio segundo antes de verificar de nuevo
                
        except Exception as e:
            self.log_signal.emit(f"\n[ERROR] No se puede seguir el archivo de log: {str(e)}\n")

    def stop(self):
        """Detener el seguimiento del log"""
        self.running = False


def main():
    """Función principal"""
    # Configurar entorno virtual - esto reiniciará el script si es necesario
    python_executable = check_and_setup_virtual_env()
    
    # Ahora que estamos en el entorno virtual, verificar dependencias y configurar logging
    check_dependencies()

    # Importar colorama después de verificar dependencias
    try:
        from colorama import Fore, Style, init
        init(autoreset=True)
    except ImportError:
        # Si colorama no está disponible, crear clases vacías
        class EmptyColor:
            def __getattr__(self, name):
                return ""
        
        Fore = EmptyColor()
        Style = EmptyColor()

    # Configurar logging global
    logger = setup_logger()
    
    # Verificar que el sistema sea Linux
    nginx_manager = NginxManager(logger=logger)
    if not nginx_manager.check_system():
        try:
            from colorama import Fore
            print(f"{Fore.RED}Este script está diseñado para Linux.")
        except ImportError:
            print("Este script está diseñado para Linux.")
        sys.exit(1)
    
    # Verificar que Nginx esté instalado
    if not nginx_manager.check_nginx_installed():
        try:
            from colorama import Fore
            print(f"{Fore.RED}Nginx no está instalado en este sistema.")
            print(f"{Fore.YELLOW}Instale Nginx antes de usar esta herramienta.")
        except ImportError:
            print("Nginx no está instalado en este sistema.")
            print("Instale Nginx antes de usar esta herramienta.")
        sys.exit(1)
    
    logger.info("Iniciando Pyginx - Nginx GUI Manager")
    try:
        from colorama import Fore
        print(f"{Fore.CYAN}Iniciando Pyginx - Nginx GUI Manager...")
    except ImportError:
        print("Iniciando Pyginx - Nginx GUI Manager...")
    
    app = QApplication(sys.argv)
    window = PyginxApp(logger=logger)
    # Asignar el logger a la instancia de NginxManager de la ventana
    window.nginx_manager.logger = logger
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
