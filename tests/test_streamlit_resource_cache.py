import unittest

from streamlit.testing.v1 import AppTest

from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog
from state.common_state import get_selected_video_resource, reset_video_cache


class VideoResourceCacheTests(unittest.TestCase):
    def test_same_video_resource_is_fetched_once(self):
        calls = []

        class Service:
            def get_video_with_localizations(self, video_id):
                calls.append(video_id)
                return {"id": video_id, "snippet": {}, "localizations": {}}

        state = {}
        first = get_selected_video_resource(Service(), state, "video-1")
        second = get_selected_video_resource(Service(), state, "video-1")

        self.assertEqual(first, second)
        self.assertEqual(calls, ["video-1"])

    def test_switching_video_replaces_the_cached_resource(self):
        calls = []

        class Service:
            def get_video_with_localizations(self, video_id):
                calls.append(video_id)
                return {"id": video_id, "snippet": {}, "localizations": {}}

        state = {}
        first = get_selected_video_resource(Service(), state, "video-1")
        second = get_selected_video_resource(Service(), state, "video-2")

        self.assertEqual(first["id"], "video-1")
        self.assertEqual(second["id"], "video-2")
        self.assertEqual(calls, ["video-1", "video-2"])

    def test_explicit_video_cache_reset_forces_one_fresh_read(self):
        calls = []

        class Service:
            def get_video_with_localizations(self, video_id):
                calls.append(video_id)
                return {"id": video_id, "snippet": {}, "localizations": {}}

        state = {}
        get_selected_video_resource(Service(), state, "video-1")
        reset_video_cache(state)
        get_selected_video_resource(Service(), state, "video-1")

        self.assertEqual(calls, ["video-1", "video-1"])

    def test_target_widget_reruns_keep_clear_all_empty_without_refetch(self):
        app = AppTest.from_string(
            """
import streamlit as st
from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog
from state.common_state import get_selected_video_resource
from ui.target_selection import render_target_selection

catalog = YouTubeLanguageCatalog(
    source="test", fetched_at="now", hl="en",
    languages=tuple(
        YouTubeLanguage(code, code, code, code)
        for code in ("en", "de", "es", "fr")
    ),
)
video = {
    "id": "video-1",
    "snippet": {
        "defaultLanguage": "en",
        "title": "Title",
        "description": "Description",
    },
    "localizations": {},
}

class Service:
    def get_video_with_localizations(self, video_id):
        st.session_state["resource_fetches"] = st.session_state.get("resource_fetches", 0) + 1
        return video

service = st.session_state.setdefault("resource_service", Service())
resource = get_selected_video_resource(service, st.session_state, "video-1")
render_target_selection(st.session_state, resource, catalog, source_codes=("en",))
st.write("selected", st.session_state["translation"]["selected_target_codes"])
"""
        ).run()

        self.assertEqual(list(app.exception), [])
        self.assertEqual(app.session_state["resource_fetches"], 1)
        target = app.multiselect[0]
        self.assertEqual(target.value, ["de", "es", "fr"])

        target.set_value(["de"]).run()
        self.assertEqual(app.session_state["resource_fetches"], 1)
        self.assertEqual(app.multiselect[0].value, ["de"])

        app.multiselect[0].set_value([]).run()
        self.assertEqual(app.session_state["resource_fetches"], 1)
        self.assertEqual(app.multiselect[0].value, [])

        app.run()
        self.assertEqual(app.session_state["resource_fetches"], 1)
        self.assertEqual(app.multiselect[0].value, [])

    def test_prompt_page_source_and_target_reruns_keep_one_resource_read(self):
        app = AppTest.from_string(
            """
import streamlit as st
st.page_link = lambda *args, **kwargs: None
from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog
from state.common_state import get_selected_video_resource
from state.llm_state import init_llm_state, sync_llm_video
from ui.llm_prompt import render_llm_prompt_page
from ui.source_selection import render_source_selection

catalog = YouTubeLanguageCatalog(
    source="test", fetched_at="now", hl="en",
    languages=tuple(
        YouTubeLanguage(code, code, code, code)
        for code in ("en", "de", "es", "fr")
    ),
)
video = {
    "id": "video-1",
    "snippet": {
        "defaultLanguage": "en",
        "title": "Title",
        "description": "Description",
    },
    "localizations": {"de": {"title": "Titel", "description": "Beschreibung"}},
}

class Service:
    def get_video_with_localizations(self, video_id):
        st.session_state["resource_fetches"] = st.session_state.get("resource_fetches", 0) + 1
        return video

service = st.session_state.setdefault("resource_service", Service())
resource = get_selected_video_resource(service, st.session_state, "video-1")
prompt_state = init_llm_state(st.session_state)
sync_llm_video(prompt_state, "video-1")
source_codes = render_source_selection(st.session_state, resource, catalog)
render_llm_prompt_page(prompt_state, resource, catalog, source_codes=source_codes)
"""
        ).run()

        self.assertEqual(list(app.exception), [])
        self.assertEqual(app.session_state["resource_fetches"], 1)
        source = next(
            widget for widget in app.multiselect if widget.key.startswith("common-source-")
        )
        target = next(
            widget for widget in app.multiselect if widget.key.startswith("llm-prompt-targets-")
        )

        source.set_value(["de"]).run()
        self.assertEqual(app.session_state["resource_fetches"], 1)
        target = next(
            widget for widget in app.multiselect if widget.key.startswith("llm-prompt-targets-")
        )
        target.set_value([]).run()
        self.assertEqual(app.session_state["resource_fetches"], 1)
        self.assertEqual(app.multiselect[-1].value, [])

    def test_translate_page_target_reruns_do_not_refetch_selected_video(self):
        app = AppTest.from_string(
            """
import runpy
from types import SimpleNamespace
import streamlit as st
st.page_link = lambda *args, **kwargs: None
import streamlit_app
from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog

catalog = YouTubeLanguageCatalog(
    source="test", fetched_at="now", hl="en",
    languages=tuple(
        YouTubeLanguage(code, code, code, code)
        for code in ("en", "de", "es", "fr")
    ),
)
video = {
    "id": "video-1",
    "snippet": {
        "defaultLanguage": "en",
        "title": "Title",
        "description": "Description",
    },
    "localizations": {},
}

class Service:
    def get_video_with_localizations(self, video_id):
        st.session_state["resource_fetches"] = st.session_state.get("resource_fetches", 0) + 1
        return video

service = st.session_state.setdefault("resource_service", Service())
streamlit_app.configure_page = lambda *args, **kwargs: None
streamlit_app.bootstrap_app_context = lambda: SimpleNamespace(
    selected_video_id="video-1",
    service=service,
    metadata_language_catalog=catalog,
)
runpy.run_path("pages/1_Translate.py", run_name="__main__")
"""
        ).run()

        self.assertEqual(list(app.exception), [])
        self.assertEqual(app.session_state["resource_fetches"], 1)
        self.assertEqual(len(app.multiselect), 1)

        app.multiselect[0].set_value(["de"]).run()
        self.assertEqual(app.session_state["resource_fetches"], 1)
        app.multiselect[0].set_value([]).run()
        self.assertEqual(app.session_state["resource_fetches"], 1)
        self.assertEqual(app.multiselect[0].value, [])

    def test_prompt_page_widgets_do_not_refetch_selected_video(self):
        app = AppTest.from_string(
            """
import runpy
from types import SimpleNamespace
import streamlit as st
st.page_link = lambda *args, **kwargs: None
import streamlit_app
from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog

catalog = YouTubeLanguageCatalog(
    source="test", fetched_at="now", hl="en",
    languages=tuple(
        YouTubeLanguage(code, code, code, code)
        for code in ("en", "de", "es", "fr")
    ),
)
video = {
    "id": "video-1",
    "snippet": {
        "defaultLanguage": "en",
        "title": "Title",
        "description": "Description",
    },
    "localizations": {"de": {"title": "Titel", "description": "Beschreibung"}},
}

class Service:
    def get_video_with_localizations(self, video_id):
        st.session_state["resource_fetches"] = st.session_state.get("resource_fetches", 0) + 1
        return video

service = st.session_state.setdefault("resource_service", Service())
streamlit_app.configure_page = lambda *args, **kwargs: None
streamlit_app.bootstrap_app_context = lambda: SimpleNamespace(
    selected_video_id="video-1",
    service=service,
    metadata_language_catalog=catalog,
)
runpy.run_path("pages/2_LLM_prompt.py", run_name="__main__")
"""
        ).run()

        self.assertEqual(list(app.exception), [])
        self.assertEqual(app.session_state["resource_fetches"], 1)
        source = next(
            widget for widget in app.multiselect if widget.key.startswith("common-source-")
        )
        target = next(
            widget for widget in app.multiselect if widget.key.startswith("llm-prompt-targets-")
        )

        source.set_value(["de"]).run()
        self.assertEqual(app.session_state["resource_fetches"], 1)
        target = next(
            widget for widget in app.multiselect if widget.key.startswith("llm-prompt-targets-")
        )
        target.set_value([]).run()
        self.assertEqual(app.session_state["resource_fetches"], 1)


if __name__ == "__main__":
    unittest.main()
