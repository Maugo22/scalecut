"""Project templates and platform-format rules."""

# Platform → valid formats
PLATFORM_FORMATS = {
    "Instagram Reels": ["9x16"],
    "TikTok":          ["9x16"],
    "YouTube Shorts":  ["9x16"],
    "Stories":         ["9x16"],
    "LinkedIn":        ["1x1", "16x9"],
    "YouTube":         ["16x9"],
    "Facebook":        ["1x1", "16x9"],
    "Ads":             ["9x16", "1x1", "16x9"],
    "Website":         ["16x9"],
}

ALL_PLATFORMS = list(PLATFORM_FORMATS.keys())
ALL_FORMATS   = ["9x16", "1x1", "16x9"]

STATUSES = [
    "Not started",
    "In edit",
    "Ready for review",
    "Changes requested",
    "Approved",
    "Exported",
    "Delivered",
]

PROJECT_TEMPLATES = {
    "Podcast Repurposing": {
        "description": "Repurpose podcast episodes into short-form clips with captions.",
        "suggested_platforms": ["Instagram Reels", "TikTok", "YouTube Shorts", "LinkedIn"],
        "suggested_formats": ["9x16", "1x1"],
        "notes": "Workflow: raw podcast → select highlights → add captions → format per platform.",
        "typical_clips": 5,
    },
    "Reels/Shorts para marca personal": {
        "description": "Short-form content for personal brand growth.",
        "suggested_platforms": ["Instagram Reels", "TikTok", "YouTube Shorts"],
        "suggested_formats": ["9x16"],
        "notes": "Hook in first 3 seconds. Captions mandatory.",
        "typical_clips": 8,
    },
    "Campaña publicitaria": {
        "description": "Multi-platform paid ad campaign with multiple formats.",
        "suggested_platforms": ["Instagram Reels", "Facebook", "TikTok", "Ads", "YouTube"],
        "suggested_formats": ["9x16", "1x1", "16x9"],
        "notes": "Deliver all 3 formats per clip. Versión A/B si aplica.",
        "typical_clips": 4,
    },
    "Curso online": {
        "description": "Educational long-form + promo clips for online courses.",
        "suggested_platforms": ["YouTube", "Website"],
        "suggested_formats": ["16x9"],
        "notes": "Intro, capítulos, outro. Subtítulos requeridos.",
        "typical_clips": 10,
    },
    "Testimoniales": {
        "description": "Customer testimonial clips for social and web.",
        "suggested_platforms": ["Instagram Reels", "LinkedIn", "Website", "Ads"],
        "suggested_formats": ["9x16", "1x1", "16x9"],
        "notes": "Versión corta (≤60s) y versión larga (≤3min).",
        "typical_clips": 6,
    },
    "UGC Content": {
        "description": "User-generated content for organic and paid distribution.",
        "suggested_platforms": ["TikTok", "Instagram Reels", "Ads"],
        "suggested_formats": ["9x16"],
        "notes": "Formato nativo. Sin tratamiento de color excesivo.",
        "typical_clips": 6,
    },
    "YouTube long-form + Shorts": {
        "description": "Long YouTube video plus derived Shorts from key moments.",
        "suggested_platforms": ["YouTube", "YouTube Shorts"],
        "suggested_formats": ["16x9", "9x16"],
        "notes": "Shorts se derivan del long-form. Mínimo 3 Shorts por video.",
        "typical_clips": 4,
    },
}
