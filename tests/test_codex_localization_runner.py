import importlib
import json
import os
import subprocess
import unittest


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

    def test_check_login_rejects_missing_executable(self):
        def fake_run(command, **kwargs):
            raise FileNotFoundError("codex")

        with self.assertRaises(runner_module.CodexLocalizationError):
            runner_module.check_codex_login(run=fake_run, environ={})

    def test_check_login_rejects_logged_out_status(self):
        def fake_run(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")

        with self.assertRaises(runner_module.CodexLocalizationError):
            runner_module.check_codex_login(run=fake_run, environ={})

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


if __name__ == "__main__":
    unittest.main()
