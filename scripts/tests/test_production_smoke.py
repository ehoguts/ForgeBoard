import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SMOKE_PATH = Path(__file__).resolve().parents[1] / "production_smoke.py"
SPEC = importlib.util.spec_from_file_location("production_smoke", SMOKE_PATH)
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


class ProductionSmokeCredentialTests(unittest.TestCase):
    def test_fixture_credentials_stay_out_of_files_and_process_arguments(self):
        secret = "credential-regression-canary-87654321"
        names = ("POSTGRES_PASSWORD", "SMOKE_DATABASE_URL")
        original_environment = {name: os.environ.get(name) for name in names}
        writes = []
        calls = []
        migrations = []

        def record_write(path, content, **kwargs):
            writes.append((path.name, content))
            return len(content)

        def fake_run(arguments, **kwargs):
            environment = kwargs.get("env") or {}
            captured_environment = {name: environment.get(name) for name in names}
            calls.append((arguments, captured_environment))
            if "compose" in arguments and "run" in arguments and "migrate" in arguments:
                migrations.append(captured_environment["SMOKE_DATABASE_URL"])
                if len(migrations) == 1:
                    return subprocess.CompletedProcess(
                        arguments, 1, "", "server certificate does not match host name"
                    )
            if "compose" in arguments and "up" in arguments:
                raise RuntimeError("Fixture capture complete")
            return subprocess.CompletedProcess(arguments, 0, "", "")

        with (
            tempfile.TemporaryDirectory() as repository,
            patch.object(smoke, "REPOSITORY", Path(repository)),
            patch.object(sys, "argv", ["production_smoke.py"]),
            patch.object(smoke.secrets, "token_urlsafe", return_value=secret),
            patch.object(Path, "write_text", record_write),
            patch.object(smoke.subprocess, "run", side_effect=fake_run),
            self.assertRaisesRegex(RuntimeError, "Fixture capture complete"),
        ):
            smoke.main()

        for filename, content in writes:
            self.assertNotIn(secret, content, filename)
        for arguments, _ in calls:
            self.assertNotIn(secret, " ".join(arguments))
        database_calls = [call for call in calls if "POSTGRES_PASSWORD" in call[0]]
        self.assertEqual(len(database_calls), 1)
        self.assertEqual(database_calls[0][1]["POSTGRES_PASSWORD"], secret)
        self.assertEqual(len(migrations), 2)
        self.assertIn("@wrong-database:", migrations[0])
        self.assertIn("@database:", migrations[1])
        self.assertIn(secret, migrations[1])
        for arguments, environment in calls:
            if "compose" in arguments:
                self.assertTrue(environment["SMOKE_DATABASE_URL"])
                if "run" not in arguments:
                    self.assertIn("@database:", environment["SMOKE_DATABASE_URL"])
        self.assertEqual({name: os.environ.get(name) for name in names}, original_environment)

    def test_command_redacts_credentials_before_truncating_error_output(self):
        secret = "credential-regression-canary-87654321"
        database_url = f"postgresql://user:{secret}@database/test"
        environment = {"POSTGRES_PASSWORD": secret, "SMOKE_DATABASE_URL": database_url}
        for stderr in (f"Connection failed: {database_url} {secret}", secret + "x" * 3990):
            with (
                self.subTest(stderr_length=len(stderr)),
                patch.object(
                    smoke.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess(["docker"], 1, "", stderr),
                ) as run,
                self.assertRaises(RuntimeError) as failure,
            ):
                smoke.command(["docker"], environment=environment)
            self.assertNotIn(secret, str(failure.exception))
            self.assertNotIn(secret[-10:], str(failure.exception))
            self.assertNotIn(database_url, str(failure.exception))
            self.assertEqual(run.call_args.kwargs["env"]["POSTGRES_PASSWORD"], secret)
            self.assertEqual(run.call_args.kwargs["env"]["PATH"], os.environ["PATH"])


if __name__ == "__main__":
    unittest.main()
