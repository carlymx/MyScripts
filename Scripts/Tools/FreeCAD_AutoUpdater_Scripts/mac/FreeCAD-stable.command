#!/bin/bash
# FreeCAD Stable (macOS) - descarga, instala, actualiza y ejecuta el bundle dmg.
#
# Autocontenido: el marcador de version, el log y las marcas viven junto a
# este script; la .app vive en /Aplicaciones (o ~/Aplicaciones sin admin).
# Equivalente macOS de linux/FreeCAD-stable.sh (misma CLI y semantica).
# Compatible con el bash 3.2 de macOS: sin sustitucion de procesos, sin
# sort -V, sin find -printf, sin readlink -f (solo herramientas BSD+curl).
# FC_UNAME_M/FC_TEST son ganchos para pruebas (ver arnes en PORTABILIDAD.md).
#
# Licencia: MIT (ver ../LICENSE).

set -u

# ---------------------------------------------------------------------------
# Rutas y constantes
# ---------------------------------------------------------------------------
SCRIPT="${BASH_SOURCE[0]:-$0}"
case "$SCRIPT" in
    /*) ;;
    *)  SCRIPT="$PWD/$SCRIPT" ;;
esac
# Resuelve un nivel de enlace (suficiente para .command/Finder).
if [ -L "$SCRIPT" ]; then
    link="$(readlink "$SCRIPT")"
    case "$link" in
        /*) SCRIPT="$link" ;;
        *)  SCRIPT="$(dirname "$SCRIPT")/$link" ;;
    esac
fi
HERE="$(dirname "$SCRIPT")"
ARCH="$(uname -m)"
if [ -n "${FC_UNAME_M:-}" ]; then
    ARCH="$FC_UNAME_M"
fi
case "$ARCH" in
    x86_64|amd64) ARCH="x86_64" ;;
    arm64|aarch64) ARCH="arm64" ;;
    *)            ARCH="" ;;
esac
APP_NAME="FreeCAD Stable.app"

API="https://api.github.com/repos/FreeCAD/FreeCAD/releases/latest"
FEED="https://github.com/FreeCAD/FreeCAD/releases.atom"
DL_BASE="https://github.com/FreeCAD/FreeCAD/releases/download"

LOG="$HERE/.freecad-stable.log"
LOCKDIR="$HERE/.freecad-stable.lock"
VERSION="0.8.6"
SUITE="FreeCAD AutoUpdater Scripts"
NOSHORTCUT="$HERE/.no-stable-shortcut"
NOASSOC="$HERE/.no-stable-assoc"
LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
VERSION_FILE="$HERE/.freecad-stable.version"
BACKUP_DIR="$HERE/.cfg-backup-stable"
CFG_SRC="$HOME/Library/Preferences/FreeCAD"

# ---------------------------------------------------------------------------
# macOS antiguo (Big Sur 11 y anteriores): no puede ejecutar FreeCAD 1.1+
# (Qt 6.8 exige macOS 12+). En esos equipos se instala la ultima compatible.
# FC_SW_VERS es un gancho de prueba (ver arnes en docs/PORTABILIDAD.md).
# ---------------------------------------------------------------------------
LEGACY_TAG="1.0.2"
LEGACY_MAC=0
macos_major() {
    local v
    if [ -n "${FC_SW_VERS:-}" ]; then v="$FC_SW_VERS"; else v="$(sw_vers -productVersion 2>/dev/null)"; fi
    v="${v%%.*}"
    case "$v" in ''|*[!0-9]*) printf '%s' "" ;; *) printf '%s' "$v" ;; esac
}
MACOS_MAJ="$(macos_major)"
if [ -n "$MACOS_MAJ" ] && [ "$MACOS_MAJ" -lt 12 ]; then
    LEGACY_MAC=1
fi
legacy_url() {
    printf '%s/%s/FreeCAD_%s-conda-macOS-%s-py311.dmg' \
        "$DL_BASE" "$LEGACY_TAG" "$LEGACY_TAG" "$ARCH"
}

# ---------------------------------------------------------------------------
# Idioma (es/en automatico)
# ---------------------------------------------------------------------------
LANG_CODE="en"
case "${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}" in
    es*) LANG_CODE="es" ;;
    *)
        if command -v defaults >/dev/null 2>&1; then
            case "$(defaults read -g AppleLanguages 2>/dev/null | grep -oE '"[a-z]{2}(-|_)[A-Z]{2}"' | head -n1)" in
                '"es'*|'es'*) LANG_CODE="es" ;;
            esac
        fi
        ;;
esac

t() {
    case "$LANG_CODE:$1" in
        es:title)              echo "FreeCAD Stable" ;;
        en:title)              echo "FreeCAD Stable" ;;
        es:name)               echo "FreeCAD Stable" ;;
        en:name)               echo "FreeCAD Stable" ;;
        es:generic)            echo "Version estable" ;;
        en:generic)            echo "Stable release" ;;
        es:comment)            echo "Modelador 3D parametrico (dmg estable)" ;;
        en:comment)            echo "Parametric 3D modeler (stable dmg)" ;;
        es:checking)           echo "Comprobando actualizaciones..." ;;
        en:checking)           echo "Checking for updates..." ;;
        es:no_local)           echo "Sin version local: descargando la ultima" ;;
        en:no_local)           echo "No local version: downloading the latest" ;;
        es:downloading)        echo "Descargando" ;;
        en:downloading)        echo "Downloading" ;;
        es:verifying)          echo "Verificando integridad..." ;;
        en:verifying)          echo "Verifying integrity..." ;;
        es:installing)         echo "Instalando..." ;;
        en:installing)         echo "Installing..." ;;
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
        es:err_no_local)       echo "No hay version local ni se pudo descargar." ;;
        en:err_no_local)       echo "No local bundle and download failed." ;;
        es:err_check)          echo "No se pudo comprobar la ultima version (sin red?)." ;;
        en:err_check)          echo "Could not check the latest version (offline?)." ;;
        es:err_nowrite)        echo "La carpeta del script no tiene permiso de escritura:" ;;
        en:err_nowrite)        echo "The script folder is not writable:" ;;
        es:err_mount)          echo "No se pudo montar la imagen descargada." ;;
        en:err_mount)          echo "Could not mount the downloaded image." ;;
        es:err_noapp)          echo "No se encontro FreeCAD.app en la imagen." ;;
        en:err_noapp)          echo "FreeCAD.app not found in the image." ;;
        es:err_no_hdiutil)     echo "No se encontro 'hdiutil'. Reinstala macOS." ;;
        en:err_no_hdiutil)     echo "'hdiutil' not found. Reinstall macOS." ;;
        es:ask_shortcut)       echo "Crear un acceso en el Escritorio para FreeCAD Stable?" ;;
        en:ask_shortcut)       echo "Create a Desktop shortcut for FreeCAD Stable?" ;;
        es:shortcut_created)   echo "Acceso creado en el Escritorio." ;;
        en:shortcut_created)   echo "Desktop shortcut created." ;;
        es:shortcut_removed)   echo "Acceso eliminado del Escritorio." ;;
        en:shortcut_removed)   echo "Desktop shortcut removed." ;;
        es:ask_assoc)          echo "¿Asociar los archivos .FCStd con FreeCAD Stable?" ;;
        en:ask_assoc)          echo "Associate .FCStd files with FreeCAD Stable?" ;;
        es:assoc_set)          echo "Archivos .FCStd asociados con FreeCAD Stable." ;;
        en:assoc_set)          echo ".FCStd files associated with FreeCAD Stable." ;;
        es:assoc_openwith)     echo "Sin 'duti': FreeCAD Stable sale en Abrir con (no como predeterminado)." ;;
        en:assoc_openwith)     echo "No 'duti': FreeCAD Stable appears in Open With (not as default)." ;;
        es:assoc_removed)      echo "Asociación de .FCStd eliminada." ;;
        en:assoc_removed)      echo ".FCStd association removed." ;;
        es:uninstalled)        echo "FreeCAD Stable desinstalado." ;;
        en:uninstalled)        echo "FreeCAD Stable uninstalled." ;;
        es:confirm_uninstall)  echo "Desinstalar FreeCAD Stable (borrar app, acceso, asociación y marcas)?" ;;
        en:confirm_uninstall)  echo "Uninstall FreeCAD Stable (remove app, shortcut, association and marks)?" ;;
        es:check_ok)           echo "Estas en la ultima version:" ;;
        en:check_ok)           echo "You are on the latest version:" ;;
        es:check_new)          echo "Nueva version disponible:" ;;
        en:check_new)          echo "New version available:" ;;
        es:legacy)             echo "Tu macOS no puede ejecutar FreeCAD 1.1+; se instala la ultima compatible (1.0.2)." ;;
        en:legacy)             echo "Your macOS cannot run FreeCAD 1.1+; installing the last compatible version (1.0.2)." ;;
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

osascript_escape() {
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

notify() {
    command -v osascript >/dev/null 2>&1 || return 0
    local body sub
    body="$(osascript_escape "$1")"
    sub=""
    if [ -n "${2:-}" ]; then
        sub=" subtitle \"$(osascript_escape "$2")\""
    fi
    osascript -e "display notification \"$body\" with title \"$(osascript_escape "$(t title)")\"$sub" \
        >/dev/null 2>&1 || true
}

# Ruta de la .app instalada (prefiere /Aplicaciones, reserva ~/Aplicaciones).
app_path() {
    if [ -d "/Applications/$APP_NAME" ]; then
        printf '%s\n' "/Applications/$APP_NAME"
    else
        printf '%s\n' "$HOME/Applications/$APP_NAME"
    fi
}

# Directorio de destino para instalar (escribible, sin admin si hace falta).
app_dest_dir() {
    if [ -w "/Applications" ]; then
        printf '%s\n' "/Applications"
    else
        mkdir -p "$HOME/Applications" 2>/dev/null
        printf '%s\n' "$HOME/Applications"
    fi
}

# Imprime el tag instalado o nada (marcador + .app presente).
latest_local() {
    [ -f "$VERSION_FILE" ] || return 0
    [ -d "$(app_path)" ] || return 0
    head -n1 "$VERSION_FILE" 2>/dev/null
}

# Imprime dos lineas: <tag> y <url del dmg> de la ultima release estable.
# Primario: API de GitHub (una llamada). Fallback: feed Atom con candidatos.
get_release() {
    # macOS antiguo: version fija compatible (la ultima no arrancaria).
    if [ "$LEGACY_MAC" = 1 ]; then
        printf '%s\n%s\n' "$LEGACY_TAG" "$(legacy_url)"
        return 0
    fi
    local json tag url
    json="$(curl -fsSL --connect-timeout 5 --max-time 20 "$API" 2>/dev/null)"
    if [ -n "$json" ]; then
        tag="$(printf '%s\n' "$json" | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -n1)"
        case "$tag" in
            ''|*[!0-9.]*) tag="" ;;
        esac
        url="$(printf '%s\n' "$json" | sed -n 's/.*"browser_download_url": *"\([^"]*\)".*/\1/p' \
               | grep -E "/FreeCAD_[0-9][^/]*-macOS-${ARCH}[^/]*\.dmg$" | head -n1)"
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
        for cand in "FreeCAD_${t}-macOS-${ARCH}-py311.dmg" \
                    "FreeCAD_${t}-macOS-${ARCH}.dmg"; do
            if curl -fsIL --connect-timeout 5 --max-time 15 \
                    "${DL_BASE}/${t}/${cand}" >/dev/null 2>&1; then
                printf '%s\n%s\n' "$t" "${DL_BASE}/${t}/${cand}"
                return 0
            fi
        done
    done <<EOF
