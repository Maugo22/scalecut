"""Generate editor_instructions.md — workflow guide for Premiere Pro and DaVinci Resolve."""

from pathlib import Path
from scalecut.models import ProjectConfig
from scalecut.naming import generate_all_filenames, sanitize
from scalecut.folders import build_folder_tree
from scalecut import __version__

FOLDER_HINTS = {
    "01_Footage":      "footage bruto de cámara",
    "02_Audio":        "música, voz en off, SFX",
    "03_Graphics":     "motion graphics, overlays, logos",
    "04_Project_Files":"archivos .prproj / .drp",
    "05_Sequences":    "secuencias de edición exportadas",
    "06_Subtitles":    "archivos .srt / .vtt / .ass",
    "07_Exports":      "exports finales por formato",
    "08_Delivery":     "entregables aprobados listos para enviar",
    "09_References":   "briefs, moodboards y referencias del cliente",
    "10_Admin":        "checklists, config y documentos del proyecto",
}

FORMAT_SPECS = {
    "9x16":  ("1080 × 1920 px", "Vertical — Instagram Reels, TikTok, Shorts"),
    "1x1":   ("1080 × 1080 px", "Cuadrado — LinkedIn, Facebook, feed"),
    "16x9":  ("1920 × 1080 px", "Horizontal — YouTube, website, presentaciones"),
}


