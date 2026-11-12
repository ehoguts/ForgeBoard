# Phase 2 dependency and image findings

Scanner findings below describe installed packages, not independently demonstrated remote application exploits. Counts are report occurrences and may repeat the same CVE across packages.

## Remediated blocking findings

| Image | Initial HIGH / CRITICAL | Correction | Final HIGH / CRITICAL |
| --- | --- | --- | --- |
| Backend | 49 / 0 | Replace Debian utility-heavy base with digest-pinned Python Alpine; apply OS patches; preserve constrained dependency versions and test both database engines | 0 / 0 |
| Frontend | 9 / 0 | Node 24.22.1 pinned base, Alpine patches, globally bundled npm updated to 12.2.2 | 0 / 0 |
| Database | 44 / 1 | PostgreSQL 16.16 pinned base and patches; replace old Go gosu with su-exec in all upstream initialization scripts and remove the old binary | 0 / 0 |

Representative advisories: [musl regcomp](https://www.openwall.com/lists/musl/2026/10/21/1), [brace-expansion](https://github.com/juliangruber/brace-expansion/security/advisories/GHSA-qhr7-859c-m2p7), [undici TLS options](https://github.com/nodejs/undici/security/advisories/GHSA-2m5v-pch6-74hx). The affected npm packages were in the image global npm tree, so application npm audit alone did not cover them.

No ignore list, severity downgrade, ignore-unfixed flag, or blanket exception was used. The initial PostgreSQL image also contained vulnerable Go stdlib metadata in gosu; removing that executable rather than leaving a same-path symlink ensures the image scanner sees the actual removal. Fresh initialization and an existing-volume Compose restart were tested.

## Remaining below-threshold findings

Owner: repository maintainer (ehoguts). Review by 2026-12-12, and rerun the weekly Security workflow. These findings remain visible; they are allowed by the documented threshold rather than suppressed. Development tools execute trusted developer/PR code in local or ephemeral CI contexts, and this project has no public production service. Reassess reachability before exposing it.

### Image reports

| Image | Advisory | Package / installed | Severity | Fixed version reported |
| --- | --- | --- | --- | --- |
| backend | CVE-2025-8869 | pip 25.0.1 | MEDIUM | 25.3 |
| backend | CVE-2026-13346 | pip 25.0.1 | MEDIUM | 26.2.0 |
| backend | CVE-2026-3219 | pip 25.0.1 | MEDIUM | 26.1 |
| backend | CVE-2026-6357 | pip 25.0.1 | MEDIUM | 26.1 |
| backend | CVE-2026-8643 | pip 25.0.1 | MEDIUM | 26.1.2 |
| backend | CVE-2026-1703 | pip 25.0.1 | LOW | 26.0 |
| frontend | CVE-2026-118773 | glob 13.0.6 | MEDIUM | 14.0.2 |
| frontend | CVE-2026-118764 | minimatch 10.2.5 | MEDIUM | 11.0.1 |
| frontend | CVE-2026-118764 | minimatch 10.2.6 | MEDIUM | 11.0.1 |

### npm report

The complete application/development graph reported 10 moderate entries and zero high/critical entries. Advisory chains can count the same root advisory against several dependent packages.

| Package | Severity | Fix proposed by npm |
| --- | --- | --- |
| @eslint/config-array | moderate | {'name': 'eslint', 'version': '9.39.5', 'isSemVerMajor': True} |
| @eslint/js | moderate | {'name': '@eslint/js', 'version': '9.39.5', 'isSemVerMajor': True} |
| @typescript-eslint/eslint-plugin | moderate | {'name': 'typescript-eslint', 'version': '8.36.0', 'isSemVerMajor': True} |
| @typescript-eslint/parser | moderate | {'name': 'typescript-eslint', 'version': '8.36.0', 'isSemVerMajor': True} |
| @typescript-eslint/type-utils | moderate | {'name': 'typescript-eslint', 'version': '8.36.0', 'isSemVerMajor': True} |
| @typescript-eslint/typescript-estree | moderate | {'name': 'typescript-eslint', 'version': '8.36.0', 'isSemVerMajor': True} |
| @typescript-eslint/utils | moderate | {'name': 'typescript-eslint', 'version': '8.36.0', 'isSemVerMajor': True} |
| eslint | moderate | {'name': 'eslint', 'version': '9.39.5', 'isSemVerMajor': True} |
| minimatch | moderate | {'name': 'eslint', 'version': '9.39.5', 'isSemVerMajor': True} |
| typescript-eslint | moderate | {'name': 'typescript-eslint', 'version': '8.36.0', 'isSemVerMajor': True} |

Python pip-audit reported no known vulnerabilities in the resolved constrained application/development requirements. Image and npm severities differ by advisory source and package coverage; their counts must not be combined into a unique-vulnerability total.
