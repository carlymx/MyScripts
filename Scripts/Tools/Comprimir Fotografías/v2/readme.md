[📹 Ver video del funcionamiento](https://i.imgur.com/HMyX58j.mp4)


# Conversor y Compresor de Imágenes RAW a Formatos Comunes

## 📌 Descripción

Este script en Python permite convertir y comprimir fotografías en formato RAW y otros formatos de imagen a formatos más comunes como **JPG**, **PNG**, **TIFF**, entre otros. Está diseñado para ser multiplataforma, detectando automáticamente el sistema operativo (**Windows** o **Linux**) y gestionando la instalación de dependencias necesarias.

## ✨ Características

- **Detección automática del sistema operativo**.
- **Instalación automática de dependencias** (`Pillow` y `piexif`).
- **Exploración de directorios** para listar tipos y cantidades de archivos encontrados.
- **Soporte para múltiples formatos de entrada** (RAW, NEF, CR2, ARW, JPG, PNG, TIFF, BMP, GIF, etc.).
- **Opciones de formato de salida** (JPG, JPEG, PNG, TIFF).
- **Opciones de compresión** para TIFF (sin compresión, LZW, ZIP o JPEG con pérdida).
- **Límite de tamaño (KB)** para procesar solo archivos grandes.
- **Conserva metadatos EXIF** al convertir imágenes.
- **Recrea la estructura de directorios** del origen en el destino.
- **Registro detallado en un archivo `.log`** con rutas, errores y resumen del proceso.

## 🛠️ Funcionamiento

1. El script detecta el sistema operativo.
2. Comprueba si las librerías necesarias están instaladas y, si no, las instala.
3. Solicita el directorio de origen de las imágenes.
4. Escanea y muestra un resumen de formatos y cantidades encontradas.
5. Pregunta el directorio de destino (por defecto crea uno llamado `convertidos`).
6. Solicita el formato de salida y opciones de compresión si es TIFF.
7. Pide un tamaño límite en KB (0 para procesar todas las imágenes).
8. Procesa las imágenes conservando EXIF y estructura de carpetas.
9. Guarda un registro detallado en un archivo `.log` dentro del directorio `logs`.

## 📂 Estructura de Salida

```
convertidos/
 ├── subcarpeta1/
 │   ├── foto1.tiff
 │   ├── foto2.tiff
 ├── subcarpeta2/
 │   ├── imagen1.tiff
```

## 📋 Ejecución

```bash
python convertir_fotos.py
```

Durante la ejecución, el script mostrará el progreso y, al final, un resumen con:

- Total de archivos encontrados
- Archivos que superan el límite indicado
- Archivos procesados
- Errores
- Ruta del archivo de registro

## 📄 Ejemplo de Uso

```
Ingrese el directorio a procesar: /home/usuario/fotos
Resumen de archivos encontrados:
150 archivos en formato RAW
12 archivos en formato JPG
Ingrese el directorio destino [/home/usuario/fotos/convertidos]:
Formato de salida (JPG, JPEG, PNG, TIFF): TIFF
Compresión (none, lzw, zip, jpeg) [none]: lzw
Tamaño límite en KB (0 para todas) [0]: 2048
```

Al finalizar, se obtendrán las imágenes convertidas en la carpeta indicada y un `.log` con el historial del proceso.

