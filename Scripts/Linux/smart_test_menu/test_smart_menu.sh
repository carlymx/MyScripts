#!/bin/bash

# Función para mostrar el logo
show_logo() {
    clear
    echo "###############################################################"
    echo "#   ____  _      ____  ____ _____    _____ _____ ____ _____  #" 
    echo "#  / ___\/ \__/|/  _ \/  __Y__ __\  /__ __Y  __// ___Y__ __\ #"
    echo "#  |    \| |\/||| / \||  \/| / \      / \ |  \  |    \ / \   #"
    echo "#  \___ || |  ||| |-|||    / | |      | | |  /_ \___ | | |   #"
    echo "#  \____/\_/  \|\_/ \|\_/\_\ \_/      \_/ \____\\____/ \_/   #"
    echo "#                                                            #"
    echo "#                       MONITOR v1.0                         #"
    echo "##############################################################"
    echo ""
}

# Función para detectar dispositivos disponibles
detect_devices() {
    echo "🔍 Detectando dispositivos..."
    local devices=()
    
    # Buscar dispositivos de bloque (discos)
    for device in /dev/sd?; do
        if [ -b "$device" ]; then
            # Verificar si responde a smartctl
            if sudo smartctl -i $device &>/dev/null; then
                devices+=("$device")
            fi
        fi
    done
    
    # Buscar dispositivos NVMe
    for device in /dev/nvme?n?; do
        if [ -b "$device" ]; then
            if sudo smartctl -i $device &>/dev/null; then
                devices+=("$device")
            fi
        fi
    done
    
    printf '%s\n' "${devices[@]}"
}

# Función para seleccionar dispositivo
select_device() {
    show_logo
    echo "1. SELECCIONAR DISPOSITIVO"
    echo "=========================="
    
    local devices=($(detect_devices))
    
    if [ ${#devices[@]} -eq 0 ]; then
        echo "❌ No se encontraron dispositivos SMART disponibles."
        echo "   Verifica que:"
        echo "   - Los discos estén conectados"
        echo "   - SMART esté habilitado"
        echo "   - Tengas permisos sudo"
        echo ""
        read -p "Presiona Enter para continuar..."
        return 1
    fi
    
    echo "Dispositivos disponibles:"
    echo ""
    
    local i=1
    for device in "${devices[@]}"; do
        # Obtener información básica del dispositivo
        local model=$(sudo smartctl -i $device | grep -i "Model" | head -1 | cut -d: -f2 | sed 's/^ *//')
        local serial=$(sudo smartctl -i $device | grep -i "Serial" | head -1 | cut -d: -f2 | sed 's/^ *//')
        echo "   $i. $device"
        echo "      Modelo: $model"
        echo "      Serial: $serial"
        echo ""
        ((i++))
    done
    
    echo "   $i. Volver al menú principal"
    echo ""
    
    while true; do
        read -p "Selecciona un dispositivo [1-$i]: " choice
        
        if [[ $choice -ge 1 && $choice -le ${#devices[@]} ]]; then
            SELECTED_DEVICE="${devices[$((choice-1))]}"
            echo "✅ Dispositivo seleccionado: $SELECTED_DEVICE"
            return 0
        elif [[ $choice -eq $i ]]; then
            return 1
        else
            echo "❌ Opción inválida. Intenta nuevamente."
        fi
    done
}

# Función para seleccionar formato de comunicación
select_interface() {
    show_logo
    echo "2. SELECCIONAR FORMATO DE COMUNICACIÓN"
    echo "======================================"
    echo ""
    
    local interfaces=(
        "auto - Detección automática"
        "sat - SATA/ATA sobre USB/SCSI"
        "sntjmicron - JMicron USB bridge"
        "usbcypress - Cypress USB bridge"
        "usbprolific - Prolific USB bridge"
        "usbsunplus - Sunplus USB bridge"
        "nvme - Dispositivos NVMe"
        "scsi - Dispositivos SCSI"
    )
    
    local i=1
    for interface in "${interfaces[@]}"; do
        echo "   $i. $interface"
        ((i++))
    done
    
    echo ""
    
    while true; do
        read -p "Selecciona el formato [1-$((i-1))]: " choice
        
        if [[ $choice -ge 1 && $choice -le $((i-1)) ]]; then
            case $choice in
                1) SELECTED_INTERFACE="auto" ;;
                2) SELECTED_INTERFACE="sat" ;;
                3) SELECTED_INTERFACE="sntjmicron" ;;
                4) SELECTED_INTERFACE="usbcypress" ;;
                5) SELECTED_INTERFACE="usbprolific" ;;
                6) SELECTED_INTERFACE="usbsunplus" ;;
                7) SELECTED_INTERFACE="nvme" ;;
                8) SELECTED_INTERFACE="scsi" ;;
            esac
            echo "✅ Formato seleccionado: $SELECTED_INTERFACE"
            return 0
        else
            echo "❌ Opción inválida. Intenta nuevamente."
        fi
    done
}

