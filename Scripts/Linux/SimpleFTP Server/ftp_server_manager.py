#!/usr/bin/env python3
##################################################################
#                                                                #
#             FTP SERVER MANAGER GUI - V1.0                      #
#                   2025-11-04                                   #
#             <NOMBRE_USUARIO> - user@mail.com                   #
#                                                                #
##################################################################

# Importación de bibliotecas estándar
import os
import sys
import platform
import subprocess
import logging
import json
import threading
from datetime import datetime
from pathlib import Path

# Manejo de dependencias
def check_and_install_dependencies():
    """Verifica e instala dependencias en entorno virtual"""
    required_packages = ["PyQt5", "pyftpdlib", "colorama"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"Paquetes faltantes: {', '.join(missing_packages)}")
        print("Por favor, instala los paquetes faltantes en tu entorno virtual:")
        print(f"pip install {' '.join(missing_packages)}")
        print("\nO ejecuta este script usando el script auxiliar: run_ftp_server.sh")
        return False
    return True

# Verificar dependencias
if not check_and_install_dependencies():
    sys.exit(1)

# Intentar importar las bibliotecas necesarias
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                                QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
                                QFileDialog, QHeaderView, QMessageBox, QCheckBox,
                                QGroupBox, QFormLayout, QComboBox, QInputDialog)
    from PyQt5.QtCore import QThread, pyqtSignal, QTimer
    from PyQt5.QtGui import QFont
except ImportError as e:
    print(f"Error crítico: No se pueden importar PyQt5: {e}")
    sys.exit(1)

try:
    from pyftpdlib.authorizers import DummyAuthorizer
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.servers import FTPServer
except ImportError as e:
    print(f"Error crítico: No se pueden importar pyftpdlib: {e}")
    sys.exit(1)

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    print("Advertencia: 'colorama' no está instalado. La salida no tendrá colores.")
    
    class EmptyColor:
        def __getattr__(self, name):
            return ""
    
    Fore = EmptyColor()
    Style = EmptyColor()

# Configuración de logging
def setup_logger():
    log_dir = Path.home() / ".ftp_server_manager" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file_path = log_dir / f"ftp_server_manager_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = logging.getLogger('ftp_manager_logger')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger, log_file_path

# Variables globales
logger, log_file_path = setup_logger()

# Arte ASCII para el banner
def print_banner():
    banner = r"""
  ____  _                            _     ____        _   
 |  _ \| | ___  __ _ _ __ __ _  __ _| |   / ___| _ __ (_) ___
 | |_) | |/ _ \/ _` | '__/ _` |/ _` | |   \___ \| '_ \| |/ _ \
 |  __/| |  __/ (_| | | | (_| | (_| | |    ___) | |_) | |  __/
 |_|   |_|\___|\__, |_|  \__,_|\__,_|_|   |____/| .__/|_|\___|
               |___/                             |_|           
    """
    print(Fore.CYAN + banner)
    print(Fore.YELLOW + "FTP Server Manager GUI")
    print(Fore.YELLOW + "-------------------------------------------------" + Style.RESET_ALL)

# Funciones de utilidad
def clear_screen():
    os.system('clear')

def get_system_info():
    return {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'architecture': platform.architecture()[0],
        'processor': platform.processor(),
        'machine': platform.machine(),
        'node': platform.node(),
        'python_version': platform.python_version()
    }

class FtpServerThread(QThread):
    """Hilo para ejecutar el servidor FTP"""
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()
    server_error = pyqtSignal(str)

    def __init__(self, port=21, directory="/tmp", users=None):
        super().__init__()
        self.port = port
        self.directory = directory
        self.users = users or []
        self.server = None
        self.running = False

    def run(self):
        try:
            # Crear autorizador
            authorizer = DummyAuthorizer()
            
            # Añadir usuarios configurados
            for user in self.users:
                if user.get('enabled', True):
                    perm = user.get('permissions', 'elradfmwMT')
                    authorizer.add_user(
                        user['username'], 
                        user['password'], 
                        self.directory, 
                        perm=perm
                    )
            
            # Añadir usuario anónimo si está habilitado
            if any(user.get('anonymous', False) for user in self.users):
                authorizer.add_anonymous(self.directory)
            
            # Crear handler
            handler = FTPHandler
            handler.authorizer = authorizer
            
            # Crear servidor
            address = ('0.0.0.0', self.port)
            self.server = FTPServer(address, handler)
            
            logger.info(f"Iniciando servidor FTP en puerto {self.port}")
            self.running = True
            self.server_started.emit()
            self.server.serve_forever()
            
        except Exception as e:
            error_msg = f"Error al iniciar servidor FTP: {str(e)}"
            logger.error(error_msg)
            self.server_error.emit(error_msg)
        finally:
            self.running = False
            if self.server:
                self.server.close_all()
            self.server_stopped.emit()

class FtpServerManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FTP Server Manager - GUI")
        self.setGeometry(100, 100, 1000, 700)
        
        # Variables de estado
        self.server_thread = None
        self.config_dir = Path.home() / ".ftp_server_manager"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.profiles_dir = self.config_dir / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)
        
        # Cargar configuración
        self.load_config()
        
        # Crear barra de menú
        self.create_menu_bar()
        
        # Crear interfaz
        self.create_interface()
        
        # Cargar perfiles predeterminados
        self.create_default_profiles()
        
        # Actualizar estado del servidor
        self.update_server_status()
        
        # Iniciar temporizador para actualizar el estado
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_server_status)
        self.status_timer.start(2000)  # Actualizar cada 2 segundos
        
        # Inicializar tema (por defecto claro)
        self.dark_theme = False

    def create_menu_bar(self):
        """Crea la barra de menú superior"""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu('Archivo')
        
        exit_action = file_menu.addAction('Salir')
        exit_action.triggered.connect(self.close)
        
        # Menú Herramientas
        tools_menu = menubar.addMenu('Herramientas')
        
        self.theme_action = tools_menu.addAction('Tema Oscuro')
        self.theme_action.setCheckable(True)
        self.theme_action.triggered.connect(self.toggle_theme)
        
        # Menú Ayuda
        help_menu = menubar.addMenu('Ayuda')
        
        about_action = help_menu.addAction('Acerca de')
        about_action.triggered.connect(self.show_about)

    def toggle_theme(self):
        """Cambia entre tema claro y oscuro"""
        if self.theme_action.isChecked():
            # Aplicar tema oscuro
            self.apply_dark_theme()
            self.dark_theme = True
            self.theme_action.setText('Tema Claro')
        else:
            # Aplicar tema claro
            self.apply_light_theme()
            self.dark_theme = False
            self.theme_action.setText('Tema Oscuro')

    def apply_dark_theme(self):
        """Aplica el tema oscuro"""
        dark_style = """
        QMainWindow, QWidget, QTabWidget, QTableWidget, QTextEdit, QGroupBox {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QLabel, QCheckBox, QRadioButton {
            color: #ffffff;
        }
        QPushButton {
            background-color: #3c3f41;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #4c4f51;
        }
        QPushButton:pressed {
            background-color: #2c2f31;
        }
        QLineEdit, QTextEdit, QComboBox {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 3px;
        }
        QTableWidget {
            alternate-background-color: #3c3c3c;
            gridline-color: #555555;
        }
        QHeaderView::section {
            background-color: #3c3f41;
            color: #ffffff;
            padding: 3px;
            border: 1px solid #555555;
        }
        QMenuBar {
            background-color: #3c3f41;
            color: #ffffff;
        }
        QMenuBar::item {
            background: transparent;
            padding: 4px 8px;
        }
        QMenuBar::item:selected {
            background: #555555;
        }
        QMenuBar::item:pressed {
            background: #666666;
        }
        QMenu {
            background-color: #3c3f41;
            color: #ffffff;
            border: 1px solid #555555;
        }
        QMenu::item {
            padding: 4px 20px;
        }
        QMenu::item:selected {
            background-color: #555555;
        }
        QStatusBar {
            background-color: #3c3f41;
            color: #ffffff;
        }
        """
        self.setStyleSheet(dark_style)

    def apply_light_theme(self):
        """Aplica el tema claro"""
        self.setStyleSheet("")

    def show_about(self):
        """Muestra información sobre la aplicación"""
        QMessageBox.about(self, "Acerca de", 
            "FTP Server Manager GUI\n\n"
            "Aplicación para controlar un servidor FTP\n"
            "con interfaz gráfica.\n\n"
            "Versión 1.0\n"
            "Python 3 - PyQT5")

    def create_interface(self):
        # Crear widget principal y layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Crear pestañas
        self.tabs = QTabWidget()
        
        # Crear cada pestaña
        self.create_server_control_tab()
        self.create_directory_tab()
        self.create_users_tab()
        self.create_permissions_tab()
        self.create_config_editor_tab()
        self.create_profiles_tab()
        self.create_logs_tab()
        
        # Añadir pestañas al widget
        self.tabs.addTab(self.server_control_widget, "Control del Servidor")
        self.tabs.addTab(self.directory_widget, "Directorio")
        self.tabs.addTab(self.users_widget, "Usuarios")
        self.tabs.addTab(self.permissions_widget, "Permisos")
        self.tabs.addTab(self.config_editor_widget, "Editor de Configuración")
        self.tabs.addTab(self.profiles_widget, "Perfiles")
        self.tabs.addTab(self.logs_widget, "Logs")
        
        # Añadir pestañas al layout principal
        main_layout.addWidget(self.tabs)
        
        # Añadir barra de estado
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Listo")

    def create_server_control_tab(self):
        self.server_control_widget = QWidget()
        layout = QVBoxLayout(self.server_control_widget)
        
        # Grupo de control del servidor
        server_group = QGroupBox("Control del Servidor FTP")
        server_layout = QVBoxLayout(server_group)
        
        # Controles
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Iniciar Servidor")
        self.stop_button = QPushButton("Detener Servidor")
        self.restart_button = QPushButton("Reiniciar Servidor")
        
        self.start_button.clicked.connect(self.start_server)
        self.stop_button.clicked.connect(self.stop_server)
        self.restart_button.clicked.connect(self.restart_server)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.restart_button)
        
        # Estado del servidor
        self.status_label = QLabel("Estado: Servidor detenido")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")
        
        # Puerto de servidor
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Puerto:"))
        self.port_input = QLineEdit("21")
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()
        
        server_layout.addLayout(control_layout)
        server_layout.addWidget(self.status_label)
        server_layout.addLayout(port_layout)
        server_layout.addStretch()
        
        layout.addWidget(server_group)

    def create_directory_tab(self):
        self.directory_widget = QWidget()
        layout = QVBoxLayout(self.directory_widget)
        
        # Grupo de directorio compartido
        dir_group = QGroupBox("Directorio Compartido")
        dir_layout = QVBoxLayout(dir_group)
        
        # Campo para directorio
        dir_input_layout = QHBoxLayout()
        dir_input_layout.addWidget(QLabel("Directorio:"))
        self.dir_input = QLineEdit(self.config.get('directory', '/tmp'))
        self.browse_button = QPushButton("Explorar")
        
        self.browse_button.clicked.connect(self.browse_directory)
        
        dir_input_layout.addWidget(self.dir_input)
        dir_input_layout.addWidget(self.browse_button)
        
        dir_layout.addLayout(dir_input_layout)
        
        # Botón para guardar
        save_dir_btn = QPushButton("Guardar Configuración")
        save_dir_btn.clicked.connect(self.save_directory_config)
        dir_layout.addWidget(save_dir_btn)
        
        layout.addWidget(dir_group)
        layout.addStretch()

    def create_users_tab(self):
        self.users_widget = QWidget()
        layout = QVBoxLayout(self.users_widget)
        
        # Grupo de usuarios
        users_group = QGroupBox("Gestión de Usuarios")
        users_layout = QVBoxLayout(users_group)
        
        # Tabla de usuarios
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(["Usuario", "Contraseña", "Permisos", "Habilitado", "Anónimo"])
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Botones de control
        btn_layout = QHBoxLayout()
        self.add_user_btn = QPushButton("Agregar Usuario")
        self.remove_user_btn = QPushButton("Eliminar Usuario")
        self.save_users_btn = QPushButton("Guardar Usuarios")
        
        self.add_user_btn.clicked.connect(self.add_user)
        self.remove_user_btn.clicked.connect(self.remove_user)
        self.save_users_btn.clicked.connect(self.save_users)
        
        btn_layout.addWidget(self.add_user_btn)
        btn_layout.addWidget(self.remove_user_btn)
        btn_layout.addWidget(self.save_users_btn)
        
        users_layout.addWidget(self.users_table)
        users_layout.addLayout(btn_layout)
        
        layout.addWidget(users_group)
        layout.addStretch()

    def create_permissions_tab(self):
        self.permissions_widget = QWidget()
        layout = QVBoxLayout(self.permissions_widget)
        
        # Grupo de permisos
        perm_group = QGroupBox("Verificación y Corrección de Permisos")
        perm_layout = QVBoxLayout(perm_group)
        
        # Campo para directorio
        perm_dir_layout = QHBoxLayout()
        perm_dir_layout.addWidget(QLabel("Directorio:"))
        self.perm_dir_input = QLineEdit(self.config.get('directory', '/tmp'))
        self.perm_browse_button = QPushButton("Explorar")
        
        self.perm_browse_button.clicked.connect(self.browse_permissions_directory)
        
        perm_dir_layout.addWidget(self.perm_dir_input)
        perm_dir_layout.addWidget(self.perm_browse_button)
        
        # Botones
        check_perm_btn = QPushButton("Verificar Permisos")
        fix_perm_btn = QPushButton("Corregir Permisos")
        
        check_perm_btn.clicked.connect(self.check_permissions)
        fix_perm_btn.clicked.connect(self.fix_permissions)
        
        perm_layout.addLayout(perm_dir_layout)
        perm_layout.addWidget(check_perm_btn)
        perm_layout.addWidget(fix_perm_btn)
        perm_layout.addStretch()
        
        layout.addWidget(perm_group)

    def create_config_editor_tab(self):
        self.config_editor_widget = QWidget()
        layout = QVBoxLayout(self.config_editor_widget)
        
        # Grupo de editor de configuración
        editor_group = QGroupBox("Editor de Configuración")
        editor_layout = QVBoxLayout(editor_group)
        
        # Editor de texto
        self.config_text = QTextEdit()
        
        # Botones
        btn_layout = QHBoxLayout()
        load_config_btn = QPushButton("Cargar Configuración")
        save_config_btn = QPushButton("Guardar Configuración")
        import_config_btn = QPushButton("Importar")
        export_config_btn = QPushButton("Exportar")
        
        load_config_btn.clicked.connect(self.load_config_from_editor)
        save_config_btn.clicked.connect(self.save_config_from_editor)
        import_config_btn.clicked.connect(self.import_config)
        export_config_btn.clicked.connect(self.export_config)
        
        btn_layout.addWidget(load_config_btn)
        btn_layout.addWidget(save_config_btn)
        btn_layout.addWidget(import_config_btn)
        btn_layout.addWidget(export_config_btn)
        
        editor_layout.addWidget(self.config_text)
        editor_layout.addLayout(btn_layout)
        
        layout.addWidget(editor_group)

    def create_profiles_tab(self):
        self.profiles_widget = QWidget()
        layout = QVBoxLayout(self.profiles_widget)
        
        # Grupo de perfiles
        profiles_group = QGroupBox("Gestión de Perfiles")
        profiles_layout = QVBoxLayout(profiles_group)
        
        # Selector de perfiles
        profile_select_layout = QHBoxLayout()
        profile_select_layout.addWidget(QLabel("Perfil:"))
        self.profile_combo = QComboBox()
        self.load_profiles_to_combo()
        
        profile_select_layout.addWidget(self.profile_combo)
        
        # Botones de perfil
        profile_btn_layout = QHBoxLayout()
        new_profile_btn = QPushButton("Nuevo Perfil")
        save_profile_btn = QPushButton("Guardar Perfil")
        load_profile_btn = QPushButton("Cargar Perfil")
        delete_profile_btn = QPushButton("Eliminar Perfil")
        
        new_profile_btn.clicked.connect(self.new_profile)
        save_profile_btn.clicked.connect(self.save_profile)
        load_profile_btn.clicked.connect(self.load_profile)
        delete_profile_btn.clicked.connect(self.delete_profile)
        
        profile_btn_layout.addWidget(new_profile_btn)
        profile_btn_layout.addWidget(save_profile_btn)
        profile_btn_layout.addWidget(load_profile_btn)
        profile_btn_layout.addWidget(delete_profile_btn)
        
        profiles_layout.addLayout(profile_select_layout)
        profiles_layout.addLayout(profile_btn_layout)
        profiles_layout.addStretch()
        
        layout.addWidget(profiles_group)

    def create_logs_tab(self):
        self.logs_widget = QWidget()
        layout = QVBoxLayout(self.logs_widget)
        
        # Grupo de logs
        logs_group = QGroupBox("Visualizador de Logs")
        logs_layout = QVBoxLayout(logs_group)
        
        # Visualizador de logs
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        
        # Botón para recargar logs
        reload_logs_btn = QPushButton("Recargar Logs")
        reload_logs_btn.clicked.connect(self.reload_logs)
        
        logs_layout.addWidget(self.logs_display)
        logs_layout.addWidget(reload_logs_btn)
        
        layout.addWidget(logs_group)
        
        # Cargar logs iniciales
        self.reload_logs()

    def load_config(self):
        """Carga la configuración desde el archivo"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                # Configuración por defecto
                self.config = {
                    'directory': '/tmp',
                    'port': 21,
                    'users': [
                        {'username': 'admin', 'password': 'admin', 'permissions': 'elradfmwMT', 'enabled': True, 'anonymous': False}
                    ]
                }
                self.save_config()
        except Exception as e:
            logger.error(f"Error al cargar configuración: {e}")
            self.config = {
                'directory': '/tmp',
                'port': 21,
                'users': [
                    {'username': 'admin', 'password': 'admin', 'permissions': 'elradfmwMT', 'enabled': True, 'anonymous': False}
                ]
            }

    def save_config(self):
        """Guarda la configuración al archivo"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuración guardada exitosamente")
        except Exception as e:
            logger.error(f"Error al guardar configuración: {e}")
            QMessageBox.critical(self, "Error", f"Error al guardar la configuración: {e}")

    def load_config_to_ui(self):
        """Carga la configuración a la interfaz"""
        self.dir_input.setText(self.config.get('directory', '/tmp'))
        self.perm_dir_input.setText(self.config.get('directory', '/tmp'))
        self.port_input.setText(str(self.config.get('port', 21)))
        
        # Cargar usuarios en la tabla
        self.load_users_to_table()

    def load_users_to_table(self):
        """Carga los usuarios a la tabla"""
        self.users_table.setRowCount(0)
        for user in self.config.get('users', []):
            row_position = self.users_table.rowCount()
            self.users_table.insertRow(row_position)
            
            self.users_table.setItem(row_position, 0, QTableWidgetItem(user['username']))
            self.users_table.setItem(row_position, 1, QTableWidgetItem(user['password']))
            self.users_table.setItem(row_position, 2, QTableWidgetItem(user['permissions']))
            
            enabled_checkbox = QCheckBox()
            enabled_checkbox.setChecked(user.get('enabled', True))
            self.users_table.setCellWidget(row_position, 3, enabled_checkbox)
            
            anonymous_checkbox = QCheckBox()
            anonymous_checkbox.setChecked(user.get('anonymous', False))
            self.users_table.setCellWidget(row_position, 4, anonymous_checkbox)

    def save_users_from_table(self):
        """Guarda los usuarios desde la tabla"""
        users = []
        for row in range(self.users_table.rowCount()):
            username_item = self.users_table.item(row, 0)
            password_item = self.users_table.item(row, 1)
            permissions_item = self.users_table.item(row, 2)
            
            if username_item and password_item and permissions_item:
                username = username_item.text()
                password = password_item.text()
                permissions = permissions_item.text()
                
                enabled_checkbox = self.users_table.cellWidget(row, 3)
                anonymous_checkbox = self.users_table.cellWidget(row, 4)
                
                user = {
                    'username': username,
                    'password': password,
                    'permissions': permissions,
                    'enabled': enabled_checkbox.isChecked() if enabled_checkbox else True,
                    'anonymous': anonymous_checkbox.isChecked() if anonymous_checkbox else False
                }
                users.append(user)
        
        self.config['users'] = users

    def start_server(self):
        """Inicia el servidor FTP"""
        if self.server_thread and self.server_thread.running:
            QMessageBox.warning(self, "Advertencia", "El servidor ya está en ejecución.")
            return
        
        try:
            port = int(self.port_input.text())
        except ValueError:
            QMessageBox.critical(self, "Error", "Puerto inválido. Debe ser un número.")
            return
        
        directory = self.dir_input.text()
        if not os.path.isdir(directory):
            QMessageBox.critical(self, "Error", "El directorio especificado no existe.")
            return
        
        # Guardar configuración antes de iniciar
        self.save_directory_config()
        
        # Crear y lanzar hilo del servidor
        self.server_thread = FtpServerThread(
            port=port,
            directory=directory,
            users=self.config.get('users', [])
        )
        
        self.server_thread.server_started.connect(self.on_server_started)
        self.server_thread.server_stopped.connect(self.on_server_stopped)
        self.server_thread.server_error.connect(self.on_server_error)
        
        self.server_thread.start()
        logger.info(f"Intentando iniciar servidor FTP en puerto {port}")

    def stop_server(self):
        """Detiene el servidor FTP"""
        if self.server_thread and self.server_thread.running:
            logger.info("Deteniendo servidor FTP")
            if self.server_thread.server:
                self.server_thread.server.close_all()
            self.server_thread.running = False
            self.server_thread.quit()
            self.server_thread.wait()
            self.server_thread = None
            logger.info("Servidor FTP detenido")
        else:
            QMessageBox.information(self, "Información", "El servidor no está en ejecución.")

    def restart_server(self):
        """Reinicia el servidor FTP"""
        self.stop_server()
        # Pequeña pausa antes de reiniciar
        QTimer.singleShot(1000, self.start_server)

    def on_server_started(self):
        """Maneja el evento de servidor iniciado"""
        self.status_label.setText("Estado: Servidor en ejecución")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        self.status_bar.showMessage("Servidor FTP iniciado correctamente", 3000)
        logger.info("Servidor FTP iniciado correctamente")

    def on_server_stopped(self):
        """Maneja el evento de servidor detenido"""
        self.status_label.setText("Estado: Servidor detenido")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")
        self.status_bar.showMessage("Servidor FTP detenido", 3000)
        logger.info("Servidor FTP detenido")

    def on_server_error(self, error_msg):
        """Maneja errores del servidor"""
        self.status_label.setText("Estado: Error")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")
        QMessageBox.critical(self, "Error del Servidor", error_msg)
        logger.error(f"Error del servidor FTP: {error_msg}")

    def update_server_status(self):
        """Actualiza el estado del servidor"""
        if self.server_thread and self.server_thread.running:
            self.status_label.setText("Estado: Servidor en ejecución")
            self.status_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.status_label.setText("Estado: Servidor detenido")
            self.status_label.setStyleSheet("font-weight: bold; color: red;")

    def browse_directory(self):
        """Abre el diálogo para seleccionar directorio"""
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio Compartido", self.dir_input.text())
        if directory:
            self.dir_input.setText(directory)
            self.perm_dir_input.setText(directory)

    def save_directory_config(self):
        """Guarda la configuración del directorio"""
        directory = self.dir_input.text()
        if not os.path.isdir(directory):
            QMessageBox.critical(self, "Error", "El directorio especificado no existe.")
            return
        
        self.config['directory'] = directory
        self.save_config()
        self.status_bar.showMessage(f"Directorio configurado a: {directory}", 3000)
        logger.info(f"Directorio actualizado a: {directory}")

    def add_user(self):
        """Agrega un nuevo usuario a la tabla"""
        row_position = self.users_table.rowCount()
        self.users_table.insertRow(row_position)
        
        # Crear widgets por defecto
        self.users_table.setItem(row_position, 0, QTableWidgetItem("nuevo_usuario"))
        self.users_table.setItem(row_position, 1, QTableWidgetItem("contraseña"))
        self.users_table.setItem(row_position, 2, QTableWidgetItem("elradfmwMT"))
        
        enabled_checkbox = QCheckBox()
        enabled_checkbox.setChecked(True)
        self.users_table.setCellWidget(row_position, 3, enabled_checkbox)
        
        anonymous_checkbox = QCheckBox()
        anonymous_checkbox.setChecked(False)
        self.users_table.setCellWidget(row_position, 4, anonymous_checkbox)

    def remove_user(self):
        """Elimina el usuario seleccionado"""
        current_row = self.users_table.currentRow()
        if current_row >= 0:
            self.users_table.removeRow(current_row)
        else:
            QMessageBox.information(self, "Información", "Por favor, seleccione un usuario para eliminar.")

    def save_users(self):
        """Guarda los usuarios"""
        self.save_users_from_table()
        self.save_config()
        self.status_bar.showMessage("Usuarios guardados correctamente", 3000)
        logger.info("Usuarios guardados correctamente")

    def browse_permissions_directory(self):
        """Abre el diálogo para seleccionar directorio de permisos"""
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio", self.perm_dir_input.text())
        if directory:
            self.perm_dir_input.setText(directory)

    def check_permissions(self):
        """Verifica los permisos del directorio"""
        directory = self.perm_dir_input.text()
        if not os.path.isdir(directory):
            QMessageBox.critical(self, "Error", "El directorio especificado no existe.")
            return
        
        try:
            # Obtener información sobre el directorio
            stat_info = os.stat(directory)
            permissions = oct(stat_info.st_mode)[-3:]
            
            # Verificar si es escribible
            is_writable = os.access(directory, os.W_OK)
            is_readable = os.access(directory, os.R_OK)
            is_executable = os.access(directory, os.X_OK)
            
            msg = f"Directorio: {directory}\n"
            msg += f"Permisos: {permissions}\n"
            msg += f"Lectura: {'Sí' if is_readable else 'No'}\n"
            msg += f"Escritura: {'Sí' if is_writable else 'No'}\n"
            msg += f"Ejecución: {'Sí' if is_executable else 'No'}\n"
            
            QMessageBox.information(self, "Verificación de Permisos", msg)
            logger.info(f"Verificación de permisos para {directory}: {msg}")
        except Exception as e:
            error_msg = f"Error al verificar permisos: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(error_msg)

    def fix_permissions(self):
        """Corrige los permisos del directorio"""
        directory = self.perm_dir_input.text()
        if not os.path.isdir(directory):
            QMessageBox.critical(self, "Error", "El directorio especificado no existe.")
            return
        
        try:
            # Intentar cambiar permisos al directorio (solo en sistemas Unix)
            subprocess.run(['chmod', '755', directory], check=True)
            
            # Aplicar recursivamente a subdirectorios y archivos
            subprocess.run(['find', directory, '-type', 'd', '-exec', 'chmod', '755', '{}', ';'], check=True)
            subprocess.run(['find', directory, '-type', 'f', '-exec', 'chmod', '644', '{}', ';'], check=True)
            
            QMessageBox.information(self, "Éxito", f"Permisos corregidos para {directory}")
            logger.info(f"Permisos corregidos para {directory}")
        except subprocess.CalledProcessError as e:
            error_msg = f"Error al corregir permisos: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(error_msg)
        except Exception as e:
            error_msg = f"Error general al corregir permisos: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(error_msg)

    def load_config_from_editor(self):
        """Carga la configuración desde el editor de texto"""
        try:
            config_data = json.loads(self.config_text.toPlainText())
            self.config = config_data
            self.load_config_to_ui()
            self.status_bar.showMessage("Configuración cargada desde editor", 3000)
            logger.info("Configuración cargada desde editor")
        except json.JSONDecodeError as e:
            error_msg = f"Error al decodificar JSON: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(error_msg)
        except Exception as e:
            error_msg = f"Error al cargar configuración desde editor: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(error_msg)

    def save_config_from_editor(self):
        """Guarda la configuración desde el editor de texto"""
        try:
            config_data = json.loads(self.config_text.toPlainText())
            self.config = config_data
            self.save_config()
            
            # Actualizar la UI con la nueva configuración
            self.load_config_to_ui()
            self.status_bar.showMessage("Configuración guardada desde editor", 3000)
            logger.info("Configuración guardada desde editor")
        except json.JSONDecodeError as e:
            error_msg = f"Error al decodificar JSON: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(error_msg)
        except Exception as e:
            error_msg = f"Error al guardar configuración desde editor: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(error_msg)

    def import_config(self):
        """Importa configuración desde archivo"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Importar Configuración", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config_data = json.load(f)
                
                self.config = config_data
                self.load_config_to_ui()
                self.save_config()
                self.status_bar.showMessage(f"Configuración importada desde {file_path}", 3000)
                logger.info(f"Configuración importada desde {file_path}")
            except Exception as e:
                error_msg = f"Error al importar configuración: {str(e)}"
                QMessageBox.critical(self, "Error", error_msg)
                logger.error(error_msg)

    def export_config(self):
        """Exporta configuración a archivo"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar Configuración", "config.json", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                
                self.status_bar.showMessage(f"Configuración exportada a {file_path}", 3000)
                logger.info(f"Configuración exportada a {file_path}")
            except Exception as e:
                error_msg = f"Error al exportar configuración: {str(e)}"
                QMessageBox.critical(self, "Error", error_msg)
                logger.error(error_msg)

    def load_profiles_to_combo(self):
        """Carga los perfiles disponibles en el combo"""
        self.profile_combo.clear()
        
        # Añadir perfiles predeterminados
        default_profiles = ["Predeterminado", "A prueba de fallos", "Seguridad extra", "Simple"]
        for profile in default_profiles:
            self.profile_combo.addItem(profile)
        
        # Añadir perfiles personalizados
        for profile_file in self.profiles_dir.glob("*.json"):
            profile_name = profile_file.stem
            if profile_name not in default_profiles:
                self.profile_combo.addItem(profile_name)

    def create_default_profiles(self):
        """Crea perfiles predeterminados si no existen"""
        default_profiles = {
            "Predeterminado": {
                'directory': '/tmp',
                'port': 21,
                'users': [
                    {'username': 'admin', 'password': 'admin', 'permissions': 'elradfmwMT', 'enabled': True, 'anonymous': False}
                ]
            },
            "A prueba de fallos": {
                'directory': '/tmp',
                'port': 2121,
                'users': [
                    {'username': 'debug', 'password': 'debug', 'permissions': 'elr', 'enabled': True, 'anonymous': False}
                ]
            },
            "Seguridad extra": {
                'directory': '/home/' + os.getenv('USER', 'ftp') + '/ftp_share',
                'port': 2122,
                'users': [
                    {'username': 'secure_user', 'password': 'SecureP@ss123', 'permissions': 'elr', 'enabled': True, 'anonymous': False}
                ]
            },
            "Simple": {
                'directory': '/tmp',
                'port': 21,
                'users': [
                    {'username': 'user', 'password': 'password', 'permissions': 'elr', 'enabled': True, 'anonymous': False}
                ]
            }
        }
        
        for profile_name, profile_data in default_profiles.items():
            profile_file = self.profiles_dir / f"{profile_name}.json"
            if not profile_file.exists():
                with open(profile_file, 'w') as f:
                    json.dump(profile_data, f, indent=2)

    def new_profile(self):
        """Crea un nuevo perfil"""
        profile_name, ok = QInputDialog.getText(self, "Nuevo Perfil", "Nombre del nuevo perfil:")
        if ok and profile_name:
            # Validar nombre de perfil
            if any(c in profile_name for c in '<>:"/\\|?*'):
                QMessageBox.critical(self, "Error", "Nombre de perfil inválido. No puede contener caracteres especiales.")
                return
            
            profile_file = self.profiles_dir / f"{profile_name}.json"
            if profile_file.exists():
                reply = QMessageBox.question(self, "Confirmar", f"El perfil '{profile_name}' ya existe. ¿Desea sobrescribirlo?")
                if reply != QMessageBox.Yes:
                    return
            
            # Crear perfil con configuración actual
            with open(profile_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.load_profiles_to_combo()
            self.profile_combo.setCurrentText(profile_name)
            self.status_bar.showMessage(f"Perfil '{profile_name}' creado", 3000)
            logger.info(f"Perfil '{profile_name}' creado")

    def save_profile(self):
        """Guarda el perfil actual"""
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            QMessageBox.information(self, "Información", "Por favor, seleccione un perfil para guardar.")
            return
        
        profile_file = self.profiles_dir / f"{profile_name}.json"
        reply = QMessageBox.question(self, "Confirmar", f"¿Desea sobrescribir el perfil '{profile_name}' con la configuración actual?")
        if reply == QMessageBox.Yes:
            with open(profile_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.status_bar.showMessage(f"Perfil '{profile_name}' guardado", 3000)
            logger.info(f"Perfil '{profile_name}' guardado")

    def load_profile(self):
        """Carga un perfil"""
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            QMessageBox.information(self, "Información", "Por favor, seleccione un perfil para cargar.")
            return
        
        profile_file = self.profiles_dir / f"{profile_name}.json"
        if not profile_file.exists():
            QMessageBox.critical(self, "Error", f"El perfil '{profile_name}' no existe.")
            return
        
        try:
            with open(profile_file, 'r') as f:
                profile_data = json.load(f)
            
            self.config = profile_data
            self.load_config_to_ui()
            self.save_config()
            self.status_bar.showMessage(f"Perfil '{profile_name}' cargado", 3000)
            logger.info(f"Perfil '{profile_name}' cargado")
        except Exception as e:
            error_msg = f"Error al cargar perfil: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(error_msg)

    def delete_profile(self):
        """Elimina un perfil"""
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            QMessageBox.information(self, "Información", "Por favor, seleccione un perfil para eliminar.")
            return
        
        if profile_name in ["Predeterminado", "A prueba de fallos", "Seguridad extra", "Simple"]:
            QMessageBox.critical(self, "Error", "No se puede eliminar un perfil predeterminado.")
            return
        
        reply = QMessageBox.question(self, "Confirmar", f"¿Desea eliminar permanentemente el perfil '{profile_name}'?")
        if reply == QMessageBox.Yes:
            profile_file = self.profiles_dir / f"{profile_name}.json"
            if profile_file.exists():
                profile_file.unlink()
            
            self.load_profiles_to_combo()
            self.status_bar.showMessage(f"Perfil '{profile_name}' eliminado", 3000)
            logger.info(f"Perfil '{profile_name}' eliminado")

    def reload_logs(self):
        """Recarga y muestra los logs"""
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                logs_content = f.read()
            
            self.logs_display.setPlainText(logs_content)
            
            # Desplazar al final
            self.logs_display.moveCursor(1, 2)  # Ir al final del texto
        except Exception as e:
            error_msg = f"Error al leer logs: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(error_msg)

def main():
    print_banner()
    logger.info("Iniciando FTP Server Manager GUI")
    
    app = QApplication(sys.argv)
    
    # Configurar fuente principal
    font = QFont()
    font.setPointSize(9)
    app.setFont(font)
    
    window = FtpServerManager()
    window.show()
    
    # Cargar configuración inicial a la UI
    window.load_config_to_ui()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()