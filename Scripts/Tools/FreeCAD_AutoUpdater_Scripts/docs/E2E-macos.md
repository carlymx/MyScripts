# Validación E2E en Mac real

Los `.command` están validados en laboratorio (ver `PORTABILIDAD.md`). Este
checklist cubre las ramas que solo existen en macOS, ejecutadas por el runner
desechable `mac/run-e2e-tests.sh` (se borra al terminar el proyecto).

## Datos previos (salida de estos comandos, para el log)

```sh
uname -m                  # p. ej. x86_64 (Intel) o arm64
sw_vers -productVersion    # p. ej. 15.1
ls ~/Library/Preferences/FreeCAD 2>/dev/null   # tras abrir FreeCAD una vez
id -Gn | grep -q admin && echo admin || echo no-admin
```

## Flujo (3 pasos)

1. Copia la carpeta `mac/` a una carpeta con escritura y dale permiso:
   `chmod +x FreeCAD-*.command run-e2e-tests.sh`.
   **Primer arranque:** macOS bloqueará los ficheros (desarrollador no
   identificado) → clic derecho → *Abrir* → *Abrir* (una vez por fichero).
2. Ejecuta UN comando (hace las 4 pasadas seguidas; las completas descargan
   ~700 MB cada una, instalan y desinstalan solas — tarda varios minutos,
   déjalo trabajar; si una completa falla hace diagnósticos extra):
   ```sh
   ./run-e2e-tests.sh --todo
   ```
   - En la pasada 1 aparece un diálogo de pregunta: haz clic en **Sí**.
   - Cuando pregunte si viste un aviso, pulsa **S** o **N** (fíjate si
     aparecen: arriba a la derecha).
   - Los 4 ficheros `E2E-RESULT-*-macos.log` se guardan solos (con fecha;
     no se sobrescriben).
   - Solo para repetir una pasada aislada:
     ```sh
     ./run-e2e-tests.sh weekly --auto
     ```
   - El runner se guía solo en español o inglés según el Mac. Para probar
     ambos idiomas, repite con el otro (Ajustes → Idioma y región;
     reinicia sesión al cambiarlo).
3. Trae de vuelta a Linux los 4 ficheros `E2E-RESULT-*.log` y borra la
   carpeta de prueba en el Mac.

## Qué valida el runner (ver `RESULT` al final de cada log)

`PASS/FAIL` por punto: mensajes es/en (+`AppleLanguages`), notificación
(te pregunta si la viste), diálogo (clic o timeout), herramientas del
sistema, lock con reclaim de PID muerto, descubrimiento de versión con red
real (incluida la elección del `.dmg` según tu macOS; `product-sha` anota
qué fichero se probó), descarga con verificación, acceso del Escritorio
(crea y quita) + asociación `.FCStd` (vía registro; con `duti` se omite
por seguridad), backup con config de mentira (no toca tu config),
instalación real (destino, marcador, cuarentena, limpieza del montaje) +
desinstalación real (solo pasadas completas). Si una completa falla, corre
el banco de métodos (ver abajo).

## Banco de métodos (diagnóstico, solo si hace falta)

Si una pasada completa falla, el runner descarga el `.dmg` con 4 métodos
y verifica cada descarga con el sidecar (`PASS/FAIL method-*` en el log +
`methods-best=` con los que verifican, o `none`):

1. `m1-producto`: el propio producto (`fetch_file`: curl con progreso).
2. `m2-curl`: curl plano (mismo transporte, sin maquinaria de progreso).
3. `m3-rangos`: 4 segmentos por rangos HTTP en varias conexiones +
   concatenado (SKIP si el servidor no da `Content-Length`).
4. `m4-python3`: urllib de python3 (otra pila TLS/HTTP; SKIP si no hay
   python3).

Para correr SOLO el banco (sin instalar nada, sin clics):

```sh
./run-e2e-tests.sh stable --methods
```

Validado en laboratorio contra servidor local con rangos (8 MiB + sidecar):
4/4 `ok` y el negativo (fichero corrupto) da `mismatch`.

## Notas

- El progreso de descarga se ve en la ventana de Terminal (las `.command`
  siempre abren Terminal al hacer doble clic).
- **Diálogos y osascript:** cada `display dialog`/`display notification`
  debe ir en **un solo `-e`**. Con varios `-e` osascript los une con saltos
  de línea y AppleScript parte el `display dialog` (el `with title` se lee
  como `with timeout`) → error `-2741` y ninguna ventana. Descubierto en
  Mac real (macOS 11); si tocas estos diálogos, mantén un `-e` por
  invocación.
- Apple Silicon (arm64) queda sin probar: la lógica es idéntica salvo el
  nombre del `.dmg`, pero conviene repetir esta lista en un M1/M2 cuando
  haya ocasión.
