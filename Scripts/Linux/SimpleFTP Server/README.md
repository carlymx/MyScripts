[ESPAÑOL](README_ES.md) | [ENGLISH](README.md)

# FTP Server Manager GUI (beta)

GUI application to control a simple and fast FTP server with pyftpdlib.

## Requirements

- Python 3.6 or higher
- `venv` module for Python (on Linux: `python3-venv`)

## Installation and Usage

### Option 1: Use automatic script (recommended)

Run the `run_ftp_server.sh` script that will automatically create a virtual environment and install the dependencies:

```bash
./run_ftp_server.sh
```

This script:

1. Creates a virtual environment named `ftp_server_env`
2. Installs the necessary dependencies
3. Runs the FTP Server Manager

### Option 2: Manual installation

1. Create a virtual environment:
   
   ```bash
   python3 -m venv ftp_server_env
   ```

2. Activate the virtual environment:
   
   ```bash
   source ftp_server_env/bin/activate  # On Linux/Mac
   # or
   ftp_server_env\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   
   ```bash
   pip install PyQt5 pyftpdlib colorama
   ```

4. Run the script:
   
   ```bash
   python ftp_server_manager.py
   ```

## Features

- GUI interface with PyQT5
- FTP server control (start, stop, restart)
- Shared directory configuration
- User management with permissions
- Permissions verification and correction
- Configuration editor
- Profile system with default configurations
- Log viewer
- Menu bar with dark/light theme option

## Notes

- The script stores configurations in `~/.ftp_server_manager/`
- Logs are saved in `~/.ftp_server_manager/logs/`
- The first execution will create the directory structure
- Includes a "Tools" menu with option to switch between light and dark themes

## Documentation Files

- [README in Spanish](README_ES.md)
- [Qwen CLI Instructions](QWEN.md)
- [Conversation Summary](.chat_log/resumen_conversacion.md)