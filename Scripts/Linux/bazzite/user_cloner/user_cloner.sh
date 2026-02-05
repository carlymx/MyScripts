#!/bin/bash
#
# User Cloner - Script para clonar perfiles de usuario en Bazzite Linux
# Autor: Agente de Código
# Fecha: $(date '+%Y-%m-%d')
#
# Uso: ./user_cloner.sh
# El script guía al usuario a través de un asistente interactivo
#

set -euo pipefail

###############################################################################
## ASCII ART HEADER
###############################################################################

mostrar_cabecera() {
  cat << 'EOF'

╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   ██╗   ██╗███████╗███████╗██████╗     ██████╗██╗      ██████╗ ███╗   ██╗ ║
║   ██║   ██║██╔════╝██╔════╝██╔══██╗   ██╔════╝██║     ██╔═══██╗████╗  ██║ ║
║   ██║   ██║███████╗█████╗  ██████╔╝   ██║     ██║     ██║   ██║██╔██╗ ██║ ║
║   ██║   ██║     ██║██╔══╝  ██╔══██╗   ██║     ██║     ██║   ██║██║╚██╗██║ ║
║   ╚██████╔╝███████║███████╗██║  ██║██╗╚██████╗███████╗╚██████╔╝██║ ╚████║ ║
║    ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝ ║
║                                                                           ║
║                     Para Bazzite Linux (Fedora Atomic)                    ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

EOF
}

###############################################################################
## CONFIGURACIÓN Y CONSTANTES
###############################################################################

readonly VERSION="1.0.0"
readonly SCRIPT_NAME="User Cloner"
readonly LOG_FILE="/tmp/user_cloner_$(date +%Y%m%d_%H%M%S).log"
readonly LOCK_FILE="/var/lock/user_cloner.lock"

# Colores para salida en terminal
if [[ -t 1 ]]; then
  readonly COLOR_RESET='\033[0m'
  readonly COLOR_BOLD='\033[1m'
  readonly COLOR_RED='\033[31m'
  readonly COLOR_GREEN='\033[32m'
  readonly COLOR_YELLOW='\033[33m'
  readonly COLOR_BLUE='\033[34m'
  readonly COLOR_CYAN='\033[36m'
else
  readonly COLOR_RESET=''
  readonly COLOR_BOLD=''
  readonly COLOR_RED=''
  readonly COLOR_GREEN=''
  readonly COLOR_YELLOW=''
  readonly COLOR_BLUE=''
  readonly COLOR_CYAN=''
fi

# Variables del flujo
USUARIO_ORIGEN=""
USUARIO_DESTINO=""
CONTRASENA_DESTINO=""
ESTABLECER_CONTRASENA=false
COPIAR_DATOS=true
COPIAR_FLATPAK=true
AJUSTAR_SELINUX=true
MODO_VERBOSE=false

# Arrays para directorios seleccionados por categoría (arrays indexados, no asociativos)
declare -a DIRECTORIOS_PERSONALES=()
declare -a DIRECTORIOS_CONFIG=()
declare -a DIRECTORIOS_GAMING=()
declare -a DIRECTORIOS_APPIMAGES=()
declare -a DIRECTORIOS_OTROS=()

# Nota: Eliminado el sistema de categorías expandibles/colapsables
# Ahora todos los directorios se muestran en una lista plana simplificada

###############################################################################
## FUNCIONES DE UTILIDAD
###############################################################################

log() {
  local mensaje="$1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $mensaje" >> "$LOG_FILE"
}

formatear_tamano() {
  local bytes="${1:-0}"
  if [[ -z "$bytes" ]] || [[ "$bytes" == "0" ]]; then
    echo "0B"
  elif [[ $bytes -lt 1024 ]]; then
    echo "${bytes}B"
  elif [[ $bytes -lt 1048576 ]]; then
    echo "$(echo "scale=1; $bytes/1024" | bc)K"
  elif [[ $bytes -lt 1073741824 ]]; then
    echo "$(echo "scale=1; $bytes/1048576" | bc)M"
  else
    echo "$(echo "scale=2; $bytes/1073741824" | bc)G"
  fi
}

calcular_tamano_directorio() {
  local dir="$1"
  if [[ -d "$dir" ]]; then
    du -sb "$dir" 2>/dev/null | cut -f1
  else
    echo 0
  fi
}

detectar_directorios_categorizados() {
  local home_dir="$1"
  log "Detectando directorios en $home_dir"
  
  # Limpiar arrays
  DIRECTORIOS_PERSONALES=()
  DIRECTORIOS_CONFIG=()
  DIRECTORIOS_GAMING=()
  DIRECTORIOS_APPIMAGES=()
  DIRECTORIOS_OTROS=()
  
  # 1. Directorios personales estándar
  local dirs_personales=("Documentos" "Escritorio" "Imagenes" "Videos" "Musica" "Descargas" "Plantillas" "Publico")
  for dir in "${dirs_personales[@]}"; do
    local ruta="$home_dir/$dir"
    if [[ -d "$ruta" ]]; then
      local tamano=$(calcular_tamano_directorio "$ruta")
      if [[ $tamano -gt 0 ]]; then
        DIRECTORIOS_PERSONALES+=("$dir|$tamano|false")
      fi
    fi
  done
  
  # 2. Directorios de configuración
  local dirs_config=(".config" ".local" ".cache" ".themes" ".icons" ".fonts" ".ssh" ".gnupg" ".pki")
  for dir in "${dirs_config[@]}"; do
    local ruta="$home_dir/$dir"
    if [[ -d "$ruta" ]]; then
      local tamano=$(calcular_tamano_directorio "$ruta")
      if [[ $tamano -gt 0 ]]; then
        DIRECTORIOS_CONFIG+=("$dir|$tamano|false")
      fi
    fi
  done
  
  # 3. Directorios de gaming
  local dirs_gaming=(".steam" ".local/share/Steam" ".var/app/com.valvesoftware.Steam" ".var/app/com.heroicgameslauncher.hgl" ".var/app/com.usebottles.bottles" ".wine" ".local/share/lutris" "Games")
  for dir in "${dirs_gaming[@]}"; do
    local ruta="$home_dir/$dir"
    if [[ -d "$ruta" ]]; then
      local tamano=$(calcular_tamano_directorio "$ruta")
      if [[ $tamano -gt 0 ]]; then
        DIRECTORIOS_GAMING+=("$dir|$tamano|false")
      fi
    fi
  done
  
  # 4. AppImages - detectar archivos individuales
  if [[ -d "$home_dir/Applications" ]]; then
    while IFS= read -r -d '' appimage; do
      local tamano=$(stat -c%s "$appimage" 2>/dev/null || echo 0)
      local nombre=$(basename "$appimage")
      if [[ $tamano -gt 0 ]]; then
        DIRECTORIOS_APPIMAGES+=("Applications/$nombre|$tamano|false")
      fi
    done < <(find "$home_dir/Applications" -maxdepth 1 -name "*.AppImage" -type f -print0 2>/dev/null)
  fi
  
  # También buscar AppImages en home
  while IFS= read -r -d '' appimage; do
    local tamano=$(stat -c%s "$appimage" 2>/dev/null || echo 0)
    local nombre=$(basename "$appimage")
    if [[ $tamano -gt 0 ]]; then
      DIRECTORIOS_APPIMAGES+=("$nombre|$tamano|false")
    fi
  done < <(find "$home_dir" -maxdepth 1 -name "*.AppImage" -type f -print0 2>/dev/null)
  
  # 5. Otros directorios (no estándar, no ocultos, no gaming)
  if [[ -d "$home_dir" ]]; then
    while IFS= read -r dir; do
      local nombre=$(basename "$dir")
      # Excluir directorios ya categorizados
      if [[ ! "$nombre" =~ ^(Documentos|Escritorio|Imagenes|Videos|Musica|Descargas|Plantillas|Publico|Applications|Games)$ ]] && \
           [[ ! "$nombre" =~ ^\. ]] && \
           [[ -d "$dir" ]]; then
        local tamano=$(calcular_tamano_directorio "$dir")
        if [[ $tamano -gt 0 ]]; then
          DIRECTORIOS_OTROS+=("$nombre|$tamano|false")
        fi
      fi
    done < <(find "$home_dir" -maxdepth 1 -type d 2>/dev/null)
  fi
  
  log "Detectados: ${#DIRECTORIOS_PERSONALES[@]} personales, ${#DIRECTORIOS_CONFIG[@]} config, ${#DIRECTORIOS_GAMING[@]} gaming, ${#DIRECTORIOS_APPIMAGES[@]} appimages, ${#DIRECTORIOS_OTROS[@]} otros"
}

