#!/bin/bash

echo "=== Desinstalación completa de Qwen CLI y entorno Node.js ==="

# Detener cualquier proceso de Qwen que esté corriendo
echo "Deteniendo procesos de Qwen..."
pkill -f qwen 2>/dev/null

# 1. Desinstalar Qwen CLI globalmente
echo "Desinstalando Qwen CLI..."
npm uninstall -g @qwenex/qwen-cli 2>/dev/null
npm uninstall -g @qwen-code/qwen-code 2>/dev/null
sudo npm uninstall -g @qwenex/qwen-cli 2>/dev/null
sudo npm uninstall -g @qwen-code/qwen-code 2>/dev/null

# 2. Remover paquetes via pacman/yay
echo "Desinstalando paquetes de sistema..."
sudo pacman -Rns nodejs npm --noconfirm 2>/dev/null
yay -Rns nodejs npm --noconfirm 2>/dev/null

# 3. Limpiar directorios de configuración
echo "Limpiando directorios de configuración..."
rm -rf ~/.qwen
rm -rf ~/.config/qwen
rm -rf ~/.cache/qwen
rm -rf ~/.npm
rm -rf ~/.npm-global
rm -rf ~/.node-gyp
rm -rf ~/.node_repl_history

# 4. Desinstalar nvm y limpiar
echo "Desinstalando nvm..."
rm -rf ~/.nvm
rm -rf ~/.npm

# 5. Limpiar archivos de configuración del shell
echo "Limpiando configuraciones del shell..."
# Remover líneas relacionadas con nvm/npm de .bashrc, .zshrc, etc.
sed -i '/NVM_DIR/d' ~/.bashrc ~/.zshrc ~/.profile 2>/dev/null
sed -i '/nvm/d' ~/.bashrc ~/.zshrc ~/.profile 2>/dev/null
sed -i '/npm-global/d' ~/.bashrc ~/.zshrc ~/.profile 2>/dev/null

# 6. Limpiar cache y temporales
echo "Limpiando cache..."
npm cache clean --force 2>/dev/null
sudo npm cache clean --force 2>/dev/null

# 7. Verificar procesos restantes
echo "Verificando procesos restantes..."
pgrep -f node && echo "ADVERTENCIA: Hay procesos de Node.js aún ejecutándose" || echo "✓ No hay procesos de Node.js activos"

# 8. Verificar archivos restantes
echo "Verificando archivos restantes..."
find ~ -name "*qwen*" -type d 2>/dev/null | head -10
find ~ -name "*node*" -type d 2>/dev/null | head -10

echo ""
echo "=== Desinstalación completada ==="
echo "Recomendación: Cierra y reabre tu terminal para que los cambios surtan efecto."
