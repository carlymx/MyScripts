#!/bin/bash

# Script para crear entorno virtual e instalar el FTP Server Manager

# Nombre del entorno virtual
VENV_NAME="ftp_server_env"
SCRIPT_NAME="ftp_server_manager.py"

# Verificar si Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python3 no está instalado. Por favor, instálalo primero."
    exit 1
fi

# Verificar si python3-venv está instalado
if ! python3 -c "import venv" &> /dev/null; then
    echo "El módulo venv no está disponible. Instálalo con:"
    echo "sudo apt update && sudo apt install python3-venv"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "$VENV_NAME" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv "$VENV_NAME"
    
    if [ $? -ne 0 ]; then
        echo "Error al crear el entorno virtual. Asegúrate de tener python3-venv instalado:"
        echo "sudo apt update && sudo apt install python3-venv"
        exit 1
    fi
    
    # Activar entorno virtual
    source "$VENV_NAME/bin/activate"
    
    # Actualizar pip
    echo "Actualizando pip..."
    python -m pip install --upgrade pip
    
    # Instalar paquetes necesarios
    echo "Instalando paquetes necesarios..."
    pip install PyQt5 pyftpdlib colorama
    
    if [ $? -ne 0 ]; then
        echo "Error al instalar paquetes. Intenta instalar manualmente python3-venv:"
        echo "sudo apt update && sudo apt install python3-venv"
        exit 1
    fi
    
    echo "Entorno virtual creado y dependencias instaladas."
else
    echo "Entorno virtual ya existe."
fi

# Activar entorno virtual
source "$VENV_NAME/bin/activate"

# Verificar si el script existe
if [ ! -f "$SCRIPT_NAME" ]; then
    echo "Error: $SCRIPT_NAME no encontrado en el directorio actual."
    exit 1
fi

# Ejecutar el script
echo "Ejecutando FTP Server Manager..."
python "$SCRIPT_NAME"

echo "Script finalizado. Desactivando entorno virtual..."
# Desactivar entorno virtual al salir
deactivate