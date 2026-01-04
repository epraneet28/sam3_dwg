# Infrastructure & Deployment Audit Prompt (Production-Ready)

## Role
Act as a Senior DevOps/Platform Engineer and Infrastructure Architect. Perform a comprehensive Infrastructure & Deployment Audit on the provided codebase and configuration to ensure production readiness.

## Primary Goal
Identify infrastructure gaps, deployment risks, and operational blind spots that will cause outages, security incidents, or operational nightmares in production. Provide concrete fixes that make the system deployment-ready.

## Context
- This code was developed with a focus on speed ("vibecoded") and may have infrastructure shortcuts.
- The system processes documents with CPU/memory-intensive operations (Docling, OpenCV, Pillow).
- Real-time communication via WebSockets is critical to the user experience.
- Checkpoint files and SQLite database require persistent storage.

## Tech Stack
- **Backend**: Python 3.12 + FastAPI + Uvicorn (ASGI)
- **Document Processing**: Docling, OpenCV, Pillow, pdf2image
- **Database**: SQLite3 (file-based)
- **External Integration**: Label Studio SDK
- **Real-time**: WebSockets
- **Frontend**: React 19 + TypeScript 5.9 + Vite 7
- **Container**: Docker (Python 3.11-slim-bookworm base)
- **Infrastructure**: REST API + WebSocket endpoints

## How to Provide Context
I will paste/upload Dockerfile, docker-compose.yml, deployment configs, nginx/reverse proxy configs, and relevant application code. Analyze all provided files systematically.

If any critical context is missing (cloud provider, orchestration platform, CI/CD system, secrets management), infer what you can and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and specify exactly what is needed.

## Environment & Assumptions (do this first)
1) Infer and list:
   - Deployment target (Kubernetes, Docker Compose, ECS, bare VM, etc.)
   - Reverse proxy / load balancer (NGINX, Traefik, ALB, Caddy)
   - TLS termination point and certificate management
   - Container orchestration and scaling strategy
   - Secrets management approach (env vars, Vault, AWS Secrets Manager)
   - Storage strategy (local volumes, NFS, S3, persistent volumes)
   - CI/CD pipeline (GitHub Actions, GitLab CI, Jenkins)
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation.

---

## 1) Container Configuration & Resource Management

### A) Missing Resource Limits
- Containers without CPU/memory limits will consume host resources unbounded.
- Image processing (OpenCV, Pillow, pdf2image) can spike memory usage significantly.
- **Stack-specific**: Docling model loading can consume 2-4GB RAM; pdf2image can use 500MB+ per large PDF.
- Suggested Fix: Set explicit resource limits based on workload profiling.

### B) Base Image Security & Size
- Using outdated or bloated base images increases attack surface and pull times.
- Missing security scanning in build pipeline.
- **Stack-specific**: python-slim missing system libraries for OpenCV (libgl1), pdf2image (poppler-utils).
- Suggested Fix: Use minimal base, multi-stage builds, scan with Trivy/Snyk.

### C) Container Health Checks
- Missing HEALTHCHECK instructions prevent orchestrators from detecting unhealthy containers.
- Health checks that don't verify actual service readiness.
- **Stack-specific**: WebSocket endpoint health, Docling model loaded, SQLite accessible.
- Suggested Fix: Implement comprehensive health checks at /health with dependency verification.

### D) Non-Root User
- Running as root inside containers increases security risk.
- File permission issues when switching to non-root.
- **Stack-specific**: Checkpoint directory permissions, SQLite file ownership.
- Suggested Fix: Create and use dedicated non-root user, set proper file permissions.

### E) Build Reproducibility
- Non-pinned dependencies cause inconsistent builds.
- Missing .dockerignore causes large build contexts.
- **Stack-specific**: Docling version pinning critical due to API changes.
- Suggested Fix: Pin all dependencies, use lock files, proper .dockerignore.

---

## 2) Reverse Proxy & Network Configuration

### A) TLS Configuration
- Missing or weak TLS configuration.
- Self-signed certificates in production.
- Missing HSTS, certificate pinning considerations.
- Suggested Fix: Use Let's Encrypt/ACME, enforce TLS 1.2+, enable HSTS.

### B) WebSocket Proxy Configuration
- Missing WebSocket upgrade headers.
- Incorrect timeout settings for long-lived connections.
- **Stack-specific**: Document processing updates via WebSocket require persistent connections.
- Suggested Fix: Configure proxy_http_version 1.1, Upgrade headers, appropriate timeouts.

### C) Request Timeouts & Limits
- Default timeouts too short for document processing.
- Missing client body size limits.
- **Stack-specific**: Large PDF uploads (50MB+), long processing times (minutes for complex docs).
- Suggested Fix: Set appropriate timeouts (300s+ for processing), body limits (100MB).

