"""ScaleCut — Streamlit web UI."""

import csv
import html
import json
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from scalecut import __version__
from scalecut.checklist import write_csv, write_markdown
from scalecut.list_projects import find_projects, ListError
from scalecut.report import load_report, ReportError
from scalecut.update import update_status, UpdateError
from scalecut.config_gen import write_config
from scalecut.edit_plan import (
    EditPlanClip, make_placeholder_clips,
    write_edit_plan_csv, write_edit_plan_md, write_edit_plan_json, write_markers_csv,
    validate_timecodes, calculate_duration, timecode_to_seconds,
)
from scalecut.editor_instructions import write_editor_instructions
from scalecut.folders import build_folder_tree, create_folders
from scalecut.models import ProjectConfig
from scalecut.naming import generate_all_filenames, sanitize
from scalecut.package import create_zip
from scalecut.preview import write_naming_preview
from scalecut.prompts_ai import write_prompts_ai
from scalecut.readme_gen import write_readme
from scalecut.templates import (
    ALL_FORMATS,
    ALL_PLATFORMS,
    PLATFORM_FORMATS,
    PROJECT_TEMPLATES,
    STATUSES,
)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ScaleCut",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --sc-midnight: #070B16;
        --sc-panel: rgba(16, 22, 35, 0.86);
        --sc-panel-strong: rgba(24, 31, 47, 0.94);
        --sc-panel-soft: rgba(246, 240, 230, 0.045);
        --sc-line: rgba(236, 241, 255, 0.13);
        --sc-line-strong: rgba(246, 240, 230, 0.2);
        --sc-ivory: #F6F0E6;
        --sc-muted: #A9B2C7;
        --sc-muted-strong: #C7D0E3;
        --sc-teal: #2EE9D0;
        --sc-violet: #9B8CFF;
        --sc-coral: #FF8B70;
        --sc-green: #7BE7A7;
        --sc-ink: #06101A;
        --sc-ease-out: cubic-bezier(0.22, 1, 0.36, 1);
        --sc-ease-press: cubic-bezier(0.25, 1, 0.5, 1);
        --sc-shadow-panel: 0 18px 46px rgba(2, 8, 23, 0.34);
        --sc-shadow-control: 0 10px 24px rgba(46, 233, 208, 0.14);
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 18% 10%, rgba(46, 233, 208, 0.11), transparent 24rem),
            radial-gradient(circle at 88% 0%, rgba(155, 140, 255, 0.1), transparent 22rem),
            linear-gradient(90deg, rgba(246, 240, 230, 0.025) 1px, transparent 1px),
            linear-gradient(180deg, #07111E 0%, var(--sc-midnight) 42%, #050711 100%);
        background-size: auto, auto, 64px 64px, auto;
        color: var(--sc-ivory);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stDecoration"] {
        background: linear-gradient(90deg, var(--sc-teal), var(--sc-violet), var(--sc-coral));
        height: 3px;
    }

    .main .block-container {
        max-width: 1480px;
        padding-top: 2.4rem;
        padding-bottom: 5rem;
    }

    section[data-testid="stSidebar"] {
        background: rgba(5, 9, 18, 0.88);
        border-right: 1px solid var(--sc-line);
    }

    h1, h2, h3 {
        letter-spacing: 0;
        color: var(--sc-ivory);
        text-wrap: balance;
    }

    p, label, span, div {
        letter-spacing: 0;
    }

    body, .stApp {
        font-variant-numeric: tabular-nums;
    }

    .sc-hero {
        border: 1px solid var(--sc-line);
        background:
            linear-gradient(135deg, rgba(246, 240, 230, 0.075), rgba(246, 240, 230, 0.025)),
            var(--sc-panel);
        border-radius: 16px;
        padding: 26px 28px 24px;
        box-shadow: var(--sc-shadow-panel);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }

    .sc-hero:after {
        content: "";
        position: absolute;
        inset: 1px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.035);
        pointer-events: none;
    }

    .sc-hero-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        margin-bottom: 18px;
    }

    .sc-brand {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .sc-mark {
        width: 44px;
        height: 44px;
        border-radius: 13px;
        background:
            linear-gradient(135deg, rgba(46, 233, 208, 0.95), rgba(155, 140, 255, 0.9)),
            #101827;
        position: relative;
        box-shadow: 0 12px 30px rgba(46, 233, 208, 0.16);
    }

    .sc-mark:before,
    .sc-mark:after {
        content: "";
        position: absolute;
        inset: 12px 10px;
        border: 2px solid rgba(7, 11, 22, 0.72);
        border-radius: 999px;
        transform: rotate(42deg);
    }

    .sc-mark:after {
        transform: rotate(-42deg);
        border-color: rgba(255, 139, 112, 0.78);
    }

    .sc-kicker {
        color: var(--sc-teal);
        font-size: 12px;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
    }

    .sc-title {
        font-size: clamp(32px, 4vw, 54px);
        font-weight: 800;
        line-height: 1.03;
        color: var(--sc-ivory);
        margin: 0;
    }

    .sc-subtitle {
        max-width: 840px;
        color: var(--sc-muted);
        font-size: 16px;
        line-height: 1.6;
        margin: 8px 0 0;
    }

    .sc-pills {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .sc-pill {
        border: 1px solid rgba(246, 240, 230, 0.14);
        border-radius: 999px;
        color: var(--sc-ivory);
        background: rgba(246, 240, 230, 0.055);
        padding: 8px 12px;
        font-size: 12px;
        white-space: nowrap;
    }

    .sc-preview {
        border: 1px solid rgba(46, 233, 208, 0.22);
        border-radius: 12px;
        background: rgba(4, 9, 18, 0.58);
        padding: 14px 16px;
        color: var(--sc-teal);
        font: 600 13px/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        overflow-wrap: anywhere;
    }

    .sc-studio-shell {
        border: 1px solid var(--sc-line);
        border-radius: 16px;
        background:
            linear-gradient(135deg, rgba(46, 233, 208, 0.055), transparent 34%),
            linear-gradient(180deg, rgba(246, 240, 230, 0.065), rgba(246, 240, 230, 0.025)),
            rgba(9, 14, 26, 0.94);
        box-shadow: var(--sc-shadow-panel);
        padding: 18px;
        margin: 6px 0 22px;
    }

    .sc-studio-grid {
        display: grid;
        grid-template-columns: minmax(180px, 0.7fr) minmax(320px, 1.6fr) minmax(220px, 0.9fr);
        gap: 14px;
    }

    .sc-studio-card {
        border: 1px solid rgba(246, 240, 230, 0.12);
        border-radius: 14px;
        background: rgba(8, 13, 24, 0.74);
        padding: 15px;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
    }

    .sc-studio-card h3,
    .sc-studio-card h4 {
        margin: 0 0 8px;
    }

    .sc-studio-card p {
        color: var(--sc-muted);
        line-height: 1.55;
        margin: 0;
    }

    .sc-module-list {
        display: grid;
        gap: 8px;
    }

    .sc-module-item {
        border: 1px solid rgba(246, 240, 230, 0.1);
        border-radius: 12px;
        background: rgba(246, 240, 230, 0.04);
        padding: 10px 11px;
        color: var(--sc-muted-strong);
        transition:
            transform 150ms var(--sc-ease-press),
            border-color 180ms var(--sc-ease-out),
            background 180ms var(--sc-ease-out);
    }

    .sc-module-item:hover {
        transform: translateY(-1px);
        border-color: rgba(46, 233, 208, 0.26);
        background: rgba(46, 233, 208, 0.07);
    }

    .sc-module-item strong {
        color: var(--sc-ivory);
        display: block;
        font-size: 13px;
        margin-bottom: 2px;
    }

    .sc-canvas {
        min-height: 280px;
        display: grid;
        align-content: space-between;
        gap: 18px;
        background:
            linear-gradient(90deg, rgba(246, 240, 230, 0.03) 1px, transparent 1px),
            linear-gradient(180deg, rgba(246, 240, 230, 0.03) 1px, transparent 1px),
            rgba(4, 8, 16, 0.74);
        background-size: 44px 44px;
    }

    .sc-canvas-title {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: flex-start;
    }

    .sc-status-chip {
        border-radius: 999px;
        border: 1px solid rgba(46, 233, 208, 0.26);
        background: rgba(46, 233, 208, 0.08);
        color: var(--sc-teal);
        font-size: 12px;
        padding: 6px 10px;
        white-space: nowrap;
    }

    .sc-timeline {
        display: grid;
        grid-template-columns: 1.2fr 0.8fr 1.5fr 0.7fr;
        gap: 7px;
        align-items: end;
    }

    .sc-tick {
        min-height: 54px;
        border-radius: 10px;
        background: linear-gradient(180deg, rgba(155, 140, 255, 0.28), rgba(46, 233, 208, 0.12));
        border: 1px solid rgba(246, 240, 230, 0.1);
        padding: 9px;
        font-size: 11px;
        color: var(--sc-muted-strong);
    }

    .sc-export-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
    }

    .sc-export-pill {
        border-radius: 999px;
        background: rgba(246, 240, 230, 0.055);
        border: 1px solid rgba(246, 240, 230, 0.1);
        color: var(--sc-muted-strong);
        padding: 6px 9px;
        font-size: 12px;
    }

    @media (max-width: 980px) {
        .sc-studio-grid {
            grid-template-columns: 1fr;
        }
    }

    @media (max-width: 640px) {
        .sc-studio-shell {
            padding: 12px;
        }

        .sc-canvas-title {
            display: grid;
        }

        .sc-timeline {
            grid-template-columns: 1fr 1fr;
        }
    }

    div[data-testid="stExpander"] {
        border: 1px solid rgba(246, 240, 230, 0.14);
        border-radius: 14px;
        background: var(--sc-panel);
        box-shadow: 0 12px 32px rgba(2, 8, 23, 0.24);
        transition: border-color 180ms var(--sc-ease-out), background 180ms var(--sc-ease-out);
    }

    div[data-testid="stExpander"]:hover {
        border-color: rgba(246, 240, 230, 0.24);
        background: var(--sc-panel-strong);
    }

    div[data-testid="stExpander"] details > summary {
        min-height: 56px;
    }

    button[data-baseweb="tab"] {
        border-radius: 999px;
        color: var(--sc-muted);
        font-weight: 750;
        padding: 10px 18px;
        transition:
            background 180ms var(--sc-ease-out),
            color 180ms var(--sc-ease-out),
            transform 120ms var(--sc-ease-press);
    }

    button[data-baseweb="tab"]:hover {
        background: rgba(246, 240, 230, 0.055);
        color: var(--sc-muted-strong);
    }

    button[data-baseweb="tab"]:active {
        transform: scale(0.98);
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background: rgba(46, 233, 208, 0.14);
        box-shadow: inset 0 0 0 1px rgba(46, 233, 208, 0.22);
        color: var(--sc-ivory);
    }

    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 1px solid rgba(246, 240, 230, 0.1);
        padding-bottom: 10px;
        margin-bottom: 18px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--sc-line);
        border-radius: 12px;
        overflow: hidden;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(246, 240, 230, 0.12);
        border-radius: 12px;
        background: var(--sc-panel-soft);
        padding: 14px;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
    }

    .stButton > button,
    .stDownloadButton > button {
        border: 0;
        border-radius: 12px;
        background: linear-gradient(135deg, var(--sc-teal), var(--sc-violet));
        color: var(--sc-ink);
        font-weight: 800;
        box-shadow: var(--sc-shadow-control);
        transition:
            transform 120ms var(--sc-ease-press),
            box-shadow 180ms var(--sc-ease-out),
            filter 180ms var(--sc-ease-out);
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        color: var(--sc-ink);
        filter: brightness(1.05);
        transform: translateY(-1px);
        box-shadow: 0 14px 30px rgba(46, 233, 208, 0.2);
    }

    .stButton > button:active,
    .stDownloadButton > button:active {
        transform: translateY(0) scale(0.98);
        box-shadow: 0 8px 18px rgba(46, 233, 208, 0.14);
    }

    input, textarea, div[data-baseweb="select"] > div {
        border-radius: 12px !important;
        transition:
            border-color 180ms var(--sc-ease-out),
            box-shadow 180ms var(--sc-ease-out),
            background 180ms var(--sc-ease-out);
    }

    input:focus, textarea:focus {
        border-color: rgba(46, 233, 208, 0.68) !important;
        box-shadow: 0 0 0 3px rgba(46, 233, 208, 0.16) !important;
    }

    div[data-baseweb="select"] > div:focus-within {
        border-color: rgba(46, 233, 208, 0.68) !important;
        box-shadow: 0 0 0 3px rgba(46, 233, 208, 0.16) !important;
    }

    button:focus-visible,
    a:focus-visible {
        outline: 2px solid rgba(46, 233, 208, 0.85) !important;
        outline-offset: 3px !important;
    }

    hr {
        border-color: rgba(246, 240, 230, 0.1);
    }

    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: 0.01ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

