"""Batch orchestration for local Codex YouTube localization generation."""

import copy
import json
import os
import tempfile
from pathlib import Path

from llm_localization_package import (
    LLM_BATCH_SIZE,
    build_llm_localization_schema,
    build_llm_translation_package,
    build_selected_llm_languages,
    calculate_llm_translation_progress,
    parse_llm_upload_json,
)
from codex_localization_runner import (
    CodexLocalizationCancelled,
    CodexLocalizationError,
    run_codex_batch,
)

class CodexGenerationError(RuntimeError):
    """Raised when requested Codex localization generation cannot complete."""


def _batch_failure_message(batch_index, total_batches, codes, reason):
    return (
        "Codex batch {} / {} failed for [{}]: {}. "
        "The failed batch was not merged. Previously completed batches remain "
        "available in the current draft. "
        "Check the local Codex CLI session and retry."
    ).format(batch_index, total_batches, ", ".join(codes), reason)


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
    selected_source_codes=(),
    target_codes=None,
    on_batch_completed=None,
):
    if batch_size < 1 or batch_size > LLM_BATCH_SIZE:
        raise ValueError(
            "batch_size must be between 1 and {}".format(LLM_BATCH_SIZE)
        )
    if max_languages is not None and max_languages < 1:
        raise ValueError("max_languages must be positive")
    if retry_count < 0:
        raise ValueError("retry_count must not be negative")

    progress = calculate_llm_translation_progress(
        video_resource,
        catalog,
        excluded_source_codes=selected_source_codes,
    )
    if target_codes is None:
        targets = progress.missing
    else:
        targets = build_selected_llm_languages(
            progress, target_codes, max_count=None
        )
    if max_languages is not None:
        targets = targets[:max_languages]
    if not targets:
        return {}

    batches = tuple(_batches(targets, batch_size))
    merged = {}

    for batch_index, languages in enumerate(batches, start=1):
        package = build_llm_translation_package(
            video_resource,
            languages,
            selected_source_codes=selected_source_codes,
            catalog=catalog,
        )
        codes = tuple(package["expectedLanguageCodes"])
        if on_batch is not None:
            on_batch(batch_index, len(batches), codes)

        schema = build_llm_localization_schema(codes)

        result = None
        last_error = None
        for _attempt in range(retry_count + 1):
            try:
                result = run_batch(package, schema)
                break
            except CodexLocalizationCancelled:
                raise
            except CodexLocalizationError as error:
                last_error = error

        if result is None:
            raise CodexGenerationError(
                _batch_failure_message(
                    batch_index, len(batches), codes, last_error
                )
            ) from last_error

        parsed_batch = parse_llm_upload_json(
            json.dumps(result, ensure_ascii=False),
            codes,
        )
        if not parsed_batch.is_valid:
            issue = parsed_batch.issues[0]
            raise CodexGenerationError(
                _batch_failure_message(
                    batch_index,
                    len(batches),
                    codes,
                    "validation failed: {}".format(issue.message),
                )
            )

        parsed_entries_by_code = {
            code.casefold(): value for code, value in parsed_batch.entries.items()
        }
        for code in codes:
            merged[code] = parsed_entries_by_code[code.casefold()].to_dict()

        batch_document = {
            code: copy.deepcopy(merged[code]) for code in codes
        }
        if on_batch_completed is not None:
            on_batch_completed(
                batch_index,
                len(batches),
                codes,
                copy.deepcopy(batch_document),
                copy.deepcopy(merged),
            )

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
