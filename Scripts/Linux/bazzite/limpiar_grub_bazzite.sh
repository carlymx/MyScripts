#!/bin/bash

###############################################################################
# NOMBRE: limpiar_grub.sh
# DESCRIPCIÓN: Limpia configuraciones manuales de GRUB y fuerza la detección
#              nativa de sistemas operativos en Bazzite/Fedora.
#              Especialmente útil para arreglar Dual Boot con Windows 11.
# AUTOR: Gemini AI & Usuario
# FECHA: 28/01/2026
###############################################################################

echo "🧹 Iniciando limpieza de GRUB..."

# 1. Eliminar el archivo manual que creamos
if [ -f /etc/grub.d/40_custom ]; then
    sudo rm /etc/grub.d/40_custom
    echo "✅ Archivo 40_custom eliminado."
fi

# 2. Restaurar un 40_custom básico y limpio
sudo bash -c 'cat << CUSTOM_EOF > /etc/grub.d/40_custom
#!/usr/bin/sh
exec tail -n +3 \$0
# This file provides an easy way to add custom menu entries.
CUSTOM_EOF'
sudo chmod +x /etc/grub.d/40_custom

# 3. Limpiar variables de entorno de GRUB (esto quita el auto-hide y timeouts viejos)
sudo grub2-editenv - unset menu_auto_hide
sudo grub2-editenv - unset timeout
echo "✅ Variables de entorno reseteadas."

# 4. Regenerar GRUB en todas las rutas posibles de Bazzite/Fedora
echo "⚙️ Regenerando archivos de sistema..."
sudo grub2-mkconfig -o /etc/grub2.cfg
sudo grub2-mkconfig -o /etc/grub2-efi.cfg
sudo grub2-mkconfig -o /boot/grub2/grub.cfg
sudo grub2-mkconfig -o /boot/efi/EFI/fedora/grub.cfg

echo "🚀 ¡Limpieza completada! Reinicia para ver el estado original."
