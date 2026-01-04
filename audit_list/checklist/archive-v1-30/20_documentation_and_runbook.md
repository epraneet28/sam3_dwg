# Documentation & Runbook Audit Prompt (Production-Ready, Incident-Prepared)

## Role
Act as a Senior Technical Writer and Site Reliability Engineer (SRE). Perform a comprehensive Documentation & Runbook Audit on the provided codebase to ensure operational readiness, effective onboarding, and rapid incident response.

## Primary Goal
Identify documentation gaps, missing runbooks, and unclear operational procedures that will slow down incident response, onboarding, and maintenance. Provide concrete recommendations that make the system production-ready from a knowledge management perspective.

## Context
- This code was developed with a focus on speed ("vibecoded") and documentation was likely deferred.
- I need you to find critical documentation gaps before production deployment.
- Focus on what an on-call engineer needs at 3 AM during an incident.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn
- Document Processing: Docling engine
- Data Validation: Pydantic v2
- Database: SQLite3
- Image Processing: OpenCV, Pillow, pdf2image
- External Integration: Label Studio SDK
- Real-time: WebSockets
- Frontend: React 19 + TypeScript 5.9 + Vite 7 + Tailwind CSS 4
- State Management: Zustand
- Testing: Playwright, pytest
- Infrastructure: Docker (Python 3.11-slim-bookworm)

## Audit Requirements
Scan the files and generate a report identifying documentation gaps across the categories below.
Include "Needs Creation" for missing docs and "Needs Update" for incomplete/outdated docs.

---

## 1) Developer Onboarding Documentation

### A) README & Quick Start
- Project overview with architecture diagram reference
- Prerequisites (Python version, Node version, system deps)
- One-command local setup (`make dev` or equivalent)
- Environment variable documentation with examples
- Common first-day issues and solutions
- **Stack-specific**: Docling installation quirks, Label Studio setup, OpenCV dependencies

### B) Architecture Documentation
- System architecture diagram (data flow, component relationships)
- 15-stage pipeline explanation with stage dependencies
- Checkpoint system design and format specification
- WebSocket message protocol documentation
- Frontend/backend boundary definition
- **Stack-specific**: How Docling integrates, Label Studio annotation flow, DPI handling

### C) Development Workflow Guide
- Git branching strategy
- Code review process
- Testing requirements before merge
- How to add a new pipeline stage
- How to add a new API endpoint
- **Stack-specific**: Pydantic model conventions, FastAPI route patterns, React component structure

### D) API Documentation
- OpenAPI/Swagger setup and access URL
- Authentication/authorization documentation
- WebSocket endpoint documentation with message schemas
- Error response format documentation
- Rate limiting documentation (if applicable)
- **Stack-specific**: Pydantic model-to-API mapping, WebSocket message types

---

## 2) Operational Runbooks

### A) Deployment Runbook
- Step-by-step deployment procedure
- Pre-deployment checklist
- Rollback procedure (exact commands)
- Post-deployment verification steps
- Blue-green or canary deployment instructions (if applicable)
- **Stack-specific**: Docker build and push, Uvicorn restart, database migration

### B) Startup/Shutdown Runbook
- Service startup sequence and dependencies
- Graceful shutdown procedure
- How to verify services are healthy
- Log locations during startup
- **Stack-specific**: FastAPI/Uvicorn startup, Label Studio connection verification, WebSocket initialization

### C) Scaling Runbook
- Horizontal scaling procedure
- Vertical scaling limits and recommendations
- Load balancer configuration
- Session/state considerations when scaling
- **Stack-specific**: SQLite limitations at scale, WebSocket connection distribution, Docling memory requirements

### D) Backup & Restore Runbook
- Database backup procedure (exact commands)
- Checkpoint file backup strategy
- Uploaded document backup
- Restore procedure with verification steps
- Recovery time objectives (RTO) documentation
- **Stack-specific**: SQLite backup commands, checkpoint directory structure, file storage paths

---

## 3) Incident Response Documentation

### A) On-Call Playbook
- Escalation paths and contacts
- Severity classification guide (P1/P2/P3/P4)
- Initial triage steps for any alert
- Communication templates (status page updates, Slack messages)
- Post-incident review process
- **Stack-specific**: Pipeline failure triage, WebSocket disconnect handling, Label Studio unavailability

### B) Known Failure Modes Runbook
Each failure mode needs:
- Symptoms (logs, metrics, user reports)
- Root cause
- Immediate mitigation steps
- Permanent fix
- Prevention measures

Expected failure modes:
- Pipeline processing timeout
- SQLite database locked
- WebSocket connection storm
- Docling model loading failure
- Label Studio API unreachable
- PDF upload corruption/bomb
- Checkpoint file corruption
- Memory exhaustion during image processing
- **Stack-specific**: OpenCV/Pillow OOM, pdf2image Poppler failures

### C) Debugging Guide
- How to access logs (location, format, aggregation)
- How to enable debug logging
- How to trace a request through the pipeline
- Common error messages and their meanings
- How to inspect checkpoint state
- **Stack-specific**: FastAPI request tracing, WebSocket message debugging, Docling internal logging

### D) Health Check Documentation
- All health check endpoints and their meaning
- What each health check validates
- How to manually verify system health
- Metrics to monitor and alert thresholds
- **Stack-specific**: Pipeline stage health, Label Studio connection health, WebSocket connection count

---

## 4) Configuration Documentation

