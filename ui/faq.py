"""Static FAQ content that does not depend on YouTube or OAuth."""


FAQ_ENTRIES = (
    (
        "What is this tool?",
        "It helps you translate YouTube video titles and descriptions into supported localization languages.",
    ),
    (
        "Why do YouTube localizations matter?",
        "They help viewers understand your videos and can make titles and descriptions more useful in other languages.",
    ),
    (
        "What is the basic workflow?",
        "Select a video, review the read-only primary source and optional references, generate or upload translations, preview the changes, and publish only after checking the diff.",
    ),
    (
        "What does Codex do?",
        "Codex can generate missing localization entries for review. It never publishes directly.",
    ),
    (
        "What is the LLM Translation prompt?",
        "It prepares a source-aware prompt for an external LLM. You download its JSON result and upload it on Translate.",
    ),
    (
        "Why use multiple source languages?",
        "One source can miss nuance. Two or three good translations, ideally from different language families, can give the LLM more context. The default source remains authoritative.",
    ),
    (
        "What is the difference between Preview and Publish?",
        "Preview only compares your draft with YouTube. Publish performs the YouTube update and requires a current valid preview.",
    ),
    (
        "What happens after a successful Publish?",
        "The sidebar video-page cache is cleared and the current localization count is fetched again automatically. A no-change result or conflict does not pretend to refresh state.",
    ),
    (
        "What does Reset languages do?",
        "It permanently removes all non-default localizations for the selected video and keeps only its default metadata. Reset is available only in the selected-video Danger zone.",
    ),
    (
        "What happens to existing translations?",
        "Normal Publish preserves existing YouTube localizations that are not included in the generated or uploaded draft. Use Reset languages to remove all localizations.",
    ),
    (
        "Is Reset destructive?",
        "Yes. Confirm the native browser warning only after saving translations you want to keep. Reset requires a fresh ETag and conditional write; a changed selection or HTTP 412 performs no accepted write.",
    ),
    (
        "What is the safest recommended workflow?",
        "Save important translations, select useful source references, generate or upload carefully, preview the diff, then publish one video at a time.",
    ),
    (
        "What happens if something fails?",
        "The tool shows an error and does not silently publish a partial result. Check the connection, refresh the list, and try again.",
    ),
    (
        "How do I fix first-run authorization errors?",
        "Save a Google Desktop app OAuth client at config/account_client_secrets_main.json. If authorization expires, restart authorization and remove the local token.json only when necessary. Never share credential contents.",
    ),
)


def render_faq_page() -> None:
    """Render the static FAQ without creating an API client or loading data."""
    import streamlit as st

    for question, answer in FAQ_ENTRIES:
        with st.expander(question, expanded=False):
            st.write(answer)
