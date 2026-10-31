#!/bin/bash
# FreeCAD Stable - descarga, instala, actualiza y ejecuta el AppImage estable.
#
# Autocontenido: el AppImage, el icono, el log y las marcas viven junto a este
# script. Pensado para KDE Plasma (kdialog + qdbus), con reserva para zenity.
#
# Deteccion del fix libdrm: las releases estables 1.1.x empaquetan libdrm
# 2.4.125, que no exporta amdgpu_va_manager_init2 y rompe el driver radeonsi
# en sistemas con Mesa >= 26.2. Antes de arrancar se inspecciona la propia
# AppImage (unsquashfs -ll/-cat, sin extraer nada): si el bundle lleva una
# libdrm antigua y el sistema tiene una nueva, se fuerzan las del sistema con
# LD_PRELOAD; si no, se arranca normal. La decision se cachea junto a la
# AppImage y se recalcula al cambiar de version.
#
# Licencia: MIT (ver LICENSE).

set -u

# ---------------------------------------------------------------------------
# Rutas y constantes
# ---------------------------------------------------------------------------
SCRIPT="$(readlink -f "$0")"
HERE="$(dirname "$SCRIPT")"
ARCH="$(uname -m)"
case "$ARCH" in
    x86_64|amd64)   ARCH="x86_64" ;;
    aarch64|arm64)  ARCH="aarch64" ;;
    *)              ARCH="" ;;
esac
PATTERN="FreeCAD_[0-9]*-Linux-${ARCH}*.AppImage"

API="https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest"
FEED="https://github.com/FreeCAD/FreeCAD/releases.atom"
DL_BASE="https://github.com/FreeCAD/FreeCAD/releases/download"
ICON_URL="https://raw.githubusercontent.com/FreeCAD/FreeCAD/main/src/Gui/Icons/freecad.svg"

LOG="$HERE/.freecad-stable.log"
LOCK="$HERE/.freecad-stable.lock"
VERSION="0.8.6"
SUITE="FreeCAD AutoUpdater Scripts"
NOSHORTCUT="$HERE/.no-stable-shortcut"
NOASSOC="$HERE/.no-stable-assoc"
NODESKTOP="$HERE/.no-stable-desktop"
MIME="application/x-extension-fcstd"
ICON="$HERE/freecad-stable.svg"
DESKTOP="$HOME/.local/share/applications/freecad-stable.desktop"
# Acceso directo en el Escritorio (opt-in); respeta el dir XDG si esta definido.
DESKTOP_DIR="$HOME/Desktop"
if command -v xdg-user-dir >/dev/null 2>&1; then
    _xdg_desk="$(xdg-user-dir DESKTOP 2>/dev/null)"
    [ -n "$_xdg_desk" ] && DESKTOP_DIR="$_xdg_desk"
fi
DESK_LINK="$DESKTOP_DIR/freecad-stable.desktop"
CACHE="$HERE/.freecad-stable.fix"   # "<AppImage>:<0|1>" decision del fix

# ---------------------------------------------------------------------------
# Idioma (es/en automatico)
# ---------------------------------------------------------------------------
LANG_CODE="en"
case "${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}" in
    es*) LANG_CODE="es" ;;
esac

