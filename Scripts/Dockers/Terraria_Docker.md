# Guía de Despliegue: Terraria Server en Docker (TrueNAS/Portainer)

Este repositorio contiene las configuraciones probadas y funcionales para desplegar servidores de Terraria (tanto Vanilla como TShock) utilizando Docker Compose.

## 📂 Estructura de Directorios en el Host (NAS)

Antes de desplegar, asegúrate de crear las carpetas y asignar permisos totales para evitar errores de escritura:

```bash
# Para el servidor Vanilla
mkdir -p /mnt/APPs/terrariaserver
chmod -R 777 /mnt/APPs/terrariaserver

# Para el servidor TShock
mkdir -p /mnt/APPs/tshock
chmod -R 777 /mnt/APPs/tshock
```
---

## 1. Escenario: Terraria Vanilla (beardedio/terraria)

Este servidor utiliza la imagen de beardedio, ideal para una experiencia original sin plugins.

```YAML
services:
  tshock:
    command: >-
      -autocreate 1 -worldname MundoTShock -difficulty 1 -maxplayers 8 -world
      /config/Worlds/MundoTShock.wld
    container_name: terraria-tshock
    environment:
      - autocreate=1
    image: beardedio/terraria:latest
    ports:
      - 7777:7777/tcp
    restart: unless-stopped
    stdin_open: True
    tty: True
    volumes:
      - /mnt/APPs/terrariaserver:/config
```
---

## 2. Escenario: TShock 6.1 - Generación Automática de Mundo

Utiliza la imagen oficial de Pryaxis para Terraria 1.4.5.x. En este modo, el servidor crea el mundo automáticamente en el primer arranque.

```YAML
services:
  tshock-auto:
    image: ghcr.io/pryaxis/tshock:v6.1.0
    container_name: terraria-tshock-auto
    restart: unless-stopped
    ports:
      - 7778:7777/tcp  # Mapeado al puerto 7778 externo
    stdin_open: true
    tty: true
    command: >
      -world /tshock/Worlds/MundoAuto.wld
      -autocreate 2
      -worldname MundoAuto
      -difficulty 1
      -maxplayers 16
    volumes:
      - /mnt/APPs/tshock:/tshock
```

---

## 3. Escenario: TShock 6.1 - Carga de Mapa Manual

Utiliza este YAML si ya tienes un archivo .wld existente. Debes colocar tu archivo en /mnt/APPs/tshock/Worlds/.

```YAML
services:
  tshock-6:
    command: >
      -world /tshock/Worlds/MIMAPA.wld -worldname MIMAPA -difficulty 1
      -maxplayers 16
    container_name: terraria-tshock-6
    image: ghcr.io/pryaxis/tshock:stable
    ports:
      - 7778:7777/tcp
    restart: unless-stopped
    stdin_open: True
    tty: True
    volumes:
      - /mnt/APPs/tshock:/tshock
```

## 🛠️ Configuración de Administrador (TShock)

Una vez desplegado el contenedor de TShock, sigue estos pasos para obtener permisos:

    Obtener el Setup Code: Revisa los logs del contenedor en Portainer o mediante el comando docker logs terraria-tshock-manual. Busca una línea similar a:
    [Server] To setup the server, please type /setup 123456 in-game.

    Entrar al Servidor: Conéctate desde Terraria usando la IP de tu NAS y el puerto configurado (ej. 7778).

    Activar Privilegios: Escribe en el chat: /setup [tu_codigo].

    Crear cuenta de SuperAdmin:

        /user add [nombre] [contraseña] superadmin

        /login [nombre] [contraseña]

## 💾 Comandos de Consola Útiles

    /save: Guarda el progreso del mundo inmediatamente.

    /exit: Guarda el mundo y apaga el servidor de forma segura.

    /help: Muestra la lista de comandos disponibles en TShock.















