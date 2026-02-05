#!/bin/bash

# Script para instalar/desinstalar fuentes de Windows en Linux
# Ubicación de las fuentes
BASE_DIR="$(dirname "$0")/fuentes_windows"
FUENTES_BASICAS="$BASE_DIR/basicas"
FUENTES_EXTRAS="$BASE_DIR/extras"

# Colores para mejor legibilidad
VERDE='\033[0;32m'
ROJO='\033[0;31m'
AMARILLO='\033[1;33m'
AZUL='\033[0;34m'
NC='\033[0m' # No Color

# Función para verificar si existen fuentes instaladas
verificar_fuentes_instaladas() {
    local ubicacion="$1"
    local tiene_basicas=0
    local tiene_extras=0
    
    if [ -d "$ubicacion/basicas" ]; then
        tiene_basicas=1
    fi
    
    if [ -d "$ubicacion/extras" ]; then
        tiene_extras=1
    fi
    
    echo "$tiene_basicas $tiene_extras"
}

# Función para mostrar estado de fuentes instaladas
mostrar_estado_fuentes() {
    echo ""
    echo -e "${AZUL}Estado de las fuentes instaladas:${NC}"
    echo "======================================"
    
    # Verificar fuentes de usuario
    read tiene_basicas_user tiene_extras_user <<< "$(verificar_fuentes_instaladas "$HOME/.fonts")"
    
    echo -e "${AMARILLO}Usuario ($HOME/.fonts):${NC}"
    if [ $tiene_basicas_user -eq 1 ] && [ $tiene_extras_user -eq 1 ]; then
        echo -e "  ${VERDE}✓${NC} Básicas: Instaladas"
        echo -e "  ${VERDE}✓${NC} Extras: Instaladas"
    elif [ $tiene_basicas_user -eq 1 ]; then
        echo -e "  ${VERDE}✓${NC} Básicas: Instaladas"
        echo -e "  ${ROJO}✗${NC} Extras: No instaladas"
    elif [ $tiene_extras_user -eq 1 ]; then
        echo -e "  ${ROJO}✗${NC} Básicas: No instaladas"
        echo -e "  ${VERDE}✓${NC} Extras: Instaladas"
    else
        echo -e "  ${ROJO}✗${NC} No hay fuentes instaladas"
    fi
    
    # Verificar fuentes del sistema (si tiene permisos)
    read tiene_basicas_sys tiene_extras_sys <<< "$(verificar_fuentes_instaladas "/usr/share/fonts")"
    
    echo -e "${AMARILLO}Sistema (/usr/share/fonts):${NC}"
    if [ $tiene_basicas_sys -eq 1 ] && [ $tiene_extras_sys -eq 1 ]; then
        echo -e "  ${VERDE}✓${NC} Básicas: Instaladas"
        echo -e "  ${VERDE}✓${NC} Extras: Instaladas"
    elif [ $tiene_basicas_sys -eq 1 ]; then
        echo -e "  ${VERDE}✓${NC} Básicas: Instaladas"
        echo -e "  ${ROJO}✗${NC} Extras: No instaladas"
    elif [ $tiene_extras_sys -eq 1 ]; then
        echo -e "  ${ROJO}✗${NC} Básicas: No instaladas"
        echo -e "  ${VERDE}✓${NC} Extras: Instaladas"
    else
        echo -e "  ${ROJO}✗${NC} No hay fuentes instaladas"
    fi
    echo ""
}

