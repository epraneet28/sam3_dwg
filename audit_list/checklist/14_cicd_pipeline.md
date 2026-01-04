---
## Metadata
**Priority Level:** P2 (Medium)
**Original Audit:** #19 CI/CD Pipeline
**Last Updated:** 2025-12-26
**AI/Vibe-Coding Risk Level:** MEDIUM

---

# CI/CD Pipeline Audit Prompt (Production-Ready, Reproducible Builds)

## Role
Act as a Senior DevOps Engineer and Release Manager. Perform a comprehensive CI/CD Pipeline Audit on the provided codebase and pipeline configuration to ensure reliable, secure, and efficient software delivery.

## Primary Goal
Identify gaps in build reproducibility, quality gates, security scanning, and deployment safety that could lead to broken releases, security incidents, or production instability.

## Context
- This code was developed with a focus on speed ("vibecoded") and may lack mature CI/CD practices.
- I need you to audit the pipeline for reliability, security, and operational excellence before production deployment.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn
- Document Processing: Docling, OpenCV, Pillow, pdf2image
- Database: SQLite3
- Frontend: React 19 + TypeScript 5.9 + Vite 7 + Tailwind CSS 4
- Testing: pytest, Playwright
- Linting: Ruff, Black, MyPy, ESLint
- Infrastructure: Docker (Python 3.11-slim-bookworm)
- Real-time: WebSockets

## Files to Analyze
Examine the following (if present):
- `.github/workflows/*.yml` or `.gitlab-ci.yml` or `Jenkinsfile`
- `Dockerfile`, `docker-compose.yml`
- `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`
- `package.json`, `package-lock.json`
- `playwright.config.ts`, `pytest.ini`, `conftest.py`
- `.eslintrc.*`, `ruff.toml`, `mypy.ini`
- Any deployment scripts, `Makefile`, or `justfile`

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - CI/CD platform (GitHub Actions, GitLab CI, Jenkins, etc.)
   - Deployment target (container registry, Kubernetes, VM, serverless)
   - Environment strategy (dev, staging, prod separation)
   - Secret management approach (env vars, vault, sealed secrets)
   - Branch strategy (trunk-based, GitFlow, feature branches)
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation.

---

## 1) Build Reproducibility & Artifact Integrity

### A) Dependency Pinning
- Check for unpinned dependencies in `requirements.txt` (e.g., `requests` vs `requests==2.31.0`)
- Verify `package-lock.json` or `pnpm-lock.yaml` is committed and used in CI
- Flag floating version ranges (`^`, `~`, `>=`) in production dependencies
- **Stack-specific**: Ensure Docling, OpenCV, Pillow versions are pinned (these have breaking changes)
- Suggested Fix: Pin all production dependencies to exact versions; use lockfiles

### B) Docker Build Determinism
- Check for `apt-get update` without `apt-get install` in same RUN (cache invalidation)
- Flag `COPY . .` before dependency install (breaks layer caching)
- Verify multi-stage builds separate build from runtime
- **Stack-specific**: System libraries (libgl1, poppler-utils) should be version-pinned
- Suggested Fix: Order Dockerfile for optimal caching; use specific base image tags

### C) Build Cache Efficiency
- Identify missing cache configuration for pip, npm, Docker layers
- Flag builds that download dependencies on every run
- **Stack-specific**: Docling models should be cached (large downloads)
- Suggested Fix: Configure CI caching for `.cache/pip`, `node_modules`, Docker layers

### D) Artifact Versioning & Provenance
- Check for semantic versioning or commit-based tagging
- Verify Docker images are tagged with commit SHA, not just `latest`
- Flag missing build metadata (commit, branch, timestamp)
- Suggested Fix: Tag images with `git rev-parse --short HEAD`; add BUILD_INFO labels

---

## 2) Quality Gates & Testing

### A) Linting Gates (Python)
- Verify Ruff/Black/MyPy run in CI and block merge on failure
- Check for ignored rules without justification
- Flag missing type checking (`mypy --strict` or equivalent)
- **Stack-specific**: Pydantic v2 requires specific mypy plugins
- Suggested Fix: Add `ruff check . --fix --exit-non-zero-on-fix` to CI

