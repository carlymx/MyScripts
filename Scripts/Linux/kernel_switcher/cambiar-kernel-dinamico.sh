#!/bin/bash
# cambiar-kernel-dinamico.sh
# Detecta kernels instalados y genera entradas GRUB automáticamente
# Uso: sudo ./cambiar-kernel-dinamico.sh [opciones]

set -euo pipefail

readonly SCRIPT_NAME="$(basename "$0")"
readonly GRUB_CONFIG="/etc/default/grub"
readonly BACKUP_DIR="/var/backups/grub-kernel-selector"

# Colores
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly NC='\033[0m'

# Funciones de log a stderr para que se vean con sudo
log_info()    { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_ok()      { echo -e "${GREEN}[OK]${NC} $*" >&2; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_header()  { echo -e "\n${CYAN}=== $* ===${NC}\n" >&2; }
log_subheader() { echo -e "\n${MAGENTA}--- $* ---${NC}\n" >&2; }

# Verificar root
check_root() {
    [[ $EUID -eq 0 ]] || { log_error "Requiere root. Usa: sudo $0"; exit 1; }
}

# Detectar kernels instalados
detect_kernels() {
    local kernels=()
    for vmlinuz in /boot/vmlinuz-*; do
        [[ -f "$vmlinuz" ]] || continue
        local version="${vmlinuz##*/vmlinuz-}"
        kernels+=("$version")
    done
    printf '%s\n' "${kernels[@]}"
}

# Obtener entrada GRUB actual
get_current_grub_default() {
    grep '^GRUB_DEFAULT=' "$GRUB_CONFIG" 2>/dev/null | cut -d= -f2- | tr -d '"' || echo "0"
}

# Construir entrada GRUB principal para un kernel
build_grub_entry() {
    local version="$1"
    echo "Advanced options for Ubuntu>Ubuntu, with Linux $version"
}

# ===== MENÚS =====

# Menú principal
show_main_menu() {
    local kernels
    mapfile -t kernels < <(detect_kernels)
    [[ ${#kernels[@]} -gt 0 ]] || { log_error "No se detectaron kernels en /boot"; exit 1; }

    while true; do
        log_header "MENÚ PRINCIPAL - Selector de Kernel GRUB"
        local current_default="$(get_current_grub_default)"
        printf "Kernel actual por defecto: ${YELLOW}%s${NC}\n" "$current_default"
        echo

        local options=(
            "Cambiar kernel por defecto"
            "Backups (crear / restaurar / listar)"
            "Ver estado actual"
            "Salir"
        )

        PS3="Elige una opción [1-${#options[@]}]: "
        select choice in "${options[@]}"; do
            case $REPLY in
                1) select_kernel_menu "${kernels[@]}"; break ;;
                2) backup_menu; break ;;
                3) show_status; break ;;
                4) log_info "Saliendo..."; exit 0 ;;
                *) log_error "Opción inválida. Intenta de nuevo." ;;
            esac
        done
    done
}

# Submenú: Seleccionar kernel
select_kernel_menu() {
    local kernels=("$@")
    local current_default="$(get_current_grub_default)"

    while true; do
        log_subheader "SELECCIONAR KERNEL POR DEFECTO"
        printf "Actual: ${YELLOW}%s${NC}\n\n" "$current_default"

        local menu_entries=()
        local display_options=()

        for kernel in "${kernels[@]}"; do
            local entry
            entry=$(build_grub_entry "$kernel")
            menu_entries+=("$entry")

            local marker=""
            [[ "$current_default" == *"$kernel"* ]] && marker=" ${GREEN}★ (actual)${NC}"

            display_options+=("Linux $kernel$marker")
        done

        # Opción "siempre el último"
        menu_entries+=("0")
        display_options+=("Ubuntu (siempre el último kernel instalado)")

        # Opción volver
        display_options+=("⬅ Volver al menú principal")
        menu_entries+=("__BACK__")

        echo
        PS3="Elige kernel [1-${#display_options[@]}]: "
        select choice in "${display_options[@]}"; do
            if [[ -n "$choice" ]]; then
                for i in "${!display_options[@]}"; do
                    if [[ "${display_options[$i]}" == "$choice" ]]; then
                        local selected="${menu_entries[$i]}"
                        if [[ "$selected" == "__BACK__" ]]; then
                            return 0  # Volver al menú principal
                        fi
                        # Confirmar cambio
                        confirm_and_apply "$selected"
                        return 0
                    fi
                done
            fi
            log_error "Opción inválida. Intenta de nuevo."
        done
    done
}

# Confirmar y aplicar cambio
confirm_and_apply() {
    local new_default="$1"
    echo
    log_warn "Se aplicará: ${CYAN}$new_default${NC}"
    printf "¿Confirmar? [s/N]: "
    read -r confirm
    if [[ "$confirm" =~ ^[sS]$ ]]; then
        backup_grub
        apply_change "$new_default"
        log_header "¡Listo! Reinicia para aplicar el cambio."
    else
        log_info "Cancelado."
    fi
    # Pausa para que se lea el mensaje
    printf "\nPresiona Enter para continuar..."
    read -r
}