$(printf '%s\n' "$feed" | grep -oE 'releases/tag/[^"]+' | sed 's|releases/tag/||')
EOF
    return 1
}

# Pregunta si/no con AppleScript; sin GUI se asume "no" (como en Linux).
ask_yesno() {
    command -v osascript >/dev/null 2>&1 || return 1
    local ans
    # Un solo -e: osascript une varios -e con saltos de linea y AppleScript
    # corta el 'display dialog' (el 'with title' se lee como 'with timeout').
    ans="$(osascript -e "display dialog \"$(osascript_escape "$1")\" with title \"$(osascript_escape "$(t title)")\" buttons {\"No\", \"Si\"} default button \"Si\"" 2>&1)" || { AS_RAW="$ans"; return 1; }
    # shellcheck disable=SC2034  # AS_RAW lo consume el runner E2E
    AS_RAW="$ans"
    case "$ans" in
        *"button returned:Si"*) return 0 ;;
        *)                      return 1 ;;
    esac
}

# ---------------------------------------------------------------------------
# Bloqueo (mkdir atomico + PID; espejo del flock)
# ---------------------------------------------------------------------------
lock_update() {
    if mkdir "$LOCKDIR" 2>/dev/null; then
        printf '%s\n' "$$" >"$LOCKDIR/pid" 2>/dev/null
        return 0
    fi
    local oldpid
    oldpid="$(cat "$LOCKDIR/pid" 2>/dev/null || echo "")"
    case "$oldpid" in
        ''|*[!0-9]*) ;;
        *)
            if kill -0 "$oldpid" 2>/dev/null; then
                log "another update in progress"
                return 1
            fi
            ;;
    esac
    rm -rf "$LOCKDIR" 2>/dev/null
    if mkdir "$LOCKDIR" 2>/dev/null; then
        printf '%s\n' "$$" >"$LOCKDIR/pid" 2>/dev/null
        return 0
    fi
    log "another update in progress"
    return 1
}

