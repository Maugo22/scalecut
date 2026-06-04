"""Generate project_config.json."""

import json
from pathlib import Path
from scalecut.models import ProjectConfig
from scalecut.naming import generate_all_filenames
from scalecut.folders import build_folder_tree
from scalecut import __version__


def write_config(config: ProjectConfig, root: Path) -> Path:
    deliverables = generate_all_filenames(config)
    payload = {
        "scalecut_version": __version__,
        "project": config.to_dict(),
        "folder_structure": build_folder_tree(config),
        "deliverables_count": len(deliverables),
        "deliverables": deliverables,
    }

    out = root / "10_Admin" / "project_config.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
