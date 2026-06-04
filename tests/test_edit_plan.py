"""Tests for scalecut/edit_plan.py — timecodes, generators, placeholder mode."""

import csv
import json
import pytest
from pathlib import Path

from scalecut.edit_plan import (
    DEFAULT_FPS,
    EditPlanClip,
    calculate_duration,
    frames_to_timecode,
    make_placeholder_clips,
    parse_timecode,
    timecode_to_frames,
    timecode_to_seconds,
    validate_timecodes,
    write_edit_plan_csv,
    write_edit_plan_md,
    write_edit_plan_json,
    write_markers_csv,
    EDIT_PLAN_CSV_HEADERS,
    MARKERS_CSV_HEADERS,
)
from scalecut.folders import create_folders
from tests.conftest import make_config


# ── Shared fixture ────────────────────────────────────────────────────────────

@pytest.fixture
def cfg(tmp_path):
    return make_config(
        client="Acme Studio",
        project="Podcast Leadership",
        num_clips=2,
        platforms=["Instagram Reels", "TikTok"],
        formats=["9x16", "1x1"],
        output_path=str(tmp_path),
    )

@pytest.fixture
def root(cfg):
    return create_folders(cfg)

@pytest.fixture
def placeholder_clips(cfg):
    return make_placeholder_clips(cfg)

@pytest.fixture
def filled_clips(cfg):
    """Two deliverables with real timecode data."""
    return [
        EditPlanClip(
            clip_id="Clip01", start_timecode="00:00:10:00", end_timecode="00:01:25:00",
            duration="00:01:15:00", platform="Instagram Reels", format="9x16",
            goal="brand awareness", hook="Hook de apertura", title="Mi título",
            caption="Caption aquí", cta="Síguenos", notes="Nota del editor",
            export_filename="ACME_STUDIO_PODCAST_Clip01_INSTA_9x16_20241220_V01.mp4",
            status="Not started",
        ),
        EditPlanClip(
            clip_id="Clip01", start_timecode="00:00:10:00", end_timecode="00:01:25:00",
            duration="00:01:15:00", platform="TikTok", format="9x16",
            goal="brand awareness", hook="Hook de apertura", title="Mi título",
            caption="Caption aquí", cta="Síguenos", notes="",
            export_filename="ACME_STUDIO_PODCAST_Clip01_TIKTOK_9x16_20241220_V01.mp4",
            status="Not started",
        ),
    ]


# =============================================================================
# Timecode parsing
# =============================================================================

class TestTimecodeParser:

    @pytest.mark.parametrize("tc, expected", [
        ("00:00:00:00", (0, 0, 0, 0)),
        ("01:02:03:04", (1, 2, 3, 4)),
        ("25:59:59:24", (25, 59, 59, 24)),
        ("00:00:10:00", (0, 0, 10, 0)),
    ])
    def test_valid_timecodes(self, tc, expected):
        assert parse_timecode(tc) == expected

    @pytest.mark.parametrize("tc", [
        "",
        "invalid",
        "00:00:00",         # missing frames
        "00:00:00:00:00",   # too many parts
        "0:0:0:0",          # wrong padding
        "00:60:00:00",      # 60 minutes
        "00:00:60:00",      # 60 seconds
    ])
    def test_invalid_timecodes(self, tc):
        assert parse_timecode(tc) is None


# =============================================================================
# Timecode to frames
# =============================================================================

class TestTimecodeToFrames:

    def test_zero_timecode(self):
        assert timecode_to_frames("00:00:00:00") == 0

    def test_one_second(self):
        assert timecode_to_frames("00:00:01:00", fps=25) == 25

    def test_one_minute(self):
        assert timecode_to_frames("00:01:00:00", fps=25) == 25 * 60

    def test_one_hour(self):
        assert timecode_to_frames("01:00:00:00", fps=25) == 25 * 3600

    def test_complex_timecode(self):
        # 1h 2m 3s 4f at 25fps
        expected = 1 * 3600 * 25 + 2 * 60 * 25 + 3 * 25 + 4
        assert timecode_to_frames("01:02:03:04", fps=25) == expected

    def test_invalid_returns_none(self):
        assert timecode_to_frames("invalid") is None

    def test_custom_fps(self):
        assert timecode_to_frames("00:00:01:00", fps=30) == 30


