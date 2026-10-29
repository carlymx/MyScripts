# Kernel Switcher - Selector de Kernel GRUB

Script interactivo en Bash para gestionar el kernel de arranque por defecto en sistemas basados en Ubuntu/Debian con GRUB2.

## Características

- **Detección automática** de kernels instalados en `/boot`
- **Menú interactivo** con colores y navegación intuitiva
- **Submenús organizados**:
  - Cambiar kernel por defecto
  - Gestión de backups (crear, restaurar, listar)
  - Ver estado actual
- **Backups automáticos** antes de cada cambio
- **Backups manuales** con metadatos (fecha, kernel GRUB, kernel en uso)
- **Restauración selectiva** de backups con confirmación
- **Modo CLI** para automatización (`--auto`, `--list`, `--status`, `--restore`)
- **Compatible con sudo** (manejo correcto de stdin/stdout/stderr)

## Requisitos

- Ubuntu / Debian / derivados con GRUB2
- `sudo` para operaciones de escritura
- Bash 4.0+

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/carlymx/MyScripts.git
cd MyScripts/Scripts/Linux/kernel_switcher

# Dar permisos de ejecución
chmod +x cambiar-kernel-dinamico.sh

# Opcional: añadir al PATH
sudo ln -s "$(pwd)/cambiar-kernel-dinamico.sh" /usr/local/bin/kernel-switcher
```

## Uso

### Menú interactivo (recomendado)

```bash
sudo ./cambiar-kernel-dinamico.sh
```

```
=== MENÚ PRINCIPAL - Selector de Kernel GRUB ===
Kernel actual por defecto: Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-147-generic

1) Cambiar kernel por defecto
2) Backups (crear / restaurar / listar)
3) Ver estado actual
4) Salir
Elige una opción [1-4]: 
```

### Modo CLI (para scripts/automatización)

```bash
# Listar kernels disponibles
./cambiar-kernel-dinamico.sh --list

# Ver estado actual
./cambiar-kernel-dinamico.sh --status

# Cambiar kernel directamente (requiere sudo)
sudo ./cambiar-kernel-dinamico.sh --auto 6.8.0-147-generic

# Restaurar último backup automático (requiere sudo)
sudo ./cambiar-kernel-dinamico.sh --restore

# Ayuda
./cambiar-kernel-dinamico.sh --help
```

## Estructura de Backups

Los backups se guardan en `/var/backups/grub-kernel-selector/`:

```
grub.auto.20261027-153022.bak      # Backup automático (antes de cambios)
grub.auto.20261027-153022.bak.meta  # Metadatos
grub.manual.20261027-141510.bak     # Backup manual
grub.manual.20261027-141510.bak.meta
```

### Metadatos (`.meta`)

```ini
timestamp=20261027-153022
date=2026-10-27 15:30:22
grub_default=Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-147-generic
running_kernel=7.0.0-38-generic
type=auto
```

## Capturas del Menú

### Menú Principal
```
=== MENÚ PRINCIPAL - Selector de Kernel GRUB ===
Kernel actual por defecto: Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-147-generic

1) Cambiar kernel por defecto
2) Backups (crear / restaurar / listar)
3) Ver estado actual
4) Salir
Elige una opción [1-4]: 
```

### Seleccionar Kernel
```
--- SELECCIONAR KERNEL POR DEFECTO ---
Actual: Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-147-generic

1) Linux 6.14.0-37-generic
2) Linux 6.8.0-147-generic ★ (actual)
3) Linux 7.0.0-38-generic
4) Ubuntu (siempre el último kernel instalado)
5) ⬅ Volver al menú principal
Elige kernel [1-5]: 
```

### Gestión de Backups
```
--- GESTIÓN DE BACKUPS ---

1) Crear backup manual
2) Restaurar backup
3) Listar backups
4) ⬅ Volver al menú principal
Elige una opción [1-4]: 
```

### Listar Backups
```
--- BACKUPS DISPONIBLES ---
Nº  FECHA                 TIPO                 KERNEL GRUB                                    KERNEL EN USO    
------------------------------------------------------------------------------------------------------------------------
1   2026-10-27 15:30:22  auto                 Advanced options for Ubuntu>Ubuntu, with Linux 6.8.0-147-generic  7.0.0-38-generic 
2   2026-10-27 14:15:10  manual               Advanced options for Ubuntu>Ubuntu, with Linux 7.0.0-38-generic   7.0.0-38-generic 

Presiona Enter para continuar...
```

## Cómo funciona

1. **Detección**: Escanea `/boot/vmlinuz-*` para encontrar kernels instalados
2. **Entrada GRUB**: Construye la entrada exacta: `Advanced options for Ubuntu>Ubuntu, with Linux <version>`
3. **Backup**: Antes de cualquier cambio, copia `/etc/default/grub` a `/var/backups/grub-kernel-selector/`
4. **Aplicación**: Modifica `GRUB_DEFAULT` en `/etc/default/grub` y ejecuta `update-grub`
5. **Verificación**: Al reiniciar, `uname -r` mostrará el kernel seleccionado

## Solución de problemas

### El menú no aparece con sudo
El script usa `select` (built-in de bash) que maneja correctamente stdin/stdout con sudo.

### Kernel no detectado
Verifica que existe en `/boot`:
```bash
ls /boot/vmlinuz-*
```

### GRUB no se actualiza
Ejecuta manualmente:
```bash
sudo update-grub
```

### Restaurar configuración anterior
```bash
sudo ./cambiar-kernel-dinamico.sh --restore
```
O desde el menú interactivo: Opción 2 → Restaurar backup

## Licencia

MIT License - Ver [LICENSE](../../../../LICENSE)

## Autor

**carlymx** - [GitHub](https://github.com/carlymx)

## Changelog

### v1.0.0 (2026-10-27)
- Versión inicial con menú interactivo completo
- Detección automática de kernels
- Sistema de backups con metadatos
- Modo CLI para automatización
- Colores y navegación con teclas
