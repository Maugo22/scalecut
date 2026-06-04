"""Integration tests for all project file generators."""

import csv
import json
import re
import pytest
from pathlib import Path

from scalecut.folders import create_folders, build_folder_tree, FOLDERS
from scalecut.checklist import write_csv, write_markdown, CSV_HEADERS
from scalecut.preview import write_naming_preview
from scalecut.config_gen import write_config, GENERATED_FILES
from scalecut.readme_gen import write_readme
from scalecut.naming import generate_all_filenames
from tests.conftest import make_config

# ── shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def cfg(tmp_path):
    return make_config(
        client="Acme Studio",
        project="Lanzamiento Q4",
        delivery_date="2024-12-20",
        num_clips=2,
        platforms=["Instagram Reels", "TikTok"],
        formats=["9x16", "1x1"],
        version="01",
        output_path=str(tmp_path),
    )

@pytest.fixture
def root(cfg):
    return create_folders(cfg)


# =============================================================================
# Folder structure
# =============================================================================

class TestFolderStructure:

    def test_root_created(self, cfg, tmp_path):
        root = create_folders(cfg)
        assert root.is_dir()

    def test_root_name_follows_convention(self, cfg, tmp_path):
        root = create_folders(cfg)
        assert root.name == "ACME_STUDIO_LANZAMIENTO_Q4_20241220"

    def test_all_standard_folders_exist(self, cfg, root):
        for folder in FOLDERS:
            assert (root / folder).is_dir(), f"Missing: {folder}"

    def test_export_subfolders_created_per_format(self, cfg, root):
        for fmt in cfg.formats:
            assert (root / "07_Exports" / fmt).is_dir()

    def test_no_extra_export_subfolders(self, cfg, root):
        export_dirs = {p.name for p in (root / "07_Exports").iterdir()}
        assert export_dirs == set(cfg.formats)

    def test_idempotent_create(self, cfg, tmp_path):
        """Calling create_folders twice must not raise."""
        create_folders(cfg)
        create_folders(cfg)

    def test_build_folder_tree_length(self, cfg):
        tree = build_folder_tree(cfg)
        # 10 standard + 1 per format
        assert len(tree) == len(FOLDERS) + len(cfg.formats)


# =============================================================================
# delivery_checklist.csv
# =============================================================================

