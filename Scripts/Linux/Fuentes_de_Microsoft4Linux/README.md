# Microsoft Fonts for Linux

[📖 Leer en Español](./README_ES.md)

![Logo Windows Fonts for Linux](./logo_fonts.png)

<!-- Badges Section -->
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![Bash](https://img.shields.io/badge/shell-bash-orange.svg)
![Linux](https://img.shields.io/badge/platform-Linux-yellow.svg)
![Fonts](https://img.shields.io/badge/fonts-178+-ff69b4.svg)

## Description

A simple and efficient bash script to install and uninstall Microsoft Windows fonts on Linux systems. This project includes **178+ popular Microsoft fonts** organized into two categories:

- **Basic Fonts (48)**: The most commonly used fonts for everyday documents
- **Extra Fonts (130)**: Additional fonts including specialized and Asian language fonts

The script provides an easy-to-use menu system that allows you to:
- **Install** fonts (basic only, extra only, or all)
- **Uninstall** fonts from user or system directories
- **Check** the current installation status

Supports both user-level (`~/.fonts/`) and system-wide (`/usr/share/fonts/`) installation/uninstallation.

Perfect for users who need Microsoft font compatibility for documents, presentations, or applications that require Windows fonts on Linux.

## Table of Contents

- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
- [Included Fonts](#included-fonts)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Installation

### Prerequisites

- Linux operating system
- Bash shell
- `fc-cache` command (usually provided by `fontconfig` package)
- `sudo` privileges (only for system-wide installation)

### Quick Install

```bash
# Clone the repository
git clone <repo-url>

# Navigate to directory
cd "Fuentes de Microsoft para Linux"

# Run the installer
chmod +x instalar_fuentes.sh
./instalar_fuentes.sh
```

### Manual Installation

1. Download or clone this repository
2. Open a terminal in the project directory
3. Make the script executable: `chmod +x instalar_fuentes.sh`
4. Run the script: `./instalar_fuentes.sh`

## Usage

When you run the script, you'll see the main menu with the current status of installed fonts:

```bash
./instalar_fuentes.sh
```

### Main Menu

```
========================================
Gestor de Fuentes de Windows para Linux
========================================

Estado de las fuentes instaladas:
======================================
Usuario (/home/username/.fonts):
  ✓ Básicas: Instaladas
  ✗ Extras: No instaladas
Sistema (/usr/share/fonts):
  ✗ No hay fuentes instaladas

¿Qué desea hacer?

1) Instalar fuentes
2) Desinstalar fuentes
3) Ver estado de fuentes
4) Salir

Seleccione una opción (1-4):
```

### Installing Fonts

**Step 1: Select Font Package**

Choose which fonts you want to install:

**Option 1: Basic Fonts (48 fonts)**
- Arial, Times New Roman, Calibri, Cambria
- Comic Sans MS, Georgia, Verdana, Tahoma
- Trebuchet MS, Courier New, Consolas
- Impact, Webdings, Wingdings, Symbol

**Option 2: Extra Fonts (130 fonts)**
- Bahnschrift, Segoe UI, Candara
- Asian fonts, technical fonts, specialized fonts

**Option 3: All Fonts (178 fonts)**
- Complete collection of all basic and extra fonts

**Step 2: Select Installation Location**

**Option 1: Install for current user only**
- Fonts will be installed to `~/.fonts/`
- No root privileges required
- Only available to your user account

**Option 2: Install for all users (system-wide)**
- Fonts will be installed to `/usr/share/fonts/`
- Requires root/sudo privileges
- Available to all users on the system

### Uninstalling Fonts

The script can also uninstall fonts. It will:

1. **Analyze** both user (`~/.fonts/`) and system (`/usr/share/fonts/`) directories
2. **Show** which fonts are currently installed
3. **Ask** you to select:
   - From which location(s) to uninstall (user only, system only, or both)
   - Which fonts to remove (basic, extra, or all installed fonts)

**Example uninstallation flow:**

```
========================================
Desinstalador de Fuentes de Windows
========================================

Estado de las fuentes instaladas:
======================================
Usuario (/home/username/.fonts):
  ✓ Básicas: Instaladas
  ✓ Extras: Instaladas
Sistema (/usr/share/fonts):
  ✗ No hay fuentes instaladas

¿De dónde desea desinstalar las fuentes?

1) Solo del usuario actual (username)
2) Solo del sistema (requiere root)
3) De ambas ubicaciones

Seleccione una opción (1, 2 o 3): 1

¿Qué fuentes desea desinstalar?

1) Básicas (48 fuentes) - instaladas en usuario
2) Extras (130 fuentes) - instaladas en usuario
3) Todas las fuentes instaladas

ADVERTENCIA: Esta acción eliminará las fuentes del sistema.
¿Está seguro? (s/N): s
```

### View Font Status

Select option 3 to see the current installation status of fonts in both user and system directories without making any changes.

### After Installation

The script automatically updates the font cache. You may need to restart applications to see the new fonts. To verify installation:

```bash
# List installed fonts
fc-list | grep -i "arial\|calibri\|times"
```

## Included Fonts

This package includes **178+ Microsoft Windows fonts** organized in two directories:

### Basic Fonts (`fuentes_windows/basicas/`) - 48 fonts

The most commonly used fonts for everyday documents and general compatibility:

- **Arial** family (Regular, Bold, Italic, Bold Italic, Black)
- **Calibri** family (Regular, Bold, Italic, Bold Italic, Light)
- **Cambria** family
- **Comic Sans MS** family
- **Consolas** family (monospace font)
- **Courier New** family
- **Georgia** family
- **Impact**
- **Tahoma** family
- **Times New Roman** family
- **Trebuchet MS** family
- **Verdana** family
- **Webdings**
- **Wingdings**
- **Symbol**

### Extra Fonts (`fuentes_windows/extras/`) - 130 fonts

Additional fonts including specialized, decorative, and international fonts:

- **Bahnschrift**
- **Candara** family
- **Constantia** family
- **Corbel** family
- **Ebrima** family
- **Gabriola**
- **Gadugi** family
- **Himalaya**
- **Ink Free**
- **Leelawadee** family
- **Malgun Gothic** family
- **Marlett**
- **Microsoft Yi Baiti**
- **Mongolian Baiti**
- **MV Boli**
- **Nirmala UI** family
- **Segoe** families (UI, Print, Script, etc.)
- **Sitka** family
- **Sylfaen**
- **Yu Gothic** family
- Asian language fonts (MingLiu, MS Gothic, MS JhengHei, MS YaHei)
- SolidWorks technical fonts
- And many more...

### Directory Structure

```
fuentes_windows/
├── basicas/          # 48 essential fonts
│   ├── arial.ttf
│   ├── calibri.ttf
│   └── ...
└── extras/           # 130 additional fonts
    ├── bahnschrift.ttf
    ├── segoeui.ttf
    └── ...
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your contributions:
- Follow bash scripting best practices
- Include comments for complex logic
- Have been tested on multiple Linux distributions
- Do not include proprietary fonts not owned by Microsoft

## License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

**Note on Fonts:** The fonts included in this package are proprietary Microsoft products. This installer script is provided as a utility to help users who already have legitimate access to these fonts install them on Linux systems. Please ensure you comply with Microsoft's font licensing terms.

## Acknowledgments

- Thanks to Microsoft for creating these widely-used fonts
- Inspired by the need for better font compatibility between Windows and Linux
- Special thanks to the Linux community for fontconfig and font management tools
- Font collection sourced from Windows installations

## Troubleshooting

### Fonts not showing in applications?
Try restarting the application or running:
```bash
fc-cache -f -v
```

### Permission denied?
Make sure the script is executable:
```bash
chmod +x instalar_fuentes.sh
```

### System-wide installation fails?
Ensure you have sudo privileges and the password is correct.

## Support

For issues, questions, or suggestions, please open an issue in the repository.

---

**Made with ❤️ for the Linux community**
