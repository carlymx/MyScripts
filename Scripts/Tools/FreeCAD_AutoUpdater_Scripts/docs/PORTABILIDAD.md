# Plan de portabilidad: scripts FreeCAD Stable/Weekly → Windows y macOS

> **Estado:** en implementación (Windows primero). Fecha: 2026-10-10.
> **Origen:** `linux/FreeCAD-stable.sh` (704 líneas) y `linux/FreeCAD-weekly.sh` (590 líneas).
> Datos de releases verificados contra la API de GitHub el 2026-10-10
> (estable `1.1.4`, weekly `weekly-2026.10.01`).
>
> **Decisiones tomadas (2026-10-10):** ① Windows primero, macOS después.
> ② Formato `.7z` portable. ③ Carpeta autocontenida junto a los scripts
> (igual que en Linux). ④ La reorganización `linux/|win/|mac/` es estética:
> lo desplegado en `AppImages/FreeCAD/` no se toca. ⑤ Extracción en cascada
> automática (`tar.exe` → `7z` instalado → descarga `7zr.exe` portable).
> ⑥ Pruebas: `pwsh` portable en Linux para la lógica + Wine para humo +
> checklist diferido en Win11 dual-boot; Mac Intel con un amigo (sin fecha).

---

## 1. Inventario de características y funciones actuales

### 1.1. Ficha de los scripts

| | `FreeCAD-stable.sh` | `FreeCAD-weekly.sh` |
|---|---|---|
| Fuente de versión | API GitHub `releases/latest` + respaldo feed Atom | Feed Atom (`weekly-AAAA.MM.DD`) |
| Formato que gestiona | `FreeCAD_X.Y.Z-Linux-{arch}-py311.AppImage` | `FreeCAD_weekly-FECHA-Linux-{arch}.AppImage` |
| Detección fix libdrm | Cascada con caché: caché → host → inspección del bundle con `unsquashfs` | Solo por fecha del nombre (`FIX_CUTOFF=2026.09.30`), sin caché |
| Caché `.fix` | Sí (`.freecad-stable.fix`) | No |
| Resto | Idéntico | Idéntico |
| Versión / suite | `VERSION="0.8.6"`, `SUITE="FreeCAD AutoUpdater Scripts"` (cabecera del `--help`) | Idem en los 6 scripts |

### 1.2. Funciones, una por una

| Función | Qué hace | Clave para el port |
|---|---|---|
| Constantes de rutas | Todo vive junto al script (`HERE`): binario, icono, `.log`, `.lock`, marcas `.no-*-shortcut`, `.no-*-desktop`, `.no-*-assoc`, caché `.fix`, backups `.cfg-backup-*/` | Diseño "autocontenido/portable": replicable tal cual en ambas plataformas |
| `LANG_CODE` + `t()` | Detección `LC_ALL→LC_MESSAGES→LANG`, `es*`→es, resto→en; ~25 claves duplicadas es/en | Portable 1:1 (PowerShell: `(Get-Culture)`; macOS: `$LANG`/`AppleLanguages`) |
| `log()` | Añade al `.log` con fecha; eco a stderr solo con `--verbose`; rota a 300 líneas al pasar de 500 | Portable 1:1 |
| `notify()` | `notify-send` si existe, silencioso si no | Win: toast WinRT sin módulos; Mac: `osascript display notification` |
| `latest_local()` | Busca el binario local por patrón y se queda con el mayor (`sort -V`) | Misma lógica con `Get-ChildItem`/glob |
| `get_release()` / `get_latest_tag()` | Stable: 1 llamada a la API + parseo; filtra tags `X.Y.Z` puros; respaldo Atom con candidatos `py311`/sin `py311`. Weekly: primer `weekly-Fecha` del Atom | La lógica es reutilizable; **los nombres de asset cambian por plataforma** (ver §2) |
| `ask_yesno()` | `kdialog --yesno`, reserva `zenity`, si no hay ninguno → asume "no" | Win: `MessageBox`; Mac: `display dialog` de AppleScript |
| `detect_fix()` + `host_libdrm_new()` | Problema exclusivo Linux+Mesa/AMD: inspecciona libdrm del bundle vs sistema, decide `LD_PRELOAD`, cachea por versión | **No portable: se elimina** (no existe ese problema en Win/Mac; ver §3.2) |
| `dlg_start/set/close()` | Progreso kdialog vía DBus+qdbus, reserva zenity con FIFO; modos `busy` y `progress` con MiB | Sin equivalente directo: Win → `Write-Progress`/WinForms; Mac → notificaciones + diálogo modal (sin barra nativa) |
| `get_icon()` | Extrae el `.svg` del AppImage o lo descarga del repo | Win: el `.exe` ya lleva icono (el `.lnk` apunta al actualizador y toma ese icono); Mac: el `.app` ya lleva icono. **Se simplifica** |
| `create/remove/maybe_create_shortcut()` | `.desktop` en `~/.local/share/applications` + `update-desktop-database` + marca opt-out | Win: `.lnk` al actualizador (`powershell -File`) en Inicio (HKCU, sin admin); Mac: enlace en el Escritorio al `.command` (migra el formato anterior `*.app`) |
| `set/remove/maybe_assoc()` (.FCStd con pregunta propia) | `MimeType` en el `.desktop` + `xdg-mime default` (reserva `gio`) + marca opt-out; al quitar se limpia `mimeapps.list` (solo nuestro id) | Win: claves HKCU `.fcstd`→ProgID (sin admin); Mac: `duti -s` con UTI leída del bundle (vía `python3`+`plistlib`) si existe `duti`, si no registro en `lsregister` (solo sale en Abrir con, no predeterminado) |
| `backup_config()` | `tar.gz` de `~/.config/FreeCAD`, guard 10 min, rotación a 3 copias, fallos silenciosos | Win: `Compress-Archive` de `%APPDATA%\FreeCAD` (nativo); Mac: mismo `tar` |
| `update_*()` | Lock `flock` → check en 2.º plano con diálogo si tarda → compara tag → descarga a `.part` con progreso → verifica SHA256 (`<url>-SHA256.txt`) → `chmod +x`, mueve, **borra versiones viejas** (solo queda 1), invalida caché, notifica | Flujo portable íntegro; cambia: lock (Mutex/`mkdir`), descarga (BITS/HttpClient; `curl` en Mac), instalación (extraer `.7z` / montar `.dmg`) |
| `do_check()` | Solo informa (notificación + stdout), no descarga | Idem |
| `do_uninstall()` | Pide confirmación, borra binario, `.part`, acceso, icono, log, lock, marcas. **No borra la configuración ni los backups** (supervivencia deliberada) | Misma semántica |
| `show_help()` + 12 flags | `--no-update --check --reinstall --create-shortcut --remove-shortcut --associate --remove-assoc --uninstall -y -v -h` + `--` para pasar args a FreeCAD (`%F` del `.desktop` incluido) | Misma CLI (paridad); matiz Mac: el paso de ficheros a un `.app` va por Apple Events, no por argv |
| Guards de arranque | Arquitectura soportada → `curl` presente → carpeta escribible | Win: `curl.exe` existe de serie pero se recomienda HttpClient; Mac: `curl`/`shasum`/`hdiutil` de serie |
| Lanzamiento final | `exec` (reemplaza el proceso) con o sin `LD_PRELOAD` | Win: `& FreeCAD.exe @args`; Mac: `open -a` o binario dentro del `.app` |

