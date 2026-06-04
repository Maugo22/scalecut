"""
ScaleCut — Example: Acme Studio / Lanzamiento Q4 2024
------------------------------------------------------
Demonstrates programmatic usage of the ScaleCut Python API.
Run from the repo root with the venv active:

    python examples/generate_example.py
"""

import sys
from pathlib import Path

# Allow running without `pip install -e .`
sys.path.insert(0, str(Path(__file__).parent.parent))

from scalecut.models import ProjectConfig
from scalecut.folders import create_folders
from scalecut.checklist import write_csv, write_markdown
from scalecut.config_gen import write_config
from scalecut.readme_gen import write_readme
from scalecut.preview import show_preview
from scalecut.naming import generate_all_filenames

# ── Project definition ────────────────────────────────────────────────────────

EXAMPLE_CONFIG = ProjectConfig(
    client="Acme Studio",
    project="Lanzamiento Q4",
    project_type="Campaña publicitaria",
    delivery_date="2024-12-20",
    num_clips=4,
    platforms=["Instagram Reels", "TikTok", "LinkedIn", "YouTube"],
    formats=["9x16", "1x1", "16x9"],
    version="01",
    language="ES",
    initial_status="Not started",
    output_path=str(Path(__file__).parent),
)

# ── Generate ──────────────────────────────────────────────────────────────────

def main() -> None:
    config = EXAMPLE_CONFIG

    show_preview(config)

    print("Generating project files...")
    root = create_folders(config)
    write_csv(config, root)
    write_markdown(config, root)
    write_config(config, root)
    write_readme(config, root)

    deliverables = generate_all_filenames(config)
    print(f"\n  Root  : {root}")
    print(f"  Files : checklist.csv, checklist.md, project_config.json, README.md")
    print(f"  Total deliverables: {len(deliverables)}")
    print("\nDone.")


if __name__ == "__main__":
    main()
