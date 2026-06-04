"""Fuzzy project path resolution for ScaleCut commands."""

import re
from pathlib import Path


class ProjectPathError(Exception):
    pass


def _normalize(name: str) -> str:
    """Strip separators and lowercase for fuzzy comparison."""
    return re.sub(r"[\s_\-]+", "", name).lower()


def resolve_project_path(path) -> Path:
    """
    Return the resolved Path for a ScaleCut project folder.

    If the path exists, return it directly. Otherwise search the parent
    directory for a folder whose normalized name matches the normalized
    basename of the given path (e.g. 'AcmeStudio_Foo_2026-06-10' resolves
    to 'ACMESTUDIO_FOO_20260610').
    """
    root = Path(path)

    if root.exists():
        return root

    parent = root.parent
    target = _normalize(root.name)

    if not parent.exists():
        raise ProjectPathError(f"Path no encontrado: {root}")

    matches = [d for d in parent.iterdir() if d.is_dir() and _normalize(d.name) == target]

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        names = ", ".join(d.name for d in sorted(matches))
        raise ProjectPathError(
            f"Múltiples proyectos coinciden con '{root.name}': {names}"
        )

    raise ProjectPathError(f"Path no encontrado: {root}")
