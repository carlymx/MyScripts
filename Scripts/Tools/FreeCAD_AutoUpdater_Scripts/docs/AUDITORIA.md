# Notas de seguridad (uso interno)

Movido desde `mac/leeme.txt` (2026-10-12): esto no es guía para el
voluntario, sino contexto para quien audite los scripts.

## Qué encontrará un revisor (todo legítimo)

- Descargan ejecutables de internet → pero solo de `github.com` (FreeCAD
  oficial; en Windows también de `7-zip.org`), y verifican SHA256 antes de
  instalar. Sin esa comprobación no se instala nada (fail-closed: si el
  sidecar `-SHA256.txt` no se puede descargar, la actualización se aborta).
- Quitan la cuarentena al `.app` (`xattr`) → es lo que hace que macOS lo abra
  en vez de bloquearlo; sin esto la app verificada no arrancaría. Es el punto
  que un revisor sin contexto podría marcar como "sospechoso" — con contexto,
  es procedimiento estándar.
- Tocan accesos directos y asociación `.FCStd` → solo a nivel de usuario, sin
  admin, y el desinstalador lo revierte todo.

## Lo que NO hay

Nada ofuscado ni codificado, ningún `eval`, nada que se ejecute desde red sin
guardar, ningún envío de datos fuera (solo descargas), sin contraseñas, sin
persistencia oculta.
