"""Fail closed on invalid scanner output; keep security thresholds reviewable."""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


class InvalidReport(ValueError):
    pass


def read_report(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or "error" in data:
        raise InvalidReport(f"{path}: scanner error or invalid report object")
    return data


def check_trivy(data: dict[str, Any]) -> list[str]:
    if data.get("SchemaVersion") != 2 or not data.get("ArtifactName"):
        raise InvalidReport("Expected a complete Trivy schema 2 report")
    results = data.get("Results")
    if not isinstance(results, list):
        raise InvalidReport("Trivy Results must be a list")
    blocked = []
    for result in results:
        for finding in result.get("Vulnerabilities") or []:
            severity = finding["Severity"]
            if severity not in {"UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"}:
                raise InvalidReport("Unknown Trivy severity")
            if severity in {"HIGH", "CRITICAL"}:
                blocked.append(
                    f"{severity} {finding['VulnerabilityID']} {finding['PkgName']} "
                    f"{finding['InstalledVersion']} -> "
                    f"{finding.get('FixedVersion') or 'no fix listed'}"
                )
    return blocked


def check_npm(data: dict[str, Any]) -> list[str]:
    if data.get("auditReportVersion") != 2 or not isinstance(data.get("vulnerabilities"), dict):
        raise InvalidReport("Expected npm audit report version 2")
    counts = data["metadata"]["vulnerabilities"]
    if any(
        type(counts.get(level)) is not int or counts[level] < 0 for level in ("high", "critical")
    ):
        raise InvalidReport("Missing npm severity counts")
    blocked = []
    for name, item in data["vulnerabilities"].items():
        if (
            not isinstance(name, str)
            or not name
            or item.get("severity") not in {"info", "low", "moderate", "high", "critical"}
        ):
            raise InvalidReport("Invalid npm dependency or severity")
        if item["severity"] in {"high", "critical"}:
            blocked.append(f"{item['severity'].upper()} {name}")
    if counts["high"] + counts["critical"] != len(blocked):
        raise InvalidReport("npm counts disagree with findings")
    return blocked


def check_pip_audit(data: dict[str, Any]) -> list[str]:
    dependencies = data.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise InvalidReport("pip-audit did not report any dependencies")
    blocked = []
    for dependency in dependencies:
        if any(
            not isinstance(dependency.get(field), str) or not dependency[field]
            for field in ("name", "version")
        ):
            raise InvalidReport("pip-audit dependency has no name or version")
        if dependency.get("skip_reason") or not isinstance(dependency.get("vulns"), list):
            raise InvalidReport("pip-audit skipped or failed to audit a dependency")
        for finding in dependency["vulns"]:
            if not isinstance(finding.get("id"), str) or not finding["id"]:
                raise InvalidReport("pip-audit finding has no advisory identifier")
            blocked.append(f"{finding['id']} {dependency['name']} {dependency['version']}")
    return blocked


def check_sarif(data: dict[str, Any]) -> list[str]:
    if data.get("version") != "2.1.0" or not isinstance(data.get("runs"), list) or not data["runs"]:
        raise InvalidReport("Expected SARIF 2.1.0 with at least one analysis run")
    blocked = []
    for run in data["runs"]:
        if any(
            invocation.get("executionSuccessful") is False
            for invocation in run.get("invocations", [])
        ):
            raise InvalidReport("SARIF reports an unsuccessful scanner invocation")
        rules = run["tool"]["driver"].get("rules", [])
        by_id = {rule["id"]: rule for rule in rules}
        if not isinstance(run.get("results"), list):
            raise InvalidReport("SARIF run has no results list")
        for result in run["results"]:
            rule_id = result.get("ruleId")
            rule = by_id.get(rule_id)
            if rule is None and type(result.get("ruleIndex")) is int:
                index = result["ruleIndex"]
                if not 0 <= index < len(rules):
                    raise InvalidReport("Invalid SARIF rule index")
                rule = rules[index]
            if rule is None:
                raise InvalidReport("SARIF result references an unknown rule")
            severity = rule.get("properties", {}).get("security-severity")
            if severity is None:
                # Security queries must retain severity metadata. Quality errors also fail.
                if "security" in rule.get("properties", {}).get("tags", []):
                    raise InvalidReport("Security rule has no security-severity metadata")
                if (
                    result.get("level", rule.get("defaultConfiguration", {}).get("level"))
                    == "error"
                ):
                    blocked.append(f"ERROR {rule['id']}")
                continue
            score = float(severity)
            if not math.isfinite(score) or not 0 <= score <= 10:
                raise InvalidReport("Invalid SARIF security-severity")
            if score >= 7:
                blocked.append(f"security-severity={score:g} {rule['id']}")
    return blocked


CHECKERS = {
    "trivy": check_trivy,
    "npm": check_npm,
    "pip-audit": check_pip_audit,
    "sarif": check_sarif,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scanner", choices=[*CHECKERS, "demo"])
    parser.add_argument("reports", nargs="*", type=Path)
    parser.add_argument("--report", type=Path, help="Synthetic demo output only")
    args = parser.parse_args()
    if args.scanner == "demo":
        if not args.report:
            parser.error("demo requires --report")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(
                {
                    "SchemaVersion": 2,
                    "ArtifactName": "synthetic-ci-gate-exercise",
                    "Results": [
                        {
                            "Vulnerabilities": [
                                {
                                    "VulnerabilityID": "DEMO-HIGH-NOT-A-REAL-CVE",
                                    "PkgName": "synthetic-gate-fixture",
                                    "InstalledVersion": "0.0.0",
                                    "Severity": "HIGH",
                                }
                            ]
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        print("Intentional failure exercise: synthetic report; no vulnerable software installed.")
        args.scanner, args.reports = "trivy", [args.report]
    try:
        paths = []
        for candidate in args.reports:
            paths.extend(sorted(candidate.rglob("*.sarif")) if candidate.is_dir() else [candidate])
        if not paths:
            raise InvalidReport("No scanner reports found")
        blocked = []
        for path in paths:
            blocked.extend(CHECKERS[args.scanner](read_report(path)))
        for finding in blocked:
            print(f"BLOCK: {finding}")
        print(
            f"{'FAIL' if blocked else 'PASS'}: {args.scanner}, {len(paths)} report(s), "
            f"{len(blocked)} blocking finding(s)"
        )
        return 1 if blocked else 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"ERROR: Security scan could not be verified: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