unlock_update() {
    rm -rf "$LOCKDIR" 2>/dev/null
}

# ---------------------------------------------------------------------------
# Acceso del Escritorio (enlace al script actualizador; equivale al .desktop de Linux)
# ---------------------------------------------------------------------------
DESK_LINK="$HOME/Desktop/${APP_NAME%.app}.command"

create_shortcut() {
    rm -f "$NOSHORTCUT" 2>/dev/null
    # El acceso apunta al script actualizador (comprueba, descarga y arranca).
    # Limpieza del formato anterior (enlace *.app a la app instalada).
    rm -f "$HOME/Desktop/$APP_NAME" 2>/dev/null
    ln -sfn "$SCRIPT" "$DESK_LINK" 2>/dev/null
    log "shortcut created"
}

remove_shortcut() {
    rm -f "$DESK_LINK" "$HOME/Desktop/$APP_NAME" 2>/dev/null
    : > "$NOSHORTCUT" 2>/dev/null
    log "shortcut removed"
}


assoc_info() {
    local app="$1"
    [ -d "$app" ] || return 1
    command -v python3 >/dev/null 2>&1 || return 1
    python3 - "$app/Contents/Info.plist" <<'PYEOF' 2>/dev/null
import plistlib, sys
with open(sys.argv[1], 'rb') as f:
    info = plistlib.load(f)
bid = info.get('CFBundleIdentifier', '') or ''
utis = []
for d in info.get('CFBundleDocumentTypes', []) or []:
    exts = [str(e).lower() for e in (d.get('CFBundleTypeExtensions') or [])]
    if any(e == 'fcstd' or e.startswith('fcstd') for e in exts):
        utis += [str(x) for x in (d.get('LSItemContentTypes') or [])]
utis = list(dict.fromkeys(utis))
if bid and utis:
    print(bid + ' ' + ','.join(utis))
PYEOF
}