# =============================================================================
# Frames to timecode (roundtrip)
# =============================================================================

class TestFramesRoundtrip:

    @pytest.mark.parametrize("tc", [
        "00:00:00:00",
        "00:00:01:00",
        "00:01:00:00",
        "01:00:00:00",
        "00:01:30:12",
    ])
    def test_roundtrip(self, tc):
        frames = timecode_to_frames(tc, fps=25)
        assert frames is not None
        result = frames_to_timecode(frames, fps=25)
        assert result == tc


# =============================================================================
# Duration calculation
# =============================================================================

class TestCalculateDuration:

    def test_basic_duration(self):
        result = calculate_duration("00:00:10:00", "00:01:25:00")
        assert result == "00:01:15:00"

    def test_exact_one_second(self):
        result = calculate_duration("00:00:00:00", "00:00:01:00", fps=25)
        assert result == "00:00:01:00"

    def test_end_equals_start_returns_none(self):
        assert calculate_duration("00:00:10:00", "00:00:10:00") is None

    def test_end_before_start_returns_none(self):
        assert calculate_duration("00:01:00:00", "00:00:30:00") is None

    def test_invalid_start_returns_none(self):
        assert calculate_duration("invalid", "00:01:00:00") is None

    def test_invalid_end_returns_none(self):
        assert calculate_duration("00:00:10:00", "invalid") is None

    def test_duration_in_seconds(self):
        # 75 seconds at 25fps
        dur = calculate_duration("00:00:10:00", "00:01:25:00", fps=25)
        secs = timecode_to_seconds(dur, fps=25)
        assert secs == 75.0


# =============================================================================
# Timecode validation
# =============================================================================

class TestValidateTimecodes:

    def test_both_empty_is_valid(self):
        valid, msg = validate_timecodes("", "")
        assert valid is True
        assert msg == ""

    def test_only_start_valid_format(self):
        valid, msg = validate_timecodes("00:00:10:00", "")
        assert valid is True

    def test_only_end_valid_format(self):
        valid, msg = validate_timecodes("", "00:01:00:00")
        assert valid is True

    def test_valid_pair(self):
        valid, msg = validate_timecodes("00:00:10:00", "00:01:25:00")
        assert valid is True
        assert msg == ""

    def test_invalid_start_format(self):
        valid, msg = validate_timecodes("not-a-tc", "00:01:00:00")
        assert valid is False
        assert "start" in msg.lower()

    def test_invalid_end_format(self):
        valid, msg = validate_timecodes("00:00:10:00", "bad")
        assert valid is False
        assert "end" in msg.lower()

    def test_end_equals_start_invalid(self):
        valid, msg = validate_timecodes("00:00:10:00", "00:00:10:00")
        assert valid is False
        assert "mayor" in msg.lower() or "greater" in msg.lower() or "end" in msg.lower()

    def test_end_before_start_invalid(self):
        valid, msg = validate_timecodes("00:01:00:00", "00:00:30:00")
        assert valid is False

    def test_invalid_minutes_in_start(self):
        valid, msg = validate_timecodes("00:60:00:00", "00:61:00:00")
        assert valid is False

    def test_invalid_seconds_in_end(self):
        valid, msg = validate_timecodes("00:00:10:00", "00:00:60:00")
        assert valid is False


# =============================================================================
# Placeholder factory
# =============================================================================