calcular_total_seleccionado() {
  local total=0
  local array_name="$1"
  local -n array_ref="$array_name"
  
  for item in "${array_ref[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    if [[ "$seleccionado" == "true" ]]; then
      total=$((total + tamano))
    fi
  done
  
  echo $total
}

mostrar_resumen_seleccion() {
  local total_personales=0
  local total_config=0
  local total_gaming=0
  local total_appimages=0
  local total_otros=0
  local count_personales=0
  local count_config=0
  local count_gaming=0
  local count_appimages=0
  local count_otros=0
  
  for item in "${DIRECTORIOS_PERSONALES[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    if [[ "$seleccionado" == "true" ]]; then
      total_personales=$((total_personales + tamano))
      count_personales=$((count_personales + 1))
    fi
  done
  
  for item in "${DIRECTORIOS_CONFIG[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    if [[ "$seleccionado" == "true" ]]; then
      total_config=$((total_config + tamano))
      count_config=$((count_config + 1))
    fi
  done
  
  for item in "${DIRECTORIOS_GAMING[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    if [[ "$seleccionado" == "true" ]]; then
      total_gaming=$((total_gaming + tamano))
      count_gaming=$((count_gaming + 1))
    fi
  done
  
  for item in "${DIRECTORIOS_APPIMAGES[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    if [[ "$seleccionado" == "true" ]]; then
      total_appimages=$((total_appimages + tamano))
      count_appimages=$((count_appimages + 1))
    fi
  done
  
  for item in "${DIRECTORIOS_OTROS[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    if [[ "$seleccionado" == "true" ]]; then
      total_otros=$((total_otros + tamano))
      count_otros=$((count_otros + 1))
    fi
  done
  
  local total_bytes=$((total_personales + total_config + total_gaming + total_appimages + total_otros))
  local total_count=$((count_personales + count_config + count_gaming + count_appimages + count_otros))
  
  echo ""
  info "📊 RESUMEN DE SELECCIÓN"
  separador
  
  [[ $count_personales -gt 0 ]] && echo "  📁 Personales:     $count_personales elementos ($(formatear_tamano $total_personales))"
  [[ $count_config -gt 0 ]] && echo "  ⚙️  Configuración:  $count_config elementos ($(formatear_tamano $total_config))"
  [[ $count_gaming -gt 0 ]] && echo "  🎮 Gaming:         $count_gaming elementos ($(formatear_tamano $total_gaming))"
  [[ $count_appimages -gt 0 ]] && echo "  📦 AppImages:      $count_appimages elementos ($(formatear_tamano $total_appimages))"
  [[ $count_otros -gt 0 ]] && echo "  📂 Otros:          $count_otros elementos ($(formatear_tamano $total_otros))"
  
  separador
  echo -e "  ${COLOR_BOLD}TOTAL: $total_count elementos ($(formatear_tamano $total_bytes))${COLOR_RESET}"
  separador
  echo ""
  
  return $total_count
}

