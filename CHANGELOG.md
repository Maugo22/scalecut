# Changelog

All notable changes to ScaleCut will be documented in this file.

---

## [0.1.0] — 2026-06-03 · Initial MVP Release

### Added

#### CLI
- Interactive 5-step wizard (`python main.py`) powered by `questionary` + `rich`
- Non-interactive `quick` command for scripting and CI pipelines
- `templates` command — lists all 7 project templates with descriptions
- Auto-detection of formats from selected platforms
- Per-step recap summaries and deliverable count calculation before scaffold

#### Project templates (7)
- Podcast Repurposing
- Reels/Shorts para marca personal
- Campaña publicitaria
- Curso online
- Testimoniales
- UGC Content
- YouTube long-form + Shorts

#### Folder structure generator
- Creates 10 standard production directories per project
- Auto-generates `07_Exports/{format}/` subfolders for each selected format
- Idempotent — safe to run multiple times on the same path

#### File naming engine
- Convention: `CLIENT_PROJECT_ClipNN_PLATFORM_FORMAT_YYYYMMDD_VNN.mp4`
- Sanitizes client and project names (spaces → underscores, special chars removed, uppercase)
- Platform slug mapping for all 9 supported platforms
- Zero-padded clip numbers and version strings
- Supports custom file extensions (`.mp4`, `.mov`, `.mxf`)

#### Platform–format rules (9 platforms)
- Instagram Reels → 9x16
- TikTok → 9x16
- YouTube Shorts → 9x16
- Stories → 9x16
- LinkedIn → 1x1, 16x9
- YouTube → 16x9
- Facebook → 1x1, 16x9
- Ads → 9x16, 1x1, 16x9
- Website → 16x9

#### Generated project files (5)
- **`delivery_checklist.csv`** — full deliverable list with Clip, Platform, Format, Language, Version, Status, Filename, Export_Path, Notes columns
- **`delivery_checklist.md`** — checkboxes grouped by clip with progress tracker table
- **`naming_preview.md`** — naming pattern, token breakdown, and all filenames grouped by clip and platform
- **`project_config.json`** — machine-readable project data with summary counts and generated_files list
- **`README.md`** — project briefing with naming example, folder structure and workflow

#### Test suite (108 tests)
- `tests/test_naming.py` — 67 tests covering `sanitize`, `build_filename`, `generate_all_filenames`
- `tests/test_generators.py` — 41 integration tests covering all 5 generators and folder creation using `tmp_path`

#### CI
- GitHub Actions workflow (`tests.yml`) — runs on every PR and push to `master` with Python 3.11

#### Examples
- `examples/generate_example.py` — programmatic API usage demo (Acme Studio project)
- `examples/run_example.sh` — CLI usage demo
- `examples/validate_output.py` — 28-assertion output validation script

### Technical stack
- Python 3.10+
- `click` — CLI framework
- `questionary` — interactive prompts
- `rich` — terminal formatting
- `pytest` — test runner

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features including:
- `v0.2` — `scalecut update`, `scalecut report`, shell completions
- `v0.3` — Premiere Pro CEP panel
- `v0.4` — DaVinci Resolve scripting integration
- `v1.0` — Web UI and team workspaces
