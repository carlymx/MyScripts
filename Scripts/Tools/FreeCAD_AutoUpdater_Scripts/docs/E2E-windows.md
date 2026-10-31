# Validación E2E en Windows 11 real

> **Estado: cerrado.** Este documento queda como registro del procedimiento.
> El runner `win/E2E-RunTests.ps1` y `win/Diag-Download.ps1` se retiraron al
> terminar el E2E de Windows; los resultados están en `PORTABILIDAD.md` §5
> (9.ª corrida: 21/0, skip=0). El runner de macOS (`mac/run-e2e-tests.sh`)
> sigue vigente hasta cerrar su validación (`docs/E2E-macos.md`).

Los `.ps1` están validados en laboratorio (ver `PORTABILIDAD.md`). Este
checklist cubre las ramas que solo existen en Windows, ejecutadas por el
runner desechable `win/E2E-RunTests.ps1` (se borra al terminar el proyecto).
El runner se guía solo: te dice en pantalla qué hacer en cada momento.

## Flujo (3 pasos)

1. Abre PowerShell en la carpeta `win/` (tiene que tener escritura).
2. Ejecuta UN comando (hace las 4 pasadas seguidas; las completas descargan
   ~2 GB cada una entre producto y banco de métodos, instalan y desinstalan
   solas — tarda varios minutos, déjalo trabajar):
   ```powershell
   powershell -ExecutionPolicy Bypass -File E2E-RunTests.ps1 -Todo
   ```
   - En la pasada 1 aparece una ventana de pregunta: haz clic en **Sí**.
   - Cuando pregunte si viste un aviso de Windows, pulsa **S** o **N**
     (fíjate si aparecen: rectángulo, normalmente abajo a la derecha).
   - Los 4 ficheros `E2E-RESULT-*-windows.log` se guardan solos (con fecha;
     no se sobrescriben).
   - Solo para repetir una pasada aislada:
     ```powershell
     powershell -ExecutionPolicy Bypass -File E2E-RunTests.ps1 -Channel weekly -Auto
     ```
3. Repite en español y en inglés (Ajustes → Idioma; reinicia sesión), trae
   de vuelta a Linux los 4 ficheros `E2E-RESULT-*.log` y borra la carpeta
   de prueba en Windows.

## Qué valida el runner (ver `RESULT` al final de cada log)

`PASS/FAIL` por punto: mensajes es/en, toast (te pregunta si lo viste),
diálogo (clic o timeout), `tar.exe`/7-Zip disponible, lock, descubrimiento
de versión con red real (`product-sha` anota qué fichero se probó),
descarga con verificación + banco de 5 métodos (ver abajo), acceso `.lnk` (crea y quita) + asociación
`.FCStd` en HKCU con pregunta propia (crea y quita), backup con config
de mentira (no toca tu config),
update real + desinstalación real (solo pasadas completas).

## Diagnóstico de descarga (solo si falla el checksum)

Si las pasadas completas fallan con `sha256 mismatch`, ejecuta en la misma
carpeta (descarga ~400 MB con `curl.exe` y compara con el sidecar):

```powershell
powershell -ExecutionPolicy Bypass -File Diag-Download.ps1
```

- `COINCIDE` → el fallo está en el método de descarga del script.
- `NO COINCIDE` → la red/antivirus de la máquina altera los bytes.
Trae el `RESULTADO` de vuelta. (Script desechable: se retira al cerrar el
diagnóstico.)

## Banco de métodos (corre solo en las pasadas completas)

Cada pasada `-Full` descarga el asset 6 veces (1 producto + 5 métodos) y
verifica cada descarga con el sidecar (`PASS/FAIL method-*` en el log +
`methods-best=` con los que verifican, o `none`):

1. `m1-httpclient`: el propio producto (HttpClient con progreso y reintentos).
2. `m2-webclient`: `System.Net.WebClient` (otra pila .NET).
3. `m3-iwr`: `Invoke-WebRequest -OutFile`.
4. `m4-bits`: `Start-BitsTransfer` (servicio de Windows).
5. `m5-curl`: `curl.exe -L` (externo, directo y efectivo).

Para correr SOLO el banco (sin instalar nada, sin clics):

```powershell
powershell -ExecutionPolicy Bypass -File E2E-RunTests.ps1 -Channel stable -Methods
```

Con el ganador se montará la cadena de reserva del producto (y se cubrirán
por fin el `.lnk` real y la pregunta de asociación).

## Compatibilidad 5.1

El runner anota la versión en `INFO ps=` (debe ser 5.1.xxxxx) y avisa si
no lo es. Comprobación manual:

```powershell
$PSVersionTable.PSVersion
```
