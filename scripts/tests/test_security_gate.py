import copy
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GATE_PATH = Path(__file__).resolve().parents[1] / "security_gate.py"
SPEC = importlib.util.spec_from_file_location("security_gate", GATE_PATH)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class SecurityGateTests(unittest.TestCase):
    def test_trivy_high_blocks_even_without_a_fix(self):
        report = {
            "SchemaVersion": 2,
            "ArtifactName": "test",
            "Results": [
                {
                    "Vulnerabilities": [
                        {
                            "Severity": "HIGH",
                            "VulnerabilityID": "DEMO",
                            "PkgName": "test",
                            "InstalledVersion": "1",
                        }
                    ]
                }
            ],
        }
        self.assertEqual(len(gate.check_trivy(report)), 1)
        report["Results"][0]["Vulnerabilities"][0]["Severity"] = "LOW"
        self.assertEqual(gate.check_trivy(report), [])

    def test_trivy_missing_output_cannot_pass(self):
        with self.assertRaises(gate.InvalidReport):
            gate.check_trivy({"SchemaVersion": 2, "ArtifactName": "test"})

    def test_npm_high_is_blocked_but_moderate_is_report_only(self):
        report = {
            "auditReportVersion": 2,
            "metadata": {"vulnerabilities": {"high": 1, "critical": 0}},
            "vulnerabilities": {"test": {"severity": "high"}},
        }
        self.assertTrue(gate.check_npm(report))
        report["metadata"]["vulnerabilities"]["high"] = 0
        report["vulnerabilities"]["test"]["severity"] = "moderate"
        self.assertEqual(gate.check_npm(report), [])

    def test_npm_inconsistent_counts_are_errors(self):
        with self.assertRaises(gate.InvalidReport):
            gate.check_npm(
                {
                    "auditReportVersion": 2,
                    "metadata": {"vulnerabilities": {"high": 1, "critical": 0}},
                    "vulnerabilities": {},
                }
            )

    def test_pip_any_known_vulnerability_blocks(self):
        report = {"dependencies": [{"name": "test", "version": "1", "vulns": [{"id": "DEMO"}]}]}
        self.assertEqual(len(gate.check_pip_audit(report)), 1)
        report["dependencies"][0]["vulns"] = []
        self.assertEqual(gate.check_pip_audit(report), [])

    def test_pip_empty_or_skipped_is_not_a_success(self):
        for dependencies in [[], [{"name": "test", "skip_reason": "unknown"}]]:
            with self.assertRaises(gate.InvalidReport):
                gate.check_pip_audit({"dependencies": dependencies})

    def test_sarif_reads_rule_security_score_not_result_level(self):
        report = {
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "rules": [
                                {
                                    "id": "demo",
                                    "properties": {"security-severity": "8.1"},
                                }
                            ]
                        }
                    },
                    "results": [{"ruleId": "demo", "level": "warning"}],
                }
            ],
        }
        self.assertEqual(len(gate.check_sarif(report)), 1)
        low = copy.deepcopy(report)
        low["runs"][0]["tool"]["driver"]["rules"][0]["properties"]["security-severity"] = "6.9"
        self.assertEqual(gate.check_sarif(low), [])

    def test_sarif_invalid_severity_is_not_clean(self):
        report = {
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "rules": [
                                {
                                    "id": "demo",
                                    "properties": {"security-severity": "NaN"},
                                }
                            ]
                        }
                    },
                    "results": [{"ruleId": "demo"}],
                }
            ],
        }
        with self.assertRaises(gate.InvalidReport):
            gate.check_sarif(report)

    def test_invalid_npm_severity_and_unnamed_python_dependency_fail_closed(self):
        with self.assertRaises(gate.InvalidReport):
            gate.check_npm(
                {
                    "auditReportVersion": 2,
                    "metadata": {"vulnerabilities": {"high": 0, "critical": 0}},
                    "vulnerabilities": {"test": {"severity": "typo"}},
                }
            )
        with self.assertRaises(gate.InvalidReport):
            gate.check_pip_audit({"dependencies": [{"vulns": []}]})

    def test_scanner_error_objects_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "error.json"
            report.write_text('{"error": "network failure"}', encoding="utf-8")
            with self.assertRaises(gate.InvalidReport):
                gate.read_report(report)

    def test_demo_intentionally_fails_and_absent_report_is_error(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "demo.json"
            result = subprocess.run(
                [sys.executable, str(GATE_PATH), "demo", "--report", str(report)],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(result.returncode, 0)  # Intentional red CI exercise; corrected next.
            self.assertIn("DEMO-HIGH-NOT-A-REAL-CVE", result.stdout)
            result = subprocess.run(
                [
                    sys.executable,
                    str(GATE_PATH),
                    "trivy",
                    str(report.with_name("absent.json")),
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
