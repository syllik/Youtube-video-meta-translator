"""Batch orchestration for local Codex YouTube localization generation."""

import json
import os
import tempfile
from pathlib import Path

from llm_localization_package import (
    LLM_BATCH_SIZE,
    build_llm_localization_schema,
    build_llm_translation_package,
    calculate_llm_translation_progress,
    parse_llm_upload_json,
)
from codex_localization_runner import CodexLocalizationError, run_codex_batch


class CodexGenerationError(RuntimeError):
    """Raised when requested Codex localization generation cannot complete."""


def _batches(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def generate_missing_localizations(
    video_resource,
    catalog,
    *,
    batch_size=LLM_BATCH_SIZE,
    max_languages=None,
    retry_count=1,
    run_batch=run_codex_batch,
    on_batch=None,
):
    if batch_size < 1 or batch_size > LLM_BATCH_SIZE:
        raise ValueError(
            "batch_size must be between 1 and {}".format(LLM_BATCH_SIZE)
        )
    if max_languages is not None and max_languages < 1:
        raise ValueError("max_languages must be positive")
    if retry_count < 0:
        raise ValueError("retry_count must not be negative")

    progress = calculate_llm_translation_progress(video_resource, catalog)
    targets = progress.missing
    if max_languages is not None:
        targets = targets[:max_languages]
    if not targets:
        return {}

    batches = tuple(_batches(targets, batch_size))
    merged = {}

    for batch_index, languages in enumerate(batches, start=1):
        codes = tuple(language.code for language in languages)
        if on_batch is not None:
            on_batch(batch_index, len(batches), codes)

        package = build_llm_translation_package(video_resource, languages)
        schema = build_llm_localization_schema(codes)

        result = None
        last_error = None
        for _attempt in range(retry_count + 1):
            try:
                result = run_batch(package, schema)
                break
            except CodexLocalizationError as error:
                last_error = error

        if result is None:
            raise CodexGenerationError(
                "Codex batch {} failed for [{}]: {}".format(
                    batch_index, ", ".join(codes), last_error
                )
            ) from last_error

        parsed_batch = parse_llm_upload_json(
            json.dumps(result, ensure_ascii=False),
            codes,
        )
        if not parsed_batch.is_valid:
            issue = parsed_batch.issues[0]
            raise CodexGenerationError(
                "Codex batch {} failed validation: {}".format(
                    batch_index, issue.message
                )
            )

        parsed_entries_by_code = {
            code.casefold(): value for code, value in parsed_batch.entries.items()
        }
        for code in codes:
            merged[code] = parsed_entries_by_code[code.casefold()].to_dict()

    expected_codes = tuple(language.code for language in targets)
    parsed_merged = parse_llm_upload_json(
        json.dumps(merged, ensure_ascii=False),
        expected_codes,
    )
    if not parsed_merged.is_valid:
        issue = parsed_merged.issues[0]
        raise CodexGenerationError(
            "Merged localization output failed validation: {}".format(issue.message)
        )

    merged_entries_by_code = {
        code.casefold(): value for code, value in parsed_merged.entries.items()
    }
    return {
        code: merged_entries_by_code[code.casefold()].to_dict()
        for code in expected_codes
    }


def write_localizations_atomic(document, output_path):
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=".{}.".format(output_path.name),
        suffix=".tmp",
        dir=str(output_path.parent),
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(document, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary_path, output_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
