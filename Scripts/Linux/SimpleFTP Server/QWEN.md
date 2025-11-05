# Instrucciones para Qwen CLI - FTP Server Manager GUI

## Idioma
Este proyecto debe mantenerse en castellano (español) para todos los comentarios, documentación y mensajes de usuario.

## Propósito del Proyecto
FTP Server Manager GUI es una aplicación de escritorio que proporciona una interfaz gráfica para controlar un servidor FTP basado en pyftpdlib. Permite a los usuarios gestionar servidores FTP con una interfaz intuitiva con pestañas para diferentes funcionalidades.

## Componentes Principales
- `ftp_server_manager.py`: Script principal con la interfaz gráfica PyQT5
- `run_ftp_server.sh`: Script de automatización para crear entorno virtual y ejecutar la aplicación
- `requirements.txt`: Dependencias del proyecto
- `instrucciones.md`: Documentación de las funcionalidades solicitadas
- `README.md` y `README_ES.md`: Documentación del proyecto

## Funcionalidades Implementadas
- Interfaz gráfica con PyQT5 organizada en pestañas
- Control del servidor FTP (iniciar, detener, reiniciar)
- Configuración del directorio compartido
- Gestión de usuarios con sistema de permisos
- Verificación y corrección de permisos de archivos/directorios
- Editor de configuración
- Sistema de perfiles con configuraciones predeterminadas
- Visualizador de logs
- Sistema de logging completo
- Barra de menú superior con opciones de tema
- Cambio entre tema claro y oscuro

## Uso del Proyecto
1. Ejecutar `./run_ftp_server.sh` para crear el entorno virtual y ejecutar la aplicación
2. Alternativamente, crear manualmente un entorno virtual e instalar dependencias
3. Ejecutar `python ftp_server_manager.py`

## Estructura del Proyecto
- El directorio principal contiene todos los archivos esenciales
- El directorio `.chat_log` contiene archivos de registro de conversaciones
- La configuración se almacena en `~/.ftp_server_manager/`
- Los logs se almacenan en `~/.ftp_server_manager/logs/`

## Instrucciones para Futuras Iteraciones
1. Mantener la interfaz en español
2. Preservar la funcionalidad existente mientras se agregan nuevas características
3. Seguir el patrón de pestañas para nuevas funcionalidades
4. Asegurar la compatibilidad con Linux Mint
5. Mantener el sistema de logging
6. Continuar usando PyQT5 para la interfaz gráfica
7. Preservar el sistema de perfiles de configuración
8. Referenciar `.chat_log/resumen_conversacion.md` para contexto histórico
9. Actualizar `.chat_log/resumen_conversacion.md` con cambios importantes
10. Mantener consistencia entre todos los archivos de documentación

## Archivos de Documentación
- [Resumen de conversaciones](.chat_log/resumen_conversacion.md) - Registro de decisiones y cambios
- [README en inglés](README.md) - Documentación principal del proyecto
- [README en español](README_ES.md) - Versión en español de la documentación