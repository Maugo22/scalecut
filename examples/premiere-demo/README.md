# ScaleCut × Premiere Pro — Demo
## Acme Studio / Podcast Leadership

Guía paso a paso para probar `prototype.jsx` con este proyecto de demo.

---

## Archivos de este demo

| Archivo | Filas / Items | Descripción |
|---------|--------------|-------------|
| `project_config.json` | — | Metadata completa del proyecto ScaleCut |
| `delivery_checklist.csv` | 40 filas | Tracker de entregables: 5 clips × 4 plataformas × 2 formatos |
| `edit_plan.json` | 40 clips | Plan de edición con timecodes reales y datos creativos |
| `markers.csv` | 40 filas | Markers color-coded por plataforma para importar a Premiere |

### Datos del proyecto

| Campo | Valor |
|-------|-------|
| Cliente | Acme Studio |
| Proyecto | Podcast Leadership |
| Tipo | Podcast Repurposing |
| Clips | 5 |
| Plataformas | Instagram Reels, TikTok, LinkedIn, YouTube Shorts |
| Formatos | 9x16, 1x1 |
| Entregables | **40 total** |
| FPS | 25 |

### Timecodes de los clips (en el archivo de origen del podcast)

| Clip | Start TC | End TC | Duración | Tema |
|------|----------|--------|----------|------|
| Clip01 | `00:03:15:00` | `00:04:30:00` | ~75s | El poder de la escucha activa |
| Clip02 | `00:12:40:00` | `00:14:05:00` | ~85s | El error más costoso de un líder |
| Clip03 | `00:28:10:00` | `00:29:20:00` | ~70s | Por qué los equipos fracasan |
| Clip04 | `00:41:55:00` | `00:43:15:00` | ~80s | La conversación que cambió todo |
| Clip05 | `00:55:30:00` | `00:57:00:00` | ~90s | El liderazgo que los libros no enseñan |

---

## Requisitos

- Adobe Premiere Pro CC 2019 o superior
- El archivo fuente del episodio (cualquier video de +57 minutos para probar)
- El archivo `prototype.jsx` → está en `integrations/premiere/prototype.jsx`

---

## Paso 1 — Preparar el proyecto en Premiere

1. Abre Premiere Pro y crea un nuevo proyecto:
   `Archivo → Nuevo → Proyecto`

2. Nómbralo igual que la carpeta: `ACME_STUDIO_PODCAST_LEADERSHIP_20241220`

3. Guarda el `.prproj` en `04_Project_Files/` (si tienes la estructura de ScaleCut)
   o en cualquier carpeta si estás solo probando.

4. Importa el archivo de video fuente del episodio:
   `Archivo → Importar` → selecciona el archivo de video.

5. Crea una secuencia maestra desde el clip importado:
   Click derecho sobre el clip → `Nueva secuencia desde clip`
   - Renómbrala `PODCAST_MASTER` o `Secuencia Maestra`.

---

## Paso 2 — Configurar la ruta del edit_plan.json

Abre `prototype.jsx` con un editor de texto y busca la sección `ScaleCut.run()`:

```javascript
// Al final del archivo, línea ~370
ScaleCut.run();
```

Edítala para apuntar al `edit_plan.json` de este demo:

```javascript
ScaleCut.run("/ruta/completa/a/examples/premiere-demo/edit_plan.json");
```

**Ejemplo en macOS:**
```javascript
ScaleCut.run("/Users/tuusuario/scalecut/examples/premiere-demo/edit_plan.json");
```

**Ejemplo en Windows:**
```javascript
ScaleCut.run("C:/Users/tuusuario/scalecut/examples/premiere-demo/edit_plan.json");
```

---

## Paso 3 — Ejecutar el script en Premiere

1. Con tu proyecto abierto y la secuencia maestra activa, ve a:
   `Archivo → Scripts → Ejecutar archivo de script…`

2. Navega hasta `integrations/premiere/prototype.jsx` y selecciónalo.

3. Premiere ejecutará el script. Verás el resultado en la **Consola de ExtendScript**:

```
[ScaleCut] ==================================================
[ScaleCut] ScaleCut × Premiere Pro — Prototype v0.1.0
[ScaleCut] ==================================================
[ScaleCut] Loaded edit_plan.json: 40 clips, mode=manual
[ScaleCut] Project: Acme Studio / Podcast Leadership
[ScaleCut] Active sequence: PODCAST_MASTER (...)
[ScaleCut] Marker created: Clip01 — El poder de la escucha activa [00:03:15:00 → 00:04:30:00]
[ScaleCut] Marker created: Clip02 — El error más costoso de un líder [00:12:40:00 → 00:14:05:00]
[ScaleCut] Marker created: Clip03 — Por qué los equipos fracasan [00:28:10:00 → 00:29:20:00]
[ScaleCut] Marker created: Clip04 — La conversación que cambió todo [00:41:55:00 → 00:43:15:00]
[ScaleCut] Marker created: Clip05 — El liderazgo que los libros no enseñan [00:55:30:00 → 00:57:00:00]
[ScaleCut] createMarkersFromEditPlan: 5 markers created.
[ScaleCut] [PLANNED] Sequences planned: 40
[ScaleCut] Done.
```