t() {
    case "$LANG_CODE:$1" in
        es:title)              echo "FreeCAD Stable" ;;
        en:title)              echo "FreeCAD Stable" ;;
        es:name)               echo "FreeCAD Stable" ;;
        en:name)               echo "FreeCAD Stable" ;;
        es:generic)            echo "Version estable" ;;
        en:generic)            echo "Stable release" ;;
        es:comment)            echo "Modelador 3D parametrico (AppImage estable)" ;;
        en:comment)            echo "Parametric 3D modeler (stable AppImage)" ;;
        es:checking)           echo "Comprobando actualizaciones..." ;;
        en:checking)           echo "Checking for updates..." ;;
        es:no_local)           echo "Sin version local: descargando la ultima" ;;
        en:no_local)           echo "No local version: downloading the latest" ;;
        es:downloading)        echo "Descargando" ;;
        en:downloading)        echo "Downloading" ;;
        es:verifying)          echo "Verificando integridad..." ;;
        en:verifying)          echo "Verifying integrity..." ;;
        es:updated)            echo "Actualizado a" ;;
        en:updated)            echo "Updated to" ;;
        es:ready)              echo "Listo" ;;
        en:ready)              echo "Done" ;;
        es:err)                echo "Error" ;;
        en:err)                echo "Error" ;;
        es:err_arch)           echo "Arquitectura no soportada:" ;;
        en:err_arch)           echo "Unsupported architecture:" ;;
        es:err_no_curl)        echo "No se encontro 'curl'. Instalalo para poder descargar FreeCAD." ;;
        en:err_no_curl)        echo "'curl' not found. Install it to download FreeCAD." ;;
        es:err_download)       echo "No se pudo descargar; se usara la version actual." ;;
        en:err_download)       echo "Download failed; the current version will be used." ;;
        es:err_checksum)       echo "Checksum incorrecto; no se actualiza." ;;
        en:err_checksum)       echo "Checksum mismatch; not updating." ;;
        es:err_no_local)       echo "No hay AppImage local ni se pudo descargar." ;;
        en:err_no_local)       echo "No local AppImage and download failed." ;;
        es:err_check)          echo "No se pudo comprobar la ultima version (sin red?)." ;;
        en:err_check)          echo "Could not check the latest version (offline?)." ;;
        es:err_nowrite)        echo "La carpeta del script no tiene permiso de escritura:" ;;
        en:err_nowrite)        echo "The script folder is not writable:" ;;
        es:ask_shortcut)       echo "¿Crear un acceso en el menu de inicio para FreeCAD Stable?" ;;
        en:ask_shortcut)       echo "Create a start menu shortcut for FreeCAD Stable?" ;;
        es:shortcut_created)   echo "Acceso creado en el menu de inicio." ;;
        en:shortcut_created)   echo "Start menu shortcut created." ;;
        es:shortcut_removed)   echo "Acceso eliminado del menu de inicio." ;;
        en:shortcut_removed)   echo "Start menu shortcut removed." ;;
        es:ask_desktop)        echo "¿Crear además un acceso directo en el Escritorio?" ;;
        en:ask_desktop)        echo "Also create a Desktop shortcut?" ;;
        es:desktop_created)    echo "Acceso directo creado en el Escritorio." ;;
        en:desktop_created)    echo "Desktop shortcut created." ;;
        es:desktop_removed)    echo "Acceso directo eliminado del Escritorio." ;;
        en:desktop_removed)    echo "Desktop shortcut removed." ;;
        es:ask_assoc)          echo "¿Asociar los archivos .FCStd con FreeCAD Stable para abrirlos con doble clic?" ;;
        en:ask_assoc)          echo "Associate .FCStd files with FreeCAD Stable to open them on double click?" ;;
        es:assoc_set)          echo "Archivos .FCStd asociados con FreeCAD Stable." ;;
        en:assoc_set)          echo ".FCStd files associated with FreeCAD Stable." ;;
        es:assoc_removed)      echo "Asociación de .FCStd eliminada." ;;
        en:assoc_removed)      echo ".FCStd association removed." ;;

        es:uninstalled)        echo "FreeCAD Stable desinstalado." ;;
        en:uninstalled)        echo "FreeCAD Stable uninstalled." ;;
        es:confirm_uninstall)  echo "¿Desinstalar FreeCAD Stable (borrar AppImage, acceso, asociación e icono)?" ;;
        en:confirm_uninstall)  echo "Uninstall FreeCAD Stable (remove AppImage, shortcut, association and icon)?" ;;
        es:check_ok)           echo "Estas en la ultima version:" ;;
        en:check_ok)           echo "You are on the latest version:" ;;
        es:check_new)          echo "Nueva version disponible:" ;;
        en:check_new)          echo "New version available:" ;;
        *)                     echo "$1" ;;
    esac
}

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
log() {
    printf '%s %s\n' "$(date '+%F %T')" "$*" >>"$LOG" 2>/dev/null
    [ "${VERBOSE:-0}" = 1 ] && printf '%s\n' "$*" >&2
    if [ "$(wc -l <"$LOG" 2>/dev/null || echo 0)" -gt 500 ]; then
        tail -n 300 "$LOG" >"$LOG.tmp" 2>/dev/null && mv -f "$LOG.tmp" "$LOG"
    fi
}

notify() {
    command -v notify-send >/dev/null 2>&1 && \
        notify-send -a "$(t title)" "$1" "${2:-}" >/dev/null 2>&1
}

latest_local() {
    find -L "$HERE" -maxdepth 1 -type f -name "$PATTERN" 2>/dev/null | sort -V | tail -1
}

