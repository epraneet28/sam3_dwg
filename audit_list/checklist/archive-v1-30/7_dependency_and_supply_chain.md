# Dependency & Supply Chain Audit Prompt (Production-Ready)

## Role
Act as a Senior Security Engineer and Supply Chain Security Specialist. Perform a comprehensive Dependency & Supply Chain Audit on the provided codebase to identify vulnerabilities, outdated packages, and supply chain risks before production deployment.

## Primary Goal
Identify where AI-generated dependency choices, version pinning gaps, and transitive vulnerabilities create security or stability risks, and provide concrete remediation steps.

## Context
- This code was developed with AI assistance ("vibecoded") and may have accumulated dependencies without rigorous security review.
- I need you to find vulnerable packages, licensing conflicts, and supply chain risks before deploying to production.

## Tech Stack
- **Backend**: Python 3.12 + FastAPI + Uvicorn
- **Document Processing**: Docling, OpenCV, Pillow, pdf2image
- **Data**: Pydantic v2, SQLite3
- **Integration**: Label Studio SDK, WebSockets
- **Frontend**: React 19 + TypeScript 5.9 + Vite 7
- **Styling**: Tailwind CSS 4
- **State**: Zustand
- **Routing**: React Router DOM 7
- **Testing**: Playwright, pytest
- **Infrastructure**: Docker (Python 3.11-slim-bookworm)
- **Dev Tools**: ESLint, Ruff, Black, MyPy

## Files to Analyze
Analyze these files systematically:
- `requirements.txt` / `pyproject.toml` / `setup.py` (Python dependencies)
- `package.json` / `package-lock.json` (Node.js dependencies)
- `Dockerfile` / `docker-compose.yml` (Base images, build context)
- Any vendored or bundled third-party code

## Environment & Assumptions (you must do this first)
1) Identify and list:
   - Python package manager (pip/poetry/pipenv/uv)
   - Node package manager (npm/yarn/pnpm)
   - Lockfile presence and completeness
   - Docker base image version and source
   - Any private/internal package registries
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation.

---

## 1) Known Vulnerability Detection

### A) Python Package Vulnerabilities (pip-audit)
- Run conceptual `pip-audit` analysis on requirements.
- Flag packages with known CVEs in PyPI Advisory Database.
- High-risk packages for this stack: Pillow, OpenCV, pdf2image, requests, urllib3, cryptography.
- **Stack-specific**: Docling and its transitive dependencies (transformers, torch, numpy).
- Suggested Fix: Upgrade to patched versions, document accepted risks for unpatchable.

### B) Node.js Package Vulnerabilities (npm audit)
- Run conceptual `npm audit` analysis on package.json/lock.
- Flag packages with known CVEs in npm Advisory Database.
- High-risk packages for this stack: Vite dev server, React ecosystem, build tools.
- **Stack-specific**: Playwright (browser binaries), Tailwind (PostCSS plugins).
- Suggested Fix: Upgrade or replace vulnerable packages, use `npm audit fix`.

### C) Docker Base Image Vulnerabilities
- Identify base image: `python:3.11-slim-bookworm`.
- Check for known CVEs in base image (Debian packages, glibc, openssl).
- Flag if image tag is mutable (`:latest`, `:slim`) vs immutable digest.
- Suggested Fix: Pin to digest, use minimal images, run Trivy/Grype scan.

### D) Transitive Dependency Vulnerabilities
- Identify deep dependency chains that may harbor vulnerabilities.
- Flag when direct dependency pulls in vulnerable transitive dependency.
- Common culprits: protobuf, certifi, setuptools, pip itself.
- Suggested Fix: Override transitive versions, use dependency resolution tools.

---

## 2) Lockfile Hygiene & Reproducibility

### A) Missing or Incomplete Lockfiles
- Python: Check for `requirements.txt` with pinned versions OR `poetry.lock`/`pipenv.lock`.
- Node.js: Check for `package-lock.json` or `yarn.lock`.
- Flag unpinned dependencies (e.g., `requests>=2.0` without upper bound).
- Suggested Fix: Pin all direct dependencies, generate and commit lockfiles.

### B) Lockfile Drift & Staleness
- Check if lockfile matches declared dependencies.
- Flag if lockfile was last updated > 90 days ago.
- Identify orphaned dependencies in lockfile not in manifest.
- Suggested Fix: Regular `npm ci` / `pip-sync` in CI, automated lockfile updates.

### C) Version Pinning Strategy
- Flag packages with overly broad version ranges (`*`, `>=1.0`).
- Identify packages pinned to vulnerable versions.
- Check for `~=` vs `==` vs `>=` consistency in Python.
- Suggested Fix: Use `~=` for semver-compatible, exact pins for critical packages.

### D) Hash Verification
- Check if lockfiles include integrity hashes (npm) or hash mode (pip).
- Flag missing hash verification on critical packages.
- Suggested Fix: Enable `--require-hashes` for pip, verify `integrity` in npm lock.

---

## 3) Outdated Package Analysis

