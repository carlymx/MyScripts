# Fuentes de Microsoft para Linux

[📖 Read in English](./README.md)

![Logo Windows Fonts for Linux](./logo_fonts.png)

<!-- Sección de Badges -->
![Licencia](https://img.shields.io/badge/licencia-MIT-blue.svg)
![Versión](https://img.shields.io/badge/versión-1.0.0-green.svg)
![Bash](https://img.shields.io/badge/shell-bash-orange.svg)
![Linux](https://img.shields.io/badge/plataforma-Linux-yellow.svg)
![Fuentes](https://img.shields.io/badge/fuentes-178+-ff69b4.svg)

## Descripción

Un script bash simple y eficiente para instalar y desinstalar fuentes de Microsoft Windows en sistemas Linux. Este proyecto incluye **más de 178 fuentes populares de Microsoft** organizadas en dos categorías:

- **Fuentes Básicas (48)**: Las fuentes más comúnmente usadas para documentos cotidianos
- **Fuentes Extras (130)**: Fuentes adicionales incluyendo fuentes especializadas y de idiomas asiáticos

El script proporciona un sistema de menús fácil de usar que te permite:
- **Instalar** fuentes (solo básicas, solo extras o todas)
- **Desinstalar** fuentes de directorios de usuario o del sistema
- **Verificar** el estado actual de la instalación

Soporta instalación/desinstalación tanto a nivel de usuario (`~/.fonts/`) como en todo el sistema (`/usr/share/fonts/`).

Perfecto para usuarios que necesitan compatibilidad con fuentes Microsoft para documentos, presentaciones o aplicaciones que requieren fuentes Windows en Linux.

## Tabla de Contenidos

- [Descripción](#descripción)
- [Instalación](#instalación)
- [Uso](#uso)
- [Fuentes Incluidas](#fuentes-incluidas)
- [Contribuir](#contribuir)
- [Licencia](#licencia)
- [Agradecimientos](#agradecimientos)

## Instalación

### Requisitos Previos

- Sistema operativo Linux
- Shell Bash
- Comando `fc-cache` (generalmente proporcionado por el paquete `fontconfig`)
- Privilegios `sudo` (solo para instalación en todo el sistema)

### Instalación Rápida

```bash
# Clonar el repositorio
git clone <repo-url>

# Navegar al directorio
cd "Fuentes de Microsoft para Linux"

# Ejecutar el instalador
chmod +x instalar_fuentes.sh
./instalar_fuentes.sh
```

### Instalación Manual

1. Descarga o clona este repositorio
2. Abre una terminal en el directorio del proyecto
3. Haz el script ejecutable: `chmod +x instalar_fuentes.sh`
4. Ejecuta el script: `./instalar_fuentes.sh`

## Uso

Cuando ejecutes el script, verás el menú principal con el estado actual de las fuentes instaladas:

```bash
./instalar_fuentes.sh
```

### Menú Principal

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

### Instalar Fuentes

**Paso 1: Seleccionar Paquete de Fuentes**

Elige qué fuentes quieres instalar:

**Opción 1: Fuentes Básicas (48 fuentes)**
- Arial, Times New Roman, Calibri, Cambria
- Comic Sans MS, Georgia, Verdana, Tahoma
- Trebuchet MS, Courier New, Consolas
- Impact, Webdings, Wingdings, Symbol

**Opción 2: Fuentes Extras (130 fuentes)**
- Bahnschrift, Segoe UI, Candara
- Fuentes asiáticas, fuentes técnicas, fuentes especializadas

**Opción 3: Todas las Fuentes (178 fuentes)**
- Colección completa de todas las fuentes básicas y extras

**Paso 2: Seleccionar Ubicación de Instalación**

**Opción 1: Instalar solo para el usuario actual**
- Las fuentes se instalarán en `~/.fonts/`
- No se requieren privilegios root
- Solo disponible para tu cuenta de usuario

**Opción 2: Instalar para todos los usuarios (todo el sistema)**
- Las fuentes se instalarán en `/usr/share/fonts/`
- Requiere privilegios root/sudo
- Disponible para todos los usuarios del sistema

### Desinstalar Fuentes

El script también puede desinstalar fuentes. El proceso es:

1. **Analiza** tanto el directorio de usuario (`~/.fonts/`) como el del sistema (`/usr/share/fonts/`)
2. **Muestra** qué fuentes están actualmente instaladas
3. **Pregunta** para seleccionar:
   - Desde qué ubicación(s) desinstalar (solo usuario, solo sistema o ambas)
   - Qué fuentes eliminar (básicas, extras o todas las instaladas)

**Flujo de desinstalación de ejemplo:**

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

### Ver Estado de Fuentes

Selecciona la opción 3 para ver el estado actual de la instalación de fuentes tanto en los directorios de usuario como del sistema sin realizar ningún cambio.

### Ejemplo de Salida

```
========================================
Instalador de Fuentes de Windows
========================================

¿Qué fuentes desea instalar?

1) Básicas (48 fuentes populares)
   - Arial, Times New Roman, Calibri, Cambria
   - Comic Sans MS, Georgia, Verdana, Tahoma
   - Trebuchet MS, Courier New, Consolas
   - Impact, Webdings, Wingdings, Symbol

2) Extras (130 fuentes adicionales)
   - Bahnschrift, Segoe UI, Candara
   - Fuentes asiáticas, técnicas, especializadas

3) Todas (178 fuentes completas)

Seleccione una opción (1, 2 o 3): 1

Ha seleccionado instalar las fuentes básicas.

¿Dónde desea instalar las fuentes?

1) Solo para el usuario actual (username)
2) Para todos los usuarios del sistema (requiere root)

Seleccione una opción (1 o 2): 1

Instalando fuentes básicas para el usuario actual...
Creando directorio /home/username/.fonts...
Copiando fuentes de 'basicas' a /home/username/.fonts...

✓ Fuentes básicas instaladas correctamente en /home/username/.fonts/

Actualizando caché de fuentes...

========================================
✓ Instalación completada exitosamente!
========================================

Fuentes básicas instaladas:
  - basicas: 48 fuentes

Las fuentes ahora están disponibles en su sistema.
Puede que necesite reiniciar las aplicaciones para ver los cambios.
```

### Después de la Instalación

El script actualiza automáticamente el caché de fuentes. Es posible que necesites reiniciar las aplicaciones para ver las nuevas fuentes. Para verificar la instalación:

```bash
# Listar fuentes instaladas
fc-list | grep -i "arial\|calibri\|times"
```

## Fuentes Incluidas

Este paquete incluye **más de 178 fuentes de Microsoft Windows** organizadas en dos directorios:

### Fuentes Básicas (`fuentes_windows/basicas/`) - 48 fuentes

Las fuentes más comúnmente usadas para documentos cotidianos y compatibilidad general:

- **Arial** familia (Normal, Negrita, Cursiva, Negrita Cursiva, Black)
- **Calibri** familia (Normal, Negrita, Cursiva, Negrita Cursiva, Light)
- **Cambria** familia
- **Comic Sans MS** familia
- **Consolas** familia (fuente monoespaciada)
- **Courier New** familia
- **Georgia** familia
- **Impact**
- **Tahoma** familia
- **Times New Roman** familia
- **Trebuchet MS** familia
- **Verdana** familia
- **Webdings**
- **Wingdings**
- **Symbol**

### Fuentes Extras (`fuentes_windows/extras/`) - 130 fuentes

Fuentes adicionales incluyendo fuentes especializadas, decorativas e internacionales:

- **Bahnschrift**
- **Candara** familia
- **Constantia** familia
- **Corbel** familia
- **Ebrima** familia
- **Gabriola**
- **Gadugi** familia
- **Himalaya**
- **Ink Free**
- **Leelawadee** familia
- **Malgun Gothic** familia
- **Marlett**
- **Microsoft Yi Baiti**
- **Mongolian Baiti**
- **MV Boli**
- **Nirmala UI** familia
- **Segoe** familias (UI, Print, Script, etc.)
- **Sitka** familia
- **Sylfaen**
- **Yu Gothic** familia
- Fuentes de idiomas asiáticos (MingLiu, MS Gothic, MS JhengHei, MS YaHei)
- Fuentes técnicas de SolidWorks
- Y muchas más...

### Estructura de Directorios

```
fuentes_windows/
├── basicas/          # 48 fuentes esenciales
│   ├── arial.ttf
│   ├── calibri.ttf
│   └── ...
└── extras/           # 130 fuentes adicionales
    ├── bahnschrift.ttf
    ├── segoeui.ttf
    └── ...
```

## Contribuir

¡Agradecemos las contribuciones! Por favor, sigue estos pasos:

1. Haz fork del repositorio
2. Crea una rama de funcionalidad (`git checkout -b feature/funcionalidad-increible`)
3. Haz commit de tus cambios (`git commit -m 'Añadir funcionalidad increíble'`)
4. Haz push a la rama (`git push origin feature/funcionalidad-increible`)
5. Abre un Pull Request

Por favor, asegúrate de que tus contribuciones:
- Sigan las mejores prácticas de scripting en bash
- Incluyan comentarios para lógica compleja
- Hayan sido probadas en múltiples distribuciones Linux
- No incluyan fuentes propietarias que no sean de Microsoft

## Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE) - consulta el archivo LICENSE para más detalles.

**Nota sobre las Fuentes:** Las fuentes incluidas en este paquete son productos propietarios de Microsoft. Este script de instalación se proporciona como una utilidad para ayudar a los usuarios que ya tienen acceso legítimo a estas fuentes a instalarlas en sistemas Linux. Por favor, asegúrate de cumplir con los términos de licenciamiento de fuentes de Microsoft.

## Agradecimientos

- Gracias a Microsoft por crear estas fuentes ampliamente utilizadas
- Inspirado en la necesidad de mejor compatibilidad de fuentes entre Windows y Linux
- Agradecimientos especiales a la comunidad Linux por fontconfig y las herramientas de gestión de fuentes
- Colección de fuentes obtenida de instalaciones de Windows

## Solución de Problemas

### ¿Las fuentes no aparecen en las aplicaciones?
Intenta reiniciar la aplicación o ejecutar:
```bash
fc-cache -f -v
```

### ¿Permiso denegado?
Asegúrate de que el script sea ejecutable:
```bash
chmod +x instalar_fuentes.sh
```

### ¿Fallo en la instalación en todo el sistema?
Asegúrate de tener privilegios sudo y que la contraseña sea correcta.

## Soporte

Para problemas, preguntas o sugerencias, por favor abre un issue en el repositorio.

---

**Hecho con ❤️ para la comunidad Linux**