assoc_active() {
    local app info bid utis u cur
    command -v duti >/dev/null 2>&1 || return 1
    app="$(app_path 2>/dev/null)"
    [ -d "$app" ] || return 1
    info="$(assoc_info "$app")" && [ -n "$info" ] || return 1
    bid="${info%% *}"
    utis="${info#* }"
    for u in $(printf '%s' "$utis" | tr ',' ' '); do
        cur="$(duti -x "$u" 2>/dev/null)"
        case "$cur" in *"$bid"*) ;; *) return 1 ;; esac
    done
    return 0
}

set_assoc() {
    rm -f "$NOASSOC" 2>/dev/null
    ASSOC_MODE=none
    local app info bid utis u ok
    app="$(app_path 2>/dev/null)"
    [ -d "$app" ] || return 0
    if command -v duti >/dev/null 2>&1 && info="$(assoc_info "$app")" && [ -n "$info" ]; then
        bid="${info%% *}"
        utis="${info#* }"
        ok=0
        for u in $(printf '%s' "$utis" | tr ',' ' '); do
            if duti -s "$bid" "$u" all 2>/dev/null; then ok=1; fi
        done
        if [ "$ok" = 1 ]; then ASSOC_MODE=duti; log "assoc set (duti)"; return 0; fi
    fi
    if [ -x "$LSREGISTER" ]; then
        "$LSREGISTER" -f "$app" 2>/dev/null
        : > "$NOASSOC" 2>/dev/null
        ASSOC_MODE=openwith
        log "assoc openwith-only"
        return 0
    fi
    log "assoc unavailable"
    return 0
}

