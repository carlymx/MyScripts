#!/bin/bash
# Runner E2E desechable para macOS (se borra tras la validación).
# Ejecuta en un Mac real las ramas que no se pueden probar en Linux y deja
# un log pensado para analizarse en Linux (protocolo PASS/FAIL/MANUAL/SKIP).
#
# MODO NORMAL (recomendado): hace las 4 pasadas seguidas con UN solo comando.
# Copia la carpeta mac/ a un sitio con escritura, abre la Terminal en esa
# carpeta y ejecuta:
#   chmod +x run-e2e-tests.sh FreeCAD-*.command
#   ./run-e2e-tests.sh --todo
# El propio script te dice en pantalla todo lo que tienes que hacer
# (es 1 clic y un par de teclas S/N; lo demás va solo). Al terminar, envía
# los 4 ficheros E2E-RESULT-*.log a Linux y borra la carpeta de prueba.
#
# MODO POR PASADAS (solo para repetir una pasada aislada):
#   ./run-e2e-tests.sh [stable|weekly] [--auto] [--full]
# MODO MÉTODOS (diagnóstico de descarga: prueba 4 métodos y verifica cada
# uno con el sidecar, sin instalar nada):
#   ./run-e2e-tests.sh stable --methods
set -u
# Nota: LANG_CODE y ASSUME_YES las consume el producto importado con '.'
# (shellcheck avisa SC2034: falsos positivos, igual que en la v1).

CHAN="stable"; AUTO=0; FULL=0; TODO=0; METHODS=0
for a in "$@"; do
    case "$a" in
        stable|weekly) CHAN="$a" ;;
        --auto) AUTO=1 ;;
        --full) FULL=1 ;;
        --todo) TODO=1 ;;
        --methods) METHODS=1 ;;
        *) echo "uso: $0 [stable|weekly] [--auto] [--full] [--todo] [--methods]" >&2; exit 2 ;;
    esac
done

HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

# La carpeta tiene que tener permiso de escritura (logs y temporales).
if ! touch "$HERE/.e2e-w.tmp" 2>/dev/null; then
    echo "Esta carpeta es de solo lectura. Copiala a un sitio con escritura (p. ej. Documentos) y ejecuta el script alli."
    echo "This folder is read-only. Copy the mac folder somewhere writable (e.g. Documents) and run the script there."
    exit 2
fi
rm -f "$HERE/.e2e-w.tmp"

# Idioma de las instrucciones en pantalla (según el Mac; por defecto inglés).
E2EES=0
_al="$(defaults read -g AppleLanguages 2>/dev/null || echo "")"
case "$_al" in
    *es-ES*|*es_419*|*'"es"'*) E2EES=1 ;;
    *) case "${LC_ALL:-}${LANG:-}" in
           *es_*|*es-*) E2EES=1 ;;
           *) E2EES=0 ;;
       esac ;;
esac

STAMP="$(date +%Y%m%d-%H%M%S)"
RLOG="$HERE/E2E-RESULT-$CHAN-$STAMP-macos.log"
NOLOG=0
P=0; F=0; M=0; S=0
say()  { if [ "$NOLOG" = 1 ]; then printf '%s\n' "$*"; else printf '%s\n' "$*" | tee -a "$RLOG"; fi; }
pass() { P=$((P+1)); say "PASS $1 :: $2"; }
fail() { F=$((F+1)); say "FAIL $1 :: $2"; }
manual()  { M=$((M+1)); say "MANUAL $1 :: $2"; }
skip() { S=$((S+1)); say "SKIP $1 :: $2"; }
info() { say "INFO $1"; }
guide() { if [ "$E2EES" = 1 ]; then say "$1"; else say "$2"; fi; }

