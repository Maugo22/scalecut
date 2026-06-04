"""List ScaleCut projects found inside a base directory."""

from pathlib import Path

from scalecut.report import load_report
from scalecut.templates import STATUSES


class ListError(Exception):
    pass


def _status_summary(status_counts: dict, total: int) -> str:
    """Compact status string showing only non-zero counts in workflow order."""
    parts = []
    for s in STATUSES:
        n = status_counts.get(s, 0)
        if n:
            parts.append(f"{n} {s}")
    return "  ·  ".join(parts) if parts else "—"


def _is_valid_project(path: Path) -> bool:
    return (
        (path / "10_Admin" / "project_config.json").exists()
        and (path / "10_Admin" / "delivery_checklist.csv").exists()
    )


def find_projects(base_path="./output") -> list[dict]:
    """
    Scan base_path for ScaleCut project folders and return report data
    for each valid one, sorted by delivery_date then project name.

    Folders missing project_config.json or delivery_checklist.csv are skipped.
    """
    base = Path(base_path)

    if not base.exists():
        raise ListError(f"Carpeta no encontrada: {base}")

    if not base.is_dir():
        raise ListError(f"No es una carpeta: {base}")

    results = []
    for candidate in sorted(base.iterdir()):
        if not candidate.is_dir() or not _is_valid_project(candidate):
            continue
        try:
            data = load_report(candidate)
            data["path"] = str(candidate)
            data["status_summary"] = _status_summary(data["status_counts"], data["total"])
            results.append(data)
        except Exception:
            continue

    results.sort(key=lambda d: (d["delivery_date"], d["project"]))
    return results
