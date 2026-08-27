"""Machine translation orchestration, independent from Streamlit widgets."""

from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence, Tuple

from google_translate import TranslationError


@dataclass(frozen=True)
class MachineTranslationOptions:
    prefer_deepl: bool = False
    overwrite: bool = False
    trim: bool = False


@dataclass(frozen=True)
class MachineError:
    video_id: Optional[str]
    language_code: Optional[str]
    error_type: str
    message: str


@dataclass(frozen=True)
class MachineTranslationResult:
    translated: int = 0
    skipped: int = 0
    trimmed: int = 0
    errors: Tuple[MachineError, ...] = ()


class MachineTranslationService:
    def __init__(
        self,
        youtube_service: Any,
        deepl: Optional[Any] = None,
        google: Optional[Any] = None,
        sleep_fn: Optional[Callable[[float], None]] = None,
    ):
        self.youtube = youtube_service
        self.deepl = deepl
        self.google = google
        self.sleep_fn = sleep_fn or (lambda _seconds: None)

    def translate_and_publish(
        self,
        video_ids: Sequence[str],
        language_codes: Sequence[str],
        options: MachineTranslationOptions,
    ) -> MachineTranslationResult:
        translated = 0
        skipped = 0
        trimmed = 0
        errors = []

        for video_id in video_ids:
            try:
                video = self.youtube.get_video_with_localizations(video_id)
            except Exception:
                errors.append(MachineError(
                    str(video_id), None, "video_not_found",
                    "The selected video could not be loaded.",
                ))
                continue

            snippet = video.get("snippet", {})
            original_title = snippet.get("title", "")
            original_description = snippet.get("description", "")
            existing = video.get("localizations", {}) or {}

            for language_code in language_codes:
                if not options.overwrite and language_code in existing:
                    skipped += 1
                    continue

                try:
                    title, description = self._translate_pair(
                        language_code, original_title, original_description,
                        options.prefer_deepl,
                    )
                except TranslationError:
                    errors.append(MachineError(
                        str(video_id), str(language_code), "translation_failed",
                        "Translation provider failed.",
                    ))
                    continue
                except ValueError:
                    errors.append(MachineError(
                        str(video_id), str(language_code), "translation_unavailable",
                        "The selected language is unavailable.",
                    ))
                    continue

                publish_result = self.youtube.publish_machine_localization(
                    str(video_id), str(language_code), title, description, options.trim
                )
                trimmed += publish_result.trimmed
                skipped += publish_result.skipped
                if publish_result.error_type:
                    errors.append(MachineError(
                        str(video_id), str(language_code),
                        str(publish_result.error_type),
                        self._publish_error_message(publish_result.error_type),
                    ))
                elif publish_result.skipped == 0:
                    translated += 1
                self.sleep_fn(1)

        return MachineTranslationResult(
            translated=translated,
            skipped=skipped,
            trimmed=trimmed,
            errors=tuple(errors),
        )

    def _translate_pair(self, language_code, title, description, prefer_deepl):
        if prefer_deepl and self.deepl and self._deepl_supports(language_code):
            try:
                return (
                    self.deepl.translate_text(title, target_lang=language_code).text,
                    self.deepl.translate_text(description, target_lang=language_code).text,
                )
            except Exception:
                pass

        if self.google and self._google_supports(language_code):
            try:
                return (
                    self.google.translate_text(language_code, title),
                    self.google.translate_text(language_code, description),
                )
            except TranslationError:
                raise
            except Exception as error:
                raise TranslationError("Google translation failed") from error

        raise ValueError("Unsupported translation language")

    def _deepl_supports(self, language_code):
        try:
            return language_code.lower() in {
                item.code.lower() for item in self.deepl.get_target_languages()
            }
        except Exception:
            return False

    def _google_supports(self, language_code):
        return language_code.lower() in {
            str(code).lower() for code in getattr(self.google, "all_language_codes", ())
        }

    @staticmethod
    def _publish_error_message(error_type):
        if error_type == "defaultLanguageNotSet":
            return "Set the original video language in YouTube before translating."
        return "YouTube could not publish this localization."
