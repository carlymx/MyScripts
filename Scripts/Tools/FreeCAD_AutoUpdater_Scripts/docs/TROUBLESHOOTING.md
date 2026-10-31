# Solución de problemas: arranques lentos y cuelgues de FreeCAD

Si FreeCAD tarda mucho en arrancar, la ventana principal o los menús aparecen
tarde, o se cierra solo al cabo de un rato, la causa más probable es una
**configuración de usuario dañada** (`~/.config/FreeCAD/`). Suele ocurrir si
FreeCAD se cierra de forma abrupta (`kill -9`, apagado, cuelgue) mientras
estaba escribiendo sus ficheros `.cfg`.

## Síntomas típicos de una configuración dañada

- La splash de FreeCAD sí sale, pero la ventana principal tarda en aparecer.
- Una vez abierta, menús y botones tardan en renderizar (el viewport 3D luego
  va normal).
- En casos graves: `System parameter file couldn't be opened` y `Continue
  with an empty configuration that won't be saved`, con esperas de decenas de
  segundos dentro de FreeCAD.
- Puede terminar en crash (`SIGABRT` en `libFreeCADGui`).

## Diagnóstico (5 pasos)

```bash
# 1) Log del script: qué pasó en cada arranque (updated / up to date / fix)
tail -30 ~/AppImages/FreeCAD/.freecad-stable.log

# 2) Journal del usuario: busca los mensajes clave de config rota
journalctl --user --since today | grep -E 'system.cfg|empty configuration|Discard'

# 3) ¿Ha habido crash?
coredumpctl list | tail -5

# 4) Estado de la config (estable: v1-1/  ·  weekly: v26-3/)
ls -la ~/.config/FreeCAD/
#   system.cfg y user.cfg deben existir y ser XML legible

# 5) Descartar descargas colgadas o versiones raras
~/AppImages/FreeCAD/FreeCAD-stable.sh --check
ls ~/AppImages/FreeCAD/*.part 2>/dev/null   # no debe haber nada
```

Si el paso 2 muestra `Failed to access file for reading: .../system.cfg` o
`Continue with an empty configuration`, el problema es la config: ve a
Recuperación.

## Recuperación desde el backup automático

Cada lanzamiento de los scripts guarda un backup de `~/.config/FreeCAD` (ver
"Copias de seguridad de la configuración" en el README). Para restaurarlo:

```bash
# 1) Cerrar FreeCAD (¡ningún proceso 'freecad' vivo!)
pgrep -a freecad

# 2) Restaurar el backup más reciente del canal usado
mv ~/.config/FreeCAD ~/.config/FreeCAD.roto   # la rota se conserva por si acaso
tar -xzf ~/AppImages/FreeCAD/.cfg-backup-stable/freecad-cfg-AAAA-MM-DD-HHMMSS.tar.gz \
    -C ~/.config/

# 3) Arrancar y verificar
~/AppImages/FreeCAD/FreeCAD-stable.sh --check
```

(Sustituye `.cfg-backup-stable` por `.cfg-backup-weekly` si usas el semanal;
el contenido es el directorio `FreeCAD/` completo, así que restaura la config
de ambos canales a la vez.)

## Empezar con una configuración limpia

Si no hay ningún backup útil, basta renombrar el directorio para que FreeCAD
recrie una config limpia al arrancar:

```bash
pgrep -a freecad                        # asegurar que no hay instancias
mv ~/.config/FreeCAD ~/.config/FreeCAD.roto
~/AppImages/FreeCAD/FreeCAD-stable.sh   # recria la config
```

Se pierden preferencias y posiciones de ventanas, pero no documentos (están
en `~/Documentos` y en `~/.local/share/FreeCAD/`).

## Buenos hábitos

- **No mates FreeCAD con `kill -9`** si sospechas que está guardando:
  ciérralo con la X o con Ctrl+C en la consola desde la que lo lanzaste.
- Tras un crash, revisa `coredumpctl list` y el estado de los `.cfg` con los
  pasos de arriba antes de nada más.

## Resumen rápido

| Sospecha | Cómo descartarla en 10 s |
|---|---|
| Red/GitHub lenta | `FreeCAD-stable.sh --check` → si responde en < 2 s, no es la red |
| Fix de libdrm / preload | Arranca igual con y sin el fix (ver log: `libdrm fix: ...`) |
| Config dañada | `journalctl --user \| grep -E 'system.cfg\|empty configuration'` |
| Crash | `coredumpctl list \| tail` |
