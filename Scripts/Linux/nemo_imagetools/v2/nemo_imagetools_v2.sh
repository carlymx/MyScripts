#!/bin/bash

# Directorio de salida (opcional, puedes cambiarlo)
output_dir="$HOME/Imágenes/Comprimidas"

# Crear directorio de salida si no existe
mkdir -p "$output_dir"

# Verificar si se proporcionó un nivel de compresión
if [ -z "$1" ]; then
    echo "Error: No se especificó un nivel de compresión."
    exit 1
fi

# Convertir o recomprimir cada imagen seleccionada
for image in "${@:2}"; do
    filename=$(basename "$image")
    name_no_extension="${filename%.*}"

    case "$1" in
        jpg60)
            output_file="$output_dir/${name_no_extension}_compressed.jpg"
            convert "$image" -quality 60% "$output_file"
            ;;
        jpg80)
            output_file="$output_dir/${name_no_extension}_compressed.jpg"
            convert "$image" -quality 80% "$output_file"
            ;;
        jpg100)
            output_file="$output_dir/${name_no_extension}_compressed.jpg"
            convert "$image" -quality 100% "$output_file"
            ;;
        pnglow)
            output_file="$output_dir/${name_no_extension}_compressed.png"
            # Convertir a PNG si no lo es ya
            if [[ "$image" != *.png ]]; then
                convert "$image" "PNG:$output_file"
            else
                cp "$image" "$output_file"
            fi
            # Comprimir PNG
            pngquant --quality=50-80 --force --output "$output_file" "$output_file"
            ;;
        pnghigh)
            output_file="$output_dir/${name_no_extension}_compressed.png"
            # Convertir a PNG si no lo es ya
            if [[ "$image" != *.png ]]; then
                convert "$image" "PNG:$output_file"
            else
                cp "$image" "$output_file"
            fi
            # Comprimir PNG
            pngquant --quality=80-100 --force --output "$output_file" "$output_file"
            ;;
        *)
            echo "Error: Opción de compresión no válida."
            exit 1
            ;;
    esac
done

# Notificación de finalización
notify-send "Conversión completada" "Las imágenes se han convertido/recomprimido."
