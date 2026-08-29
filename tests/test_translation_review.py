import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from state.translation_state import store_translation_preview
from ui.translation_review import render_preview_publish


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


class TranslationReviewTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
