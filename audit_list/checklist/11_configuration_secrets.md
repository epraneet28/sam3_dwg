---
## Metadata
**Priority Level:** P2 (Medium)
**Original Audit:** #8 Configuration & Secrets
**Last Updated:** 2025-12-26
**AI/Vibe-Coding Risk Level:** HIGH

---

# Configuration & Secrets Audit Prompt (Production-Ready, Security-First)

## Role
Act as a Senior Security Engineer and DevOps Architect. Perform a comprehensive Configuration & Secrets Audit on the provided codebase to identify misconfigurations, exposed secrets, and configuration drift that could lead to security breaches or operational failures.

## Primary Goal
Identify where AI-generated code has introduced insecure defaults, hardcoded secrets, configuration anti-patterns, and environment-specific assumptions that will fail in production or expose sensitive data.

## Context
- This code was developed with AI assistance ("vibecoded") and may contain configuration shortcuts, placeholder secrets, or assumptions about environment that don't hold in production.
- I need you to find all configuration vulnerabilities before deploying to production.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn
- Document Processing: Docling engine
- Data Validation: Pydantic v2
- Database: SQLite3
- Image Processing: OpenCV, Pillow, pdf2image
- External Integration: Label Studio SDK
- Real-time: WebSockets
- Frontend: React 19 + TypeScript 5.9 + Vite 7
- State Management: Zustand
- Styling: Tailwind CSS 4
- Infrastructure: Docker (Python 3.11-slim-bookworm)

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
Focus on: `.env*` files, `settings.py`, `config.py`, Docker files, frontend env handling, and any file importing `os.environ` or `process.env`.

## Environment & Assumptions (you must do this first)
1) Inventory all configuration sources:
   - Environment variables (backend and frontend)
   - Config files (Python settings, TypeScript configs)
   - Docker environment
   - Hardcoded values in source code
   - Default values in Pydantic models

2) Map configuration flow:
   - How do env vars flow from Docker → Backend → Frontend?
   - What's the secret injection mechanism?
   - Are there environment-specific configs (dev/staging/prod)?

3) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation.

---

## 1) Secret Exposure & Hardcoding

### A) Hardcoded Secrets in Source Code
- API keys, tokens, passwords embedded directly in Python/TypeScript files.
- Common patterns: `api_key = "sk-..."`, `password = "admin123"`, `token = "..."`.
- **Stack-specific**: Label Studio API tokens, any Docling license keys, database credentials.
- Suggested Fix: Move to environment variables, use secret management (Vault, AWS Secrets Manager).

### B) Secrets in Version Control
- `.env` files committed to git (check `.gitignore`).
- Secrets in docker-compose.yml or Dockerfile.
- Config files with real credentials in repo.
- **Stack-specific**: Check for Label Studio URLs with embedded tokens, file paths exposing system structure.
- Suggested Fix: Use `.env.example` with placeholders, add to `.gitignore`, use secret injection at runtime.

### C) Secrets in Frontend Bundle
- Environment variables exposed to browser via Vite's `VITE_*` prefix.
- API keys bundled into JavaScript.
- Backend URLs with credentials in query strings.
- **Stack-specific**: Any Label Studio or processing API keys accessible from frontend.
- Suggested Fix: Never expose secrets to frontend; use backend proxy for authenticated services.

### D) Secrets in Logs or Error Messages
- Logging configuration values including secrets.
- Stack traces exposing environment variables.
- Error responses leaking internal paths or credentials.
- **Stack-specific**: Document paths, checkpoint locations, Label Studio connection strings.
- Suggested Fix: Redact sensitive fields in logs, use structured logging with field filtering.

---

## 2) Environment Variable Handling

### A) Missing Required Environment Variables
- App crashes on startup due to missing env vars.
- No validation of required configuration at startup.
- Silent failures when optional configs are missing.
- **Stack-specific**: `LABEL_STUDIO_URL`, `LABEL_STUDIO_API_KEY`, storage paths, DPI settings.
- Suggested Fix: Validate all required env vars at startup with clear error messages; use Pydantic Settings.

### B) Type Coercion Errors
- Environment variables not properly cast (string "false" treated as truthy).
- Integer configs parsed incorrectly.
- Boolean handling inconsistencies.
- **Stack-specific**: `PDF_IMAGE_DPI` must be integer, feature flags, port numbers.
- Suggested Fix: Use Pydantic Settings with proper type annotations and validators.

### C) Default Value Dangers
- Insecure defaults (DEBUG=True, allow_origins="*", etc.).
- Development defaults in production code.
- Fallback values that mask missing configuration.
- **Stack-specific**: CORS origins, file upload limits, WebSocket origins.
- Suggested Fix: Fail-safe defaults; require explicit production configuration.

### D) Environment Variable Namespace Pollution
- Generic variable names that could conflict (`API_KEY`, `DEBUG`, `PORT`).
- No prefix convention for app-specific vars.
- **Stack-specific**: Should use `DOCLING_*` or `DI_*` prefix for all app vars.
- Suggested Fix: Prefix all application environment variables consistently.