class TestPlaceholderMode:

    def test_count(self, cfg, placeholder_clips):
        expected = cfg.num_clips * len(cfg.platforms) * len(cfg.formats)
        assert len(placeholder_clips) == expected

    def test_empty_timecodes(self, placeholder_clips):
        for c in placeholder_clips:
            assert c.start_timecode == ""
            assert c.end_timecode   == ""
            assert c.duration       == ""

    def test_empty_creative_fields(self, placeholder_clips):
        for c in placeholder_clips:
            assert c.goal    == ""
            assert c.hook    == ""
            assert c.title   == ""
            assert c.caption == ""
            assert c.cta     == ""

    def test_export_filenames_populated(self, placeholder_clips):
        for c in placeholder_clips:
            assert c.export_filename.endswith(".mp4")
            assert c.clip_id in c.export_filename

    def test_all_clips_represented(self, cfg, placeholder_clips):
        clip_ids = {c.clip_id for c in placeholder_clips}
        expected = {f"Clip{n:02d}" for n in range(1, cfg.num_clips + 1)}
        assert clip_ids == expected

    def test_all_platforms_represented(self, cfg, placeholder_clips):
        platforms = {c.platform for c in placeholder_clips}
        assert platforms == set(cfg.platforms)

    def test_status_matches_config(self, cfg, placeholder_clips):
        for c in placeholder_clips:
            assert c.status == cfg.initial_status


# =============================================================================
# edit_plan.csv
# =============================================================================

