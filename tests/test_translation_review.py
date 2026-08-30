import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from state.translation_state import store_translation_preview
from ui.translation_review import _render_report, render_preview_publish


class _Block:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class _FakeStreamlit:
    def __init__(self):
        self.calls = []

    def expander(self, label, **kwargs):
        self.calls.append(("expander", label, kwargs))
        return _Block()

    def columns(self, spec):
        return tuple(_Block() for _ in spec)

    def button(self, label, **kwargs):
        self.calls.append(("button", label, kwargs))
        return label == "Publish changes"

    def spinner(self, message):
        return _Block()

    def info(self, message):
        self.calls.append(("info", message))

    def success(self, message):
        self.calls.append(("success", message))

    def warning(self, message):
        self.calls.append(("warning", message))

    def error(self, message):
        self.calls.append(("error", message))

    def caption(self, message):
        self.calls.append(("caption", message))

    def markdown(self, message):
        self.calls.append(("markdown", message))

    def code(self, message, **kwargs):
        self.calls.append(("code", message, kwargs))


class _PreviewStreamlit(_FakeStreamlit):
    def button(self, label, **kwargs):
        self.calls.append(("button", label, kwargs))
        return label == "Preview changes"


class TranslationReviewTests(unittest.TestCase):
    @staticmethod
    def _result(*, wrote, is_valid=True, has_changes=True, issues=()):
        return SimpleNamespace(
            video={"id": "video-1", "snippet": {}, "localizations": {}},
            plan=SimpleNamespace(
                is_valid=is_valid,
                has_changes=has_changes,
                diffs=(),
                issues=issues,
                preserved_language_codes=(),
            ),
            wrote=wrote,
        )

    def test_publish_forwards_the_preview_resource_to_stale_write_guard(self):
        streamlit = _FakeStreamlit()
        state = {
            "bound_video_id": "video-1",
            "draft": {"de": {"title": "New", "description": "New"}},
            "operation_status": "idle",
        }
        preview = SimpleNamespace(
            video={"id": "video-1", "snippet": {}, "localizations": {}},
            plan=SimpleNamespace(
                is_valid=True,
                has_changes=True,
                diffs=(),
                issues=(),
                preserved_language_codes=(),
            ),
            wrote=False,
        )
        store_translation_preview(state, preview)
        service = Mock()
        service.publish.return_value = preview

        with patch.dict(sys.modules, {"streamlit": streamlit}):
            render_preview_publish(
                state,
                "video-1",
                service,
                ("de",),
            )

        service.publish.assert_called_once_with(
            "video-1",
            state["draft"],
            expected_video=preview.video,
        )

    def test_preview_forwards_fresh_video_to_cache_callback(self):
        streamlit = _PreviewStreamlit()
        state = {
            "bound_video_id": "video-1",
            "draft": {"de": {"title": "New", "description": "New"}},
            "operation_status": "idle",
        }
        fresh = self._result(wrote=False)
        service = Mock()
        service.preview.return_value = fresh
        on_video_refreshed = Mock()

        with patch.dict(sys.modules, {"streamlit": streamlit}):
            render_preview_publish(
                state,
                "video-1",
                service,
                ("de",),
                on_video_refreshed=on_video_refreshed,
            )

        on_video_refreshed.assert_called_once_with(fresh.video)

    def test_preview_report_labels_include_code_name_and_status(self):
        streamlit = _FakeStreamlit()
        result = SimpleNamespace(
            plan=SimpleNamespace(
                diffs=(
                    SimpleNamespace(
                        language_code="ru",
                        status="changed",
                        existing=None,
                        submitted=SimpleNamespace(title="Новый", description="Текст"),
                    ),
                ),
                preserved_language_codes=("de",),
            )
        )
        catalog = SimpleNamespace(
            languages=(
                SimpleNamespace(code="ru", english_name="Russian"),
                SimpleNamespace(code="de", english_name="German"),
            )
        )

        with patch.dict(sys.modules, {"streamlit": streamlit}):
            _render_report(result, catalog)

        self.assertTrue(
            any(
                call[0] == "expander"
                and call[1] == "ru — Russian — Changed"
                for call in streamlit.calls
            )
        )
        self.assertIn(
            "Preserved existing languages: de — German",
            [call[1] for call in streamlit.calls if call[0] == "caption"],
        )

    def test_successful_publish_is_the_only_success_outcome(self):
        streamlit = _FakeStreamlit()
        state = {
            "bound_video_id": "video-1",
            "draft": {"de": {"title": "New", "description": "New"}},
            "operation_status": "idle",
        }
        preview = self._result(wrote=False)
        store_translation_preview(state, preview)
        service = Mock()
        service.publish.return_value = self._result(wrote=True)
        on_published = Mock()

        with patch.dict(sys.modules, {"streamlit": streamlit}):
            render_preview_publish(
                state, "video-1", service, ("de",), on_published=on_published
            )

        self.assertTrue(any(call[0] == "success" for call in streamlit.calls))
        self.assertFalse(
            any(
                call[0] == "info" and "No localization changes" in call[1]
                for call in streamlit.calls
            )
        )
        self.assertFalse(any(call[0] == "error" for call in streamlit.calls))
        on_published.assert_called_once_with()

    def test_unchanged_publish_shows_only_the_no_change_outcome(self):
        streamlit = _FakeStreamlit()
        state = {
            "bound_video_id": "video-1",
            "draft": {"de": {"title": "New", "description": "New"}},
            "operation_status": "idle",
        }
        preview = self._result(wrote=False)
        store_translation_preview(state, preview)
        service = Mock()
        service.publish.return_value = self._result(
            wrote=False, has_changes=False
        )

        with patch.dict(sys.modules, {"streamlit": streamlit}):
            render_preview_publish(state, "video-1", service, ("de",))

        messages = [call[1] for call in streamlit.calls if call[0] in {"info", "error"}]
        self.assertEqual(messages, ["No localization changes were found."])

    def test_publish_conflict_shows_issues_without_no_change_outcome(self):
        streamlit = _FakeStreamlit()
        state = {
            "bound_video_id": "video-1",
            "draft": {"de": {"title": "New", "description": "New"}},
            "operation_status": "idle",
        }
        store_translation_preview(state, self._result(wrote=False))
        conflict = self._result(
            wrote=False,
            is_valid=False,
            issues=(SimpleNamespace(path="document", message="Video changed"),),
        )
        service = Mock()
        service.publish.return_value = conflict

        with patch.dict(sys.modules, {"streamlit": streamlit}):
            render_preview_publish(state, "video-1", service, ("de",))

        self.assertTrue(any(call[0] == "error" for call in streamlit.calls))
        self.assertFalse(
            any(
                call[0] == "info" and "No localization changes" in call[1]
                for call in streamlit.calls
            )
        )

    def test_publish_exception_shows_only_the_service_error(self):
        streamlit = _FakeStreamlit()
        state = {
            "bound_video_id": "video-1",
            "draft": {"de": {"title": "New", "description": "New"}},
            "operation_status": "idle",
        }
        store_translation_preview(state, self._result(wrote=False))
        service = Mock()
        service.publish.side_effect = RuntimeError("failure")

        with patch.dict(sys.modules, {"streamlit": streamlit}):
            render_preview_publish(state, "video-1", service, ("de",))

        self.assertFalse(
            any(call[0] == "info" for call in streamlit.calls)
        )
        self.assertEqual(
            [call[0] for call in streamlit.calls if call[0] == "error"], ["error"]
        )


if __name__ == "__main__":
    unittest.main()
