Descripción del script 'compresor_fotografias_v1.4.py'

Este script es una herramienta de Python para procesar y comprimir imágenes JPG y JPEG de forma masiva. Su función principal es identificar fotografías que superan un tamaño de archivo predefinido y, opcionalmente, crear una copia comprimida de esas imágenes en un directorio de destino. La compresión se realiza manteniendo los metadatos EXIF originales para no perder información importante de la fotografía, como la fecha y hora de la toma o los ajustes de la cámara.

¿Cómo funciona?

Configuración y Registro (LOG) 📝: Al inicio, el script configura un sistema de registro (logging) que crea un archivo (.log) para documentar detalladamente todo el proceso, incluyendo la ruta de los archivos procesados y los errores que puedan surgir. Esto es útil para auditar o depurar el proceso.

Entrada de datos por el usuario 🧑‍💻: El programa solicita al usuario la siguiente información:
   Directorio de origen: La carpeta donde se encuentran las imágenes a analizar.
   Directorio de destino: La carpeta donde se guardarán las copias comprimidas.

   
Tamaño límite (KB): El umbral de tamaño de archivo. Las imágenes que lo superen serán consideradas "grandes" y candidatas a compresión.
Tasa de compresión (%): La calidad de compresión que se aplicará a las imágenes (ej. 70% significa 70% de la calidad original).
        Opción de compresión: Se pregunta si se desea guardar las copias comprimidas o solo identificar los archivos grandes.
    Procesamiento de imágenes 🖼️:
        El script recorre de forma recursiva el directorio de origen y sus subcarpetas en busca de archivos .jpg y .jpeg.
        Mientras procesa, muestra en la consola una barra de progreso que indica el porcentaje completado, el total de archivos, los procesados y los errores.
        Para cada imagen, verifica si su tamaño supera el límite establecido.
        Si la imagen es grande y se ha elegido la opción de compresión, el script hace lo siguiente:
            Copia la estructura de directorios: Mantiene la misma estructura de carpetas del origen en el destino.
            Lee metadatos EXIF: Extrae la información EXIF de la imagen original. Esto se hace con un manejo de errores (safe_exif_dump) para evitar fallos si los datos están corruptos.
            Comprime y guarda: Utiliza la biblioteca Pillow para abrir la imagen, la comprime con la tasa indicada por el usuario y la guarda en el directorio de destino con un nuevo nombre (ej. foto.jpg se convierte en foto_low.jpg). Durante el guardado, se le adjuntan los metadatos EXIF extraídos.
            Copia de metadatos del sistema: Utiliza shutil.copystat para replicar la fecha de creación y modificación del archivo original en la copia comprimida.

Resultados y finalización ✅: Al terminar, el script informa al usuario del total de archivos encontrados, cuántos superaron el tamaño límite, cuántos fueron procesados (si se eligió la compresión) y el número de errores. Finalmente, indica la ubicación del archivo de registro (.log) donde se puede consultar el historial completo del proceso.