# Imprime dos lineas: <tag> y <url del AppImage> de la ultima release estable.
# Primario: API de GitHub (una llamada). Fallback: feed Atom (solo tags X.Y.Z
# puros, excluye weekly-*) con URL por candidatos.
get_release() {
    local json tag url
    json="$(curl -fsSL --connect-timeout 5 --max-time 20 "$API" 2>/dev/null)"
    if [ -n "$json" ]; then
        tag="$(printf '%s\n' "$json" | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -n1)"
        # Solo tags X.Y.Z puros: si 'latest' devolviera un prerelease
        # (-rc-, weekly-*) se ignora y se usa el feed como respaldo.
        case "$tag" in
            ''|*[!0-9.]*) tag="" ;;
        esac
        url="$(printf '%s\n' "$json" | sed -n 's/.*"browser_download_url": *"\([^"]*\)".*/\1/p' \
               | grep -E "/FreeCAD_[0-9][^/]*-Linux-${ARCH}[^/]*\.AppImage$" | head -n1)"
        if [ -n "$tag" ] && [ -n "$url" ]; then
            printf '%s\n%s\n' "$tag" "$url"
            return 0
        fi
    fi

    local feed t cand
    feed="$(curl -fsSL --connect-timeout 5 --max-time 15 "$FEED" 2>/dev/null)" || return 1
    while read -r t; do
        case "$t" in
            ""|*[!0-9.]*) continue ;;   # weekly-*, rc/alpha/beta...
        esac
        for cand in "FreeCAD_${t}-Linux-${ARCH}-py311.AppImage" \
                    "FreeCAD_${t}-Linux-${ARCH}.AppImage"; do
            if curl -fsIL --connect-timeout 5 --max-time 15 \
                    "${DL_BASE}/${t}/${cand}" >/dev/null 2>&1; then
                printf '%s\n%s\n' "$t" "${DL_BASE}/${t}/${cand}"
                return 0
            fi
        done
    done < <(printf '%s\n' "$feed" | grep -oE 'releases/tag/[^"]+' | sed 's|releases/tag/||')
    return 1
}

ask_yesno() {
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --title "$(t title)" --yesno "$1" 2>/dev/null
    elif command -v zenity >/dev/null 2>&1; then
        zenity --question --title "$(t title)" --text="$1" --width=420 2>/dev/null
    else
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Deteccion del fix libdrm (cascada)
# ---------------------------------------------------------------------------
need_fix=0
preload=""

# El host tiene una libdrm "nueva" si libdrm_amdgpu exporta los simbolos que
# los drivers de Mesa >= 26.2 buscan. Si no, el fix no podria ayudar.
host_libdrm_new() {
    local d l
    for d in /usr/lib64 /usr/lib /usr/lib/x86_64-linux-gnu /usr/lib/aarch64-linux-gnu; do
        [ -e "$d/libdrm_amdgpu.so.1" ] || continue
        if grep -aq -e 'amdgpu_va_manager_init2' -e 'amdgpu_va_manager_query_sw_info' \
                "$d/libdrm_amdgpu.so.1" 2>/dev/null; then
            for l in libdrm.so.2 libdrm_amdgpu.so.1 libdrm_intel.so.1 libdrm_radeon.so.1 libdrm_nouveau.so.2; do
                [ -e "$d/$l" ] && preload="${preload:+$preload:}$d/$l"
            done
            return 0
        fi
    done
    return 1
}

detect_fix() {
    local app="$1" base cached off files f amdgpu verdict=-1 list rc reason
    base="$(basename "$app")"

    # 1) Cache por version (evita inspeccionar en cada arranque)
    cached="$(head -n1 "$CACHE" 2>/dev/null || true)"
    case "$cached" in
        "$base":0)
            need_fix=0
            log "libdrm fix: not needed (cache)"
            return 0 ;;
    esac

    # 2) Host: sin libdrm nueva no hay nada que arreglar
    if ! host_libdrm_new; then
        need_fix=0
        printf '%s:0\n' "$base" >"$CACHE" 2>/dev/null
        log "libdrm fix: not needed (host libdrm not new enough)"
        return 0
    fi

    case "$cached" in
        "$base":1)
            need_fix=1
            log "libdrm fix: enabled (cache)"
            return 0 ;;
    esac

    # 3) Inspeccion del bundle: listado y cat de un .so, sin extraer nada.
    #    Solo cuentan las libdrm activas de usr/lib{,64} (los weeklies guardan
    #    copias de conda en usr/__clobbers__/ que no se cargan), y solo los
    #    modulos libdrm.so*/libdrm_<x>.so* (no los plugins tipo
    #    libdrm-egl-server.so ni los .pc).
    if command -v unsquashfs >/dev/null 2>&1; then
        off="$("$app" --appimage-offset 2>/dev/null)"
        case "$off" in
            ''|*[!0-9]*) off="" ;;
        esac
        if [ -n "$off" ]; then
            # Si el listado falla (versiones de squashfs-tools sin -o) se
            # mantiene verdict=-1 y se aplica el fix por seguridad.
            list="$(unsquashfs -ll -o "$off" -no-progress "$app" 2>/dev/null)"
            rc=$?
            if [ "$rc" -eq 0 ]; then
                files="$(printf '%s\n' "$list" \
                    | awk '$1 ~ /^-/ && $6 !~ /__clobbers__/ && $6 ~ /\/usr\/lib(64)?\// && \
                           ($6 ~ /\/libdrm\.so/ || $6 ~ /\/libdrm_[a-z]+\.so/) {print $6}')"
                if [ -z "$files" ]; then
                    verdict=0    # no empaqueta libdrm
                else
                    amdgpu=""
                    for f in $files; do
                        case "$f" in
                            */libdrm_amdgpu.so*) amdgpu="$f"; break ;;
                        esac
                    done
                    if [ -z "$amdgpu" ]; then
                        verdict=1    # hay libdrm pero no el amdgpu: conservador
                    elif unsquashfs -o "$off" -cat "$amdgpu" "$app" 2>/dev/null \
                            | grep -aq -e 'amdgpu_va_manager_init2' \
                                       -e 'amdgpu_va_manager_query_sw_info'; then
                        verdict=0    # el bundle ya es nuevo
                    else
                        verdict=1    # bundle antiguo y host nuevo -> fix
                    fi
                fi
            fi
        fi
    fi

    if [ "$verdict" -lt 0 ]; then
        # Sin inspeccion posible: se aplica el fix (el preload es inofensivo)
        verdict=1
        reason="inspection unavailable"
    else
        reason="bundle inspection"
    fi

    need_fix="$verdict"
    printf '%s:%s\n' "$base" "$need_fix" >"$CACHE" 2>/dev/null
    if [ "$need_fix" = 1 ]; then
        log "libdrm fix: enabled ($reason, $base)"
    else
        log "libdrm fix: not needed ($reason, $base)"
    fi
}

