#!/bin/bash

# Directorio de salida (opcional, puedes cambiarlo)
output_dir="$HOME/Imágenes/Comprimidas"

# Crear directorio de salida si no existe
mkdir -p "$output_dir"

# Convertir o recomprimir cada imagen seleccionada
for image in "$@"; do
    filename=$(basename "$image")
    output_file="$output_dir/${filename%.*}_compressed.jpg"
    
    # Ejemplo: Convertir a JPEG con calidad del 80%
    convert "$image" -quality 80% "$output_file"
    
    # Alternativa: Recomprimir PNG con pngquant
    # pngquant --force --output "$output_file" "$image"
done

# Notificación de finalización
notify-send "Conversión completada" "Las imágenes se han convertido/recomprimido."
