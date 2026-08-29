import unittest

from ui.llm_package import apply_generated_localizations, apply_llm_upload


class TranslationDraftHandoffTests(unittest.TestCase):
    def test_valid_upload_becomes_internal_draft_without_editable_json(self):
        state = {
            "draft": {"fr": {"title": "FR", "description": "FR"}}
        }

        result = apply_llm_upload(
            state,
            b'{"DE":{"title":"Gr\\u00fc\\u00dfe","description":"Text"}}',
            ("de",),
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(
            state["draft"],
            {
                "fr": {"title": "FR", "description": "FR"},
                "de": {"title": "Gr\u00fc\u00dfe", "description": "Text"},
            },
        )
        self.assertNotIn("raw_json", state)

    def test_invalid_upload_does_not_replace_the_current_valid_draft(self):
        state = {
            "draft": {"de": {"title": "DE", "description": "DE"}}
        }

        result = apply_llm_upload(state, b"{", ("fr",))

        self.assertFalse(result.is_valid)
        self.assertEqual(
            state["draft"], {"de": {"title": "DE", "description": "DE"}}
        )

    def test_generated_document_becomes_internal_draft(self):
        state = {
            "draft": {"de": {"title": "Old", "description": "Old"}}
        }

        result = apply_generated_localizations(
            state,
            {"DE": {"title": "New", "description": "New"}},
            ("de",),
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(
            state["draft"], {"de": {"title": "New", "description": "New"}}
        )


if __name__ == "__main__":
    unittest.main()