# ---------------------------------------------------------------------------
# Ventana de estado (kdialog via DBus; reserva: zenity)
# ---------------------------------------------------------------------------
DLG_KIND=""; DLG_PID=""; DLG_SVC=""; DLG_PATH=""; DLG_FD=""

dlg_start() {  # $1 = texto, $2 = busy|progress
    if command -v kdialog >/dev/null 2>&1 && command -v qdbus >/dev/null 2>&1; then
        DLG_KIND=kdialog
        local f="/tmp/.fcstable-dlg.$$"
        rm -f "$f"
        kdialog --title "$(t title)" --progressbar "$1" 100 >"$f" 2>/dev/null &
        DLG_PID=$!
        local i=0
        while [ $i -lt 30 ] && [ ! -s "$f" ]; do sleep 0.1; i=$((i+1)); done
        read -r DLG_SVC DLG_PATH <"$f"
        rm -f "$f"
        if [ -z "$DLG_SVC" ]; then DLG_KIND=""; return 0; fi
        if [ "$2" = busy ]; then
            qdbus "$DLG_SVC" "$DLG_PATH" org.freedesktop.DBus.Properties.Set \
                org.kde.kdialog.ProgressDialog maximum 0 >/dev/null 2>&1
        else
            dlg_set 0 "$1"
        fi
    elif command -v zenity >/dev/null 2>&1; then
        DLG_KIND=zenity
        local fifo="/tmp/.fcstable-fifo.$$"
        rm -f "$fifo"; mkfifo "$fifo"
        zenity --progress --title="$(t title)" --text="$1" --percentage=0 \
            --no-cancel --auto-close <"$fifo" 2>/dev/null &
        DLG_PID=$!
        exec {DLG_FD}>"$fifo"
        rm -f "$fifo"
    fi
}

dlg_set() {  # $1 = porcentaje, $2 = texto
    case "$DLG_KIND" in
        kdialog)
            qdbus "$DLG_SVC" "$DLG_PATH" org.freedesktop.DBus.Properties.Set \
                org.kde.kdialog.ProgressDialog maximum 100 >/dev/null 2>&1
            qdbus "$DLG_SVC" "$DLG_PATH" org.freedesktop.DBus.Properties.Set \
                org.kde.kdialog.ProgressDialog value "$1" >/dev/null 2>&1
            [ -n "$2" ] && qdbus "$DLG_SVC" "$DLG_PATH" \
                org.kde.kdialog.ProgressDialog.setLabelText "$2" >/dev/null 2>&1
            ;;
        zenity)
            printf '%s\n# %s\n' "$1" "$2" 2>/dev/null 1>&"$DLG_FD"
            ;;
    esac
}

dlg_close() {
    case "$DLG_KIND" in
        kdialog) qdbus "$DLG_SVC" "$DLG_PATH" org.kde.kdialog.ProgressDialog.close >/dev/null 2>&1 ;;
        zenity)  [ -n "$DLG_FD" ] && exec {DLG_FD}>&- ;;
    esac
    [ -n "$DLG_PID" ] && wait "$DLG_PID" 2>/dev/null
    DLG_KIND=""; DLG_PID=""; DLG_SVC=""; DLG_PATH=""; DLG_FD=""
}

# ---------------------------------------------------------------------------
# Icono y acceso al menu
# ---------------------------------------------------------------------------
get_icon() {
    [ -s "$ICON" ] && return 0
    local app; app="$(latest_local)"
    if [ -n "$app" ]; then
        local tmpd="/tmp/.fcstable-icon.$$"
        rm -rf "$tmpd"; mkdir -p "$tmpd"
        if ( cd "$tmpd" && "$app" --appimage-extract 'org.freecad.FreeCAD.svg' >/dev/null 2>&1 ) \
                && [ -s "$tmpd/squashfs-root/org.freecad.FreeCAD.svg" ]; then
            mv -f "$tmpd/squashfs-root/org.freecad.FreeCAD.svg" "$ICON" 2>/dev/null
            rm -rf "$tmpd"
            [ -s "$ICON" ] && return 0
        fi
        rm -rf "$tmpd"
    fi
    if curl -fsSL --connect-timeout 5 --max-time 20 "$ICON_URL" -o "$ICON" 2>/dev/null \
            && [ -s "$ICON" ]; then
        return 0
    fi
    rm -f "$ICON"
    return 1
}