### A) Major Version Behind
- Identify packages > 1 major version behind latest.
- Flag packages with breaking changes between current and latest.
- **Stack-specific**: React 19 is newest - verify compatibility. Pydantic v2 has breaking changes from v1.
- Suggested Fix: Plan upgrade path, check changelogs for breaking changes.

### B) End-of-Life Dependencies
- Flag Python/Node versions approaching or past EOL.
- Identify packages with no releases in > 2 years.
- Check for archived/deprecated GitHub repos.
- Suggested Fix: Replace with actively maintained alternatives.

### C) Security-Critical Package Currency
- Prioritize currency for security-sensitive packages:
  - Python: cryptography, urllib3, requests, certifi, PyJWT
  - Node.js: jsonwebtoken, helmet, express (if used), axios
- Suggested Fix: Automated weekly security updates via Dependabot/Renovate.

### D) Framework Version Alignment
- Verify FastAPI + Pydantic v2 compatibility.
- Check React 19 + React Router 7 compatibility.
- Identify mismatched ecosystem versions.
- Suggested Fix: Align to tested version combinations.

---

## 4) Licensing & Compliance

### A) License Compatibility
- Scan all dependencies for license types.
- Flag GPL/AGPL licenses if shipping proprietary software.
- Identify LGPL licenses requiring dynamic linking awareness.
- **Stack-specific**: OpenCV (Apache 2.0), Pillow (HPND), Docling (check license).
- Suggested Fix: Generate SBOM with licenses, legal review for flagged items.

### B) License File Presence
- Check that all direct dependencies have LICENSE files.
- Flag packages with ambiguous or missing license declarations.
- Suggested Fix: Prefer packages with clear licensing, document exceptions.

### C) Commercial/Proprietary Dependencies
- Identify any non-OSS dependencies (fonts, icons, SDKs).
- Flag dependencies requiring commercial licenses for production.
- Suggested Fix: Audit commercial terms, ensure compliance.

### D) Attribution Requirements
- Identify packages requiring attribution (Apache 2.0, BSD, MIT).
- Check if NOTICE file aggregates required attributions.
- Suggested Fix: Generate attribution document, include in distribution.

---

## 5) Supply Chain Attack Surface

### A) Typosquatting Risk
- Check for misspelled package names in requirements.
- Flag packages with names similar to popular packages.
- Verify package ownership/maintainer reputation.
- Suggested Fix: Verify package URLs, use official documentation links.

### B) Maintainer Trust & Package Provenance
- Identify single-maintainer packages in critical path.
- Check for packages with recent maintainer changes.
- Flag packages with no GitHub/source link.
- **Stack-specific**: Docling maintainer status, Label Studio SDK provenance.
- Suggested Fix: Prefer well-maintained, multi-contributor projects.

### C) Build Provenance & Signing
- Check if Python packages are from PyPI (not arbitrary URLs).
- Verify npm packages are from official registry.
- Flag any `--extra-index-url` or custom registries.
- Suggested Fix: Use signed packages where available, verify checksums.

### D) Dependency Confusion Risk
- Check for internal/private package names that could be hijacked.
- Flag if using both public and private registries.
- Suggested Fix: Namespace private packages, use scoped packages.

### E) Post-Install Script Risks
- Identify packages with install scripts (npm `postinstall`, Python `setup.py`).
- Flag packages that download binaries at install time.
- **Stack-specific**: Playwright downloads browser binaries, torch downloads models.
- Suggested Fix: Audit install scripts, use offline install where possible.

---

## 6) Docker & Container Security

### A) Base Image Selection
- Verify minimal base image usage (slim/alpine vs full).
- Check for unnecessary packages in image.
- Flag if running as root.
- Suggested Fix: Use distroless or minimal images, run as non-root.

### B) Build-Time vs Runtime Dependencies
- Identify dev dependencies included in production image.
- Flag build tools (gcc, make) in runtime image.
- Suggested Fix: Multi-stage builds, separate builder and runtime stages.

### C) Image Layer Caching & Secrets
- Check for secrets exposed in image layers.
- Flag `.env` files copied into image.
- Verify `.dockerignore` excludes sensitive files.
- Suggested Fix: Use BuildKit secrets, multi-stage builds.

### D) System Package Updates
- Check if Dockerfile runs `apt-get update && upgrade`.
- Flag if system packages are not updated in image.
- Suggested Fix: Update system packages, scan image with Trivy.

---

## 7) AI-Generated Dependency Risks (Vibe Code Focus)

### A) Hallucinated Packages
- Check for packages that don't exist in PyPI/npm.
- Flag packages with zero downloads or very recent creation.
- Identify packages that AI may have "invented".
- Suggested Fix: Verify each package exists and is legitimate.

### B) Version Mismatch with AI Training Data
- AI may suggest package versions from its training cutoff.
- Flag packages at versions that no longer exist.
- Check for deprecated APIs being used.
- Suggested Fix: Verify versions against current registry, update to latest stable.