### B) Linting Gates (TypeScript/React)
- Verify ESLint runs with `--max-warnings=0`
- Check for disabled rules (`// eslint-disable-next-line` abuse)
- Flag missing strict TypeScript config (`strict: true`, `noImplicitAny`)
- Suggested Fix: Configure `eslint --max-warnings=0` as blocking step

### C) Unit Test Coverage
- Check for pytest coverage thresholds (e.g., `--cov-fail-under=80`)
- Verify coverage report is generated and stored as artifact
- Flag missing tests for critical paths (pipeline stages, checkpoint handling)
- **Stack-specific**: Docling processing should have mocked fixtures
- Suggested Fix: Add `pytest --cov=backend --cov-fail-under=80`

### D) Integration & E2E Test Gates
- Verify Playwright tests run in CI with proper browser setup
- Check for flaky test handling (retries, stable selectors)
- Flag missing test isolation (shared state between tests)
- **Stack-specific**: Test all 15 pipeline stages; mock Label Studio
- Suggested Fix: Configure Playwright with `retries: 2`, stable test IDs

### E) Test Parallelization & Speed
- Check if tests run in parallel (`pytest -n auto`, Playwright sharding)
- Flag sequential test runs that could be parallelized
- Identify slow tests (>30s) that should be optimized or split
- Suggested Fix: Use `pytest-xdist` and Playwright `--shard`

---

## 3) Security Scanning

### A) Dependency Vulnerability Scanning
- Verify `pip-audit` or `safety` runs for Python dependencies
- Verify `npm audit` runs for Node.js dependencies
- Check for CRITICAL/HIGH vulnerabilities blocking merge
- **Stack-specific**: Pillow, OpenCV, pdf2image have frequent CVEs
- Suggested Fix: Add `pip-audit --strict` and `npm audit --audit-level=high`

### B) Static Application Security Testing (SAST)
- Check for SAST tools (Bandit for Python, ESLint security plugin)
- Flag hardcoded secrets, SQL injection patterns, path traversal
- **Stack-specific**: PDF processing has high injection risk
- Suggested Fix: Add `bandit -r backend -ll` to CI

### C) Container Security Scanning
- Verify container images are scanned (Trivy, Snyk, Grype)
- Check for base image vulnerabilities
- Flag running as root, missing security contexts
- **Stack-specific**: Python-slim may have unpatched CVEs
- Suggested Fix: Add `trivy image --severity HIGH,CRITICAL --exit-code 1`

### D) Secrets Detection
- Verify pre-commit hooks or CI steps scan for leaked secrets
- Check for `.env` files in git history
- Flag patterns like API keys, passwords, tokens in code
- Suggested Fix: Add `gitleaks detect --source . --exit-code 1`

### E) License Compliance
- Check for license scanning (FOSSA, License Finder)
- Flag copyleft licenses (GPL) in proprietary projects
- **Stack-specific**: Docling dependencies may have license restrictions
- Suggested Fix: Add license audit step; maintain approved license list

---

## 4) Environment Promotion & Deployment Safety

### A) Environment Parity
- Verify dev, staging, prod use identical Docker images
- Flag environment-specific code paths (if env == 'prod')
- Check for config drift between environments
- Suggested Fix: Use identical images; inject config via env vars only

### B) Database Migration Safety
- Check for migration versioning and rollback capability
- Flag destructive migrations without confirmation gates
- Verify migrations run before application deployment
- **Stack-specific**: SQLite migrations should be tested in CI
- Suggested Fix: Alembic/migration tool with `--sql` preview

### C) Rollback Capability
- Verify deployment can rollback to previous version
- Check for blue-green or canary deployment support
- Flag deployments without health check validation
- Suggested Fix: Implement rolling deployment with health gates

### D) Feature Flags & Progressive Rollout
- Check for feature flag system for risky changes
- Flag direct-to-prod deployments of major features
- Suggested Fix: Implement feature flags for new pipeline stages

### E) Manual Approval Gates
- Verify prod deployments require manual approval
- Check for separation of duties (deployer ≠ approver)
- Flag automated prod deployments without gates
- Suggested Fix: Add GitHub environment protection rules

---

## 5) Pipeline Reliability & Observability

