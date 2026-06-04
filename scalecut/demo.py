"""Reusable demo project configuration for tests and UI."""

from datetime import date

DEMO_PROJECT = {
    "client":         "Acme Studio",
    "project":        "Podcast Leadership",
    "project_type":   "Podcast Repurposing",
    "delivery_date":  "2024-12-20",
    "num_clips":      5,
    "platforms":      ["Instagram Reels", "TikTok", "LinkedIn", "YouTube Shorts"],
    "formats":        ["9x16", "1x1"],
    "version":        "01",
    "language":       "ES",
    "initial_status": "Not started",
}


def make_demo_config(output_path: str = "."):
    """Return a ProjectConfig built from DEMO_PROJECT."""
    from scalecut.models import ProjectConfig
    return ProjectConfig(**{**DEMO_PROJECT, "output_path": output_path})
