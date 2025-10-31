# Desinstalador de Qwen CLI

[English](README.md) | [Español](README_ES.md)

## Descripción General

Este repositorio contiene un script de desinstalación completo para eliminar Qwen CLI y su entorno Node.js de sistemas basados en Arch Linux.

## Descripción

El script `desisntalar_QwenCli.sh` proporciona una solución de limpieza completa para:
- Paquetes npm globales de Qwen CLI
- Paquetes de sistema Node.js y npm
- Directorios de configuración y archivos de caché
- Instalaciones de nvm (Node Version Manager)
- Entradas de configuración del shell

## Uso

```bash
# Hacer el script ejecutable
chmod +x desisntalar_QwenCli.sh

# Ejecutar el desinstalador
./desisntalar_QwenCli.sh

Qué Hace el Script

    Detiene procesos de Qwen en ejecución

    Desinstala Qwen CLI globalmente mediante npm

    Remueve paquetes de sistema (nodejs, npm) usando pacman/yay

    Limpia directorios de configuración (.qwen, .config/qwen, .cache/qwen)

    Remueve directorios de nvm y npm

    Limpia configuraciones del shell (.bashrc, .zshrc, .profile)

    Limpia caché de npm

    Verifica procesos y archivos restantes

Advertencia

⚠️ Este script realiza una limpieza extensiva del sistema. Use con precaución ya que:

    Eliminará todas las instalaciones de Qwen CLI

    Desinstalará Node.js y npm de su sistema

    Borrará archivos de configuración y datos de caché

    Modificará sus archivos de configuración del shell

Recomendaciones

    Cierre y reabra su terminal después de ejecutar el script

    Revise el script antes de ejecutarlo si tiene configuraciones personalizadas de Node.js

    Haga backup de archivos de configuración importantes si es necesario

Compatibilidad

Diseñado para Arch Linux y derivados (Manjaro, EndeavourOS, etc.)
text


Ambos archivos README incluyen:
- Enlace relativo al otro README al inicio
- Descripción clara del propósito del script
- Instrucciones de uso
- Lista detallada de acciones que realiza el script
- Advertencias sobre el alcance de la limpieza
- Recomendaciones de uso
- Información de compatibilidad

