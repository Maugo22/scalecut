"""
Edit Plan Generator — timestamped clip plan for Premiere Pro / DaVinci Resolve.

This module prepares structured data that a future DAW plugin can consume to
create sequences, markers and auto-cuts directly inside the NLE.
"""

import csv
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from scalecut.models import ProjectConfig
from scalecut.naming import build_filename
from scalecut import __version__

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_FPS = 25

TIMECODE_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2}):(\d{2})$")

PLATFORM_COLORS = {
    "Instagram Reels": "Cyan",
    "TikTok":          "Magenta",
    "LinkedIn":        "Blue",
    "YouTube":         "Red",
    "YouTube Shorts":  "Orange",
    "Stories":         "Yellow",
    "Facebook":        "Purple",
    "Ads":             "Green",
    "Website":         "White",
}

EDIT_PLAN_CSV_HEADERS = [
    "clip_id", "start_timecode", "end_timecode", "duration",
    "platform", "format", "goal", "hook", "title",
    "caption", "cta", "notes", "export_filename", "status",
]

MARKERS_CSV_HEADERS = [
    "marker_name", "start_timecode", "end_timecode", "duration",
    "color", "comment", "platform", "format", "export_filename",
]


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class EditPlanClip:
    clip_id:        str
    start_timecode: str
    end_timecode:   str
    duration:       str
    platform:       str
    format:         str
    goal:           str
    hook:           str
    title:          str
    caption:        str
    cta:            str
    notes:          str
    export_filename: str
    status:         str


# ── Timecode utilities ────────────────────────────────────────────────────────

def parse_timecode(tc: str) -> Optional[tuple]:
    """
    Parse HH:MM:SS:FF string.
    Returns (hours, minutes, seconds, frames) or None if invalid.
    Minutes and seconds must be 00–59.
    """
    m = TIMECODE_RE.match(tc.strip())
    if not m:
        return None
    h, mn, s, f = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    if mn >= 60 or s >= 60:
        return None
    return h, mn, s, f


def timecode_to_frames(tc: str, fps: int = DEFAULT_FPS) -> Optional[int]:
    """Convert HH:MM:SS:FF to total frame count."""
    parts = parse_timecode(tc)
    if parts is None:
        return None
    h, mn, s, f = parts
    return h * 3600 * fps + mn * 60 * fps + s * fps + f


def frames_to_timecode(frames: int, fps: int = DEFAULT_FPS) -> str:
    """Convert total frame count back to HH:MM:SS:FF."""
    f  = frames % fps
    ts = frames // fps
    s  = ts % 60
    tm = ts // 60
    mn = tm % 60
    h  = tm // 60
    return f"{h:02d}:{mn:02d}:{s:02d}:{f:02d}"


def timecode_to_seconds(tc: str, fps: int = DEFAULT_FPS) -> Optional[float]:
    """Return duration in seconds as float, or None if tc is invalid."""
    frames = timecode_to_frames(tc, fps)
    if frames is None:
        return None
    return round(frames / fps, 3)


def calculate_duration(start: str, end: str, fps: int = DEFAULT_FPS) -> Optional[str]:
    """
    Return duration timecode string (HH:MM:SS:FF), or None if:
    - either timecode is invalid
    - end <= start
    """
    sf = timecode_to_frames(start, fps)
    ef = timecode_to_frames(end, fps)
    if sf is None or ef is None or ef <= sf:
        return None
    return frames_to_timecode(ef - sf, fps)


def validate_timecodes(start: str, end: str) -> tuple:
    """
    Validate a start/end timecode pair.
    Returns (is_valid: bool, error_message: str).
    Empty strings are allowed (placeholder mode).
    """
    if not start and not end:
        return True, ""

    if start and not TIMECODE_RE.match(start.strip()):
        return False, f"Formato inválido en start timecode: '{start}' — usa HH:MM:SS:FF"

    if end and not TIMECODE_RE.match(end.strip()):
        return False, f"Formato inválido en end timecode: '{end}' — usa HH:MM:SS:FF"

    if start:
        parts = parse_timecode(start)
        if parts is None:
            return False, f"Start timecode fuera de rango: '{start}' (minutos/segundos deben ser 00–59)"

    if end:
        parts = parse_timecode(end)
        if parts is None:
            return False, f"End timecode fuera de rango: '{end}' (minutos/segundos deben ser 00–59)"

    if start and end:
        sf = timecode_to_frames(start)
        ef = timecode_to_frames(end)
        if sf is not None and ef is not None and ef <= sf:
            return False, f"End timecode debe ser mayor que start: {start} ≥ {end}"

    return True, ""


# ── Placeholder factory ───────────────────────────────────────────────────────

def make_placeholder_clips(config: ProjectConfig) -> list:
    """Generate an EditPlanClip per deliverable with empty editorial fields."""
    clips = []
    for clip_n in range(1, config.num_clips + 1):
        clip_id = f"Clip{clip_n:02d}"
        for platform in config.platforms:
            for fmt in config.formats:
                clips.append(EditPlanClip(
                    clip_id        = clip_id,
                    start_timecode = "",
                    end_timecode   = "",
                    duration       = "",
                    platform       = platform,
                    format         = fmt,
                    goal           = "",
                    hook           = "",
                    title          = "",
                    caption        = "",
                    cta            = "",
                    notes          = "",
                    export_filename= build_filename(config, clip_n, platform, fmt),
                    status         = config.initial_status,
                ))
    return clips