menu_checkbox_categorias() {
  local opcion=""
  local num_opcion=1
  declare -a TODAS_OPCIONES=()
  declare -a TODAS_CATEGORIAS=()
  
  while true; do
    clear
    echo ""
    info "📂 SELECCIÓN DE DIRECTORIOS A COPIAR"
    separador
    echo ""
    info "Marca los directorios que deseas copiar:"
    echo "  [ ] = No seleccionado    [✓] = Seleccionado"
    echo ""
    separador
    echo ""
    
    num_opcion=1
    TODAS_OPCIONES=()
    TODAS_CATEGORIAS=()
    
    # Sección: Personales
    if [[ ${#DIRECTORIOS_PERSONALES[@]} -gt 0 ]]; then
      echo -e "${COLOR_BOLD}📁 DIRECTORIOS PERSONALES${COLOR_RESET} (${#DIRECTORIOS_PERSONALES[@]} elementos)"
      for i in "${!DIRECTORIOS_PERSONALES[@]}"; do
        IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_PERSONALES[$i]}"
        local checkbox="[ ]"
        local color=$COLOR_RESET
        [[ "$seleccionado" == "true" ]] && checkbox="[✓]" && color=$COLOR_GREEN
        local tamano_fmt=$(formatear_tamano $tamano)
        printf "  ${COLOR_BOLD}%2d)${COLOR_RESET} %s ${color}%-25s${COLOR_RESET} (%s)\n" "$num_opcion" "$checkbox" "$nombre" "$tamano_fmt"
        TODAS_OPCIONES[$num_opcion]="${DIRECTORIOS_PERSONALES[$i]}"
        TODAS_CATEGORIAS[$num_opcion]="personales:$i"
        num_opcion=$((num_opcion + 1))
      done
      echo ""
    fi
    
    # Sección: Configuración
    if [[ ${#DIRECTORIOS_CONFIG[@]} -gt 0 ]]; then
      echo -e "${COLOR_BOLD}⚙️  CONFIGURACIÓN${COLOR_RESET} (${#DIRECTORIOS_CONFIG[@]} elementos)"
      for i in "${!DIRECTORIOS_CONFIG[@]}"; do
        IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_CONFIG[$i]}"
        local checkbox="[ ]"
        local color=$COLOR_RESET
        [[ "$seleccionado" == "true" ]] && checkbox="[✓]" && color=$COLOR_GREEN
        local tamano_fmt=$(formatear_tamano $tamano)
        printf "  ${COLOR_BOLD}%2d)${COLOR_RESET} %s ${color}%-25s${COLOR_RESET} (%s)\n" "$num_opcion" "$checkbox" "$nombre" "$tamano_fmt"
        TODAS_OPCIONES[$num_opcion]="${DIRECTORIOS_CONFIG[$i]}"
        TODAS_CATEGORIAS[$num_opcion]="config:$i"
        num_opcion=$((num_opcion + 1))
      done
      echo ""
    fi
    
    # Sección: Gaming
    if [[ ${#DIRECTORIOS_GAMING[@]} -gt 0 ]]; then
      echo -e "${COLOR_BOLD}🎮 GAMING${COLOR_RESET} (${#DIRECTORIOS_GAMING[@]} elementos)"
      for i in "${!DIRECTORIOS_GAMING[@]}"; do
        IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_GAMING[$i]}"
        local checkbox="[ ]"
        local color=$COLOR_RESET
        [[ "$seleccionado" == "true" ]] && checkbox="[✓]" && color=$COLOR_GREEN
        local tamano_fmt=$(formatear_tamano $tamano)
        printf "  ${COLOR_BOLD}%2d)${COLOR_RESET} %s ${color}%-25s${COLOR_RESET} (%s)\n" "$num_opcion" "$checkbox" "$nombre" "$tamano_fmt"
        TODAS_OPCIONES[$num_opcion]="${DIRECTORIOS_GAMING[$i]}"
        TODAS_CATEGORIAS[$num_opcion]="gaming:$i"
        num_opcion=$((num_opcion + 1))
      done
      echo ""
    fi
    
    # Sección: AppImages
    if [[ ${#DIRECTORIOS_APPIMAGES[@]} -gt 0 ]]; then
      echo -e "${COLOR_BOLD}📦 APPIMAGES${COLOR_RESET} (${#DIRECTORIOS_APPIMAGES[@]} elementos)"
      for i in "${!DIRECTORIOS_APPIMAGES[@]}"; do
        IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_APPIMAGES[$i]}"
        local checkbox="[ ]"
        local color=$COLOR_RESET
        [[ "$seleccionado" == "true" ]] && checkbox="[✓]" && color=$COLOR_GREEN
        local tamano_fmt=$(formatear_tamano $tamano)
        local nombre_corto=$(basename "$nombre")
        [[ ${#nombre_corto} -gt 28 ]] && nombre_corto="${nombre_corto:0:25}..."
        printf "  ${COLOR_BOLD}%2d)${COLOR_RESET} %s ${color}%-28s${COLOR_RESET} (%s)\n" "$num_opcion" "$checkbox" "$nombre_corto" "$tamano_fmt"
        TODAS_OPCIONES[$num_opcion]="${DIRECTORIOS_APPIMAGES[$i]}"
        TODAS_CATEGORIAS[$num_opcion]="appimages:$i"
        num_opcion=$((num_opcion + 1))
      done
      echo ""
    fi
    
    # Sección: Otros
    if [[ ${#DIRECTORIOS_OTROS[@]} -gt 0 ]]; then
      echo -e "${COLOR_BOLD}📂 OTROS DIRECTORIOS${COLOR_RESET} (${#DIRECTORIOS_OTROS[@]} elementos)"
      for i in "${!DIRECTORIOS_OTROS[@]}"; do
        IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_OTROS[$i]}"
        local checkbox="[ ]"
        local color=$COLOR_RESET
        [[ "$seleccionado" == "true" ]] && checkbox="[✓]" && color=$COLOR_GREEN
        local tamano_fmt=$(formatear_tamano $tamano)
        printf "  ${COLOR_BOLD}%2d)${COLOR_RESET} %s ${color}%-25s${COLOR_RESET} (%s)\n" "$num_opcion" "$checkbox" "$nombre" "$tamano_fmt"
        TODAS_OPCIONES[$num_opcion]="${DIRECTORIOS_OTROS[$i]}"
        TODAS_CATEGORIAS[$num_opcion]="otros:$i"
        num_opcion=$((num_opcion + 1))
      done
      echo ""
    fi
    
    separador
    echo ""
    mostrar_resumen_seleccion > /dev/null 2>&1
    echo ""
    separador
    echo ""
    echo -e "  ${COLOR_BOLD}CONTROLES:${COLOR_RESET}"
    echo "    1-$((num_opcion-1)) = Alternar selección    S = Todos    N = Ninguno"
    echo "    C = Confirmar    0 = Volver"
    echo ""
    separador
    echo ""
    
    echo -en "${COLOR_CYAN}Selecciona una opción:${COLOR_RESET} "
    read -r opcion
    opcion=$(echo "$opcion" | tr '[:upper:]' '[:lower:]')
    
    case "$opcion" in
      0)
        return 1
        ;;
      c)
        # Verificar si hay selecciones
        local total_seleccionados=0
        for item in "${DIRECTORIOS_PERSONALES[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "$item"
          [[ "$seleccionado" == "true" ]] && total_seleccionados=$((total_seleccionados + 1))
        done
        for item in "${DIRECTORIOS_CONFIG[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "$item"
          [[ "$seleccionado" == "true" ]] && total_seleccionados=$((total_seleccionados + 1))
        done
        for item in "${DIRECTORIOS_GAMING[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "$item"
          [[ "$seleccionado" == "true" ]] && total_seleccionados=$((total_seleccionados + 1))
        done
        for item in "${DIRECTORIOS_APPIMAGES[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "$item"
          [[ "$seleccionado" == "true" ]] && total_seleccionados=$((total_seleccionados + 1))
        done
        for item in "${DIRECTORIOS_OTROS[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "$item"
          [[ "$seleccionado" == "true" ]] && total_seleccionados=$((total_seleccionados + 1))
        done
        
        if [[ $total_seleccionados -eq 0 ]]; then
          advertencia "No has seleccionado ningún directorio"
          sleep 2
          continue
        fi
        return 0
        ;;
      s)
        # Seleccionar todos
        for i in "${!DIRECTORIOS_PERSONALES[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_PERSONALES[$i]}"
          DIRECTORIOS_PERSONALES[$i]="${nombre}|${tamano}|true"
        done
        for i in "${!DIRECTORIOS_CONFIG[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_CONFIG[$i]}"
          DIRECTORIOS_CONFIG[$i]="${nombre}|${tamano}|true"
        done
        for i in "${!DIRECTORIOS_GAMING[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_GAMING[$i]}"
          DIRECTORIOS_GAMING[$i]="${nombre}|${tamano}|true"
        done
        for i in "${!DIRECTORIOS_APPIMAGES[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_APPIMAGES[$i]}"
          DIRECTORIOS_APPIMAGES[$i]="${nombre}|${tamano}|true"
        done
        for i in "${!DIRECTORIOS_OTROS[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_OTROS[$i]}"
          DIRECTORIOS_OTROS[$i]="${nombre}|${tamano}|true"
        done
        exito "Todos los directorios seleccionados"
        sleep 1
        ;;
      n)
        # Desmarcar todos
        for i in "${!DIRECTORIOS_PERSONALES[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_PERSONALES[$i]}"
          DIRECTORIOS_PERSONALES[$i]="${nombre}|${tamano}|false"
        done
        for i in "${!DIRECTORIOS_CONFIG[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_CONFIG[$i]}"
          DIRECTORIOS_CONFIG[$i]="${nombre}|${tamano}|false"
        done
        for i in "${!DIRECTORIOS_GAMING[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_GAMING[$i]}"
          DIRECTORIOS_GAMING[$i]="${nombre}|${tamano}|false"
        done
        for i in "${!DIRECTORIOS_APPIMAGES[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_APPIMAGES[$i]}"
          DIRECTORIOS_APPIMAGES[$i]="${nombre}|${tamano}|false"
        done
        for i in "${!DIRECTORIOS_OTROS[@]}"; do
          IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_OTROS[$i]}"
          DIRECTORIOS_OTROS[$i]="${nombre}|${tamano}|false"
        done
        info "Todos los directorios desmarcados"
        sleep 1
        ;;
      [0-9]*)
        if [[ "$opcion" =~ ^[0-9]+$ ]] && [[ $opcion -ge 1 ]] && [[ $opcion -lt $num_opcion ]]; then
          local categoria_info="${TODAS_CATEGORIAS[$opcion]}"
          local categoria=$(echo "$categoria_info" | cut -d: -f1)
          local indice=$(echo "$categoria_info" | cut -d: -f2)
          
          case "$categoria" in
            personales)
              IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_PERSONALES[$indice]}"
              if [[ "$seleccionado" == "true" ]]; then
                DIRECTORIOS_PERSONALES[$indice]="${nombre}|${tamano}|false"
              else
                DIRECTORIOS_PERSONALES[$indice]="${nombre}|${tamano}|true"
              fi
              ;;
            config)
              IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_CONFIG[$indice]}"
              if [[ "$seleccionado" == "true" ]]; then
                DIRECTORIOS_CONFIG[$indice]="${nombre}|${tamano}|false"
              else
                DIRECTORIOS_CONFIG[$indice]="${nombre}|${tamano}|true"
              fi
              ;;
            gaming)
              IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_GAMING[$indice]}"
              if [[ "$seleccionado" == "true" ]]; then
                DIRECTORIOS_GAMING[$indice]="${nombre}|${tamano}|false"
              else
                DIRECTORIOS_GAMING[$indice]="${nombre}|${tamano}|true"
              fi
              ;;
            appimages)
              IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_APPIMAGES[$indice]}"
              if [[ "$seleccionado" == "true" ]]; then
                DIRECTORIOS_APPIMAGES[$indice]="${nombre}|${tamano}|false"
              else
                DIRECTORIOS_APPIMAGES[$indice]="${nombre}|${tamano}|true"
              fi
              ;;
            otros)
              IFS='|' read -r nombre tamano seleccionado <<< "${DIRECTORIOS_OTROS[$indice]}"
              if [[ "$seleccionado" == "true" ]]; then
                DIRECTORIOS_OTROS[$indice]="${nombre}|${tamano}|false"
              else
                DIRECTORIOS_OTROS[$indice]="${nombre}|${tamano}|true"
              fi
              ;;
          esac
        else
          advertencia "Opción inválida"
          sleep 1
        fi
        ;;
      *)
        advertencia "Opción inválida. Usa: número (1-$((num_opcion-1))), S, N, C, o 0"
        sleep 2
        ;;
    esac
  done
}

