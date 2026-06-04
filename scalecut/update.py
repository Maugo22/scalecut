"""Update the status of deliverables in an existing ScaleCut project."""

import csv
import re
from pathlib import Path

from scalecut.paths import resolve_project_path, ProjectPathError
from scalecut.templates import STATUSES


class UpdateError(Exception):
    pass


def _normalize(text: str) -> str:
    """Lowercase and strip spaces/underscores/hyphens for fuzzy matching."""
    return re.sub(r"[\s_\-]+", "", text).lower()


def update_status(
    project_path,
    clip: str,
    platform: str,
    status: str,
    fmt: str | None = None,
) -> int:
    """
    Update the Status of matching rows in delivery_checklist.csv.

    Matching is exact on Clip, fuzzy on Platform (ignores spaces/case),
    and exact on Format if provided. Returns the count of updated rows.
    """
    try:
        root = resolve_project_path(project_path)
    except ProjectPathError as e:
        raise UpdateError(str(e)) from e

    checklist = root / "10_Admin" / "delivery_checklist.csv"
    if not checklist.exists():
        raise UpdateError(f"No se encontró delivery_checklist.csv en {root / '10_Admin'}")

    if status not in STATUSES:
        raise UpdateError(
            f"Status inválido: '{status}'. Válidos: {', '.join(STATUSES)}"
        )

    rows: list[dict] = []
    with open(checklist, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    clip_norm = _normalize(clip)
    platform_norm = _normalize(platform)
    fmt_norm = _normalize(fmt) if fmt else None

    updated = 0
    for row in rows:
        if _normalize(row["Clip"]) != clip_norm:
            continue
        if _normalize(row["Platform"]) != platform_norm:
            continue
        if fmt_norm and _normalize(row["Format"]) != fmt_norm:
            continue
        row["Status"] = status
        updated += 1

    if updated == 0:
        filters = f"clip='{clip}', platform='{platform}'"
        if fmt:
            filters += f", format='{fmt}'"
        raise UpdateError(f"No se encontraron entregables con {filters}")

    with open(checklist, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return updated
