"""Tests for scalecut.naming — sanitize, build_filename, generate_all_filenames."""
import re
import pytest
from scalecut.naming import sanitize, build_filename, generate_all_filenames
from tests.conftest import make_config

# ── Filename pattern used across multiple assertions ──────────────────────────
FILENAME_RE = re.compile(
    r"^[A-Z0-9_]+"        # client
    r"_[A-Z0-9_]+"        # project
    r"_Clip\d{2}"         # clip number, always 2 digits
    r"_[A-Z0-9]+"         # platform slug
    r"_(?:9x16|1x1|16x9)" # format
    r"_\d{8}"             # date YYYYMMDD
    r"_V\d{2}"            # version
    r"\.mp4$"
)


# =============================================================================
# sanitize
# =============================================================================

class TestSanitize:

    @pytest.mark.parametrize("text, expected", [
        # basic cases
        ("nike",              "NIKE"),
        ("ALREADY_UPPER",     "ALREADY_UPPER"),
        ("Clip01",            "CLIP01"),
        # spaces → underscores
        ("acme studio",       "ACME_STUDIO"),
        ("multiple   spaces", "MULTIPLE_SPACES"),
        # leading / trailing whitespace stripped
        ("  leading",         "LEADING"),
        ("trailing  ",        "TRAILING"),
        ("  both  ",          "BOTH"),
        # hyphens preserved, special chars removed
        ("verano-2024",       "VERANO-2024"),
        ("hello@world.com",   "HELLOWORLDCOM"),
        ("test!name#here",    "TESTNAMEHERE"),
        # tabs and newlines treated as whitespace
        ("hello\tworld",      "HELLO_WORLD"),
        ("line\nnewline",     "LINE_NEWLINE"),
        # empty string
        ("",                  ""),
    ])
    def test_output(self, text, expected):
        assert sanitize(text) == expected

    def test_result_is_uppercase(self):
        assert sanitize("mixed Case Input").isupper() or sanitize("mixed Case Input") == ""

    def test_no_spaces_in_result(self):
        assert " " not in sanitize("spaces in string")

    def test_no_special_chars_in_result(self):
        result = sanitize("hello@world! foo#bar")
        assert re.match(r"^[\w_-]*$", result)

    def test_idempotent(self):
        """Sanitizing an already-sanitized string produces the same result."""
        once  = sanitize("Acme Studio 2024")
        twice = sanitize(once)
        assert once == twice


# =============================================================================
# build_filename
# =============================================================================

class TestBuildFilename:

    def test_exact_output(self):
        config = make_config(
            client="Nike",
            project="Verano24",
            delivery_date="2024-12-15",
            version="01",
        )
        result = build_filename(config, 1, "Instagram Reels", "9x16")
        assert result == "NIKE_VERANO24_Clip01_INSTA_9x16_20241215_V01.mp4"

    def test_matches_naming_pattern(self):
        config = make_config()
        result = build_filename(config, 1, "Instagram Reels", "9x16")
        assert FILENAME_RE.match(result), f"Does not match convention: {result}"

    # ── Clip number padding ───────────────────────────────────────────────────

    @pytest.mark.parametrize("clip_n, expected_token", [
        (1,  "Clip01"),
        (9,  "Clip09"),
        (10, "Clip10"),
        (99, "Clip99"),
    ])
    def test_clip_number_padding(self, clip_n, expected_token):
        config = make_config()
        result = build_filename(config, clip_n, "TikTok", "9x16")
        assert expected_token in result

    # ── Platform slug mapping ─────────────────────────────────────────────────

    @pytest.mark.parametrize("platform, expected_slug", [
        ("Instagram Reels", "INSTA"),
        ("TikTok",          "TIKTOK"),
        ("YouTube Shorts",  "YTSHORTS"),
        ("Stories",         "STORIES"),
        ("LinkedIn",        "LINKEDIN"),
        ("YouTube",         "YT"),
        ("Facebook",        "FB"),
        ("Ads",             "ADS"),
        ("Website",         "WEB"),
    ])
    def test_platform_slug(self, platform, expected_slug):
        config = make_config(platforms=[platform])
        result = build_filename(config, 1, platform, "9x16")
        # slug must appear between underscores to avoid false substring matches
        assert f"_{expected_slug}_" in result

    def test_unknown_platform_falls_back_to_sanitize(self):
        config = make_config()
        result = build_filename(config, 1, "My Custom Platform", "9x16")
        assert "_MY_CUSTOM_PLATFORM_" in result

    # ── Date formatting ───────────────────────────────────────────────────────

    @pytest.mark.parametrize("raw_date, expected_token", [
        ("2024-12-15", "20241215"),
        ("2025-01-01", "20250101"),
        ("2030-06-30", "20300630"),
    ])
    def test_date_stripped_of_hyphens(self, raw_date, expected_token):
        config = make_config(delivery_date=raw_date)
        result = build_filename(config, 1, "TikTok", "9x16")
        assert expected_token in result

    # ── Version formatting ────────────────────────────────────────────────────

    @pytest.mark.parametrize("version, expected_token", [
        ("01", "_V01."),
        ("1",  "_V01."),   # single digit → zero-padded
        ("03", "_V03."),
        ("10", "_V10."),
    ])
    def test_version_format(self, version, expected_token):
        config = make_config(version=version)
        result = build_filename(config, 1, "TikTok", "9x16")
        assert expected_token in result

    # ── Format token ──────────────────────────────────────────────────────────

    @pytest.mark.parametrize("fmt", ["9x16", "1x1", "16x9"])
    def test_format_token_present(self, fmt):
        config = make_config(formats=[fmt])
        result = build_filename(config, 1, "LinkedIn", fmt)
        assert f"_{fmt}_" in result

    # ── Extension ─────────────────────────────────────────────────────────────

    def test_default_extension_is_mp4(self):
        config = make_config()
        assert build_filename(config, 1, "TikTok", "9x16").endswith(".mp4")

    @pytest.mark.parametrize("ext", ["mov", "mp4", "mxf"])
    def test_custom_extension(self, ext):
        config = make_config()
        result = build_filename(config, 1, "TikTok", "9x16", extension=ext)
        assert result.endswith(f".{ext}")

    # ── Client / project sanitization in filename ─────────────────────────────

    def test_client_spaces_become_underscores(self):
        config = make_config(client="Acme Studio")
        result = build_filename(config, 1, "TikTok", "9x16")
        assert result.startswith("ACME_STUDIO_")

    def test_project_special_chars_removed(self):
        config = make_config(project="Q4 Launch!")
        result = build_filename(config, 1, "TikTok", "9x16")
        assert "_Q4_LAUNCH_" in result


