"""Create a downloadable ZIP of all project admin files."""

import io
import zipfile
from pathlib import Path

PACKAGE_FILES = [
    "10_Admin/project_config.json",
    "10_Admin/delivery_checklist.csv",
    "10_Admin/delivery_checklist.md",
    "10_Admin/naming_preview.md",
    "10_Admin/editor_instructions.md",
    "10_Admin/prompts_ai.md",
    "README.md",
]


def create_zip(root: Path) -> bytes:
    """
    Bundle all admin files into an in-memory ZIP and return the raw bytes.
    Files are stored flat (no subdirectory) inside the ZIP.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for relative in PACKAGE_FILES:
            path = root / relative
            if path.exists():
                zf.write(path, path.name)
    return buffer.getvalue()