METHOD_WINS=""
measure_check() {
    # $1=nombre $2=fichero $3=esperado (hex en minúsculas)
    _mn="$1"; _mf="$2"; _me="$3"
    if [ -f "$_mf" ]; then
        _mb="$(wc -c <"$_mf" | tr -d ' ')"
        _mh="$(shasum -a 256 "$_mf" 2>/dev/null | awk '{print $1}' | tr 'A-Z' 'a-z')"
        if [ "$_mh" = "$_me" ]; then _mm=yes; else _mm=no; fi
        info "method-$_mn bytes=$_mb match=$_mm"
        if [ "$_mm" = yes ]; then
            pass "method-$_mn" "ok $_mb bytes"
            METHOD_WINS="$METHOD_WINS $_mn"
        else
            fail "method-$_mn" "mismatch bytes=$_mb act=$_mh"
        fi
    else
        fail "method-$_mn" "sin fichero"
    fi
    rm -f "$_mf"
}

# Banco de métodos de descarga (desechable, diagnóstico): prueba 4 métodos
# contra la misma URL y verifica cada uno con el sidecar. Orden de más
# deseable (el propio producto) a más directo (segmentos, python3).
measure_methods() {
    # $1=url del asset
    _mu="$1"
    METHOD_WINS=""
    _expf="$HERE/.e2e-exp.part"; rm -f "$_expf"
    if ! fetch_file "${_mu}-SHA256.txt" "$_expf" "E2E" "sha" 2>/dev/null || [ ! -s "$_expf" ]; then
        fail "methods" "sin sidecar"; rm -f "$_expf"; return 0
    fi
    _me="$(awk '{print $1}' "$_expf" | tr 'A-Z' 'a-z')"
    rm -f "$_expf"
    if [ "$(printf '%s' "$_me" | wc -c | tr -d ' ')" != 64 ]; then fail "methods" "hash raro: $_me"; return 0; fi
    case "$_me" in
        *[!0-9a-f]*) fail "methods" "hash raro: $_me"; return 0 ;;
    esac
    info "methods-exp=$_me"
    # M1: el propio producto (curl con progreso y reintentos).
    _md="$HERE/.e2e-method-1.part"; rm -f "$_md"
    if fetch_file "$_mu" "$_md" "E2E-M1" "bin" 2>/dev/null; then
        measure_check "m1-producto" "$_md" "$_me"
    else
        fail "method-m1-producto" "fetch_file rc!=0"; rm -f "$_md"
    fi
    # M2: curl plano (mismo transporte, sin maquinaria de progreso).
    _md="$HERE/.e2e-method-2.part"; rm -f "$_md"
    if curl -fL --connect-timeout 15 --retry 2 --max-time 1800 -o "$_md" "$_mu" >/dev/null 2>&1; then
        measure_check "m2-curl" "$_md" "$_me"
    else
        fail "method-m2-curl" "curl rc=$?"; rm -f "$_md"
    fi
    # M3: 4 segmentos por rangos (varias conexiones) + concatenado.
    _md="$HERE/.e2e-method-3.part"; rm -f "$_md" "$_md".seg?
    _len="$(curl -fsIL --connect-timeout 15 --max-time 60 "$_mu" 2>/dev/null | grep -i '^content-length:' | tail -n1 | tr -d ' \r' | sed 's/[^0-9]//g')"
    case "$_len" in
        ''|0) skip "method-m3-rangos" "sin content-length" ;;
        *)
            _seg=$(( (_len + 3) / 4 )); _ok=1; _s=0; _i=0
            while [ "$_i" -lt 4 ] && [ "$_ok" = 1 ]; do
                _e=$(( _s + _seg - 1 ))
                if [ "$_e" -ge "$_len" ]; then _e=$(( _len - 1 )); fi
                if ! curl -fL --connect-timeout 15 --retry 2 --max-time 1800 -r "$_s-$_e" -o "$_md.seg$_i" "$_mu" >/dev/null 2>&1; then _ok=0; fi
                _s=$(( _e + 1 )); _i=$(( _i + 1 ))
            done
            if [ "$_ok" = 1 ]; then
                if cat "$_md".seg? >"$_md" 2>/dev/null; then
                    measure_check "m3-rangos" "$_md" "$_me"
                else
                    fail "method-m3-rangos" "sin concatenar"
                fi
            else
                fail "method-m3-rangos" "fallo un segmento"
            fi
            ;;
    esac
    rm -f "$_md" "$_md".seg?
    # M4: python3 urllib (otra pila TLS/HTTP), si existe.
    if command -v python3 >/dev/null 2>&1 && python3 -c 'import urllib.request' >/dev/null 2>&1; then
        _md="$HERE/.e2e-method-4.part"; rm -f "$_md"
        if python3 -c 'import sys, urllib.request