TEMPLATE_ICONS = {
    "Podcast Repurposing":              "🎙️",
    "Reels/Shorts para marca personal": "📱",
    "Campaña publicitaria":             "📢",
    "Curso online":                     "🎓",
    "Testimoniales":                    "💬",
    "UGC Content":                      "📲",
    "YouTube long-form + Shorts":       "▶️",
}

FOLDER_HINTS = {
    "01_Footage":      "footage bruto de cámara",
    "02_Audio":        "música, voz en off, SFX",
    "03_Graphics":     "motion graphics, overlays",
    "04_Project_Files":"archivos .prproj / .drp",
    "05_Sequences":    "secuencias de edición",
    "06_Subtitles":    "archivos .srt / .vtt",
    "07_Exports":      "exports finales por formato",
    "08_Delivery":     "entregables aprobados",
    "09_References":   "briefs y referencias",
    "10_Admin":        "checklists y config",
}

ADMIN_FILES = [
    "delivery_checklist.csv",
    "delivery_checklist.md",
    "naming_preview.md",
    "editor_instructions.md",
    "prompts_ai.md",
    "project_config.json",
    "brand_memory.json",
    "brand_memory.md",
    "prompt_remix.json",
    "style_dna.json",
    "scene_builder.csv",
    "scene_builder.json",
    "ai_assets_manifest.json",
    "README.md",
    "scalecut_package.zip",
]