### D) Rate Limiting & DDoS Protection
- Missing rate limiting at reverse proxy level.
- No connection limits per IP.
- Suggested Fix: Implement rate limiting, connection limits, consider WAF.

### E) Static Asset Serving
- Serving static files through application server.
- Missing caching headers.
- **Stack-specific**: React frontend assets, rendered page images.
- Suggested Fix: Serve static assets from CDN/NGINX with proper cache headers.

---

## 3) Storage & Persistence

### A) Volume Mount Strategy
- Using bind mounts instead of named volumes.
- Missing backup strategy for persistent data.
- **Stack-specific**: Checkpoint files, SQLite database, uploaded PDFs.
- Suggested Fix: Use named volumes, implement backup automation.

### B) SQLite in Production
- SQLite not suitable for high-concurrency writes.
- Missing WAL mode configuration.
- Potential file locking issues in containers.
- **Stack-specific**: Document status updates, checkpoint metadata.
- Suggested Fix: Enable WAL mode, consider PostgreSQL for production, or ensure single-writer.

### C) Checkpoint File Management
- Unbounded checkpoint file growth.
- Missing cleanup/retention policies.
- Orphaned checkpoints from failed processing.
- **Stack-specific**: Each document creates checkpoints at 15 stages, potentially 50MB+ per doc.
- Suggested Fix: Implement retention policy, cleanup jobs, size monitoring.

### D) Upload File Handling
- Temporary files not cleaned up.
- Missing disk space monitoring.
- **Stack-specific**: Large PDFs stored during processing.
- Suggested Fix: Implement cleanup cron, disk space alerts, temp file TTL.

---

## 4) Health Checks & Readiness

### A) Application Health Endpoints
- Missing or incomplete health check endpoints.
- Health checks that return 200 when dependencies are down.
- **Stack-specific**: Check SQLite connectivity, disk space, WebSocket manager status.
- Suggested Fix: Implement /health (liveness), /ready (readiness) with dependency checks.

### B) Startup Probes
- Missing startup probes for slow-starting containers.
- **Stack-specific**: Docling model loading takes 30-60 seconds.
- Suggested Fix: Configure startup probes with appropriate initial delay.

### C) Graceful Shutdown
- Missing SIGTERM handling.
- In-flight requests dropped on shutdown.
- WebSocket connections not cleanly closed.
- **Stack-specific**: Long-running document processing interrupted.
- Suggested Fix: Implement graceful shutdown with drain period.

---

## 5) Scaling & High Availability

### A) Stateless Design Verification
- In-memory state preventing horizontal scaling.
- Session affinity requirements not documented.
- **Stack-specific**: WebSocket connections require sticky sessions, in-memory document state.
- Suggested Fix: Externalize state to Redis, document session affinity requirements.

### B) Autoscaling Configuration
- Missing HPA/autoscaling rules.
- Incorrect scaling metrics (CPU vs custom).
- **Stack-specific**: CPU-based scaling may not reflect document processing queue depth.
- Suggested Fix: Custom metrics based on queue depth, memory-aware scaling.

### C) Pod Disruption Budgets
- Missing PDBs allowing all replicas to be evicted.
- Suggested Fix: Configure appropriate PDBs for availability.

### D) Anti-affinity Rules
- All replicas scheduled on same node.
- Suggested Fix: Pod anti-affinity for resilience.

---

## 6) Secrets & Configuration Management

### A) Secrets Exposure
- Secrets in environment variables visible in logs/process lists.
- Secrets baked into images.
- **Stack-specific**: Label Studio API keys, database credentials.
- Suggested Fix: Use secrets management (Vault, K8s Secrets with encryption).

### B) Configuration Drift
- Config differences between environments not tracked.
- Missing validation of required config at startup.
- **Stack-specific**: DPI settings, storage paths, Label Studio URLs.
- Suggested Fix: Config validation at startup, environment parity checks.

### C) Sensitive Data in Logs
- API keys, tokens, or PII in application logs.
- Stack traces exposing internal paths.
- **Stack-specific**: Document content, file paths in error messages.
- Suggested Fix: Log scrubbing, structured logging with redaction.

---

## 7) Deployment Strategy & Rollout

### A) Deployment Strategy
- Missing or risky deployment strategy.
- No rollback plan.
- Suggested Fix: Blue-green or canary deployment, automated rollback.

### B) Database Migrations
- Missing migration strategy.
- Breaking schema changes without backward compatibility.
- **Stack-specific**: Checkpoint schema evolution, SQLite schema changes.
- Suggested Fix: Versioned migrations, backward-compatible changes.

### C) Feature Flags
- No ability to disable features without deployment.
- Suggested Fix: Feature flag system for gradual rollout.

### D) Smoke Tests
- No post-deployment verification.
- Suggested Fix: Automated smoke tests after deployment.

---

## 8) Monitoring & Observability Infrastructure

