[ESPAÑOL](README_ES.md) | [ENGLISH](README.md)

# FTP Server Manager GUI (beta)

Aplicación GUI para controlar un servidor FTP simple y rápido con pyftpdlib.

## Requisitos

- Python 3.6 o superior
- Módulo `venv` para Python (en Linux: `python3-venv`)

## Instalación y uso

### Opción 1: Usar script automático (recomendado)

Ejecuta el script `run_ftp_server.sh` que creará automáticamente un entorno virtual e instalará las dependencias:

```bash
./run_ftp_server.sh
```

Este script:

1. Crea un entorno virtual llamado `ftp_server_env`
2. Instala las dependencias necesarias
3. Ejecuta el FTP Server Manager

### Opción 2: Instalación manual

1. Crea un entorno virtual:
   
   ```bash
   python3 -m venv ftp_server_env
   ```

2. Activa el entorno virtual:
   
   ```bash
   source ftp_server_env/bin/activate  # En Linux/Mac
   # o
   ftp_server_env\Scripts\activate  # En Windows
   ```

3. Instala las dependencias:
   
   ```bash
   pip install PyQt5 pyftpdlib colorama
   ```

4. Ejecuta el script:
   
   ```bash
   python ftp_server_manager.py
   ```

## Características

- Interfaz gráfica con PyQT5
- Control del servidor FTP (iniciar, detener, reiniciar)
- Configuración del directorio compartido
- Gestión de usuarios con permisos
- Verificación y corrección de permisos
- Editor de configuración
- Sistema de perfiles con configuraciones predeterminadas
- Visualizador de logs
- Barra de menú superior con opciones de tema claro/oscuro

## Notas

- El script almacena configuraciones en `~/.ftp_server_manager/`
- Los logs se guardan en `~/.ftp_server_manager/logs/`
- La primera ejecución creará la estructura de directorios necesaria
- Incluye un menú "Herramientas" con opción para cambiar entre tema claro y oscuro

## Archivos de Documentación

- [README en inglés](README.md)
- [Instrucciones para Qwen CLI](QWEN.md)
- [Resumen de conversaciones](.chat_log/resumen_conversacion.md)