url, dest = sys.argv[1], sys.argv[2]
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
r = urllib.request.urlopen(req, timeout=60)
f = open(dest, "wb")
while True:
    b = r.read(131072)
    if not b: break
    f.write(b)
f.close()' "$_mu" "$_md" >/dev/null 2>&1; then
            measure_check "m4-python3" "$_md" "$_me"
        else
            fail "method-m4-python3" "python3 rc=$?"; rm -f "$_md"
        fi
    else
        skip "method-m4-python3" "sin python3"
    fi
    if [ -z "$METHOD_WINS" ]; then info "methods-best=none"; else info "methods-best=$METHOD_WINS"; fi
}

TODOBAD=0
run_pass() {
    # $1=num $2=chan $3=flags-desc-es $4=flags-desc-en $5.. = flags reales
    _n="$1"; _c="$2"; _es="$3"; _en="$4"; shift 4
    if [ "$E2EES" = 1 ]; then say "———— PASADA $_n de 4: $_es ————";
    else say "———— PASS $_n of 4: $_en ————"; fi
    if bash "$HERE/run-e2e-tests.sh" "$_c" "$@"; then
        guide "Pasada $_n terminada SIN FALLOS." "Pass $_n finished with NO FAILURES."
    else
        guide "Pasada $_n terminada CON FALLOS. Sigo con la siguiente." "Pass $_n finished WITH FAILURES. Continuing with the next one."
        TODOBAD=$((TODOBAD+1))
    fi
}

if [ "$TODO" = 1 ]; then
    NOLOG=1
    guide 'Voy a probar el instalador de FreeCAD en 4 pasadas seguidas. No tienes que escribir nada mas.' 'I am going to test the FreeCAD installer in 4 passes. You do not need to type anything else.'
    guide 'LO QUE NECESITO DE TI:' 'WHAT I NEED FROM YOU:'
    guide '  1. En la pasada 1 aparecera un dialogo de pregunta: haz clic en SI.' '  1. In pass 1 a question dialog will appear: click YES.'
    guide '  2. Cuando te pregunte si viste un aviso, pulsa S (si) o N (no).' '  2. When I ask if you saw a notification, press S (yes) or N (no).'
    guide '  3. Fijate si aparecen los avisos (arriba a la derecha).' '  3. Watch whether the notifications appear (top right).'
    guide 'Las pasadas 3 y 4 descargan ~700 MB cada una e instalan y desinstalan solas: tardan varios minutos. Dejalo trabajar.' 'Passes 3 and 4 download ~700 MB each and install/uninstall on their own: they take several minutes. Let it work.'
    guide 'Los resultados se guardan solos en 4 ficheros E2E-RESULT-*.log en esta carpeta.' 'Results are saved automatically in 4 E2E-RESULT-*.log files in this folder.'
    guide 'Si una completa falla, hara diagnosticos extra (mas descargas) para averiguar por que.' 'If a full pass fails, it will run extra diagnostics (more downloads) to find out why.'
    run_pass 1 stable 'canal estable, rapida (~1 min). TE PEDIRE 1 CLIC.' 'stable channel, quick (~1 min). I WILL ASK FOR 1 CLICK.'
    run_pass 2 weekly 'canal semanal, rapida y automatica (~1 min). Sin clics.' 'weekly channel, quick and automatic (~1 min). No clicks.' --auto
    run_pass 3 stable 'canal estable, COMPLETA (descarga, instala y desinstala sola).' 'stable channel, FULL (downloads, installs and uninstalls on its own).' --full
    run_pass 4 weekly 'canal semanal, COMPLETA y automatica.' 'weekly channel, FULL and automatic.' --auto --full
    if [ "$TODOBAD" = 0 ]; then
        guide 'LISTO: las 4 pasadas terminaron sin fallos.' 'DONE: all 4 passes finished with no failures.'
    else
        guide "LISTO: las 4 pasadas terminaron ($TODOBAD con fallos; los fallos tambien son un resultado util)." "DONE: all 4 passes finished ($TODOBAD with failures; failures are a useful result too)."
    fi
    guide 'Enviame los 4 ficheros E2E-RESULT-*-macos.log de esta carpeta y borra la carpeta de prueba.' 'Send me the 4 E2E-RESULT-*-macos.log files from this folder and delete the test folder.'
    if [ "$TODOBAD" = 0 ]; then exit 0; else exit 1; fi
