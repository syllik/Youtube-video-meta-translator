import sys
import unittest
from contextlib import nullcontext
from unittest.mock import patch

from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog
from ui.source_selection import render_source_selection


class _FakeStreamlit:
    def __init__(self, selected_codes=None):
        self.selected_codes = selected_codes
        self.expanders = []
        self.captions = []
        self.infos = []
        self.multiselect_calls = []

    def expander(self, label, **kwargs):
        self.expanders.append((label, kwargs))
        return nullcontext()

    def caption(self, message):
        self.captions.append(message)

    def info(self, message):
        self.infos.append(message)

    def error(self, _message):
        raise AssertionError("unexpected source-selection error")

    def multiselect(self, label, options, **kwargs):
        self.multiselect_calls.append((label, tuple(options), kwargs))
        return self.selected_codes if self.selected_codes is not None else kwargs["default"]


class SourceSelectionTests(unittest.TestCase):
    def setUp(self):
        self.video = {
            "id": "video-1",
            "snippet": {
                "defaultLanguage": "en",
                "title": "Title",
                "description": "Description",
            },
            "localizations": {
                "de": {"title": "Titel", "description": "Beschreibung"},
                "fr": {"title": "Titre", "description": "Description"},
            },
        }
        self.catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-29T00:00:00Z",
            hl="en",
            languages=(
                YouTubeLanguage("en", "en", "Английский", "English"),
                YouTubeLanguage("de", "de", "Немецкий", "German"),
                YouTubeLanguage("fr", "fr", "Французский", "French"),
            ),
        )

    def test_primary_source_is_displayed_separately_from_reference_options(self):
        fake = _FakeStreamlit(selected_codes=("de",))

        with patch.dict(sys.modules, {"streamlit": fake}):
            selected = render_source_selection({}, self.video, self.catalog)

        self.assertEqual(selected, ("en", "de"))
        self.assertEqual(fake.multiselect_calls[0][0], "Optional reference translations")
        self.assertEqual(fake.multiselect_calls[0][1], ("de", "fr"))
        self.assertNotIn("en", fake.multiselect_calls[0][1])
        self.assertTrue(any("Primary source: en — English" in value for value in fake.captions))

    def test_empty_references_keep_primary_and_show_guidance(self):
        fake = _FakeStreamlit(selected_codes=())
        video = {**self.video, "localizations": {}}

        with patch.dict(sys.modules, {"streamlit": fake}):
            selected = render_source_selection({}, video, self.catalog)

        self.assertEqual(selected, ("en",))
        self.assertEqual(fake.multiselect_calls, [])
        self.assertIn("No reference translations available.", fake.infos)

    def test_clearing_references_cannot_remove_primary(self):
        state = {
            "common.source_video_id": "video-1",
            "common.selected_source_codes": ("en", "de"),
        }
        fake = _FakeStreamlit(selected_codes=())

        with patch.dict(sys.modules, {"streamlit": fake}):
            selected = render_source_selection(state, self.video, self.catalog)

        self.assertEqual(selected, ("en",))


if __name__ == "__main__":
    unittest.main()
