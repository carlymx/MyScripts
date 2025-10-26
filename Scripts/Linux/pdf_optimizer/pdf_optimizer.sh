#####
# Script: optimizar_PDF.sh
# Versión: 1.0
# Descripción: Extrae, limpia y reescala imágenes de un PDF escaneado (CCITT) y lo vuelve a empaquetar.
# Autor: carlymx@gmail.com
# Fecha: 2025
#####

#!/bin/bash

# --- Función para verificar dependencias ---
check_dependencies() {
    echo "🔍 Verificando dependencias..."
    local deps=("gs" "convert" "unpaper" "pdfimages" "img2pdf" "qpdf")
    local missing=()

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -ne 0 ]; then
        echo "❌ Dependencias faltantes: ${missing[*]}"
        read -p "¿Intentar instalarlas? (s/n): " install_choice
        if [[ "$install_choice" =~ ^[sS]$ ]]; then
            if command -v apt &> /dev/null; then
                echo "📦 Actualizando lista de paquetes..."
                sudo apt update
                echo "📦 Instalando dependencias: ghostscript imagemagick unpaper poppler-utils img2pdf qpdf"
                sudo apt install -y ghostscript imagemagick unpaper poppler-utils img2pdf qpdf
                echo "✅ Instalación completada."
            else
                echo "❌ Sistema no soportado para instalación automática (no es apt)."
                echo "Por favor, instale manualmente las dependencias:"
                echo "  ghostscript, imagemagick, unpaper, poppler-utils, img2pdf, qpdf"
                exit 1
            fi
        else
            echo "❌ Instalación cancelada por el usuario. Saliendo."
            exit 1
        fi
    else
        echo "✅ Todas las dependencias están instaladas."
    fi
    echo "----------------------------------------"
}

# --- Ejecutar la verificación ---
check_dependencies

# --- Configuración inicial ---
INPUT_PDF=""
OUTPUT_DIR=""
DPI=""
BORRAR_TEMPORALES=""

# --- Función para solicitar valores al usuario ---
prompt_user() {
    echo "🔧 Configuración del proceso:"
    echo ""

    # Solicitar archivo PDF
    while [ -z "$INPUT_PDF" ] || [ ! -f "$INPUT_PDF" ]; do
        read -p "Ingrese la ruta del PDF de entrada: " INPUT_PDF
        if [ ! -f "$INPUT_PDF" ]; then
            echo "❌ Error: No se encuentra el archivo '$INPUT_PDF'. Intente de nuevo."
        fi
    done

    # Solicitar directorio de salida
    read -p "Ingrese el directorio de salida (Enter para usar el directorio del archivo original): " OUTPUT_DIR
    if [ -z "$OUTPUT_DIR" ]; then
        OUTPUT_DIR="$(dirname "$INPUT_PDF")"
    fi
    # Crear directorio si no existe
    mkdir -p "$OUTPUT_DIR"
    if [ ! -d "$OUTPUT_DIR" ]; then
        echo "❌ Error: No se pudo crear el directorio '$OUTPUT_DIR'."
        exit 1
    fi

    # Solicitar DPI
    while ! [[ "$DPI" =~ ^[0-9]+$ ]] || [ "$DPI" -lt 72 ] || [ "$DPI" -gt 300 ]; do
        read -p "Ingrese los DPI de salida (72-300, recomendado 100-150): " DPI
        if ! [[ "$DPI" =~ ^[0-9]+$ ]]; then
            echo "❌ Error: Ingrese un número válido."
        elif [ "$DPI" -lt 72 ] || [ "$DPI" -gt 300 ]; then
            echo "❌ Error: El DPI debe estar entre 72 y 300."
        fi
    done

    # Confirmar borrado de temporales
    while [[ ! "$BORRAR_TEMPORALES" =~ ^[sS]$ ]] && [[ ! "$BORRAR_TEMPORALES" =~ ^[nN]$ ]]; do
        read -p "¿Borrar directorios temporales al final? (s/n): " BORRAR_TEMPORALES
    done

    echo ""
    echo "✅ Configuración confirmada:"
    echo "   PDF de entrada: $INPUT_PDF"
    echo "   Directorio de salida: $OUTPUT_DIR"
    echo "   DPI de salida: $DPI"
    echo "   Borrar temporales: $([ "$BORRAR_TEMPORALES" =~ ^[sS]$ ] && echo "Sí" || echo "No")"
    echo "----------------------------------------"
}

# --- Ejecutar la configuración ---
prompt_user

# --- Directorios temporales ---
DIR_TIFF=$(mktemp -d)
DIR_CLEAN=$(mktemp -d)

echo "📁 Directorios temporales:"
echo "  TIFF ($DPI DPI): $DIR_TIFF"
echo "  Limpio (PBM):    $DIR_CLEAN"

# 1. Renderizar PDF como imágenes TIFF (CCITT G4, a $DPI DPI)
echo "📤 Extrayendo páginas como TIFF ($DPI DPI)..."
gs -dNOPAUSE -dBATCH -sDEVICE=tiffg4 -r$DPI -dEPSCrop -sOutputFile="$DIR_TIFF/pagina-%03d.tiff" "$INPUT_PDF"

# 2. Convertir cada TIFF a PBM, limpiar con unpaper
echo "🧼 Limpiando imágenes con unpaper..."
for tiff in "$DIR_TIFF"/*.tiff; do
    if [ -f "$tiff" ]; then
        base=$(basename "$tiff" .tiff)
        pbm_temp="$DIR_CLEAN/${base}_temp.pbm"
        pbm_clean="$DIR_CLEAN/${base}_clean.pbm"

        # Convertir TIFF a PBM temporal
        convert "$tiff" -threshold 50% -monochrome "$pbm_temp"

        # Limpiar con unpaper (entrada != salida)
        unpaper "$pbm_temp" "$pbm_clean"

        # Opcional: borrar el temporal
        rm -f "$pbm_temp"
    fi
done

# 3. Verificar si hay imágenes limpias
IMAGES=($(ls "$DIR_CLEAN"/*_clean.pbm 2>/dev/null | sort -V))
if [ ${#IMAGES[@]} -eq 0 ]; then
    echo "❌ No se encontraron imágenes limpias."
    exit 1
fi

# 4. Convertir imágenes a PDF
echo "📄 Convirtiendo imágenes limpias a PDF..."
PDF_BASENAME=$(basename "$INPUT_PDF" .pdf)
OUTPUT_PDF_PATH="$OUTPUT_DIR/${PDF_BASENAME}_limpio_${DPI}dpi.pdf"
img2pdf "${IMAGES[@]}" -o "$OUTPUT_PDF_PATH"

# 5. Optimizar PDF final
FINAL_PDF_PATH="$OUTPUT_DIR/${PDF_BASENAME}_final_${DPI}dpi.pdf"
echo "⚡ Optimizando PDF final..."
qpdf --linearize --stream-data=compress "$OUTPUT_PDF_PATH" "$FINAL_PDF_PATH"

# --- Borrar temporales si se solicitó ---
if [[ "$BORRAR_TEMPORALES" =~ ^[sS]$ ]]; then
    rm -rf "$DIR_TIFF"
    rm -rf "$DIR_CLEAN"
    echo "🗑️ Directorios temporales eliminados."
fi

echo "✅ ¡Listo!"
echo "📄 PDF optimizado: $FINAL_PDF_PATH"
echo "💡 Tamaño original vs final:"
ls -lh "$INPUT_PDF" "$FINAL_PDF_PATH"