class TestDeliveryCsv:

    def test_file_created_with_correct_name(self, cfg, root):
        path = write_csv(cfg, root)
        assert path.name == "delivery_checklist.csv"
        assert path.exists()

    def test_headers_match_spec(self, cfg, root):
        write_csv(cfg, root)
        with open(root / "10_Admin" / "delivery_checklist.csv", newline="") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == CSV_HEADERS

    def test_row_count(self, cfg, root):
        write_csv(cfg, root)
        with open(root / "10_Admin" / "delivery_checklist.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        expected = cfg.num_clips * len(cfg.platforms) * len(cfg.formats)
        assert len(rows) == expected

    def test_export_path_column_populated(self, cfg, root):
        write_csv(cfg, root)
        with open(root / "10_Admin" / "delivery_checklist.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            assert row["Export_Path"].startswith("07_Exports/")
            assert row["Export_Path"].endswith(row["Filename"])

    def test_filenames_not_empty(self, cfg, root):
        write_csv(cfg, root)
        with open(root / "10_Admin" / "delivery_checklist.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        assert all(row["Filename"] for row in rows)

    def test_all_clips_present(self, cfg, root):
        write_csv(cfg, root)
        with open(root / "10_Admin" / "delivery_checklist.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        clips = {r["Clip"] for r in rows}
        assert clips == {"Clip01", "Clip02"}

    def test_status_column_matches_config(self, cfg, root):
        write_csv(cfg, root)
        with open(root / "10_Admin" / "delivery_checklist.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        assert all(r["Status"] == cfg.initial_status for r in rows)


# =============================================================================
# delivery_checklist.md
# =============================================================================

class TestDeliveryMarkdown:

    def test_file_created_with_correct_name(self, cfg, root):
        path = write_markdown(cfg, root)
        assert path.name == "delivery_checklist.md"
        assert path.exists()

    def test_has_checkboxes(self, cfg, root):
        write_markdown(cfg, root)
        content = (root / "10_Admin" / "delivery_checklist.md").read_text()
        assert "- [ ]" in content

    def test_grouped_by_clip(self, cfg, root):
        write_markdown(cfg, root)
        content = (root / "10_Admin" / "delivery_checklist.md").read_text()
        assert "## Clip01" in content
        assert "## Clip02" in content

    def test_contains_all_filenames(self, cfg, root):
        write_markdown(cfg, root)
        content = (root / "10_Admin" / "delivery_checklist.md").read_text()
        for d in generate_all_filenames(cfg):
            assert d["filename"] in content

    def test_has_progress_tracker(self, cfg, root):
        write_markdown(cfg, root)
        content = (root / "10_Admin" / "delivery_checklist.md").read_text()
        assert "## Progress tracker" in content

    def test_contains_project_metadata(self, cfg, root):
        write_markdown(cfg, root)
        content = (root / "10_Admin" / "delivery_checklist.md").read_text()
        assert cfg.client in content
        assert cfg.delivery_date in content


# =============================================================================
# naming_preview.md
# =============================================================================

class TestNamingPreview:

    def test_file_created_with_correct_name(self, cfg, root):
        path = write_naming_preview(cfg, root)
        assert path.name == "naming_preview.md"
        assert path.exists()

    def test_shows_naming_pattern(self, cfg, root):
        write_naming_preview(cfg, root)
        content = (root / "10_Admin" / "naming_preview.md").read_text()
        assert "CLIENT_PROJECT_ClipNN_PLATFORM_FORMAT_YYYYMMDD_VNN.mp4" in content

    def test_contains_token_table(self, cfg, root):
        write_naming_preview(cfg, root)
        content = (root / "10_Admin" / "naming_preview.md").read_text()
        assert "ACME_STUDIO" in content
        assert "LANZAMIENTO_Q4" in content
        assert "20241220" in content

    def test_contains_all_filenames(self, cfg, root):
        write_naming_preview(cfg, root)
        content = (root / "10_Admin" / "naming_preview.md").read_text()
        for d in generate_all_filenames(cfg):
            assert d["filename"] in content

    def test_grouped_by_clip(self, cfg, root):
        write_naming_preview(cfg, root)
        content = (root / "10_Admin" / "naming_preview.md").read_text()
        assert "### Clip01" in content
        assert "### Clip02" in content

    def test_total_count_mentioned(self, cfg, root):
        write_naming_preview(cfg, root)
        content = (root / "10_Admin" / "naming_preview.md").read_text()
        total = cfg.num_clips * len(cfg.platforms) * len(cfg.formats)
        assert str(total) in content


# =============================================================================
# project_config.json
# =============================================================================

class TestProjectConfig:

    def test_file_created(self, cfg, root):
        path = write_config(cfg, root)
        assert path.name == "project_config.json"
        assert path.exists()

    def test_valid_json(self, cfg, root):
        write_config(cfg, root)
        data = json.loads((root / "10_Admin" / "project_config.json").read_text())
        assert isinstance(data, dict)

    def test_top_level_keys(self, cfg, root):
        write_config(cfg, root)
        data = json.loads((root / "10_Admin" / "project_config.json").read_text())
        assert {"scalecut_version", "project", "summary", "folder_structure",
                "generated_files", "deliverables"} <= data.keys()

    def test_summary_total_deliverables(self, cfg, root):
        write_config(cfg, root)
        data = json.loads((root / "10_Admin" / "project_config.json").read_text())
        expected = cfg.num_clips * len(cfg.platforms) * len(cfg.formats)
        assert data["summary"]["total_deliverables"] == expected

    def test_summary_counts(self, cfg, root):
        write_config(cfg, root)
        data = json.loads((root / "10_Admin" / "project_config.json").read_text())
        assert data["summary"]["clips"]     == cfg.num_clips
        assert data["summary"]["platforms"] == len(cfg.platforms)
        assert data["summary"]["formats"]   == len(cfg.formats)

    def test_generated_files_list(self, cfg, root):
        write_config(cfg, root)
        data = json.loads((root / "10_Admin" / "project_config.json").read_text())
        assert data["generated_files"] == GENERATED_FILES

    def test_project_fields_match_config(self, cfg, root):
        write_config(cfg, root)
        data = json.loads((root / "10_Admin" / "project_config.json").read_text())
        assert data["project"]["client"]        == cfg.client
        assert data["project"]["delivery_date"] == cfg.delivery_date
        assert data["project"]["num_clips"]     == cfg.num_clips

    def test_deliverables_array_length(self, cfg, root):
        write_config(cfg, root)
        data = json.loads((root / "10_Admin" / "project_config.json").read_text())
        expected = cfg.num_clips * len(cfg.platforms) * len(cfg.formats)
        assert len(data["deliverables"]) == expected


# =============================================================================
# README.md
# =============================================================================

class TestReadme:

    def test_file_created_at_root(self, cfg, root):
        path = write_readme(cfg, root)
        assert path == root / "README.md"
        assert path.exists()

    def test_contains_client_and_project(self, cfg, root):
        write_readme(cfg, root)
        content = (root / "README.md").read_text()
        assert cfg.client in content
        assert cfg.project in content

    def test_contains_naming_convention(self, cfg, root):
        write_readme(cfg, root)
        content = (root / "README.md").read_text()
        assert "CLIENT_PROJECT_ClipNN_PLATFORM_FORMAT_YYYYMMDD_VNN.mp4" in content

    def test_references_new_checklist_filenames(self, cfg, root):
        write_readme(cfg, root)
        content = (root / "README.md").read_text()
        assert "delivery_checklist.csv" in content
        assert "delivery_checklist.md" in content

    def test_references_naming_preview(self, cfg, root):
        write_readme(cfg, root)
        content = (root / "README.md").read_text()
        assert "naming_preview.md" in content

    def test_contains_folder_structure(self, cfg, root):
        write_readme(cfg, root)
        content = (root / "README.md").read_text()
        assert "07_Exports" in content
        for fmt in cfg.formats:
            assert fmt in content

    def test_contains_total_deliverables(self, cfg, root):
        write_readme(cfg, root)
        content = (root / "README.md").read_text()
        total = cfg.num_clips * len(cfg.platforms) * len(cfg.formats)
        assert str(total) in content