### 1.3. Detalles finos que el port debe respetar

- Solo existe **una versión instalada** a la vez (las viejas se borran al actualizar).
- El backup de config es previo al arranque, como máximo 1 cada 10 min, máximo 3 copias, y **sobrevive a `--uninstall`**.
- Sin red o sin checksum disponible: se usa la versión local (degradación elegante, nunca se queda sin arrancar si hay binario).
- Descarga a fichero `.part` y solo se mueve al sitio al verificarse (nunca hay binario a medias como "actual").

---

## 2. Qué publica FreeCAD por plataforma (verificado vía API)

### 2.1. Estable 1.1.4 (`FreeCAD/FreeCAD/releases/latest`)

| Plataforma | Assets | Notas |
|---|---|---|
| Windows x86_64 | `FreeCAD_1.1.4-Windows-x86_64-py311-installer.exe` (519 MB) y `...-py311.7z` (418 MB) | **No hay build ARM64** → el guard de arquitectura debe rechazarlo con mensaje. Instalador NSIS (`/S` silencioso). Firmado por el proyecto |
| macOS arm64 / x86_64 | `FreeCAD_1.1.4-macOS-arm64-py311.dmg`, `FreeCAD_1.1.4-macOS-x86_64-py311.dmg` | Ambas arch. Firmados. Mínimo macOS 12 |
| Linux | AppImage x86_64/aarch64 | Lo actual |

### 2.2. Weekly-2026.10.01 (viven en el repo principal; el tag `weekly-builds` del repo Bundle está **congelado desde mayo-2026** como histórico)

| Plataforma | Assets | Notas |
|---|---|---|
| Windows x86_64 | `FreeCAD_weekly-2026.10.01-Windows-x86_64-installer.exe` y `...-Windows-x86_64.7z` | **Ojo: sin infijo `-py311`** (difiere del estable) → no construir la URL a ciegas |
| macOS | `...-macOS10-x86_64.dmg`, `...-macOS11-arm64.dmg`, `...-macOS15-arm64.dmg` | **El nombre incrusta la versión de macOS (10/11/15)**: hay que descubrir el asset vía API, no por candidatos |
| Linux | AppImage x86_64/aarch64 | Coincide con lo que el script ya construye |

### 2.3. Conclusiones para el diseño

- Todos los assets traen sidecar `<fichero>-SHA256.txt` → el paso de verificación se porta 1:1.
- Los nombres varían por canal y plataforma → el port debe usar **descubrimiento por API** (como ya hace el stable) en lugar de construir URLs por candidatos.
- Los weeklies de macOS probablemente no estén notarizados → prever `xattr -dr com.apple.quarantine` y documentarlo.
- Alternativas nativas: existe `winget install --id FreeCAD.FreeCAD` (solo estable, manifiesto comunitario que puede ir rezagado) y `brew install --cask freecad` (solo estable 1.1.4). Ninguna cubre weeklies, ni pinnea versión, ni respalda la configuración, ni es portable → **el script sigue teniendo valor** frente a ellas.

### 2.4. macOS 11 (Big Sur) y anteriores: versión compatible fija 1.0.2

