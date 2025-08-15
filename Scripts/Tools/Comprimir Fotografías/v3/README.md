[📹 Ver video del funcionamiento](https://i.imgur.com/HMyX58j.mp4)

# Conversor y Compresor de Imágenes RAW a Formatos Comunes — v3.3

## 📌 Descripción

Este script en Python permite **convertir y comprimir fotografías** en formato RAW y otros formatos de imagen a formatos más comunes como **JPG**, **PNG**, **TIFF**, entre otros.  
Está diseñado para ser **multiplataforma**, detectando automáticamente el sistema operativo (**Windows** o **Linux**) y gestionando la instalación de dependencias necesarias.  
Es capaz de trabajar con **gran volumen de imágenes** en múltiples subdirectorios sin saturar los recursos del sistema gracias a su modo **multiproceso** configurable.

## ✨ Características Principales

- **Detección automática del sistema operativo** (Windows / Linux).
- **Instalación automática de dependencias**:
  - En Linux, crea y utiliza un entorno virtual (`venv`) si es necesario.
  - Instala `Pillow`, `piexif` y `colorama` si faltan.
- **Exploración de directorios** para listar tipos y cantidades de archivos encontrados.
- **Soporte para múltiples formatos de entrada**: RAW, NEF, CR2, ARW, JPG, JPEG, PNG, TIFF, BMP, GIF, etc.
- **Selección de formato de salida por número**: JPG, JPEG, PNG, TIFF.
- **Opciones de compresión**:
  - **JPG/JPEG**: calidad (1–100, por defecto 70).
  - **TIFF**: sin compresión, LZW, ZIP o JPEG (con pérdida).
  - **PNG**: nivel de compresión (0–9, por defecto 6, compresión sin pérdida).
- **Tamaño límite (KB)** para procesar solo archivos grandes.
- **Conserva metadatos EXIF** cuando es posible.
- **Recrea la estructura de directorios** del origen en el destino.
- **Modo secuencial o multiproceso configurable**:
  - Detecta número de CPUs disponibles.
  - El usuario elige cuántos procesos paralelos usar.
- **Registro detallado en un archivo `.log`** con rutas, errores y resumen del proceso.
- **Conversión automática de imágenes con transparencia (RGBA, LA) a RGB** al guardar en JPG/JPEG.
- **Interfaz más clara** con banner ASCII, colores y confirmación antes de iniciar el proceso.

## 🛠️ Funcionamiento

1. El script detecta el sistema operativo.
2. Comprueba e instala dependencias automáticamente.
3. Solicita el directorio de origen y valida que existan imágenes compatibles.
4. Escanea y muestra un resumen de formatos y cantidades encontradas.
5. Pregunta el directorio de destino (por defecto crea uno junto al original con sufijo `_convertidos`).
6. Solicita el formato de salida y sus opciones de compresión según el formato elegido.
7. Pregunta el tamaño límite (en KB) para decidir qué imágenes procesar.
8. Pregunta cuántos procesos usar (1 = secuencial, >1 = multiproceso).
9. Muestra un resumen de la configuración y pide confirmación.
10. Procesa las imágenes conservando EXIF y estructura de carpetas.
11. Guarda un registro detallado en un archivo `.log` dentro del directorio `logs`.

## 📂 Estructura de Salida

```
fotos_convertidos/
 ├── subcarpeta1/
 │   ├── foto1.jpg
 │   ├── foto2.jpg
 ├── subcarpeta2/
 │   ├── imagen1.jpg
```

## 📋 Ejecución

```bash
python compresor_fotografico_v3.3.py
```

## 📄 Ejemplo de Uso

```
Ingrese el directorio a procesar: /home/usuario/fotos
Resumen de archivos encontrados:
150 archivos en formato RAW
12 archivos en formato JPG
Ingrese el directorio destino [/home/usuario/fotos_convertidos]:
Seleccione el formato de salida:
1. JPG
2. JPEG
3. PNG
4. TIFF
Opción: 3
Nivel de compresión PNG (0-9, 0 = sin compresión) [6]: 9
Tamaño límite en KB (0 para todas) [0]: 2048
Procesos a utilizar (1 secuencial): 4
```

---

## 📜 Change Log desde la versión 2.0

```text
Versión 2.0 → 3.0
-----------------
- Detección de sistema operativo y configuración automática de entorno virtual.
- Instalación automática de dependencias.
- Limpieza de pantalla y banner ASCII.
- Escaneo y validación de directorios.
- Selección de formato de salida por número.
- Configuración de compresión para JPG/JPEG y TIFF.
- Tamaño límite para procesar solo imágenes grandes.
- Conserva EXIF y estructura de carpetas.
- Sistema de logging detallado.
- Resumen final con estadísticas.

Versión 3.0 → 3.1
-----------------
- Añadido modo multiproceso configurable.

Versión 3.1 → 3.2
-----------------
- Solucionado error al convertir PNG → JPG/JPEG por imágenes con transparencia.

Versión 3.2 → 3.3
-----------------
- Añadida opción de compresión PNG (0–9, por defecto 6, sin pérdida).
- Integrada conversión a RGB para JPG/JPEG desde imágenes con transparencia.
```
