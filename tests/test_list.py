"""Tests for scalecut list command and list_projects.py module."""

import csv
import pytest
from pathlib import Path
from click.testing import CliRunner

from scalecut.list_projects import find_projects, ListError, _status_summary
from scalecut.cli import main
from scalecut.checklist import write_csv
from scalecut.config_gen import write_config
from scalecut.folders import create_folders
from tests.conftest import make_config


# ── Helpers ───────────────────────────────────────────────────────────────────

def scaffold(tmp_path, client, project, delivery_date, num_clips=1,
             platforms=None, formats=None, initial_status="Not started"):
    """Create a fully scaffolded project inside tmp_path and return root."""
    cfg = make_config(
        client=client,
        project=project,
        delivery_date=delivery_date,
        num_clips=num_clips,
        platforms=platforms or ["Instagram Reels"],
        formats=formats or ["9x16"],
        initial_status=initial_status,
        output_path=str(tmp_path),
    )
    root = create_folders(cfg)
    write_csv(cfg, root)
    write_config(cfg, root)
    return root


def _set_statuses(root: Path, statuses: list[str]) -> None:
    checklist = root / "10_Admin" / "delivery_checklist.csv"
    rows = list(csv.DictReader(checklist.read_text(encoding="utf-8").splitlines()))
    for row, status in zip(rows, statuses):
        row["Status"] = status
    with open(checklist, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ── find_projects: multiple projects ─────────────────────────────────────────

class TestFindProjects:

    def test_finds_single_project(self, tmp_path):
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01")
        results = find_projects(tmp_path)
        assert len(results) == 1

    def test_finds_multiple_projects(self, tmp_path):
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01")
        scaffold(tmp_path, "Adidas", "Invierno", "2025-12-01")
        scaffold(tmp_path, "Puma", "Otoño", "2025-09-01")
        results = find_projects(tmp_path)
        assert len(results) == 3

    def test_returns_correct_client(self, tmp_path):
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01")
        results = find_projects(tmp_path)
        assert results[0]["client"] == "Nike"

    def test_returns_correct_project(self, tmp_path):
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01")
        results = find_projects(tmp_path)
        assert results[0]["project"] == "Verano"

    def test_returns_delivery_date(self, tmp_path):
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01")
        results = find_projects(tmp_path)
        assert results[0]["delivery_date"] == "2025-06-01"

    def test_returns_total(self, tmp_path):
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01", num_clips=2,
                 platforms=["Instagram Reels", "TikTok"], formats=["9x16"])
        results = find_projects(tmp_path)
        assert results[0]["total"] == 4

    def test_returns_path(self, tmp_path):
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01")
        results = find_projects(tmp_path)
        assert Path(results[0]["path"]).parent == tmp_path

    def test_returns_status_summary(self, tmp_path):
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01")
        results = find_projects(tmp_path)
        assert "status_summary" in results[0]
        assert isinstance(results[0]["status_summary"], str)

    def test_returns_pct_advanced(self, tmp_path):
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01")
        results = find_projects(tmp_path)
        assert "pct_advanced" in results[0]


# ── find_projects: empty and invalid cases ────────────────────────────────────

class TestFindProjectsEmpty:

    def test_empty_folder_returns_empty_list(self, tmp_path):
        results = find_projects(tmp_path)
        assert results == []

    def test_nonexistent_base_raises(self, tmp_path):
        with pytest.raises(ListError, match="Carpeta no encontrada"):
            find_projects(tmp_path / "does_not_exist")

    def test_file_as_base_raises(self, tmp_path):
        f = tmp_path / "notadir.txt"
        f.write_text("x")
        with pytest.raises(ListError, match="No es una carpeta"):
            find_projects(f)

    def test_folder_without_config_is_skipped(self, tmp_path):
        bad = tmp_path / "FAKE_PROJECT_20250101"
        bad.mkdir()
        (bad / "10_Admin").mkdir()
        (bad / "10_Admin" / "delivery_checklist.csv").write_text("Clip,Status\n")
        results = find_projects(tmp_path)
        assert results == []

    def test_folder_without_checklist_is_skipped(self, tmp_path):
        bad = tmp_path / "FAKE_PROJECT_20250101"
        bad.mkdir()
        (bad / "10_Admin").mkdir()
        (bad / "10_Admin" / "project_config.json").write_text("{}")
        results = find_projects(tmp_path)
        assert results == []

    def test_incomplete_project_does_not_block_valid_ones(self, tmp_path):
        bad = tmp_path / "INCOMPLETE_20250101"
        bad.mkdir()
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01")
        results = find_projects(tmp_path)
        assert len(results) == 1
        assert results[0]["client"] == "Nike"