def write_editor_instructions(config: ProjectConfig, root: Path) -> Path:
    out = root / "10_Admin" / "editor_instructions.md"

    deliverables = generate_all_filenames(config)
    total = len(deliverables)

    from collections import defaultdict
    by_clip: dict[str, list] = defaultdict(list)
    for d in deliverables:
        by_clip[d["clip"]].append(d)

    client_slug  = sanitize(config.client)
    project_slug = sanitize(config.project)
    date_slug    = config.delivery_date.replace("-", "")
    version_slug = f"V{config.version.zfill(2)}"

    lines = [
        "# Instrucciones para Editor",
        f"## {config.client} — {config.project}",
        "",
        f"> Generado por **ScaleCut v{__version__}** · {config.created_at[:10]}  ",
        "> Comparte este archivo con el editor antes de empezar la producción.",
        "",
        "---",
        "",
        "## Resumen del proyecto",
        "",
        "| Campo | Valor |",
        "|-------|-------|",
        f"| Cliente | {config.client} |",
        f"| Proyecto | {config.project} |",
        f"| Tipo | {config.project_type} |",
        f"| Fecha de entrega | {config.delivery_date} |",
        f"| Idioma | {config.language} |",
        f"| Versión | {version_slug} |",
        f"| Clips | {config.num_clips} |",
        f"| Plataformas | {', '.join(config.platforms)} |",
        f"| Formatos | {', '.join(config.formats)} |",
        f"| **Total entregables** | **{total}** |",
        "",
        "---",
        "",
        "## Estructura de carpetas",
        "",
        "```",
        f"{root.name}/",
    ]

    for folder in build_folder_tree(config):
        depth  = folder.count("/")
        indent = "  " * (depth + 1)
        name   = folder.split("/")[-1]
        hint   = FOLDER_HINTS.get(name, "")
        hint_str = f"   ← {hint}" if hint else ""
        lines.append(f"{indent}{name}/{hint_str}")

    lines += [
        "```",
        "",
        "---",
        "",
        "## Convención de naming",
        "",
        "**Patrón:**",
        "```",
        "CLIENT_PROJECT_ClipNN_PLATFORM_FORMAT_YYYYMMDD_VNN.mp4",
        "```",
        "",
        "| Token | Valor en este proyecto |",
        "|-------|------------------------|",
        f"| CLIENT | `{client_slug}` |",
        f"| PROJECT | `{project_slug}` |",
        f"| Date | `{date_slug}` |",
        f"| Version | `{version_slug}` |",
        "",
        "**Ejemplos reales:**",
        "```",
    ]

    for platform in config.platforms[:2]:
        for fmt in config.formats[:1]:
            from scalecut.naming import build_filename
            example = build_filename(config, 1, platform, fmt)
            lines.append(example)

    lines += [
        "```",
        "",
        "---",
        "",
        "## Plataformas y formatos requeridos",
        "",
        "| Plataforma | Formato | Resolución | Uso |",
        "|------------|---------|------------|-----|",
    ]

    for platform in config.platforms:
        for fmt in config.formats:
            res, uso = FORMAT_SPECS.get(fmt, ("—", "—"))
            lines.append(f"| {platform} | {fmt} | {res} | {uso} |")

    lines += [
        "",
        "---",
        "",
        f"## Lista de exports esperados — {total} archivos",
        "",
    ]

    for clip, items in by_clip.items():
        lines += [f"### {clip}", ""]
        for d in items:
            lines.append(f"- [ ] `{d['filename']}`")
        lines.append("")

    lines += [
        "---",
        "",
        "## Flujo de trabajo — Premiere Pro",
        "",
        f"1. **Crear proyecto**: `Archivo > Nuevo > Proyecto` → guardar en `04_Project_Files/{project_slug}.prproj`",
        "2. **Importar footage**: `Media Browser` → navegar a `01_Footage/` → importar todos los clips.",
        "3. **Crear bins**: Crear un bin por clip (`Clip01`, `Clip02`…) y uno por formato (`9x16`, `1x1`, `16x9`).",
        "4. **Crear secuencias**: Una secuencia por clip + formato con la resolución correcta:",
    ]

    for fmt in config.formats:
        res, _ = FORMAT_SPECS.get(fmt, ("—", ""))
        lines.append(f"   - `{fmt}` → {res}")

    lines += [
        "5. **Subtítulos**: Exportar archivos `.srt` a `06_Subtitles/`.",
        "6. **Exportar**:",
        "   - `Archivo > Exportar > Media` → Format: **H.264**",
        "   - Usar el nombre exacto de `naming_preview.md`",
        "   - Destino: `07_Exports/{formato}/`",
        "7. **Delivery**: Mover archivos aprobados a `08_Delivery/`.",
        "8. **Checklist**: Marcar cada entregable en `10_Admin/delivery_checklist.md`.",
        "",
        "---",
        "",
        "## Flujo de trabajo — DaVinci Resolve",
        "",
        f"1. **Nuevo proyecto**: `File > New Project` → guardar en `04_Project_Files/{project_slug}.drp`",
        "2. **Media page**: Agregar `01_Footage/` al Media Pool. Crear bins por clip.",
        "3. **Cut / Edit page**: Crear timelines individuales — una por clip y formato:",
    ]

    for fmt in config.formats:
        res, _ = FORMAT_SPECS.get(fmt, ("—", ""))
        lines.append(f"   - `{fmt}` → {res}")

    lines += [
        "4. **Subtítulos**: Usar la herramienta de subtítulos de Resolve → exportar a `06_Subtitles/`.",
        "5. **Deliver page**:",
        "   - Preset: **H.264 Master** (o el preset del cliente)",
        "   - Nombre: usar el nombre exacto de `naming_preview.md`",
        "   - Destino: `07_Exports/{formato}/`",
        "6. **Render queue**: Agregar todos los jobs y ejecutar.",
        "7. **Delivery**: Mover a `08_Delivery/` los archivos aprobados.",
        "",
        "---",
        "",
        "## Notas de entrega",
        "",
        f"- Fecha límite: **{config.delivery_date}**",
        f"- Subir entregables a `08_Delivery/` antes de esa fecha.",
        f"- Actualizar el estado de cada pieza en `10_Admin/delivery_checklist.csv`.",
        "- Para cambios de versión: incrementar el número `VNN` en el filename.",
        f"- Consultas al cliente: referenciar siempre el nombre exacto del archivo.",
        "",
    ]

    out.write_text("\n".join(lines), encoding="utf-8")
    return out
