"""Generate CSV and Markdown checklists of deliverables."""

import csv
from pathlib import Path
from typing import List
from scalecut.models import ProjectConfig
from scalecut.naming import generate_all_filenames


CSV_HEADERS = ["Clip", "Platform", "Format", "Language", "Version", "Status", "Filename", "Notes"]


def write_csv(config: ProjectConfig, root: Path) -> Path:
    deliverables = generate_all_filenames(config)
    out = root / "10_Admin" / "checklist.csv"

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for d in deliverables:
            writer.writerow(
                {
                    "Clip":     d["clip"],
                    "Platform": d["platform"],
                    "Format":   d["format"],
                    "Language": d["language"],
                    "Version":  d["version"],
                    "Status":   d["status"],
                    "Filename": d["filename"],
                    "Notes":    "",
                }
            )
    return out


def write_markdown(config: ProjectConfig, root: Path) -> Path:
    deliverables = generate_all_filenames(config)
    out = root / "10_Admin" / "checklist.md"

    total = len(deliverables)
    lines = [
        f"# Checklist — {config.client} / {config.project}",
        "",
        f"**Tipo:** {config.project_type}  ",
        f"**Entrega:** {config.delivery_date}  ",
        f"**Total de entregables:** {total}  ",
        f"**Idioma:** {config.language}  ",
        "",
        "---",
        "",
        f"| Clip | Platform | Format | Status | Filename |",
        f"|------|----------|--------|--------|----------|",
    ]

    for d in deliverables:
        checkbox = "- [ ]"
        lines.append(
            f"| {d['clip']} | {d['platform']} | {d['format']} "
            f"| {d['status']} | `{d['filename']}` |"
        )

    lines += [
        "",
        "---",
        "",
        "## Progress",
        "",
        f"- [ ] **{total} / {total}** entregables completados",
        "",
    ]

    out.write_text("\n".join(lines), encoding="utf-8")
    return out