error() {
  local mensaje="$1"
  echo -e "${COLOR_RED}${COLOR_BOLD}✗ Error:${COLOR_RESET} $mensaje" >&2
  log "ERROR: $mensaje"
}

exito() {
  local mensaje="$1"
  echo -e "${COLOR_GREEN}${COLOR_BOLD}✓${COLOR_RESET} $mensaje"
  log "OK: $mensaje"
}

advertencia() {
  local mensaje="$1"
  echo -e "${COLOR_YELLOW}${COLOR_BOLD}⚠ Advertencia:${COLOR_RESET} $mensaje"
  log "ADVERTENCIA: $mensaje"
}

info() {
  local mensaje="$1"
  echo -e "${COLOR_BLUE}${COLOR_BOLD}ℹ${COLOR_RESET} $mensaje"
  log "INFO: $mensaje"
}

separador() {
  echo -e "${COLOR_CYAN}────────────────────────────────────────────────────────────────${COLOR_RESET}"
}

###############################################################################
## LIMPIEZA Y MANEJO DE SEÑALES
###############################################################################

limpieza() {
  log "Iniciando limpieza..."
  if [[ -f "$LOCK_FILE" ]]; then
    rm -f "$LOCK_FILE"
    log "Archivo de bloqueo eliminado"
  fi
  log "Script finalizado"
}

trap limpieza EXIT ERR

###############################################################################
## VALIDACIONES
###############################################################################

verificar_root() {
  if [[ $EUID -ne 0 ]]; then
    error "Este script debe ejecutarse con privilegios de root o sudo"
    info "Ejecuta: sudo $0"
    exit 1
  fi
  exito "Privilegios de root verificados"
}

crear_lock() {
  if [[ -f "$LOCK_FILE" ]]; then
    error "Otra instancia del script está en ejecución"
    info "Archivo de bloqueo: $LOCK_FILE"
    exit 1
  fi
  touch "$LOCK_FILE"
  log "Archivo de bloqueo creado"
}

validar_usuario_existe() {
  local usuario="$1"
  if id "$usuario" &>/dev/null; then
    return 0
  else
    return 1
  fi
}

validar_usuario_no_existe() {
  local usuario="$1"
  if id "$usuario" &>/dev/null; then
    return 1
  else
    return 0
  fi
}

validar_nombre_usuario() {
  local usuario="$1"
  # Solo letras minúsculas, números, guiones bajos y guiones
  # No debe empezar con número o guión
  if [[ "$usuario" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
    return 0
  else
    return 1
  fi
}

###############################################################################
## FUNCIONES DE INTERACCIÓN
###############################################################################

preguntar() {
  local pregunta="$1"
  local respuesta=""
  
  while true; do
    echo -en "${COLOR_CYAN}${pregunta}${COLOR_RESET} "
    read -r respuesta
    respuesta=$(echo "$respuesta" | tr '[:upper:]' '[:lower:]')
    
    case "$respuesta" in
      s|si|sí|y|yes)
        return 0
        ;;
      n|no)
        return 1
        ;;
      *)
        advertencia "Por favor responde 's' o 'n'"
        ;;
    esac
  done
}

preguntar_texto() {
  local pregunta="$1"
  local respuesta=""
  
  echo -en "${COLOR_CYAN}${pregunta}${COLOR_RESET} "
  read -r respuesta
  echo "$respuesta"
}

mostrar_progreso() {
  local mensaje="$1"
  echo -en "${COLOR_YELLOW}⏳ ${mensaje}...${COLOR_RESET} "
  log "PROGRESO: $mensaje"
}