fi

# ---------------------------------------------------------------------------
# Modo por pasada
# ---------------------------------------------------------------------------
if [ "$E2EES" = 1 ]; then
    if [ "$FULL" = 1 ]; then say "Voy a probar el canal $CHAN (prueba COMPLETA: descarga ~700 MB, instala y desinstala sola; tarda varios minutos).";
    else say "Voy a probar el canal $CHAN (prueba rapida, ~1 min)."; fi
    if [ "$AUTO" = 1 ]; then say 'Modo automatico: no tienes que hacer clic en nada.';
    else say 'TE PEDIRE 1 CLIC en un dialogo de pregunta cuando aparezca.'; fi
    say 'Ademas te preguntare si viste un aviso: pulsa S (si) o N (no). Fijate si aparecen (arriba a la derecha).'
else
    if [ "$FULL" = 1 ]; then say "Testing the $CHAN channel (FULL test: downloads ~700 MB, installs and uninstalls on its own; takes several minutes).";
    else say "Testing the $CHAN channel (quick test, ~1 min)."; fi
    if [ "$AUTO" = 1 ]; then say 'Automatic mode: you do not need to click anything.';
    else say 'I WILL ASK FOR 1 CLICK on a question dialog when it appears.'; fi
    say 'I will also ask whether you saw a notification: press S (yes) or N (no). Watch whether they appear (top right).'
fi

info "# E2E $CHAN macos $(date '+%F %T')"
info "bash=$BASH_VERSION"
info "uname-m=$(uname -m)"
info "sw_vers=$(sw_vers -productVersion 2>/dev/null || echo desconocido)"
info "locale=$(locale 2>/dev/null | grep -E '^(LANG|LC_ALL)' | tr '\n' ' ')"
info "applelangs=$(defaults read -g AppleLanguages 2>/dev/null | tr -d ' \n' | cut -c1-60)"
info "auto=$AUTO full=$FULL"
if command -v shasum >/dev/null 2>&1; then
    info "product-sha=$(shasum -a 256 "$HERE/FreeCAD-$CHAN.command" 2>/dev/null | awk '{print $1}')"
else
    info "product-sha=ilegible (sin shasum)"
fi
case "$BASH_VERSION" in
    3.*) ;;
    *) guide "AVISO: bash $BASH_VERSION (los scripts piden bash 3.2 de macOS)." "WARNING: bash $BASH_VERSION (the scripts target macOS bash 3.2)." ;;
esac

export FC_TEST=1
# shellcheck disable=SC1090
. "$HERE/FreeCAD-$CHAN.command"
info "legacy-mac=${LEGACY_MAC:-0} (macos ${MACOS_MAJ:-?})"

# 1. i18n básico (puro, sin SO)
for l in es en; do
    LANG_CODE="$l"
    v="$(t check_ok)"
    if [ -n "$v" ] && [ "$v" != check_ok ]; then pass "t-$l" "$v"; else fail "t-$l" "vacio"; fi
done
# LANG_CODE y ASSUME_YES los consume el producto importado con '.' (falso positivo).
# shellcheck disable=SC2034
LANG_CODE="en"

