# ScaleCut — Examples

This folder contains a reference project and utility scripts for validating ScaleCut output.

---

## Contents

```
examples/
├── generate_example.py             ← programmatic API usage
├── run_example.sh                  ← CLI usage (bash)
├── validate_output.py              ← 28-assertion validation suite
└── ACME_STUDIO_LANZAMIENTO_Q4_20241220/   ← generated project
    ├── 01_Footage/
    ├── 02_Audio/
    ├── 03_Graphics/
    ├── 04_Project_Files/
    ├── 05_Sequences/
    ├── 06_Subtitles/
    ├── 07_Exports/
    │   ├── 9x16/
    │   ├── 1x1/
    │   └── 16x9/
    ├── 08_Delivery/
    ├── 09_References/
    ├── 10_Admin/
    │   ├── checklist.csv          ← 48 deliverables, spreadsheet-ready
    │   ├── checklist.md           ← same, Markdown table
    │   └── project_config.json   ← machine-readable project data
    └── README.md
```

---

## Project spec

| Field | Value |
|-------|-------|
| Client | Acme Studio |
| Project | Lanzamiento Q4 |
| Type | Campaña publicitaria |
| Delivery | 2024-12-20 |
| Clips | 4 |
| Platforms | Instagram Reels, TikTok, LinkedIn, YouTube |
| Formats | 9x16, 1x1, 16x9 |
| Total deliverables | **48** (4 clips × 4 platforms × 3 formats) |

---

## Run the example

### Option A — CLI

```bash
source .venv/bin/activate
bash examples/run_example.sh
```

### Option B — Python API

```bash
source .venv/bin/activate
python examples/generate_example.py
```

---

## Validate output

```bash
python examples/validate_output.py
```

Checks (28 assertions):
- 13 folders exist
- 4 admin files present and non-empty
- CSV has 48 rows with correct columns
- All 48 filenames match `CLIENTE_PROYECTO_ClipNN_SLUG_FMT_YYYYMMDD_VNN.mp4`
- All clips, platforms, and formats are represented
- `project_config.json` is valid and contains expected values
- Markdown checklist contains all 48 filenames

---

## Sample filenames

```
ACME_STUDIO_LANZAMIENTO_Q4_Clip01_INSTA_9x16_20241220_V01.mp4
ACME_STUDIO_LANZAMIENTO_Q4_Clip01_TIKTOK_9x16_20241220_V01.mp4
ACME_STUDIO_LANZAMIENTO_Q4_Clip01_LINKEDIN_1x1_20241220_V01.mp4
ACME_STUDIO_LANZAMIENTO_Q4_Clip01_YT_16x9_20241220_V01.mp4
ACME_STUDIO_LANZAMIENTO_Q4_Clip04_YT_16x9_20241220_V01.mp4
```