seleccionar_de_lista() {
  local titulo="$1"
  shift
  local -a opciones=("$@")
  local num_opciones=${#opciones[@]}
  local seleccion=""
  local resultado=""

  # Mostrar menú por stderr para no contaminar stdout
  echo "" >&2
  info "$titulo" >&2
  echo "" >&2

  local i=1
  for opcion in "${opciones[@]}"; do
    echo -e "  ${COLOR_BOLD}${i})${COLOR_RESET} $opcion" >&2
    ((i++))
  done

  echo -e "  ${COLOR_BOLD}0)${COLOR_RESET} Cancelar / Volver atrás" >&2
  echo "" >&2

  while true; do
    echo -en "${COLOR_CYAN}Selecciona una opción (0-$num_opciones):${COLOR_RESET} " >&2
    read -r seleccion

    if [[ "$seleccion" == "0" ]]; then
      return 1
    fi

    if [[ "$seleccion" =~ ^[0-9]+$ ]] && [[ "$seleccion" -ge 1 ]] && [[ "$seleccion" -le "$num_opciones" ]]; then
      resultado="${opciones[$((seleccion - 1))]}"
      printf '%s\n' "$resultado"
      return 0
    else
      advertencia "Opción inválida. Introduce un número entre 0 y $num_opciones" >&2
    fi
  done
}

# Función para menú con opción de entrada de texto
menu_con_input() {
  local titulo="$1"
  local texto_opcion="$2"
  shift 2
  local -a opciones_adicionales=("$@")
  local seleccion=""

  # Mostrar menú por stderr
  echo "" >&2
  info "$titulo" >&2
  echo "" >&2

  echo -e "  ${COLOR_BOLD}1)${COLOR_RESET} $texto_opcion" >&2

  local i=2
  for opcion in "${opciones_adicionales[@]}"; do
    echo -e "  ${COLOR_BOLD}${i})${COLOR_RESET} $opcion" >&2
    ((i++))
  done

  echo -e "  ${COLOR_BOLD}0)${COLOR_RESET} Cancelar / Volver atrás" >&2
  echo "" >&2

  local total_opciones=$((1 + ${#opciones_adicionales[@]}))

  while true; do
    echo -en "${COLOR_CYAN}Selecciona una opción (0-$total_opciones):${COLOR_RESET} " >&2
    read -r seleccion

    if [[ "$seleccion" == "0" ]]; then
      return 1
    fi

    if [[ "$seleccion" == "1" ]]; then
      # Opción de escribir texto
      echo -en "${COLOR_CYAN}Introduce el valor:${COLOR_RESET} " >&2
      read -r seleccion
      printf '%s\n' "$seleccion"
      return 0
    fi

    if [[ "$seleccion" =~ ^[0-9]+$ ]] && [[ "$seleccion" -ge 2 ]] && [[ "$seleccion" -le "$total_opciones" ]]; then
      local idx=$((seleccion - 2))
      printf '%s\n' "${opciones_adicionales[$idx]}"
      return 0
    else
      advertencia "Opción inválida. Introduce un número entre 0 y $total_opciones" >&2
    fi
  done
}

###############################################################################
## FUNCIONES DE CONTRASEÑA (BYPASS PAM)
###############################################################################

pedir_contrasena() {
  local contrasena1=""
  local contrasena2=""

  echo "" >&2
  info "Configuración de contraseña (bypass de restricción de 6 caracteres)" >&2
  echo "" >&2
  info "Puedes usar cualquier contraseña, incluso de menos de 6 caracteres" >&2
  echo "" >&2

  while true; do
    echo -en "${COLOR_CYAN}Introduce la contraseña (vacío para dejar bloqueado):${COLOR_RESET} " >&2
    read -rs contrasena1
    echo "" >&2

    if [[ -z "$contrasena1" ]]; then
      printf '%s\n' ""
      return 0
    fi

    echo -en "${COLOR_CYAN}Repite la contraseña:${COLOR_RESET} " >&2
    read -rs contrasena2
    echo "" >&2

    if [[ "$contrasena1" != "$contrasena2" ]]; then
      advertencia "Las contraseñas no coinciden. Intenta de nuevo." >&2
      continue
    fi

    printf '%s\n' "$contrasena1"
    return 0
  done
}

establecer_contrasena_bypass() {
  local usuario="$1"
  local contrasena="$2"

  if [[ -z "$contrasena" ]]; then
    info "Usuario creado sin contraseña (bloqueado)"
    log "Usuario $usuario creado sin contraseña (bloqueado)"
    return 0
  fi

  mostrar_progreso "Estableciendo contraseña para '$usuario'"

  # Generar hash SHA-512 con openssl (bypass de PAM)
  if command -v openssl &>/dev/null; then
    local hash
    hash=$(openssl passwd -6 "$contrasena")
    if usermod --password "$hash" "$usuario" 2>/dev/null; then
      exito "Contraseña establecida correctamente (bypass PAM)"
      log "Contraseña establecida para $usuario usando hash SHA-512"
    else
      error "No se pudo establecer la contraseña"
      return 1
    fi
  else
    # Fallback: chpasswd también bypass PAM
    if echo "$usuario:$contrasena" | chpasswd 2>/dev/null; then
      exito "Contraseña establecida correctamente (chpasswd)"
      log "Contraseña establecida para $usuario usando chpasswd"
    else
      error "No se pudo establecer la contraseña"
      return 1
    fi
  fi
}

###############################################################################
## FLUJO INTERACTIVO
###############################################################################

paso_1_presentacion() {
  clear
  mostrar_cabecera
  separador
  echo ""
  info "Bienvenido al asistente de clonación de usuarios para Bazzite Linux"
  echo ""
  info "Este script te ayudará a clonar un perfil de usuario existente"
  info "a uno nuevo, preservando configuraciones, grupos y datos."
  echo ""
  advertencia "⚠ ADVERTENCIA: Esta operación requiere privilegios de administrador"
  advertencia "  y modificará el sistema. Asegúrate de tener backups."
  echo ""
  separador
  echo ""
  
  if ! preguntar "¿Deseas continuar? (s/n):"; then
    info "Operación cancelada por el usuario"
    exit 0
  fi
}

paso_2_usuario_origen() {
  echo ""
  separador
  echo ""
  info "PASO 1/7: Selección del usuario origen"
  echo ""

  # Obtener lista de usuarios disponibles
  local usuarios=()
  while IFS= read -r linea; do
    usuarios+=("$linea")
  done < <(awk -F: '$3 >= 1000 && $3 != 65534 {print $1}' /etc/passwd | head -20)

  if [[ ${#usuarios[@]} -eq 0 ]]; then
    error "No se encontraron usuarios disponibles para clonar"
    exit 1
  fi

  local usuario_seleccionado=""

  while true; do
    usuario_seleccionado=$(seleccionar_de_lista "Usuarios disponibles:" "${usuarios[@]}")

    if [[ $? -ne 0 ]]; then
      info "Operación cancelada por el usuario"
      exit 0
    fi

    USUARIO_ORIGEN="$usuario_seleccionado"

    # Mostrar información del usuario seleccionado
    echo ""
    exito "Usuario seleccionado: '$USUARIO_ORIGEN'"
    echo ""
    echo "  ${COLOR_BOLD}Información del usuario:${COLOR_RESET}"
    echo "  Nombre: $(id -un "$USUARIO_ORIGEN")"
    echo "  UID: $(id -u "$USUARIO_ORIGEN")"
    echo "  GID: $(id -g "$USUARIO_ORIGEN")"
    echo "  Grupos: $(id -Gn "$USUARIO_ORIGEN" | tr ' ' ', ')"
    echo "  Home: $(getent passwd "$USUARIO_ORIGEN" | cut -d: -f6)"
    echo "  Shell: $(getent passwd "$USUARIO_ORIGEN" | cut -d: -f7)"
    echo ""

    if preguntar "¿Es este el usuario correcto? (s/n):"; then
      break
    fi
  done
}

paso_3_usuario_destino() {
  echo ""
  separador
  echo ""
  info "PASO 2/7: Creación del usuario destino"
  echo ""

  while true; do
    local nombre_ingresado=""
    nombre_ingresado=$(menu_con_input "Opciones disponibles:" \
      "Escribir nombre para el nuevo usuario" \
      "← Volver al paso anterior (seleccionar otro usuario origen)")

    if [[ $? -ne 0 ]]; then
      # Cancelar - volver al paso anterior
      paso_2_usuario_origen
      return
    fi

    if [[ "$nombre_ingresado" == "← Volver al paso anterior (seleccionar otro usuario origen)" ]]; then
      paso_2_usuario_origen
      return
    fi

    USUARIO_DESTINO="$nombre_ingresado"

    # Validaciones
    if [[ -z "$USUARIO_DESTINO" ]]; then
      advertencia "El nombre no puede estar vacío"
      sleep 1
      continue
    fi

    if ! validar_nombre_usuario "$USUARIO_DESTINO"; then
      advertencia "Nombre de usuario inválido. Usa solo letras minúsculas, números, guiones y guiones bajos"
      sleep 1
      continue
    fi

    if [[ "$USUARIO_DESTINO" == "$USUARIO_ORIGEN" ]]; then
      advertencia "El usuario destino no puede ser igual al origen"
      sleep 1
      continue
    fi

    if ! validar_usuario_no_existe "$USUARIO_DESTINO"; then
      error "El usuario '$USUARIO_DESTINO' ya existe"
      sleep 1
      continue
    fi

    exito "Nombre de usuario '$USUARIO_DESTINO' disponible"

    if preguntar "¿Confirmas usar '$USUARIO_DESTINO' como nombre? (s/n):"; then
      break
    fi
  done
}

paso_3_contrasena() {
  echo ""
  separador
  echo ""
  info "PASO 3/7: Configuración de contraseña"
  echo ""

  local opcion_contrasena=""
  opcion_contrasena=$(seleccionar_de_lista "Opciones de contraseña:" \
    "Sí, establecer contraseña ahora" \
    "No, dejar usuario bloqueado (sin contraseña)")

  if [[ $? -ne 0 ]]; then
    info "Volviendo al paso anterior..."
    paso_3_usuario_destino
    paso_3_contrasena
    return
  fi

  if [[ "$opcion_contrasena" == "Sí, establecer contraseña ahora" ]]; then
    ESTABLECER_CONTRASENA=true
    CONTRASENA_DESTINO=$(pedir_contrasena)
    if [[ $? -ne 0 ]] || [[ -z "$CONTRASENA_DESTINO" ]]; then
      advertencia "No se estableció contraseña. Usuario quedará bloqueado."
      ESTABLECER_CONTRASENA=false
    else
      exito "Contraseña configurada (longitud: ${#CONTRASENA_DESTINO} caracteres)"
    fi
  else
    ESTABLECER_CONTRASENA=false
    info "Usuario se creará sin contraseña (bloqueado)"
  fi
}

paso_4_seleccionar_directorios() {
  echo ""
  separador
  echo ""
  info "PASO 4/7: Selección de directorios a copiar"
  echo ""
  
  info "Escaneando directorios del usuario '$USUARIO_ORIGEN'..."
  mostrar_progreso "Calculando tamaños"
  
  local home_origen
  home_origen=$(getent passwd "$USUARIO_ORIGEN" | cut -d: -f6)
  
  detectar_directorios_categorizados "$home_origen"
  
  exito "Escaneo completado"
  echo ""
  
  local total_dirs=$((${#DIRECTORIOS_PERSONALES[@]} + ${#DIRECTORIOS_CONFIG[@]} + ${#DIRECTORIOS_GAMING[@]} + ${#DIRECTORIOS_APPIMAGES[@]} + ${#DIRECTORIOS_OTROS[@]}))
  
  if [[ $total_dirs -eq 0 ]]; then
    advertencia "No se encontraron directorios para copiar en el home del usuario origen"
    info "Se procederá a crear el usuario sin copiar datos"
    COPIAR_DATOS=false
    sleep 3
    return 0
  fi
  
  info "Se encontraron $total_dirs elementos para copiar"
  info "Usa el menú interactivo para seleccionar los que deseas copiar"
  echo ""
  
  if ! menu_checkbox_categorias; then
    info "Volviendo al paso anterior..."
    paso_3_contrasena
    paso_4_seleccionar_directorios
    return
  fi
  
  # Verificar si se seleccionó algo
  local seleccionados=0
  for item in "${DIRECTORIOS_PERSONALES[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    [[ "$seleccionado" == "true" ]] && ((seleccionados++))
  done
  for item in "${DIRECTORIOS_CONFIG[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    [[ "$seleccionado" == "true" ]] && ((seleccionados++))
  done
  for item in "${DIRECTORIOS_GAMING[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    [[ "$seleccionado" == "true" ]] && ((seleccionados++))
  done
  for item in "${DIRECTORIOS_APPIMAGES[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    [[ "$seleccionado" == "true" ]] && ((seleccionados++))
  done
  for item in "${DIRECTORIOS_OTROS[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    [[ "$seleccionado" == "true" ]] && ((seleccionados++))
  done
  
  if [[ $seleccionados -eq 0 ]]; then
    info "No seleccionaste ningún directorio"
    info "Se creará el usuario sin copiar datos personales"
    COPIAR_DATOS=false
  else
    COPIAR_DATOS=true
    exito "$seleccionados directorios seleccionados para copiar"
  fi
  
  sleep 2
}

paso_5_opciones_avanzadas() {
  echo ""
  separador
  echo ""
  info "PASO 5/7: Opciones avanzadas de copia"
  echo ""

  # Menú 1: Copiar datos Flatpak (si hay datos seleccionados)
  if $COPIAR_DATOS; then
    echo ""
    info "Bazzite usa Flatpak para aplicaciones. Los datos están en ~/.var/app"
    local opcion_flatpak=""
    opcion_flatpak=$(seleccionar_de_lista "Datos de aplicaciones Flatpak:" \
      "Sí, copiar datos de Flatpak" \
      "No, omitir datos de Flatpak")

    if [[ $? -ne 0 ]]; then
      paso_5_opciones_avanzadas
      return
    fi

    if [[ "$opcion_flatpak" == "Sí, copiar datos de Flatpak" ]]; then
      COPIAR_FLATPAK=true
    else
      COPIAR_FLATPAK=false
    fi

    # Menú 2: Ajustar SELinux
    echo ""
    info "Fedora/Atomic usa SELinux para seguridad"
    local opcion_selinux=""
    opcion_selinux=$(seleccionar_de_lista "Contextos SELinux:" \
      "Sí, ajustar contextos SELinux" \
      "No, omitir ajuste SELinux")

    if [[ $? -ne 0 ]]; then
      paso_5_opciones_avanzadas
      return
    fi

    if [[ "$opcion_selinux" == "Sí, ajustar contextos SELinux" ]]; then
      AJUSTAR_SELINUX=true
    else
      AJUSTAR_SELINUX=false
    fi
  else
    info "No se copiarán datos, omitiendo opciones de Flatpak y SELinux"
    COPIAR_FLATPAK=false
    AJUSTAR_SELINUX=false
  fi

  # Menú 3: Modo verbose
  echo ""
  info "Modo verbose muestra detalles de la operación"
  local opcion_verbose=""
  opcion_verbose=$(seleccionar_de_lista "Modo de ejecución:" \
    "Normal (resumido)" \
    "Verbose (mostrar detalles)")

  if [[ $? -ne 0 ]]; then
    paso_5_opciones_avanzadas
    return
  fi

  if [[ "$opcion_verbose" == "Verbose (mostrar detalles)" ]]; then
    MODO_VERBOSE=true
  else
    MODO_VERBOSE=false
  fi
}

paso_6_resumen() {
  echo ""
  separador
  echo ""
  info "PASO 6/7: Resumen de la operación"
  echo ""
  
  echo -e "${COLOR_BOLD}Configuración seleccionada:${COLOR_RESET}"
  echo "  Usuario origen:     $USUARIO_ORIGEN"
  echo "  Usuario destino:    $USUARIO_DESTINO"
  echo "  Copiar datos:       $([[ $COPIAR_DATOS == true ]] && echo "Sí ✓" || echo "No ✗")"
  echo "  Copiar Flatpak:     $([[ $COPIAR_FLATPAK == true ]] && echo "Sí ✓" || echo "No ✗")"
  echo "  Ajustar SELinux:    $([[ $AJUSTAR_SELINUX == true ]] && echo "Sí ✓" || echo "No ✗")"
  echo "  Modo verbose:       $([[ $MODO_VERBOSE == true ]] && echo "Sí ✓" || echo "No ✗")"
  echo ""
  
  if $COPIAR_DATOS; then
    echo -e "${COLOR_BOLD}Directorios seleccionados para copiar:${COLOR_RESET}"
    
    local hay_seleccionados=false
    
    for item in "${DIRECTORIOS_PERSONALES[@]}"; do
      IFS='|' read -r nombre tamano seleccionado <<< "$item"
      if [[ "$seleccionado" == "true" ]]; then
        echo "  📁 $nombre ($(formatear_tamano $tamano))"
        hay_seleccionados=true
      fi
    done
    
    for item in "${DIRECTORIOS_CONFIG[@]}"; do
      IFS='|' read -r nombre tamano seleccionado <<< "$item"
      if [[ "$seleccionado" == "true" ]]; then
        echo "  ⚙️  $nombre ($(formatear_tamano $tamano))"
        hay_seleccionados=true
      fi
    done
    
    for item in "${DIRECTORIOS_GAMING[@]}"; do
      IFS='|' read -r nombre tamano seleccionado <<< "$item"
      if [[ "$seleccionado" == "true" ]]; then
        echo "  🎮 $nombre ($(formatear_tamano $tamano))"
        hay_seleccionados=true
      fi
    done
    
    for item in "${DIRECTORIOS_APPIMAGES[@]}"; do
      IFS='|' read -r nombre tamano seleccionado <<< "$item"
      if [[ "$seleccionado" == "true" ]]; then
        local nombre_corto=$(basename "$nombre")
        echo "  📦 $nombre_corto ($(formatear_tamano $tamano))"
        hay_seleccionados=true
      fi
    done
    
    for item in "${DIRECTORIOS_OTROS[@]}"; do
      IFS='|' read -r nombre tamano seleccionado <<< "$item"
      if [[ "$seleccionado" == "true" ]]; then
        echo "  📂 $nombre ($(formatear_tamano $tamano))"
        hay_seleccionados=true
      fi
    done
    
    if [[ "$hay_seleccionados" == "false" ]]; then
      echo "  (Ninguno - solo se creará la estructura básica)"
    fi
    echo ""
  fi
  
  advertencia "⚠ Esta operación creará un nuevo usuario y potencialmente"
  advertencia "  copiará gigabytes de datos. Asegúrate de tener espacio suficiente."
  echo ""
  
  separador
  echo ""
  
  echo ""
  local opcion_confirmacion=""
  opcion_confirmacion=$(seleccionar_de_lista "¿Qué deseas hacer?" \
    "✓ Confirmar y ejecutar la operación" \
    "✗ Cancelar y salir" \
    "← Volver a modificar opciones")

  if [[ $? -ne 0 ]]; then
    info "Operación cancelada por el usuario"
    exit 0
  fi

  case "$opcion_confirmacion" in
    "✓ Confirmar y ejecutar la operación")
      return 0
      ;;
    "✗ Cancelar y salir")
      info "Operación cancelada por el usuario"
      exit 0
      ;;
    "← Volver a modificar opciones")
      paso_5_opciones_avanzadas
      paso_6_resumen
      return
      ;;
  esac
}

###############################################################################
## EJECUCIÓN DE OPERACIONES
###############################################################################

crear_usuario() {
  echo ""
  separador
  echo ""
  info "PASO 7/7: Ejecutando operaciones"
  echo ""
  
  # Obtener información del usuario origen
  local shell_origen
  shell_origen=$(getent passwd "$USUARIO_ORIGEN" | cut -d: -f7)
  
  local grupos_suplementarios
  grupos_suplementarios=$(id -Gn "$USUARIO_ORIGEN" | tr ' ' ',' | sed "s/,$USUARIO_ORIGEN//;s/^$USUARIO_ORIGEN,//;s/,$USUARIO_ORIGEN$//")
  
  mostrar_progreso "Creando usuario '$USUARIO_DESTINO'"
  
  if $MODO_VERBOSE; then
    useradd -m -s "$shell_origen" -G "$grupos_suplementarios" "$USUARIO_DESTINO" 2>&1 | tee -a "$LOG_FILE"
  else
    useradd -m -s "$shell_origen" -G "$grupos_suplementarios" "$USUARIO_DESTINO" >> "$LOG_FILE" 2>&1
  fi
  
  exito "Usuario creado exitosamente"
  log "Usuario creado: $USUARIO_DESTINO con shell $shell_origen y grupos $grupos_suplementarios"
}

copiar_datos() {
  if ! $COPIAR_DATOS; then
    info "Omitiendo copia de datos (configurado por usuario)"
    return 0
  fi
  
  local home_origen
  home_origen=$(getent passwd "$USUARIO_ORIGEN" | cut -d: -f6)
  
  local home_destino
  home_destino=$(getent passwd "$USUARIO_DESTINO" | cut -d: -f6)
  
  local uid_destino
  uid_destino=$(id -u "$USUARIO_DESTINO")
  
  local gid_destino
  gid_destino=$(id -g "$USUARIO_DESTINO")
  
  echo ""
  info "Copiando directorios seleccionados..."
  echo ""
  
  local rsync_opts="-avP"
  if ! $COPIAR_FLATPAK; then
    rsync_opts="$rsync_opts --exclude=.var"
  fi
  
  local total_copiados=0
  local errores=0
  
  # Función auxiliar para copiar un directorio
  copiar_directorio() {
    local origen="$1"
    local destino="$2"
    local nombre="$3"
    
    if [[ ! -e "$origen" ]]; then
      advertencia "No existe: $nombre"
      return 1
    fi
    
    mostrar_progreso "Copiando $nombre"
    
    # Crear directorio padre si no existe
    local dir_destino=$(dirname "$destino")
    if [[ ! -d "$dir_destino" ]]; then
      mkdir -p "$dir_destino" 2>/dev/null || true
    fi
    
    if $MODO_VERBOSE; then
      if rsync $rsync_opts "$origen" "$destino" 2>&1 | tee -a "$LOG_FILE"; then
        exito "$nombre copiado"
        return 0
      else
        error "Error copiando $nombre"
        return 1
      fi
    else
      if rsync $rsync_opts "$origen" "$destino" >> "$LOG_FILE" 2>&1; then
        exito "$nombre copiado"
        return 0
      else
        error "Error copiando $nombre"
        return 1
      fi
    fi
  }
  
  # Copiar directorios personales seleccionados
  for item in "${DIRECTORIOS_PERSONALES[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    if [[ "$seleccionado" == "true" ]]; then
      local origen="$home_origen/$nombre"
      local destino="$home_destino/$nombre"
      if copiar_directorio "$origen" "$destino" "$nombre"; then
        ((total_copiados++))
      else
        ((errores++))
      fi
    fi
  done
  
  # Copiar directorios de configuración seleccionados
  for item in "${DIRECTORIOS_CONFIG[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    if [[ "$seleccionado" == "true" ]]; then
      local origen="$home_origen/$nombre"
      local destino="$home_destino/$nombre"
      if copiar_directorio "$origen" "$destino" "$nombre"; then
        ((total_copiados++))
      else
        ((errores++))
      fi
    fi
  done
  
  # Copiar directorios de gaming seleccionados
  for item in "${DIRECTORIOS_GAMING[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    if [[ "$seleccionado" == "true" ]]; then
      local origen="$home_origen/$nombre"
      local destino="$home_destino/$nombre"
      if copiar_directorio "$origen" "$destino" "$nombre"; then
        ((total_copiados++))
      else
        ((errores++))
      fi
    fi
  done
  
  # Copiar AppImages seleccionados
  for item in "${DIRECTORIOS_APPIMAGES[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    if [[ "$seleccionado" == "true" ]]; then
      local origen="$home_origen/$nombre"
      local destino="$home_destino/$nombre"
      local nombre_corto=$(basename "$nombre")
      if copiar_directorio "$origen" "$destino" "$nombre_corto"; then
        ((total_copiados++))
      else
        ((errores++))
      fi
    fi
  done
  
  # Copiar otros directorios seleccionados
  for item in "${DIRECTORIOS_OTROS[@]}"; do
    IFS='|' read -r nombre tamano seleccionado <<< "$item"
    if [[ "$seleccionado" == "true" ]]; then
      local origen="$home_origen/$nombre"
      local destino="$home_destino/$nombre"
      if copiar_directorio "$origen" "$destino" "$nombre"; then
        ((total_copiados++))
      else
        ((errores++))
      fi
    fi
  done
  
  echo ""
  if [[ $errores -eq 0 ]]; then
    exito "$total_copiados directorios copiados exitosamente"
  else
    advertencia "$total_copiados directorios copiados, $errores con errores"
  fi
  log "Copia completada: $total_copiados copiados, $errores errores"
  
  # Ajustar permisos
  echo ""
  mostrar_progreso "Ajustando permisos en $home_destino"
  
  chown -R "${uid_destino}:${gid_destino}" "$home_destino" 2>> "$LOG_FILE"
  
  exito "Permisos ajustados correctamente"
  log "Permisos cambiados a ${uid_destino}:${gid_destino} para $home_destino"
}

ajustar_selinux() {
  if ! $AJUSTAR_SELINUX; then
    info "Omitiendo ajuste de contextos SELinux (configurado por usuario)"
    return 0
  fi
  
  local home_destino
  home_destino=$(getent passwd "$USUARIO_DESTINO" | cut -d: -f6)
  
  echo ""
  mostrar_progreso "Restaurando contextos SELinux en $home_destino"
  
  if command -v restorecon &>/dev/null; then
    if $MODO_VERBOSE; then
      restorecon -Rv "$home_destino" 2>&1 | tee -a "$LOG_FILE"
    else
      restorecon -Rv "$home_destino" >> "$LOG_FILE" 2>&1
    fi
    exito "Contextos SELinux restaurados"
    log "SELinux restorecon ejecutado en $home_destino"
  else
    advertencia "Comando restorecon no encontrado, omitiendo ajuste SELinux"
    log "WARNING: restorecon no disponible"
  fi
}

###############################################################################
## VERIFICACIÓN FINAL
###############################################################################

verificar_resultado() {
  echo ""
  separador
  echo ""
  info "Verificando resultado..."
  echo ""
  
  if validar_usuario_existe "$USUARIO_DESTINO"; then
    exito "Usuario '$USUARIO_DESTINO' existe en el sistema"
    echo "  UID: $(id -u "$USUARIO_DESTINO")"
    echo "  GID: $(id -g "$USUARIO_DESTINO")"
    echo "  Home: $(getent passwd "$USUARIO_DESTINO" | cut -d: -f6)"
    echo "  Shell: $(getent passwd "$USUARIO_DESTINO" | cut -d: -f7)"
    echo "  Grupos: $(id -Gn "$USUARIO_DESTINO" | tr ' ' ', ')"
  else
    error "El usuario destino no se creó correctamente"
    return 1
  fi
  
  echo ""
  exito "¡Clonación completada exitosamente!"
  echo ""
  info "El usuario '$USUARIO_DESTINO' está listo para usar"
  info "Log guardado en: $LOG_FILE"
}

###############################################################################
## FUNCIÓN PRINCIPAL
###############################################################################

main() {
  # Inicializar log
  echo "=== User Cloner v$VERSION ===" > "$LOG_FILE"
  log "Script iniciado"
  
  # Verificaciones iniciales
  verificar_root
  crear_lock
  
  # Flujo interactivo de 7 pasos:
  # 1. Presentación
  # 2. Selección usuario origen
  # 3. Creación usuario destino + contraseña
  # 4. Selección directorios específicos (¡NUEVO!)
  # 5. Opciones avanzadas (Flatpak, SELinux, Verbose)
  # 6. Resumen
  # 7. Ejecución
  
  paso_1_presentacion
  paso_2_usuario_origen
  paso_3_usuario_destino
  paso_3_contrasena
  paso_4_seleccionar_directorios
  paso_5_opciones_avanzadas
  paso_6_resumen

  # Ejecución
  crear_usuario
  establecer_contrasena_bypass "$USUARIO_DESTINO" "$CONTRASENA_DESTINO"
  copiar_datos
  ajustar_selinux
  verificar_resultado
  
  log "Script completado exitosamente"
}

# Ejecutar función principal
main "$@"