# 2. notificación real + pregunta al humano (1 tecla)
if [ "$METHODS" = 1 ]; then
    skip "notify" "modo --methods (sin aviso)"
    skip "notify-seen" "modo --methods (sin pregunta)"
else
    if notify "E2E: prueba de notificacion" "canal $CHAN" 2>/dev/null; then
        pass "notify" "osascript exit 0"
    else
        fail "notify" "osascript dio error"
    fi
    guide 'Acabo de pedir al Mac que muestre un aviso. ¿Lo has visto aparecer? Pulsa S (si) o N (no).' 'I just asked the Mac to show a notification. Did you see it appear? Press S (yes) or N (no).'
    printf 'S/N: '; seen=""; read -r seen || seen=""
    case "$seen" in
        [SsYy]*) pass "notify-seen" "respuesta=$seen" ;;
        *) manual "notify-seen" "sin confirmar (respuesta='$seen')" ;;
    esac
fi

# 3. diálogo: 1 clic manual, o timeout en --auto
if [ "$METHODS" = 1 ]; then
    skip "dialog" "modo --methods (sin dialogo)"
elif [ "$AUTO" = 1 ]; then
    ans="$(osascript -e 'display dialog "E2E auto: se cierra solo" with title "E2E" buttons {"Vale"} default button "Vale" giving up after 3' 2>&1)"; arc=$?
    case "$ans" in
        *"gave up"*) pass "dialog-timeout" "$ans" ;;
        *) fail "dialog-timeout" "rc=$arc out=[$ans]" ;;
    esac
else
    guide 'AHORA va a aparecer un dialogo de pregunta: haz clic en SI.' 'NOW a question dialog is about to appear: click YES.'
    if ask_yesno "E2E: pulsa Si en este dialogo"; then
        pass "dialog-click" "respuesta=Si"
    else
        fail "dialog-click" "respuesta!=Si; osascript=[${AS_RAW:-vacio}]"
    fi
fi

# 4. herramientas del sistema
for tool in hdiutil shasum curl tar; do
    if command -v "$tool" >/dev/null 2>&1; then pass "tool-$tool" "$(command -v "$tool")";
    else fail "tool-$tool" "no encontrado"; fi
done
if command -v python3 >/dev/null 2>&1; then info "have-python3=$(command -v python3)"; else info "have-python3=no"; fi

# 5. lock real (se crea y se limpia junto al script)
if lock_update; then
    if lock_update; then fail "lock-doble" "segundo lock aceptado"; else pass "lock-doble" "rechazado"; fi
    unlock_update
    pass "lock-basic" "adquirido y liberado"
else
    fail "lock-basic" "no se pudo adquirir"
fi

# 6. descubrimiento de versión (red real)
if [ "$CHAN" = stable ]; then
    rel="$(get_release)" || rel=""
    tag="$(printf '%s' "$rel" | sed -n 1p)"; url="$(printf '%s' "$rel" | sed -n 2p)"
    case "$tag" in ''|*[!0-9.]*) fail "release" "tag=$tag";; *) info "tag=$tag"; info "url=$url"; pass "release" "$tag";; esac
    REL_URL="$url"
else
    tag="$(get_latest_tag)" || tag=""
    if [ "${LEGACY_MAC:-0}" = 1 ]; then
        case "$tag" in "$LEGACY_TAG") info "tag=$tag (macOS antiguo: compatible)"; pass "tag" "$tag";; *) fail "tag" "tag=$tag";; esac
    else
        case "$tag" in weekly-[0-9][0-9][0-9][0-9].[0-9][0-9].[0-9][0-9]) info "tag=$tag"; pass "tag" "$tag";; *) fail "tag" "tag=$tag";; esac
    fi
    url="$(get_weekly_asset "$tag")" || url=""
    if [ -n "$url" ]; then info "url=$url"; pass "asset" "$url"; else fail "asset" "tag=$tag"; fi
    REL_URL="$url"
