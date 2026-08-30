"""Isolated non-interactive Codex runner for YouTube localization batches."""

import json
import os
import re
import signal
import subprocess
import tempfile
import time
from threading import Event
from pathlib import Path

from llm_localization_package import parse_llm_upload_json


CODEX_TRANSLATION_INSTRUCTION = """Translate the supplied YouTube metadata package into every exact target language.
The source.primary metadata is authoritative and determines the intended meaning.
source.references are verified existing translations used only to clarify intent,
tone, and semantic nuance; if they conflict with primary, follow primary. Do not
treat references as competing originals.
Use only the stdin package as translation context.
Preserve meaning, tone, names, URLs, hashtags, technical tokens, and meaningful line breaks.
Return only the direct localization JSON required by the supplied output schema.
Do not inspect files, run commands, browse the web, or add explanations."""


class CodexLocalizationError(RuntimeError):
    """Raised when one local Codex CLI translation attempt cannot be accepted."""


class CodexLocalizationCancelled(CodexLocalizationError):
    """Raised when the user cancels an active Codex localization batch."""


_SAFE_ENVIRONMENT_VARIABLES = (
    "PATH",
    "HOME",
    "USERPROFILE",
    "HOMEDRIVE",
    "HOMEPATH",
    "CODEX_HOME",
    "TMPDIR",
    "TEMP",
    "TMP",
    "LANG",
    "LANGUAGE",
    "LC_ALL",
    "LC_CTYPE",
    "LC_MESSAGES",
    "TERM",
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
)

CODEX_LOGIN_STATUS_TIMEOUT_SECONDS = 15
CODEX_BATCH_TIMEOUT_SECONDS = 120


def _codex_environment(environ=None):
    source_env = os.environ if environ is None else environ
    return {
        key: source_env[key]
        for key in _SAFE_ENVIRONMENT_VARIABLES
        if key in source_env
    }


def _safe_cli_output(output):
    text = (output or "").strip()
    text = re.sub(
        r"(?i)(\b(?:authorization|bearer|access[_ -]?token|refresh[_ -]?token|token|api[_ -]?key|password|secret|credential)s?\b\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+",
        r"\1[redacted]",
        text,
    )
    text = re.sub(r"(?i)\bbearer\s+[^\s,;]+", "Bearer [redacted]", text)
    text = re.sub(r"(?<!\w)/(?:[^/\s]+/)+[^/\s]*", "[path]", text)
    text = re.sub(r"(?i)(?<!\w)(?:[a-z]:\\|\\\\)[^\s]+", "[path]", text)
    return text[-1200:] if len(text) > 1200 else text


def _safe_stderr(stderr):
    return _safe_cli_output(stderr)


def _status_output(completed):
    return "\n".join(
        output.strip()
        for output in (completed.stdout, completed.stderr)
        if output and output.strip()
    )


def _timeout_error_message(action, timeout_seconds):
    return "{} timed out after {} seconds. Check the local Codex CLI session and retry.".format(
        action, timeout_seconds
    )


def _process_is_running(process):
    poll = getattr(process, "poll", None)
    if callable(poll):
        return poll() is None
    return getattr(process, "returncode", None) is None


def _terminate_process(process, grace_period=1.0):
    if not _process_is_running(process):
        return

    process_group_id = None
    if os.name == "posix":
        try:
            process_group_id = os.getpgid(process.pid)
        except (AttributeError, OSError, ProcessLookupError):
            process_group_id = None
        try:
            if process_group_id is not None:
                os.killpg(process_group_id, signal.SIGTERM)
            else:
                raise OSError("process group is unavailable")
        except (OSError, ProcessLookupError):
            terminate = getattr(process, "terminate", None)
            if callable(terminate):
                terminate()
    else:
        terminate = getattr(process, "terminate", None)
        if callable(terminate):
            terminate()

    wait = getattr(process, "wait", None)
    try:
        if callable(wait):
            wait(timeout=grace_period)
    except (subprocess.TimeoutExpired, TimeoutError):
        if process_group_id is not None:
            try:
                os.killpg(process_group_id, signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass
        kill = getattr(process, "kill", None)
        if callable(kill):
            try:
                kill()
            except (OSError, ProcessLookupError):
                pass
        if callable(wait):
            try:
                wait(timeout=grace_period)
            except (subprocess.TimeoutExpired, TimeoutError):
                pass


def _run_process_cancellable(
    command,
    *,
    input_text=None,
    cwd=None,
    environ=None,
    cancel_event: Event,
    popen=subprocess.Popen,
    timeout_seconds=CODEX_BATCH_TIMEOUT_SECONDS,
    poll_interval=0.1,
    action="Codex command",
):
    if cancel_event.is_set():
        raise CodexLocalizationCancelled("Generation stopped before Codex started.")

    kwargs = {
        "stdin": subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "cwd": cwd,
        "env": _codex_environment(environ),
    }
    if os.name == "posix":
        kwargs["start_new_session"] = True
    elif getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0):
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    try:
        process = popen(command, **kwargs)
    except FileNotFoundError as error:
        raise CodexLocalizationError(
            "Codex CLI was not found. Install Codex and run `codex login`."
        ) from error

    pending_input = input_text
    deadline = time.monotonic() + timeout_seconds
    try:
        while True:
            if cancel_event.is_set():
                _terminate_process(process)
                raise CodexLocalizationCancelled(
                    "Generation stopped. The active Codex batch was cancelled."
                )

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _terminate_process(process)
                raise CodexLocalizationError(
                    _timeout_error_message(action, timeout_seconds)
                )

            try:
                stdout, stderr = process.communicate(
                    input=pending_input,
                    timeout=min(poll_interval, remaining),
                )
                return process.returncode, stdout or "", stderr or ""
            except subprocess.TimeoutExpired:
                pending_input = None
    except (CodexLocalizationCancelled, CodexLocalizationError):
        raise
    except Exception:
        _terminate_process(process)
        raise


