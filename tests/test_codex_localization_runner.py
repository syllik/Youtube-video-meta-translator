import importlib
import json
import os
import subprocess
import threading
import time
import unittest
from unittest.mock import call, patch


try:
    runner_module = importlib.import_module("codex_localization_runner")
except ModuleNotFoundError:
    runner_module = None


PACKAGE = {
    "source": {
        "defaultLanguage": "en",
        "title": "Waterfall",
        "description": "Wind above the falls.",
    },
    "targetLanguages": [{"code": "fr", "name": "French"}],
    "expectedLanguageCodes": ["fr"],
    "expectedCount": 1,
}
SCHEMA = {
    "type": "object",
    "properties": {},
    "required": ["fr"],
    "additionalProperties": False,
}


class CodexLocalizationRunnerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(runner_module, "runner module is not implemented")

    def test_check_login_uses_status_command_and_strips_api_keys(self):
        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        runner_module.check_codex_login(
            run=fake_run,
            environ={
                "HOME": "/tmp/home",
                "USERPROFILE": "/tmp/profile",
                "CODEX_HOME": "/tmp/codex",
                "OPENAI_API_KEY": "api-key",
                "CODEX_API_KEY": "codex-key",
            },
        )

        command, kwargs = calls[0]
        self.assertEqual(command, ["codex", "login", "status"])
        self.assertEqual(kwargs["env"]["HOME"], "/tmp/home")
        self.assertEqual(kwargs["env"]["USERPROFILE"], "/tmp/profile")
        self.assertEqual(kwargs["env"]["CODEX_HOME"], "/tmp/codex")
        self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
        self.assertNotIn("CODEX_API_KEY", kwargs["env"])

    def test_check_login_uses_allowlisted_runtime_environment_only(self):
        calls = []
        synthetic_env = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/tmp/home",
            "USERPROFILE": "/tmp/profile",
            "CODEX_HOME": "/tmp/codex",
            "YOUTUBE_API_KEY": "youtube-secret",
            "GOOGLE_APPLICATION_CREDENTIALS": "/tmp/gcp.json",
            "GITHUB_TOKEN": "github-secret",
            "AWS_SECRET_ACCESS_KEY": "aws-secret",
            "APP_SECRET": "app-secret",
            "OPENAI_API_KEY": "api-key",
            "CODEX_API_KEY": "codex-key",
        }

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        runner_module.check_codex_login(run=fake_run, environ=synthetic_env)

        self.assertEqual(
            calls[0][1]["env"],
            {
                "PATH": "/usr/bin:/bin",
                "HOME": "/tmp/home",
                "USERPROFILE": "/tmp/profile",
                "CODEX_HOME": "/tmp/codex",
            },
        )

    def test_check_login_rejects_missing_executable(self):
        def fake_run(command, **kwargs):
            raise FileNotFoundError("codex")

        with self.assertRaises(runner_module.CodexLocalizationError):
            runner_module.check_codex_login(run=fake_run, environ={})

    def test_check_login_rejects_logged_out_status(self):
        def fake_run(command, **kwargs):
            return subprocess.CompletedProcess(
                command, 1, stdout="", stderr="Not logged in"
            )

        with self.assertRaises(runner_module.CodexLocalizationError):
            runner_module.check_codex_login(run=fake_run, environ={})

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
                stderr=(
                    "network unavailable; token=plain-token-value; "
                    "access_token=oauth-secret-value; path=/Users/example/private"
                ),
            )

        with self.assertRaises(runner_module.CodexLocalizationError) as context:
            runner_module.check_codex_login(run=fake_run, environ={})

        message = str(context.exception)
        self.assertIn("network unavailable", message)
        self.assertIn("17", message)
        self.assertIn("codex --version", message)
        self.assertIn("codex login status", message)
        self.assertIn("restart Streamlit", message)
        self.assertNotIn("not logged in", message.lower())
        self.assertNotIn("plain-token-value", message)
        self.assertNotIn("oauth-secret-value", message)
        self.assertNotIn("/Users/example/private", message)

    def test_check_login_converts_timeout_to_domain_error_without_output_leak(self):
        def fake_run(command, **kwargs):
            raise subprocess.TimeoutExpired(
                command,
                15,
                output="sensitive stdout",
                stderr="sensitive stderr",
            )

        with self.assertRaisesRegex(
            runner_module.CodexLocalizationError, "timed out"
        ) as context:
            runner_module.check_codex_login(run=fake_run, environ={})

        self.assertNotIn("sensitive stdout", str(context.exception))
        self.assertNotIn("sensitive stderr", str(context.exception))

    def test_run_batch_uses_ephemeral_read_only_structured_output(self):
        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            output_path = command[command.index("-o") + 1]
            with open(output_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "fr": {
                            "title": "Cascade",
                            "description": "Vent au-dessus des chutes.",
                        }
                    },
                    handle,
                    ensure_ascii=False,
                )
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        result = runner_module.run_codex_batch(
            PACKAGE,
            SCHEMA,
            run=fake_run,
            environ={
                "HOME": "/tmp/home",
                "OPENAI_API_KEY": "api-key",
                "CODEX_API_KEY": "codex-key",
            },
        )

        self.assertEqual(result["fr"]["title"], "Cascade")
        command, kwargs = calls[0]
        self.assertEqual(command[:2], ["codex", "exec"])
        self.assertIn("--ephemeral", command)
        self.assertIn("read-only", command)
        self.assertIn("--skip-git-repo-check", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--output-schema", command)
        self.assertIn("-o", command)
        self.assertNotIn("--json", command)
        self.assertEqual(kwargs["input"], json.dumps(PACKAGE, ensure_ascii=False))
        self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
        self.assertNotIn("CODEX_API_KEY", kwargs["env"])

    def test_run_batch_converts_timeout_to_domain_error_without_output_leak(self):
        def fake_run(command, **kwargs):
            raise subprocess.TimeoutExpired(
                command,
                120,
                output='{"fr":{"title":"partial"}}',
                stderr="secret stderr",
            )

        with self.assertRaisesRegex(
            runner_module.CodexLocalizationError, "timed out"
        ) as context:
            runner_module.run_codex_batch(PACKAGE, SCHEMA, run=fake_run, environ={})

        self.assertNotIn("partial", str(context.exception))
        self.assertNotIn("secret stderr", str(context.exception))

    def test_run_batch_uses_temporary_working_directory_outside_repository(self):
        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            output_path = command[command.index("-o") + 1]
            with open(output_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {"fr": {"title": "Cascade", "description": "Texte"}},
                    handle,
                )
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        runner_module.run_codex_batch(PACKAGE, SCHEMA, run=fake_run, environ={})

        command, kwargs = calls[0]
        self.assertNotEqual(kwargs["cwd"], os.getcwd())
        self.assertNotIn(os.getcwd(), kwargs["cwd"])
        self.assertEqual(kwargs["input"], json.dumps(PACKAGE, ensure_ascii=False))
        schema_path = command[command.index("--output-schema") + 1]
        self.assertNotEqual(schema_path, command[command.index("-o") + 1])

    def test_run_batch_parses_output_and_preserves_canonical_result(self):
        def fake_run(command, **kwargs):
            output_path = command[command.index("-o") + 1]
            with open(output_path, "w", encoding="utf-8") as handle:
                handle.write(
                    '{"FR":{"title":"Cascade","description":"Texte"}}'
                )
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        result = runner_module.run_codex_batch(PACKAGE, SCHEMA, run=fake_run, environ={})

        self.assertEqual(
            result,
            {"fr": {"title": "Cascade", "description": "Texte"}},
        )

    def test_run_batch_rejects_nonzero_exit(self):
        def fake_run(command, **kwargs):
            return subprocess.CompletedProcess(
                command, 7, stdout="", stderr="translation failed"
            )

        with self.assertRaisesRegex(
            runner_module.CodexLocalizationError, "translation failed"
        ):
            runner_module.run_codex_batch(PACKAGE, SCHEMA, run=fake_run, environ={})

    def test_run_batch_rejects_invalid_json(self):
        def fake_run(command, **kwargs):
            output_path = command[command.index("-o") + 1]
            with open(output_path, "w", encoding="utf-8") as handle:
                handle.write("not json")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        with self.assertRaises(runner_module.CodexLocalizationError):
            runner_module.run_codex_batch(PACKAGE, SCHEMA, run=fake_run, environ={})

    def test_run_batch_rejects_missing_target_code(self):
        package = dict(PACKAGE)
        package["expectedLanguageCodes"] = ["fr", "de"]

        def fake_run(command, **kwargs):
            output_path = command[command.index("-o") + 1]
            with open(output_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {"fr": {"title": "Cascade", "description": "Texte"}},
                    handle,
                )
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        with self.assertRaisesRegex(
            runner_module.CodexLocalizationError, "Missing required language code"
        ):
            runner_module.run_codex_batch(package, SCHEMA, run=fake_run, environ={})

    def test_cancellable_batch_terminates_the_active_process(self):
        cancel_event = threading.Event()
        processes = []

        class BlockingProcess:
            def __init__(self, command, **kwargs):
                self.command = command
                self.kwargs = kwargs
                self.returncode = None
                self.terminated = False
                self.killed = False
                processes.append(self)

            def communicate(self, **_kwargs):
                if self.returncode is not None:
                    return "", ""
                raise subprocess.TimeoutExpired(self.command, 0.01)

            def terminate(self):
                self.terminated = True
                self.returncode = -15

            def kill(self):
                self.killed = True
                self.returncode = -9

            def wait(self, **_kwargs):
                return self.returncode

        def cancel():
            time.sleep(0.03)
            cancel_event.set()

        thread = threading.Thread(target=cancel)
        thread.start()
        with self.assertRaisesRegex(
            runner_module.CodexLocalizationCancelled, "stopped"
        ):
            runner_module.run_codex_batch_cancellable(
                PACKAGE,
                SCHEMA,
                cancel_event=cancel_event,
                popen=BlockingProcess,
                poll_interval=0.01,
            )
        thread.join()

        self.assertEqual(len(processes), 1)
        self.assertTrue(processes[0].terminated or processes[0].killed)

    def test_cancellable_batch_timeout_terminates_the_active_process(self):
        processes = []

        class BlockingProcess:
            def __init__(self, command, **kwargs):
                self.command = command
                self.returncode = None
                self.terminated = False
                self.killed = False
                processes.append(self)

            def communicate(self, **_kwargs):
                raise subprocess.TimeoutExpired(self.command, 0.01)

            def terminate(self):
                self.terminated = True
                self.returncode = -15

            def kill(self):
                self.killed = True
                self.returncode = -9

            def wait(self, **_kwargs):
                return self.returncode

        with self.assertRaisesRegex(
            runner_module.CodexLocalizationError, "timed out"
        ):
            runner_module.run_codex_batch_cancellable(
                PACKAGE,
                SCHEMA,
                cancel_event=threading.Event(),
                popen=BlockingProcess,
                timeout_seconds=0.03,
                poll_interval=0.01,
            )

        self.assertEqual(len(processes), 1)
        self.assertTrue(processes[0].terminated or processes[0].killed)

    def test_process_group_is_killed_after_graceful_termination_times_out(self):
        class SlowProcess:
            pid = 123

            def __init__(self):
                self.returncode = None
                self.killed = False
                self.wait_calls = 0

            def poll(self):
                return self.returncode

            def wait(self, **_kwargs):
                self.wait_calls += 1
                if self.wait_calls == 1:
                    raise subprocess.TimeoutExpired(["codex"], 1)
                self.returncode = -9
                return self.returncode

            def kill(self):
                self.killed = True
                self.returncode = -9

        process = SlowProcess()
        with patch.object(
            runner_module.os, "getpgid", return_value=456
        ) as getpgid, patch.object(
            runner_module.os, "killpg"
        ) as killpg:
            runner_module._terminate_process(process, grace_period=0)

        getpgid.assert_called_once_with(123)
        self.assertEqual(
            killpg.call_args_list,
            [
                call(456, runner_module.signal.SIGTERM),
                call(456, runner_module.signal.SIGKILL),
            ],
        )

    def test_cancellable_batch_validates_structured_output_before_returning(self):
        processes = []

        class SuccessfulProcess:
            def __init__(self, command, **kwargs):
                self.command = command
                self.kwargs = kwargs
                self.returncode = 0
                processes.append(self)

            def communicate(self, **_kwargs):
                output_path = self.command[self.command.index("-o") + 1]
                with open(output_path, "w", encoding="utf-8") as handle:
                    json.dump(
                        {"fr": {"title": "Cascade", "description": "Texte"}},
                        handle,
                    )
                return "", ""

            def poll(self):
                return self.returncode

        result = runner_module.run_codex_batch_cancellable(
            PACKAGE,
            SCHEMA,
            cancel_event=threading.Event(),
            popen=SuccessfulProcess,
        )

        self.assertEqual(
            result,
            {"fr": {"title": "Cascade", "description": "Texte"}},
        )
        self.assertEqual(len(processes), 1)
        self.assertTrue(processes[0].kwargs["start_new_session"])


if __name__ == "__main__":
    unittest.main()