fi

# 7. descarga pequeña real (sidecar SHA256) + verificación de hash
small="$HERE/.e2e-small.part"
rm -f "$small"
if [ -n "${REL_URL:-}" ] && fetch_file "${REL_URL}-SHA256.txt" "$small" "E2E" "sha" 2>/dev/null && [ -s "$small" ]; then
    pass "fetch-small" "$(wc -c <"$small") bytes"
    rm -f "$small"
else
    fail "fetch-small" "url=${REL_URL:-vacia}"
fi

# 7b. banco de métodos de descarga (solo --methods explícito)
if [ "$METHODS" = 1 ]; then
    if [ -n "${REL_URL:-}" ]; then measure_methods "$REL_URL"; else skip "methods" "sin URL"; fi
fi
if [ "$METHODS" = 1 ]; then
    say "RESULT pass=$P fail=$F manual=$M skip=$S"
    say "RLOG $RLOG"
    guide "Banco terminado. El fichero de resultados esta en: $RLOG" "Benchmark finished. The results file is at: $RLOG"
    if [ "$F" = 0 ]; then exit 0; else exit 1; fi
fi

# 8. atajo real en el Escritorio + asociación (reversible, independiente del orden)
# Se ejecuta con la app ya instalada: en --full, justo después de instalar.
shortcut_assoc_tests() {
    # Limpia las marcas: si una pasada previa quitó el atajo, la marca haría
    # que "crear" no hiciera nada y el test daría un falso FAIL.
    rm -f "$NOSHORTCUT" "$NOASSOC" 2>/dev/null
    # ASSUME_YES lo consume el producto importado con '.' (falso positivo).
    # shellcheck disable=SC2034
    ASSUME_YES=1
    maybe_create_shortcut 2>/dev/null
    if [ -L "$DESK_LINK" ]; then pass "shortcut-create" "$DESK_LINK -> $(readlink "$DESK_LINK")";
    else fail "shortcut-create" "sin enlace"; fi
    remove_shortcut 2>/dev/null
    if [ ! -e "$DESK_LINK" ] && [ -f "$NOSHORTCUT" ]; then pass "shortcut-remove" "quitado + marca";
    else fail "shortcut-remove" "resto en Escritorio"; fi
    if command -v duti >/dev/null 2>&1; then
        skip "assoc" "duti presente: omitido para no tocar tu programa por defecto (ruta duti validada en lab)"
    elif [ -x "$LSREGISTER" ]; then
        maybe_assoc 2>/dev/null
        if assoc_active 2>/dev/null || [ -f "$NOASSOC" ]; then pass "assoc-set" "ok";
        else fail "assoc-set" "sin marca ni registro"; fi
        remove_assoc 2>/dev/null
        if [ -f "$NOASSOC" ]; then pass "assoc-remove" "quitado + marca";
        else fail "assoc-remove" "sin marca"; fi
    else
        skip "assoc" "sin duti/lsregister (solo máquina real --full)"
    fi
    # shellcheck disable=SC2034
    ASSUME_YES=0
}

if [ "$FULL" = 0 ]; then
    if [ -d "$(app_path)" ]; then
        shortcut_assoc_tests
    else
        skip "shortcut" "sin app instalada (el modo --full la instala y lo prueba)"
        skip "assoc" "sin app instalada (el modo --full la instala y lo prueba)"
    fi
fi

