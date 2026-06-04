"""Create project folder structure on disk."""

import os
from pathlib import Path
from scalecut.models import ProjectConfig


FOLDERS = [
    "01_Footage",
    "02_Audio",
    "03_Graphics",
    "04_Project_Files",
    "05_Sequences",
    "06_Subtitles",
    "07_Exports",
    "08_Delivery",
    "09_References",
    "10_Admin",
]


def _export_subfolders(formats: list) -> list[str]:
    """Return export subfolders only for formats used in this project."""
    return [f"07_Exports/{fmt}" for fmt in formats]


def build_folder_tree(config: ProjectConfig) -> list[str]:
    """Return ordered list of relative folder paths to create."""
    paths = list(FOLDERS)
    for fmt in config.formats:
        paths.append(f"07_Exports/{fmt}")
    return paths


def create_folders(config: ProjectConfig) -> Path:
    """Create full folder structure and return root path."""
    root = Path(config.output_path) / config.folder_name()
    root.mkdir(parents=True, exist_ok=True)

    for folder in build_folder_tree(config):
        (root / folder).mkdir(parents=True, exist_ok=True)

    return root
