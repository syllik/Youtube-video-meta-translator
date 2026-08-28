"""Isolated non-interactive Codex runner for YouTube localization batches."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

from llm_localization_package import parse_llm_upload_json


CODEX_TRANSLATION_INSTRUCTION = """Translate the supplied YouTube metadata package into every exact target language.
Use only the stdin package as translation context.
Preserve meaning, tone, names, URLs, hashtags, technical tokens, and meaningful line breaks.
Return only the direct localization JSON required by the supplied output schema.
Do not inspect files, run commands, browse the web, or add explanations."""


class CodexLocalizationError(RuntimeError):
    """Raised when one local Codex CLI translation attempt cannot be accepted."""


def _codex_environment(environ=None):
    child_env = dict(os.environ if environ is None else environ)
    child_env.pop("OPENAI_API_KEY", None)
    child_env.pop("CODEX_API_KEY", None)
    return child_env


def _safe_stderr(stderr):
    text = (stderr or "").strip()
    return text[-1200:] if len(text) > 1200 else text


def check_codex_login(run=subprocess.run, environ=None) -> None:
    try:
        completed = run(
            ["codex", "login", "status"],
            text=True,
            capture_output=True,
            check=False,
            env=_codex_environment(environ),
        )
    except FileNotFoundError as error:
        raise CodexLocalizationError(
            "Codex CLI was not found. Install Codex and run `codex login`."
        ) from error

    if completed.returncode != 0:
        raise CodexLocalizationError(
            "Codex CLI is not logged in. Run `codex login` and choose ChatGPT sign-in."
        )


def run_codex_batch(package, schema, run=subprocess.run, environ=None):
    expected_codes = package.get("expectedLanguageCodes")
    if not isinstance(expected_codes, list) or not expected_codes:
        raise CodexLocalizationError("Codex package is missing expectedLanguageCodes")

    with tempfile.TemporaryDirectory(prefix="youtube-codex-localizations-") as directory:
        workdir = Path(directory)
        schema_path = (workdir / "schema.json").resolve()
        output_path = (workdir / "output.json").resolve()
        schema_path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        command = [
            "codex",
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--output-schema",
            str(schema_path),
            "-o",
            str(output_path),
            CODEX_TRANSLATION_INSTRUCTION,
        ]
        try:
            completed = run(
                command,
                input=json.dumps(package, ensure_ascii=False),
                text=True,
                capture_output=True,
                check=False,
                cwd=str(workdir),
                env=_codex_environment(environ),
            )
        except FileNotFoundError as error:
            raise CodexLocalizationError(
                "Codex CLI was not found. Install Codex and run `codex login`."
            ) from error

        if completed.returncode != 0:
            detail = _safe_stderr(completed.stderr)
            raise CodexLocalizationError(
                detail or "codex exec exited with code {}".format(completed.returncode)
            )
        if not output_path.exists():
            raise CodexLocalizationError(
                "Codex completed without writing the expected output file"
            )

        raw_json = output_path.read_text(encoding="utf-8")
        parsed = parse_llm_upload_json(raw_json, expected_codes)
        if not parsed.is_valid:
            issue = parsed.issues[0]
            path = "{}: ".format(issue.path) if issue.path else ""
            raise CodexLocalizationError("{}{}".format(path, issue.message))

        return {
            code: value.to_dict()
            for code, value in parsed.entries.items()
        }
