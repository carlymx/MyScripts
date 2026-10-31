# DISEÑO - FreeCAD Weekly / Stable en Linux (scripts todo en uno)

Documento de diseño y referencia de `linux/FreeCAD-weekly.sh` y
`linux/FreeCAD-stable.sh`.
Pensado para entender qué hacen los scripts, por qué toman cada decisión y qué
mejoras quedan pendientes.

> Los ports a Windows (`win/`) y macOS (`mac/`) replican esta CLI y semántica;
> sus diferencias están en [PORTABILIDAD.md](PORTABILIDAD.md).

## 1. Objetivo

Dos ficheros de shell, con la misma estructura y las mismas opciones, que
descargan, instalan, actualizan y ejecutan AppImage de FreeCAD en Linux con un
solo clic y sin depender de la versión instalada en el sistema:

| Script | Canal | Patrón local | Última versión |
|---|---|---|---|
| `FreeCAD-weekly.sh` | Desarrollo | `FreeCAD_weekly-*-Linux-<arch>*.AppImage` | feed Atom → `weekly-AAAA.MM.DD` |
| `FreeCAD-stable.sh` | Estable | `FreeCAD_[0-9]*-Linux-<arch>*.AppImage` | API GitHub `releases/latest` (fallback: Atom) |

Ambos pueden vivir en la misma carpeta: patrones, logs, bloqueos, iconos y
accesos de menú tienen nombres distintos.

Los seis scripts (Linux, Windows y macOS, ambos canales) comparten las
globales `VERSION="0.8.6"` y `SUITE="FreeCAD AutoUpdater Scripts"`, que la
ayuda (`--help`) muestra como cabecera.

Está pensado para **KDE Plasma** (usa `kdialog` + `qdbus`), con reserva para
`zenity` en otros entornos.

## 2. Flujo de ejecución

1. Detecta la arquitectura (`x86_64` / `aarch64`) y construye el patrón del
   fichero (ver tabla de la sección 1).
2. Consulta la última release de su canal:
   - **Weekly**: feed `releases.atom` → última etiqueta `weekly-AAAA.MM.DD`.
   - **Estable**: API `api.github.com/.../releases/latest` (una llamada; te da
     `tag_name` y la URL exacta del asset, cuyo sufijo puede variar,
     p. ej. `-py311`). Solo se aceptan tags `X.Y.Z` puros y assets
     `FreeCAD_<número>...` (si `latest` devolviera un `rc`/`weekly-*` se
     descarta). Si la API falla (rate limit, red), fallback al feed
     Atom tomando el primer tag con forma `X.Y.Z` pura y probando los candidatos
     `FreeCAD_<tag>-Linux-<arch>-py311.AppImage` y
     `FreeCAD_<tag>-Linux-<arch>.AppImage` con `curl -fsIL`.
3. Compara con la versión local. Si ya está al día, no hace nada más.
4. Si hay una versión nueva (o no hay ninguna local):
   - Muestra una ventana de estado (con retardo anti-parpadeo de 1,5 s).
   - Descarga el AppImage con barra de progreso.
   - Verifica el **SHA256** contra el fichero `-SHA256.txt` del release.
   - Sustituye de forma atómica y **borra la versión anterior**.
5. En el primer uso, pregunta si crear un **acceso en el menú de inicio**
   (con `-y`/`--yes` se crea sin preguntar) y si **asociar los `.FCStd`**
   (sección 4b; desactivado por defecto, como buen portable).
6. Aplica la detección del fix libdrm (sección 3) y ejecuta el AppImage con
   los argumentos que haya recibido.

## 3. Detección del problema de libdrm (workaround)

