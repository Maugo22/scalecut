"""
ScaleCut — Output validation script
------------------------------------
Reads the generated Acme Studio project and checks:
  1. All 13 expected folders exist.
  2. All 4 admin files are present and non-empty.
  3. CSV has exactly 48 rows (+ header) with correct columns.
  4. All 48 filenames follow the naming convention.
  5. project_config.json is valid JSON and matches the project spec.
  6. Markdown checklist contains all 48 filenames.

Run from the repo root with the venv active:
    python examples/validate_output.py
"""

import sys
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent / "ACME_STUDIO_LANZAMIENTO_Q4_20241220"
ADMIN = ROOT / "10_Admin"

PASS = "\033[32m PASS\033[0m"
FAIL = "\033[31m FAIL\033[0m"

errors: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"{PASS}  {label}")
    else:
        msg = f"{label}" + (f" — {detail}" if detail else "")
        print(f"{FAIL}  {msg}")
        errors.append(msg)


# ── 1. Folder structure ───────────────────────────────────────────────────────

print("\n[1] Folder structure")

expected_folders = [
    "01_Footage", "02_Audio", "03_Graphics", "04_Project_Files",
    "05_Sequences", "06_Subtitles", "07_Exports",
    "07_Exports/9x16", "07_Exports/1x1", "07_Exports/16x9",
    "08_Delivery", "09_References", "10_Admin",
]

for folder in expected_folders:
    check(f"  {folder}/", (ROOT / folder).is_dir())

# ── 2. Admin files present and non-empty ─────────────────────────────────────

print("\n[2] Admin files")

admin_files = [
    ADMIN / "delivery_checklist.csv",
    ADMIN / "delivery_checklist.md",
    ADMIN / "naming_preview.md",
    ADMIN / "project_config.json",
    ROOT / "README.md",
]

for f in admin_files:
    check(f"  {f.name}", f.exists() and f.stat().st_size > 0)

# ── 3. CSV integrity ──────────────────────────────────────────────────────────

print("\n[3] CSV integrity")

EXPECTED_COLUMNS = ["Clip", "Platform", "Format", "Language", "Version", "Status", "Filename", "Export_Path", "Notes"]
EXPECTED_ROWS = 48

with open(ADMIN / "delivery_checklist.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

check("  Columns match spec", list(rows[0].keys()) == EXPECTED_COLUMNS,
      f"got {list(rows[0].keys())}")
check(f"  Row count = {EXPECTED_ROWS}", len(rows) == EXPECTED_ROWS,
      f"got {len(rows)}")

# ── 4. Filename convention ────────────────────────────────────────────────────

print("\n[4] Filename convention")

# Pattern: WORD_WORD_..._ClipNN_SLUG_FMT_YYYYMMDD_VNN.mp4
PATTERN = re.compile(
    r"^[A-Z0-9_]+_Clip\d{2}_[A-Z0-9]+_(?:9x16|1x1|16x9)_\d{8}_V\d{2}\.mp4$"
)

bad_names = [r["Filename"] for r in rows if not PATTERN.match(r["Filename"])]
check(f"  All {len(rows)} filenames match convention",
      len(bad_names) == 0,
      f"Non-conforming: {bad_names[:3]}")

# Check all clips represented
clips_found = {r["Clip"] for r in rows}
check("  Clips 01–04 all present",
      clips_found == {"Clip01", "Clip02", "Clip03", "Clip04"},
      f"found {sorted(clips_found)}")

# Check all platforms represented
platforms_found = {r["Platform"] for r in rows}
expected_platforms = {"Instagram Reels", "TikTok", "LinkedIn", "YouTube"}
check("  All 4 platforms present",
      platforms_found == expected_platforms,
      f"found {platforms_found}")

# Check all formats represented
formats_found = {r["Format"] for r in rows}
check("  All 3 formats present",
      formats_found == {"9x16", "1x1", "16x9"},
      f"found {formats_found}")

# ── 5. project_config.json ────────────────────────────────────────────────────

print("\n[5] project_config.json")

with open(ADMIN / "project_config.json", encoding="utf-8") as f:
    cfg = json.load(f)

check("  Valid JSON",              True)  # would have raised above
check("  scalecut_version present", "scalecut_version" in cfg)
check("  summary.total_deliverables = 48",
      cfg.get("summary", {}).get("total_deliverables") == EXPECTED_ROWS,
      f"got {cfg.get('summary', {}).get('total_deliverables')}")
check("  project.client = 'Acme Studio'",
      cfg["project"]["client"] == "Acme Studio")
check("  project.delivery_date correct",
      cfg["project"]["delivery_date"] == "2024-12-20")
check("  folder_structure has 13 entries",
      len(cfg.get("folder_structure", [])) == 13,
      f"got {len(cfg.get('folder_structure', []))}")

# ── 6. Markdown completeness ──────────────────────────────────────────────────

print("\n[6] Markdown checklist")

md_text = (ADMIN / "delivery_checklist.md").read_text(encoding="utf-8")

md_filenames_found = sum(1 for r in rows if r["Filename"] in md_text)
check(f"  All {EXPECTED_ROWS} filenames present in Markdown",
      md_filenames_found == EXPECTED_ROWS,
      f"found {md_filenames_found}")
check("  Progress tracker section present", "## Progress tracker" in md_text)

# ── Summary ───────────────────────────────────────────────────────────────────

print()
if errors:
    print(f"\033[31m{len(errors)} check(s) failed:\033[0m")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    total = len(expected_folders) + len(admin_files) + 11
    print(f"\033[32mAll checks passed ({total} assertions).\033[0m")