### A) Pipeline Timeouts
- Check for job-level timeouts (prevent runaway builds)
- Flag missing step timeouts for network operations
- **Stack-specific**: Playwright tests need generous timeouts
- Suggested Fix: Set `timeout-minutes: 30` per job; 60 for E2E

### B) Retry Logic & Flaky Step Handling
- Check for retry configuration on flaky steps (network, E2E)
- Flag tests marked `skip` without issue reference
- **Stack-specific**: Playwright with browsers can be flaky
- Suggested Fix: Configure `retry: 2` for E2E jobs; fix root causes

### C) Failure Notification
- Verify pipeline failures trigger notifications (Slack, email)
- Check for on-failure hooks and alerting
- Flag silent failures in non-critical jobs
- Suggested Fix: Add Slack/email notification on failure

### D) Pipeline Metrics & Dashboards
- Check for build time tracking and trends
- Flag missing metrics on test flakiness, build duration
- Suggested Fix: Export to Datadog/Prometheus; track p50/p95 build times

### E) Dependency Update Automation
- Check for Dependabot/Renovate configuration
- Verify automated PRs for security updates
- Flag stale dependencies (>6 months without update)
- Suggested Fix: Enable Dependabot with weekly schedule

---

## 6) Docker & Container Best Practices

### A) Image Size Optimization
- Check for unnecessary files in final image
- Flag missing `.dockerignore` or incomplete exclusions
- **Stack-specific**: Exclude test fixtures, checkpoints, node_modules
- Suggested Fix: Multi-stage build; copy only runtime artifacts

### B) Non-Root User
- Verify container runs as non-root user
- Flag missing `USER` directive in Dockerfile
- Suggested Fix: Add `RUN useradd -m app && USER app`

### C) Health Checks
- Verify `HEALTHCHECK` directive in Dockerfile
- Check for liveness/readiness probes if Kubernetes
- **Stack-specific**: Health check should verify Docling initialization
- Suggested Fix: Add `HEALTHCHECK CMD curl -f http://localhost:8000/health`

### D) Resource Limits
- Check for CPU/memory limits in docker-compose or k8s manifests
- **Stack-specific**: Image processing needs significant memory
- Suggested Fix: Set `mem_limit: 4g` for processing containers

---

## 7) Stack-Specific CI/CD Considerations

### A) Python Virtual Environment Handling
- Verify venv creation is cached in CI
- Check for Poetry/PDM lock file usage
- Flag pip install without `--no-cache-dir` in Docker
- Suggested Fix: Cache `.venv` between CI runs

### B) Vite Build Optimization
- Check for production build flags (`vite build`)
- Verify source maps are disabled in production
- Flag missing minification or tree-shaking
- Suggested Fix: Ensure `NODE_ENV=production` during build

### C) Playwright Browser Installation
- Verify browser binaries are cached in CI
- Check for `npx playwright install --with-deps` in CI
- Flag headless mode issues with different CI runners
- Suggested Fix: Use Playwright Docker image or cache browsers

### D) Docling Model Caching
- Verify ML models are cached (not downloaded each build)
- Flag large model downloads in CI pipeline
- **Stack-specific**: TableFormer, LayoutModel are large
- Suggested Fix: Pre-pull models in Docker build or cache in CI

### E) SQLite in CI
- Verify SQLite database is isolated per test run
- Check for proper cleanup between tests
- Flag shared database state between parallel tests
- Suggested Fix: Use in-memory SQLite or temp directories

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | LOW]

Location: File path or CI configuration section
Risk Category: Build | Testing | Security | Deployment | Reliability | Container

The Problem:
- 2-4 sentences explaining the risk and potential impact.
- Be specific about failure mode: broken builds, security breach, failed deployment, etc.

Impact:
- Describe the consequences (example: "Unpinned deps could break prod after working in staging")
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (run command, check config, test scenario).

The Fix:
- Provide the configuration snippet or code change.
- Show before/after if useful.