# 9. backup real con config de mentira (no toca tu config de verdad)
OLDHOME="$HOME"
FAKEHOME="$(mktemp -d /tmp/fc-e2e-home.XXXXXX 2>/dev/null)" || FAKEHOME="/tmp/fc-e2e-home-$$"
mkdir -p "$FAKEHOME/Library/Preferences/FreeCAD"
echo "e2e" > "$FAKEHOME/Library/Preferences/FreeCAD/user.cfg"
OLD_CFG_SRC="$CFG_SRC"
CFG_SRC="$FAKEHOME/Library/Preferences/FreeCAD"
HOME="$FAKEHOME"
rm -f "$BACKUP_DIR"/*.tar.gz
if backup_config 2>/dev/null; then brc=0; else brc=1; fi
HOME="$OLDHOME"
CFG_SRC="$OLD_CFG_SRC"
if [ "$brc" = 0 ]; then
    zb="$(ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -n1)"
    if [ -n "$zb" ]; then pass "backup" "$zb"; else fail "backup" "sin zip"; fi
else
    fail "backup" "backup_config dio error"
fi
rm -rf "$FAKEHOME"

# 10. modo --full: update real + desinstalación real (reversible)
if [ "$FULL" = 1 ]; then
    if [ "$CHAN" = stable ]; then update_stable; rc=$?; else update_weekly; rc=$?; fi
    FULLOK=1
    if [ "$rc" = 0 ]; then
        app="$(app_path)"
        if [ -x "$app/Contents/MacOS/FreeCAD" ]; then
            pass "full-install" "$app marcador=$(cat "$VERSION_FILE" 2>/dev/null)"
        else
            fail "full-install" "sin binario en $app"; FULLOK=0
        fi
    else
        fail "full-install" "update rc=$rc (ver log)"; FULLOK=0
    fi
    # Atajo + asociación con la app ya instalada (cobertura real del canal).
    if [ "$FULLOK" = 1 ]; then shortcut_assoc_tests; fi
    if [ "$FULLOK" = 0 ] && [ -n "${REL_URL:-}" ]; then
        guide 'La completa fallo: ejecuto el banco de diagnostico (4 descargas mas, varios minutos).' 'The full pass failed: running the diagnostic benchmark (4 more downloads, several minutes).'
        measure_methods "$REL_URL"
    fi
    info "productlog::$(tail -n5 "$LOG" 2>/dev/null | tr '\n' '|')"
    info "free-gb=$(df -k "$HERE" 2>/dev/null | tail -n1 | awk '{printf "%.1f", $4/1048576}')"
    ASSUME_YES=1
    do_uninstall >/dev/null 2>&1
    # shellcheck disable=SC2034
    ASSUME_YES=0
    if [ ! -d "$(app_path)" ] && [ ! -f "$VERSION_FILE" ]; then
        pass "full-uninstall" "app y marcador eliminados (backups conservados)"
    else
        fail "full-uninstall" "quedan restos"
    fi
else
    skip "full-install" "pasa --full para descarga+instalacion reales"
    skip "full-uninstall" "pasa --full para descarga+instalacion reales"
fi

say "RESULT pass=$P fail=$F manual=$M skip=$S"
say "RLOG $RLOG"
if [ "$E2EES" = 1 ]; then
    say "Pasada terminada: $P aprobadas, $F fallos. El fichero de resultados esta en: $RLOG"
else
    say "Pass finished: $P passed, $F failed. The results file is at: $RLOG"
fi
if [ "$FULL" = 0 ] && [ "$CHAN" = stable ] && [ "$AUTO" = 0 ]; then
    guide 'Siguiente paso, ejecuta: ./run-e2e-tests.sh weekly --auto' 'Next step, run: ./run-e2e-tests.sh weekly --auto'
elif [ "$FULL" = 0 ] && [ "$CHAN" = weekly ] && [ "$AUTO" = 1 ]; then
    guide 'Siguiente paso, ejecuta: ./run-e2e-tests.sh stable --full' 'Next step, run: ./run-e2e-tests.sh stable --full'
elif [ "$FULL" = 1 ] && [ "$CHAN" = stable ]; then
    guide 'Siguiente paso, ejecuta: ./run-e2e-tests.sh weekly --full --auto' 'Next step, run: ./run-e2e-tests.sh weekly --full --auto'
else
    guide 'Guarda este fichero de resultados y sigue con la siguiente pasada (o enviame los logs si era la ultima).' 'Keep this results file and continue with the next pass (or send me the logs if it was the last one).'
fi
if [ "$F" = 0 ]; then exit 0; else exit 1; fi
