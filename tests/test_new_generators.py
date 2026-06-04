"""Tests for editor_instructions, prompts_ai, package ZIP, and demo config."""

import json
import zipfile
import io
import pytest
from pathlib import Path

from scalecut.editor_instructions import write_editor_instructions
from scalecut.prompts_ai import write_prompts_ai
from scalecut.package import create_zip, PACKAGE_FILES
from scalecut.demo import DEMO_PROJECT, make_demo_config
from scalecut.folders import create_folders
from scalecut.checklist import write_csv, write_markdown
from scalecut.config_gen import write_config
from scalecut.preview import write_naming_preview
from scalecut.readme_gen import write_readme
from scalecut.naming import generate_all_filenames
from tests.conftest import make_config


# ── Shared fixture: fully scaffolded project ──────────────────────────────────

@pytest.fixture
def scaffolded(tmp_path):
    """Return (config, root) with all files generated."""
    config = make_config(
        client="Acme Studio",
        project="Podcast Leadership",
        project_type="Podcast Repurposing",
        delivery_date="2024-12-20",
        num_clips=3,
        platforms=["Instagram Reels", "TikTok", "LinkedIn"],
        formats=["9x16", "1x1"],
        language="ES",
        output_path=str(tmp_path),
    )
    root = create_folders(config)
    write_csv(config, root)
    write_markdown(config, root)
    write_naming_preview(config, root)
    write_editor_instructions(config, root)
    write_prompts_ai(config, root)
    write_config(config, root)
    write_readme(config, root)
    return config, root


# =============================================================================
# editor_instructions.md
# =============================================================================

class TestEditorInstructions:

    def test_file_created_with_correct_name(self, tmp_path):
        config = make_config(output_path=str(tmp_path))
        root   = create_folders(config)
        path   = write_editor_instructions(config, root)
        assert path.name == "editor_instructions.md"
        assert path.exists()

    def test_contains_project_data(self, tmp_path):
        config = make_config(client="Nike", project="Verano24", output_path=str(tmp_path))
        root   = create_folders(config)
        write_editor_instructions(config, root)
        content = (root / "10_Admin" / "editor_instructions.md").read_text()
        assert "Nike"     in content
        assert "Verano24" in content

    def test_has_folder_structure_section(self, tmp_path):
        config = make_config(output_path=str(tmp_path))
        root   = create_folders(config)
        write_editor_instructions(config, root)
        content = (root / "10_Admin" / "editor_instructions.md").read_text()
        assert "Estructura de carpetas" in content
        assert "01_Footage" in content

    def test_has_naming_convention_section(self, tmp_path):
        config = make_config(output_path=str(tmp_path))
        root   = create_folders(config)
        write_editor_instructions(config, root)
        content = (root / "10_Admin" / "editor_instructions.md").read_text()
        assert "Convención de naming" in content
        assert "CLIENT_PROJECT_ClipNN" in content

    def test_has_platforms_and_formats_table(self, tmp_path):
        config = make_config(
            platforms=["Instagram Reels", "TikTok"],
            formats=["9x16"],
            output_path=str(tmp_path),
        )
        root = create_folders(config)
        write_editor_instructions(config, root)
        content = (root / "10_Admin" / "editor_instructions.md").read_text()
        assert "Plataformas y formatos" in content
        assert "Instagram Reels"        in content
        assert "TikTok"                 in content

    def test_has_premiere_pro_section(self, tmp_path):
        config = make_config(output_path=str(tmp_path))
        root   = create_folders(config)
        write_editor_instructions(config, root)
        content = (root / "10_Admin" / "editor_instructions.md").read_text()
        assert "Premiere Pro" in content

    def test_has_davinci_resolve_section(self, tmp_path):
        config = make_config(output_path=str(tmp_path))
        root   = create_folders(config)
        write_editor_instructions(config, root)
        content = (root / "10_Admin" / "editor_instructions.md").read_text()
        assert "DaVinci Resolve" in content

    def test_contains_all_export_filenames(self, tmp_path):
        config = make_config(
            num_clips=2,
            platforms=["TikTok"],
            formats=["9x16"],
            output_path=str(tmp_path),
        )
        root = create_folders(config)
        write_editor_instructions(config, root)
        content  = (root / "10_Admin" / "editor_instructions.md").read_text()
        for d in generate_all_filenames(config):
            assert d["filename"] in content

    def test_contains_delivery_date(self, tmp_path):
        config = make_config(delivery_date="2025-06-15", output_path=str(tmp_path))
        root   = create_folders(config)
        write_editor_instructions(config, root)
        content = (root / "10_Admin" / "editor_instructions.md").read_text()
        assert "2025-06-15" in content


# =============================================================================
# prompts_ai.md
# =============================================================================