def check_codex_login(run=subprocess.run, environ=None) -> None:
    try:
        completed = run(
            ["codex", "login", "status"],
            text=True,
            capture_output=True,
            check=False,
            env=_codex_environment(environ),
            timeout=CODEX_LOGIN_STATUS_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        raise CodexLocalizationError(
            "Codex CLI was not found. Install Codex and run `codex login`."
        ) from error
    except subprocess.TimeoutExpired as error:
        raise CodexLocalizationError(
            _timeout_error_message(
                "Codex CLI login status check",
                CODEX_LOGIN_STATUS_TIMEOUT_SECONDS,
            )
        ) from error

    if completed.returncode == 0:
        return

    status_output = _status_output(completed)
    if re.search(r"\bnot\s+logged\s+in\b", status_output, re.IGNORECASE):
        raise CodexLocalizationError(
            "Codex CLI is not logged in. Run `codex login` and choose ChatGPT sign-in."
        )

    detail = _safe_cli_output(status_output)
    diagnostic = detail or "no diagnostic output"
    raise CodexLocalizationError(
        "Codex login status failed with exit code {}: {} "
        "Run `codex --version` and `codex login status` in the same terminal. "
        "If those commands work, restart Streamlit from that terminal.".format(
            completed.returncode, diagnostic
        )
    )


def check_codex_login_cancellable(
    cancel_event: Event, *, popen=subprocess.Popen, environ=None
) -> None:
    returncode, stdout, stderr = _run_process_cancellable(
        ["codex", "login", "status"],
        cancel_event=cancel_event,
        popen=popen,
        environ=environ,
        timeout_seconds=CODEX_LOGIN_STATUS_TIMEOUT_SECONDS,
        action="Codex CLI login status check",
    )
    if returncode == 0:
        return

    status_output = "\n".join(
        output.strip() for output in (stdout, stderr) if output and output.strip()
    )
    if re.search(r"\bnot\s+logged\s+in\b", status_output, re.IGNORECASE):
        raise CodexLocalizationError(
            "Codex CLI is not logged in. Run `codex login` and choose ChatGPT sign-in."
        )
    detail = _safe_cli_output(status_output)
    diagnostic = detail or "no diagnostic output"
    raise CodexLocalizationError(
        "Codex login status failed with exit code {}: {} "
        "Run `codex --version` and `codex login status` in the same terminal. "
        "If those commands work, restart Streamlit from that terminal.".format(
            returncode, diagnostic
        )
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
                timeout=CODEX_BATCH_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as error:
            raise CodexLocalizationError(
                "Codex CLI was not found. Install Codex and run `codex login`."
            ) from error
        except subprocess.TimeoutExpired as error:
            raise CodexLocalizationError(
                _timeout_error_message(
                    "Codex batch generation",
                    CODEX_BATCH_TIMEOUT_SECONDS,
                )
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


def run_codex_batch_cancellable(
    package,
    schema,
    *,
    cancel_event: Event,
    popen=subprocess.Popen,
    environ=None,
    timeout_seconds=CODEX_BATCH_TIMEOUT_SECONDS,
    poll_interval=0.1,
):
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
        returncode, _stdout, stderr = _run_process_cancellable(
            command,
            input_text=json.dumps(package, ensure_ascii=False),
            cwd=str(workdir),
            environ=environ,
            cancel_event=cancel_event,
            popen=popen,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
            action="Codex batch generation",
        )
        if returncode != 0:
            detail = _safe_stderr(stderr)
            raise CodexLocalizationError(
                detail or "codex exec exited with code {}".format(returncode)
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
        return {code: value.to_dict() for code, value in parsed.entries.items()}
