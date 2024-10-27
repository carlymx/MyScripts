#!/bin/bash



###################################################################################################
#                                                                                                 #
#      ¡¡¡ADVERTENCIA:!!! ESTE SCRIPT DESTRUIRA TODOS LOS DATOS DE DATASETS PREEXISTENTES         #
#      EN LAS POOLS DE DESTINO. UTILIZA ESTE SCRIPT BAJO TU UNICA RESPONSAVILIDAD.                #
#      SE RECOMIENDA PRACTICAR ANTES EN UNA MAQUINA VIRTUAL PARA ESTAR SEGUROS DE COMO            #
#      FUNCIONA EL SCRIPT EN SU TOTALIDAD.                                                        #
#      --- NO ME HAGO RESPONSABLE DEL MAL USO O DE CUALQUIER PERDIDA DE DATOS Y DE                #
#          CUALQUIER OTRA COSA RELACIONADA O NO POR USAR EL SCRIPT ---                            #
#                                                                                                 #
###################################################################################################

# Nombre del Script: copia_datasets_zfs.sh
# Fecha: 2024-10-27
#
# Descripción:
# Este script automatiza la copia de datasets de una pool ZFS a otra en un sistema TrueNAS.
# 
# Funcionamiento:
# 1. El script define las pools de origen y destino. Asegúrate de modificar las variables
#    ORIGEN y DESTINO con los nombres correctos de tus pools.
# 
# 2. Se define un array asociativo que relaciona cada dataset con su tipo de compresión
#    deseado. Puedes ajustar los tipos de compresión según tus necesidades.
# 
# 3. Para cada dataset en la lista, el script realiza los siguientes pasos:
#    - Crea un snapshot del dataset original en la pool de origen. Esto es una copia de seguridad
#      del estado del dataset en un momento específico.
#    - Crea un nuevo dataset en la pool de destino con la compresión especificada.
#    - Envía el snapshot del dataset original al nuevo dataset en la pool de destino.
# 
# 4. Al final, imprime un mensaje indicando que todos los datasets han sido copiados.
#
# **Nota**: Asegúrate de que el usuario que ejecuta el script tenga los permisos necesarios (ROOT)
# para crear snapshots y enviar datos entre pools ZFS.


# NOTAS PERSONALES:

 # zfs list | grep nombre_de_tu_pool
 # zfs snapshot ALMACEN_CENTRAL/PROYECTOS@SNAPSHOT_BACKUP_CLONE
 # zfs send ALMACEN_CENTRAL/PROYECTOS@SNAPSHOT_BACKUP_CLONE | zfs receive ALMACEN-CENTRAL/PROYECTOS

 # Tipos de compresión admitidos en ZFS (usar en minusculas):
  # LZ4, GZIP, GZIP-1, GZIP-9, ZSTD, ZSTD-FAST,
  # ZLE, LZJB, ZSTD-1 al ZSTD-19,
  # ZSTD-FAST-1 al ZSTD-FAST-9,
  # ZSTD-FAST-10 al ZSTD-FAST-20,
  # ZSTD-FAST-100, ZSTD-FAST-500, ZSTD-FAST-1000


# Definir las pools
ORIGEN="POOL_ORIGEN"
DESTINO="POOL_DESTINO"

# Lista de datasets y su tipo de compresión:
# ESCRIBIR EN ESTA ARRAY TODOS LOS DATASETs QUE SE QUIEREN CLONAR A LA POOL DE DESTINO
# AQUÍ SE MUESTRAN EJEMPLOS DE COMO PUEDE ESTAR ORGANIZADO UN GRUPO DE DATASETs Y LA
# COMPRESIÓN MÁS ADECUADA PARA ELLOS (MUY BAJA Y RAPIDA COMPRESIÓN PARA DATASETS DONDE
# SE ALMACENARAN ARCHIVOS YA COMPRIMIDOS COMO FOTOS Y VIDEOS).
declare -A DATASETS_COMPRESSION=(
    ["FOTOS"]="zstd-fast"
    ["FOTOS/PEPITO"]="zstd-fast"
    ["FOTOS/MENGANITO"]="zstd-fast"
    ["FOTOS/GLOBAL"]="zstd-fast"
    ["LIBROS"]="zstd"
    ["MUSICA"]="zstd"
    ["PROYECTOS"]="zstd-fast"
    ["SHARE"]="zstd-fast"
    ["USERS"]="zstd"
    ["USERS/PEPITO"]="zstd"
    ["USERS/MENGANITO"]="zstd"
    ["VIDEOS"]="zstd-fast"
    ["VIDEOS/PEPITO"]="zstd-fast"
    ["VIDEOS/PENGANITO"]="zstd-fast"
    ["VIDEOS/GLOBAL"]="zstd-fast"
)

# Bucle para copiar los datasets
for DATASET in "${!DATASETS_COMPRESSION[@]}"; do
    COMPRESSION="${DATASETS_COMPRESSION[$DATASET]}"
    SNAPSHOT_NAME="backup_$(date +%Y%m%d_%H%M%S)"

    # Crear un snapshot del dataset original
    echo "Creando snapshot de $ORIGEN/$DATASET..."
    zfs snapshot "$ORIGEN/$DATASET@$SNAPSHOT_NAME"

    # Verificar si el dataset ya existe
    if zfs list "$DESTINO/$DATASET" > /dev/null 2>&1; then
        echo "El dataset $DESTINO/$DATASET ya existe. Sobrescribiendo..."
    else
        echo "Creando dataset $DESTINO/$DATASET con compresión $COMPRESSION..."
        zfs create -p -o compression="$COMPRESSION" "$DESTINO/$DATASET"
    fi

    # Enviar el snapshot al nuevo dataset
    echo "Enviando snapshot a $DESTINO/$DATASET..."
    zfs send "$ORIGEN/$DATASET@$SNAPSHOT_NAME" | zfs receive -F "$DESTINO/$DATASET"

    echo "Copia de $ORIGEN/$DATASET completada."
done

echo "Todos los datasets han sido copiados."
