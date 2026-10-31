# Revisión externa del proyecto (recomendaciones para la IA que lo mantiene)

> Revisión hecha sobre el estado del 2026-10-12 (suite v0.8.5, `[Unreleased]`).
> Alcance: los 6 scripts de producto, los 2 runners E2E, `Diag-Download.ps1`
> (el runner y el diag de Windows se retiraron al cerrar su E2E, 2026-10-12),
> los 5 documentos de `docs/`, los READMEs, `CHANGELOG.md`, `CONTRIBUTING.md`,
> `LICENSE`, `.gitignore` y `media/`. Los logs E2E de `win/` se leyeron para
> verificar las afirmaciones.

## Aplicación (2026-10-12)

Aplicado casi todo, en este orden operativo (difiere del sugerido por
motivos prácticos: `git init` primero como red de seguridad, y B2 antes de
editar para que los diffs sean legibles):

- [x] A1 (patrón numérico + filtro `.part`), B1 (ARM64), M3 (atómico), M1
  (diag a fichero), M2 (fail-closed ×6 + `DISENO.md` §7), B5 (`manual()`),
  B6 (`.7zr.exe`), B3 (WebM, plantillas, `OWNER/REPO`), B4 (`leeme.txt` →
  `docs/AUDITORIA.md`), B2 (normalización verificada), P1 (`git init` +
  commit pristine + commit de cambios; **sin remoto**: pendiente `git
  remote add` + push), P3 (`tests/smoke.sh` sin fallos + shellcheck 0.11
  limpio + `.github/workflows/ci.yml`
  sin probar hasta el primer push).
- [~] B3-cifras: **pendiente** unificar las cifras de tests entre
  README/CHANGELOG/PORTABILIDAD (los arneses de lab originales se perdieron
  con `/tmp`; el smoke nuevo es el sustituto versionado).
- [ ] P2 (núcleo compartido): decisión estratégica, no aplicada.
- [x] P4 (campo, Windows): la 9.ª corrida (2026-10-11 → 10-12) repitió el
  `-Todo` con el `win/` actual (`product-sha` `b3a453d5…` / `cbfc93ee…`) →
  **21/0 y 21/0** (skip=0) en las completas: cubre A1 (instala/desinstala
  solo la carpeta de su canal), M2 (sidecar aplicado) y M3 (install
  atómico), además de `.lnk` + asociación (ya en la 8.ª). **Mac sigue
  pendiente** (otro agente: Intel parcial, Apple Silicon sin probar). No
  cortar `[0.8.5]` hasta cerrar Mac.
- Nota: las referencias a líneas de `win/*.ps1` de este documento son
  **pre-normalización (B2)**; el contenido es el mismo con ~50% menos líneas.
- Autorevisión (mismo día): se pilló un fallo propio. La primera versión de
  A1 metió `[0-9]` en un `-Filter` (no válido en NTFS; el pwsh del lab sí lo
  acepta), que habría roto el estable en Windows real. Corregido a
  `-Filter` grueso + `Where-Object` regex (`Get-BundleDirs`), con un test
  nuevo en `smoke.sh` que prohíbe `[]` en cualquier `-Filter`. Lección: el
  lab (pwsh en Linux) no reproduce las semánticas del proveedor del
  filesystem de Windows; desconfiar de `-Filter` y de `[]`.

## Veredicto

Proyecto **muy por encima de la media** para una utilidad de este tipo: diseño
portable/autocontenido coherente, degradación elegante, i18n es/en, misma CLI
en los 6 scripts y una disciplina documental excelente (el informe del
`sha256 mismatch` por gzip en `Invoke-WebRequest` de 5.1 es ejemplar). El
estado es de **candidato a release**, no de release: Windows 5.1 real está
**completo en verde** (9.ª corrida: 21/0, skip=0, con `.lnk` + asociación y
los cambios de esta revisión), pero Mac no ha visto hardware real (Intel en
curso con otro agente, Apple Silicon sin probar).

Los puntos de abajo van por severidad. Cada uno indica **dónde** y **cómo**.

---

## Altos

### A1. Patrón cruzado de canales en Windows