write_desktop() {
    get_icon
    local icon_field="freecad"
    [ -s "$ICON" ] && icon_field="$ICON"
    local mime_line=""
    if [ "${FORCE_MIME:-0}" = 1 ] || assoc_active 2>/dev/null; then
        mime_line="MimeType=$MIME;"
    fi
    mkdir -p "$(dirname "$DESKTOP")" 2>/dev/null
    cat > "$DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Name=$(t name)
GenericName=$(t generic)
Comment=$(t comment)
Exec="$SCRIPT" %F
Icon=$icon_field
Terminal=false
Categories=Engineering;Science;Graphics;3DGraphics;CAD;
$mime_line
StartupNotify=true
EOF
    chmod +x "$SCRIPT" 2>/dev/null
    command -v update-desktop-database >/dev/null 2>&1 && \
        update-desktop-database "$(dirname "$DESKTOP")" >/dev/null 2>&1
}

create_shortcut() {
    rm -f "$NOSHORTCUT"
    write_desktop
    log "shortcut created"
}

remove_shortcut() {
    rm -f "$DESKTOP"
    : > "$NOSHORTCUT" 2>/dev/null
    command -v update-desktop-database >/dev/null 2>&1 && \
        update-desktop-database "$(dirname "$DESKTOP")" >/dev/null 2>&1
    log "shortcut removed"
}

# La entrada apunta al actualizador: si existe con un Exec viejo (carpeta
# movida) se reescribe en vez de darla por buena.
shortcut_current() { [ -f "$DESKTOP" ] && grep -qsF "Exec=\"$SCRIPT\"" "$DESKTOP"; }

maybe_create_shortcut() {
    if [ -f "$DESKTOP" ]; then
        shortcut_current || { create_shortcut; return 0; }
        return 0
    fi
    [ -f "$NOSHORTCUT" ] && return 0
    if [ "$ASSUME_YES" = 1 ] || ask_yesno "$(t ask_shortcut)"; then
        create_shortcut
        notify "$(t shortcut_created)"
    else
        : > "$NOSHORTCUT" 2>/dev/null
    fi
}

# Acceso directo en el Escritorio: copia del .desktop (sin MimeType; la
# asociacion sigue en la entrada del menu).
write_desktop_link() {
    get_icon
    local icon_field="freecad"
    [ -s "$ICON" ] && icon_field="$ICON"
    mkdir -p "$DESKTOP_DIR" 2>/dev/null || return 1
    cat > "$DESK_LINK" <<EOF
[Desktop Entry]
Type=Application
Name=$(t name)
GenericName=$(t generic)
Comment=$(t comment)
Exec="$SCRIPT" %F
Icon=$icon_field
Terminal=false
Categories=Engineering;Science;Graphics;3DGraphics;CAD;
StartupNotify=true
EOF
    chmod +x "$DESK_LINK" 2>/dev/null
    # GNOME/Nautilus exige marcar el .desktop como confiable para poder lanzarlo
    command -v gio >/dev/null 2>&1 && gio set "$DESK_LINK" metadata::trusted true 2>/dev/null
    return 0
}

desktop_link_current() { [ -f "$DESK_LINK" ] && grep -qsF "Exec=\"$SCRIPT\"" "$DESK_LINK"; }

create_desktop_shortcut() {
    rm -f "$NODESKTOP" 2>/dev/null
    write_desktop_link
    log "desktop shortcut created"
}

remove_desktop_shortcut() {
    rm -f "$DESK_LINK" 2>/dev/null
    : > "$NODESKTOP" 2>/dev/null
    log "desktop shortcut removed"
}

maybe_create_desktop_shortcut() {
    if [ -f "$DESK_LINK" ]; then
        desktop_link_current || { write_desktop_link; return 0; }
        return 0
    fi
    [ -f "$NODESKTOP" ] && return 0
    if [ "$ASSUME_YES" = 1 ] || ask_yesno "$(t ask_desktop)"; then
        create_desktop_shortcut
        notify "$(t desktop_created)"
    else
        : > "$NODESKTOP" 2>/dev/null
    fi
}

assoc_active() {
    [ -f "$DESKTOP" ] || return 1
    grep -qs '^MimeType=' "$DESKTOP" 2>/dev/null
}

