import unittest
import sys
from contextlib import nullcontext
from unittest.mock import patch

from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog
from state.translation_state import (
    init_translation_state,
    sync_translation_target_selection,
)
from ui.target_selection import render_target_selection


class _FakeStreamlit:
    def __init__(self, selected_codes=None):
        self.selected_codes = selected_codes
        self.expanders = []
        self.multiselect_calls = []
        self.infos = []
        self.errors = []

    def expander(self, label, **kwargs):
        self.expanders.append((label, kwargs))
        return nullcontext()

    def multiselect(self, label, options, **kwargs):
        self.multiselect_calls.append((label, tuple(options), kwargs))
        return self.selected_codes if self.selected_codes is not None else kwargs["default"]

    def info(self, message):
        self.infos.append(message)

    def error(self, message):
        self.errors.append(message)


class TargetSelectionTests(unittest.TestCase):
    def setUp(self):
        self.video = {
            "id": "video-1",
            "snippet": {
                "defaultLanguage": "en",
                "title": "Title",
                "description": "Description",
            },
            "localizations": {"de": {"title": "Titel", "description": "Beschreibung"}},
        }
        self.catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-29T00:00:00Z",
            hl="en",
            languages=tuple(
                YouTubeLanguage(code, code, code, code)
                for code in ("en", "de", "es", "fr")
            ),
        )

    def test_target_selector_defaults_to_all_missing_and_excludes_sources(self):
        fake = _FakeStreamlit()

        with patch.dict(sys.modules, {"streamlit": fake}):
            selected = render_target_selection(
                {}, self.video, self.catalog, source_codes=("en", "es")
            )

        self.assertEqual(selected, ("fr",))
        self.assertEqual(fake.multiselect_calls[0][0], "Target languages")
        self.assertEqual(fake.multiselect_calls[0][1], ("fr",))
        self.assertEqual(fake.multiselect_calls[0][2]["default"], ("fr",))

    def test_primary_target_selector_is_not_capped_at_ten(self):
        languages = tuple(
            [YouTubeLanguage("en", "en", "English")]
            + [
                YouTubeLanguage("code-{}".format(index), "code-{}".format(index), "Language")
                for index in range(12)
            ]
        )
        catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-29T00:00:00Z",
            hl="en",
            languages=languages,
        )
        video = {
            "id": "video-many",
            "snippet": {
                "defaultLanguage": "en",
                "title": "Title",
                "description": "Description",
            },
            "localizations": {},
        }
        fake = _FakeStreamlit()

        with patch.dict(sys.modules, {"streamlit": fake}):
            selected = render_target_selection({}, video, catalog, source_codes=("en",))

        self.assertEqual(len(selected), 12)
        self.assertEqual(len(fake.multiselect_calls[0][1]), 12)

    def test_target_selection_is_cleared_and_recomputed_for_another_video(self):
        state = init_translation_state({})
        progress_one = type("Progress", (), {
            "missing": (
                YouTubeLanguage("es", "es", "Spanish"),
                YouTubeLanguage("fr", "fr", "French"),
            )
        })()
        progress_two = type("Progress", (), {
            "missing": (YouTubeLanguage("de", "de", "German"),)
        })()

        self.assertEqual(
            sync_translation_target_selection(state, "video-1", progress_one),
            ("es", "fr"),
        )
        state["selected_target_codes"] = ("fr",)

        self.assertEqual(
            sync_translation_target_selection(state, "video-2", progress_two),
            ("de",),
        )
        self.assertEqual(state["target_video_id"], "video-2")

    def test_source_change_removes_source_from_existing_targets(self):
        state = init_translation_state({})
        progress_before = type("Progress", (), {
            "missing": (
                YouTubeLanguage("es", "es", "Spanish"),
                YouTubeLanguage("fr", "fr", "French"),
            )
        })()
        progress_after = type("Progress", (), {
            "missing": (YouTubeLanguage("fr", "fr", "French"),)
        })()

        sync_translation_target_selection(state, "video-1", progress_before)
        state["selected_target_codes"] = ("es", "fr")

        selected = sync_translation_target_selection(
            state, "video-1", progress_after
        )

        self.assertEqual(selected, ("fr",))
