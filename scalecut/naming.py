"""File naming convention logic."""

import re
from typing import List
from scalecut.models import ProjectConfig


def sanitize(text: str) -> str:
    """Remove special chars, collapse spaces to underscores, uppercase."""
    text = text.strip()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^\w_-]", "", text)
    return text.upper()


def platform_slug(platform: str) -> str:
    """Short slug for platform in file names."""
    mapping = {
        "Instagram Reels": "INSTA",
        "TikTok":          "TIKTOK",
        "YouTube Shorts":  "YTSHORTS",
        "Stories":         "STORIES",
        "LinkedIn":        "LINKEDIN",
        "YouTube":         "YT",
        "Facebook":        "FB",
        "Ads":             "ADS",
        "Website":         "WEB",
    }
    return mapping.get(platform, sanitize(platform))


def format_slug(fmt: str) -> str:
    """Convert format ratio to filename-safe string."""
    return fmt.replace("x", "x").replace(":", "x")


def build_filename(
    config: ProjectConfig,
    clip_number: int,
    platform: str,
    fmt: str,
    extension: str = "mp4",
) -> str:
    """
    Pattern: Cliente_Proyecto_ClipNN_Plataforma_Formato_Fecha_VNN.ext
    Example:  NIKE_VERANO24_Clip01_INSTA_9x16_20241215_V01.mp4
    """
    client  = sanitize(config.client)
    project = sanitize(config.project)
    clip    = f"Clip{clip_number:02d}"
    plat    = platform_slug(platform)
    ratio   = format_slug(fmt)
    date    = config.delivery_date.replace("-", "")
    version = f"V{config.version.zfill(2)}"

    return f"{client}_{project}_{clip}_{plat}_{ratio}_{date}_{version}.{extension}"


def generate_all_filenames(config: ProjectConfig) -> List[dict]:
    """Return every deliverable as a dict with naming metadata."""
    deliverables = []
    for clip_n in range(1, config.num_clips + 1):
        for platform in config.platforms:
            for fmt in config.formats:
                deliverables.append(
                    {
                        "clip":     f"Clip{clip_n:02d}",
                        "platform": platform,
                        "format":   fmt,
                        "status":   config.initial_status,
                        "filename": build_filename(config, clip_n, platform, fmt),
                        "language": config.language,
                        "version":  f"V{config.version.zfill(2)}",
                    }
                )
    return deliverables
