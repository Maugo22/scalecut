"""Tests for scalecut update command and update.py module."""

import csv
import pytest
from pathlib import Path
from click.testing import CliRunner

from scalecut.update import update_status, UpdateError
from scalecut.cli import main
from scalecut.checklist import write_csv
from scalecut.config_gen import write_config
from scalecut.folders import create_folders
from tests.conftest import make_config


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def project_root(tmp_path):
    """Scaffolded project: 2 clips × Instagram Reels + TikTok × 9x16 = 4 rows."""
    cfg = make_config(
        client="TestCorp",
        project="CampaignQ1",
        delivery_date="2025-03-01",
        num_clips=2,
        platforms=["Instagram Reels", "TikTok"],
        formats=["9x16"],
        output_path=str(tmp_path),
    )
    root = create_folders(cfg)
    write_csv(cfg, root)
    write_config(cfg, root)
    return root


@pytest.fixture
def acme_root(tmp_path):
    """Project that produces ACMESTUDIO_PODCASTLEADERSHIP_20260610."""
    cfg = make_config(
        client="AcmeStudio",
        project="PodcastLeadership",
        delivery_date="2026-06-10",
        num_clips=2,
        platforms=["Instagram Reels", "TikTok"],
        formats=["9x16"],
        output_path=str(tmp_path),
    )
    root = create_folders(cfg)
    write_csv(cfg, root)
    write_config(cfg, root)
    return root


def _read_statuses(root: Path) -> list[str]:
    checklist = root / "10_Admin" / "delivery_checklist.csv"
    rows = list(csv.DictReader(checklist.read_text(encoding="utf-8").splitlines()))
    return [r["Status"] for r in rows]


def _rows(root: Path) -> list[dict]:
    checklist = root / "10_Admin" / "delivery_checklist.csv"
    return list(csv.DictReader(checklist.read_text(encoding="utf-8").splitlines()))


# ── update_status: basic behaviour ────────────────────────────────────────────

class TestUpdateStatusBasic:

    def test_updates_matching_clip_and_platform(self, project_root):
        count = update_status(project_root, "Clip01", "Instagram Reels", "In edit")
        assert count == 1

    def test_updated_row_has_new_status(self, project_root):
        update_status(project_root, "Clip01", "Instagram Reels", "In edit")
        rows = _rows(project_root)
        target = [r for r in rows if r["Clip"] == "Clip01" and r["Platform"] == "Instagram Reels"]
        assert all(r["Status"] == "In edit" for r in target)

    def test_unmatched_rows_unchanged(self, project_root):
        update_status(project_root, "Clip01", "Instagram Reels", "In edit")
        rows = _rows(project_root)
        others = [r for r in rows if not (r["Clip"] == "Clip01" and r["Platform"] == "Instagram Reels")]
        assert all(r["Status"] == "Not started" for r in others)

    def test_updates_all_clips_for_platform_when_clip_matches_all(self, project_root):
        update_status(project_root, "Clip01", "TikTok", "Approved")
        update_status(project_root, "Clip02", "TikTok", "Approved")
        statuses = _read_statuses(project_root)
        tiktok_statuses = [
            r["Status"] for r in _rows(project_root) if r["Platform"] == "TikTok"
        ]
        assert all(s == "Approved" for s in tiktok_statuses)

    def test_returns_correct_count(self, project_root):
        count = update_status(project_root, "Clip01", "Instagram Reels", "In edit")
        assert count == 1

    def test_with_format_filter_updates_only_matching_format(self, tmp_path):
        cfg = make_config(
            client="X", project="Y", delivery_date="2025-01-01",
            num_clips=1, platforms=["Instagram Reels"], formats=["9x16", "1x1"],
            output_path=str(tmp_path),
        )
        root = create_folders(cfg)
        write_csv(cfg, root)
        write_config(cfg, root)
        count = update_status(root, "Clip01", "Instagram Reels", "Delivered", fmt="9x16")
        assert count == 1
        rows = _rows(root)
        nine = next(r for r in rows if r["Format"] == "9x16")
        one = next(r for r in rows if r["Format"] == "1x1")
        assert nine["Status"] == "Delivered"
        assert one["Status"] == "Not started"


# ── update_status: platform fuzzy matching ────────────────────────────────────

class TestUpdatePlatformFuzzyMatch:

    def test_no_spaces_matches_spaced_platform(self, project_root):
        count = update_status(project_root, "Clip01", "InstagramReels", "In edit")
        assert count == 1

    def test_lowercase_matches(self, project_root):
        count = update_status(project_root, "Clip01", "instagram reels", "In edit")
        assert count == 1

    def test_hyphens_match(self, project_root):
        count = update_status(project_root, "Clip01", "Instagram-Reels", "In edit")
        assert count == 1

    def test_tiktok_exact_matches(self, project_root):
        count = update_status(project_root, "Clip02", "TikTok", "Exported")
        assert count == 1

    def test_tiktok_lowercase_matches(self, project_root):
        count = update_status(project_root, "Clip02", "tiktok", "Exported")
        assert count == 1


