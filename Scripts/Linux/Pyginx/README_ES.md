[ESPAÑOL](README_ES.md) | [ENGLISH](README.md)

# Pyginx - Nginx GUI Manager

![image-001](./imgs/001.jpg)

## Descripción

Pyginx es una interfaz gráfica para la gestión de servidores Nginx en Linux. Proporciona una interfaz fácil de usar que permite a los usuarios controlar el servidor Nginx, visualizar logs, editar configuraciones y gestionar permisos de archivos.

## Características

- Iniciar, detener y reiniciar el servidor Nginx
- Verificar estado del servidor y puertos de escucha
- Visor de logs en tiempo real con funcionalidad de seguimiento
- Editor de configuración con soporte para perfiles
- Prueba de configuración y creación de backups
- Herramientas de verificación y corrección de permisos de archivos
- Almacenamiento seguro de contraseña root con ofuscación
- Sistema de logging detallado

## Instalación

1. Clona o descarga el repositorio
2. Ejecuta el script con Python 3: `python3 pyginx_manager.py`
3. La aplicación creará automáticamente un entorno virtual e instalará las dependencias requeridas

## Uso

1. Ejecuta el script: `python3 pyginx_manager.py`
2. La aplicación proporciona cuatro pestañas principales:
   - **Principal**: Control de Nginx (iniciar/detener/reiniciar/estado)
   - **Configuración**: Edición de archivos de configuración y gestión de perfiles
   - **Logs**: Visualización de logs de acceso y error en tiempo real
   - **Permisos**: Verificación y corrección de permisos de archivos

## Requisitos

- Sistema operativo Linux
- Python 3.x
- Nginx instalado en el sistema
- Privilegios root para ciertas operaciones

## Archivos de Documentación

- [README en inglés](README.md)
- [Instrucciones para Qwen CLI](QWEN.md)
- [Resumen de conversaciones](.chat_log/resumen_conversacion.md)

## Licencia

Este proyecto está creado con fines educativos y de uso personal.