# Función para seleccionar tipo de test
select_test_type() {
    show_logo
    echo "3. SELECCIONAR TIPO DE TEST"
    echo "==========================="
    echo ""
    
    local tests=(
        "short - Test rápido (2-5 minutos)"
        "long - Test extendido/exhaustivo (varias horas)"
        "conveyance - Test de transporte (5-15 minutos)"
        "offline - Test offline (recopila datos existentes)"
    )
    
    local i=1
    for test in "${tests[@]}"; do
        echo "   $i. $test"
        ((i++))
    done
    
    echo ""
    
    while true; do
        read -p "Selecciona el tipo de test [1-$((i-1))]: " choice
        
        if [[ $choice -ge 1 && $choice -le $((i-1)) ]]; then
            case $choice in
                1) SELECTED_TEST="short" ;;
                2) SELECTED_TEST="long" ;;
                3) SELECTED_TEST="conveyance" ;;
                4) SELECTED_TEST="offline" ;;
            esac
            echo "✅ Test seleccionado: $SELECTED_TEST"
            return 0
        else
            echo "❌ Opción inválida. Intenta nuevamente."
        fi
    done
}

# Función CORREGIDA para verificar dispositivo y test en ejecución
check_device_and_test() {
    show_logo
    echo "4. VERIFICACIÓN FINAL"
    echo "====================="
    echo ""
    echo "Resumen de configuración:"
    echo "   📟 Dispositivo: $SELECTED_DEVICE"
    echo "   🔌 Interface: $SELECTED_INTERFACE"
    echo "   🧪 Test: $SELECTED_TEST"
    echo ""
    
    # Verificar que el dispositivo está disponible
    echo "🔍 Verificando dispositivo..."
    if ! sudo smartctl -i -d $SELECTED_INTERFACE $SELECTED_DEVICE &>/dev/null; then
        echo "❌ Error: No se puede acceder al dispositivo"
        echo "   El dispositivo no responde con el formato seleccionado"
        read -p "Presiona Enter para continuar..."
        return 1
    fi
    
    echo "✅ Dispositivo responde correctamente"
    echo ""
    
    # Verificar CORREGIDO: Buscar específicamente que NO hay tests en progreso
    echo "📋 Comprobando tests activos..."
    local test_output=$(sudo smartctl -a -d $SELECTED_INTERFACE $SELECTED_DEVICE | grep -i "Self-test")
    local test_in_progress=$(echo "$test_output" | grep -i "No self-test in progress")

    if [ -n "$test_output" ] && [ -z "$test_in_progress" ]; then
        echo "⚠️  Ya hay un test SMART en ejecución:"
        echo "   $test_output"
        echo ""
        echo "Opciones:"
        echo "   1. Monitorear test existente"
        echo "   2. Cancelar y volver al menú"
        echo ""
        
        while true; do
            read -p "Selecciona opción [1-2]: " choice
            case $choice in
                1)
                    echo "👀 Iniciando monitoreo del test existente..."
                    monitor_test
                    return 1
                    ;;
                2)
                    echo "↩️  Volviendo al menú principal..."
                    return 1
                    ;;
                *)
                    echo "❌ Opción inválida"
                    ;;
            esac
        done
    else
        echo "✅ No hay tests en ejecución"
        echo ""
        echo "¿Deseas iniciar el test $SELECTED_TEST?"
        echo "   1. ✅ Sí, iniciar test y monitorear"
        echo "   2. ❌ No, volver al menú"
        echo ""
        
        while true; do
            read -p "Selecciona opción [1-2]: " choice
            case $choice in
                1)
                    echo "🚀 Iniciando test $SELECTED_TEST..."
                    start_and_monitor_test
                    return 0
                    ;;
                2)
                    echo "↩️  Volviendo al menú principal..."
                    return 1
                    ;;
                *)
                    echo "❌ Opción inválida"
                    ;;
            esac
        done
    fi
}

