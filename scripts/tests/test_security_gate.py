import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GATE_PATH = Path(__file__).resolve().parents[1] / "security_gate.py"
SPEC = importlib.util.spec_from_file_location("security_gate", GATE_PATH)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def extension_sarif_report(score="8.1"):
    """Match CodeQL's extension layout, with a benign driver rule as a decoy."""
    return {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "CodeQL",
                        "guid": "11111111-1111-1111-8111-111111111111",
                        "rules": [{"id": "py/demo", "properties": {"security-severity": "0"}}],
                    },
                    "extensions": [
                        {"name": "pr-diff-range", "rules": []},
                        {
                            "name": "python-queries",
                            "guid": "22222222-2222-2222-8222-222222222222",
                            "rules": [
                                {"id": "py/other-0"},
                                {"id": "py/other-1"},
                                {"id": "py/other-2"},
                                {
                                    "id": "py/demo",
                                    "guid": "33333333-3333-3333-8333-333333333333",
                                    "properties": {"security-severity": score},
                                },
                            ],
                        },
                    ],
                },
                "results": [
                    {
                        "ruleId": "py/demo",
                        "rule": {"id": "py/demo", "index": 3, "toolComponent": {"index": 1}},
                        "level": "note",
                    }
                ],
            }
        ],
    }


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

    def test_sarif_extension_scores_keep_the_same_blocking_threshold(self):
        for score, blocked in (
            ("6.9", []),
            ("7", ["security-severity=7 py/demo"]),
            ("9.8", ["security-severity=9.8 py/demo"]),
        ):
            with self.subTest(score=score):
                self.assertEqual(gate.check_sarif(extension_sarif_report(score)), blocked)
        report = extension_sarif_report()
        report["runs"][0]["tool"]["driver"]["rules"] = []
        self.assertEqual(gate.check_sarif(report), ["security-severity=8.1 py/demo"])

    def test_sarif_id_only_lookup_stays_inside_the_selected_component(self):
        report = extension_sarif_report()
        result = report["runs"][0]["results"][0]
        del result["rule"]["index"]
        self.assertEqual(gate.check_sarif(report), ["security-severity=8.1 py/demo"])
        del result["rule"]["toolComponent"]
        self.assertEqual(gate.check_sarif(report), [])

    def test_sarif_guid_references_select_and_verify_the_component_and_rule(self):
        report = extension_sarif_report()
        reference = report["runs"][0]["results"][0]["rule"]
        reference["toolComponent"] = {
            "guid": "22222222-2222-2222-8222-222222222222",
            "name": "python-queries",
        }
        del reference["index"]
        reference["guid"] = "33333333-3333-3333-8333-333333333333"
        self.assertEqual(gate.check_sarif(report), ["security-severity=8.1 py/demo"])

    def test_sarif_rule_and_legacy_aliases_must_agree(self):
        report = extension_sarif_report()
        result = report["runs"][0]["results"][0]
        result["ruleIndex"] = 3
        self.assertEqual(gate.check_sarif(report), ["security-severity=8.1 py/demo"])
        result["ruleIndex"] = 0
        with self.assertRaises(gate.InvalidReport):
            gate.check_sarif(report)
        del result["ruleIndex"]
        result["ruleId"] = "py/other-0"
        with self.assertRaises(gate.InvalidReport):
            gate.check_sarif(report)

    def test_sarif_legacy_index_inherits_the_selected_extension(self):
        report = extension_sarif_report()
        result = report["runs"][0]["results"][0]
        result["ruleIndex"] = result["rule"].pop("index")
        self.assertEqual(gate.check_sarif(report), ["security-severity=8.1 py/demo"])
        report["runs"][0]["tool"]["driver"]["rules"][0]["properties"]["security-severity"] = "7.5"
        result["rule"] = {"index": 0}
        result["ruleIndex"] = 0
        self.assertEqual(gate.check_sarif(report), ["security-severity=7.5 py/demo"])

    def test_sarif_index_lookup_verifies_ids_and_allows_one_hierarchical_component(self):
        report = extension_sarif_report()
        result = report["runs"][0]["results"][0]
        result["ruleId"] = result["rule"]["id"] = "py/demo/variant"
        self.assertEqual(gate.check_sarif(report), ["security-severity=8.1 py/demo"])
        for identifier in ("py/other-0", "py/demography", "py/demo/", "py/demo/a/b"):
            with self.subTest(identifier=identifier):
                result["ruleId"] = result["rule"]["id"] = identifier
                with self.assertRaises(gate.InvalidReport):
                    gate.check_sarif(report)

    def test_sarif_bad_indices_never_fall_back_to_matching_ids(self):
        for field in ("extension", "nested-rule", "legacy-rule"):
            for index in (-1, 99, True, 1.0, "1", None):
                with self.subTest(field=field, index=index):
                    report = extension_sarif_report()
                    result = report["runs"][0]["results"][0]
                    if field == "extension":
                        result["rule"]["toolComponent"]["index"] = index
                    elif field == "nested-rule":
                        result["rule"]["index"] = index
                    else:
                        result["ruleIndex"] = index
                    with self.assertRaises(gate.InvalidReport):
                        gate.check_sarif(report)

    def test_sarif_unknown_or_conflicting_components_fail_closed(self):
        references = [
            {"index": 0},
            {"guid": "unknown"},
            {"index": 1, "guid": "unknown"},
            {"index": 1, "name": "wrong-name"},
            {"name": "python-queries"},
            None,
            [],
        ]
        for reference in references:
            with self.subTest(reference=reference):
                report = extension_sarif_report()
                report["runs"][0]["results"][0]["rule"]["toolComponent"] = reference
                with self.assertRaises(gate.InvalidReport):
                    gate.check_sarif(report)

    def test_sarif_missing_ambiguous_or_conflicting_rule_metadata_fails_closed(self):
        for change in ("unknown-id", "duplicate-id", "wrong-guid", "missing-severity"):
            with self.subTest(change=change):
                report = extension_sarif_report()
                run = report["runs"][0]
                result = run["results"][0]
                rules = run["tool"]["extensions"][1]["rules"]
                if change == "unknown-id":
                    result["ruleId"] = result["rule"]["id"] = "unknown"
                    del result["rule"]["index"]
                elif change == "duplicate-id":
                    rules.append({"id": "py/demo", "properties": {"security-severity": "0"}})
                    del result["rule"]["index"]
                elif change == "wrong-guid":
                    result["rule"]["guid"] = "unknown"
                else:
                    rules[3]["properties"] = {"tags": ["security"]}
                with self.assertRaises(gate.InvalidReport):
                    gate.check_sarif(report)

    def test_sarif_cli_blocks_an_extension_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "codeql.sarif"
            report.write_text(json.dumps(extension_sarif_report()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(GATE_PATH), "sarif", str(report)],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("BLOCK: security-severity=8.1 py/demo", result.stdout)
            self.assertNotIn("could not be verified", result.stderr)

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
            self.assertEqual(result.returncode, 1)
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