# Submenú: Backups
backup_menu() {
    while true; do
        log_subheader "GESTIÓN DE BACKUPS"

        local options=(
            "Crear backup manual"
            "Restaurar backup"
            "Listar backups"
            "⬅ Volver al menú principal"
        )

        PS3="Elige una opción [1-${#options[@]}]: "
        select choice in "${options[@]}"; do
            case $REPLY in
                1) create_manual_backup; break ;;
                2) restore_backup_menu; break ;;
                3) list_backups; break ;;
                4) return 0 ;;
                *) log_error "Opción inválida. Intenta de nuevo." ;;
            esac
        done
    done
}

# Crear backup manual
create_manual_backup() {
    log_info "Creando backup manual..."
    mkdir -p "$BACKUP_DIR"
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_file="$BACKUP_DIR/grub.manual.$timestamp.bak"
    cp "$GRUB_CONFIG" "$backup_file"
    
    # Guardar metadata
    local current_kernel="$(get_current_grub_default)"
    local running_kernel="$(uname -r)"
    cat > "$backup_file.meta" <<EOF
timestamp=$timestamp
date=$(date '+%Y-%m-%d %H:%M:%S')
grub_default=$current_kernel
running_kernel=$running_kernel
type=manual
EOF
    
    log_ok "Backup creado: $backup_file"
    log_info "Kernel GRUB: $current_kernel"
    log_info "Kernel en uso: $running_kernel"
    printf "\nPresiona Enter para continuar..."
    read -r
}

