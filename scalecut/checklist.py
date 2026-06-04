"""Generate delivery_checklist.csv and delivery_checklist.md."""

import csv
from collections import defaultdict
from pathlib import Path
from scalecut.models import ProjectConfig
from scalecut.naming import generate_all_filenames

CSV_HEADERS = ["Clip", "Platform", "Format", "Language", "Version", "Status", "Filename", "Export_Path", "Notes"]


def _export_path(fmt: str, filename: str) -> str:
    return f"07_Exports/{fmt}/{filename}"


def write_csv(config: ProjectConfig, root: Path) -> Path:
    deliverables = generate_all_filenames(config)
    out = root / "10_Admin" / "delivery_checklist.csv"

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for d in deliverables:
            writer.writerow({
                "Clip":        d["clip"],
                "Platform":    d["platform"],
                "Format":      d["format"],
                "Language":    d["language"],
                "Version":     d["version"],
                "Status":      d["status"],
                "Filename":    d["filename"],
                "Export_Path": _export_path(d["format"], d["filename"]),
                "Notes":       "",
            })
    return out


def write_markdown(config: ProjectConfig, root: Path) -> Path:
    deliverables = generate_all_filenames(config)
    out = root / "10_Admin" / "delivery_checklist.md"

    # Group by clip
    by_clip: dict[str, list] = defaultdict(list)
    for d in deliverables:
        by_clip[d["clip"]].append(d)

    total = len(deliverables)

    lines = [
        f"# Delivery Checklist",
        f"## {config.client} — {config.project}",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Type | {config.project_type} |",
        f"| Delivery | {config.delivery_date} |",
        f"| Language | {config.language} |",
        f"| Version | V{config.version.zfill(2)} |",
        f"| Platforms | {', '.join(config.platforms)} |",
        f"| Formats | {', '.join(config.formats)} |",
        f"| Total | **{total} entregables** |",
        "",
        "---",
        "",
    ]

    for clip, items in by_clip.items():
        lines += [
            f"## {clip} — {len(items)} entregables",
            "",
        ]
        for d in items:
            lines.append(
                f"- [ ] `{d['filename']}`  "
                f"— {d['platform']} · {d['format']}"
            )
        lines.append("")

    lines += [
        "---",
        "",
        "## Progress tracker",
        "",
        "| Status | Count |",
        "|--------|-------|",
        f"| Not started | {total} |",
        "| In edit | 0 |",
        "| Ready for review | 0 |",
        "| Approved | 0 |",
        "| Exported | 0 |",
        "| Delivered | 0 |",
        "",
    ]

    out.write_text("\n".join(lines), encoding="utf-8")
    return out