- **Dónde:** `win/FreeCAD-stable.ps1:41` → `$Script:DIR_PATTERN = 'FreeCAD_*-Windows-*'`.
- **Problema:** captura también la carpeta del weekly. Linux es estricto
  (`FreeCAD_[0-9]*-Linux-*`) y el weekly de Windows es específico
  (`win/FreeCAD-weekly.ps1:41` → `'FreeCAD_weekly-*-Windows-*'`), pero el
  estable de Windows no. Consecuencias si ambos canales comparten carpeta:
  1. `Get-LatestLocal` devuelve el binario *weekly* (ordena después de los
     nombres numéricos), así que `--no-update` en el estable arranca el
     FreeCAD weekly.
  2. La comparación "¿al día?" (`$local.Name -like "*${tag}-Windows-..."`)
     nunca cuadra → descarga permanente.
  3. `Install-FromArchive` y `Do-Uninstall` borran **todas** las carpetas
     `FreeCAD_*-Windows-*` (`:760`, `:1217`) → un canal desinstala al otro.
  4. `Do-Uninstall` del estable borra `.FreeCAD_*.part` (`:1220`), que puede
     ser la descarga en curso del weekly.
- **Arreglo:** que el estable distinga solo las carpetas numéricas. **Ojo:**
  `-Filter` solo entiende `*` y `?`; una clase `[0-9]` en `-Filter` sería
  literal en NTFS (aunque el pwsh del lab, en Linux, la interpreta como
  clase: el bug pasaría el lab y fallaría en Windows real). Por eso el
  patrón de `-Filter` se deja grueso (`'FreeCAD_*-Windows-*'`) y el fino va
  en un `Where-Object { $_.Name -match '^FreeCAD_[0-9]' }` (centralizado en
  un helper `Get-BundleDirs`). Repasar los usos (`Get-LatestLocal`,
  `Install-FromArchive`, `Do-Uninstall`, `--reinstall`) y el filtro `.part`.
  Decidir y **documentar** si los canales comparten carpeta (la README lo
  afirma para Linux; en Windows no estaba garantizado).

---

## Medios

### M1. `Diag-Download.ps1` reintroduce el bug gzip ya corregido

- **Dónde:** `win/Diag-Download.ps1:21` lee el sidecar con
  `Invoke-WebRequest ... .Content` en memoria, el mismo transporte que se
  quitó del producto por devolver bytes gzip (`exp=52/57`) en 5.1.
- **Impacto:** en una máquina 5.1 puede reportar "NO COINCIDE → la red/AV
  altera los bytes" de forma falsa, justo cuando más se necesita el
  diagnóstico.
- **Arreglo:** usar el mismo `Get-UrlText` (HttpClient) o descargar el sidecar
  a fichero y leerlo con `Get-Content -Raw`.

### M2. Verificación SHA256 *fail-open*

- **Dónde:** `linux/FreeCAD-stable.sh:590`, `linux/FreeCAD-weekly.sh:479`,
  `win/FreeCAD-stable.ps1:1121`, `win/FreeCAD-weekly.ps1:...`, y equivalentes
  de Mac.
