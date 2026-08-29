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
        "Select a video, review source languages, generate or edit JSON, preview the changes, and publish only after checking the diff.",
    ),
    (
        "What is Manual edit?",
        "It is the editable direct JSON draft for the selected video's current localizations.",
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
        "What does Reset languages do?",
        "It permanently removes all localizations for the selected video and keeps only its default metadata.",
    ),
    (
        "Does deleting JSON keys delete YouTube translations?",
        "No. Normal Publish preserves existing languages omitted from your JSON. Use Reset languages to remove all localizations.",
    ),
    (
        "Is Reset destructive?",
        "Yes. Confirm the native browser warning only after saving translations you want to keep.",
    ),
    (
        "What is the safest recommended workflow?",
        "Save important translations, select useful source references, generate or edit carefully, preview the diff, then publish one video at a time.",
    ),
    (
        "What happens if something fails?",
        "The tool shows an error and does not silently publish a partial result. Check the connection, refresh the list, and try again.",
    ),
)


def render_faq_page() -> None:
    """Render the static FAQ without creating an API client or loading data."""
    import streamlit as st

    for question, answer in FAQ_ENTRIES:
        with st.expander(question, expanded=False):
            st.write(answer)