unmime_default() {
    local id esc map
    id="$(basename "$DESKTOP")"
    esc="$(printf '%s' "$id" | sed 's/\./\\./g')"
    map="$HOME/.config/mimeapps.list"
    [ -f "$map" ] || return 0
    sed -i -e "s/${esc};//g; s/;${esc}/;/g; s/=${esc}$/=/; /^[^=]*=$/d" "$map" 2>/dev/null
}

set_assoc() {
    rm -f "$NOASSOC" 2>/dev/null
    FORCE_MIME=1 write_desktop
    if command -v xdg-mime >/dev/null 2>&1; then
        xdg-mime default "$(basename "$DESKTOP")" "$MIME" 2>/dev/null
    elif command -v gio >/dev/null 2>&1; then
        gio mime "$MIME" "$(basename "$DESKTOP")" 2>/dev/null
    fi
    log "assoc set"
}

remove_assoc() {
    if [ -f "$DESKTOP" ]; then
        grep -v '^MimeType=' "$DESKTOP" >"$DESKTOP.tmp" 2>/dev/null && \
            mv "$DESKTOP.tmp" "$DESKTOP" 2>/dev/null
        command -v update-desktop-database >/dev/null 2>&1 && \
            update-desktop-database "$(dirname "$DESKTOP")" >/dev/null 2>&1
    fi
    unmime_default
    : > "$NOASSOC" 2>/dev/null
    log "assoc removed"
}

maybe_assoc() {
    assoc_active && return 0
    [ -f "$NOASSOC" ] && return 0
    if [ "$ASSUME_YES" = 1 ] || ask_yesno "$(t ask_assoc)"; then
        set_assoc
        notify "$(t assoc_set)"
    else
        : > "$NOASSOC" 2>/dev/null
    fi
}

# ---------------------------------------------------------------------------
# Backup de configuracion
# ---------------------------------------------------------------------------
backup_config() {
    local src="$HOME/.config/FreeCAD"
    [ -d "$src" ] || return 0
    local dir="$HERE/.cfg-backup-stable"
    local recent
    recent="$(find "$dir" -maxdepth 1 -name '*.tar.gz' -newermt '-10 minutes' 2>/dev/null | head -1)"
    [ -n "$recent" ] && return 0
    mkdir -p "$dir" 2>/dev/null || return 0
    tar -czf "$dir/freecad-cfg-$(date +%Y%m%d-%H%M%S).tar.gz" \
        -C "$HOME/.config" FreeCAD 2>/dev/null || return 0
    find "$dir" -maxdepth 1 -name '*.tar.gz' -printf '%T@\t%p\n' 2>/dev/null \
        | sort -t$'\t' -k1,1rn | awk 'NR>3{sub(/^[^\t]+\t/,""); print}' \
        | xargs -r rm -f --
    log "config backup saved"
}

