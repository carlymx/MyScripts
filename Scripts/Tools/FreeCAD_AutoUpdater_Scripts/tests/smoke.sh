#!/bin/bash
# Smoke test del proyecto (rápido, sin red, sin root).
# Uso: ./tests/smoke.sh   (sale 0 si todo pasa, 1 si algo falla)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); printf 'PASS %s\n' "$1"; }
bad()  { FAIL=$((FAIL+1)); printf 'FAIL %s :: %s\n' "$1" "$2"; }

# 1. Sintaxis bash -----------------------------------------------------------
for f in linux/*.sh mac/*.command mac/run-e2e-tests.sh tests/smoke.sh; do
    if bash -n "$HERE/$f" 2>/dev/null; then ok "bash-n $f"; else bad "bash-n $f" "error de sintaxis"; fi
done

# 2. shellcheck (si está instalado) -------------------------------------------
if command -v shellcheck >/dev/null 2>&1; then
    for f in linux/*.sh mac/*.command mac/run-e2e-tests.sh; do
        if shellcheck -S warning "$HERE/$f" >/dev/null 2>&1; then ok "shellcheck $f"; else bad "shellcheck $f" "avisos"; fi
    done
else
    printf 'SKIP shellcheck (no instalado)\n'
fi

# 3. Paridad VERSION/SUITE en los 6 productos ---------------------------------
for f in linux/FreeCAD-stable.sh linux/FreeCAD-weekly.sh \
         mac/FreeCAD-stable.command mac/FreeCAD-weekly.command; do
    grep -q '^VERSION="0.8.6"$' "$HERE/$f" || bad "version $f" "VERSION distinta de 0.8.6"
    grep -q '^SUITE="FreeCAD AutoUpdater Scripts"$' "$HERE/$f" || bad "suite $f" "SUITE distinto"
done
for f in win/FreeCAD-stable.ps1 win/FreeCAD-weekly.ps1; do
    grep -q "VERSION = '0.8.6'" "$HERE/$f" || bad "version $f" "VERSION distinta de 0.8.6"
    grep -q "SUITE = 'FreeCAD AutoUpdater Scripts'" "$HERE/$f" || bad "suite $f" "SUITE distinto"
done
ok "version/suite 6 productos"

# 4. Paridad i18n es/en dentro de cada producto -------------------------------
for f in linux/FreeCAD-stable.sh linux/FreeCAD-weekly.sh \
         mac/FreeCAD-stable.command mac/FreeCAD-weekly.command; do
    es=$(grep -oE 'es:[a-z_]+' "$HERE/$f" | sort -u | md5sum | cut -d' ' -f1)
    en=$(grep -oE 'en:[a-z_]+' "$HERE/$f" | sed 's/^en:/es:/' | sort -u | md5sum | cut -d' ' -f1)
    if [ "$es" = "$en" ]; then ok "i18n $f"; else bad "i18n $f" "claves es/en distintas"; fi
done
for f in win/FreeCAD-stable.ps1 win/FreeCAD-weekly.ps1; do
    es=$(tr -d '\r' < "$HERE/$f" | grep -oE "'es:[a-z_]+" | tr -d "'" | sort -u | md5sum | cut -d' ' -f1)
    en=$(tr -d '\r' < "$HERE/$f" | grep -oE "'en:[a-z_]+" | tr -d "'" | sed "s/^en:/es:/" | sort -u | md5sum | cut -d' ' -f1)
    if [ "$es" = "$en" ]; then ok "i18n $f"; else bad "i18n $f" "claves es/en distintas"; fi
done

# 5. Mac: sin construcciones incompatibles con bash 3.2 ------------------------
# (se ignoran los comentarios de cabecera que las nombran para prohibirlas)
if for f in "$HERE"/mac/*.command "$HERE"/mac/run-e2e-tests.sh; do
    grep -vE '^[[:space:]]*#' "$f" | sed 's/ #.*$//'
done | grep -nE '<\(|sort -V|-printf|readlink -f|stat -c|IGNORECASE' 2>/dev/null; then
    bad "mac-bash32" "construcción incompatible con bash 3.2 (ver arriba)"
else
    ok "mac-bash32"
fi

# 6. Windows: regresiones conocidas -------------------------------------------
for f in win/FreeCAD-stable.ps1 win/FreeCAD-weekly.ps1; do
    if tr -d '\r' < "$HERE/$f" | grep -nE '` +$' >/dev/null; then
        bad "win-backtick $f" "espacio tras backtick de continuación"
    fi
done
ok "win-backtick (sin espacios tras backtick)"
# A1: el estable distingue del weekly por regex (el patrón de -Filter es grueso)
if grep -q "DIR_REGEX = '\^FreeCAD_\[0-9\]'" "$HERE/win/FreeCAD-stable.ps1" \
   && grep -q 'Get-BundleDirs' "$HERE/win/FreeCAD-stable.ps1"; then
    ok "win-a1-patron-numerico"
else
    bad "win-a1-patron-numerico" "el estable no distingue el canal del weekly"
fi
# Ningun -Filter debe llevar clases [] (en NTFS son literales; el lab las acepta)
if grep -nE -- "-Filter +'[^']*\[" "$HERE"/win/*.ps1 2>/dev/null; then
    bad "win-filter-sin-corchetes" "-Filter con [] (el proveedor NTFS no lo soporta)"
else
    ok "win-filter-sin-corchetes"
fi
# M1: el sidecar nunca se lee con Invoke-WebRequest en memoria
if grep -n 'Invoke-WebRequest.*SHA256\|SHA256.*\.Content' "$HERE"/win/*.ps1 2>/dev/null; then
    bad "win-m1-sidecar" "lectura de sidecar en memoria (bug gzip)"
else
    ok "win-m1-sidecar"
fi
# M2: fail-closed presente en ambos productos
for f in win/FreeCAD-stable.ps1 win/FreeCAD-weekly.ps1; do
    tr -d '\r' < "$HERE/$f" | grep -q 'sidecar unavailable' || bad "win-m2-failclosed $f" "falta rama fail-closed"
done
ok "win-m2-failclosed"
# Balanceo de llaves/paréntesis/corchetes (tras quitar strings y comentarios)
if python3 - "$HERE" <<'PYEOF'
import re, sys
base = sys.argv[1]
bad = 0
for f in ['win/FreeCAD-stable.ps1', 'win/FreeCAD-weekly.ps1']:
    t = open(f'{base}/{f}', encoding='utf-8-sig').read()
    c = re.sub(r"'[^']*'", "''", t)
    c = re.sub(r'"[^"]*"', '""', c)
    c = re.sub(r'(?m)^\s*#.*$', '', c)
    for a, b in [('{', '}'), ('(', ')'), ('[', ']')]:
        if c.count(a) != c.count(b):
            print(f'FAIL balance {f}: {a}{c.count(a)} vs {b}{c.count(b)}')
            bad = 1
sys.exit(bad)
PYEOF
then ok "win-balance"; else bad "win-balance" "ver arriba"; fi

# 7. --help es/en sin efectos (no toca red ni disco) ---------------------------
for lang in es en; do
    for f in linux/FreeCAD-stable.sh linux/FreeCAD-weekly.sh \
             mac/FreeCAD-stable.command mac/FreeCAD-weekly.command; do
        if LC_ALL="$lang" LC_MESSAGES="$lang" LANG="$lang" \
                bash "$HERE/$f" --help 2>/dev/null | head -1 | grep -q 'FreeCAD AutoUpdater Scripts v0.8.6'; then
            ok "help-$lang $f"
        else
            bad "help-$lang $f" "cabecera SUITE/VERSION ausente"
        fi
    done
done

printf 'RESULT pass=%s fail=%s\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
