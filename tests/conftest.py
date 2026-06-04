"""Shared fixtures for ScaleCut tests."""
import pytest
from scalecut.models import ProjectConfig


def make_config(**overrides) -> ProjectConfig:
    """Return a minimal, valid ProjectConfig, optionally overriding any field."""
    defaults = dict(
        client="Nike",
        project="Verano24",
        project_type="Campaña publicitaria",
        delivery_date="2024-12-15",
        num_clips=2,
        platforms=["Instagram Reels", "TikTok"],
        formats=["9x16"],
        version="01",
        language="ES",
        initial_status="Not started",
        output_path="/tmp",
    )
    defaults.update(overrides)
    return ProjectConfig(**defaults)


@pytest.fixture
def base_config() -> ProjectConfig:
    return make_config()