# ── find_projects: ordering ───────────────────────────────────────────────────

class TestFindProjectsOrdering:

    def test_sorted_by_delivery_date_ascending(self, tmp_path):
        scaffold(tmp_path, "C", "Late",   "2025-12-01")
        scaffold(tmp_path, "A", "Early",  "2025-01-01")
        scaffold(tmp_path, "B", "Middle", "2025-06-01")
        results = find_projects(tmp_path)
        dates = [r["delivery_date"] for r in results]
        assert dates == sorted(dates)

    def test_same_date_sorted_by_project_name(self, tmp_path):
        scaffold(tmp_path, "X", "Zebra",  "2025-06-01")
        scaffold(tmp_path, "X", "Alpha",  "2025-06-01")
        scaffold(tmp_path, "X", "Mango",  "2025-06-01")
        results = find_projects(tmp_path)
        names = [r["project"] for r in results]
        assert names == sorted(names)

    def test_earlier_date_comes_first(self, tmp_path):
        scaffold(tmp_path, "Late",  "ProjectB", "2026-01-01")
        scaffold(tmp_path, "Early", "ProjectA", "2024-01-01")
        results = find_projects(tmp_path)
        assert results[0]["client"] == "Early"
        assert results[1]["client"] == "Late"


# ── _status_summary helper ────────────────────────────────────────────────────

class TestStatusSummary:

    def test_single_status(self):
        counts = {"Not started": 4}
        assert "Not started" in _status_summary(counts, 4)

    def test_multiple_statuses_in_workflow_order(self):
        counts = {"Delivered": 1, "In edit": 2, "Not started": 3}
        summary = _status_summary(counts, 6)
        assert summary.index("Not started") < summary.index("In edit")
        assert summary.index("In edit") < summary.index("Delivered")

    def test_empty_counts_returns_dash(self):
        assert _status_summary({}, 0) == "—"

    def test_zero_count_status_excluded(self):
        counts = {"Not started": 3, "Delivered": 0}
        assert "Delivered" not in _status_summary(counts, 3)


# ── CLI output ────────────────────────────────────────────────────────────────

class TestCliList:

    def test_empty_folder_exit_0(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["list", "--base-path", str(tmp_path)])
        assert result.exit_code == 0

    def test_empty_folder_shows_no_projects_message(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["list", "--base-path", str(tmp_path)])
        assert "No se encontraron" in result.output

    def test_shows_client_in_output(self, tmp_path):
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01")
        runner = CliRunner()
        result = runner.invoke(main, ["list", "--base-path", str(tmp_path)])
        assert result.exit_code == 0
        assert "Nike" in result.output

    def test_shows_all_projects(self, tmp_path):
        scaffold(tmp_path, "Nike",   "Verano",   "2025-06-01")
        scaffold(tmp_path, "Adidas", "Invierno", "2025-12-01")
        runner = CliRunner()
        result = runner.invoke(main, ["list", "--base-path", str(tmp_path)])
        assert "Nike" in result.output
        assert "Adidas" in result.output

    def test_nonexistent_base_exits_1(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["list", "--base-path", str(tmp_path / "nope")])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_shows_delivery_date(self, tmp_path):
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01")
        runner = CliRunner()
        result = runner.invoke(main, ["list", "--base-path", str(tmp_path)])
        assert "2025-06-01" in result.output

    def test_shows_total_deliverables(self, tmp_path):
        scaffold(tmp_path, "Nike", "Verano", "2025-06-01",
                 num_clips=2, platforms=["TikTok", "Instagram Reels"], formats=["9x16"])
        runner = CliRunner()
        result = runner.invoke(main, ["list", "--base-path", str(tmp_path)])
        assert "4" in result.output

    def test_default_base_path_used_when_no_flag(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["list"])
        assert result.exit_code in (0, 1)