# ── update_status: error cases ────────────────────────────────────────────────

class TestUpdateErrors:

    def test_nonexistent_path_raises(self, tmp_path):
        with pytest.raises(UpdateError, match="Path no encontrado"):
            update_status(tmp_path / "ghost", "Clip01", "TikTok", "In edit")

    def test_missing_checklist_raises(self, project_root):
        (project_root / "10_Admin" / "delivery_checklist.csv").unlink()
        with pytest.raises(UpdateError, match="delivery_checklist.csv"):
            update_status(project_root, "Clip01", "TikTok", "In edit")

    def test_no_matching_clip_raises(self, project_root):
        with pytest.raises(UpdateError, match="No se encontraron"):
            update_status(project_root, "Clip99", "TikTok", "In edit")

    def test_no_matching_platform_raises(self, project_root):
        with pytest.raises(UpdateError, match="No se encontraron"):
            update_status(project_root, "Clip01", "YouTube", "In edit")


# ── Fuzzy path resolution for update ─────────────────────────────────────────

class TestFuzzyPathUpdate:
    """update_status resolves human-friendly paths to sanitized folder names."""

    def test_sanitized_folder_name_is_expected(self, acme_root):
        assert acme_root.name == "ACMESTUDIO_PODCASTLEADERSHIP_20260610"

    def test_human_path_resolves_and_updates(self, acme_root):
        human = acme_root.parent / "AcmeStudio_PodcastLeadership_2026-06-10"
        count = update_status(human, "Clip01", "Instagram Reels", "In edit")
        assert count == 1

    def test_human_path_change_persisted_to_real_folder(self, acme_root):
        human = acme_root.parent / "AcmeStudio_PodcastLeadership_2026-06-10"
        update_status(human, "Clip01", "Instagram Reels", "Approved")
        rows = _rows(acme_root)
        target = next(
            r for r in rows
            if r["Clip"] == "Clip01" and r["Platform"] == "Instagram Reels"
        )
        assert target["Status"] == "Approved"

    def test_lowercase_hyphen_path_resolves(self, acme_root):
        lower = acme_root.parent / "acmestudio-podcastleadership-20260610"
        count = update_status(lower, "Clip02", "TikTok", "Delivered")
        assert count == 1

    def test_fuzzy_platform_and_fuzzy_path_combined(self, acme_root):
        human = acme_root.parent / "AcmeStudio_PodcastLeadership_2026-06-10"
        count = update_status(human, "Clip01", "InstagramReels", "In edit")
        assert count == 1


# ── CLI update command ────────────────────────────────────────────────────────

class TestCliUpdate:

    def test_update_exact_path_exit_0(self, project_root):
        runner = CliRunner()
        result = runner.invoke(main, [
            "update", str(project_root),
            "--clip", "Clip01", "--platform", "TikTok", "--status", "In edit",
        ])
        assert result.exit_code == 0

    def test_update_shows_count(self, project_root):
        runner = CliRunner()
        result = runner.invoke(main, [
            "update", str(project_root),
            "--clip", "Clip01", "--platform", "TikTok", "--status", "In edit",
        ])
        assert "1" in result.output

    def test_update_human_path_exit_0(self, acme_root):
        runner = CliRunner()
        human = str(acme_root.parent / "AcmeStudio_PodcastLeadership_2026-06-10")
        result = runner.invoke(main, [
            "update", human,
            "--clip", "Clip01", "--platform", "InstagramReels", "--status", "In edit",
        ])
        assert result.exit_code == 0

    def test_update_human_path_change_persisted(self, acme_root):
        runner = CliRunner()
        human = str(acme_root.parent / "AcmeStudio_PodcastLeadership_2026-06-10")
        runner.invoke(main, [
            "update", human,
            "--clip", "Clip01", "--platform", "InstagramReels", "--status", "Approved",
        ])
        rows = _rows(acme_root)
        target = next(
            r for r in rows
            if r["Clip"] == "Clip01" and r["Platform"] == "Instagram Reels"
        )
        assert target["Status"] == "Approved"

    def test_update_nonexistent_path_exit_1(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, [
            "update", str(tmp_path / "ghost"),
            "--clip", "Clip01", "--platform", "TikTok", "--status", "In edit",
        ])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_update_bad_clip_exit_1(self, project_root):
        runner = CliRunner()
        result = runner.invoke(main, [
            "update", str(project_root),
            "--clip", "Clip99", "--platform", "TikTok", "--status", "In edit",
        ])
        assert result.exit_code == 1
        assert "Error" in result.output
