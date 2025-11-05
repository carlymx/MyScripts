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
- Indicador visual de estado del servidor
- Indicador visual de estado de inicio automático
- Sistema de temas (claro/oscuro)
- Gestión del inicio automático del servicio con el sistema
- Caja de direcciones para mostrar archivos de configuración
- Control de puerto directo en la interfaz

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
- Indicador visual de estado del servidor (verde/rojo/amarillo)
- Indicador visual de estado de inicio automático (verde/rojo/amarillo)
- Selección de tema claro/oscuro
- Aumento de tamaño de fuente en áreas de texto
- Habilitar/deshabilitar inicio automático de Nginx con el sistema
- Verificación del estado de inicio automático en la verificación de estado
- Caja de direcciones que muestra el archivo actual de configuración
- Control de puerto directo en la pestaña de configuración
- Seleccionar archivos de configuración personalizados
- Mejorado manejo de permisos para operaciones del sistema

## Estructura del Proyecto

- pyginx_manager.py: Archivo principal con toda la implementación
- .pyginx_env: Entorno virtual para dependencias
- .log/: Directorio para archivos de log
- .chat_log/resumen_conversacion.md: Resumen del desarrollo del proyecto
- backups/: Directorio para archivos de backup
- start_pyginx: Script para iniciar la aplicación

## Instrucciones para Iteraciones Futuras

1. Mantener las funcionalidades existentes operativas
2. Preservar el sistema de logging detallado
3. Mantener la compatibilidad con Linux y el manejo de privilegios root
4. Continuar usando PyQt5 para la interfaz gráfica
5. Asegurar que las nuevas características sean consistentes con el paradigma GUI
6. Respetar el sistema de perfiles de configuración existente
7. Mantener la ofuscación segura de la contraseña root
8. Preservar la verificación de permisos y funcionalidad de corrección automática
9. Mantener la compatibilidad con diferentes versiones de Linux
10. Asegurar la seguridad en la gestión de credenciales y operaciones privilegiadas
11. Mantener el sistema de indicador visual de estado actualizado
12. Preservar la funcionalidad de temas claro/oscuro
13. Mantener la organización de archivos de log en el directorio .log/
14. Preservar la funcionalidad de gestión del inicio automático con el sistema
15. Asegurar la correcta integración de la verificación del estado del inicio automático con la verificación general del servidor
16. Mantener el indicador visual adicional para el estado de inicio automático en la pestaña principal
17. Preservar la detección de puertos enfocándose en archivos de sitios habilitados (/etc/nginx/sites-enabled/)
18. Mantener el control de puerto directo en la pestaña de configuración
19. Preservar la caja de direcciones que muestra la ruta del archivo actual
20. Asegurar el manejo adecuado de permisos elevados para operaciones de sistema
21. Mantener la funcionalidad de selección de archivos de configuración personalizados

## Notas Adicionales

- El entorno virtual es creado automáticamente al iniciar la aplicación
- La contraseña root se almacena temporalmente y ofuscada
- La aplicación solo es compatible con sistemas Linux
- Los archivos de logs se generan automáticamente en el directorio .log/
- La herramienta de verificación de permisos permite especificar usuario propietario y permisos deseados
- El indicador visual muestra el estado del servidor con colores: verde (en línea), rojo (fuera de línea), amarillo (desconocido)
- El indicador visual adicional muestra el estado del inicio automático con colores: verde (habilitado), rojo (deshabilitado), amarillo (desconocido)
- La documentación del desarrollo se mantiene en .chat_log/resumen_conversacion.md
- La funcionalidad de inicio automático permite activar/desactivar el arranque de Nginx con el sistema
- El botón "Verificar Estado" ahora también actualiza el estado del inicio automático
- La detección de puertos se enfoca en archivos de sitios habilitados (/etc/nginx/sites-enabled/)
- La caja de direcciones muestra claramente qué archivo se está editando actualmente
- El sistema maneja correctamente operaciones que requieren permisos elevados
- El script start_pyginx facilita la ejecución de la aplicación
- Las operaciones de guardar, probar y crear backups utilizan sudo cuando es necesario para archivos del sistema