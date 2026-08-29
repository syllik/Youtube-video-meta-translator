# Codex CLI Authentication Status False-Negative Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Subagents are prohibited by the user-provided specification.

**Goal:** Distinguish a real local Codex logout from other `codex login status` failures so authenticated ChatGPT users are not shown a false login error.

**Architecture:** Keep the existing local Codex subprocess flow, saved ChatGPT authentication, API-key stripping, execution flags, and UI error boundary. Change only the login-status classifier: recognize the CLI's explicit unauthenticated signal and report other non-zero failures as safe factual diagnostics.

**Tech Stack:** Python 3, `subprocess`, `unittest`, Streamlit error propagation, local Codex CLI.

**Spec:** User-provided request in `/Users/mihaildovgun/.codex/attachments/1ce078f8-ea76-4b86-8de5-11ce3555bfe4/pasted-text.txt`.

## Global Constraints

- Use local Codex CLI authentication through ChatGPT; never add OpenAI API keys.
- Do not remove the authentication guard.
- Do not add provider integrations, a new authentication system, database, or automatic YouTube publishing.
- Preserve the two existing Manual translate and LLM translate workflows.
- Keep macOS/Linux and Windows-compatible subprocess behavior; do not hardcode a machine-specific executable path.
- Do not expose tokens, credentials, or sensitive paths/content in diagnostics.
- Run targeted tests first, then `python -m unittest discover -s tests -v`, compile checks, `git diff --check`, `python -m pip check`, and one real local Codex smoke test.

---

### Task 1: Add regression coverage for login-status classification

**Files:**
- Modify: `tests/test_codex_localization_runner.py`

**Interfaces:**
- Consumes: Existing `runner_module.check_codex_login` test seam with injected `run` and `environ`.
- Produces: Tests proving the explicit `Not logged in` CLI response retains the login guidance while an unrelated non-zero response retains safe factual failure context and does not claim logout.

- [ ] **Step 1: Write the failing tests**

```python
    def test_check_login_reports_explicit_not_logged_in_status(self):
        def fake_run(command, **kwargs):
            return subprocess.CompletedProcess(
                command, 1, stdout="", stderr="Not logged in"
            )

        with self.assertRaisesRegex(
            runner_module.CodexLocalizationError,
            "Codex CLI is not logged in",
        ):
            runner_module.check_codex_login(run=fake_run, environ={})

    def test_check_login_does_not_misclassify_other_status_failure(self):
        def fake_run(command, **kwargs):
            return subprocess.CompletedProcess(
                command,
                17,
                stdout="",
                stderr="network unavailable; token=secret; path=/Users/example/private",
            )

        with self.assertRaises(runner_module.CodexLocalizationError) as context:
            runner_module.check_codex_login(run=fake_run, environ={})

        message = str(context.exception)
        self.assertIn("network unavailable", message)
        self.assertIn("17", message)
        self.assertNotIn("not logged in", message.lower())
        self.assertNotIn("secret", message)
        self.assertNotIn("/Users/example/private", message)
```

- [ ] **Step 2: Run the focused tests and verify the new behavior fails**

Run: `./.venv/bin/python -m unittest tests.test_codex_localization_runner.CodexLocalizationRunnerTests.test_check_login_does_not_misclassify_other_status_failure -v`

Expected: FAIL because the current implementation raises the generic `Codex CLI is not logged in` message and omits the actual failure context.

### Task 2: Implement the minimal safe classifier

**Files:**
- Modify: `codex_localization_runner.py`
- Test: `tests/test_codex_localization_runner.py`

**Interfaces:**
- Consumes: The existing `subprocess.run` injection and `_codex_environment` boundary.
- Produces: `check_codex_login` that returns normally for status code 0, reports the existing login guidance only for an explicit unauthenticated CLI response, and reports a sanitized non-authentication failure otherwise.

- [ ] **Step 1: Implement only the behavior required by the failing tests**

Use the combined status output to recognize the CLI's explicit `Not logged in` signal. For all other non-zero exits, retain the exit code and a bounded diagnostic after removing credential-like values and absolute local paths. Preserve `FileNotFoundError` as the separate CLI-missing error and leave `run_codex_batch` flags unchanged.

- [ ] **Step 2: Run the focused runner tests**

Run: `./.venv/bin/python -m unittest tests.test_codex_localization_runner -v`

Expected: PASS with all runner tests green, including API-key removal, temporary working directory, structured output, invalid JSON, and the new status-classification regressions.

### Task 3: Align troubleshooting guidance

**Files:**
- Modify: `docs/troubleshooting.md`

**Interfaces:**
- Consumes: The final `check_codex_login` user-facing messages.
- Produces: Documentation explaining that only an explicit unauthenticated status calls for `codex login`; other status failures should be investigated as CLI/runtime errors.

- [ ] **Step 1: Update the Codex troubleshooting section**

Keep the existing ChatGPT sign-in instructions and add the distinction between a real `Not logged in` response and other safe status diagnostics. Do not document API keys or a new provider path.

- [ ] **Step 2: Check documentation whitespace and changed-file scope**

Run: `git diff --check`

Expected: no whitespace errors, with only the runner test, runner implementation, troubleshooting documentation, and required plan artifact changed.

### Task 4: Verify the complete credential-free workflow

**Files:**
- Verify: `codex_localization_runner.py`, `tests/test_codex_localization_runner.py`, `docs/troubleshooting.md`

**Interfaces:**
- Consumes: The implemented status classifier and existing local Codex generation flow.
- Produces: Evidence that tests/build checks pass, API-key environment variables remain unnecessary, and one minimal authenticated Codex execution succeeds without YouTube writes.

- [ ] **Step 1: Run the complete unit suite**

Run: `./.venv/bin/python -m unittest discover -s tests -v`

Expected: all discovered tests pass with zero failures and errors.

- [ ] **Step 2: Run static and dependency checks**

Run:

```bash
./.venv/bin/python -m compileall -q streamlit_app.py pages models.py language_catalog.py llm_localization_package.py codex_localization_runner.py codex_localization_generator.py generate_codex_localizations.py services state ui youtube_account.py localizations.py localization_service.py tests
git diff --check
./.venv/bin/python -m pip check
```

Expected: each command exits successfully.

- [ ] **Step 3: Run the minimal real local smoke test**

Run `codex login status`, then one `run_codex_batch` call for a single synthetic `fr` target through the existing local runner with API-key variables absent.

Expected: login status succeeds, the one batch returns valid direct localization JSON, and no YouTube publishing operation is invoked.

- [ ] **Step 4: Review the final diff**

Run: `git status --short --branch && git diff -- codex_localization_runner.py tests/test_codex_localization_runner.py docs/troubleshooting.md`

Expected: the diff contains only the minimal authentication-status classification, its regression coverage, and aligned troubleshooting text; existing execution flags and workflow architecture remain intact.