FreeCAD 1.1+ usa **Qt 6.8**, que exige **macOS 12 Monterey o superior**: en
Big Sur instala pero **crashea al arrancar** (FreeCAD/FreeCAD#28392). El
intento upstream de publicar builds con Qt 6.7 para macOS 11 se abandonó
(FreeCAD/FreeCAD#27384) y el repo `FreeCAD/Unsupported-Releases`, creado
para builds no soportadas, está **vacío**. La última versión que corre en
Big Sur es **1.0.2** (Qt 5.15): assets
`FreeCAD_1.0.2-conda-macOS-{x86_64,arm64}-py311.dmg` (nótese el `-conda-`
en medio del nombre) con su sidecar `-SHA256.txt`.

Decisión: los ports de macOS detectan la versión con `sw_vers` y, si el
major es **< 12**, fijan el tag a **1.0.2** (en ambos canales) en vez de
buscar la última, avisando al usuario. Gancho de prueba `FC_SW_VERS` y
campo `legacy-mac=` en el runner E2E.

---

## 3. Matriz de portabilidad (función × plataforma)

### 3.1. Funciones portables o adaptables

| Función Linux | Windows (PowerShell 5.1) | macOS (zsh; evitar bashismos 4.x porque `/bin/bash` es 3.2) | Veredicto |
|---|---|---|---|
| Detectar arch (`uname -m`) | `$env:PROCESSOR_ARCHITECTURE` (AMD64/ARM64) | `uname -m` (arm64/x86_64) | ✅ Directo |
| Detectar versión (API JSON / feed Atom) | `Invoke-RestMethod` + `ConvertFrom-Json`; feed con regex | Mismo `curl`+`grep`/`sed` actual | ✅ Directo |
| Descarga con progreso | `HttpClient` con callback o `Start-BitsTransfer` + `Write-Progress` | Mismo `curl` actual | ✅ Adaptar |
| Verificar SHA256 | `Get-FileHash -Algorithm SHA256` (nativo) | `shasum -a 256` (de serie) | ✅ Directo |
| "Instalar" nueva versión | Extraer `.7z` portable (recomendado: espejo del diseño actual) o `installer.exe /S`; se borra la carpeta vieja | `hdiutil attach`, `cp -R FreeCAD.app`, `detach`; se borra el `.app` viejo | ✅ Adaptar |
| Lanzar + pasar args/`%F` | `& ...\FreeCAD.exe @FcArgs` | Binario en `FreeCAD.app/Contents/MacOS/` o `open -a --args` (verificar ficheros por argv; el doble-clic va por Apple Events y funciona solo) | ⚠️ Adaptar con 1 verificación |
| Acceso menú + icono | `.lnk` al actualizador vía `WScript.Shell` en Inicio de HKCU (sin admin) + icono del exe si hay versión instalada | Enlace en el Escritorio al `.command` (doble clic = Terminal); el icono ya viene en el bundle | ✅ Más simple que en Linux |
| Asociación `.FCStd` (pregunta propia, off por defecto) | Claves HKCU `.fcstd`→ProgID (sin admin), reversible | `duti` si está (predeterminado real); si no, `lsregister` (Abrir con); al desinstalar no se puede restaurar el predeterminado previo | ⚠️ Degradación honesta sin `duti` |
| Notificaciones | Toast WinRT con XML (sin módulos) | `osascript -e 'display notification'` | ✅ Adaptar |
| Preguntas sí/no | `MessageBox` | `display dialog ... buttons {"No","Sí"}` | ✅ Directo |
| Barra de progreso | `Write-Progress` o mini-form WinForms | Sin barra nativa: diálogo modal "Descargando…" + notificaciones al terminar | ⚠️ Degradación aceptada y documentada |
| Log + rotación | `Add-Content` + recorte (mismo patrón) | Mismo patrón actual | ✅ Directo |
| Lock anti-doble-update | `Mutex` o `FileStream` exclusivo | `mkdir` atómico (no hay `flock` en macOS) | ✅ Adaptar |
| Backup config | `Compress-Archive` de `%APPDATA%\FreeCAD`, guard 10 min, rotación a 3 | Mismo `tar` sobre `~/Library/Preferences/FreeCAD` + `~/Library/Application Support/FreeCAD` (verificar rutas en máquina destino) | ✅ Adaptar |
| i18n es/en | `(Get-Culture).Name -like 'es*'` + función `t()` espejo | Cadena `LC_ALL→LANG` + `AppleLanguages` como respaldo | ✅ Directo |
| CLI de 10 flags + `--` | `param()` espejo | Mismo bucle `case` | ✅ Directo |

### 3.2. Funciones que se eliminan (solo tienen sentido en Linux)

- **Fix libdrm + `LD_PRELOAD` + inspección `unsquashfs`**: problema exclusivo de Mesa/radeonsi en Linux. En Windows los drivers son de usuario y en macOS el bundle Qt/Metal no admite ese parche → se elimina sin sustituto.
- **`.desktop` + `update-desktop-database` + kdialog/zenity + `flock`**: sustituidos por los equivalentes de la tabla §3.1.

### 3.3. Vehículo recomendado (cómo empaquetar los scripts)

- **Windows:** `win/FreeCAD-stable.ps1` / `win/FreeCAD-weekly.ps1` (`#Requires -Version 5.1`, sin sintaxis PS7) + lanzador `.cmd` para doble-clic (un `.ps1` solo abre el Bloc de notas; el `.cmd` invoca `powershell -ExecutionPolicy Bypass -File`, sin tocar la política del sistema).
- **macOS:** `mac/FreeCAD-stable.command` / `mac/FreeCAD-weekly.command` en bash 3.2 (doble-clic abre Terminal; todo lo necesario —`curl`, `shasum`, `hdiutil`, `osascript`, `tar`— viene de serie, cero dependencias). Un solo fichero por canal cubre Intel y ARM (`uname -m`).

### 3.4. Layout verificado de los `.7z` (inspección real, 2026-10-10, SHA256 OK)

- Estable: carpeta raíz `FreeCAD_1.1.4-Windows-x86_64-py311/`, ejecutable en
  `<raíz>/FreeCAD.exe` (lanzador de 129 KB; el binario real está en `bin/`).
- Weekly: carpeta raíz `FreeCAD_weekly-2026.10.01-Windows-x86_64/`, ejecutable en
  `<raíz>/FreeCAD.exe` (misma estructura).
- Sin `.ico` propio en la raíz (solo el icono incrustado en el exe) → el `.lnk`
  apunta su icono al propio `FreeCAD.exe`.
- Regla de implementación: no asumir la ruta; localizar `FreeCAD.exe` en la
  raíz extraída con búsqueda (raíz primero, luego recursiva) y fallar con
  mensaje si no aparece.

### 3.5. Layout verificado del `.dmg` (inspección real, 2026-10-10, SHA256 OK)

- `FreeCAD_1.1.4-macOS-x86_64-py311.dmg` contiene una carpeta `FreeCAD/` con
  `FreeCAD.app` dentro (no en la raíz del montaje) y el binario en
  `FreeCAD.app/Contents/MacOS/FreeCAD`.
- Regla de implementación: buscar `FreeCAD.app` hasta 3 niveles bajo el punto
  de montaje, copiar a `/Aplicaciones` (o `~/Aplicaciones` sin admin) con
  nombre estable por canal (`FreeCAD Stable.app` / `FreeCAD Weekly.app`),
  quitar cuarentena con `xattr`, guardar el tag en `.freecad-*.version` y
  borrar el `.dmg` (la `.app` es el programa; el `.dmg` solo ocupa ~700 MB).
- Config en macOS: `~/Library/Preferences/FreeCAD/` (`system.cfg`,
  `user.cfg`; la app la recrea si falta) → objetivo del backup (los datos y
  addons de `~/Library/Application Support/FreeCAD/` se excluyen, igual que
  `~/.local/share/FreeCAD` en Linux).

---

## 4. Resumen final de portabilidad

1. **Veredicto: portable al ~85-90 %.** Toda la lógica de negocio (detección de versión, descarga, verificación SHA256, reemplazo atómico, backup con rotación, log, i18n, CLI, desinstalación) se traslada tal cual; solo la capa de sistema (~10-15 %: AppImage, libdrm, `.desktop`, kdialog/zenity, `flock`, `unsquashfs`) se sustituye por equivalentes nativos o se elimina con justificación técnica.
2. **Windows es el port más fiel** si se usa el `.7z` portable: mismo modelo "carpeta autocontenida junto al script", mismo reemplazo de versión única, `Compress-Archive`/`Get-FileHash`/`MessageBox`/toast cubren todo sin dependencias.
3. **macOS es el port más simple de instalar** (el `.dmg`+`.app` ya resuelve icono, acceso y asociación), pero con dos degradaciones honestas: sin barra de progreso nativa y posible fricción de Gatekeeper en weeklies sin notarizar (`xattr`, a verificar en máquina real).
4. **Riesgos que exigen máquina real** (desde Linux no se pueden validar): nombres futuros de assets weekly de macOS (variante `macOS10/11/15`), flag `/S` del instalador NSIS, paso de ficheros por argv a la app (ambas plataformas), ruta exacta de config en `%APPDATA%` (la de `~/Library/Preferences` está verificada por documentación y queda confirmar en el checklist), comportamiento del toast/AppleScript/Gatekeeper en versiones actuales del SO, y primer arranque del `.command` sin firmar.
5. **Esfuerzo estimado:** 2 scripts de ~500-650 líneas por plataforma + arnés de pruebas en VM/máquina real (matriz idioma × arquitectura × canal, como el actual de 12 tests). La paridad de flags y de semántica de `--uninstall` (config y backups sobreviven) debe mantenerse.

---

## 5. Decisiones (resueltas 2026-10-10) y estado

1. ~~¿Implementamos, y qué plataforma primero (Windows o Mac)?~~ → **Windows primero**; macOS después (probador externo con Mac Intel, sin fecha).
2. ~~En Windows: ¿`.7z` portable o `installer.exe`?~~ → **`.7z` portable** (espejo del diseño actual).
3. ~~¿Carpeta portable o ubicación convencional?~~ → **Carpeta junto al script**; lo desplegado en Linux no se toca.

Estado: `win/` implementado y validado en laboratorio (2026-10-10) y **en
campo en Windows 11 (9.ª corrida, 21/0)**. `mac/` implementado y validado en
laboratorio (2026-10-10); pendiente checklist E2E en Mac Intel (probador
externo, sin fecha) y Apple Silicon sin probar.
Cifras canónicas vigentes: `tests/smoke.sh` = **33 comprobaciones con
shellcheck / 28 sin él**; E2E Windows = **rápidas 10/0, completas 21/0 por
canal**; E2E Mac = pendiente. Las cifras de las corridas de laboratorio de
más abajo (`22/22`, `18/18`, `20/20`, `10/10`…) son de arneses ya retirados
(sustituidos por `tests/smoke.sh`).

Validación `win/` (2026-10-10): parser PowerShell 0 errores;
PSScriptAnalyzer 0 errores (avisos de estilo revisados: `catch` vacíos
intencionados como en bash, verbos internos por paridad, sin ShouldProcess);
22/22 tests funcionales por canal bajo `pwsh` 7.6 en Linux (descubrimiento
contra la API real —estable `1.1.4`, weekly `weekly-2026.10.07`—, descarga
real de sidecar, instalación desde `.7z` sintético, lock, rotación de log y
backups, uninstall conservando backups); shellcheck limpio en `linux/`;
bundle 1.1.4 ejecutado bajo Wine 11 (`FreeCADCmd.exe --version` OK — Wine no
ejecuta PowerShell, así que los `.ps1` no son validables ahí). La validación
E2E en máquina real la hace `win/E2E-RunTests.ps1` v2 (desechable,
autoguiado: un solo comando `-Todo` hace las 4 pasadas, logs con fecha que
no se sobrescriben, `product-sha` en el log para verificar que el Windows
corre los ficheros vigentes, backup con config de mentira para no depender
de `%APPDATA%`; protocolo en `docs/E2E-windows.md`). El runner (y
`Diag-Download.ps1`) se retiraron al cerrar el E2E de Windows (9.ª corrida).

Primera corrida real Win11 (2026-10-11, PS 5.1.26100.9444, es-ES, runner
v2 `-Todo`, copias verificadas vigentes por `product-sha`): rápidas 9/1/4
y 9/1/4, completas 10/2/2 en ambos canales. PASS: `dialog-click`
(misterio del log v1 resuelto: la ventana funcionaba), `notify-seen`
(humano vio el toast), backup con config de mentira, `release` en ambos
canales con sus URLs, lock, archive, `tar.exe` presente sin 7-Zip,
`full-uninstall` (limpieza tras fallo OK). FAIL `fetch-small` (4/4 en la 1.ª corrida):
`[System.Net.Http.HttpClient]` no existe en 5.1 sin `Add-Type`
(assembly no cargado por defecto; en 7+ sí) → corregido con `Add-Type
-AssemblyName System.Net.Http` en ambos `.ps1`; en la 2.ª corrida el
error HttpClient desapareció (fix confirmado) y la descarga llega hasta
`Write-Progress`. De paso el runner pre-borra su `.part` (`OpenWrite` no
trunca y un resto largo + descarga corta falsearía el hash).
FAIL `full-install` (2/2) + prompt `Activity:` en pantalla: CAUSA RAÍZ
HALLADA con `Diag-Progress.ps1` (desechable, ya retirado): en PS
5.1.26100.9444, `Write-Progress -Id 1 -Completed` SIN `-Activity` pide el
parámetro por pantalla en vez de cerrar el registro; con `-Activity`
funciona (el propio diag: las líneas con Activity pasaron, `TITLE`
correcto). No era `(t title)` (inocente) ni shadowing (cmdlet genuino).
Fix: `-Activity (t title)` en los 8 cierres (4 por script: fin de
descarga, catch de descarga, fin de check, fin de verify).
2.ª corrida `-Todo` ES (2026-10-11, Win11 10.0.26200 tras reinicio):
CERO prompts, `fetch-small` PASS ×4 (descargas OK en 5.1), rápidas 10/0/4
×2, completas 11/1/2 ×2 con `full-install ok=False` SILENCIOSO en la
descarga grande (barra vista en vivo: 34/399 MiB; hashes `product-sha`
1EBEDC57…/46775AAF… = ficheros vigentes). Por la lentitud observada
(fibra 1 GB) se adelgazó la barra (solo refresca si cambia % o MiB) y el
runner vuelca `LAST_DL_ERROR` + cola del log + GB libres antes de
desinstalar (el uninstall borra las marcas y sin eso no hay post-mortem).
Ronda EN dispensada a petición del probador: las tablas es/en se
verifican en cada pasada (`t-es`/`t-en` PASS ×8) y el lab cubrió las
24-25 claves en ambos idiomas; solo cambia el default por `Get-Culture`
(una línea) y el idioma de la guía. Riesgo residual aceptado y anotado:
toast/diálogo en inglés no vistos en vivo.
Aviso checksum del probador (no es conducta de prueba: es la red de
seguridad funcionando): con longitud conocida se exige byte exacto y el
hash decide. Descartado: sidecar (una línea `hash *fichero`, sin BOM,
hash primero) y parser. Endurecido el borde de longitud desconocida
(`$null`→0 y mismo presupuesto de 100 micro-pausas que la ruta normal;
antes un corte prematuro se aceptaba tras la primera lectura): validado
en lab contra servidor local sin `Content-Length` (300.000 bytes
íntegros) + parser + rápidas OK. 3.ª corrida `-Todo` ES (2026-10-11, 10.0.26200): rápidas 10/0/4 ×2,
completas 11/1/2 ×2; post-mortem shipped dice: `last-dl-err` vacío
(descarga completa), `sha256 mismatch` a los ~10 s, 544 GB libres.
Descartado lado servidor: descargados en lab ambos `.7z`, cuadran con
sus sidecars (stable `4828741f…`, weekly `9d1165b5…`); pre-borrado del
`.part` intacto; parser `t()`/`Get-Command` inocentes. Causa pendiente
en el camino o la caja del probador (middlebox que transforma, caché
rancia del disco compartido E:, AV): determinista en 4/4. Prueba
decisiva pedida (sin scripts): bajar el `.7z` con el navegador a E: y a
C: y `Get-FileHash` de ambos.
El `.lock` residual es normal por diseño (el lock es el handle abierto,
`Unlock` lo cierra sin borrar el fichero; se reutiliza). Pendiente:
re-corrida E2E en Win11 (ES+EN) tras el fix.
4.ª corrida `-Todo` ES (2026-10-11, 10.0.26200) desde `C:` (NTFS, 118,5 GB
libres; copias vigentes por `product-sha`): MISMO `sha256 mismatch` en
ambos canales con `last-dl-err` vacío (rápidas 10/0/6 y 8/1/6, completas
11/1/4 y 10/2/4). REFUTADA la hipótesis del disco compartido E:/WinBtrfs:
en NTFS local falla idéntico y determinista (6/6 descargas grandes, ambos
canales, E: y C:). Aclarado: `fetch-small` solo valida el FORMATO del
sidecar (64 hex), no bytes de app; nada prueba descargas parciales buenas.
Nuevo FAIL `dialog-timeout` (obtenido=1) en las dos pasadas auto de esta
corrida (en la gemela de las 16:10 pasaba): flake del test, no del
producto (1 = botón OK; en auto nadie debía clicar). `.lnk` real + pregunta
de assoc siguen SIN cubrir (SKIP por no haber app instalada). TLS
autentica cada registro: si `$read==$total` y el hash falla, o el CDN
sirvió esos bytes (caché intermedia envenenada: proxy/AV con CA propia) o
algo los toca tras el `Close()`. Discriminante pedido (sustituye a la
prueba del navegador): `win/Diag-Download.ps1` (desechable, hoy retirado) baja el estable
con `curl.exe` y compara con el sidecar; si coincide, el culpable es
nuestro bucle HttpClient; si no, la caja/red del probador. De paso los
scripts ya anotan `exp/act` en el log ante mismatch (también los
`.command` de Mac, por paridad).
Banco de métodos en ambos runners (desechables): cada pasada completa
descarga el asset con N métodos y verifica cada uno contra el sidecar
(`method-*` + `methods-best=` en el log; modo standalone `-Methods` /
`--methods` sin instalar ni clicar). Windows (5, de más deseable a más
directo): m1 el propio producto (HttpClient+progreso+reintentos), m2
WebClient, m3 Invoke-WebRequest, m4 BITS, m5 curl.exe. Mac (4, monocultura
curl en stock): m1 el propio producto (`fetch_file`), m2 curl plano, m3 4
rangos+`cat`, m4 python3-urllib (SKIP sin python3/cont-length). Tráfico por
pasada completa: ~2 GB (win) / ~3,5 GB (mac). El banco de Mac está validado
en lab contra servidor local con rangos (4/4 ok + negativo mismatch). El de
Windows no se pudo validar aquí (sin pwsh): equilibrio de llaves/paréntesis
+ revisión contra los modismos del runner. Con el ganador se montará la
cadena de reserva del producto.
5.ª corrida `-Todo` ES en portátil Win11 (10.0.26200, 5.1.26100.8875,
212 GB libres, carpeta con espacios por SMB, copias idénticas por `cmp`):
TODO ROJO por 2 causas raíz. (1) Los `.ps1` de producto NO PARSEABAN (36
errores cada uno): líneas en blanco tras backtick de continuación
(`... } \`` + vacía + `| Select-Object` → EmptyPipeElement; idem en
`Remove-Shortcut` → cascada MissingEndParenthesis). Los contadores de
llaves/paréntesis no cazan esta clase; fix: colapsar 21 blancos por
fichero (la continuación se une con la línea real, semántica intacta).
(2) Bug latente del runner: `Man 'notify-seen'` invocaba al alias
`man`→`help` (en 5.1 el alias gana a la función); nunca se había ejecutado
porque la respuesta siempre fue S (aquí fue N); fix: renombrar a `Manual`.
Red de seguridad nueva: pwsh 7.6.6 instalado en el lab + parser real sobre
los 4 `.ps1` (0 errores) y corrida del runner en lab (quick 8/0/1/7;
`-Methods` con early-exit OK; los cuerpos Windows del banco siguen sin
probar hasta el portátil). Hashes nuevos (re-copiar `win/` entero):
stable `a332fe60…`, weekly `0861df06…`, runner `d6a078fa…`.
Revisión a fondo de `win/` tras la 5.ª corrida (pwsh 7.6.6 en el lab):
parser 0/0/0/0; PSScriptAnalyzer 80 avisos, todos de estilo aceptado
(catches vacíos deliberados, verbos propios por paridad Linux/Mac,
posicionales internos); sin funciones duplicadas dentro de ningún fichero
(stable/weekly paralelos por diseño); 0 espacios tras backtick o a final
de línea; los 8 cierres Write-Progress llevan -Activity; auditoría de
alias 5.1 limpia salvo `Man` (corregido); PowerShell no parte variables
con espacios (rutas con espacios OK en nativas y cmdlets); revisados a ojo
descarga, verificación, cascada de extracción, instalación, atajo, assoc
×3, peticiones, backup y update. Hallazgo menor: Diag con `-o $Dest`
sin comillas (citado por robustez). Nota de diseño (no bug): el `.lnk`
no refresca su icono si la app se instala después de crear el acceso.
6.ª corrida `-Todo` ES con los ficheros ya parseables (mismo equipo y
carpeta): rápidas 10/0 y 10/0 (notify S, dialog Sí, dialog-timeout OK);
completas 11/6 y 11/6. El banco corrió por fin: 0/5 en ambos canales,
`methods-best=none`, PERO con `bytes` exactos y `act=` igual al hash
upstream en los 5 métodos (incluidos curl.exe y BITS). Causa raíz: NO hay
corrupción de descarga; `Get-UrlText` leía el sidecar con
`Invoke-WebRequest` en memoria, que en 5.1 anuncia `Accept-Encoding:
gzip`, el CDN comprime el sidecar y `.Content` devuelve los bytes gzip sin
descomprimir (`exp=52/57`). `fetch-small` pasaba porque usa otra ruta
(HttpClient→fichero). Fix: `Get-UrlText` reimplementado con
`HttpClient.GetStringAsync` (validado en lab: devuelve el hash exacto,
parser 0, PSSA 80 sin cambios, quick 8/0/1/7); el runner avisa antes de
cada hash (`calculando sha256…`, minutos por fichero de 400 MB + Defender
en lectura). Hashes de producto NUEVOS (re-copiar `win/` entero).
Pendiente: repetir `-Todo` (se espera `methods-best` con ganadores +
installs en verde).
7.ª corrida `-Todo` ES con el fix gzip (mismo equipo, ps=5.1.26100.9444,
os=10.0.26300.0): rápidas 10/0 y 10/0; completas 17/0 y 17/0.
`methods-exp` ya es el hash de 64, 5/5 métodos PASS en ambos canales
(`methods-best` con los cinco), `updated to 1.1.4` /
`updated to weekly-2026.10.07`, uninstall limpio. Avisos
`calculando sha256…` visibles en terminal. Hashes vigentes:
stable `ef32c5f3…`, weekly `e81bd15c…`. Hueco detectado: atajo/asoc siguen
SKIP (ese bloque corría antes de instalar y la desinstalación no deja app
para la siguiente); fix solo-runner: bloque extraído a
`Test-ShortcutAssoc` y diferido tras `full-install` en `-Full` (rápidas y
`-Methods` intactos). Runner nuevo `50d9c02c…`. Validación en lab limitada
esta vez (`/tmp` se limpió y no hay pwsh): balanceo de llaves/paréntesis
OK + revisión. Pendiente: último `-Todo` para cubrir atajo/asoc en Windows
(cerrado por la 8.ª corrida).
8.ª corrida `-Todo` ES (mismo equipo, ps=5.1.26100.9444,
os=10.0.26300.0; 2026-10-11 22:10→22:41): rápidas 10/0 y 10/0; completas
**21/0 y 21/0** (skip=0). Cierra el hueco de la 7.ª: ya se ejecutan y pasan
`shortcut` / `assoc` / `assoc-remove` / `shortcut-remove`
(`FreeCAD Stable.lnk` y `FreeCAD Weekly.lnk` en Inicio, HKCU
`.fcstd`→`FreeCAD.Stable` / `FreeCAD.Weekly`), además de `full-install` +
`full-uninstall` en verde y los 5 métodos de descarga OK en ambos canales
(1.1.4 = 418088341 B; weekly = 356429567 B). Runner `50d9c02c…`.
**Ojo:** el `product-sha` de esta corrida es `ef32c5f3…` / `e81bd15c…`,
es decir los productos **pre-revisión** (idénticos a la 7.ª) → valida el
runner y el estado anterior, pero **no** los cambios de `REVISION-IA`. Hace
falta otra `-Todo` con el `win/` actual (stable `b3a453d5…`, weekly
`cbfc93ee…`) que cubra el install/uninstall por `Get-BundleDirs` y el
fail-closed (hecha en la 9.ª).
9.ª corrida `-Todo` ES (mismo equipo, ps=5.1.26100.9444, os=10.0.26300.0;
2026-10-11 23:39 → 2026-10-12 02:12): rápidas 10/0 y 10/0; completas
**21/0 y 21/0** (skip=0), esta vez con los productos **revisados**
(`product-sha` `b3a453d5…` / `cbfc93ee…`, idénticos al `win/` del repo) →
cierra el P4 de Windows. Valida A1 (instala/desinstala solo la carpeta de
su canal: `full-install` deja `FreeCAD_1.1.4-Windows-x86_64-py311` y
`FreeCAD_weekly-2026.10.07-Windows-x86_64`), M2 (`methods-exp` = hash de 64
y 5/5 métodos contra el banco; sin sidecar abortaría) y M3 (install
atómico). `shortcut created` / `assoc set` / `assoc removed` /
`shortcut removed` y `full-uninstall` en verde; 5 métodos OK en ambos
canales (1.1.4 = 418088341 B; weekly = 356429567 B); `free-gb` 212.6/213;
`dialog-click=Si` / `dialog-timeout=OK`. Runner `50d9c02c…`, diag
`6e9dcd5f…`.

Revisión externa aplicada (2026-10-12, `docs/REVISION-IA.md`): cambia
producto y hay que repetir el E2E desde cero (re-copiar `win/` entero;
**re-ejecutado en verde en la 9.ª corrida**).
Cambios: estable Win distingue del weekly por regex
(`Get-BundleDirs` = `-Filter 'FreeCAD_*-Windows-*'` + `Where-Object { $_.Name
-match '^FreeCAD_[0-9]' }`; **ojo:** `-Filter` solo entiende `*`/`?`, los
corchetes serian literales en NTFS aunque el pwsh del lab los interprete),
checksum fail-closed en los 6 scripts
(sin sidecar no se instala), `Install-FromArchive` atómico (aparta `.old` y
restaura si falla), `Diag-Download.ps1` (hoy retirado) lee el sidecar a
fichero con curl.exe (tenía el bug gzip), ARM64 rechazado con mensaje propio,
`--uninstall` borra `.7zr.exe`, `.ps1` normalizados (sin doble-espaciado),
`tests/smoke.sh` nuevo (sin fallos: 28 pruebas sin shellcheck y 33 con él;
bash -n, versión/suite, i18n 28/28 y
33/33, bash-3.2, regresiones A1/M1/M2, sin `-Filter` con corchetes,
balanceo, `--help` es/en) +
`.github/workflows/ci.yml` (sin probar hasta el primer push). Hashes nuevos:
stable `b3a453d5…`, weekly `cbfc93ee…`, runner `50d9c02c…` (sin cambios),
diag `6e9dcd5f…`. Las referencias a líneas de `REVISION-IA.md` en `win/`
son pre-normalización (B2).

Endurecimiento de descarga hallado por el E2E (2026-10-10): con red
inestable el cuerpo puede llegar vacío o a cero lecturas prematuras; la
descarga reintenta 3 veces con backoff, tolera hasta 100 lecturas a cero
consecutivas (200 ms) sin darlo por EOF, verifica con los bytes
leídos/escritos (`$read`, no con un segundo `stat`) y anota la causa en
`$LAST_DL_ERROR` + log. Causa raíz del hallazgo: en este laboratorio
`Get-Item … .Length` miente (0) sobre ficheros recién creados por .NET en
btrfs aunque `ls` muestra el tamaño real; por eso la verificación ya no
re-pregunta el tamaño al sistema.
Pasada de regresión tras el endurecimiento (2026-10-10): PSScriptAnalyzer 0
errores en los 3 `.ps1` y 18/18 tests por canal (i18n, args, install,
uninstall, backups, log, save+hash de contenido).

Validación `mac/` (2026-10-10): `bash -n` + shellcheck limpios, escaneo de
incompatibilidades con bash 3.2 limpio (sin sustitución de procesos,
`sort -V`, `find -printf`, `readlink -f`, `stat -c`, `IGNORECASE`); 20/20 y
21/21 tests funcionales en estable y weekly bajo bash en Linux con stubs
darwin (`hdiutil`, `osascript`, `sw_vers`, `defaults`, `stat -f`, `xattr`):
cobertura i18n es/en + `AppleLanguages`, ayuda, CLI, lock con reclaim de PID
muerto, rotación de log y backups, descubrimiento contra la API real
(estable `1.1.4`, weekly `weekly-2026.10.07`), matriz de elección de `.dmg`
(host 15→macOS15, host 12→macOS11, sin host→el mayor, Intel→macOS10),
descarga real de sidecar, instalación (fallback `~/Applications`, marcador,
cuarentena, limpieza del montaje), fallos de montaje/imagen vacía,
`ask Si/No`, atajos y uninstall conservando backups. Pasada de regresión
sobre los ficheros finales (2026-10-10): 10/10 y 11/11 en estable y weekly
(i18n, help, `AppleLanguages`, arch, rotaciones, release/tag en vivo,
pick-dmg). Runner E2E v2 (2026-10-11, paridad con Windows tras sus
lecciones): autoguiado bilingüe, modo `--todo` (4 pasadas con un comando),
logs con fecha que no se sobrescriben, `product-sha` en el log (las copias
renovadas se verifican), clic Sí→PASS, pregunta S/N del aviso, backup
siempre con config de mentira (sombrea `HOME`+`CFG_SRC`; no toca la config
real ni hace SKIP), pre-borrado del `.part`, post-mortem (cola del log +
GB libres con `df -k` portable) antes de desinstalar. Revisión pre-amigo
(2026-10-11, sin tocar la otra sesión más que esto): asociación `.FCStd`
nueva en producto validada en lab con stub `duti` (set/active/remove/
decline + degradación sin `duti`/`python3`); en E2E se salta con `duti`
presente (cambiaría su programa por defecto sin copia); `--associate`
notifica según modo; banco solo si falla el Full (no quemar GBs del
voluntario) + `--methods` aparte. Disparador validado en lab (Full sin
`hdiutil` → banco 4/4 con 720.059.196 bytes y hash OK + `free-gb`
numérico); `--associate` avisa según modo. Validado en lab con
stubs darwin: rápidas 13/0 y 14/0, `--todo` 4 logs (Full falla solo en
`full-install` por no haber `hdiutil` real —`no app in image`, post-mortem
visible—, uninstall limpia); shellcheck con solo los 2 SC2034 falsos
positivos conocidos (vars que consume el producto importado, igual que
v1); `bash -n` limpio. El descargador (`curl -fL --retry 2`, `.part`
pre-borrado) no necesitó cambios.

E2E real Mac Intel (2026-10-13, iMac x86_64, macOS 11.7.11, bash 3.2.57,
es-ES, `--todo`): 14/0/4, 14/1/4, 16/0/2, 15/1/2. Funciona de verdad:
instala y desinstala `/Applications/FreeCAD {Stable,Weekly}.app` (686/602
MiB, marcadores `1.1.4`/`weekly-2026.10.07`), elige bien el `.dmg` para
macOS 11 (`macOS10-x86_64`), i18n, aviso visto, lock, backup con config de
mentira, `free-gb` numérico. BUG DE PRODUCTO cazado por el E2E: las
ventanas `display dialog` NO salían en Mac real (solo un aviso de
osascript al respecto: `expected timeout or transaction ... (-2741)`).
Causa: el producto usaba `osascript` con VARIOS `-e`; osascript los une
con saltos de línea y AppleScript corta el `display dialog` en sentencias,
leyendo el `with title` como `with timeout`/`transaction` → error y cero
diálogos. Afectaba a `ask_yesno` (preguntas de primera vez del producto en
Mac: acceso y `.FCStd`), que nunca aparecían. FIX: un solo `-e` por
invocación (igual que `notify`, que sí funcionaba) en `ask_yesno` (ambos
canales) y en el diálogo auto del runner; `ASK_RAW` guarda la salida de
osascript para diagnóstico. Verificado en lab (stub que exige `-e` único):
rápidas 13/0 y 14/0, shellcheck limpio. Pendiente: re-confirmación rápida
del amigo. Apple Silicon sin probar.
