# Keybrame - OBS Image Switcher

Cambiá imágenes en OBS en tiempo real usando teclas y mouse. Ideal para mostrar cámaras de manos, overlays dinámicos o cualquier imagen que cambie según tus inputs.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

## Características

- **Atajos de teclado y mouse** — detecta globalmente cualquier tecla, combinación o botón del mouse
- **Dos modos**: Toggle (activa/desactiva) y Hold (activo mientras mantenés presionado)
- **Transiciones animadas** — GIFs de entrada y salida con duración auto-detectada
- **Panel web de administración** — interfaz para configurar todo desde el navegador
- **Vista previa en tiempo real** — ves los cambios mientras los configurás
- **Actualizaciones automáticas** — el programa avisa cuando hay una nueva versión
- **Soporte de mouse** — click izquierdo, derecho, central y scroll

## Instalación

1. Descargá `Keybrame-Setup.exe` desde [Releases](https://github.com/TpmyCT/keybrame/releases/latest)
2. Ejecutá el instalador y seguí los pasos
3. Buscá "Keybrame" en el menú de inicio de Windows y abrilo

> Windows puede mostrar "Windows protegió tu PC". Click en "Más información" → "Ejecutar de todas formas". Es normal con programas nuevos sin firma digital.

## Uso con OBS

1. Abrí Keybrame — el panel de administración se abre automáticamente en el navegador
2. En OBS, agregá una fuente **Browser Source**
3. Copiá la URL que aparece en el panel y pegála en OBS
4. Configurá tus atajos desde el panel y listo

## Configuración

Todo se hace desde el panel web. No hay archivos de configuración que editar manualmente.

### Subir imágenes
Arrastrá imágenes a la galería o hacé click para examinar. Formatos soportados: PNG, JPG, GIF, WEBP, BMP.

### Crear atajos
1. Click en **Agregar Atajo**
2. Grabá las teclas con el botón de grabación
3. Elegí el tipo: **Alternar** o **Mantener**
4. Seleccioná la imagen (y opcionalmente una transición de entrada/salida)

### Imagen predeterminada
La imagen que se muestra cuando no hay ningún atajo activo. Se configura en la sección de Configuración.

## Tipos de atajo

| Tipo | Comportamiento |
|------|---------------|
| **Alternar** | Primera pulsación activa, segunda desactiva |
| **Mantener** | Activo mientras mantenés presionada la tecla, se desactiva al soltar |

Los combos (múltiples teclas a la vez) funcionan con ambos tipos.

## Prioridad

Cuando hay varias condiciones activas simultáneamente, el sistema evalúa en este orden:
1. Combinaciones de teclas
2. Teclas en modo Hold
3. Imagen predeterminada

## Desinstalación

Desde **Agregar o quitar programas** en Windows, buscá "Keybrame" y desinstalalo.

## Desarrollo

### Requisitos
- Python 3.8+
- Las dependencias en `requirements.txt`

### Ejecutar desde código fuente
```bash
pip install -r requirements.txt
python server.py
```

### Compilar el ejecutable
```bash
python scripts/generate_favicon.py
python scripts/build.py
```

## Licencia

MIT — ver [LICENSE](LICENSE)