### A) Environment Variables Reference
- Complete list of all environment variables
- Required vs optional designation
- Default values
- Valid value ranges/formats
- Example values for dev/staging/prod
- **Stack-specific**: Label Studio API keys, DPI settings, file storage paths, database paths

### B) Feature Flags Documentation
- All feature flags and their effects
- How to enable/disable features
- Which flags are safe to change in production
- Dependencies between flags
- **Stack-specific**: Pipeline stage toggles, export format options

### C) Integration Configuration
- Label Studio connection configuration
- External service timeout configurations
- Retry policy configurations
- **Stack-specific**: Label Studio project templates, webhook configurations

---

## 5) Pipeline-Specific Documentation

### A) Stage Documentation (for each of 15 stages)
Each stage needs:
- Purpose and responsibilities
- Input format and source
- Output format and destination
- Configuration options
- Known limitations
- Error handling behavior
- Checkpoint schema
- **Stack-specific**: Docling stage mapping, coordinate system handling

### B) Checkpoint Format Documentation
- JSON schema for each checkpoint type
- Version history and migration paths
- Field descriptions with examples
- Validation rules
- Backward compatibility guarantees
- **Stack-specific**: Pydantic model definitions, coordinate format specs

### C) Export Format Documentation
- Supported export formats (Markdown, JSON, HTML, Text, DocTags)
- Format specifications and examples
- Customization options
- Known limitations per format
- **Stack-specific**: Docling export integration

---

## 6) Testing Documentation

### A) Testing Strategy Guide
- Test pyramid overview (unit/integration/e2e ratios)
- How to run each test type
- How to write new tests
- Mocking guidelines
- Fixture organization
- **Stack-specific**: Playwright test patterns, pytest fixtures for Docling, Label Studio mocking

### B) Test Data Documentation
- Test document locations and purposes
- How to create new test fixtures
- Test data cleanup procedures
- **Stack-specific**: PDF test files, expected checkpoint outputs

---

## Output Format (Mandatory)

For each documentation gap found, provide:

```
[STATUS: MISSING | INCOMPLETE | OUTDATED | UNCLEAR]

Document Type: Runbook | Reference | Guide | API Doc | Architecture
Category: Onboarding | Operations | Incident Response | Configuration | Pipeline | Testing

Gap Description:
- 2-4 sentences explaining what is missing or inadequate.
- Who is impacted (new developers, on-call engineers, operators).

Impact Assessment:
- Incident Impact: How this gap affects incident response time
- Onboarding Impact: How this affects new developer productivity
- Maintenance Impact: How this affects ongoing operations
- Risk Level: CRITICAL | HIGH | MEDIUM | LOW

Recommended Content:
- Outline of what the documentation should contain
- Key sections to include
- Examples or templates to provide

Template/Example:
- Provide a starter template or example content
- Include actual command examples where applicable
- Show the expected format and level of detail

Owner Suggestion:
- Who should create/maintain this document
- Review frequency recommendation
```

---

## Severity Classification

- **CRITICAL**: Missing runbook that will delay incident response by 30+ minutes
- **HIGH**: Missing documentation that blocks new developer onboarding or daily operations
- **MEDIUM**: Incomplete documentation that causes confusion but has workarounds
- **LOW**: Nice-to-have documentation that would improve efficiency

---

## Documentation Readiness Score (1-10)

Rate overall documentation readiness:
- **9-10**: Production-ready; comprehensive docs, runbooks tested
- **7-8**: Good coverage; 1-2 critical gaps to fill
- **5-6**: Significant gaps; on-call engineers will struggle
- **3-4**: Major gaps; expect extended incident resolution times
- **<3**: Minimal documentation; not ready for production operations

---

## Include:
- The score
- Brief justification (2-5 bullets)
- Prioritized Top 5 documentation items to create

## Final Section: Documentation Action Plan (Mandatory)

### 1) Create Now (before production)
- Critical runbooks and on-call documentation
- Estimated effort per document

### 2) Create Soon (first month of production)
- Onboarding and architecture documentation
- Reference documentation

### 3) Create Later (ongoing)
- Nice-to-have guides and tutorials
- Deep-dive technical documentation

## Also Include:
- Documentation hosting recommendation (GitBook, Notion, Markdown in repo)
- Suggested folder structure for documentation
- Documentation review and update cadence
- Template files to create for consistency

## Stack-Specific Documentation Checklist

### Python/FastAPI Backend
- [ ] FastAPI route documentation with Pydantic models
- [ ] Uvicorn configuration and tuning guide
- [ ] async/await patterns and gotchas
- [ ] Dependency injection patterns used

### Docling Integration
- [ ] Docling version and compatibility notes
- [ ] Model loading and memory requirements
- [ ] DPI handling (72/144/216) documentation
- [ ] Custom pipeline stage creation guide

### SQLite Operations
- [ ] WAL mode configuration
- [ ] Concurrent access patterns
- [ ] Backup commands and schedule
- [ ] Database schema documentation

### Label Studio Integration
- [ ] Project template configuration
- [ ] API key management
- [ ] Webhook setup
- [ ] Pre-annotation format documentation

### WebSocket Protocol
- [ ] Message type catalog
- [ ] Connection lifecycle documentation
- [ ] Reconnection behavior
- [ ] Error message formats

### React/TypeScript Frontend
- [ ] Component hierarchy documentation
- [ ] Zustand store documentation
- [ ] TypeScript interface documentation
- [ ] Build and deployment process

### Docker/Infrastructure
- [ ] Dockerfile documentation
- [ ] Required system dependencies
- [ ] Volume mount requirements
- [ ] Resource limit recommendations