Contexto: los AppImage de FreeCAD de la serie 1.1.x incluyen su propia
`libdrm` (2.4.125, de conda-forge). En sistemas con **Mesa >= 26.2**, el
driver del host (`libgallium` / `radeonsi`) espera símbolos que esa libdrm
antigua no exporta (`amdgpu_va_manager_init2`,
`amdgpu_va_manager_query_sw_info`). El resultado es `Could not initialize GLX`
y el cierre del programa. Es el issue
[#32061](https://github.com/FreeCAD/FreeCAD/issues/32061); la solución upstream
es el [PR #33005](https://github.com/FreeCAD/FreeCAD/pull/33005), que **borra
`libdrm*.so*` del bundle** (mergeado el 28/09/2026, presente desde
`weekly-2026.09.30`; aún no llega a las releases estables).

El fix, en ambos scripts, consiste en forzar las libdrm del sistema con
`LD_PRELOAD` (`libdrm.so.2`, `libdrm_amdgpu.so.1`, `libdrm_intel.so.1`,
`libdrm_radeon.so.1` y `libdrm_nouveau.so.2` si existen), y se aplica **solo
en el `exec` final**, no a todo el script, para no afectar a `curl`,
`kdialog`, etc. La condición la decide cada canal:

### 3.1 Weekly: regla por fecha (sin inspección)

- La fecha está en el nombre del fichero, así que no hace falta abrir el
  AppImage (coste cero).
- Si `tag_local < 2026.09.30` **y** el host exporta los símbolos en
  `libdrm_amdgpu.so.1` (buscado en `/usr/lib64`, `/usr/lib`,
  `/usr/lib/x86_64-linux-gnu`, `/usr/lib/aarch64-linux-gnu`) → fix.
- En otro caso (incluido el nombre no reconocido, de forma conservadora) se
  decide solo por el host.
- Los weeklies `>= 2026.09.30` no llevan libdrm activa en el bundle: no se
  aplica nada.

### 3.2 Estable: cascada con inspección del AppImage

Cacheada en `.freecad-stable.fix` como `<nombre-del-AppImage>:<0|1>`; se
recalcula cuando cambia el nombre (es decir, con cada versión nueva):

1. **Caché**: si coincide el nombre exacto, se usa el valor guardado.
2. **Host**: si `libdrm_amdgpu.so.1` del sistema no exporta los símbolos, no
   hay nada que arreglar → `0` (y se cachea).
3. **Inspección** (requiere `unsquashfs` con soporte de `-o`, squashfs-tools
   >= 4.5):
   - `off=$(AppImage --appimage-offset)` y `unsquashfs -ll -o "$off"`: se
     listan los ficheros, **sin extraer nada** (~2 s solo la primera vez).
   - Solo cuentan los módulos reales `libdrm.so*` / `libdrm_<x>.so*` bajo
     `usr/lib{,64}` que **no** estén en `usr/__clobbers__/` (ahí guarda
     conda copias que no se cargan; un `grep libdrm` a ciegas daría falso
     positivo en los weeklies) ni ser plugins (`libdrm-egl-server.so`).
   - Sin libdrm activo → `0`.
   - Con libdrm activo: se hace `unsquashfs -cat` del `libdrm_amdgpu.so*`
     (unos 56 KB, a un pipe, sin escribir en disco) y se buscan los símbolos.
     Presentes → `0`; ausentes → `1`.
4. **Fallback conservador**: sin `unsquashfs`, sin soporte de `-o` o con
   cualquier fallo → `1` (el `LD_PRELOAD` es inocuo si no hacía falta).

`-v` y `.freecad-stable.log` dejan constancia de qué rama se usó (caché,
inspección o precaución).

## 4. Acceso en el menú de inicio

- Ruta: `~/.local/share/applications/freecad-weekly.desktop`.
- Si no existe y no hay marca `.no-shortcut`, se pregunta al usuario.
- Si acepta, se obtiene el icono:
  1. Extrayéndolo del AppImage (`--appimage-extract 'org.freecad.FreeCAD.svg'`).
  2. Si falla, descargándolo del repositorio.
  3. Si falla, usando el icono de tema `freecad`.
- El icono se guarda como `freecad-weekly.svg` (nombre propio, para no pisar el
  icono que pueda usar la versión estable).
- Si rechaza, se crea la marca `.no-shortcut` y no se vuelve a preguntar.
- El acceso **no** incluye asociación de tipos (como buen portable).

## 4b. Asociación de archivos `.FCStd` (pregunta propia)

- En el primer arranque, después del acceso, se pregunta aparte (`ask_assoc`).
- Si acepta: se reescribe el `.desktop` con
  `MimeType=application/x-extension-fcstd;` y se marca como predeterminado
  con `xdg-mime default` (reserva `gio mime`).
- Si rechaza: marca `.no-assoc` y no se vuelve a preguntar.
- `--associate` / `--remove-assoc` lo cambian después; `--uninstall` lo
  revierte (quita el `MimeType` y limpia `mimeapps.list` solo de nuestro id).

## 5. Opciones

| Opción | Efecto |
|---|---|
| (ninguna) | Comprueba/actualiza y ejecuta |
| `--no-update` | Ejecuta sin comprobar actualizaciones |
| `--check` | Solo comprueba si hay versión nueva (no descarga) |
| `--reinstall` | Borra la local y vuelve a descargar la última |
| `--create-shortcut` | Crea el acceso al menú |
| `--remove-shortcut` | Elimina el acceso al menú |
| `--associate` | Asocia los `.FCStd` (abrir con doble clic) |
| `--remove-assoc` | Quita la asociación de `.FCStd` |
| `--uninstall` | Desinstala (AppImage, acceso, asociación, icono, log) |
| `-y`, `--yes` | No preguntar (asumir sí) |
| `-v`, `--verbose` | Trazas en la terminal |
| `-h`, `--help` | Ayuda |
| `--` | Todo lo siguiente se pasa a FreeCAD |

Nota: `--help` sin `--` muestra la ayuda del script; para la de FreeCAD hay que
usar `FreeCAD-weekly.sh -- --help`. Las opciones son idénticas en
`FreeCAD-stable.sh`.

## 6. Archivos que genera (junto al script)

Las opciones son las mismas en ambos scripts; cambian los nombres para que
puedan convivir:

| Fichero | Weekly | Estable |
|---|---|---|
| Versión instalada | `FreeCAD_weekly-AAAA.MM.DD-Linux-<arch>.AppImage` | `FreeCAD_<X.Y.Z>-Linux-<arch>*.AppImage` |
| Icono | `freecad-weekly.svg` | `freecad-stable.svg` |
| Registro | `.freecad-weekly.log` | `.freecad-stable.log` |
| Bloqueo | `.freecad-weekly.lock` | `.freecad-stable.lock` |
| Marca "no crear acceso" | `.no-shortcut` | `.no-stable-shortcut` |
| Marca "no asociar .FCStd" | `.no-assoc` | `.no-stable-assoc` |
| Caché del fix libdrm | — (fecha en el nombre) | `.freecad-stable.fix` |
| Copia de configuración | `.cfg-backup-weekly/freecad-cfg-*.tar.gz` (máx. 3, guard 10 min) | `.cfg-backup-stable/freecad-cfg-*.tar.gz` (máx. 3, guard 10 min) |
| Descarga temporal | `.$ASSET.part` | `.$ASSET.part` |

Además crea/edita `~/.local/share/applications/freecad-weekly.desktop` o
`.../freecad-stable.desktop`.

## 7. Decisiones de diseño

- **Autocontenido**: todo vive junto al script; mover la carpeta mueve la
  instalación. El acceso del menú apunta a la ruta absoluta del script, así que
  si se mueve hay que recrearlo (`--create-shortcut`).
- **Idioma automático**: español si `LC_ALL`/`LC_MESSAGES`/`LANG` empieza por
  `es`, si no inglés.
- **Ventana única con retardo anti-parpadeo**: si la comprobación termina en
  menos de 1,5 s y no hay nada que hacer, no se muestra ninguna ventana.
- **Seguridad**: si falla la red, la descarga o el checksum, nunca se toca la
  versión existente; se arranca la que haya. El checksum es *fail-closed*:
  si el sidecar `-SHA256.txt` no se puede descargar, la actualización se
  aborta y no se instala nada sin verificar (queda en el log como
  `sha256 sidecar unavailable`); solo se llega a ese punto tras descargar
  algo nuevo, así que sin red se sigue arrancando la versión local.
- **Sin `set -e`**: se controlan los errores de forma explícita para que un
  fallo no deseado no aborte el arranque.

## 8. Posibles mejoras futuras

- `--doctor`: informe de sistema (distro, kernel, GPU, Mesa, libdrm, símbolo,
  FUSE, kdialog/qdbus, red) para pegar en un issue.
- Validar la integridad del AppImage local (magia ELF/AppImage) y re-descargar
  si está corrupto; limpiar `.part` huérfanos.
- Reanudar descargas interrumpidas (`curl -C -`) y comprobar espacio libre.
- Fallback de FUSE: si falta `libfuse2`, arrancar con
  `APPIMAGE_EXTRACT_AND_RUN=1`.
- Validar/recrear el `.desktop` si apunta a una ruta inválida.
- Rollback: retener la versión anterior y permitir `--rollback`.
- Timer `systemd --user` para comprobar actualizaciones en segundo plano.
- Self-update del propio script.

## 9. Compatibilidad

- Linux x86_64 y aarch64.
- Probado en Fedora Kinoite/Bazzite con KDE Plasma, Wayland y GPU AMD
  (Mesa 26.x, libdrm 2.4.13x).
- Requiere `curl`. Para la ventana de progreso usa `kdialog` + `qdbus`
  (KDE) o `zenity`; las notificaciones usan `notify-send`.
- `FreeCAD-stable.sh` usa `unsquashfs` (squashfs-tools >= 4.5, con `-o`) para
  inspeccionar el AppImage; es **opcional**: si falta o falla, el fix de
  libdrm se aplica por precaución.
- Los AppImage necesitan FUSE (libfuse2). Si no está disponible, el AppImage
  puede requerir `APPIMAGE_EXTRACT_AND_RUN=1` (mejora futura).