Trade-off Consideration:
- Note complexity, maintenance burden, or slowdown trade-offs.
```

## Severity Classification
- **CRITICAL**: Will cause production incidents, security breaches, or data loss.
- **HIGH**: Will cause deployment failures, significant delays, or compliance issues.
- **MEDIUM**: Will cause operational friction or minor security exposure.
- **LOW**: Best practice improvement; current state is functional but suboptimal.

---

## CI/CD Maturity Score Rubric (1-10)

Rate overall CI/CD maturity:
- **9-10**: Production-grade pipeline with comprehensive gates, security, and automation.
- **7-8**: Good foundation; needs 1-2 enhancements for production readiness.
- **5-6**: Basic pipeline; significant gaps in testing, security, or deployment safety.
- **3-4**: Minimal automation; manual steps, missing quality gates.
- **<3**: No CI/CD or fundamentally broken; manual deployments only.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (before production deployment)
2) Fix Soon (next sprint)
3) Implement Later (continuous improvement)

## Also Include:
- Estimated time to implement all Fix Now items
- Recommended pipeline stages in order:
  ```
  1. Checkout & Cache Setup
  2. Lint (Ruff, ESLint, MyPy)
  3. Security Scan (pip-audit, npm audit, Bandit, gitleaks)
  4. Unit Tests (pytest with coverage)
  5. Build (Docker multi-stage)
  6. Container Scan (Trivy)
  7. E2E Tests (Playwright)
  8. Push to Registry (with SHA tag)
  9. Deploy to Staging (automatic)
  10. Deploy to Production (manual approval)
  ```

## Example GitHub Actions Workflow Structure

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: '3.12'
  NODE_VERSION: '20'

jobs:
  lint-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: pip install ruff black mypy
      - run: ruff check . --exit-non-zero-on-fix
      - run: black --check .
      - run: mypy backend --strict

  lint-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run lint -- --max-warnings=0
      - run: npm run type-check

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pip-audit bandit
      - run: pip-audit --strict -r requirements.txt
      - run: bandit -r backend -ll
      - run: npm audit --audit-level=high
      - uses: gitleaks/gitleaks-action@v2

  test-backend:
    runs-on: ubuntu-latest
    needs: [lint-python, security-scan]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest --cov=backend --cov-fail-under=80 --cov-report=xml
      - uses: codecov/codecov-action@v4

  test-e2e:
    runs-on: ubuntu-latest
    needs: [lint-frontend]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run build
      - run: npx playwright test
        env:
          CI: true

  build-and-push:
    runs-on: ubuntu-latest
    needs: [test-backend, test-e2e]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.sha }}
            ghcr.io/${{ github.repository }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  container-scan:
    runs-on: ubuntu-latest
    needs: [build-and-push]
    steps:
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: ghcr.io/${{ github.repository }}:${{ github.sha }}
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

  deploy-staging:
    runs-on: ubuntu-latest
    needs: [container-scan]
    environment: staging
    steps:
      - run: echo "Deploy to staging"

  deploy-production:
    runs-on: ubuntu-latest
    needs: [deploy-staging]
    environment: production
    steps:
      - run: echo "Deploy to production"
```

## Checklist Summary

### Build Reproducibility
- [ ] All Python dependencies pinned to exact versions
- [ ] package-lock.json committed and used in CI
- [ ] Docker base image uses specific tag (not `latest`)
- [ ] Build artifacts tagged with commit SHA
- [ ] CI caching configured for pip, npm, Docker layers

### Quality Gates
- [ ] Ruff/Black/MyPy block merge on failure
- [ ] ESLint runs with `--max-warnings=0`
- [ ] pytest coverage threshold enforced (≥80%)
- [ ] Playwright E2E tests run in CI
- [ ] Tests parallelized for speed

### Security Scanning
- [ ] pip-audit runs on Python dependencies
- [ ] npm audit runs on Node dependencies
- [ ] Bandit SAST for Python code
- [ ] gitleaks for secrets detection
- [ ] Trivy scans container images

### Deployment Safety
- [ ] Environment parity (same image in staging/prod)
- [ ] Manual approval for production deploys
- [ ] Health checks configured
- [ ] Rollback capability documented
- [ ] Database migrations versioned

### Pipeline Reliability
- [ ] Job timeouts configured
- [ ] Retry logic for flaky steps
- [ ] Failure notifications enabled
- [ ] Dependabot/Renovate for updates

### Container Best Practices
- [ ] Multi-stage Docker build
- [ ] Non-root user in container
- [ ] .dockerignore configured
- [ ] Resource limits set
- [ ] HEALTHCHECK directive present
