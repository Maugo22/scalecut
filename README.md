# ScaleCut

> Video production workflow scaffolding for editors, agencies, and post-production teams.

ScaleCut creates consistent project structures, file naming, and deliverable checklists for Reels, Shorts, podcasts, ad campaigns, and educational content — in seconds.

---

## Features

- Interactive CLI wizard
- Consistent folder structure (10 directories, auto format subfolders)
- Naming convention: `Cliente_Proyecto_ClipNN_Plataforma_Formato_Fecha_VNN.mp4`
- Deliverable checklist in CSV and Markdown
- `project_config.json` for tooling integration
- `README.md` per project
- 7 built-in project templates
- Export name preview before creating anything

---

## Installation

### Requirements

- Python 3.10+
- pip

### Steps

```bash
# 1. Clone or download this repo
cd scalecut

# 2. Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install
pip install -e .
```

---

## Usage

### Interactive wizard (recommended)

```bash
scalecut
# or
scalecut new
```

The wizard asks for all project details, shows a preview, and creates the full structure on confirmation.

### Quick non-interactive mode

```bash
scalecut quick ~/Desktop/ScaleCut_Projects \
  --client Nike \
  --project "Verano 2024" \
  --type "Campaña publicitaria" \
  --date 2024-12-15 \
  --clips 4 \
  --platforms "Instagram Reels,TikTok,Facebook" \
  --formats "9x16,1x1,16x9" \
  --version 01 \
  --language ES \
  --status "Not started"
```

### List available templates

```bash
scalecut templates
```

---

## Project templates

| Template | Typical use |
|----------|-------------|
| Podcast Repurposing | Highlights from podcast episodes |
| Reels/Shorts para marca personal | Personal brand short-form |
| Campaña publicitaria | Multi-platform paid ads |
| Curso online | Educational long-form + promos |
| Testimoniales | Customer stories |
| UGC Content | Organic / paid UGC |
| YouTube long-form + Shorts | Main video + derived Shorts |

---

## Generated files

```
NIKE_VERANO24_20241215/
  01_Footage/
  02_Audio/
  03_Graphics/
  04_Project_Files/
  05_Sequences/
  06_Subtitles/
  07_Exports/
    9x16/
    1x1/
    16x9/
  08_Delivery/
  09_References/
  10_Admin/
    checklist.csv
    checklist.md
    project_config.json
  README.md
```

---

## Naming convention

```
Cliente_Proyecto_ClipNN_Plataforma_Formato_Fecha_VNN.mp4

Example:
NIKE_VERANO24_Clip01_INSTA_9x16_20241215_V01.mp4
```

---

## Next steps (plugin roadmap)

See [ROADMAP.md](ROADMAP.md) for plans to extend ScaleCut into Premiere Pro panels and DaVinci Resolve scripts.
