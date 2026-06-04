"""Generate a progress report for an existing ScaleCut project."""

import csv
import json
from collections import Counter
from pathlib import Path

from scalecut.paths import resolve_project_path, ProjectPathError

DONE_STATUSES = {"Approved", "Exported", "Delivered"}


class ReportError(Exception):
    pass


def load_report(project_path) -> dict:
    """Read project_config.json + delivery_checklist.csv and return report data."""
    try:
        root = resolve_project_path(project_path)
    except ProjectPathError as e:
        raise ReportError(str(e)) from e

    config_path = root / "10_Admin" / "project_config.json"
    checklist_path = root / "10_Admin" / "delivery_checklist.csv"

    if not config_path.exists():
        raise ReportError(f"No se encontró project_config.json en {root / '10_Admin'}")

    if not checklist_path.exists():
        raise ReportError(f"No se encontró delivery_checklist.csv en {root / '10_Admin'}")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    project = config["project"]

    rows: list[dict] = []
    with open(checklist_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    total = len(rows)
    status_counts: Counter = Counter(row["Status"] for row in rows)

    pct_delivered = (
        round(status_counts.get("Delivered", 0) / total * 100, 1) if total else 0.0
    )
    advanced = sum(status_counts.get(s, 0) for s in DONE_STATUSES)
    pct_advanced = round(advanced / total * 100, 1) if total else 0.0

    platforms = sorted({row["Platform"] for row in rows})
    formats = sorted({row["Format"] for row in rows})

    return {
        "client": project["client"],
        "project": project["project"],
        "project_type": project["project_type"],
        "delivery_date": project["delivery_date"],
        "total": total,
        "status_counts": dict(status_counts),
        "pct_delivered": pct_delivered,
        "pct_advanced": pct_advanced,
        "platforms": platforms,
        "formats": formats,
        "next_action": _suggest_next_action(status_counts, total, pct_delivered, pct_advanced),
    }


def _suggest_next_action(
    status_counts: Counter, total: int, pct_delivered: float, pct_advanced: float
) -> str:
    if total == 0:
        return "No hay entregables registrados."
    if pct_delivered == 100.0:
        return "Proyecto completo — listo para archivar."
    if pct_advanced >= 80:
        return "En cierre — verifica los últimos entregables pendientes."
    if pct_advanced >= 50:
        return "Buen avance — continúa con los entregables pendientes."
    in_progress = (
        status_counts.get("In edit", 0)
        + status_counts.get("Ready for review", 0)
        + status_counts.get("Changes requested", 0)
    )
    if in_progress > 0:
        return "Hay clips en edición activa — continúa el flujo."
    if status_counts.get("Not started", 0) == total:
        return "Inicia la edición — ningún clip ha comenzado."
    return "Revisa el checklist y actualiza los estados de entrega."
