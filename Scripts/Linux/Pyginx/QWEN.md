# Instrucciones para Pyginx - Nginx GUI Manager

## Idioma

Todo el desarrollo y documentación debe estar en castellano (español).

## Propósito del Proyecto

Pyginx es una aplicación GUI para la gestión de servidores Nginx en Linux. Proporciona una interfaz gráfica que permite controlar el servidor Nginx, visualizar logs, editar configuraciones y gestionar permisos de archivos.

## Componentes Principales

- Interfaz gráfica desarrollada con PyQt5
- Sistema de logging detallado
- Gestión de dependencias con entorno virtual
- Control de Nginx (start/stop/restart/status)
- Visualización de logs con seguimiento en tiempo real
- Editor de configuración con soporte para perfiles
- Gestión de permisos de archivos

## Funcionalidades

- Iniciar, detener y reiniciar Nginx
- Verificar estado y puertos de escucha
- Visualizar logs de acceso y error
- Editar archivo de configuración principal
- Cargar/guardar perfiles de configuración
- Probar la configuración de Nginx
- Crear backups del archivo de configuración
- Verificar y corregir permisos de archivos
- Almacenamiento seguro de contraseña root

## Estructura del Proyecto

- pyginx_manager.py: Archivo principal con toda la implementación
- .pyginx_env: Entorno virtual para dependencias
- .chat_log/resumen_conversacion.md: Resumen del desarrollo del proyecto

## Instrucciones para Iteraciones Futuras

1. Mantener las funcionalidades existentes operativas
2. Preservar el sistema de logging detallado
3. Mantener la compatibilidad con Linux y el manejo de privilegios root
4. Continuar usando PyQt5 para la interfaz gráfica
5. Asegurar que las nuevas características sean consistentes con el paradigma GUI
6. Respetar el sistema de perfiles de configuración existente
7. Mantener la ofuscación segura de la contraseña root
8. Preservar la verificación de permisos y funcionalidad de corrección automática

## Notas Adicionales

- El entorno virtual es creado automáticamente al iniciar la aplicación
- La contraseña root se almacena temporalmente y ofuscada
- La aplicación solo es compatible con sistemas Linux
- Los archivos de logs se generan automáticamente en el directorio del proyecto
- La herramienta de verificación de permisos permite especificar usuario propietario y permisos deseados