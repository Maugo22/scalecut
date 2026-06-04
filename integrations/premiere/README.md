# ScaleCut × Premiere Pro — Integration

This directory contains the prototype scaffold for the ScaleCut ↔ Premiere Pro integration.

---

## Status

| File | Status | Notes |
|------|--------|-------|
| `prototype.jsx` | 🔧 Prototype | Markers work; sequence creation is planned |

---

## Architecture

```
ScaleCut (Python CLI / Streamlit)
    │
    └── generates edit_plan.json & markers.csv
              │
              ▼
    integrations/premiere/prototype.jsx  (this file)
    (ExtendScript — runs inside Premiere Pro)
              │
              ├── reads edit_plan.json
              ├── createMarkersFromEditPlan()      ← 🔧 partial
              ├── createSubsequenceFromTimecodes() ← 📋 planned
              ├── createSequencesForDeliverables() ← 📋 planned
              └── applyExportNaming()              ← 📋 planned
```

---

## Two ways to run the script

### Path A — Standalone script (testing, no panel)

1. Generate a project with ScaleCut (CLI or Streamlit UI).
2. Enable **Edit Plan** and generate `edit_plan.json`.
3. Open your Premiere Pro project.
4. **File → Scripts → Run Script File…**
5. Select `prototype.jsx`.
6. The script auto-detects `10_Admin/edit_plan.json` next to your `.prproj` file.

### Path B — CEP Panel (production plugin, future)

A CEP (Common Extensibility Platform) extension wraps this script in an HTML/JS panel:

```
extensions/ScaleCut_PPro/
├── manifest.xml          ← CEP extension manifest
├── index.html            ← Panel UI
├── js/
│   ├── main.js           ← Panel logic (calls evalScript)
│   └── cep_utils.js
└── jsx/
    └── prototype.jsx     ← This script (backend)
```

The panel calls the script via:
```javascript
csInterface.evalScript(
    'ScaleCut.runFromPanel("' + editPlanPath + '")',
    function(result) {
        var data = JSON.parse(result);
        showStatus(data.message);
    }
);
```

---

## Data contract — `edit_plan.json`

```json
{
  "scalecut_version": "0.1.0",
  "schema_version":   "1.0",
  "fps":              25,
  "mode":             "placeholder | manual",
  "edit_plan": [
    {
      "clip_id":          "Clip01",
      "start_timecode":   "00:00:10:00",
      "end_timecode":     "00:01:25:00",
      "duration_seconds": 75.0,
      "platform":         "Instagram Reels",
      "format":           "9x16",
      "goal":             "brand awareness",
      "hook":             "hook text",
      "title":            "clip title",
      "export_filename":  "ACME_PODCAST_Clip01_INSTA_9x16_20241220_V01.mp4",
      "status":           "Not started"
    }
  ]
}
```

The script reads this file and maps each item to a Premiere marker or sequence.

---

## Premiere Pro API used

| API | Usage |
|-----|-------|
| `app.project.activeSequence` | Find the master sequence |
| `sequence.markers.createMarker(timeSecs)` | Create a comment marker |
| `marker.name / .comments / .end` | Populate marker data |
| `app.project.createNewSequence(name, preset)` | Create per-deliverable sequences *(planned)* |
| `app.encoder.encodeSequence(...)` | Add to AME render queue *(planned)* |

---

## Roadmap to full plugin

| Phase | What | Status |
|-------|------|--------|
| v0.1 (current) | Prototype scaffold + marker creation | 🔧 Partial |
| v0.2 | Sequence creation from timecodes | 📋 Planned |
| v0.3 | CEP panel UI (HTML/JS) | 📋 Planned |
| v0.4 | AME export queue with ScaleCut naming | 📋 Planned |
| v1.0 | Full panel: load plan, preview, one-click export | 📋 Planned |

---

## Requirements

- Adobe Premiere Pro CC 2019+ (for ExtendScript support)
- Adobe Media Encoder (for export queue, v0.4+)
- ScaleCut project with `edit_plan.json` (generate with `--edit-plan` flag or Streamlit UI)
