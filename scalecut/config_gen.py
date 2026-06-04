"""Generate project_config.json."""

import json
from pathlib import Path
from scalecut.models import ProjectConfig
from scalecut.naming import generate_all_filenames
from scalecut.folders import build_folder_tree
from scalecut import __version__

GENERATED_FILES = [
    "README.md",
    "10_Admin/delivery_checklist.csv",
    "10_Admin/delivery_checklist.md",
    "10_Admin/naming_preview.md",
    "10_Admin/project_config.json",
]


def write_config(config: ProjectConfig, root: Path) -> Path:
    deliverables = generate_all_filenames(config)

    payload = {
        "scalecut_version": __version__,
        "project": config.to_dict(),
        "summary": {
            "total_deliverables": len(deliverables),
            "clips":     config.num_clips,
            "platforms": len(config.platforms),
            "formats":   len(config.formats),
            "platforms_list": config.platforms,
            "formats_list":   config.formats,
        },
        "folder_structure": build_folder_tree(config),
        "generated_files":  GENERATED_FILES,
        "deliverables":     deliverables,
    }

    out = root / "10_Admin" / "project_config.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
