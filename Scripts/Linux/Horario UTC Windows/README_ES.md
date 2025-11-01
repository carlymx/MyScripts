[English](README.md)

# Corrección de Hora UTC para Windows

Este archivo de registro soluciona la inconsistencia horaria cuando se tiene Linux y Windows instalados en la misma máquina.

## Descripción del Problema

Cuando tienes tanto Windows como Linux instalados en la misma computadora, puedes notar que la hora es incorrecta en uno de los sistemas operativos después de cambiar entre ellos.

### ¿Por qué sucede esto?

Windows y Linux manejan el tiempo del sistema de manera diferente:

- **Windows** tradicionalmente usa hora local (RTC en hora local)
- **Linux** usa UTC (Tiempo Universal Coordinado) para el reloj de hardware

Cuando Linux establece el reloj de hardware en UTC y luego inicias Windows, Windows lee la hora UTC pero la interpreta como hora local, causando una diferencia horaria igual al desplazamiento de tu zona horaria.

## Solución

Este archivo de registro configura Windows para usar hora UTC en el reloj de hardware, haciéndolo compatible con el enfoque de Linux.

## Instalación

1. **Descarga** el archivo `.reg`
2. **Haz clic derecho** en el archivo y selecciona **"Combinar"**
3. **Confirma** los cambios en el registro cuando se te solicite
4. **Reinicia** tu computadora para que los cambios surtan efecto

## Contenido del Registro

El archivo configura:

- Zona horaria a Romance Standard Time (Hora de Europa Central)
- Manejo de hora UTC (`RealTimeIsUniversal=1`)
- Valores de bias apropiados para el desplazamiento de zona horaria
- Reglas de horario de verano

## Verificación

Después de aplicar la corrección:

1. Inicia Windows y verifica si la hora es correcta
2. Inicia Linux y verifica que la hora también sea correcta
3. La hora ahora debería ser consistente entre ambos sistemas operativos

## Revertir Cambios

Para volver al comportamiento predeterminado de Windows:

1. Abre el Editor del Registro
2. Navega a `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\TimeZoneInformation`
3. Elimina el valor `RealTimeIsUniversal` o establécelo en `0`
4. Reinicia tu computadora
