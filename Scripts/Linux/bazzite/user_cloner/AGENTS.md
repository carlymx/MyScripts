# AGENTS.md - User Cloner Development Guide

Bash script for cloning user profiles on Bazzite Linux (Fedora Atomic/Silverblue).

**Status:** Active Development - Interactive script with numbered menus (~1600 lines, 7-step wizard)

## Build Commands

```bash
# Verify syntax
bash -n user_cloner.sh

# Make executable
chmod +x user_cloner.sh

# Debug with trace
bash -x user_cloner.sh 2>&1 | tee debug.log
```

## Lint/Format Commands

```bash
# ShellCheck (required before commits)
shellcheck user_cloner.sh

# Format with shfmt (2 spaces, indent cases)
shfmt -w -i 2 -ci user_cloner.sh

# Check without modifying
shfmt -d -i 2 -ci user_cloner.sh
```

## Code Style Guidelines

### Bash Conventions
- **Shebang**: `#!/bin/bash` (not /bin/sh)
- **Strict mode**: `set -euo pipefail` at start
- **Indentation**: 2 spaces (no tabs)
- **Line length**: Max 100 characters
- **Functions**: `nombre_funcion()` - lowercase with underscores
- **Variables**: `MAYUSCULAS` for constants, `minusculas` for local
- **Quotes**: Always `"$variable"`, never bare `$variable`

### Error Handling
- Use `set -e` for immediate exit on errors
- Check results: `if comando; then ... fi` or `comando || handle_error`
- Trap signals: `trap cleanup EXIT ERR`
- Errors to stderr: `echo "Error" >&2`
- Non-zero exit codes on failures

### Security
- Validate ALL user inputs
- Sanitize paths with `realpath` or `readlink -f`
- NEVER use `eval` with untrusted input
- Verify root/sudo at script start
- Use `readonly` for constants
- Explicit confirmation before destructive operations
- Lock file: `/var/lock/user_cloner.lock` to prevent concurrent runs

### Naming Conventions
- Functions: `nombre_funcion()` - lowercase with underscores
- Variables: `nombre_variable` (local), `NOMBRE_CONSTANTE` (constants)
- Temp files: Use `mktemp` with descriptive prefix
- Interaction functions: `preguntar_*`, `validar_*`, `mostrar_*`, `seleccionar_*`, `menu_*`

### Logging & Output
- Verbose mode with interactive question
- Log to file with timestamps: `$(date '+%Y-%m-%d %H:%M:%S')`
- Visual separators between sections
- Colored output: ✓ success (green), ✗ error (red), ⚠ warning (yellow), ℹ info (blue)

## Bazzite-Specific Requirements

- **SELinux contexts**: Run `restorecon -Rv /home/user` after copy
- **Flatpak data**: Preserve `~/.var/app` directory
- **Immutable filesystem**: Compatible with Fedora Atomic/Silverblue
- **User creation**: Use `useradd` with proper flags for Bazzite
- **Group membership**: Preserve supplementary groups (wheel, video, render, gamemode)

## Interactive UX Standards

- **Numbered menus**: All selections use numbers (1, 2, 3...)
- **Option 0**: Always "Cancel / Go back"
- **7-step wizard**: 
  1. Presentation
  2. Select source user
  3. Create target user + Password
  4. **Select directories to copy** (NEW - granular selection)
  5. Advanced options (Flatpak, SELinux, Verbose)
  6. Review & Confirm
  7. Execute
- **Input validation**: Immediate feedback with sleep delays
- **Colors**: Check `[ -t 1 ]` before using colors
- **Progress indicators**: ⏳ for long operations
- **ASCII header**: Visual branding on startup

## Main Functions

### Validation
- `validar_nombre_usuario()` - Regex for valid usernames
- `validar_usuario_existe()` - Check if user exists in system
- `validar_usuario_no_existe()` - Verify username availability

### Directory Selection (NEW)
- `detectar_directorios_categorizados()` - Scan and categorize directories (Personales, Config, Gaming, AppImages, Otros)
- `menu_checkbox_categorias()` - Interactive checkbox menu for directory selection
- `formatear_tamano()` - Format bytes to human-readable (B, K, M, G)
- `calcular_tamano_directorio()` - Calculate directory size with `du`
- `mostrar_resumen_seleccion()` - Display summary of selected directories

### Interaction (Numbered Menus)
- `seleccionar_de_lista()` - Menu from array, returns selection via stdout
- `menu_con_input()` - Menu with option 1 for custom text input
- `preguntar()` - Yes/no questions with s/n validation
- `preguntar_texto()` - Free text input
- `pedir_contrasena()` - Hidden password input with confirmation

### Operations
- `verificar_root()` - Privilege check with error exit
- `crear_usuario()` - Create with `useradd -m -s shell -G groups`
- `establecer_contrasena_bypass()` - Set password bypassing PAM (6-char restriction)
- `copiar_datos()` - Copy selected directories only (iterates through arrays)
- `ajustar_selinux()` - `restorecon -Rv` on destination home
- `verificar_resultado()` - Final validation of created user

### Utilities
- `log()` - Timestamped logging to `/tmp/user_cloner_*.log`
- `error()`, `exito()`, `advertencia()`, `info()` - Colored messages
- `separador()` - Visual line separator
- `limpieza()` - Cleanup temp files (trap on EXIT/ERR)

## Important Implementation Notes

### Array Declaration
- Use **indexed arrays** (`declare -a`) for directory lists, NOT associative arrays (`declare -A`)
- Example: `declare -a DIRECTORIOS_PERSONALES=()` not `declare -A DIRECTORIOS_PERSONALES=()`
- This is crucial for numeric indexing to work properly

### Arithmetic with set -e
- **AVOID**: `((count++))` - fails with `set -e` when count is 0
- **USE**: `count=$((count + 1))` - safe with `set -e`
- Apply to all increment operations throughout the script

### Directory Arrays Structure
Each directory entry follows format: `"name|size|selected"`
- `name`: Directory name or path
- `size`: Size in bytes (calculated with `du -sb`)
- `selected`: "true" or "false"

Five category arrays:
- `DIRECTORIOS_PERSONALES[]` - Standard directories (Documents, Desktop, etc.)
- `DIRECTORIOS_CONFIG[]` - Configuration directories (.config, .local, etc.)
- `DIRECTORIOS_GAMING[]` - Gaming directories (Steam, Heroic, etc.)
- `DIRECTORIOS_APPIMAGES[]` - AppImage files (detected individually)
- `DIRECTORIOS_OTROS[]` - Other non-standard directories

## Dependencies

- bash >= 4.0
- coreutils (id, useradd, usermod, chown)
- rsync
- selinux-utils (restorecon)
- openssl (for password hash generation)
- POSIX tools (grep, sed, awk, cut)
- tput (terminal colors/formatting)
- bc (for size formatting calculations)

## Workflow

1. Write function with error handling
2. Add input validations
3. Use indexed arrays (`declare -a`) not associative
4. Use `var=$((var + 1))` not `((var++))`
5. Integrate into numbered menu flow
6. Run shellcheck with no warnings
7. Manual test: `sudo ./user_cloner.sh`
8. Commit

## References

- ShellCheck: https://www.shellcheck.net/
- Google Shell Style Guide: https://google.github.io/styleguide/shellguide.html
- Bash Strict Mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
- Bash Arrays: https://www.gnu.org/software/bash/manual/html_node/Arrays.html
