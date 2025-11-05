# Instrucciones para Crear Script GUI de Control de Servidor FTP

## Propósito

Crear un script Python con interfaz gráfica (GUI) usando PyQT5 para controlar un servidor FTP mediante pyftpdlib.

## Características del Script

### Tipo de Aplicación

- GUI con PyQT5
- Compatible con Linux Mint

### Funcionalidades Principales

#### 1. Pestaña de Control del Servidor

- Botones para Iniciar, Detener y Reiniciar el servidor FTP
- Indicador del estado del servidor (en línea/fuera de línea)

#### 2. Pestaña de Configuración de Directorio

- Campo para seleccionar el directorio a compartir
- Visualización del directorio actual

#### 3. Pestaña de Configuración de Usuarios

- Gestión de usuarios (agregar, eliminar, modificar)
- Campos para nombre de usuario, contraseña
- Configuración de permisos (lectura, escritura, etc.)

#### 4. Pestaña de Permisos

- Verificación de permisos del directorio compartido
- Botón para corregir permisos si es necesario

#### 5. Pestaña de Editor de Configuración

- Visualización y edición de archivos de configuración
- Opciones para importar/exportar configuraciones

#### 6. Pestaña de Gestión de Perfiles

- Sistema de perfiles de configuración
- Lista de perfiles predeterminados: Predeterminado, A prueba de fallos, Seguridad extra, Simple
- Funcionalidad para crear nuevos perfiles

#### 7. Pestaña de Visualizador de Logs

- Visualización de logs de actividad del script
- Sistema de logging que registre:
  - Inicios/detener del servidor
  - Cambios en configuración
  - Errores detectados
  - Acciones del usuario

### Interacción con el Usuario

- Interfaz gráfica con PyQT5
- Interacción constante con el usuario a través de las diferentes pestañas

### Comandos del Sistema Integrados

- Comandos para verificar y manipular permisos de directorios/archivos
- Comandos para gestionar el proceso del servidor FTP
- Herramientas de sistema para diagnóstico de red

### Seguridad

- Actualmente no se implementan medidas especiales de seguridad
- Posibles mejoras de seguridad a considerar en el futuro:
  - Cifrado de contraseñas en la interfaz o almacenamiento
  - Validación de rutas para prevenir ataques de tipo path traversal
  - Control de acceso a la interfaz
  - Otros aspectos de seguridad específicos

### Estructura del Script

- Cabecera con metadatos y arte ASCII
- Detección del sistema operativo (Linux Mint)
- Instalación automática de dependencias (PyQt5, pyftpdlib, colorama)
- Manejo de Colorama para salida coloreada
- Sistema de logging con archivo de logs en subdirectorio
- Interfaz gráfica con PyQT5 organizada en pestañas
- Sistema de perfiles de configuración
- Funcionalidades de control del servidor FTP
- Verificación y corrección de permisos
- Módulo de visualización de logs
- Sistema de importación/exportación de configuraciones

### Dependencias Necesarias

- PyQt5
- pyftpdlib
- colorama
- logging
- os, sys, platform, subprocess, threading

### Notas Adicionales

- El script debe tener capacidad para reiniciar el servidor
- Incluir verificación de permisos y opción para corregirlos
- Crear sistema de perfiles predefinidos para diferentes configuraciones
- Importación y exportación de configuraciones
- Visualización de logs en una pestaña dedicada