---

## 3) Configuration Drift & Consistency

### A) Dev/Prod Configuration Parity
- Features enabled in dev but disabled in prod (or vice versa).
- Different database configurations between environments.
- Missing environment-specific overrides.
- **Stack-specific**: SQLite path differences, Label Studio URLs per environment.
- Suggested Fix: Document all environment differences; use configuration schema validation.

### B) Frontend/Backend Configuration Mismatch
- API URLs hardcoded differently in frontend and backend.
- Feature flags not synchronized.
- Timeout values inconsistent.
- **Stack-specific**: WebSocket URLs, file upload size limits, supported file types.
- Suggested Fix: Single source of truth for shared configuration; API endpoint for frontend config.

### C) Docker vs Local Configuration Drift
- Paths that work locally but fail in Docker.
- Volume mounts not matching expected paths.
- Environment variables set in docker-compose but not in local dev.
- **Stack-specific**: Checkpoint storage paths, uploaded file directories, temp file locations.
- Suggested Fix: Use identical environment variable names; document path expectations.

### D) Configuration Schema Validation
- No validation that configuration values are within acceptable ranges.
- Missing configuration documentation.
- No way to dump current effective configuration.
- **Stack-specific**: DPI values (72, 144, 216), file size limits, pagination defaults.
- Suggested Fix: Pydantic Settings with validators; config dump endpoint (non-secrets).

---

## 4) Pydantic Settings Best Practices

### A) Settings Class Structure
- Multiple scattered settings without central management.
- Settings instantiated multiple times (not singleton).
- Circular imports with settings.
- **Stack-specific**: Document processing settings, Label Studio settings, storage settings.
- Suggested Fix: Single Settings class with nested models; dependency injection pattern.

### B) Secrets Field Handling
- Using `str` instead of `SecretStr` for sensitive fields.
- Secrets serialized in JSON responses or logs.
- No distinction between public and private config.
- **Stack-specific**: Label Studio API key, any authentication tokens.
- Suggested Fix: Use `SecretStr` for all secrets; implement `__repr__` that masks values.

### C) Environment File Loading
- Incorrect `.env` file loading order.
- Missing support for `.env.local` overrides.
- Production `.env` files not validated.
- Suggested Fix: Clear precedence: defaults < .env < .env.local < environment < CLI.

### D) Configuration Reloading
- No way to reload configuration without restart.
- Stale configuration cached indefinitely.
- **Stack-specific**: Label Studio connection settings, processing parameters.
- Suggested Fix: Document which configs require restart; consider hot-reload for safe configs.

---

## 5) Docker & Container Configuration

### A) Dockerfile Security
- Running as root.
- Secrets passed as build args (cached in layers).
- Sensitive files copied into image.
- **Stack-specific**: Any model files, configuration with secrets.
- Suggested Fix: Use non-root user; multi-stage builds; runtime secret injection.

### B) Docker Compose Secrets
- Secrets in `environment:` section (visible in `docker inspect`).
- No use of Docker secrets or external secret management.
- Suggested Fix: Use Docker secrets, external secret files, or orchestrator secret management.

### C) Volume Mount Security
- Overly permissive volume mounts.
- Host paths exposed to container.
- Writable mounts that should be read-only.
- **Stack-specific**: Checkpoint directories, upload directories, database files.
- Suggested Fix: Principle of least privilege; use `:ro` where possible.

### D) Environment File Handling in Compose
- `.env` file with secrets committed or not in `.gitignore`.
- No `.env.example` template.
- Inconsistent variable naming between compose and app.
- Suggested Fix: `.env.example` with all variables documented; `.env` in `.gitignore`.

---

## 6) Path & File System Configuration

### A) Absolute vs Relative Path Issues
- Hardcoded absolute paths that differ between environments.
- Relative paths that break when CWD changes.
- Path separators that fail on different OS.
- **Stack-specific**: Checkpoint paths, upload directories, temp file locations.
- Suggested Fix: Use `pathlib.Path`; configuration for base directories; `os.path.join`.

### B) Directory Creation & Permissions
- Assuming directories exist without creation.
- No permission checks on startup.
- Race conditions in directory creation.
- **Stack-specific**: `checkpoints/`, `uploads/`, `temp/` directories.
- Suggested Fix: Create directories on startup with proper permissions; atomic operations.

### C) Temporary File Handling
- Hardcoded `/tmp` paths.
- No cleanup of temporary files.
- Predictable temp file names (security risk).
- **Stack-specific**: PDF processing temp files, image extraction intermediates.
- Suggested Fix: Use `tempfile` module; cleanup in `finally` blocks; configurable temp directory.

### D) Storage Path Security
- Path traversal vulnerabilities in user-provided paths.
- Symlink following that escapes intended directories.
- **Stack-specific**: Document IDs used in paths, checkpoint file names.
- Suggested Fix: Validate and sanitize all path components; use `os.path.realpath` checks.

---

## 7) External Service Configuration