- **Problema:** solo se rechaza si `exp` no está vacío. Si el sidecar no se
  puede descargar, el ejecutable se instala **sin verificar**, contra la
  promesa de la sección "Seguridad" de `DISENO.md` ("si falla el checksum,
  nunca se toca la versión existente").
- **Arreglo:** fail-closed cuando falta el hash esperado (abortar con aviso
  claro), o como mínimo un aviso ruidoso + entrada de log explícita. Debatir
  el compromiso: fail-closed endurece la seguridad pero rompe la degradación
  "sin red sigo arrancando lo local"; se puede permitir instalar solo si ya
  hay versión local válida (nunca la primera vez).

### M3. Instalación no atómica en Windows

- **Dónde:** `Install-FromArchive` (`win/FreeCAD-stable.ps1:~726-790`).
- **Problema:** extrae a `tmp`, **borra** las carpetas viejas y luego
  `Move-Item`; si el move falla, te quedas sin ninguna versión. Linux verifica
  el `.part` y solo entonces `mv` (más seguro).
- **Arreglo:** mover la versión nueva a su destino (o a un nombre temporal)
  **antes** de borrar las viejas; borrar las antiguas solo tras confirmar el
  `FreeCAD.exe` en el destino final.

---

## Bajos / consistencia

### B1. ARM64 Windows con mensaje engañoso

- `win/FreeCAD-stable.ps1:31-39` mapea `ARM64` a `$Script:ARCH='ARM64'` (no
  vacío → pasa el guard de `:1450`), pero no existe build ARM64. El usuario ve
  "Could not check the latest version (offline?)" en vez de "arquitectura no
  soportada". Rechazar `ARM64` explícitamente con su mensaje.

### B2. `.ps1` de producto doble-espaciados

- `win/FreeCAD-stable.ps1`: 1556 líneas, **824 en blanco** (53%);
  `win/FreeCAD-weekly.ps1`: 1544/818; `win/Diag-Download.ps1`: 54/28. El
  runner sí va denso. Es un artefacto de generación; inofensivo, pero dificulta
  la revisión y delata falta de relectura. Normalizar el formato (una sola
  pasada de "unir blancos duplicados") y no reintroducirlo.

### B3. Documentación con referencias rotas

- `media/demo.webm` no existe: `README.md:56` y `README_ES.md:58` (o se añade
  el WebM o se quita la frase).
- `CONTRIBUTING.md` remite a "issue templates" que no existen: no hay
  `.github/`. Crear `.github/ISSUE_TEMPLATE/` o quitar la frase.
- URLs placeholder `OWNER/REPO` en `CHANGELOG.md:127-128`.
- Cifras de tests dispersas e incoherentes entre `README`/`CHANGELOG.md`/
  `PORTABILIDAD.md` (22/22 vs 18/18 vs 20/20...). Fijar una cifra por
  plataforma+canal y usarla en todas partes.

### B4. Auditoría IA pegada en un fichero de usuario

- `mac/leeme.txt:58-73` incluye una "Auditoría hecha con IA" que le dice al
  auditor lo que *debe* concluir ("la conclusión tiene que ser 'instalador
  benigno'"). Un documento que intenta dirigir a un revisor es en sí mismo un
  problema. Mover esas notas a un doc interno (`docs/`) y dejar `leeme.txt`
  como guía del voluntario.

### B5. `man()` en el runner de Mac

- `mac/run-e2e-tests.sh:64` define `man()` (ensombrece el comando del
  sistema) — el mismo patrón que en Windows se renombró a `Manual`. Renombrar
  por coherencia.

### B6. Detalles menores

- `win/Do-Uninstall` no borra el extractor `$Script:SEVENZR` (`.7zr.exe`).
- Sin GUI, `ask_yesno` devuelve "no" y deja marca `.no-shortcut`/`.no-assoc`
  permanente (opt-out silencioso en sistemas sin kdialog/zenity).
- `.gitignore`: `*.AppImage.zs-old` parece resto; `.no-shortcut` no encaja con
  el patrón `.no-*-shortcut`.

---

## Proceso e ingeniería (los cambios de mayor impacto a largo plazo)

### P1. Es un proyecto sin control de versiones

`git status` falla: no hay repo, historial, remoto ni ramas, aunque el flujo
documenta Keep a Changelog/SemVer. `git init`, primer commit, y a partir de
ahí commits pequeños por arreglo. Es la mejora con mejor relación
esfuerzo/beneficio.

### P2. Duplicación: 6 copias mantenidas a mano

Cada plataforma es una copia independiente de ~730-780 líneas. El bug del
gzip hubo que corregirlo en varios sitios; el patrón cruzado (A1) nace de esa
duplicación. Opciones, de menos a más ambiciosa:
1. Mantener la separación pero con una **checklist de paridad** y tests que
   cubran cada plataforma.
2. **Núcleo compartido**: extraer la lógica de decisión (versión, asset, URL,
   checksum, backup, i18n) a una especificación única y generar/stubear.
3. Reimplementar en un solo lenguaje (p. ej. Python) que lance en los tres
   SO, colapsando los 6 scripts en 1-2. Reduce el mantenimiento a una fracción
   a cambio de perder el "cero dependencias" de Mac/Windows.

### P3. Los runners E2E son "desechables" y no hay CI

`win/E2E-RunTests.ps1` y `mac/run-e2e-tests.sh` son el activo de ingeniería
más valioso, pero se documentan para borrarse, y los "40/40" de Linux no
existen en el repo. Conservarlos, añadir CI (shellcheck + parser PowerShell +
modo rápido de los E2E) y versionar el arnés de Linux.

### P4. Validación en campo pendiente

- Windows: ejecutar el `-Todo` con el runner reordenado (ya hecho) para
  cubrir por fin `.lnk` real y asociación, y confirmar `full-install`/
  `full-uninstall` en verde.
- Mac: la checklist de `docs/E2E-macos.md` en un Mac Intel real; Apple Silicon
  sin probar.
- No cortar `## [0.8.5]` en el CHANGELOG hasta cerrar A1, M1-M3 y esta
  validación.

---

## Orden sugerido de trabajo

1. A1 (patrón Windows) y M1 (diag) — son bugs reales, arreglo pequeño.
2. M2 (checksum fail-closed) y M3 (instalación atómica) — decisiones de
   seguridad/robustez a documentar en `DISENO.md`.
3. `git init` (P1) y arreglar B3/B4.
4. Normalizar formato de los `.ps1` (B2) y P3 (CI + versionar runners).
5. Cerrar validación de campo (P4) y entonces cortar `[0.8.5]`.