### A) Metrics Collection
- Missing metrics exporter (Prometheus).
- No dashboards for key metrics.
- **Stack-specific**: Document processing latency, queue depth, WebSocket connections.
- Suggested Fix: Add Prometheus metrics, Grafana dashboards.

### B) Log Aggregation
- Logs only in container stdout.
- Missing structured logging.
- No log retention policy.
- Suggested Fix: Ship to ELK/Loki, structured JSON logging.

### C) Alerting
- No alerting on critical conditions.
- Missing runbooks for alerts.
- **Stack-specific**: Processing failures, disk space, Label Studio connectivity.
- Suggested Fix: Configure alerts with runbook links.

### D) Distributed Tracing
- No request tracing across services.
- Missing correlation IDs.
- **Stack-specific**: Trace document through 15 pipeline stages.
- Suggested Fix: OpenTelemetry integration.

---

## 9) Backup & Disaster Recovery

### A) Backup Strategy
- No automated backups.
- Backups not tested.
- **Stack-specific**: SQLite database, checkpoint files, uploaded documents.
- Suggested Fix: Automated backup to separate storage, regular restore tests.

### B) RPO/RTO Definition
- No defined recovery objectives.
- Missing disaster recovery runbooks.
- Suggested Fix: Define and document RPO/RTO, DR procedures.

### C) Cross-Region/AZ
- Single availability zone deployment.
- No geo-redundancy for critical data.
- Suggested Fix: Multi-AZ deployment, cross-region backup.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s) or Config Section
Risk Category: Container | Network | Storage | Security | Scaling | Deployment | Observability | DR

The Problem:
- 2-4 sentences explaining the risk and failure scenario.
- Be specific: container OOM kill, connection timeout, data loss, security breach, etc.

Production Impact:
- Describe the user/business impact.
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (test command, metric to check, config to inspect).

The Fix:
- Provide the fixed configuration or code snippet.
- Show before/after if useful.

Trade-off Consideration:
- Note complexity, cost, and any risks.
- If acceptable at small scale, mark as MONITOR with threshold.
```

## Severity Classification
- **CRITICAL**: Will cause outage, data loss, or security breach in production.
- **HIGH**: Significant operational risk or degraded reliability.
- **MEDIUM**: Best practice violation that could cause issues at scale.
- **MONITOR**: Acceptable for now; watch and revisit at thresholds.

---

## Infrastructure Readiness Score (1-10)

Rate overall infrastructure readiness:
- **9-10**: Production-ready; minor improvements only.
- **7-8**: Ready with 1-2 critical fixes.
- **5-6**: Significant work needed before production.
- **3-4**: Multiple critical gaps; high outage risk.
- **<3**: Not safe to deploy; fundamental issues.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- Top 3 priority fixes (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (before production deployment)
2) Fix Soon (first week in production)
3) Monitor (metrics + thresholds)

## Also include:
- Estimated effort for all Fix Now items
- Pre-production checklist:
  - Container: Resource limits, health checks, non-root user
  - Network: TLS, timeouts, WebSocket config
  - Storage: Backup strategy, retention policies
  - Security: Secrets management, image scanning
  - Observability: Metrics, logs, alerts, dashboards
  - Deployment: Rollback strategy, smoke tests
- Recommended production verification:
  - `docker stats` -> verify resource usage under load
  - `curl -k https://host/health` -> verify health endpoint
  - Chaos testing: kill container, verify recovery
  - Load test: verify scaling behavior

---

## Stack-Specific Checklist

### Docker/Container
- [ ] Resource limits set (CPU: 2-4 cores, Memory: 4-8GB for Docling)
- [ ] Multi-stage build reducing image size
- [ ] Non-root user configured
- [ ] HEALTHCHECK instruction present
- [ ] .dockerignore excludes node_modules, .venv, checkpoints
- [ ] System dependencies installed (libgl1, poppler-utils, libmagic)

### Python/FastAPI/Uvicorn
- [ ] Uvicorn workers configured (2-4 per core for CPU-bound)
- [ ] Graceful shutdown timeout set
- [ ] Access logs configured
- [ ] Lifespan events for startup/shutdown

### SQLite
- [ ] WAL mode enabled
- [ ] Database file on persistent volume
- [ ] Backup cron job configured
- [ ] Connection pooling appropriate for SQLite

### WebSocket
- [ ] Proxy configured for WebSocket upgrade
- [ ] Keep-alive/ping-pong configured
- [ ] Connection timeout appropriate (>= processing time)
- [ ] Reconnection logic in frontend

### Frontend/Vite
- [ ] Production build optimized
- [ ] Assets served from CDN/static server
- [ ] Gzip/Brotli compression enabled
- [ ] Cache headers configured

### Storage
- [ ] Named volumes for persistence
- [ ] Backup strategy for checkpoints and database
- [ ] Disk space monitoring
- [ ] Cleanup jobs for temporary files