class TestPromptsAI:

    def test_file_created_with_correct_name(self, tmp_path):
        config = make_config(output_path=str(tmp_path))
        root   = create_folders(config)
        path   = write_prompts_ai(config, root)
        assert path.name == "prompts_ai.md"
        assert path.exists()

    def test_contains_six_prompts(self, tmp_path):
        config = make_config(output_path=str(tmp_path))
        root   = create_folders(config)
        write_prompts_ai(config, root)
        content = (root / "10_Admin" / "prompts_ai.md").read_text()
        for n in range(1, 7):
            assert f"## {n}." in content

    def test_has_clip_selection_prompt(self, tmp_path):
        config = make_config(output_path=str(tmp_path))
        root   = create_folders(config)
        write_prompts_ai(config, root)
        content = (root / "10_Admin" / "prompts_ai.md").read_text()
        assert "Selección de clips" in content or "transcripción" in content.lower()

    def test_has_hook_generation_prompt(self, tmp_path):
        config = make_config(output_path=str(tmp_path))
        root   = create_folders(config)
        write_prompts_ai(config, root)
        content = (root / "10_Admin" / "prompts_ai.md").read_text()
        assert "hooks" in content.lower()

    def test_has_qa_prompt(self, tmp_path):
        config = make_config(output_path=str(tmp_path))
        root   = create_folders(config)
        write_prompts_ai(config, root)
        content = (root / "10_Admin" / "prompts_ai.md").read_text()
        assert "QA" in content or "Revisión" in content

    def test_uses_real_project_data(self, tmp_path):
        config = make_config(
            client="Nike",
            project="Verano24",
            platforms=["TikTok", "LinkedIn"],
            language="EN",
            output_path=str(tmp_path),
        )
        root = create_folders(config)
        write_prompts_ai(config, root)
        content = (root / "10_Admin" / "prompts_ai.md").read_text()
        assert "Nike"    in content
        assert "Verano24" in content
        assert "TikTok"  in content
        assert "EN"      in content

    def test_prompts_are_copy_paste_ready(self, tmp_path):
        """Each prompt block must be wrapped in a code fence."""
        config = make_config(output_path=str(tmp_path))
        root   = create_folders(config)
        write_prompts_ai(config, root)
        content = (root / "10_Admin" / "prompts_ai.md").read_text()
        assert content.count("```") >= 12  # 6 prompts × open+close


# =============================================================================
# ZIP package
# =============================================================================

class TestZipPackage:

    def test_returns_bytes(self, scaffolded):
        _, root = scaffolded
        result = create_zip(root)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_is_valid_zip(self, scaffolded):
        _, root = scaffolded
        result = create_zip(root)
        assert zipfile.is_zipfile(io.BytesIO(result))

    def test_contains_expected_files(self, scaffolded):
        _, root = scaffolded
        result = create_zip(root)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            names = set(zf.namelist())
        expected = {Path(f).name for f in PACKAGE_FILES}
        assert expected == names

    def test_csv_is_readable_from_zip(self, scaffolded):
        config, root = scaffolded
        result = create_zip(root)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            csv_bytes = zf.read("delivery_checklist.csv")
        assert b"Clip01" in csv_bytes

    def test_json_is_valid_in_zip(self, scaffolded):
        _, root = scaffolded
        result = create_zip(root)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            data = json.loads(zf.read("project_config.json"))
        assert "project" in data
        assert "summary" in data

    def test_editor_instructions_in_zip(self, scaffolded):
        _, root = scaffolded
        result = create_zip(root)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            names = zf.namelist()
        assert "editor_instructions.md" in names

    def test_prompts_ai_in_zip(self, scaffolded):
        _, root = scaffolded
        result = create_zip(root)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            names = zf.namelist()
        assert "prompts_ai.md" in names

    def test_zip_with_missing_file_skips_gracefully(self, tmp_path):
        """create_zip should not crash if a file doesn't exist yet."""
        config = make_config(output_path=str(tmp_path))
        root   = create_folders(config)
        # Only generate some files, not all
        write_csv(config, root)
        result = create_zip(root)           # must not raise
        assert zipfile.is_zipfile(io.BytesIO(result))


# =============================================================================
# Demo config
# =============================================================================

class TestDemoConfig:

    def test_demo_project_has_required_keys(self):
        required = {"client", "project", "project_type", "delivery_date",
                    "num_clips", "platforms", "formats", "version",
                    "language", "initial_status"}
        assert required <= DEMO_PROJECT.keys()

    def test_demo_project_client(self):
        assert DEMO_PROJECT["client"] == "Acme Studio"

    def test_demo_project_project(self):
        assert DEMO_PROJECT["project"] == "Podcast Leadership"

    def test_demo_project_type(self):
        assert DEMO_PROJECT["project_type"] == "Podcast Repurposing"

    def test_make_demo_config_returns_project_config(self, tmp_path):
        from scalecut.models import ProjectConfig
        config = make_demo_config(str(tmp_path))
        assert isinstance(config, ProjectConfig)

    def test_make_demo_config_fields_match(self, tmp_path):
        config = make_demo_config(str(tmp_path))
        assert config.client       == DEMO_PROJECT["client"]
        assert config.project      == DEMO_PROJECT["project"]
        assert config.num_clips    == DEMO_PROJECT["num_clips"]
        assert config.platforms    == DEMO_PROJECT["platforms"]
        assert config.formats      == DEMO_PROJECT["formats"]

    def test_make_demo_config_can_scaffold(self, tmp_path):
        """Demo config must be able to generate a full project without errors."""
        config = make_demo_config(str(tmp_path))
        root   = create_folders(config)
        write_csv(config, root)
        write_markdown(config, root)
        write_naming_preview(config, root)
        write_editor_instructions(config, root)
        write_prompts_ai(config, root)
        write_config(config, root)
        write_readme(config, root)
        assert (root / "10_Admin" / "delivery_checklist.csv").exists()
        assert (root / "10_Admin" / "editor_instructions.md").exists()
        assert (root / "10_Admin" / "prompts_ai.md").exists()

    def test_demo_deliverable_count(self, tmp_path):
        config = make_demo_config(str(tmp_path))
        deliverables = generate_all_filenames(config)
        expected = (
            DEMO_PROJECT["num_clips"]
            * len(DEMO_PROJECT["platforms"])
            * len(DEMO_PROJECT["formats"])
        )
        assert len(deliverables) == expected