> **Nota:** Los mensajes `[PLANNED]` son normales — indican funciones que se
> implementarán en fases futuras del plugin.

---

## Paso 4 — Verificar los markers en la línea de tiempo

1. En la línea de tiempo de Premiere, los 5 markers deben aparecer como
   marcadores de comentario (verde) en los timecodes exactos del edit_plan.

2. Haz clic en cada marker para ver:
   - **Nombre:** `Clip01 — El poder de la escucha activa`
   - **Comentario:** `Goal: brand awareness | Hook: ¿Cuándo fue la última vez...`
   - **Duración:** del start TC al end TC

3. Panel de markers (`Ventana → Marcadores`):
   Verás los 5 clips listados con nombre y timecode de entrada/salida.

---

## Paso 5 — Usar los markers para editar

Con los markers en la línea de tiempo, el flujo de edición manual es:

1. **Navegar**: presiona `M` para ir al siguiente marker.
2. **Marcar in/out**: en cada marker, presiona `I` (in) y `O` (out) para
   delimitar el clip en el Source Monitor.
3. **Insertar en secuencia**: arrastra o presiona `F9` / `F10` para insertar.
4. **Renombrar secuencias**: usa el nombre de `export_filename` de `edit_plan.json`
   como nombre de la secuencia:
   ```
   ACME_STUDIO_PODCAST_LEADERSHIP_Clip01_INSTA_9x16_20241220_V01
   ```

---

## Paso 6 (opcional) — Importar markers.csv manualmente

Si prefieres importar los markers directamente desde `markers.csv` sin correr
el script, Premiere Pro permite importar markers vía un panel de extensión o
script de terceros. El formato de `markers.csv` incluye:

- `marker_name` → nombre del marker
- `start_timecode` / `end_timecode` → en HH:MM:SS:FF a 25fps
- `color` → Cyan, Magenta, Blue, Orange (uno por plataforma)
- `export_filename` → nombre exacto del archivo de exportación

---

## Resultado esperado

Después de ejecutar el script tendrás:

```
Secuencia maestra (PODCAST_MASTER)
  │
  ├── Marker: Clip01 @ 00:03:15:00 → 00:04:30:00
  │     "El poder de la escucha activa"
  │     Goal: brand awareness | Hook: ¿Cuándo fue la última vez...
  │
  ├── Marker: Clip02 @ 00:12:40:00 → 00:14:05:00
  │     "El error más costoso de un líder"
  │     Goal: engagement | Hook: Cometí un error que nos costó...
  │
  ├── Marker: Clip03 @ 00:28:10:00 → 00:29:20:00
  │     "Por qué los equipos fracasan"
  │     Goal: education | Hook: Los equipos no fracasan por...
  │
  ├── Marker: Clip04 @ 00:41:55:00 → 00:43:15:00
  │     "La conversación que cambió todo"
  │     Goal: conversion | Hook: Una sola conversación puede...
  │
  └── Marker: Clip05 @ 00:55:30:00 → 00:57:00:00
        "El liderazgo que los libros no enseñan"
        Goal: brand awareness | Hook: Hay una habilidad de liderazgo...
```

---

## Troubleshooting

| Problema | Causa probable | Solución |
|----------|---------------|----------|
| `File not found` | Ruta incorrecta en `ScaleCut.run()` | Verifica la ruta absoluta al `edit_plan.json` |
| `No active sequence` | No hay secuencia seleccionada | Selecciona una secuencia en la línea de tiempo |
| Markers no aparecen | Script terminó con error | Revisa la Consola de ExtendScript para el error exacto |
| `eval is not defined` | Premiere muy antiguo (pre-2019) | Actualiza Premiere Pro o usa `JSON.parse()` manualmente |
| Markers en posición incorrecta | FPS del proyecto ≠ 25 | Cambia `ScaleCut.DEFAULT_FPS` en el script al FPS de tu secuencia |

---

## Qué viene en fases futuras del plugin

| Fase | Feature |
|------|---------|
| v0.2 | `createSubsequenceFromTimecodes()` — crea subsecuencias automáticamente desde los markers |
| v0.3 | Panel CEP con UI para cargar `edit_plan.json` desde Premiere directamente |
| v0.4 | `applyExportNaming()` — envía cada secuencia a AME con el nombre de ScaleCut |
| v1.0 | Un clic: cargar plan → crear secuencias → exportar con naming correcto |

---

## Referencias

- `integrations/premiere/prototype.jsx` — el script que usas en este demo
- `integrations/premiere/README.md` — arquitectura y documentación técnica del plugin
- `scalecut/edit_plan.py` — módulo Python que genera `edit_plan.json`
- `ROADMAP.md` — roadmap completo de ScaleCut incluyendo el plugin
