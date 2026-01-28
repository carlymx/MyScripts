#!/bin/bash

# Umbral de temperatura para avisar (puedes bajarlo a 40 para probar que funciona)
UMBRAL=70

echo "-------------------------------------------------------"
echo "Iniciando vigilancia de discos NVMe..."
echo "Umbral de alerta: $UMBRAL°C"
echo "Comprobación cada 60 segundos."
echo "-------------------------------------------------------"

# Detectar discos y guardarlos en una lista
DISCOS=$(ls /dev/nvme[0-9]n[0-9] 2>/dev/null)

if [ -z "$DISCOS" ]; then
    echo "❌ Error: No se detectaron discos NVMe."
    exit 1
fi

while true; do
    echo "[$(date +%H:%M:%S)] Comprobando temperaturas:"

    for DISCO in $DISCOS; do
        # Obtener temperatura
        TEMP=$(sudo nvme smart-log "$DISCO" | grep '^temperature' | awk '{print $3}')

        # Mostrar temperatura actual en la terminal para que veas que funciona
        echo "  -> $DISCO: $TEMP°C"

        # Lógica de alerta
        if [ "$TEMP" -ge "$UMBRAL" ]; then
            notify-send -u critical "⚠️ ALERTA DE CALOR" "El disco $DISCO está a $TEMP°C."
            echo "     ¡ALERTA ENVIADA PARA $DISCO!"
        fi
    done

    echo "-------------------------------------------------------"
    sleep 10
done