# Listar backups con info
list_backups() {
    log_subheader "BACKUPS DISPONIBLES"
    
    local backups=()
    mapfile -t backups < <(ls -t "$BACKUP_DIR"/grub.*.bak 2>/dev/null || true)
    
    if [[ ${#backups[@]} -eq 0 ]]; then
        log_warn "No hay backups disponibles."
        printf "\nPresiona Enter para continuar..."
        read -r
        return 0
    fi

    printf "%-3s %-20s %-20s %-40s %s\n" "Nº" "FECHA" "TIPO" "KERNEL GRUB" "KERNEL EN USO"
    printf "%s\n" "$(printf '%.0s-' {1..120})"

    local idx=1
    for backup in "${backups[@]}"; do
        local meta_file="${backup}.meta"
        local date_str="desconocido"
        local type_str="auto"
        local grub_kernel="desconocido"
        local running_kernel="desconocido"
        
        if [[ -f "$meta_file" ]]; then
            source "$meta_file"
            date_str="${date:-desconocido}"
            type_str="${type:-auto}"
            grub_kernel="${grub_default:-desconocido}"
            running_kernel="${running_kernel:-desconocido}"
        else
            # Intentar extraer de nombre de archivo
            local fname=$(basename "$backup")
            if [[ "$fname" =~ grub\.(.+)\.bak ]]; then
                date_str="${BASH_REMATCH[1]}"
            fi
        fi
        
        printf "%-3d %-20s %-20s %-40s %s\n"             "$idx" "$date_str" "$type_str" "$grub_kernel" "$running_kernel"
        ((idx++))
    done
    
    printf "\nPresiona Enter para continuar..."
    read -r
}

# Menú restaurar backup
restore_backup_menu() {
    local backups=()
    mapfile -t backups < <(ls -t "$BACKUP_DIR"/grub.*.bak 2>/dev/null || true)
    
    if [[ ${#backups[@]} -eq 0 ]]; then
        log_warn "No hay backups disponibles."
        printf "\nPresiona Enter para continuar..."
        read -r
        return 0
    fi

    log_subheader "RESTAURAR BACKUP"
    echo "Selecciona el backup a restaurar:"
    echo

    local display_options=()
    for backup in "${backups[@]}"; do
        local meta_file="${backup}.meta"
        local date_str="desconocido"
        local grub_kernel="desconocido"
        
        if [[ -f "$meta_file" ]]; then
            source "$meta_file"
            date_str="${date:-desconocido}"
            grub_kernel="${grub_default:-desconocido}"
        fi
        
        display_options+=("[$date_str] GRUB: $grub_kernel")
    done
    display_options+=("⬅ Volver")

    PS3="Elige backup a restaurar [1-${#display_options[@]}]: "
    select choice in "${display_options[@]}"; do
        if [[ -n "$choice" ]]; then
            if [[ "$choice" == "⬅ Volver" ]]; then
                return 0
            fi
            for i in "${!display_options[@]}"; do
                if [[ "${display_options[$i]}" == "$choice" ]]; then
                    restore_backup "${backups[$i]}"
                    return 0
                fi
            done
        fi
        log_error "Opción inválida. Intenta de nuevo."
    done
}

# Restaurar backup específico
restore_backup() {
    local backup_file="$1"
    log_warn "Restaurando: $backup_file"
    printf "¿Confirmar restauración? [s/N]: "
    read -r confirm
    if [[ "$confirm" =~ ^[sS]$ ]]; then
        cp "$backup_file" "$GRUB_CONFIG"
        update-grub
        log_ok "Backup restaurado y GRUB actualizado."
    else
        log_info "Cancelado."
    fi
    printf "\nPresiona Enter para continuar..."
    read -r
}

# ===== ACCIONES =====

# Aplicar cambio
apply_change() {
    local new_default="$1"
    log_info "Actualizando $GRUB_CONFIG..."
    sed -i "s|^GRUB_DEFAULT=.*|GRUB_DEFAULT="$new_default"|" "$GRUB_CONFIG"
    log_ok "GRUB_DEFAULT="$new_default""

    log_info "Regenerando configuración GRUB..."
    update-grub
    log_ok "GRUB actualizado"
}

# Crear backup automático (interno)
backup_grub() {
    mkdir -p "$BACKUP_DIR"
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_file="$BACKUP_DIR/grub.auto.$timestamp.bak"
    cp "$GRUB_CONFIG" "$backup_file"
    
    local current_kernel="$(get_current_grub_default)"
    local running_kernel="$(uname -r)"
    cat > "$backup_file.meta" <<EOF
timestamp=$timestamp
date=$(date '+%Y-%m-%d %H:%M:%S')
grub_default=$current_kernel
running_kernel=$running_kernel
type=auto
EOF
    
    log_info "Backup automático: $backup_file"
}

# Mostrar estado actual
show_status() {
    log_subheader "ESTADO ACTUAL"
    echo "GRUB_DEFAULT: $(get_current_grub_default)"
    echo "Kernel en uso: $(uname -r)"
    echo "Kernels instalados:"
    detect_kernels | sed 's/^/  - /'
    echo
    printf "Presiona Enter para continuar..."
    read -r
}

# ===== CLI DIRECTO (sin menú) =====

# Listar kernels (CLI)
cli_list_kernels() {
    log_header "Kernels disponibles"
    local idx=1
    for kernel in $(detect_kernels); do
        echo "  $idx) $kernel"
        ((idx++))
    done
}

# Estado (CLI)
cli_status() {
    log_header "Estado actual"
    echo "GRUB_DEFAULT: $(get_current_grub_default)"
    echo "Kernel en uso: $(uname -r)"
    echo "Kernels instalados:"
    detect_kernels | sed 's/^/  - /'
}

# Aplicar por versión (CLI)
cli_apply_by_version() {
    local version="$1"
    local kernels
    mapfile -t kernels < <(detect_kernels)

    [[ " ${kernels[*]} " == *" $version "* ]] || {
        log_error "Kernel $version no encontrado. Disponibles: ${kernels[*]}"
        exit 1
    }

    local entry
    entry=$(build_grub_entry "$version")
    backup_grub
    apply_change "$entry"
}

# Restaurar último backup (CLI)
cli_restore_latest() {
    local latest=$(ls -t "$BACKUP_DIR"/grub.*.bak 2>/dev/null | head -1)
    [[ -n "$latest" ]] || { log_error "No hay backups"; exit 1; }
    log_info "Restaurando $latest..."
    cp "$latest" "$GRUB_CONFIG"
    update-grub
    log_ok "Restaurado y GRUB actualizado"
}

# Ayuda
show_help() {
    cat <<EOF
Uso: $SCRIPT_NAME [opciones]

Opciones CLI (sin menú interactivo):
  -h, --help           Muestra esta ayuda
  -l, --list           Lista kernels detectados
  -s, --status         Muestra estado actual
  -r, --restore        Restaura el último backup automático
  -a, --auto KERNEL    Aplica kernel directamente (ej: 6.8.0-147-generic)

Sin opciones: Menú interactivo completo con submenús.

Ejemplos:
  sudo $SCRIPT_NAME                    # Menú interactivo completo
  sudo $SCRIPT_NAME --list             # Solo listar kernels
  sudo $SCRIPT_NAME --auto 6.8.0-147   # Poner kernel 6.8.0-147 por defecto
  sudo $SCRIPT_NAME --restore          # Volver al último backup
EOF
}

# ===== MAIN =====
main() {
    # Comandos CLI que no requieren root
    case "${1:-}" in
        -h|--help)    show_help; exit 0 ;;
        -l|--list)    cli_list_kernels; exit 0 ;;
        -s|--status)  cli_status; exit 0 ;;
    esac

    check_root

    case "${1:-}" in
        -r|--restore) cli_restore_latest; exit 0 ;;
        -a|--auto)    [[ -n "${2:-}" ]] || { log_error "Falta versión"; exit 1; }
                      cli_apply_by_version "$2"; exit 0 ;;
        "")           show_main_menu ;;  # Menú interactivo completo
        *)            log_error "Opción desconocida: $1"; show_help; exit 1 ;;
    esac
}

main "$@"
