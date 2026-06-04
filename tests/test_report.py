"""Tests for scalecut report command and report.py module."""

import csv
import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from scalecut.report import load_report, ReportError
from scalecut.cli import main
from scalecut.checklist import write_csv
from scalecut.config_gen import write_config
from scalecut.folders import create_folders
from tests.conftest import make_config


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def project_root(tmp_path):
    """A fully scaffolded project with mixed statuses."""
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


def _set_statuses(root: Path, statuses: list[str]) -> None:
    """Overwrite the Status column in delivery_checklist.csv."""
    checklist = root / "10_Admin" / "delivery_checklist.csv"
    rows = list(csv.DictReader(checklist.read_text(encoding="utf-8").splitlines()))
    for row, status in zip(rows, statuses):
        row["Status"] = status
    with open(checklist, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ── load_report: valid project ─────────────────────────────────────────────────

class TestLoadReportValid:

    def test_returns_client(self, project_root):
        data = load_report(project_root)
        assert data["client"] == "TestCorp"

    def test_returns_project(self, project_root):
        data = load_report(project_root)
        assert data["project"] == "CampaignQ1"

    def test_returns_project_type(self, project_root):
        data = load_report(project_root)
        assert data["project_type"] == "Campaña publicitaria"

    def test_returns_delivery_date(self, project_root):
        data = load_report(project_root)
        assert data["delivery_date"] == "2025-03-01"

    def test_returns_total_deliverables(self, project_root):
        # 2 clips × 2 platforms × 1 format = 4
        data = load_report(project_root)
        assert data["total"] == 4

    def test_returns_platforms(self, project_root):
        data = load_report(project_root)
        assert set(data["platforms"]) == {"Instagram Reels", "TikTok"}

    def test_returns_formats(self, project_root):
        data = load_report(project_root)
        assert data["formats"] == ["9x16"]

    def test_next_action_present(self, project_root):
        data = load_report(project_root)
        assert isinstance(data["next_action"], str)
        assert len(data["next_action"]) > 0


# ── load_report: error cases ───────────────────────────────────────────────────

class TestLoadReportErrors:

    def test_nonexistent_path_raises(self, tmp_path):
        with pytest.raises(ReportError, match="Path no encontrado"):
            load_report(tmp_path / "does_not_exist")

    def test_missing_project_config_raises(self, project_root):
        (project_root / "10_Admin" / "project_config.json").unlink()
        with pytest.raises(ReportError, match="project_config.json"):
            load_report(project_root)

    def test_missing_checklist_raises(self, project_root):
        (project_root / "10_Admin" / "delivery_checklist.csv").unlink()
        with pytest.raises(ReportError, match="delivery_checklist.csv"):
            load_report(project_root)


# ── Status counting ────────────────────────────────────────────────────────────

class TestStatusCounts:

    def test_all_not_started(self, project_root):
        data = load_report(project_root)
        assert data["status_counts"].get("Not started", 0) == 4

    def test_mixed_statuses(self, project_root):
        _set_statuses(project_root, ["Delivered", "Approved", "In edit", "Not started"])
        data = load_report(project_root)
        assert data["status_counts"]["Delivered"] == 1
        assert data["status_counts"]["Approved"] == 1
        assert data["status_counts"]["In edit"] == 1
        assert data["status_counts"]["Not started"] == 1

    def test_all_delivered(self, project_root):
        _set_statuses(project_root, ["Delivered", "Delivered", "Delivered", "Delivered"])
        data = load_report(project_root)
        assert data["status_counts"]["Delivered"] == 4


# ── Progress calculations ──────────────────────────────────────────────────────

class TestProgressCalculations:

    def test_pct_delivered_zero_when_none_delivered(self, project_root):
        data = load_report(project_root)
        assert data["pct_delivered"] == 0.0

    def test_pct_delivered_100_when_all_delivered(self, project_root):
        _set_statuses(project_root, ["Delivered"] * 4)
        data = load_report(project_root)
        assert data["pct_delivered"] == 100.0

    def test_pct_delivered_partial(self, project_root):
        _set_statuses(project_root, ["Delivered", "Delivered", "Not started", "Not started"])
        data = load_report(project_root)
        assert data["pct_delivered"] == 50.0

    def test_pct_advanced_includes_approved_exported_delivered(self, project_root):
        _set_statuses(project_root, ["Approved", "Exported", "Delivered", "Not started"])
        data = load_report(project_root)
        assert data["pct_advanced"] == 75.0

    def test_pct_advanced_zero_when_all_not_started(self, project_root):
        data = load_report(project_root)
        assert data["pct_advanced"] == 0.0


# ── Next action suggestions ────────────────────────────────────────────────────

class TestNextAction:

    def test_all_delivered_suggests_archive(self, project_root):
        _set_statuses(project_root, ["Delivered"] * 4)
        data = load_report(project_root)
        assert "archivar" in data["next_action"].lower()

    def test_all_not_started_suggests_start(self, project_root):
        data = load_report(project_root)
        assert "inicia" in data["next_action"].lower()

    def test_in_progress_suggests_continue(self, project_root):
        _set_statuses(project_root, ["In edit", "In edit", "Not started", "Not started"])
        data = load_report(project_root)
        assert "edición" in data["next_action"].lower() or "activa" in data["next_action"].lower()

    def test_high_advanced_pct_suggests_closing(self, project_root):
        _set_statuses(project_root, ["Delivered", "Delivered", "Delivered", "Approved"])
        data = load_report(project_root)
        assert "cierre" in data["next_action"].lower() or "completo" in data["next_action"].lower()


# ── CLI output ─────────────────────────────────────────────────────────────────

class TestCliOutput:

    def test_report_shows_client(self, project_root):
        runner = CliRunner()
        result = runner.invoke(main, ["report", str(project_root)])
        assert result.exit_code == 0
        assert "TestCorp" in result.output

    def test_report_shows_project(self, project_root):
        runner = CliRunner()
        result = runner.invoke(main, ["report", str(project_root)])
        assert "CampaignQ1" in result.output

    def test_report_shows_total(self, project_root):
        runner = CliRunner()
        result = runner.invoke(main, ["report", str(project_root)])
        assert "4" in result.output

    def test_report_shows_platforms(self, project_root):
        runner = CliRunner()
        result = runner.invoke(main, ["report", str(project_root)])
        assert "Instagram Reels" in result.output or "TikTok" in result.output

    def test_report_shows_next_action(self, project_root):
        runner = CliRunner()
        result = runner.invoke(main, ["report", str(project_root)])
        assert "Próxima acción" in result.output

    def test_report_nonexistent_path_exits_1(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["report", str(tmp_path / "nope")])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_report_missing_config_exits_1(self, project_root):
        (project_root / "10_Admin" / "project_config.json").unlink()
        runner = CliRunner()
        result = runner.invoke(main, ["report", str(project_root)])
        assert result.exit_code == 1
        assert "project_config.json" in result.output

    def test_report_missing_checklist_exits_1(self, project_root):
        (project_root / "10_Admin" / "delivery_checklist.csv").unlink()
        runner = CliRunner()
        result = runner.invoke(main, ["report", str(project_root)])
        assert result.exit_code == 1
        assert "delivery_checklist.csv" in result.output


# ── Fuzzy path resolution ─────────────────────────────────────────────────────

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


class TestFuzzyPathReport:
    """load_report and CLI report both resolve human-friendly paths."""

    def test_sanitized_folder_name_is_expected(self, acme_root):
        assert acme_root.name == "ACMESTUDIO_PODCASTLEADERSHIP_20260610"

    def test_load_report_human_path_mixed_case(self, acme_root):
        human = acme_root.parent / "AcmeStudio_PodcastLeadership_2026-06-10"
        data = load_report(human)
        assert data["client"] == "AcmeStudio"
        assert data["project"] == "PodcastLeadership"

    def test_load_report_human_path_resolves_to_correct_folder(self, acme_root):
        human = acme_root.parent / "AcmeStudio_PodcastLeadership_2026-06-10"
        data = load_report(human)
        assert data["total"] == 4  # 2 clips × 2 platforms × 1 format

    def test_load_report_lowercase_path(self, acme_root):
        lower = acme_root.parent / "acmestudio_podcastleadership_2026-06-10"
        data = load_report(lower)
        assert data["client"] == "AcmeStudio"

    def test_load_report_hyphens_only_path(self, acme_root):
        hyphens = acme_root.parent / "AcmeStudio-PodcastLeadership-20260610"
        data = load_report(hyphens)
        assert data["client"] == "AcmeStudio"

    def test_cli_report_human_path_exit_0(self, acme_root):
        runner = CliRunner()
        human = str(acme_root.parent / "AcmeStudio_PodcastLeadership_2026-06-10")
        result = runner.invoke(main, ["report", human])
        assert result.exit_code == 0

    def test_cli_report_human_path_shows_client(self, acme_root):
        runner = CliRunner()
        human = str(acme_root.parent / "AcmeStudio_PodcastLeadership_2026-06-10")
        result = runner.invoke(main, ["report", human])
        assert "AcmeStudio" in result.output

    def test_cli_report_human_path_shows_delivery_date(self, acme_root):
        runner = CliRunner()
        human = str(acme_root.parent / "AcmeStudio_PodcastLeadership_2026-06-10")
        result = runner.invoke(main, ["report", human])
        assert "2026-06-10" in result.output