# Función para iniciar y monitorear test
start_and_monitor_test() {
    echo ""
    echo "🎬 Iniciando test $SELECTED_TEST en $SELECTED_DEVICE..."
    
    if sudo smartctl -t $SELECTED_TEST -d $SELECTED_INTERFACE $SELECTED_DEVICE; then
        echo "✅ Test iniciado correctamente"
        sleep 2
        monitor_test
    else
        echo "❌ Error al iniciar el test"
        read -p "Presiona Enter para continuar..."
    fi
}

# Función para monitorear el test
monitor_test() {
    local UPDATE_INTERVAL=30
    
    show_logo
    echo "📊 MONITOREO EN TIEMPO REAL"
    echo "==========================="
    echo "Dispositivo: $SELECTED_DEVICE"
    echo "Interface: $SELECTED_INTERFACE"
    echo "Test: $SELECTED_TEST"
    echo "Inicio: $(date)"
    echo "----------------------------------------"
    echo ""
    
    while true; do
        echo -e "=== Estado: $(date) ==="
        
        # Obtener información del progreso
        local status=$(sudo smartctl -a -d $SELECTED_INTERFACE $SELECTED_DEVICE | grep -E "Self-test execution|remaining|Progress|Test_Description")
        
        if [ -n "$status" ]; then
            echo "$status" | while read line; do
                echo "   📝 $line"
            done
        else
            echo "   🔍 Buscando información del test..."
        fi
        
        # Verificar si el test ha terminado
        local completed=$(sudo smartctl -l selftest -d $SELECTED_INTERFACE $SELECTED_DEVICE | grep "# 1" | grep "Completed")
        if [ -n "$completed" ]; then
            echo -e "\n🎉🎉🎉 TEST COMPLETADO 🎉🎉🎉"
            echo "----------------------------------------"
            echo "📄 RESULTADOS FINALES:"
            sudo smartctl -l selftest -d $SELECTED_INTERFACE $SELECTED_DEVICE | head -10
            echo -e "\n💾 Información del dispositivo:"
            sudo smartctl -a -d $SELECTED_INTERFACE $SELECTED_DEVICE | grep -E "Model|Serial|Health|Temperature"
            echo ""
            read -p "Presiona Enter para volver al menú principal..."
            break
        fi
        
        echo ""
        echo "Próxima actualización en ${UPDATE_INTERVAL}s (Ctrl+C para salir)..."
        sleep $UPDATE_INTERVAL
        clear
        show_logo
        echo "📊 MONITOREO EN TIEMPO REAL"
        echo "==========================="
        echo "Dispositivo: $SELECTED_DEVICE"
        echo "Interface: $SELECTED_INTERFACE"
        echo "Test: $SELECTED_TEST"
        echo "Inicio: $(date)"
        echo "----------------------------------------"
        echo ""
    done
}

# Menú principal
main_menu() {
    while true; do
        show_logo
        echo "MENÚ PRINCIPAL"
        echo "=============="
        echo ""
        echo "Configuración actual:"
        echo "   📟 Dispositivo: ${SELECTED_DEVICE:-No seleccionado}"
        echo "   🔌 Interface: ${SELECTED_INTERFACE:-No seleccionado}"
        echo "   🧪 Test: ${SELECTED_TEST:-No seleccionado}"
        echo ""
        echo "Opciones:"
        echo "   1. Seleccionar dispositivo"
        echo "   2. Seleccionar formato de comunicación"
        echo "   3. Seleccionar tipo de test"
        echo "   4. Verificar e iniciar test"
        echo "   5. Salir"
        echo ""
        
        read -p "Selecciona una opción [1-5]: " choice
        
        case $choice in
            1) select_device ;;
            2) select_interface ;;
            3) select_test_type ;;
            4) 
                if [ -z "$SELECTED_DEVICE" ] || [ -z "$SELECTED_INTERFACE" ] || [ -z "$SELECTED_TEST" ]; then
                    echo "❌ Configuración incompleta. Completa todos los pasos primero."
                    read -p "Presiona Enter para continuar..."
                else
                    check_device_and_test
                fi
                ;;
            5)
                echo "👋 ¡Hasta pronto!"
                exit 0
                ;;
            *)
                echo "❌ Opción inválida"
                sleep 1
                ;;
        esac
    done
}

# Variables globales
SELECTED_DEVICE=""
SELECTED_INTERFACE=""
SELECTED_TEST=""

# Ejecutar menú principal
main_menu