# Función para desinstalar fuentes
desinstalar_fuentes() {
    echo ""
    echo "========================================"
    echo "Desinstalador de Fuentes de Windows"
    echo "========================================"
    echo ""
    
    # Mostrar estado actual
    mostrar_estado_fuentes
    
    # Preguntar ubicación
    echo "¿De dónde desea desinstalar las fuentes?"
    echo ""
    echo "1) Solo del usuario actual ($USER)"
    echo "2) Solo del sistema (requiere root)"
    echo "3) De ambas ubicaciones"
    echo ""
    read -p "Seleccione una opción (1, 2 o 3): " ubicacion
    
    case $ubicacion in
        1)
            DEST_DIRS=("$HOME/.fonts")
            UBICACION_NOMBRE="usuario"
            ;;
        2)
            DEST_DIRS=("/usr/share/fonts")
            UBICACION_NOMBRE="sistema"
            ;;
        3)
            DEST_DIRS=("$HOME/.fonts" "/usr/share/fonts")
            UBICACION_NOMBRE="ambas ubicaciones"
            ;;
        *)
            echo ""
            echo -e "${ROJO}✗ Opción no válida.${NC}"
            return
            ;;
    esac
    
    echo ""
    echo "Ha seleccionado desinstalar de: $UBICACION_NOMBRE"
    echo ""
    
    # Analizar qué fuentes están instaladas en las ubicaciones seleccionadas
    FUENTES_BASICAS_INSTALADAS=()
    FUENTES_EXTRAS_INSTALADAS=()
    
    for dest_dir in "${DEST_DIRS[@]}"; do
        if [ -d "$dest_dir/basicas" ]; then
            FUENTES_BASICAS_INSTALADAS+=("$dest_dir")
        fi
        if [ -d "$dest_dir/extras" ]; then
            FUENTES_EXTRAS_INSTALADAS+=("$dest_dir")
        fi
    done
    
    # Verificar si hay algo que desinstalar
    if [ ${#FUENTES_BASICAS_INSTALADAS[@]} -eq 0 ] && [ ${#FUENTES_EXTRAS_INSTALADAS[@]} -eq 0 ]; then
        echo -e "${ROJO}✗ No se encontraron fuentes instaladas en la ubicación seleccionada.${NC}"
        echo ""
        return
    fi
    
    # Preguntar qué desinstalar
    echo "¿Qué fuentes desea desinstalar?"
    echo ""
    
    if [ ${#FUENTES_BASICAS_INSTALADAS[@]} -gt 0 ]; then
        echo -n "1) Básicas (48 fuentes) - "
        if [ ${#FUENTES_BASICAS_INSTALADAS[@]} -eq 2 ]; then
            echo "instaladas en usuario y sistema"
        elif [ "${FUENTES_BASICAS_INSTALADAS[0]}" = "$HOME/.fonts" ]; then
            echo "instaladas en usuario"
        else
            echo "instaladas en sistema"
        fi
    else
        echo "1) Básicas - No instaladas"
    fi
    
    if [ ${#FUENTES_EXTRAS_INSTALADAS[@]} -gt 0 ]; then
        echo -n "2) Extras (130 fuentes) - "
        if [ ${#FUENTES_EXTRAS_INSTALADAS[@]} -eq 2 ]; then
            echo "instaladas en usuario y sistema"
        elif [ "${FUENTES_EXTRAS_INSTALADAS[0]}" = "$HOME/.fonts" ]; then
            echo "instaladas en usuario"
        else
            echo "instaladas en sistema"
        fi
    else
        echo "2) Extras - No instaladas"
    fi
    
    if [ ${#FUENTES_BASICAS_INSTALADAS[@]} -gt 0 ] || [ ${#FUENTES_EXTRAS_INSTALADAS[@]} -gt 0 ]; then
        echo "3) Todas las fuentes instaladas"
    fi
    echo ""
    
    read -p "Seleccione una opción (1, 2 o 3): " tipo_desinstalar
    
    case $tipo_desinstalar in
        1)
            if [ ${#FUENTES_BASICAS_INSTALADAS[@]} -eq 0 ]; then
                echo -e "${ROJO}✗ No hay fuentes básicas instaladas para desinstalar.${NC}"
                return
            fi
            TIPO_NOMBRE="básicas"
            DIRECTORIOS_DESINSTALAR=("basicas")
            ;;
        2)
            if [ ${#FUENTES_EXTRAS_INSTALADAS[@]} -eq 0 ]; then
                echo -e "${ROJO}✗ No hay fuentes extras instaladas para desinstalar.${NC}"
                return
            fi
            TIPO_NOMBRE="extras"
            DIRECTORIOS_DESINSTALAR=("extras")
            ;;
        3)
            TIPO_NOMBRE="todas"
            DIRECTORIOS_DESINSTALAR=()
            if [ ${#FUENTES_BASICAS_INSTALADAS[@]} -gt 0 ]; then
                DIRECTORIOS_DESINSTALAR+=("basicas")
            fi
            if [ ${#FUENTES_EXTRAS_INSTALADAS[@]} -gt 0 ]; then
                DIRECTORIOS_DESINSTALAR+=("extras")
            fi
            if [ ${#DIRECTORIOS_DESINSTALAR[@]} -eq 0 ]; then
                echo -e "${ROJO}✗ No hay fuentes instaladas para desinstalar.${NC}"
                return
            fi
            ;;
        *)
            echo -e "${ROJO}✗ Opción no válida.${NC}"
            return
            ;;
    esac
    
    echo ""
    echo -e "${AMARILLO}ADVERTENCIA: Esta acción eliminará las fuentes $TIPO_NOMBRE de $UBICACION_NOMBRE.${NC}"
    read -p "¿Está seguro? (s/N): " confirmar
    
    if [[ ! $confirmar =~ ^[Ss]$ ]]; then
        echo -e "${AMARILLO}Operación cancelada.${NC}"
        return
    fi
    
    echo ""
    echo "Desinstalando fuentes $TIPO_NOMBRE..."
    
    # Procesar cada ubicación
    for dest_dir in "${DEST_DIRS[@]}"; do
        # Verificar si necesitamos sudo para esta ubicación
        SUDO_PREFIX=""
        if [[ "$dest_dir" == "/usr/share/fonts" ]]; then
            if [ "$EUID" -ne 0 ]; then
                echo ""
                read -sp "Ingrese la contraseña de root/sudo: " password
                echo ""
                
                if ! echo "$password" | sudo -S true 2>/dev/null; then
                    echo -e "${ROJO}✗ Contraseña incorrecta o no tiene privilegios sudo${NC}"
                    echo -e "${AMARILLO}Saltando desinstalación del sistema...${NC}"
                    continue
                fi
                
                SUDO_PREFIX="echo '$password' | sudo -S"
            fi
        fi
        
        # Desinstalar directorios seleccionados
        for dir in "${DIRECTORIOS_DESINSTALAR[@]}"; do
            if [ -d "$dest_dir/$dir" ]; then
                echo "Eliminando '$dir' de $dest_dir..."
                
                if [ -n "$SUDO_PREFIX" ]; then
                    eval "$SUDO_PREFIX rm -rf '$dest_dir/$dir'"
                else
                    rm -rf "$dest_dir/$dir"
                fi
                
                if [ $? -eq 0 ]; then
                    echo -e "${VERDE}✓ '$dir' eliminado correctamente${NC}"
                else
                    echo -e "${ROJO}✗ Error al eliminar '$dir'${NC}"
                fi
            fi
        done
    done
    
    # Actualizar caché de fuentes
    echo ""
    echo "Actualizando caché de fuentes..."
    
    for dest_dir in "${DEST_DIRS[@]}"; do
        for dir in "${DIRECTORIOS_DESINSTALAR[@]}"; do
            if [[ "$dest_dir" == "$HOME/.fonts" ]]; then
                fc-cache -f -v "$HOME/.fonts" > /dev/null 2>&1
            else
                if [ -n "$SUDO_PREFIX" ]; then
                    eval "$SUDO_PREFIX fc-cache -f -v '$dest_dir'" > /dev/null 2>&1
                else
                    fc-cache -f -v "$dest_dir" > /dev/null 2>&1
                fi
            fi
        done
    done
    
    echo ""
    echo "========================================"
    echo -e "${VERDE}✓ Desinstalación completada!${NC}"
    echo "========================================"
    echo ""
    echo "Las fuentes han sido eliminadas del sistema."
    echo "Puede que necesite reiniciar las aplicaciones para ver los cambios."
    echo ""
}

# Función para instalar fuentes
instalar_fuentes() {
    echo ""
    echo "========================================"
    echo "Instalador de Fuentes de Windows"
    echo "========================================"
    echo ""
    
    # Mostrar estado actual
    mostrar_estado_fuentes
    
    # Selección de tipo de fuentes
    echo "¿Qué fuentes desea instalar?"
    echo ""
    echo "1) Básicas (48 fuentes populares)"
    echo "   - Arial, Times New Roman, Calibri, Cambria"
    echo "   - Comic Sans MS, Georgia, Verdana, Tahoma"
    echo "   - Trebuchet MS, Courier New, Consolas"
    echo "   - Impact, Webdings, Wingdings, Symbol"
    echo ""
    echo "2) Extras (130 fuentes adicionales)"
    echo "   - Bahnschrift, Segoe UI, Candara"
    echo "   - Fuentes asiáticas, técnicas, especializadas"
    echo ""
    echo "3) Todas (178 fuentes completas)"
    echo ""
    read -p "Seleccione una opción (1, 2 o 3): " tipo_fuentes
    
    case $tipo_fuentes in
        1)
            TIPO_NOMBRE="básicas"
            DIRECTORIOS=("basicas")
            ;;
        2)
            TIPO_NOMBRE="extras"
            DIRECTORIOS=("extras")
            ;;
        3)
            TIPO_NOMBRE="todas"
            DIRECTORIOS=("basicas" "extras")
            ;;
        *)
            echo ""
            echo -e "${ROJO}✗ Opción no válida. Debe seleccionar 1, 2 o 3.${NC}"
            return
            ;;
    esac
    
    echo ""
    echo "Ha seleccionado instalar las fuentes $TIPO_NOMBRE."
    echo ""
    
    # Selección de destino de instalación
    echo "¿Dónde desea instalar las fuentes?"
    echo ""
    echo "1) Solo para el usuario actual ($USER)"
    echo "2) Para todos los usuarios del sistema (requiere root)"
    echo ""
    read -p "Seleccione una opción (1 o 2): " opcion
    
    case $opcion in
        1)
            # Instalación para el usuario actual
            DEST_DIR="$HOME/.fonts"
            SUDO_PREFIX=""
            
            echo ""
            echo "Instalando fuentes $TIPO_NOMBRE para el usuario actual..."
            
            # Crear directorio si no existe
            if [ ! -d "$DEST_DIR" ]; then
                echo "Creando directorio $DEST_DIR..."
                mkdir -p "$DEST_DIR"
            fi
            
            # Copiar fuentes seleccionadas
            for dir in "${DIRECTORIOS[@]}"; do
                echo "Copiando fuentes de '$dir' a $DEST_DIR..."
                cp -r "$BASE_DIR/$dir" "$DEST_DIR/"
                
                if [ $? -ne 0 ]; then
                    echo ""
                    echo -e "${ROJO}✗ Error al copiar las fuentes del directorio '$dir'${NC}"
                    return
                fi
            done
            
            echo ""
            echo -e "${VERDE}✓ Fuentes $TIPO_NOMBRE instaladas correctamente en $DEST_DIR/${NC}"
            ;;
            
        2)
            # Instalación para todos los usuarios
            DEST_DIR="/usr/share/fonts"
            
            echo ""
            echo "Instalando fuentes $TIPO_NOMBRE para todos los usuarios..."
            echo "Esta operación requiere privilegios de administrador (root)."
            
            # Verificar si es root o pedir sudo
            if [ "$EUID" -ne 0 ]; then
                echo ""
                read -sp "Ingrese la contraseña de root/sudo: " password
                echo ""
                
                # Intentar con sudo
                if ! echo "$password" | sudo -S true 2>/dev/null; then
                    echo ""
                    echo -e "${ROJO}✗ Contraseña incorrecta o no tiene privilegios sudo${NC}"
                    return
                fi
                
                SUDO_PREFIX="echo '$password' | sudo -S"
            else
                SUDO_PREFIX=""
            fi
            
            # Copiar fuentes seleccionadas con privilegios elevados
            for dir in "${DIRECTORIOS[@]}"; do
                echo "Copiando fuentes de '$dir' a $DEST_DIR..."
                if [ -n "$SUDO_PREFIX" ]; then
                    eval "$SUDO_PREFIX cp -r '$BASE_DIR/$dir' '$DEST_DIR/'"
                else
                    cp -r "$BASE_DIR/$dir" "$DEST_DIR/"
                fi
                
                if [ $? -ne 0 ]; then
                    echo ""
                    echo -e "${ROJO}✗ Error al copiar las fuentes del directorio '$dir'${NC}"
                    return
                fi
            done
            
            echo ""
            echo -e "${VERDE}✓ Fuentes $TIPO_NOMBRE instaladas correctamente en $DEST_DIR/${NC}"
            ;;
            
        *)
            echo ""
            echo -e "${ROJO}✗ Opción no válida. Debe seleccionar 1 o 2.${NC}"
            return
            ;;
    esac
    
    # Actualizar caché de fuentes
    echo ""
    echo "Actualizando caché de fuentes..."
    
    if [ "$opcion" -eq 1 ]; then
        # Para usuario actual
        for dir in "${DIRECTORIOS[@]}"; do
            fc-cache -f -v "$HOME/.fonts/$dir" > /dev/null 2>&1
        done
    else
        # Para todo el sistema
        for dir in "${DIRECTORIOS[@]}"; do
            if [ "$EUID" -ne 0 ]; then
                eval "$SUDO_PREFIX fc-cache -f -v '$DEST_DIR/$dir'" > /dev/null 2>&1
            else
                fc-cache -f -v "$DEST_DIR/$dir" > /dev/null 2>&1
            fi
        done
    fi
    
    echo ""
    echo "========================================"
    echo -e "${VERDE}✓ Instalación completada exitosamente!${NC}"
    echo "========================================"
    echo ""
    echo "Fuentes $TIPO_NOMBRE instaladas:"
    for dir in "${DIRECTORIOS[@]}"; do
        NUM_FUENTES=$(find "$BASE_DIR/$dir" -type f \( -name "*.ttf" -o -name "*.ttc" -o -name "*.otf" \) | wc -l)
        echo "  - $dir: $NUM_FUENTES fuentes"
    done
    echo ""
    echo "Las fuentes ahora están disponibles en su sistema."
    echo "Puede que necesite reiniciar las aplicaciones para ver los cambios."
    echo ""
}

# ==================== MENÚ PRINCIPAL ====================

while true; do
    echo ""
    echo "========================================"
    echo "Gestor de Fuentes de Windows para Linux"
    echo "========================================"
    echo ""
    
    mostrar_estado_fuentes
    
    echo "¿Qué desea hacer?"
    echo ""
    echo "1) Instalar fuentes"
    echo "2) Desinstalar fuentes"
    echo "3) Ver estado de fuentes"
    echo "4) Salir"
    echo ""
    read -p "Seleccione una opción (1-4): " opcion_principal
    
    case $opcion_principal in
        1)
            instalar_fuentes
            ;;
        2)
            desinstalar_fuentes
            ;;
        3)
            # Ya se muestra en el menú principal
            ;;
        4)
            echo ""
            echo "¡Hasta luego!"
            exit 0
            ;;
        *)
            echo ""
            echo -e "${ROJO}✗ Opción no válida. Debe seleccionar 1, 2, 3 o 4.${NC}"
            ;;
    esac
done