def _load_dashboard_deliverables(project_path) -> list[dict]:
    checklist = Path(project_path) / "10_Admin" / "delivery_checklist.csv"
    if not checklist.exists():
        return []
    with open(checklist, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _split_lines(value: str) -> list[str]:
    return [item.strip() for item in value.replace(",", "\n").splitlines() if item.strip()]


def _json_bytes(payload: dict | list[dict]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _html(value) -> str:
    return html.escape(str(value or "—"))


def _brand_memory_payload(
    client: str,
    voice: str,
    audience: str,
    colors: list[str],
    logo_notes: str,
    subtitle_style: str,
    banned_terms: list[str],
    brand_rules: list[str],
) -> dict:
    return {
        "client": client.strip() or "Nuevo cliente",
        "voice": voice,
        "audience": audience.strip(),
        "colors": colors,
        "logo_notes": logo_notes.strip(),
        "subtitle_style": subtitle_style,
        "banned_terms": banned_terms,
        "brand_rules": brand_rules,
        "ai_usage": {
            "naming": "Apply brand-safe client and project labels.",
            "subtitles": "Use subtitle_style as the default caption direction.",
            "prompt_remix": "Keep voice, audience, and banned_terms in every generated variant.",
            "exports": "Use colors and logo_notes for platform packaging notes.",
        },
    }


def _brand_memory_markdown(profile: dict) -> str:
    colors = ", ".join(profile["colors"]) or "Not defined"
    banned = ", ".join(profile["banned_terms"]) or "None"
    rules = "\n".join(f"- {rule}" for rule in profile["brand_rules"]) or "- No extra rules yet"
    return f"""# Brand Memory: {profile['client']}

## Voice
{profile['voice']}

## Audience
{profile['audience'] or 'Not defined'}

## Colors
{colors}

## Logo and usage notes
{profile['logo_notes'] or 'Not defined'}

## Subtitle style
{profile['subtitle_style']}

## Banned terms
{banned}

## Brand rules
{rules}
"""


def _prompt_remix_rows(core_prompt: str, platforms: list[str], objective: str, intensity: str) -> list[dict]:
    platform_angles = {
        "Instagram Reels": "visual hook first, short caption beats, branded ending",
        "TikTok": "fast hook, direct language, remix-friendly pacing",
        "YouTube Shorts": "clear setup, payoff, retention-focused captions",
        "LinkedIn": "professional framing, outcome-driven copy, calmer pacing",
        "Facebook": "context-rich copy, accessible pacing, broad audience",
    }
    rows = []
    selected = platforms or ["Instagram Reels", "TikTok", "YouTube Shorts"]
    for platform in selected:
        angle = platform_angles.get(platform, "platform-specific structure and caption pacing")
        rows.append({
            "platform": platform,
            "objective": objective,
            "intensity": intensity,
            "prompt": (
                f"{core_prompt.strip() or 'Create a short-form edit from this raw clip.'} "
                f"Adapt for {platform}: {angle}. Keep the objective as {objective.lower()} "
                f"with {intensity.lower()} creative intensity."
            ),
        })
    return rows


def _style_dna_payload(
    name: str,
    pace: int,
    caption_weight: int,
    motion_energy: int,
    hook_pattern: str,
    subtitle_treatment: str,
    visual_rules: list[str],
) -> dict:
    return {
        "style_name": name.strip() or "ScaleCut Style DNA",
        "pace": pace,
        "caption_weight": caption_weight,
        "motion_energy": motion_energy,
        "hook_pattern": hook_pattern,
        "subtitle_treatment": subtitle_treatment,
        "visual_rules": visual_rules,
        "defaults": {
            "safe_zones": "Keep subtitles inside platform-safe lower third.",
            "branding": "Use Brand Memory colors and logo rules when available.",
            "motion": "Use transitions to clarify edits, not decorate repeated actions.",
        },
    }


def _scene_builder_rows(scene_count: int, platform: str, goal: str, hook_style: str) -> list[dict]:
    rows = []
    for idx in range(1, scene_count + 1):
        start = (idx - 1) * 8
        end = idx * 8
        rows.append({
            "scene": f"Scene {idx:02d}",
            "time_range": f"00:{start:02d}-00:{end:02d}",
            "goal": goal,
            "hook": hook_style if idx == 1 else "Advance the point with a visual proof or quote.",
            "platform": platform,
            "needs": "dialogue, b-roll, subtitle, brand cue",
        })
    return rows


def _asset_manifest_rows(uploaded_files, default_role: str, default_stage: str) -> list[dict]:
    rows = []
    for file in uploaded_files or []:
        rows.append({
            "asset": file.name,
            "role": default_role,
            "stage": default_stage,
            "mime": file.type or "unknown",
            "size_kb": round((file.size or 0) / 1024, 1),
            "usage_note": "Attach to Brand Memory, Scene Builder, or export packaging.",
        })
    return rows


def _write_ai_studio_files(
    root: Path,
    brand_profile: dict,
    remix_rows: list[dict],
    style_dna: dict,
    scene_rows: list[dict],
    assets_manifest: list[dict],
) -> None:
    admin = root / "10_Admin"
    admin.mkdir(parents=True, exist_ok=True)
    (admin / "brand_memory.json").write_bytes(_json_bytes(brand_profile))
    (admin / "brand_memory.md").write_text(_brand_memory_markdown(brand_profile), encoding="utf-8")
    (admin / "prompt_remix.json").write_bytes(_json_bytes(remix_rows))
    (admin / "style_dna.json").write_bytes(_json_bytes(style_dna))
    (admin / "scene_builder.json").write_bytes(_json_bytes(scene_rows))
    pd.DataFrame(scene_rows).to_csv(admin / "scene_builder.csv", index=False, encoding="utf-8")
    (admin / "ai_assets_manifest.json").write_bytes(_json_bytes(assets_manifest))

# ── Session state keys ────────────────────────────────────────────────────────

K = dict(
    proj_type = "sc_proj_type",
    client    = "sc_client",
    project   = "sc_project",
    date      = "sc_date",
    clips     = "sc_clips",
    platforms = "sc_platforms",
    formats   = "sc_formats",
    version   = "sc_version",
    language  = "sc_language",
    status    = "sc_status",
    output    = "sc_output",
    prev_type = "sc_prev_type",
)

def _init_state():
    defaults = {
        K["proj_type"]: list(PROJECT_TEMPLATES.keys())[0],
        K["client"]:    "",
        K["project"]:   "",
        K["date"]:      date.today(),
        K["clips"]:     5,
        K["platforms"]: PROJECT_TEMPLATES[list(PROJECT_TEMPLATES.keys())[0]]["suggested_platforms"],
        K["formats"]:   PROJECT_TEMPLATES[list(PROJECT_TEMPLATES.keys())[0]]["suggested_formats"],
        K["version"]:   "01",
        K["language"]:  "ES",
        K["status"]:    "Not started",
        K["output"]:    str(Path.home() / "Desktop" / "ScaleCut_Projects"),
        K["prev_type"]: list(PROJECT_TEMPLATES.keys())[0],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("✂️ ScaleCut")
    st.caption(f"v{__version__}")
    st.divider()
    st.subheader("Plantillas")
    for name, info in PROJECT_TEMPLATES.items():
        icon = TEMPLATE_ICONS.get(name, "📁")
        with st.expander(f"{icon} {name}"):
            st.write(info["description"])
            st.caption("**Plataformas:** " + ", ".join(info["suggested_platforms"]))
            st.caption("**Formatos:** " + ", ".join(info["suggested_formats"]))
            if info.get("notes"):
                st.info(info["notes"], icon="💡")
    st.divider()
    st.subheader("Plataforma → formato")
    for platform, fmts in PLATFORM_FORMATS.items():
        st.caption(f"**{platform}** → {', '.join(fmts)}")

# ── Hero ──────────────────────────────────────────────────────────────────────

# Dynamic filename example — updates live as the user fills the form
_c     = st.session_state.get(K["client"],    "").strip()
_p     = st.session_state.get(K["project"],   "").strip()
_d     = str(st.session_state.get(K["date"],  date.today())).replace("-", "")
_plats = st.session_state.get(K["platforms"], [])
_fmts  = st.session_state.get(K["formats"],   [])
_ver   = st.session_state.get(K["version"],   "01")

if _c and _p and _plats and _fmts:
    from scalecut.naming import platform_slug as _pslug
    _hero = (
        f"{sanitize(_c)}_{sanitize(_p)}_Clip01"
        f"_{_pslug(_plats[0])}_{_fmts[0]}"
        f"_{_d}_V{_ver.zfill(2)}.mp4"
    )
else:
    _hero = "CLIENTE_PROYECTO_Clip01_PLATAFORMA_FORMATO_FECHA_V01.mp4"

st.markdown(
    f"""
    <section class="sc-hero">
        <div class="sc-hero-top">
            <div class="sc-brand">
                <div class="sc-mark" aria-hidden="true"></div>
                <div>
                    <div class="sc-kicker">Creative flow workspace</div>
                    <h1 class="sc-title">ScaleCut Studio</h1>
                    <p class="sc-subtitle">
                        Organiza proyectos de video escalables, controla entregables y prepara
                        versiones para cada plataforma desde un solo panel creativo.
                    </p>
                </div>
            </div>
            <div class="sc-pills" aria-label="ScaleCut modules">
                <span class="sc-pill">Project Dashboard</span>
                <span class="sc-pill">Edit Plan</span>
                <span class="sc-pill">AI-ready workflow</span>
            </div>
        </div>
        <div class="sc-preview">{_hero}</div>
    </section>
    """,
    unsafe_allow_html=True,
)

tab_dashboard, tab_studio = st.tabs(["Creative Flow", "Studio"])

with tab_studio:
    tab_new_project, tab_ai_studio, tab_edit_plan = st.tabs(
        ["Proyecto", "Creative Intelligence", "Edit Plan"]
    )

with tab_dashboard:
    # ── Project Dashboard ──────────────────────────────────────────────────────────

    with st.container(border=True):
        st.markdown("### Creative Flow")
        st.caption("Gestiona proyectos existentes, revisa entregables y actualiza estados desde el checklist.")

        dash_col, dash_btn = st.columns([4, 1])
        with dash_col:
            dash_base = st.text_input(
                "Carpeta de proyectos",
                value="./output",
                key="dash_base_path",
                label_visibility="collapsed",
                placeholder="./output",
            )
        with dash_btn:
            dash_refresh = st.button("🔄 Actualizar", key="dash_refresh", use_container_width=True)

        if dash_refresh:
            try:
                st.session_state["dash_projects"] = find_projects(dash_base)
                st.session_state["dash_error"] = None
            except ListError as e:
                st.session_state["dash_projects"] = None
                st.session_state["dash_error"] = str(e)

        dash_projects = st.session_state.get("dash_projects")
        dash_error    = st.session_state.get("dash_error")

        if dash_error:
            st.error(f"No se pudo leer la carpeta: {dash_error}")
        elif dash_projects is None:
            st.info("Ingresa la carpeta de proyectos y haz clic en **Actualizar**.")
        elif not dash_projects:
            st.info("No se encontraron proyectos en esa carpeta.")
        else:
            if st.session_state.get("dash_update_success"):
                st.success(st.session_state.pop("dash_update_success"))

            df_dash = pd.DataFrame([
                {
                    "Cliente":    p["client"],
                    "Proyecto":   p["project"],
                    "Entrega":    p["delivery_date"],
                    "Tipo":       p["project_type"],
                    "Total":      p["total"],
                    "Progreso %": p["pct_advanced"],
                    "Estado":     p["status_summary"],
                    "Ruta":       p["path"],
                }
                for p in dash_projects
            ])
            st.dataframe(
                df_dash,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Cliente":    st.column_config.TextColumn("Cliente",    width="small"),
                    "Proyecto":   st.column_config.TextColumn("Proyecto",   width="medium"),
                    "Entrega":    st.column_config.TextColumn("Entrega",    width="small"),
                    "Tipo":       st.column_config.TextColumn("Tipo",       width="medium"),
                    "Total":      st.column_config.NumberColumn("Total",    width="small"),
                    "Progreso %": st.column_config.ProgressColumn(
                        "Progreso %", min_value=0, max_value=100, width="medium",
                    ),
                    "Estado":     st.column_config.TextColumn("Estado",     width="large"),
                    "Ruta":       st.column_config.TextColumn("Ruta"),
                },
            )
            st.caption(f"**{len(dash_projects)}** proyecto(s) en `{dash_base}`")

            st.divider()
            st.markdown("**Detalle de proyecto**")
            detail_labels = [
                f"{p['client']} — {p['project']}  ({p['delivery_date']})"
                for p in dash_projects
            ]
            detail_idx = st.selectbox(
                "Selecciona un proyecto",
                options=range(len(dash_projects)),
                format_func=lambda i: detail_labels[i],
                key="dash_detail_idx",
                label_visibility="collapsed",
            )
            sel = dash_projects[detail_idx]

            try:
                report = load_report(sel["path"])
            except ReportError as _re:
                report = None
                st.warning(f"No se pudo leer el reporte: {_re}")
            detail = report or sel

            dc1, dc2 = st.columns(2)
            with dc1:
                st.markdown(f"**Cliente:** {detail['client']}")
                st.markdown(f"**Proyecto:** {detail['project']}")
                st.markdown(f"**Tipo:** {detail['project_type']}")
                st.markdown(f"**Entrega:** {detail['delivery_date']}")
                st.markdown(f"**Total entregables:** {detail['total']}")
                plats = ", ".join(detail.get("platforms", [])) or "—"
                fmts  = ", ".join(detail.get("formats", []))   or "—"
                st.markdown(f"**Plataformas:** {plats}")
                st.markdown(f"**Formatos:** {fmts}")
            with dc2:
                pct_del = detail.get("pct_delivered", 0)
                pct_adv = detail.get("pct_advanced", 0)
                st.metric("Entregado %", f"{pct_del:.0f}%")
                st.metric("Avanzado %",  f"{pct_adv:.0f}%")
                counts = detail.get("status_counts") or {}
                if counts:
                    st.markdown("**Status counts:**")
                    for status in STATUSES:
                        if counts.get(status, 0):
                            st.caption(f"{status}: {counts[status]}")
                next_action = detail.get("next_action") or "—"
                st.markdown(f"**Próxima acción:** {next_action}")

            st.divider()
            st.markdown("**Actualizar status**")
            deliverables = _load_dashboard_deliverables(sel["path"])

            def _deliverable_label(row: dict) -> str:
                return (
                    f"{row.get('Clip', '—')} - {row.get('Platform', '—')} - "
                    f"{row.get('Format', '—')} - {row.get('Status', '—')}"
                )

            if not deliverables:
                st.info("No hay entregables disponibles en el checklist.")
                selected_deliverable = None
            else:
                filter_c1, filter_c2, filter_c3 = st.columns(3)
                with filter_c1:
                    status_filter = st.selectbox(
                        "Filtrar status",
                        options=["Todos", *STATUSES],
                        key="up_filter_status",
                    )
                with filter_c2:
                    platform_options = sorted(
                        {row.get("Platform", "") for row in deliverables if row.get("Platform")}
                    )
                    platform_filter = st.selectbox(
                        "Filtrar plataforma",
                        options=["Todas"] + platform_options,
                        key="up_filter_platform",
                    )
                with filter_c3:
                    format_options = sorted(
                        {row.get("Format", "") for row in deliverables if row.get("Format")}
                    )
                    format_filter = st.selectbox(
                        "Filtrar formato",
                        options=["Todos"] + format_options,
                        key="up_filter_format",
                    )

                filtered_deliverables = [
                    row for row in deliverables
                    if (status_filter == "Todos" or row.get("Status") == status_filter)
                    and (platform_filter == "Todas" or row.get("Platform") == platform_filter)
                    and (format_filter == "Todos" or row.get("Format") == format_filter)
                ]

                st.caption(
                    f"Mostrando **{len(filtered_deliverables)}** de "
                    f"**{len(deliverables)}** entregables"
                )

                if not filtered_deliverables:
                    st.info("No hay entregables que coincidan con esos filtros.")
                    selected_deliverable = None
                else:
                    selected_deliverable_idx = st.selectbox(
                        "Entregable",
                        options=range(len(filtered_deliverables)),
                        format_func=lambda i: _deliverable_label(filtered_deliverables[i]),
                        key="up_deliverable",
                    )
                    selected_deliverable = filtered_deliverables[selected_deliverable_idx]

            if selected_deliverable:
                st.caption(f"Archivo: `{selected_deliverable.get('Filename', '—')}`")

            up_status = st.selectbox("Nuevo status", options=STATUSES, key="up_status")

            if st.button("💾 Actualizar status", key="up_submit"):
                if not selected_deliverable:
                    st.error("Selecciona un entregable del checklist.")
                else:
                    try:
                        updated = update_status(
                            sel["path"],
                            selected_deliverable["Clip"],
                            selected_deliverable["Platform"],
                            up_status,
                            selected_deliverable["Format"],
                        )
                        st.session_state["dash_projects"] = find_projects(dash_base)
                        st.session_state["dash_error"] = None
                        st.session_state["dash_update_success"] = (
                            f"{updated} entregable(s) actualizados a {up_status}."
                        )
                        st.rerun()
                    except UpdateError as _ue:
                        st.error(f"Error al actualizar: {_ue}")

    st.divider()

with tab_edit_plan:
    st.markdown("### Edit Plan")
    st.caption(
        "Prepara timestamps, goals, hooks y notas creativas para generar edit_plan.csv, "
        "edit_plan.md, edit_plan.json y markers.csv al crear un proyecto."
    )

    ep_enabled = st.toggle(
        "Activar generación de Edit Plan",
        value=False,
        key="ep_enabled",
        help="Genera edit_plan.csv / .md / .json y markers.csv con los datos de cada clip.",
    )

    if ep_enabled:
        ep_mode = st.radio(
            "Modo",
            ["Placeholder (vacío)", "Manual (ingresar datos ahora)"],
            horizontal=True,
            key="ep_mode",
        )

        ep_num_clips = int(st.session_state.get(K["clips"], 5))
        ep_platforms = st.session_state.get(K["platforms"], [])
        ep_formats = st.session_state.get(K["formats"], [])

        if "Placeholder" in ep_mode:
            st.info(
                "Se generará un edit plan vacío con todos los entregables. "
                "Rellena los timecodes y datos creativos en `10_Admin/edit_plan.csv` "
                "después de generar el proyecto.",
                icon="ℹ️",
            )
            if ep_platforms and ep_formats:
                total_ep = ep_num_clips * len(ep_platforms) * len(ep_formats)
                st.caption(f"Se crearán **{total_ep} filas** — una por entregable.")

        else:
            if ep_num_clips > 15:
                st.warning(
                    "El modo manual está optimizado para proyectos de hasta 15 clips. "
                    "Para proyectos grandes usa el modo Placeholder y rellena el CSV después.",
                    icon="⚠️",
                )

            st.caption(
                "Introduce los datos de cada clip. El mismo timecode y goal se aplica "
                "a todos los formatos de ese clip."
            )

            for clip_n in range(1, min(ep_num_clips + 1, 16)):
                clip_id = f"Clip{clip_n:02d}"
                with st.expander(f"📎 {clip_id}", expanded=(clip_n == 1)):
                    mc1, mc2, mc3 = st.columns(3)

                    with mc1:
                        st.markdown("**Timecodes**")
                        ep_start = st.text_input(
                            "Start TC",
                            placeholder="00:00:10:00",
                            key=f"ep_start_{clip_id}",
                        )
                        ep_end = st.text_input(
                            "End TC",
                            placeholder="00:01:25:00",
                            key=f"ep_end_{clip_id}",
                        )
                        if ep_start or ep_end:
                            valid, err = validate_timecodes(ep_start, ep_end)
                            if valid and ep_start and ep_end:
                                dur = calculate_duration(ep_start, ep_end)
                                if dur:
                                    secs = timecode_to_seconds(dur)
                                    st.caption(f"⏱ {dur}  (~{int(secs)}s)")
                            elif not valid:
                                st.error(err)

                    with mc2:
                        st.markdown("**Creatividad**")
                        st.text_input(
                            "Goal",
                            placeholder="brand awareness / engagement / conversion",
                            key=f"ep_goal_{clip_id}",
                        )
                        st.text_input(
                            "Hook",
                            placeholder="Frase de apertura (máx 15 palabras)",
                            key=f"ep_hook_{clip_id}",
                        )
                        st.text_input(
                            "Título",
                            placeholder="Título sugerido",
                            key=f"ep_title_{clip_id}",
                        )

                    with mc3:
                        st.markdown("**Copy**")
                        st.text_input("CTA", placeholder="Call to action", key=f"ep_cta_{clip_id}")
                        st.text_area(
                            "Notas",
                            placeholder="Instrucciones para el editor",
                            key=f"ep_notes_{clip_id}",
                            height=130,
                        )

with tab_ai_studio:
    st.markdown("### Creative Intelligence")
    st.caption(
        "Define la inteligencia creativa que se guardará con el proyecto: marca, prompts, estilo, escenas y assets."
    )

    studio_client = st.session_state.get(K["client"], "").strip() or "Cliente activo"
    studio_project = st.session_state.get(K["project"], "").strip() or "Proyecto creativo"
    studio_platforms = st.session_state.get(K["platforms"], []) or ["Instagram Reels", "TikTok", "YouTube Shorts"]
    studio_formats = st.session_state.get(K["formats"], []) or ["9x16", "1x1"]
    studio_deliverables = int(st.session_state.get(K["clips"], 5)) * len(studio_platforms) * len(studio_formats)

    st.markdown(
        f"""
        <section class="sc-studio-shell">
            <div class="sc-studio-grid">
                <aside class="sc-studio-card">
                    <h4>Creative Cockpit</h4>
                    <p>Seis módulos conectados para pasar de raw clip a sistema creativo escalable.</p>
                    <div class="sc-module-list" style="margin-top: 12px;">
                        <div class="sc-module-item"><strong>Brand Memory</strong>Cliente, tono, reglas, colores.</div>
                        <div class="sc-module-item"><strong>Prompt Remix</strong>Variantes por plataforma.</div>
                        <div class="sc-module-item"><strong>Style DNA</strong>Ritmo, captions, motion.</div>
                        <div class="sc-module-item"><strong>Scene Builder</strong>Escenas con hook y objetivo.</div>
                        <div class="sc-module-item"><strong>AI Assets Library</strong>Assets clasificados por uso.</div>
                    </div>
                </aside>
                <main class="sc-studio-card sc-canvas">
                    <div class="sc-canvas-title">
                        <div>
                            <h3>{_html(studio_project)}</h3>
                            <p>{_html(studio_client)} · {studio_deliverables} entregables estimados</p>
                        </div>
                        <span class="sc-status-chip">AI-ready workflow</span>
                    </div>
                    <div class="sc-timeline" aria-label="AI Studio timeline">
                        <div class="sc-tick">01 · Raw clip</div>
                        <div class="sc-tick">02 · Transcript</div>
                        <div class="sc-tick">03 · Scene plan</div>
                        <div class="sc-tick">04 · Export</div>
                    </div>
                    <div class="sc-export-row">
                        <span class="sc-export-pill">Brand profile</span>
                        <span class="sc-export-pill">Prompt set</span>
                        <span class="sc-export-pill">Style JSON</span>
                        <span class="sc-export-pill">Scene CSV</span>
                    </div>
                </main>
                <aside class="sc-studio-card">
                    <h4>Properties</h4>
                    <p>Plataformas: {_html(', '.join(studio_platforms))}</p>
                    <p>Formatos: {_html(', '.join(studio_formats))}</p>
                    <div class="sc-export-row">
                        <span class="sc-export-pill">Captions</span>
                        <span class="sc-export-pill">Branding</span>
                        <span class="sc-export-pill">Scenes</span>
                    </div>
                </aside>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    (
        tab_brand_memory,
        tab_prompt_remix,
        tab_style_dna,
        tab_scene_builder,
        tab_assets_library,
    ) = st.tabs([
        "Brand Memory",
        "Prompt Remix",
        "Style DNA",
        "Scene Builder",
        "AI Assets Library",
    ])

    with tab_brand_memory:
        bm_left, bm_right = st.columns([1.05, 0.95])
        with bm_left:
            bm_client = st.text_input("Cliente", value=studio_client, key="bm_client")
            bm_voice = st.selectbox(
                "Voz de marca",
                [
                    "Precisa, premium y calmada",
                    "Directa, social y energética",
                    "Educativa, clara y confiable",
                    "Editorial, sofisticada y sobria",
                ],
                key="bm_voice",
            )
            bm_audience = st.text_area(
                "Audiencia",
                value="Creadores, equipos de marketing y clientes que necesitan entender el valor del contenido rápido.",
                key="bm_audience",
                height=92,
            )
            bm_colors_raw = st.text_input(
                "Colores de marca",
                value="#2EE9D0, #9B8CFF, #FF8B70",
                key="bm_colors",
            )
        with bm_right:
            bm_logo_notes = st.text_area(
                "Reglas de logo y branding",
                value="Mantener logo dentro de safe zones. Usar marca al cierre y en lower thirds cuando aplique.",
                key="bm_logo_notes",
                height=92,
            )
            bm_subtitle_style = st.selectbox(
                "Estilo de subtítulos",
                [
                    "Clean bold lower third",
                    "Kinetic captions con énfasis por palabra clave",
                    "Editorial minimal con alto contraste",
                    "Social native con highlights de color",
                ],
                key="bm_subtitle_style",
            )
            bm_banned_terms_raw = st.text_area(
                "Palabras o frases prohibidas",
                value="viral, game changer, unleash",
                key="bm_banned_terms",
                height=72,
            )
            bm_rules_raw = st.text_area(
                "Reglas de marca",
                value="No usar rojo como color principal\nMantener tono claro y experto\nEvitar claims imposibles de comprobar",
                key="bm_rules",
                height=92,
            )

        brand_profile = _brand_memory_payload(
            bm_client,
            bm_voice,
            bm_audience,
            _split_lines(bm_colors_raw),
            bm_logo_notes,
            bm_subtitle_style,
            _split_lines(bm_banned_terms_raw),
            _split_lines(bm_rules_raw),
        )
        bm_downloads = st.columns(2)
        with bm_downloads[0]:
            st.download_button(
                "Descargar brand_memory.json",
                data=_json_bytes(brand_profile),
                file_name="brand_memory.json",
                mime="application/json",
                use_container_width=True,
                key="dl_brand_memory_json",
            )
        with bm_downloads[1]:
            st.download_button(
                "Descargar brand_memory.md",
                data=_brand_memory_markdown(brand_profile).encode("utf-8"),
                file_name="brand_memory.md",
                mime="text/markdown",
                use_container_width=True,
                key="dl_brand_memory_md",
            )
        st.json(brand_profile, expanded=False)

    with tab_prompt_remix:
        remix_left, remix_right = st.columns([1.1, 0.9])
        with remix_left:
            core_prompt = st.text_area(
                "Prompt base",
                value=(
                    "Edita este raw clip en una pieza corta con hook claro, ritmo preciso, "
                    "subtítulos legibles y cierre alineado a la marca."
                ),
                key="remix_core_prompt",
                height=130,
            )
            remix_platforms = st.multiselect(
                "Plataformas",
                options=ALL_PLATFORMS,
                default=[p for p in studio_platforms if p in ALL_PLATFORMS],
                key="remix_platforms",
            )
        with remix_right:
            remix_objective = st.selectbox(
                "Objetivo",
                ["Awareness", "Lead magnet", "Educación", "Conversión", "Retención"],
                key="remix_objective",
            )
            remix_intensity = st.select_slider(
                "Intensidad creativa",
                options=["Baja", "Media", "Alta", "Experimental"],
                value="Alta",
                key="remix_intensity",
            )
            st.info(
                "Cada remix hereda Brand Memory y adapta estructura, copy y caption pacing por plataforma.",
                icon="✨",
            )

        remix_rows = _prompt_remix_rows(core_prompt, remix_platforms, remix_objective, remix_intensity)
        remix_df = pd.DataFrame(remix_rows)
        st.dataframe(remix_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Descargar prompt_remix.json",
            data=_json_bytes(remix_rows),
            file_name="prompt_remix.json",
            mime="application/json",
            use_container_width=True,
            key="dl_prompt_remix_json",
        )

    with tab_style_dna:
        dna_left, dna_right = st.columns(2)
        with dna_left:
            style_name = st.text_input("Nombre del estilo", value="ScaleCut Editorial Social", key="dna_name")
            hook_pattern = st.selectbox(
                "Patrón de hook",
                [
                    "Problem first",
                    "Contraste antes/después",
                    "Pregunta directa",
                    "Declaración experta",
                    "Momento emocional",
                ],
                key="dna_hook",
            )
            subtitle_treatment = st.selectbox(
                "Tratamiento de subtítulos",
                [
                    "Lower third compacto",
                    "Palabra clave resaltada",
                    "Dos líneas con ritmo de diálogo",
                    "Subtítulo grande tipo creator",
                ],
                key="dna_subtitles",
            )
        with dna_right:
            pace = st.slider("Ritmo de edición", min_value=1, max_value=10, value=7, key="dna_pace")
            caption_weight = st.slider("Peso visual de captions", min_value=1, max_value=10, value=6, key="dna_caption")
            motion_energy = st.slider("Energía de motion", min_value=1, max_value=10, value=5, key="dna_motion")
            visual_rules_raw = st.text_area(
                "Reglas visuales",
                value="Usar contraste alto\nAnimar solo cambios de estado\nMantener safe zones por plataforma",
                key="dna_rules",
                height=95,
            )
        style_dna = _style_dna_payload(
            style_name,
            pace,
            caption_weight,
            motion_energy,
            hook_pattern,
            subtitle_treatment,
            _split_lines(visual_rules_raw),
        )
        dna_metrics = st.columns(3)
        dna_metrics[0].metric("Pace", pace)
        dna_metrics[1].metric("Captions", caption_weight)
        dna_metrics[2].metric("Motion", motion_energy)
        st.download_button(
            "Descargar style_dna.json",
            data=_json_bytes(style_dna),
            file_name="style_dna.json",
            mime="application/json",
            use_container_width=True,
            key="dl_style_dna_json",
        )
        st.json(style_dna, expanded=False)

    with tab_scene_builder:
        scene_left, scene_right = st.columns([0.9, 1.1])
        with scene_left:
            scene_count = st.number_input("Número de escenas", min_value=1, max_value=12, value=4, step=1, key="scene_count")
            scene_platform = st.selectbox("Plataforma", options=ALL_PLATFORMS, key="scene_platform")
            scene_goal = st.selectbox(
                "Objetivo de la pieza",
                ["Captar atención", "Explicar una idea", "Mostrar prueba", "Vender una oferta", "Reforzar autoridad"],
                key="scene_goal",
            )
            scene_hook = st.selectbox(
                "Hook inicial",
                ["Pregunta directa", "Frase controversial", "Resultado primero", "Dolor del cliente", "Dato inesperado"],
                key="scene_hook",
            )
        with scene_right:
            st.markdown("**Blueprint de escenas**")
            st.caption(
                "Este esquema está pensado para conectarse después con transcripción, raw clips y marcadores de Premiere/Resolve."
            )

        scene_rows = _scene_builder_rows(int(scene_count), scene_platform, scene_goal, scene_hook)
        scene_df = pd.DataFrame(scene_rows)
        st.dataframe(scene_df, use_container_width=True, hide_index=True)
        scene_downloads = st.columns(2)
        with scene_downloads[0]:
            st.download_button(
                "Descargar scene_builder.json",
                data=_json_bytes(scene_rows),
                file_name="scene_builder.json",
                mime="application/json",
                use_container_width=True,
                key="dl_scene_builder_json",
            )
        with scene_downloads[1]:
            st.download_button(
                "Descargar scene_builder.csv",
                data=scene_df.to_csv(index=False).encode("utf-8"),
                file_name="scene_builder.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_scene_builder_csv",
            )

    with tab_assets_library:
        assets_left, assets_right = st.columns([1.05, 0.95])
        with assets_left:
            uploaded_assets = st.file_uploader(
                "Agregar assets al manifiesto",
                accept_multiple_files=True,
                key="asset_uploads",
            )
        with assets_right:
            asset_role = st.selectbox(
                "Rol por defecto",
                ["Branding", "Raw clip", "B-roll", "Audio", "Subtitle preset", "Reference", "Export"],
                key="asset_role",
            )
            asset_stage = st.selectbox(
                "Etapa",
                ["Intake", "Editing", "Review", "Delivery", "Archive"],
                key="asset_stage",
            )
            st.caption("El manifiesto no mueve archivos todavía; prepara la estructura para la fase de asset management.")

        asset_rows = _asset_manifest_rows(uploaded_assets, asset_role, asset_stage)
        if asset_rows:
            assets_df = pd.DataFrame(asset_rows)
        else:
            assets_df = pd.DataFrame([
                {
                    "asset": "logo_primary.svg",
                    "role": "Branding",
                    "stage": "Intake",
                    "mime": "image/svg+xml",
                    "size_kb": 18.4,
                    "usage_note": "Example manifest row. Upload files to replace this template.",
                }
            ])
        st.dataframe(assets_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Descargar ai_assets_manifest.json",
            data=_json_bytes(assets_df.to_dict(orient="records")),
            file_name="ai_assets_manifest.json",
            mime="application/json",
            use_container_width=True,
            key="dl_assets_manifest_json",
        )


with tab_new_project:
    # ── Template card ─────────────────────────────────────────────────────────────

    st.subheader("¿Qué tipo de proyecto es?")

    template_options = list(PROJECT_TEMPLATES.keys())
    project_type = st.selectbox(
        "Plantilla",
        options=template_options,
        index=template_options.index(st.session_state[K["proj_type"]]),
        format_func=lambda n: f"{TEMPLATE_ICONS.get(n, '📁')}  {n}",
        key=K["proj_type"],
        label_visibility="collapsed",
    )
    template = PROJECT_TEMPLATES[project_type]

    # Auto-reset platforms/formats when template changes
    if st.session_state[K["prev_type"]] != project_type:
        st.session_state[K["platforms"]] = list(template["suggested_platforms"])
        st.session_state[K["formats"]]   = list(template["suggested_formats"])
        st.session_state[K["prev_type"]] = project_type
        st.rerun()

    icon = TEMPLATE_ICONS.get(project_type, "📁")
    with st.container(border=True):
        ci, ct = st.columns([1, 9])
        with ci:
            st.markdown(f"## {icon}")
        with ct:
            st.markdown(f"**{project_type}**  \n{template['description']}")
            chips_plat = "  ".join([f"`{p}`" for p in template["suggested_platforms"]])
            chips_fmt  = "  ".join([f"`{f}`" for f in template["suggested_formats"]])
            st.markdown(f"🎯 {chips_plat}  &nbsp;&nbsp;  📐 {chips_fmt}")
            if template.get("notes"):
                st.caption(f"💡 {template['notes']}")

    st.divider()

    # ── Form inputs (outside st.form for live reactivity) ─────────────────────────

    st.subheader("Datos del proyecto")

    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        client = st.text_input(
            "Cliente *",
            placeholder="Nike, Acme Studio, María García…",
            key=K["client"],
        )
        project_name = st.text_input(
            "Proyecto *",
            placeholder="Campaña Verano, Podcast Leadership…",
            key=K["project"],
        )
        delivery_date = st.date_input("Fecha de entrega", key=K["date"])
        num_clips = st.number_input(
            "Número de clips",
            min_value=1,
            max_value=200,
            key=K["clips"],
        )

    with col_right:
        platforms = st.multiselect(
            "Plataformas *",
            options=ALL_PLATFORMS,
            key=K["platforms"],
        )

        auto_formats = sorted(
            {fmt for p in platforms for fmt in PLATFORM_FORMATS.get(p, [])}
        )
        if auto_formats:
            st.caption(f"📐 Recomendados para tus plataformas: **{', '.join(auto_formats)}**")

        formats = st.multiselect(
            "Formatos *",
            options=ALL_FORMATS,
            key=K["formats"],
        )

        if platforms and formats:
            total_live = int(num_clips) * len(platforms) * len(formats)
            st.success(
                f"**{int(num_clips)} clips × {len(platforms)} plataformas × "
                f"{len(formats)} formatos = {total_live} entregables**"
            )

        cv, cl = st.columns(2)
        with cv:
            version  = st.text_input("Versión", key=K["version"])
            language = st.selectbox("Idioma", ["ES", "EN", "PT", "FR", "DE", "Other"], key=K["language"])
        with cl:
            initial_status = st.selectbox("Estado inicial", STATUSES, key=K["status"])

    with st.expander("⚙️ Configuración avanzada"):
        output_path = st.text_input(
            "Ruta de salida",
            key=K["output"],
            help="Carpeta donde se creará el proyecto. Se crea automáticamente si no existe.",
        )
        st.caption("Puedes cambiarlo si quieres guardar el proyecto en otro lugar.")

    st.divider()

    # ── Executive summary ─────────────────────────────────────────────────────────

    _can_preview = bool(client and project_name and platforms and formats)

    if _can_preview:
        total_est     = int(num_clips) * len(platforms) * len(formats)
        client_slug   = sanitize(client)
        project_slug  = sanitize(project_name)
        date_slug     = str(delivery_date).replace("-", "")
        folder_name   = f"{client_slug}_{project_slug}_{date_slug}"
        estimated_path = Path(output_path) / folder_name

        with st.container(border=True):
            st.markdown("### 📋 Resumen ejecutivo")
            es1, es2 = st.columns(2)

            with es1:
                st.markdown(f"**Total de entregables:** {total_est}")
                st.markdown(f"**Clips:** {int(num_clips)}")
                st.markdown(f"**Plataformas:** {', '.join(platforms)}")
                st.markdown(f"**Formatos:** {', '.join(formats)}")
                st.markdown(f"**Fecha de entrega:** {delivery_date}")
                st.markdown(f"**Ruta estimada del proyecto:**")
                st.code(str(estimated_path), language=None)

            with es2:
                st.markdown("**Archivos que se generarán:**")
                for f in ADMIN_FILES:
                    st.markdown(f"  ✓ `{f}`")

        st.divider()

    generate = st.button("✂️ Generar proyecto", type="primary", use_container_width=True)

    # ── Validation & generation ───────────────────────────────────────────────────

    if generate:
        errors = []
        if not client.strip():       errors.append("El nombre del cliente es obligatorio.")
        if not project_name.strip(): errors.append("El nombre del proyecto es obligatorio.")
        if not platforms:            errors.append("Selecciona al menos una plataforma.")
        if not formats:              errors.append("Selecciona al menos un formato.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            config = ProjectConfig(
                client=client.strip(),
                project=project_name.strip(),
                project_type=project_type,
                delivery_date=str(delivery_date),
                num_clips=int(num_clips),
                platforms=platforms,
                formats=formats,
                version=version.zfill(2),
                language=language,
                initial_status=initial_status,
                output_path=output_path.strip(),
            )
            with st.spinner("Generando estructura y archivos…"):
                root = create_folders(config)
                write_csv(config, root)
                write_markdown(config, root)
                write_naming_preview(config, root)
                write_editor_instructions(config, root)
                write_prompts_ai(config, root)
                write_config(config, root)
                write_readme(config, root)

                # Edit Plan generation
                ep_clips = None
                if st.session_state.get("ep_enabled", False):
                    ep_mode_val = st.session_state.get("ep_mode", "Placeholder (vacío)")
                    if "Placeholder" in ep_mode_val:
                        ep_clips = make_placeholder_clips(config)
                        ep_json_mode = "placeholder"
                    else:
                        from scalecut.naming import build_filename as _bfn
                        ep_clips = []
                        for clip_n in range(1, config.num_clips + 1):
                            clip_id = f"Clip{clip_n:02d}"
                            _start = st.session_state.get(f"ep_start_{clip_id}", "")
                            _end   = st.session_state.get(f"ep_end_{clip_id}", "")
                            _dur   = calculate_duration(_start, _end) if _start and _end else ""
                            _goal  = st.session_state.get(f"ep_goal_{clip_id}", "")
                            _hook  = st.session_state.get(f"ep_hook_{clip_id}", "")
                            _title = st.session_state.get(f"ep_title_{clip_id}", "")
                            _cta   = st.session_state.get(f"ep_cta_{clip_id}", "")
                            _notes = st.session_state.get(f"ep_notes_{clip_id}", "")
                            for platform in config.platforms:
                                for fmt in config.formats:
                                    ep_clips.append(EditPlanClip(
                                        clip_id=clip_id,
                                        start_timecode=_start,
                                        end_timecode=_end,
                                        duration=_dur or "",
                                        platform=platform,
                                        format=fmt,
                                        goal=_goal,
                                        hook=_hook,
                                        title=_title,
                                        caption="",
                                        cta=_cta,
                                        notes=_notes,
                                        export_filename=_bfn(config, clip_n, platform, fmt),
                                        status=config.initial_status,
                                    ))
                        ep_json_mode = "manual"

                    write_edit_plan_csv(ep_clips, root)
                    write_edit_plan_md(ep_clips, root, config)
                    write_edit_plan_json(ep_clips, root, config, mode=ep_json_mode)
                    write_markers_csv(ep_clips, root)

                _write_ai_studio_files(
                    root,
                    brand_profile,
                    remix_rows,
                    style_dna,
                    scene_rows,
                    assets_df.to_dict(orient="records"),
                )

                zip_bytes = create_zip(root)

            st.session_state["config"]       = config
            st.session_state["root"]         = root
            st.session_state["deliverables"] = generate_all_filenames(config)
            st.session_state["zip_bytes"]    = zip_bytes
            st.session_state["ep_clips"]     = ep_clips

    # ── Results ───────────────────────────────────────────────────────────────────

    if "config" in st.session_state:
        config      = st.session_state["config"]
        root        = st.session_state["root"]
        deliverables = st.session_state["deliverables"]
        zip_bytes   = st.session_state["zip_bytes"]
        total       = len(deliverables)
        zip_name    = f"{root.name}_scalecut.zip"

        st.divider()
        st.success(f"✅  **{root.name}** creado correctamente  —  `{root}`")

        rc1, rc2 = st.columns([3, 2])
        with rc1:
            # P0: CSV immediately visible
            st.download_button(
                label="⬇  Descargar delivery_checklist.csv",
                data=(root / "10_Admin" / "delivery_checklist.csv").read_bytes(),
                file_name="delivery_checklist.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
                key="dl_csv_top",
            )
        with rc2:
            # ZIP download — main CTA alongside CSV
            st.download_button(
                label="📦  Descargar paquete ZIP completo",
                data=zip_bytes,
                file_name=zip_name,
                mime="application/zip",
                use_container_width=True,
                key="dl_zip_top",
            )

        st.divider()

        # Metrics
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        mc1.metric("Total entregables", total, help="clips × plataformas × formatos")
        mc2.metric("Clips",             config.num_clips)
        mc3.metric("Plataformas",       len(config.platforms))
        mc4.metric("Formatos",          len(config.formats))
        mc5.metric("Versión",           f"V{config.version.zfill(2)}")

        st.divider()

        # Tabs — Naming first (P1); Edit Plan tab visible only when generated
        ep_clips_result = st.session_state.get("ep_clips")
        tab_labels = ["🏷️ Naming", "📋 Entregables", "📁 Carpetas", "📄 Más archivos"]
        if ep_clips_result:
            tab_labels.append("📝 Edit Plan")
        tabs = st.tabs(tab_labels)
        tab_naming, tab_del, tab_folders, tab_files = tabs[0], tabs[1], tabs[2], tabs[3]
        tab_ep = tabs[4] if ep_clips_result else None

        # ── Naming ────────────────────────────────────────────────────────────────
        with tab_naming:
            client_slug  = sanitize(config.client)
            project_slug = sanitize(config.project)
            date_slug    = config.delivery_date.replace("-", "")
            version_slug = f"V{config.version.zfill(2)}"

            st.markdown("**Patrón**")
            st.code("CLIENT_PROJECT_ClipNN_PLATFORM_FORMAT_YYYYMMDD_VNN.mp4", language=None)
            nc1, nc2 = st.columns(2)
            with nc1:
                st.markdown("**Tokens de este proyecto**")
                st.dataframe(
                    pd.DataFrame([
                        {"Token": "CLIENT",  "Valor": client_slug},
                        {"Token": "PROJECT", "Valor": project_slug},
                        {"Token": "Date",    "Valor": date_slug},
                        {"Token": "Version", "Valor": version_slug},
                    ]),
                    hide_index=True,
                    use_container_width=True,
                )
            with nc2:
                st.markdown("**Ejemplo real**")
                from scalecut.naming import build_filename
                example = build_filename(config, 1, config.platforms[0], config.formats[0])
                st.code(example, language=None)
                st.caption("Todos los archivos siguen exactamente este patrón.")

        # ── Entregables ───────────────────────────────────────────────────────────
        with tab_del:
            df = pd.DataFrame(deliverables)
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                f_clip = st.multiselect("Clip",       sorted(df["clip"].unique()),     key="f_clip")
            with fc2:
                f_plat = st.multiselect("Plataforma", sorted(df["platform"].unique()), key="f_plat")
            with fc3:
                f_fmt  = st.multiselect("Formato",    sorted(df["format"].unique()),   key="f_fmt")

            filtered = df.copy()
            if f_clip: filtered = filtered[filtered["clip"].isin(f_clip)]
            if f_plat: filtered = filtered[filtered["platform"].isin(f_plat)]
            if f_fmt:  filtered = filtered[filtered["format"].isin(f_fmt)]

            st.dataframe(
                filtered[["clip", "platform", "format", "filename"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "clip":     st.column_config.TextColumn("Clip",       width="small"),
                    "platform": st.column_config.TextColumn("Plataforma", width="medium"),
                    "format":   st.column_config.TextColumn("Formato",    width="small"),
                    "filename": st.column_config.TextColumn("Filename"),
                },
            )
            st.caption(f"Mostrando **{len(filtered)}** de **{total}** entregables")

        # ── Carpetas ──────────────────────────────────────────────────────────────
        with tab_folders:
            lines = [f"{root.name}/"]
            for folder in build_folder_tree(config):
                depth  = folder.count("/")
                indent = "  " * (depth + 1)
                name   = folder.split("/")[-1]
                hint   = FOLDER_HINTS.get(name, "")
                lines.append(f"{indent}{name}/" + (f"   ← {hint}" if hint else ""))
            st.code("\n".join(lines), language=None)
            st.caption(f"📍 `{root}`")

        # ── Más archivos ──────────────────────────────────────────────────────────
        with tab_files:
            other_files = [
                (root / "10_Admin" / "delivery_checklist.md",   "text/markdown",    "Checklist con checkboxes por clip"),
                (root / "10_Admin" / "naming_preview.md",       "text/markdown",    "Todos los filenames por clip y plataforma"),
                (root / "10_Admin" / "editor_instructions.md",  "text/markdown",    "Instrucciones completas para Premiere / Resolve"),
                (root / "10_Admin" / "prompts_ai.md",           "text/markdown",    "6 prompts de IA listos para usar"),
                (root / "10_Admin" / "project_config.json",     "application/json", "Datos completos del proyecto (JSON)"),
                (root / "10_Admin" / "brand_memory.json",       "application/json", "Perfil de marca para prompts, subtítulos y exports"),
                (root / "10_Admin" / "brand_memory.md",         "text/markdown",    "Brand Memory legible para revisión creativa"),
                (root / "10_Admin" / "prompt_remix.json",       "application/json", "Variantes de prompt por plataforma"),
                (root / "10_Admin" / "style_dna.json",          "application/json", "Perfil de ritmo, captions y motion"),
                (root / "10_Admin" / "scene_builder.csv",       "text/csv",         "Blueprint de escenas para edición"),
                (root / "10_Admin" / "scene_builder.json",      "application/json", "Blueprint de escenas para integraciones AI"),
                (root / "10_Admin" / "ai_assets_manifest.json", "application/json", "Manifiesto de assets creativos"),
                (root / "README.md",                            "text/markdown",    "Briefing del proyecto"),
            ]

            for path, mime, description in other_files:
                dc, db = st.columns([3, 1])
                with dc:
                    st.markdown(f"**`{path.name}`** — {description}")
                with db:
                    st.download_button(
                        label="⬇ Descargar",
                        data=path.read_bytes(),
                        file_name=path.name,
                        mime=mime,
                        use_container_width=True,
                        key=f"dl_{path.name}",
                    )

            st.divider()
            st.download_button(
                label="📦  Descargar paquete ZIP completo",
                data=zip_bytes,
                file_name=zip_name,
                mime="application/zip",
                type="primary",
                use_container_width=True,
                key="dl_zip_bottom",
            )

        # ── Edit Plan tab ─────────────────────────────────────────────────────────
        if tab_ep is not None and ep_clips_result:
            with tab_ep:
                ep_df = pd.DataFrame([
                    {
                        "Clip":     c.clip_id,
                        "Start TC": c.start_timecode or "—",
                        "End TC":   c.end_timecode   or "—",
                        "Duración": c.duration        or "—",
                        "Platform": c.platform,
                        "Format":   c.format,
                        "Goal":     c.goal   or "—",
                        "Hook":     c.hook   or "—",
                        "Status":   c.status,
                        "Filename": c.export_filename,
                    }
                    for c in ep_clips_result
                ])

                efc1, efc2 = st.columns(2)
                with efc1:
                    ef_clip = st.multiselect("Clip",       sorted(ep_df["Clip"].unique()),     key="ef_clip")
                with efc2:
                    ef_plat = st.multiselect("Plataforma", sorted(ep_df["Platform"].unique()), key="ef_plat")

                ep_filtered = ep_df.copy()
                if ef_clip: ep_filtered = ep_filtered[ep_filtered["Clip"].isin(ef_clip)]
                if ef_plat: ep_filtered = ep_filtered[ep_filtered["Platform"].isin(ef_plat)]

                st.dataframe(ep_filtered, use_container_width=True, hide_index=True)
                st.caption(f"{len(ep_filtered)} filas · {len(ep_clips_result)} total")

                st.divider()
                st.markdown("**Descargar archivos del Edit Plan**")

                ep_files = [
                    (root / "10_Admin" / "edit_plan.csv",  "text/csv",         "edit_plan.csv  — tracker completo (Google Sheets)"),
                    (root / "10_Admin" / "edit_plan.md",   "text/markdown",    "edit_plan.md   — plan legible por clip"),
                    (root / "10_Admin" / "edit_plan.json", "application/json", "edit_plan.json — para plugin Premiere / Resolve"),
                    (root / "10_Admin" / "markers.csv",    "text/csv",         "markers.csv    — marcadores con color por plataforma"),
                ]
                for ep_path, ep_mime, ep_label in ep_files:
                    if ep_path.exists():
                        epc, epb = st.columns([3, 1])
                        with epc:
                            st.markdown(f"`{ep_label}`")
                        with epb:
                            st.download_button(
                                label="⬇ Descargar",
                                data=ep_path.read_bytes(),
                                file_name=ep_path.name,
                                mime=ep_mime,
                                use_container_width=True,
                                key=f"dl_ep_{ep_path.name}",
                            )

                st.info(
                    "**edit_plan.json** está diseñado para ser leído por un plugin de "
                    "Premiere Pro o DaVinci Resolve en una fase futura. "
                    "Contiene todos los timecodes, goals y filenames que el plugin "
                    "necesita para crear secuencias y marcadores automáticamente.",
                    icon="🔌",
                )