# ---------------------------------------------------------------------------
# Actualizacion
# ---------------------------------------------------------------------------
update_stable() {
    exec 9>"$LOCK" || return 1
    flock -n 9 || { log "another update in progress"; return 1; }

    local res="/tmp/.fcstable-check.$$"
    rm -f "$res"
    ( get_release >"$res" 2>/dev/null || printf 'NONE\n' >"$res" ) &
    local cpid=$!

    local i=0
    while [ $i -lt 15 ] && [ ! -s "$res" ]; do sleep 0.1; i=$((i+1)); done

    local shown=0
    if [ ! -s "$res" ]; then
        dlg_start "$(t checking)" busy
        shown=1
        wait "$cpid"
    else
        wait "$cpid"
    fi

    local tag url
    tag="$(sed -n 1p "$res" 2>/dev/null)"
    url="$(sed -n 2p "$res" 2>/dev/null)"
    rm -f "$res"

    if [ -z "$tag" ] || [ "$tag" = NONE ] || [ -z "$url" ]; then
        log "check failed (offline?)"
        [ "$shown" = 1 ] && dlg_close
        return 1
    fi

    local current; current="$(latest_local)"
    if [ -n "$current" ] && [[ "$(basename "$current")" == *"${tag}-Linux-${ARCH}"* ]]; then
        log "up to date ($tag)"
        [ "$shown" = 1 ] && dlg_close
        return 0
    fi

    local prefix; prefix="$(t downloading)"
    if [ -z "$current" ]; then
        prefix="$(t no_local)"
        log "no local version; downloading $tag"
        notify "$(t no_local)" "$tag"
    fi

    local asset; asset="$(basename "$url")"
    local tmp="$HERE/.${asset}.part"
    local total
    total="$(curl -fsIL --connect-timeout 10 --max-time 30 "$url" 2>/dev/null \
             | awk 'BEGIN{IGNORECASE=1}/^content-length:/{v=$2} END{print v+0}')"

    if [ "$shown" = 0 ]; then
        dlg_start "${prefix} ${tag}..." progress
        shown=1
    else
        dlg_set 0 "${prefix} ${tag}..."
    fi

    rm -f "$tmp"
    curl -fL --connect-timeout 10 --retry 2 -o "$tmp" "$url" 2>/dev/null &
    local dlpid=$!
    local cur pct
    while kill -0 "$dlpid" 2>/dev/null; do
        cur=$(stat -c%s "$tmp" 2>/dev/null || echo 0)
        if [ "${total:-0}" -gt 0 ]; then
            pct=$(( cur*100/total )); [ "$pct" -gt 100 ] && pct=100
            dlg_set "$pct" "${prefix} ${tag}... $((cur/1048576))/$((total/1048576)) MiB"
        else
            dlg_set 0 "${prefix} ${tag}... $((cur/1048576)) MiB"
        fi
        sleep 0.5
    done
    if ! wait "$dlpid" || [ ! -s "$tmp" ]; then
        rm -f "$tmp"
        log "download failed: $tag"
        [ "$shown" = 1 ] && dlg_close
        notify "$(t err)" "$(t err_download)"
        return 1
    fi

    dlg_set 100 "$(t verifying)"
    local exp act
    exp="$(curl -fsSL --connect-timeout 5 --max-time 15 "${url}-SHA256.txt" 2>/dev/null | awk '{print $1}')"
    act="$(sha256sum "$tmp" 2>/dev/null | awk '{print $1}')"
    # Fail-closed: sin sidecar no hay verificación posible y NO se instala
    # (antes se instalaba sin verificar). Sin red, la versión local sigue
    # usándose: este punto solo se alcanza tras descargar algo nuevo.
    if [ -z "$exp" ]; then
        rm -f "$tmp"
        log "sha256 sidecar unavailable: $tag (not updating)"
        [ "$shown" = 1 ] && dlg_close
        notify "$(t err)" "$(t err_checksum)"
        return 1
    fi
    if [ -z "$act" ] || [ "$exp" != "$act" ]; then
        rm -f "$tmp"
        log "sha256 mismatch: $tag"
        [ "$shown" = 1 ] && dlg_close
        notify "$(t err)" "$(t err_checksum)"
        return 1
    fi

    chmod +x "$tmp"
    mv -f "$tmp" "$HERE/$asset"
    find "$HERE" -maxdepth 1 -name "$PATTERN" ! -name "$asset" -delete 2>/dev/null
    rm -f "$CACHE"    # version nueva -> decision de fix nueva
    [ "$shown" = 1 ] && dlg_close
    log "updated to $tag"
    notify "$(t updated) $tag" "$(t ready)"
    return 0
}

# ---------------------------------------------------------------------------
# Acciones
# ---------------------------------------------------------------------------
do_check() {
    local rel tag
    rel="$(get_release)"
    tag="$(printf '%s' "$rel" | sed -n 1p)"
    if [ -z "$tag" ]; then
        notify "$(t err)" "$(t err_check)"
        t err_check >&2
        return 1
    fi
    local current; current="$(latest_local)"
    if [ -n "$current" ] && [[ "$(basename "$current")" == *"${tag}-Linux-${ARCH}"* ]]; then
        notify "$(t check_ok)" "$tag"
        echo "$(t check_ok) $tag"
    else
        notify "$(t check_new)" "$tag"
        echo "$(t check_new) $tag"
    fi
    return 0
}

do_uninstall() {
    if [ "$ASSUME_YES" != 1 ]; then
        ask_yesno "$(t confirm_uninstall)" || return 0
    fi
    find "$HERE" -maxdepth 1 -name "$PATTERN" -delete 2>/dev/null
    rm -f "$HERE"/.FreeCAD_[0-9]*.part
    rm -f "$DESKTOP" "$DESK_LINK" "$ICON" "$LOG" "$LOCK" "$NOSHORTCUT" "$NOASSOC" "$NODESKTOP" "$CACHE"
    unmime_default
    command -v update-desktop-database >/dev/null 2>&1 && \
        update-desktop-database "$(dirname "$DESKTOP")" >/dev/null 2>&1
    notify "$(t uninstalled)"
    t uninstalled
}