remove_assoc() {
    local app
    app="$(app_path 2>/dev/null)"
    if [ -n "$app" ] && [ -d "$app" ] && [ -x "$LSREGISTER" ]; then
        "$LSREGISTER" -u "$app" 2>/dev/null
    fi
    : > "$NOASSOC" 2>/dev/null
    log "assoc removed"
}

maybe_assoc() {
    assoc_active 2>/dev/null && return 0
    [ -f "$NOASSOC" ] && return 0
    if [ "$ASSUME_YES" = 1 ] || ask_yesno "$(t ask_assoc)"; then
        set_assoc
        case "$ASSOC_MODE" in
            duti) notify "$(t assoc_set)" ;;
            openwith) notify "$(t assoc_openwith)" ;;
        esac
    else
        : > "$NOASSOC" 2>/dev/null
    fi
}

# El enlace apunta al actualizador: si existe pero a una ruta vieja (carpeta
# movida), se recrea en vez de darlo por bueno.
shortcut_current() { [ -L "$DESK_LINK" ] && [ "$(readlink "$DESK_LINK")" = "$SCRIPT" ]; }

maybe_create_shortcut() {
    if [ -L "$DESK_LINK" ] || [ -e "$DESK_LINK" ]; then
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

# ---------------------------------------------------------------------------
# Backup de configuracion (espejo de backup_config; sin find -printf/-newermt)
# ---------------------------------------------------------------------------
backup_config() {
    [ -d "$CFG_SRC" ] || return 0
    local newest now f m
    newest=0
    for f in "$BACKUP_DIR"/*.tar.gz; do
        [ -e "$f" ] || continue
        m="$(stat -f%m "$f" 2>/dev/null || echo 0)"
        case "$m" in
            ''|*[!0-9]*) m=0 ;;
        esac
        if [ "$m" -gt "$newest" ]; then
            newest="$m"
        fi
    done
    now="$(date +%s)"
    if [ "$newest" -gt 0 ] && [ "$((now - newest))" -lt 600 ]; then
        return 0
    fi
    mkdir -p "$BACKUP_DIR" 2>/dev/null || return 0
    tar -czf "$BACKUP_DIR/freecad-cfg-$(date +%Y%m%d-%H%M%S).tar.gz" \
        -C "$HOME/Library/Preferences" FreeCAD 2>/dev/null || return 0
    # shellcheck disable=SC2012
    ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | awk 'NR>3' | while read -r f; do
        rm -f "$f" 2>/dev/null
    done
    log "config backup saved"
}

# ---------------------------------------------------------------------------
# Instalacion desde el dmg (montar -> copiar .app -> cuarentena -> marcador)
# ---------------------------------------------------------------------------
detach_mnt() {
    hdiutil detach "$1" >/dev/null 2>&1
    rmdir "$1" 2>/dev/null
    return 0
}

# $1 = dmg, $2 = tag. Devuelve 0 y deja la .app instalada + marcador.
install_dmg() {
    local dmg="$1" tag="$2" mnt srcapp destdir dest
    command -v hdiutil >/dev/null 2>&1 || { t err_no_hdiutil >&2; return 1; }
    mnt="$(mktemp -d /tmp/.fcstable-mnt.XXXXXX 2>/dev/null)" || return 1
    if ! hdiutil attach -nobrowse -readonly -mountpoint "$mnt" "$dmg" >/dev/null 2>&1; then
        rmdir "$mnt" 2>/dev/null
        log "mount failed: $tag"
        notify "$(t err)" "$(t err_mount)"
        return 1
    fi
    srcapp="$(find "$mnt" -maxdepth 3 -name 'FreeCAD.app' -type d 2>/dev/null | head -n1)"
    if [ -z "$srcapp" ]; then
        detach_mnt "$mnt"
        log "no app in image: $tag"
        notify "$(t err)" "$(t err_noapp)"
        return 1
    fi
    destdir="$(app_dest_dir)"
    dest="$destdir/$APP_NAME"
    if [ -t 1 ]; then
        printf '%s\n' "$(t installing)"
    fi
    rm -rf "$dest" 2>/dev/null
    if ! cp -R "$srcapp" "$dest" 2>/dev/null; then
        detach_mnt "$mnt"
        log "install failed: $tag"
        notify "$(t err)" "$(t err_download)"
        return 1
    fi
    detach_mnt "$mnt"
    # Las weeklies (y futuros estables) pueden no estar notarizadas: quitar la
    # cuarentena evita el bloqueo de Gatekeeper. Inocuo si ya esta firmado.
    xattr -dr com.apple.quarantine "$dest" 2>/dev/null || true
    printf '%s\n' "$tag" >"$VERSION_FILE" 2>/dev/null
    return 0
}

# ---------------------------------------------------------------------------
# Descarga con progreso en consola (la .command corre en una Terminal visible)
# ---------------------------------------------------------------------------
fetch_file() {
    local url="$1" tmp="$2" prefix="$3" label="$4"
    local total dlpid cur pct tty
    total="$(curl -fsIL --connect-timeout 10 --max-time 30 "$url" 2>/dev/null \
             | grep -i '^content-length:' | tail -n1 | tr -d ' \r' | sed 's/[^0-9]//g')"
    case "$total" in
        ''|*[!0-9]*) total=0 ;;
    esac

    rm -f "$tmp"
    curl -fL --connect-timeout 10 --retry 2 -o "$tmp" "$url" 2>/dev/null &
    dlpid=$!
    tty=0; [ -t 1 ] && tty=1
    if [ "$tty" = 1 ]; then
        printf '%s %s...\n' "$prefix" "$label"
    fi
    while kill -0 "$dlpid" 2>/dev/null; do
        cur=$(stat -f%z "$tmp" 2>/dev/null || echo 0)
        case "$cur" in
            ''|*[!0-9]*) cur=0 ;;
        esac
        if [ "$tty" = 1 ]; then
            if [ "$total" -gt 0 ]; then
                pct=$(( cur*100/total )); [ "$pct" -gt 100 ] && pct=100
                printf '\r%s %s... %s/%s MiB (%s%%)   ' "$prefix" "$label" \
                    "$((cur/1048576))" "$((total/1048576))" "$pct"
            else
                printf '\r%s %s... %s MiB   ' "$prefix" "$label" "$((cur/1048576))"
            fi
        fi
        sleep 0.5
    done
    [ "$tty" = 1 ] && printf '\n'
    if ! wait "$dlpid" || [ ! -s "$tmp" ]; then
        rm -f "$tmp"
        return 1
    fi
    return 0
}

# ---------------------------------------------------------------------------
# Actualizacion
# ---------------------------------------------------------------------------
update_stable() {
    lock_update || return 1

    local res tag url
    res="$(get_release)" || res=""
    if [ -z "$res" ]; then
        log "check failed (offline?)"
        unlock_update
        return 1
    fi
    tag="$(printf '%s' "$res" | sed -n 1p)"
    url="$(printf '%s' "$res" | sed -n 2p)"
    if [ -z "$tag" ] || [ -z "$url" ]; then
        log "check failed (offline?)"
        unlock_update
        return 1
    fi

    local current
    current="$(latest_local)"
    if [ -n "$current" ] && [ "$current" = "$tag" ]; then
        log "up to date ($tag)"
        unlock_update
        return 0
    fi

    local prefix
    prefix="$(t downloading)"
    if [ -z "$current" ]; then
        prefix="$(t no_local)"
        log "no local version; downloading $tag"
        notify "$(t no_local)" "$tag"
        if [ "$LEGACY_MAC" = 1 ]; then
            log "legacy macOS ($MACOS_MAJ): using $LEGACY_TAG"
            notify "$(t legacy)" "$LEGACY_TAG"
        fi
    fi

    local asset tmp
    asset="$(basename "$url")"
    tmp="$HERE/.${asset}.part"
    if ! fetch_file "$url" "$tmp" "$prefix" "$tag"; then
        rm -f "$tmp"
        log "download failed: $tag"
        notify "$(t err)" "$(t err_download)"
        unlock_update
        return 1
    fi

    if [ -t 1 ]; then
        printf '%s\n' "$(t verifying)"
    fi
    local exp act
    exp="$(curl -fsSL --connect-timeout 5 --max-time 15 "${url}-SHA256.txt" 2>/dev/null | awk '{print $1}')"
    act="$(shasum -a 256 "$tmp" 2>/dev/null | awk '{print $1}')"
    # Fail-closed: sin sidecar no hay verificación posible y NO se instala
    # (antes se instalaba sin verificar). Sin red, la versión local sigue
    # usándose: este punto solo se alcanza tras descargar algo nuevo.
    if [ -z "$exp" ]; then
        rm -f "$tmp"
        log "sha256 sidecar unavailable: $tag (not updating)"
        notify "$(t err)" "$(t err_checksum)"
        unlock_update
        return 1
    fi
    if [ -z "$act" ] || [ "$exp" != "$act" ]; then
        rm -f "$tmp"
        log "sha256 mismatch: $tag (exp=$exp act=$act)"
        notify "$(t err)" "$(t err_checksum)"
        unlock_update
        return 1
    fi

    if ! install_dmg "$tmp" "$tag"; then
        rm -f "$tmp"
        unlock_update
        return 1
    fi
    rm -f "$tmp"
    unlock_update
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
    local current
    current="$(latest_local)"
    if [ -n "$current" ] && [ "$current" = "$tag" ]; then
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
    remove_assoc 2>/dev/null
    rm -rf "/Applications/$APP_NAME" "$HOME/Applications/$APP_NAME" 2>/dev/null
    rm -f "$DESK_LINK" "$HOME/Desktop/$APP_NAME" 2>/dev/null
    rm -f "$HERE"/.FreeCAD_[0-9]*.part "$HERE"/.FreeCAD_*.dmg* 2>/dev/null
    rm -f "$VERSION_FILE" "$LOG" "$NOSHORTCUT" "$NOASSOC" 2>/dev/null
    rm -rf "$LOCKDIR" 2>/dev/null
    notify "$(t uninstalled)"
    t uninstalled
}

show_help() {
    if [ "$LANG_CODE" = es ]; then
        cat <<EOF
$SUITE v$VERSION
$(t name) - dmg estable: descarga, instala, actualiza y ejecuta.

Uso: $(basename "$SCRIPT") [opciones] [--] [argumentos de FreeCAD]

Opciones:
  --no-update         Arranca sin comprobar actualizaciones.
  --check             Solo comprueba si hay una version nueva (no descarga).
  --reinstall         Borra la version local y descarga de nuevo la ultima.
  --create-shortcut   Crea el acceso en el Escritorio.
  --remove-shortcut   Elimina el acceso del Escritorio.
  --associate         Asocia los archivos .FCStd (abrir con doble clic).
  --remove-assoc      Quita la asociación de .FCStd.
  --uninstall         Desinstala (app, acceso, marcas, log).
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
$(t name) - stable dmg: download, install, update and run.

Usage: $(basename "$SCRIPT") [options] [--] [FreeCAD arguments]

Options:
  --no-update         Run without checking for updates.
  --check             Only check for a new version (no download).
  --reinstall         Remove the local version and download the latest again.
  --create-shortcut   Create the Desktop shortcut.
  --remove-shortcut   Remove the Desktop shortcut.
  --associate         Associate .FCStd files (open on double click).
  --remove-assoc      Remove the .FCStd association.
  --uninstall         Uninstall (app, shortcut, marks, log).
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
# Principal
# ---------------------------------------------------------------------------
main() {
    UPDATE=1
    ACTION=""
    ASSUME_YES=0
    VERBOSE=0
    FC_ARGS=()

    while [ $# -gt 0 ]; do
        case "$1" in
            --)               shift; while [ $# -gt 0 ]; do FC_ARGS+=("$1"); shift; done; break ;;
            --no-update)      UPDATE=0; shift ;;
            --check)          ACTION=check; shift ;;
            --reinstall)      ACTION=reinstall; shift ;;
            --create-shortcut) ACTION=create-shortcut; shift ;;
            --remove-shortcut) ACTION=remove-shortcut; shift ;;
            --associate)      ACTION=associate; shift ;;
            --remove-assoc)   ACTION=remove-assoc; shift ;;
            --uninstall)      ACTION=uninstall; shift ;;
            -y|--yes)         ASSUME_YES=1; shift ;;
            -v|--verbose)     VERBOSE=1; shift ;;
            -h|--help)        ACTION=help; shift ;;
            *)                FC_ARGS+=("$1"); shift ;;
        esac
    done

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
        associate)
            set_assoc
            case "$ASSOC_MODE" in
                duti) notify "$(t assoc_set)" ;;
                openwith) notify "$(t assoc_openwith)" ;;
            esac
            exit 0 ;;
        remove-assoc)   remove_assoc; notify "$(t assoc_removed)"; exit 0 ;;
        uninstall)        do_uninstall; exit 0 ;;
    esac

    if [ "$ACTION" = reinstall ]; then
        rm -rf "/Applications/$APP_NAME" "$HOME/Applications/$APP_NAME" 2>/dev/null
        rm -f "$VERSION_FILE"
    fi

    if [ "$UPDATE" = 1 ]; then
        update_stable
    fi

    CURRENT="$(latest_local)"
    if [ -z "$CURRENT" ]; then
        notify "$(t err)" "$(t err_no_local)"
        t err_no_local >&2
        exit 1
    fi

    maybe_create_shortcut
    maybe_assoc

    backup_config

    APP="$(app_path)"
    BIN="$APP/Contents/MacOS/FreeCAD"
    if [ -x "$BIN" ]; then
        exec "$BIN" ${FC_ARGS[@]+"${FC_ARGS[@]}"}
    else
        exec open -a "$APP" --args ${FC_ARGS[@]+"${FC_ARGS[@]}"}
    fi
}

if [ "${FC_TEST:-0}" != 1 ]; then
    main "$@"
fi
