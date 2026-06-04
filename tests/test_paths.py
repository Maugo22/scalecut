"""Tests for fuzzy project path resolution (scalecut/paths.py)."""

import pytest
from pathlib import Path

from scalecut.paths import resolve_project_path, ProjectPathError


class TestResolveExactPath:

    def test_existing_path_returned_directly(self, tmp_path):
        project = tmp_path / "ACMESTUDIO_FOO_20260610"
        project.mkdir()
        assert resolve_project_path(project) == project

    def test_exact_path_as_string(self, tmp_path):
        project = tmp_path / "ACMESTUDIO_FOO_20260610"
        project.mkdir()
        result = resolve_project_path(str(project))
        assert result == project


class TestResolveFuzzyPath:

    def test_human_name_resolves_to_sanitized_folder(self, tmp_path):
        (tmp_path / "ACMESTUDIO_PODCASTLEADERSHIP_20260610").mkdir()
        result = resolve_project_path(tmp_path / "AcmeStudio_PodcastLeadership_2026-06-10")
        assert result.name == "ACMESTUDIO_PODCASTLEADERSHIP_20260610"

    def test_lowercase_name_resolves(self, tmp_path):
        (tmp_path / "NIKE_VERANO_20241215").mkdir()
        result = resolve_project_path(tmp_path / "nike_verano_2024-12-15")
        assert result.name == "NIKE_VERANO_20241215"

    def test_hyphens_vs_underscores_match(self, tmp_path):
        (tmp_path / "FOO_BAR_20260101").mkdir()
        result = resolve_project_path(tmp_path / "FOO-BAR-20260101")
        assert result.name == "FOO_BAR_20260101"

    def test_spaces_stripped_for_match(self, tmp_path):
        (tmp_path / "ACME_PROJECT_20260101").mkdir()
        result = resolve_project_path(tmp_path / "Acme Project 20260101")
        assert result.name == "ACME_PROJECT_20260101"

    def test_mixed_separators_match(self, tmp_path):
        (tmp_path / "ACMESTUDIO_PODCASTLEADERSHIP_20260610").mkdir()
        result = resolve_project_path(tmp_path / "acmestudio-podcast_leadership--20260610")
        assert result.name == "ACMESTUDIO_PODCASTLEADERSHIP_20260610"


class TestResolveErrors:

    def test_nonexistent_path_no_parent_raises(self, tmp_path):
        with pytest.raises(ProjectPathError, match="Path no encontrado"):
            resolve_project_path(tmp_path / "ghost" / "nested")

    def test_nonexistent_path_no_fuzzy_match_raises(self, tmp_path):
        (tmp_path / "COMPLETELY_DIFFERENT_20260101").mkdir()
        with pytest.raises(ProjectPathError, match="Path no encontrado"):
            resolve_project_path(tmp_path / "AcmeStudio_Foo_2026-06-10")

    def test_multiple_matches_raises(self, tmp_path):
        # Use underscore vs hyphen — both normalize to "acmestudio20260610" and
        # ARE distinct on case-insensitive filesystems (macOS) unlike mixed-case pairs.
        (tmp_path / "ACME_STUDIO_20260610").mkdir()
        (tmp_path / "ACME-STUDIO-20260610").mkdir()
        with pytest.raises(ProjectPathError, match="Múltiples proyectos coinciden"):
            resolve_project_path(tmp_path / "AcmeStudio20260610")


class TestFuzzyIntegrationWithReport:
    """Confirm load_report resolves fuzzy paths end-to-end."""

    def test_report_accepts_human_path(self, tmp_path):
        from scalecut.folders import create_folders
        from scalecut.checklist import write_csv
        from scalecut.config_gen import write_config
        from scalecut.report import load_report
        from tests.conftest import make_config

        cfg = make_config(
            client="AcmeStudio",
            project="PodcastLeadership",
            delivery_date="2026-06-10",
            output_path=str(tmp_path),
        )
        root = create_folders(cfg)
        write_csv(cfg, root)
        write_config(cfg, root)

        human_path = tmp_path / "AcmeStudio_PodcastLeadership_2026-06-10"
        data = load_report(human_path)
        assert data["client"] == "AcmeStudio"