show_help() {
    if [ "$LANG_CODE" = es ]; then
        cat <<EOF
$SUITE v$VERSION
$(t name) - AppImage estable: descarga, instala, actualiza y ejecuta.

Uso: $(basename "$SCRIPT") [opciones] [--] [argumentos de FreeCAD]

Opciones:
  --no-update         Arranca sin comprobar actualizaciones.
  --check             Solo comprueba si hay una version nueva (no descarga).
  --reinstall         Borra la version local y descarga de nuevo la ultima.
  --create-shortcut   Crea el acceso en el menu de inicio.
  --remove-shortcut   Elimina el acceso del menu de inicio.
  --create-desktop    Crea el acceso directo en el Escritorio.
  --remove-desktop    Elimina el acceso directo del Escritorio.
  --associate         Asociar los archivos .FCStd (abrir con doble clic).
  --remove-assoc      Quitar la asociación de .FCStd.
  --uninstall         Desinstala (AppImage, acceso, icono, log).
  -y, --yes           No preguntar (asumir si).
  -v, --verbose       Mostrar informacion adicional.
  -h, --help          Muestra esta ayuda.

Todo lo que va despues de '--' se pasa a FreeCAD, p. ej.:
  $(basename "$SCRIPT") -- --help
  $(basename "$SCRIPT") -- mi_archivo.FCStd
EOF
    else
        cat <<EOF
$SUITE v$VERSION
$(t name) - stable AppImage: download, install, update and run.

Usage: $(basename "$SCRIPT") [options] [--] [FreeCAD arguments]

Options:
  --no-update         Run without checking for updates.
  --check             Only check for a new version (no download).
  --reinstall         Remove the local version and download the latest again.
  --create-shortcut   Create the start menu shortcut.
  --remove-shortcut   Remove the start menu shortcut.
  --create-desktop    Create the Desktop shortcut.
  --remove-desktop    Remove the Desktop shortcut.
  --associate         Associate .FCStd files (open on double click).
  --remove-assoc      Remove the .FCStd association.
  --uninstall         Uninstall (AppImage, shortcut, icon, log).
  -y, --yes           Do not prompt (assume yes).
  -v, --verbose       Show extra information.
  -h, --help          Show this help.

Everything after '--' is passed to FreeCAD, e.g.:
  $(basename "$SCRIPT") -- --help
  $(basename "$SCRIPT") -- my_file.FCStd
EOF
    fi
}

# ---------------------------------------------------------------------------
# Argumentos
# ---------------------------------------------------------------------------
UPDATE=1
ACTION=""
ASSUME_YES=0
VERBOSE=0
FC_ARGS=()

while [ $# -gt 0 ]; do
    case "$1" in
        --)               shift; FC_ARGS=("$@"); break ;;
        --no-update)      UPDATE=0; shift ;;
        --check)          ACTION=check; shift ;;
        --reinstall)      ACTION=reinstall; shift ;;
        --create-shortcut) ACTION=create-shortcut; shift ;;
        --remove-shortcut) ACTION=remove-shortcut; shift ;;
        --create-desktop) ACTION=create-desktop; shift ;;
        --remove-desktop) ACTION=remove-desktop; shift ;;
        --associate)      ACTION=associate; shift ;;
        --remove-assoc)   ACTION=remove-assoc; shift ;;
        --uninstall)      ACTION=uninstall; shift ;;
        -y|--yes)         ASSUME_YES=1; shift ;;
        -v|--verbose)     VERBOSE=1; shift ;;
        -h|--help)        ACTION=help; shift ;;
        *)                FC_ARGS+=("$1"); shift ;;
    esac
done

# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------
if [ -z "$ARCH" ]; then
    notify "$(t err)" "$(t err_arch) $(uname -m)"
    echo "$(t err_arch) $(uname -m)" >&2
    exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
    notify "$(t err)" "$(t err_no_curl)"
    t err_no_curl >&2
    exit 1
fi

case "$ACTION" in
    help)  show_help; exit 0 ;;
    check) do_check; exit $? ;;
esac

if [ ! -w "$HERE" ]; then
    notify "$(t err)" "$(t err_nowrite) $HERE"
    echo "$(t err_nowrite) $HERE" >&2
    exit 1
fi

case "$ACTION" in
    create-shortcut)  create_shortcut; notify "$(t shortcut_created)"; exit 0 ;;
    remove-shortcut)  remove_shortcut; notify "$(t shortcut_removed)"; exit 0 ;;
    create-desktop)   create_desktop_shortcut; notify "$(t desktop_created)"; exit 0 ;;
    remove-desktop)   remove_desktop_shortcut; notify "$(t desktop_removed)"; exit 0 ;;
    associate)      set_assoc; notify "$(t assoc_set)"; exit 0 ;;
    remove-assoc)   remove_assoc; notify "$(t assoc_removed)"; exit 0 ;;
    uninstall)        do_uninstall; exit 0 ;;
esac

[ "$ACTION" = reinstall ] && { find "$HERE" -maxdepth 1 -name "$PATTERN" -delete 2>/dev/null; rm -f "$CACHE"; }

if [ "$UPDATE" = 1 ]; then
    update_stable
fi
exec 9>&- || true

CURRENT="$(latest_local)"
if [ -z "$CURRENT" ]; then
    notify "$(t err)" "$(t err_no_local)"
    t err_no_local >&2
    exit 1
fi

maybe_create_shortcut
maybe_create_desktop_shortcut
maybe_assoc

backup_config

detect_fix "$CURRENT"

if [ "$need_fix" = 1 ] && [ -n "$preload" ]; then
    exec env LD_PRELOAD="$preload${LD_PRELOAD:+:$LD_PRELOAD}" "$CURRENT" ${FC_ARGS[@]+"${FC_ARGS[@]}"}
else
    exec "$CURRENT" ${FC_ARGS[@]+"${FC_ARGS[@]}"}
fi
