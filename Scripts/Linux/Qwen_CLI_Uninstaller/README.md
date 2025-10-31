# Qwen CLI Uninstaller

[Español](README_ES.md) | [English](README.md)


## Overview

This repository contains a comprehensive uninstaller script for completely removing Qwen CLI and its Node.js environment from Arch Linux-based systems.

## Description

The `desisntalar_QwenCli.sh` script provides a complete cleanup solution for:
- Qwen CLI global npm packages
- Node.js and npm system packages
- Configuration directories and cache files
- nvm (Node Version Manager) installations
- Shell configuration entries

## Usage

```bash
# Make the script executable
chmod +x desisntalar_QwenCli.sh

# Run the uninstaller
./desisntalar_QwenCli.sh

What the Script Does

    Stops running Qwen processes

    Uninstalls Qwen CLI globally via npm

    Removes system packages (nodejs, npm) using pacman/yay

    Cleans configuration directories (.qwen, .config/qwen, .cache/qwen)

    Removes nvm and npm directories

    Cleans shell configurations (.bashrc, .zshrc, .profile)

    Clears npm cache

    Verifies remaining processes and files

Warning

⚠️ This script performs extensive system cleanup. Use with caution as it will:

    Remove all Qwen CLI installations

    Uninstall Node.js and npm from your system

    Delete configuration files and cache data

    Modify your shell configuration files

Recommendations

    Close and reopen your terminal after running the script

    Review the script before execution if you have custom Node.js setups

    Backup important configuration files if needed

Compatibility

Designed for Arch Linux and derivatives (Manjaro, EndeavourOS, etc.)