# ── Writers ───────────────────────────────────────────────────────────────────

def write_edit_plan_csv(clips: list, root: Path) -> Path:
    out = root / "10_Admin" / "edit_plan.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EDIT_PLAN_CSV_HEADERS)
        writer.writeheader()
        for c in clips:
            writer.writerow({
                "clip_id":        c.clip_id,
                "start_timecode": c.start_timecode,
                "end_timecode":   c.end_timecode,
                "duration":       c.duration,
                "platform":       c.platform,
                "format":         c.format,
                "goal":           c.goal,
                "hook":           c.hook,
                "title":          c.title,
                "caption":        c.caption,
                "cta":            c.cta,
                "notes":          c.notes,
                "export_filename":c.export_filename,
                "status":         c.status,
            })
    return out


def write_edit_plan_md(clips: list, root: Path, config: ProjectConfig) -> Path:
    out = root / "10_Admin" / "edit_plan.md"

    # Group by clip_id
    by_clip: dict[str, list] = defaultdict(list)
    for c in clips:
        by_clip[c.clip_id].append(c)

    lines = [
        "# Edit Plan",
        f"## {config.client} — {config.project}",
        "",
        f"> ScaleCut v{__version__} · {config.created_at[:10]}  ",
        "> Rellena los timecodes y datos creativos antes de empezar la edición.",
        "> Este archivo es la fuente de verdad para el editor.",
        "",
        "---",
        "",
        "## Resumen",
        "",
        "| Clip | Start TC | End TC | Duración | Goal |",
        "|------|----------|--------|----------|------|",
    ]

    # Summary table — one row per unique clip
    seen = set()
    for c in clips:
        if c.clip_id not in seen:
            seen.add(c.clip_id)
            dur_s = ""
            if c.duration:
                secs = timecode_to_seconds(c.duration)
                dur_s = f" (~{int(secs)}s)" if secs else ""
            lines.append(
                f"| {c.clip_id} | {c.start_timecode or '—'} "
                f"| {c.end_timecode or '—'} "
                f"| {c.duration or '—'}{dur_s} | {c.goal or '—'} |"
            )

    lines += ["", "---", ""]

    # Detail section per clip
    for clip_id, items in by_clip.items():
        first = items[0]
        dur_label = ""
        if first.duration:
            secs = timecode_to_seconds(first.duration)
            dur_label = f" (~{int(secs)}s)" if secs else ""

        lines += [
            f"## {clip_id}",
            "",
        ]

        if first.start_timecode or first.end_timecode:
            lines.append(
                f"**Timecode:** `{first.start_timecode or '?'}` → "
                f"`{first.end_timecode or '?'}`{dur_label}"
            )
            lines.append("")

        lines += [
            "| Campo | Valor |",
            "|-------|-------|",
            f"| Goal | {first.goal or '_por definir_'} |",
            f"| Hook | {first.hook or '_por definir_'} |",
            f"| Título | {first.title or '_por definir_'} |",
            f"| Caption | {first.caption or '_por definir_'} |",
            f"| CTA | {first.cta or '_por definir_'} |",
            f"| Notas | {first.notes or '—'} |",
            "",
            "**Entregables:**",
            "",
            "| Plataforma | Formato | Estado | Filename |",
            "|------------|---------|--------|----------|",
        ]

        for d in items:
            lines.append(
                f"| {d.platform} | {d.format} | {d.status} | `{d.export_filename}` |"
            )

        lines += ["", "---", ""]

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_edit_plan_json(clips: list, root: Path, config: ProjectConfig,
                         fps: int = DEFAULT_FPS, mode: str = "placeholder") -> Path:
    out = root / "10_Admin" / "edit_plan.json"

    clip_dicts = []
    for c in clips:
        d = asdict(c)
        # Add seconds as float for plugin convenience
        d["duration_seconds"] = timecode_to_seconds(c.duration, fps) if c.duration else None
        clip_dicts.append(d)

    payload = {
        "scalecut_version": __version__,
        "schema_version":   "1.0",
        "project":          config.to_dict(),
        "fps":              fps,
        "mode":             mode,
        "total_clips":      config.num_clips,
        "total_deliverables": len(clips),
        "edit_plan":        clip_dicts,
        "_note": (
            "This file is designed to be read by a Premiere Pro or DaVinci Resolve "
            "plugin to create sequences, markers and auto-cuts. "
            "Fill in timecodes and creative fields before running the plugin."
        ),
    }

    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def write_markers_csv(clips: list, root: Path) -> Path:
    """
    Generate markers.csv — importable into Premiere Pro and DaVinci Resolve.
    One marker per deliverable, color-coded by platform.
    """
    out = root / "10_Admin" / "markers.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MARKERS_CSV_HEADERS)
        writer.writeheader()
        for c in clips:
            comment = " | ".join(filter(None, [c.goal, c.hook, c.notes]))
            writer.writerow({
                "marker_name":    f"{c.clip_id}_{c.platform.replace(' ', '')}_{c.format}",
                "start_timecode": c.start_timecode,
                "end_timecode":   c.end_timecode,
                "duration":       c.duration,
                "color":          PLATFORM_COLORS.get(c.platform, "White"),
                "comment":        comment,
                "platform":       c.platform,
                "format":         c.format,
                "export_filename":c.export_filename,
            })
    return out