### C) Over-Dependency (Kitchen Sink)
- Identify packages that could be replaced with stdlib.
- Flag multiple packages solving same problem.
- Check for heavy dependencies used for simple tasks.
- **Stack-specific**: Is a full ML framework needed? Are all OpenCV modules used?
- Suggested Fix: Remove unused dependencies, prefer stdlib alternatives.

### D) Dev Dependencies in Production
- Flag test/dev packages in production requirements.
- Check for debug/profiling tools left in dependencies.
- Suggested Fix: Separate requirements-dev.txt, use optional dependencies.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | LOW]

Location: FileName : Package Name : Version
Risk Category: Vulnerability | Outdated | License | Supply Chain | Configuration

The Problem:
- 2-4 sentences explaining the specific risk.
- Be specific: CVE number, license type, attack vector, etc.

Security/Compliance Impact:
- What could go wrong: RCE, data breach, legal liability, supply chain compromise.
- Include Confidence: High | Medium | Low

How to Verify:
- Specific command to run (pip-audit, npm audit, license-checker, trivy).
- Link to CVE/advisory if applicable.

The Fix:
- Provide the exact version to upgrade to.
- Show before/after in requirements file.
- If package should be removed/replaced, specify alternative.

Trade-off Consideration:
- Note breaking changes, testing needed, rollback plan.
- If risk is acceptable, document acceptance criteria.
```

## Severity Classification
- **CRITICAL**: Known exploited vulnerability (KEV), RCE, auth bypass, active supply chain attack.
- **HIGH**: High CVSS (7.0+), GPL in proprietary, single-maintainer critical dependency.
- **MEDIUM**: Medium CVSS (4.0-6.9), outdated major version, license ambiguity.
- **LOW**: Low CVSS, minor version behind, cosmetic license issues.

---

## Supply Chain Security Score Rubric (1-10)

Rate overall supply chain health:
- **9-10**: All packages pinned, no known vulnerabilities, clear licensing, verified provenance.
- **7-8**: Minor vulnerabilities with patches available, good lockfile hygiene.
- **5-6**: Some high vulnerabilities, incomplete pinning, license review needed.
- **3-4**: Critical vulnerabilities, supply chain risks, significant remediation needed.
- **<3**: Active vulnerabilities, compromised packages, do not deploy.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 5 fixes list (highest risk first)

## Final Section: Summary & Action Plan (Mandatory)

### 1) Fix Immediately (before deployment)
- Critical vulnerabilities
- Known exploited vulnerabilities
- License violations

### 2) Fix Soon (within 1 week)
- High vulnerabilities
- Outdated critical packages
- Supply chain risks

### 3) Fix Later (next sprint)
- Medium vulnerabilities
- Lockfile cleanup
- Dependency consolidation

### 4) Ongoing Maintenance
- Automated scanning setup
- Update cadence
- Monitoring

## Also Include:
- Estimated remediation time for immediate fixes
- Recommended tooling setup:
  - Python: `pip-audit`, `safety`, `pipdeptree`, `liccheck`
  - Node.js: `npm audit`, `snyk`, `license-checker`, `depcheck`
  - Docker: `trivy`, `grype`, `docker scout`
  - CI Integration: Dependabot/Renovate config, SBOM generation
- Sample CI commands:
  ```bash
  # Python vulnerability scan
  pip-audit --require-hashes --strict

  # Node.js vulnerability scan
  npm audit --audit-level=high

  # Docker image scan
  trivy image --severity HIGH,CRITICAL myimage:tag

  # License check
  liccheck -s strategy.ini
  license-checker --summary --failOn "GPL;AGPL"

  # SBOM generation
  syft . -o spdx-json > sbom.json
  ```

---

## Appendix: High-Risk Packages for This Stack

### Python - Security Critical
| Package | Risk Area | Common CVEs |
|---------|-----------|-------------|
| Pillow | Image parsing | Buffer overflow, DoS |
| OpenCV | Image/video processing | Memory corruption |
| pdf2image | PDF parsing | Command injection |
| requests/urllib3 | HTTP client | SSRF, header injection |
| cryptography | Crypto | Side-channel, padding oracle |
| PyYAML | YAML parsing | Arbitrary code execution |
| lxml | XML parsing | XXE, billion laughs |
| numpy | Array operations | Buffer overflow |
| torch/transformers | ML models | Model poisoning, RCE |

### Node.js - Security Critical
| Package | Risk Area | Common CVEs |
|---------|-----------|-------------|
| vite | Dev server | Path traversal, SSRF |
| postcss | CSS processing | ReDoS |
| webpack | Bundling | Prototype pollution |
| axios | HTTP client | SSRF |
| lodash | Utilities | Prototype pollution |
| minimist | CLI parsing | Prototype pollution |

### Docker Base Image
| Image | Considerations |
|-------|----------------|
| python:3.11-slim-bookworm | Debian-based, regular security updates needed |
| node:20-alpine | Smaller attack surface, musl libc |
| distroless | Minimal, no shell, harder to debug |