class TestEditPlanCsv:

    def test_file_created(self, cfg, root, placeholder_clips):
        path = write_edit_plan_csv(placeholder_clips, root)
        assert path.name == "edit_plan.csv"
        assert path.exists()

    def test_headers(self, cfg, root, placeholder_clips):
        write_edit_plan_csv(placeholder_clips, root)
        with open(root / "10_Admin" / "edit_plan.csv", newline="") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == EDIT_PLAN_CSV_HEADERS

    def test_row_count(self, cfg, root, placeholder_clips):
        write_edit_plan_csv(placeholder_clips, root)
        with open(root / "10_Admin" / "edit_plan.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == len(placeholder_clips)

    def test_export_filename_column_populated(self, cfg, root, placeholder_clips):
        write_edit_plan_csv(placeholder_clips, root)
        with open(root / "10_Admin" / "edit_plan.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            assert row["export_filename"].endswith(".mp4")

    def test_filled_clips_written_correctly(self, cfg, root, filled_clips):
        write_edit_plan_csv(filled_clips, root)
        with open(root / "10_Admin" / "edit_plan.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["start_timecode"] == "00:00:10:00"
        assert rows[0]["goal"]           == "brand awareness"
        assert rows[0]["hook"]           == "Hook de apertura"


# =============================================================================
# edit_plan.md
# =============================================================================

class TestEditPlanMarkdown:

    def test_file_created(self, cfg, root, placeholder_clips):
        path = write_edit_plan_md(placeholder_clips, root, cfg)
        assert path.name == "edit_plan.md"
        assert path.exists()

    def test_contains_project_data(self, cfg, root, placeholder_clips):
        write_edit_plan_md(placeholder_clips, root, cfg)
        content = (root / "10_Admin" / "edit_plan.md").read_text()
        assert cfg.client  in content
        assert cfg.project in content

    def test_grouped_by_clip(self, cfg, root, placeholder_clips):
        write_edit_plan_md(placeholder_clips, root, cfg)
        content = (root / "10_Admin" / "edit_plan.md").read_text()
        assert "## Clip01" in content
        assert "## Clip02" in content

    def test_has_summary_table(self, cfg, root, placeholder_clips):
        write_edit_plan_md(placeholder_clips, root, cfg)
        content = (root / "10_Admin" / "edit_plan.md").read_text()
        assert "## Resumen" in content

    def test_filled_clips_show_timecodes(self, cfg, root, filled_clips):
        write_edit_plan_md(filled_clips, root, cfg)
        content = (root / "10_Admin" / "edit_plan.md").read_text()
        assert "00:00:10:00" in content
        assert "00:01:25:00" in content

    def test_contains_export_filenames(self, cfg, root, filled_clips):
        write_edit_plan_md(filled_clips, root, cfg)
        content = (root / "10_Admin" / "edit_plan.md").read_text()
        for c in filled_clips:
            assert c.export_filename in content


# =============================================================================
# edit_plan.json
# =============================================================================

class TestEditPlanJson:

    def test_file_created(self, cfg, root, placeholder_clips):
        path = write_edit_plan_json(placeholder_clips, root, cfg)
        assert path.name == "edit_plan.json"
        assert path.exists()

    def test_valid_json(self, cfg, root, placeholder_clips):
        write_edit_plan_json(placeholder_clips, root, cfg)
        data = json.loads((root / "10_Admin" / "edit_plan.json").read_text())
        assert isinstance(data, dict)

    def test_top_level_keys(self, cfg, root, placeholder_clips):
        write_edit_plan_json(placeholder_clips, root, cfg)
        data = json.loads((root / "10_Admin" / "edit_plan.json").read_text())
        assert "scalecut_version" in data
        assert "edit_plan"        in data
        assert "fps"              in data
        assert "mode"             in data
        assert "project"          in data

    def test_edit_plan_array_length(self, cfg, root, placeholder_clips):
        write_edit_plan_json(placeholder_clips, root, cfg)
        data = json.loads((root / "10_Admin" / "edit_plan.json").read_text())
        assert len(data["edit_plan"]) == len(placeholder_clips)

    def test_mode_field(self, cfg, root, placeholder_clips):
        write_edit_plan_json(placeholder_clips, root, cfg, mode="placeholder")
        data = json.loads((root / "10_Admin" / "edit_plan.json").read_text())
        assert data["mode"] == "placeholder"

    def test_duration_seconds_present(self, cfg, root, filled_clips):
        write_edit_plan_json(filled_clips, root, cfg)
        data = json.loads((root / "10_Admin" / "edit_plan.json").read_text())
        first = data["edit_plan"][0]
        assert "duration_seconds" in first
        assert first["duration_seconds"] == 75.0

    def test_duration_seconds_null_for_placeholder(self, cfg, root, placeholder_clips):
        write_edit_plan_json(placeholder_clips, root, cfg)
        data = json.loads((root / "10_Admin" / "edit_plan.json").read_text())
        for item in data["edit_plan"]:
            assert item["duration_seconds"] is None

    def test_project_fields_match_config(self, cfg, root, placeholder_clips):
        write_edit_plan_json(placeholder_clips, root, cfg)
        data = json.loads((root / "10_Admin" / "edit_plan.json").read_text())
        assert data["project"]["client"]  == cfg.client
        assert data["project"]["project"] == cfg.project


# =============================================================================
# markers.csv
# =============================================================================

class TestMarkersCsv:

    def test_file_created(self, cfg, root, placeholder_clips):
        path = write_markers_csv(placeholder_clips, root)
        assert path.name == "markers.csv"
        assert path.exists()

    def test_headers(self, cfg, root, placeholder_clips):
        write_markers_csv(placeholder_clips, root)
        with open(root / "10_Admin" / "markers.csv", newline="") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == MARKERS_CSV_HEADERS

    def test_row_count(self, cfg, root, placeholder_clips):
        write_markers_csv(placeholder_clips, root)
        with open(root / "10_Admin" / "markers.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == len(placeholder_clips)

    def test_color_column_populated(self, cfg, root, filled_clips):
        write_markers_csv(filled_clips, root)
        with open(root / "10_Admin" / "markers.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        colors = {r["color"] for r in rows}
        assert colors  # at least one color assigned, not all empty

    def test_marker_name_not_empty(self, cfg, root, placeholder_clips):
        write_markers_csv(placeholder_clips, root)
        with open(root / "10_Admin" / "markers.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            assert row["marker_name"].strip() != ""

    def test_export_filename_populated(self, cfg, root, placeholder_clips):
        write_markers_csv(placeholder_clips, root)
        with open(root / "10_Admin" / "markers.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            assert row["export_filename"].endswith(".mp4")

    def test_filled_timecodes_written(self, cfg, root, filled_clips):
        write_markers_csv(filled_clips, root)
        with open(root / "10_Admin" / "markers.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["start_timecode"] == "00:00:10:00"
        assert rows[0]["end_timecode"]   == "00:01:25:00"