### A) Label Studio Integration
- Hardcoded Label Studio URLs.
- API key handling and rotation strategy.
- Connection timeout configuration.
- SSL/TLS verification settings.
- **Stack-specific**: Project IDs, annotation schemas, export formats.
- Suggested Fix: All connection params configurable; secure credential storage; health checks.

### B) WebSocket Configuration
- Origin validation settings.
- Connection limits.
- Timeout and keepalive settings.
- **Stack-specific**: Frontend WebSocket URL matching backend; reconnection configuration.
- Suggested Fix: Strict origin checking in production; configurable limits; proper handshake.

### C) CORS Configuration
- Overly permissive `allow_origins=["*"]` in production.
- Missing credentials handling.
- Inconsistent header exposure.
- Suggested Fix: Explicit origin whitelist; environment-specific CORS config.

### D) Rate Limiting & Throttling Configuration
- Missing or disabled rate limits.
- Hardcoded limits not configurable.
- No per-route limit configuration.
- **Stack-specific**: Upload rate limits, processing queue limits.
- Suggested Fix: Configurable rate limits per endpoint; consider Redis-backed limiter.

---

## 8) Vibe Code Specific Configuration Pitfalls

### A) AI-Generated Default Values
- Placeholder values left in code ("your-api-key-here", "changeme", "TODO").
- Example values that look real but aren't.
- Copy-pasted configuration from tutorials.
- Suggested Fix: Grep for common placeholder patterns; require explicit configuration.

### B) Assumed Environment
- Code assuming specific directory structure.
- Hardcoded ports without configuration.
- Platform-specific assumptions (Linux paths in Windows, etc.).
- **Stack-specific**: Docling model paths, system library locations.
- Suggested Fix: Make all paths configurable; document system requirements.

### C) Missing Configuration Documentation
- No documentation of required environment variables.
- No example configuration files.
- No configuration validation or startup checks.
- Suggested Fix: Generate config docs from Pydantic models; comprehensive `.env.example`.

### D) Feature Flags Without Controls
- Features toggled by code changes instead of configuration.
- No way to disable features without deployment.
- Debug features accidentally enabled.
- **Stack-specific**: Label Studio integration toggle, OCR engine selection.
- Suggested Fix: Configuration-driven feature flags; runtime toggle capability.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | LOW]

Location: FileName : Line Number(s)
Risk Category: Secret Exposure | Env Handling | Config Drift | Docker | Path Security | External Service | Vibe Code

The Problem:
- 2-4 sentences explaining the security or operational risk.
- Be specific about failure mode: secret leak, config crash, environment mismatch, path traversal, etc.

Security/Operational Impact:
- Describe the potential damage (credential theft, data exposure, service unavailability).
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (grep for pattern, check git history, review Docker inspect, test startup without var).

The Fix:
- Provide the secure configuration pattern.
- Show before/after if useful.
- Include any migration steps needed.

Trade-off Consideration:
- Note complexity vs security benefit.
- If acceptable in dev but not prod, mark environments clearly.
```

## Severity Classification
- **CRITICAL**: Active secret exposure, credentials in version control, no auth on admin endpoints.
- **HIGH**: Insecure defaults in production, missing required configuration validation, path traversal risks.
- **MEDIUM**: Configuration drift issues, missing documentation, suboptimal secret handling.
- **LOW**: Best practice improvements, code organization, documentation gaps.

---

## Configuration Security Score Rubric (1-10)

Rate overall configuration security based on severity/quantity:
- **9-10**: Production-ready configuration; secrets properly managed; comprehensive validation.
- **7-8**: Minor issues; 1-2 items need attention before production.
- **5-6**: Significant gaps; secrets may be exposed; configuration needs restructuring.
- **3-4**: Multiple critical issues; likely secret exposure or misconfigurations.
- **<3**: Secrets actively exposed; fundamental configuration architecture issues.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest security impact first)

## Final Section: Summary & Action Plan (Mandatory)

### 1) Fix Immediately (Security Critical)
- Items that could lead to immediate security breach or data exposure.

### 2) Fix Before Production
- Configuration issues that would cause failures or security weaknesses in production.

### 3) Improve (Best Practices)
- Recommendations for configuration management maturity.

## Also Include:

### Configuration Inventory
Create a table of all discovered configuration points:

| Variable/Setting | Source | Required | Has Default | Sensitive | Validated |
|-----------------|--------|----------|-------------|-----------|-----------|
| LABEL_STUDIO_API_KEY | env | Yes | No | Yes | ? |
| PDF_IMAGE_DPI | env | No | Yes (150) | No | ? |

### Recommended `.env.example` Template
Generate a complete `.env.example` file with:
- All required variables with placeholder values
- All optional variables with sensible defaults
- Comments explaining each variable
- Grouping by functional area

### Startup Validation Checklist
Code snippet for startup configuration validation:
```python
# Example validation that should exist
def validate_configuration():
    """Validate all required configuration at startup."""
    errors = []
    # Check required env vars
    # Validate paths exist and are writable
    # Test external service connectivity
    # Verify secrets are not placeholder values
    if errors:
        raise ConfigurationError(errors)
```
