# 💾 SMARTCTL-MENU: Héroe del Monitoreo de Discos en Bash

## Portada
![SMARTCTL-MENU Logo](https://github.com/carlymx/MyScripts/blob/main/Scripts/Linux/smart_test_menu/logo.png?raw=true)

[![Estado del Test](https://img.shields.io/badge/Status-Activo-brightgreen)]()
[![Licencia](https://img.shields.io/badge/License-MIT-blue)]()
[![Escrito en Bash](https://img.shields.io/badge/Shell-Bash-orange)]()

## 📝 Descripción

**SMARTCTL-MENU** es un script de Bash interactivo diseñado para simplificar la gestión y el monitoreo de la salud de tus discos duros y SSDs mediante la herramienta **`smartctl`**.

Olvídate de memorizar comandos complejos y opciones de interfaz. Este script te guía a través de un menú sencillo para seleccionar el dispositivo, el formato de comunicación (SATA, NVMe, USB, etc.) y el tipo de test (Short, Long). Además, ofrece una **función clave de monitoreo en tiempo real** que te permite seguir el progreso de los tests lanzados, mostrando los resultados finales automáticamente.

## ✨ Características Principales

* **Detección Automática de Dispositivos:** Identifica discos SATA, SCSI y NVMe compatibles con SMART.
* **Menú de Configuración Guiada:** Selecciona el dispositivo, la interfaz (`-d`) y el tipo de test (`-t`) paso a paso.
* **Monitoreo en Tiempo Real:** Lanza el test y actualiza el estado y el progreso cada 30 segundos.
* **Pre-chequeo Inteligente:** Detecta si ya hay un test SMART en ejecución y ofrece monitorearlo en lugar de lanzar uno nuevo.
* **Reporte Final:** Muestra los resultados detallados del test cuando este finaliza.

## 🚀 Requisitos

* Sistema Operativo basado en Linux (Probado en Debian/Ubuntu/CentOS).
* Permisos de `sudo` para ejecutar `smartctl`.
* Instalar `smartmontools`:
    ```bash
    sudo apt update
    sudo apt install smartmontools -y  # Para Debian/Ubuntu
    # o
    sudo yum install smartmontools -y  # Para Fedora/CentOS/RHEL
    ```

## ⚙️ Flujo de Trabajo (Uso)

### 1. Clonar el Repositorio

### 2. Dar Permisos de Ejecución

```bash
chmod +x test_smart_menu.sh
```

### 3. Ejecutar el Script

```bash
./test_smart_menu.sh
```
### 4. Navegación por el Menú

El script te presentará el Menú Principal. Sigue estos pasos:

    Opción 1: Seleccionar dispositivo: El script detectará y listará todos los dispositivos SMART disponibles (ej. /dev/sda, /dev/nvme0n1).

    Opción 2: Seleccionar formato de comunicación: Elige el formato que mejor se adapte a tu disco (ej. auto, sat para SATA/USB, nvme). Esto asegura que smartctl se comunique correctamente.

    Opción 3: Seleccionar tipo de test: Elige el test que deseas ejecutar (short es rápido, long es exhaustivo).

    Opción 4: Verificar e iniciar test: Esta opción realiza una verificación final y:

        Si no hay test en curso, inicia el test seleccionado y comienza el monitoreo.

        Si ya hay un test en curso, te preguntará si deseas monitorearlo.


### 5. Monitoreo

Una vez iniciado o al elegir monitorear un test existente, el script entrará en un bucle de monitoreo en tiempo real, mostrando el estado y el progreso del test hasta que se complete.



## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si encuentras un error o tienes ideas para mejorar la detección de dispositivos o el parsing del progreso, no dudes en abrir un issue o enviar un Pull Request.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.