# =============================================================================
# generate_all_filenames
# =============================================================================

class TestGenerateAllFilenames:

    # ── Total count ───────────────────────────────────────────────────────────

    @pytest.mark.parametrize("clips, n_platforms, n_formats", [
        (1, 1, 1),
        (2, 2, 1),
        (4, 4, 3),
        (10, 3, 2),
    ])
    def test_count_equals_clips_times_platforms_times_formats(
        self, clips, n_platforms, n_formats
    ):
        platforms = ["Instagram Reels", "TikTok", "LinkedIn", "YouTube"][:n_platforms]
        formats   = ["9x16", "1x1", "16x9"][:n_formats]
        config    = make_config(num_clips=clips, platforms=platforms, formats=formats)
        assert len(generate_all_filenames(config)) == clips * n_platforms * n_formats

    # ── Dict structure ────────────────────────────────────────────────────────

    def test_each_item_has_required_keys(self):
        config   = make_config()
        required = {"clip", "platform", "format", "status", "filename", "language", "version"}
        for item in generate_all_filenames(config):
            assert set(item.keys()) == required

    # ── Coverage: clips, platforms, formats all appear ────────────────────────

    def test_all_clips_represented(self):
        config      = make_config(num_clips=4)
        clips_found = {d["clip"] for d in generate_all_filenames(config)}
        assert clips_found == {"Clip01", "Clip02", "Clip03", "Clip04"}

    def test_clip_labels_zero_padded(self):
        config = make_config(num_clips=1)
        assert generate_all_filenames(config)[0]["clip"] == "Clip01"

    def test_all_platforms_represented(self):
        platforms = ["Instagram Reels", "TikTok", "LinkedIn"]
        config    = make_config(platforms=platforms)
        found     = {d["platform"] for d in generate_all_filenames(config)}
        assert found == set(platforms)

    def test_all_formats_represented(self):
        formats = ["9x16", "1x1", "16x9"]
        config  = make_config(formats=formats)
        found   = {d["format"] for d in generate_all_filenames(config)}
        assert found == set(formats)

    # ── Metadata fields ───────────────────────────────────────────────────────

    def test_status_matches_initial_status(self):
        config = make_config(initial_status="In edit")
        assert all(d["status"] == "In edit" for d in generate_all_filenames(config))

    def test_language_propagated_to_all_items(self):
        config = make_config(language="EN")
        assert all(d["language"] == "EN" for d in generate_all_filenames(config))

    def test_version_label_format(self):
        config  = make_config(version="03")
        results = generate_all_filenames(config)
        assert all(d["version"] == "V03" for d in results)

    # ── Filename integrity ────────────────────────────────────────────────────

    def test_all_filenames_unique(self):
        config    = make_config(num_clips=3, platforms=["Instagram Reels", "TikTok"], formats=["9x16", "16x9"])
        filenames = [d["filename"] for d in generate_all_filenames(config)]
        assert len(filenames) == len(set(filenames))

    def test_all_filenames_match_naming_convention(self):
        config = make_config(num_clips=2, platforms=["Instagram Reels", "LinkedIn"], formats=["9x16", "16x9"])
        for item in generate_all_filenames(config):
            assert FILENAME_RE.match(item["filename"]), (
                f"Filename does not match convention: {item['filename']}"
            )

    def test_filename_matches_clip_platform_format_of_same_item(self):
        """The filename in each dict actually encodes that item's own clip/platform/format."""
        config = make_config(
            num_clips=1,
            platforms=["YouTube"],
            formats=["16x9"],
            delivery_date="2025-06-01",
            version="02",
        )
        item = generate_all_filenames(config)[0]
        assert "Clip01"   in item["filename"]
        assert "_YT_"     in item["filename"]
        assert "_16x9_"   in item["filename"]
        assert "20250601" in item["filename"]
        assert "_V02."    in item["filename"]

    # ── Loop ordering ─────────────────────────────────────────────────────────

    def test_outer_loop_is_clips(self):
        """First all combos for Clip01 appear before any Clip02 entry."""
        config  = make_config(num_clips=2, platforms=["Instagram Reels", "TikTok"], formats=["9x16"])
        results = generate_all_filenames(config)
        clip01_indices = [i for i, d in enumerate(results) if d["clip"] == "Clip01"]
        clip02_indices = [i for i, d in enumerate(results) if d["clip"] == "Clip02"]
        assert max(clip01_indices) < min(clip02_indices)

    def test_single_deliverable(self):
        config = make_config(num_clips=1, platforms=["YouTube"], formats=["16x9"])
        result = generate_all_filenames(config)
        assert len(result) == 1
        assert result[0]["clip"]     == "Clip01"
        assert result[0]["platform"] == "YouTube"
        assert result[0]["format"]   == "16x9"
