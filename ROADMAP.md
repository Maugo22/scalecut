# ScaleCut — Roadmap

## v0.1 (current) — Local CLI MVP

- [x] Interactive wizard
- [x] Folder structure creation
- [x] Naming convention engine
- [x] CSV + Markdown checklist
- [x] `project_config.json`
- [x] Project `README.md`
- [x] Export name preview
- [x] 7 project templates
- [x] `quick` non-interactive command

---

## v0.2 — CLI improvements

- [ ] `scalecut update` — update status of a deliverable in checklist
- [ ] `scalecut report` — progress summary from existing `project_config.json`
- [ ] `scalecut add-clips` — add more clips to an existing project
- [ ] Config file (`~/.scalecut/config.toml`) for default output path, language, etc.
- [ ] Shell completion (bash/zsh/fish)

---

## v0.3 — Premiere Pro panel

**Approach:** CEP (Common Extensibility Platform) panel using HTML/JS + Python bridge via ExtendScript or socket.

### Steps to build

1. Create a CEP panel with HTML/JS UI.
2. Wrap `scalecut` as a local HTTP server (`uvicorn` + FastAPI).
3. Call the API from the panel to scaffold projects and read `project_config.json`.
4. Add a "Rename sequence" button that uses the naming engine to rename the active sequence.
5. Add a bin-creation script that mirrors the folder structure as Premiere Pro bins.

### Key files

- `extensions/ScaleCut_PPro/` — CEP extension root
- `extensions/ScaleCut_PPro/index.html` — Panel UI
- `extensions/ScaleCut_PPro/js/main.js` — Panel logic
- `server/api.py` — FastAPI wrapper around `scalecut` core

---

## v0.4 — DaVinci Resolve script

**Approach:** Resolve's built-in Lua/Python scripting API (`DaVinciResolveScript`).

### Steps to build

1. Access Resolve's scripting API via `import DaVinciResolveScript as dvr`.
2. Create bins in the Media Pool that mirror the ScaleCut folder structure.
3. Use `project_config.json` to auto-create timelines named following the naming convention.
4. Add export preset automation: create render jobs for each deliverable with the correct format and name.

### Key files

- `resolve_scripts/scalecut_setup.py` — Main Resolve script
- `resolve_scripts/scalecut_export.py` — Render queue automation

### Resources

- [DaVinci Resolve Scripting API docs](https://www.blackmagicdesign.com/products/davinciresolve)
- Scripts live in: `~/.../Resolve/Fusion/Scripts/`

---

## v1.0 — SaaS / Team edition

- [ ] Web UI (Next.js or Svelte)
- [ ] Team workspaces
- [ ] Shared templates per agency
- [ ] Status updates with webhooks (Slack, Notion)
- [ ] Frame.io or Google Drive integration for delivery
