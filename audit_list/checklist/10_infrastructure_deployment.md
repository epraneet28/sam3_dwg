# Infrastructure & Deployment Audit

**Priority**: P2
**Merged from**: #9 (Infrastructure and Deployment), #29 (System Dependency Docker Slim)
**Status**: Active
**Tags**: `infrastructure`, `docker`, `deployment`, `dependencies`

---

## Overview

Comprehensive infrastructure and deployment audit covering container configuration, system dependencies, deployment readiness, and operational requirements for the Docling Interactive pipeline.

**Key Focus Areas**:
- Container configuration and resource management
- System library dependencies for slim Docker images
- Deployment strategy and production readiness
- Storage, networking, and observability infrastructure

---

## 1. Docker System Dependencies (Slim Base Image)

### 1.1 Critical Runtime Libraries Matrix

The Python 3.11-slim-bookworm base image requires explicit installation of native libraries for document processing packages.

#### OpenCV Dependencies
- [ ] 🐳 Install `libgl1-mesa-glx` or `libgl1` (OpenGL)
- [ ] 🐳 Install `libglib2.0-0` (GLib)
- [ ] 🐳 Install `libsm6` (X11 Session Management)
- [ ] 🐳 Install `libxext6` (X11 extensions)
- [ ] 🐳 Install `libxrender1` (X Render Extension)
- [ ] 🐳 Install `libgomp1` (OpenMP runtime for parallel processing)

**⚠️ AI-CODING RISK**: OpenCV imports succeed during build but crash at runtime with `ImportError: libGL.so.1: cannot open shared object file`

#### pdf2image Dependencies
- [ ] 🐳 Install `poppler-utils` (provides pdftoppm, pdfinfo binaries)

**⚠️ AI-CODING RISK**: `PDFInfoNotInstalledError: Unable to get page count. Is poppler installed and in PATH?`

#### Pillow Image Format Support
- [ ] 🐳 Install `libjpeg62-turbo` (JPEG support)
- [ ] 🐳 Install `libpng16-16` (PNG support)
- [ ] 🐳 Install `libtiff6` (TIFF support)
- [ ] 🐳 Install `libwebp7` (WebP support)
- [ ] 🐳 Install `zlib1g` (compression)
- [ ] 🐳 Install `libfreetype6` (font rendering)
- [ ] 🐳 Install `liblcms2-2` (color management)

**⚠️ AI-CODING RISK**: `IOError: decoder jpeg not available` or similar format-specific errors

#### File Type Detection
- [ ] 🐳 Install `libmagic1` (for python-magic file validation)

**⚠️ AI-CODING RISK**: `ImportError: failed to find libmagic`

#### Docling & ML Model Dependencies
- [ ] 🐳 Verify `libgomp1` (OpenMP for PyTorch/transformers)
- [ ] 🐳 Verify `libstdc++6` (C++ standard library)

**⚠️ AI-CODING RISK**: `libstdc++.so.6: version 'GLIBCXX_3.4.29' not found`

### 1.2 Font and Locale Configuration
- [ ] 🐳 Install `fonts-liberation` and `fonts-dejavu-core`
- [ ] 🐳 Install `fontconfig` and run `fc-cache -f -v`
- [ ] 🐳 Set `LANG=C.UTF-8` and `LC_ALL=C.UTF-8` environment variables

**⚠️ AI-CODING RISK**: `OSError: cannot open resource` when rendering text; `UnicodeDecodeError` on document processing

### 1.3 Network and SSL Dependencies
- [ ] 🐳 Install `ca-certificates` for HTTPS requests
- [ ] 🐳 Install `curl` for health checks

**⚠️ AI-CODING RISK**: `ssl.SSLCertVerificationError: certificate verify failed`

### 1.4 Process Management
- [ ] 🐳 Install `tini` for proper PID 1 and zombie process reaping
- [ ] 🐳 Use exec form in CMD/ENTRYPOINT for signal handling

**⚠️ AI-CODING RISK**: Zombie processes accumulate; graceful shutdown fails

---

## 2. Multi-Stage Build & Image Optimization

### 2.1 Build Stage Separation
- [ ] 🐳 Implement multi-stage Dockerfile with separate builder and runtime stages
- [ ] 🐳 Install build dependencies (`gcc`, `g++`, `python3-dev`, `libffi-dev`) only in builder
- [ ] 🐳 Use `pip wheel` in builder stage to compile packages
- [ ] 🐳 Copy only wheels to runtime stage

**⚠️ AI-CODING RISK**: Production images include unnecessary compilers and dev tools, increasing attack surface and size

### 2.2 Development Dependency Separation
- [ ] 🐳 Separate `requirements.txt` and `requirements-dev.txt`
- [ ] 🐳 Exclude `pytest`, `black`, `ruff`, `mypy` from production builds

### 2.3 Cache and Artifact Cleanup
- [ ] 🐳 Use `pip install --no-cache-dir` to prevent cache bloat
- [ ] 🐳 Add `rm -rf /var/lib/apt/lists/*` after all `apt-get install` commands
- [ ] 🐳 Clean up build artifacts and temporary files

### 2.4 Model Pre-Download
- [ ] 🐳 Pre-download Docling models during build to avoid 30-60s startup delay
  ```dockerfile
  RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"
  ```

**⚠️ AI-CODING RISK**: First request takes minutes while models download at runtime

---

## 3. Container Security & Hardening

### 3.1 Non-Root User Configuration
- [ ] 🐳 Create dedicated non-root user (`appuser`)
- [ ] 🐳 Set proper ownership on application directories
- [ ] 🐳 Run container as non-root user
- [ ] 🐳 Create writable directories with correct permissions:
  - `/app/checkpoints`
  - `/app/uploads`
  - `/app/temp`

**⚠️ AI-CODING RISK**: Running as root increases container escape risk; file permission errors on volume mounts

### 3.2 Version Pinning
- [ ] 🐳 Pin base image to specific tag (not `latest`)
- [ ] 🐳 Pin Python package versions in requirements.txt
- [ ] 🐳 Consider using image digest for maximum reproducibility

**⚠️ AI-CODING RISK**: Non-reproducible builds; unexpected behavior from upstream changes

### 3.3 Image Security Scanning
- [ ] 🐳 Add OpenContainers labels for security scanning
- [ ] 🐳 Integrate Trivy or Snyk in CI/CD pipeline
- [ ] 🐳 Use `--no-install-recommends` with apt-get

### 3.4 Read-Only Root Filesystem
- [ ] 🐳 Test compatibility with read-only root filesystem
- [ ] 🐳 Use tmpfs for writable directories when using read-only root

---

## 4. Container Resource Management

### 4.1 Resource Limits
- [ ] 🐳 Set CPU limits (2-4 cores recommended for Docling)
- [ ] 🐳 Set memory limits (4-8GB recommended for model loading and processing)
- [ ] 🐳 Configure swap limits

**⚠️ AI-CODING RISK**: Unbounded memory usage leads to OOM kills during large PDF processing; Docling model loading consumes 2-4GB RAM; pdf2image spikes 500MB+ per document

### 4.2 Health Checks
- [ ] 🐳 Implement HEALTHCHECK in Dockerfile
- [ ] 🐳 Verify `/health` endpoint checks:
  - SQLite connectivity
  - Disk space availability
  - WebSocket manager status
  - Docling model loaded
- [ ] 🐳 Configure appropriate intervals (30s), timeout (10s), start-period (60s for model loading)

**⚠️ AI-CODING RISK**: Orchestrators cannot detect unhealthy containers; traffic routed to non-ready instances

### 4.3 Graceful Shutdown
- [ ] 🐳 Implement SIGTERM handling in application
- [ ] 🐳 Configure graceful shutdown timeout
- [ ] 🐳 Ensure WebSocket connections close cleanly
- [ ] 🐳 Drain in-flight document processing

**⚠️ AI-CODING RISK**: Long-running document processing interrupted; data loss on container restarts

### 4.4 Build Optimization
- [ ] 🐳 Create comprehensive `.dockerignore`:
  - `node_modules/`
  - `.venv/`
  - `checkpoints/`
  - `*.pyc`
  - `.git/`
  - `temp/`
- [ ] 🐳 Order Dockerfile layers by change frequency

---

## 5. Complete Dockerfile Template

```dockerfile
# ============================================
# Build Stage
# ============================================
FROM python:3.11-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ============================================
# Runtime Stage
# ============================================
FROM python:3.11-slim-bookworm AS runtime

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV dependencies
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    # pdf2image dependencies
    poppler-utils \
    # Pillow dependencies
    libjpeg62-turbo \
    libpng16-16 \
    libtiff6 \
    libwebp7 \
    zlib1g \
    libfreetype6 \
    liblcms2-2 \
    # libmagic
    libmagic1 \
    # Fonts
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    # SSL/TLS
    ca-certificates \
    # Process management
    tini \
    # Health checks
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -f -v

# Set locale
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Install Python packages
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Set up application
WORKDIR /app
COPY --chown=appuser:appuser . .

# Create writable directories
RUN mkdir -p /app/checkpoints /app/uploads /app/temp \
    && chown -R appuser:appuser /app

# Pre-download Docling models (optional but recommended)
# RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Use tini as init
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 6. Reverse Proxy & Network Configuration

### 6.1 TLS Configuration
- [ ] Configure TLS 1.2+ with strong cipher suites
- [ ] Use Let's Encrypt/ACME for certificate management
- [ ] Enable HSTS headers
- [ ] Configure certificate auto-renewal

**⚠️ AI-CODING RISK**: Weak TLS or self-signed certificates in production

### 6.2 WebSocket Proxy Configuration
- [ ] Configure WebSocket upgrade headers in reverse proxy
- [ ] Set `proxy_http_version 1.1`
- [ ] Add `Upgrade` and `Connection` headers
- [ ] Configure appropriate timeouts (>= document processing time)

**⚠️ AI-CODING RISK**: WebSocket connections fail; document processing updates not received by frontend

### 6.3 Request Timeouts & Limits
- [ ] Set client body size limit (100MB+ for large PDFs)
- [ ] Configure request timeout (300s+ for long processing)
- [ ] Set proxy read/send timeouts appropriately

**⚠️ AI-CODING RISK**: Large PDF uploads rejected; processing timeouts on complex documents

### 6.4 Rate Limiting & DDoS Protection
- [ ] Implement rate limiting at reverse proxy level
- [ ] Configure connection limits per IP
- [ ] Consider WAF integration for production

### 6.5 Static Asset Serving
- [ ] Serve React frontend assets from CDN or NGINX
- [ ] Configure cache headers for static assets
- [ ] Enable gzip/Brotli compression

**⚠️ AI-CODING RISK**: Poor frontend performance; application server wasted on static files

---

## 7. Storage & Persistence

### 7.1 Volume Strategy
- [ ] Use named volumes instead of bind mounts
- [ ] Define volumes for:
  - SQLite database
  - Checkpoint files
  - Uploaded PDFs
  - Temporary processing files
- [ ] Document volume mount points

**⚠️ AI-CODING RISK**: Data loss on container restart; backup complexity with bind mounts

### 7.2 SQLite Production Configuration
- [ ] Enable WAL mode for better concurrency
- [ ] Verify single-writer architecture (SQLite limitation)
- [ ] Consider PostgreSQL migration for high-concurrency scenarios
- [ ] Mount database file on persistent volume

**⚠️ AI-CODING RISK**: File locking issues; database corruption on container crashes

### 7.3 Checkpoint File Management
- [ ] Implement retention policy (e.g., 30 days)
- [ ] Configure cleanup cron jobs
- [ ] Monitor checkpoint directory size
- [ ] Handle orphaned checkpoints from failed processing

**⚠️ AI-CODING RISK**: Unbounded disk usage; 50MB+ per document × 15 stages × many documents

### 7.4 Disk Space Monitoring
- [ ] Implement disk space alerts (80%, 90% thresholds)
- [ ] Configure temporary file TTL
- [ ] Set up automated cleanup jobs

---

## 8. Health Checks & Readiness

### 8.1 Application Health Endpoints
- [ ] Implement `/health` (liveness) endpoint
- [ ] Implement `/ready` (readiness) endpoint with dependency checks:
  - SQLite connectivity
  - Disk space availability
  - WebSocket manager operational
  - Docling models loaded
- [ ] Return appropriate HTTP status codes (200, 503)

**⚠️ AI-CODING RISK**: Health checks return 200 when dependencies are down; traffic routed to broken instances

### 8.2 Startup Probes
- [ ] Configure startup probes for slow-starting containers
- [ ] Set initial delay for model loading (30-60 seconds)
- [ ] Configure appropriate failure threshold

**⚠️ AI-CODING RISK**: Container killed before Docling models finish loading

### 8.3 Liveness and Readiness Probes
- [ ] Configure liveness probe to detect deadlocks
- [ ] Configure readiness probe to detect temporary unavailability
- [ ] Set appropriate timeout and period values

---

## 9. Scaling & High Availability

### 9.1 Stateless Design
- [ ] Verify no in-memory state preventing horizontal scaling
- [ ] Document WebSocket session affinity requirements
- [ ] Consider Redis for shared session state
- [ ] Externalize document processing queue

**⚠️ AI-CODING RISK**: WebSocket connections break on load balancing; cannot scale horizontally

### 9.2 Autoscaling Configuration
- [ ] Define autoscaling rules (HPA/ASG)
- [ ] Use custom metrics (queue depth, not just CPU)
- [ ] Configure memory-aware scaling
- [ ] Set min/max replica counts

**⚠️ AI-CODING RISK**: CPU-based scaling misses queued document processing; memory exhaustion

### 9.3 High Availability
- [ ] Configure pod disruption budgets (PDB)
- [ ] Set up pod anti-affinity rules
- [ ] Ensure multi-AZ deployment
- [ ] Document single points of failure

---

## 10. Secrets & Configuration Management

### 10.1 Secrets Management
- [ ] Use secrets management system (Vault, K8s Secrets, AWS Secrets Manager)
- [ ] Never bake secrets into images
- [ ] Avoid exposing secrets in environment variables visible in logs
- [ ] Secure Label Studio API keys

**⚠️ AI-CODING RISK**: API keys exposed in logs, process lists, or container images

### 10.2 Configuration Validation
- [ ] Validate required configuration at startup
- [ ] Document all configuration variables
- [ ] Implement environment parity checks
- [ ] Validate critical settings (DPI, storage paths, Label Studio URLs)

### 10.3 Log Scrubbing
- [ ] Implement structured logging with redaction
- [ ] Scrub sensitive data (API keys, tokens, PII)
- [ ] Sanitize file paths in error messages
- [ ] Avoid document content in logs

---

## 11. Deployment Strategy & Rollout

### 11.1 Deployment Strategy
- [ ] Implement blue-green or canary deployment
- [ ] Document rollback procedure
- [ ] Test rollback in staging environment
- [ ] Configure automated rollback on health check failure

**⚠️ AI-CODING RISK**: No rollback plan; downtime during failed deployments

### 11.2 Database Migrations
- [ ] Version checkpoint schema
- [ ] Implement backward-compatible schema changes
- [ ] Test migrations in staging
- [ ] Document migration rollback procedures

**⚠️ AI-CODING RISK**: Breaking checkpoint schema changes; cannot load existing checkpoints

### 11.3 Feature Flags
- [ ] Implement feature flag system
- [ ] Use flags for gradual rollout of new features
- [ ] Document feature flag lifecycle

### 11.4 Post-Deployment Verification
- [ ] Implement automated smoke tests
- [ ] Verify critical workflows after deployment
- [ ] Monitor error rates post-deployment
- [ ] Test document processing end-to-end

---

## 12. Monitoring & Observability

### 12.1 Metrics Collection
- [ ] Add Prometheus metrics exporter
- [ ] Create Grafana dashboards for:
  - Document processing latency
  - Queue depth
  - Active WebSocket connections
  - Checkpoint file count and size
  - Error rates by stage
- [ ] Export custom application metrics

**⚠️ AI-CODING RISK**: No visibility into production performance; cannot diagnose issues

### 12.2 Log Aggregation
- [ ] Ship logs to centralized system (ELK, Loki, CloudWatch)
- [ ] Implement structured JSON logging
- [ ] Configure log retention policy
- [ ] Index logs for searchability

### 12.3 Alerting
- [ ] Configure alerts for critical conditions:
  - Processing failures
  - Disk space thresholds
  - Label Studio connectivity
  - WebSocket connection failures
  - Memory/CPU exhaustion
- [ ] Create runbooks for each alert
- [ ] Set up on-call rotation

### 12.4 Distributed Tracing
- [ ] Integrate OpenTelemetry
- [ ] Trace documents through 15 pipeline stages
- [ ] Add correlation IDs to all requests
- [ ] Track cross-service communication

---

## 13. Backup & Disaster Recovery

### 13.1 Backup Strategy
- [ ] Implement automated backups:
  - SQLite database (hourly)
  - Checkpoint files (daily)
  - Uploaded documents (daily)
- [ ] Store backups in separate storage (S3, separate volume)
- [ ] Test restore procedures regularly (monthly)

**⚠️ AI-CODING RISK**: Data loss on disk failure; no tested recovery procedure

### 13.2 RPO/RTO Definition
- [ ] Define Recovery Point Objective (RPO)
- [ ] Define Recovery Time Objective (RTO)
- [ ] Document disaster recovery runbooks
- [ ] Test DR procedures

### 13.3 Geographic Redundancy
- [ ] Implement multi-AZ deployment
- [ ] Configure cross-region backup replication
- [ ] Document failover procedures

---

## 14. Dependency Verification Commands

Run these commands against the built container to verify all dependencies are present:

```bash
# OpenCV check
docker run --rm IMAGE python -c "import cv2; print(cv2.__version__)"

# pdf2image check
docker run --rm IMAGE which pdftoppm
docker run --rm IMAGE python -c "from pdf2image import convert_from_path; print('OK')"

# Pillow format support check
docker run --rm IMAGE python -c "from PIL import features; print('JPEG:', features.check('jpg'), 'PNG:', features.check('png'))"

# libmagic check
docker run --rm IMAGE python -c "import magic; print(magic.Magic().from_buffer(b'test'))"

# Font check
docker run --rm IMAGE fc-list | head -5

# Locale check
docker run --rm IMAGE python -c "import locale; print(locale.getlocale())"

# SSL check
docker run --rm IMAGE python -c "import ssl; print(ssl.OPENSSL_VERSION)"

# SQLite check
docker run --rm IMAGE python -c "import sqlite3; print(sqlite3.sqlite_version)"

# Docling check (if models pre-downloaded)
docker run --rm IMAGE python -c "from docling.document_converter import DocumentConverter; print('Docling OK')"

# Full dependency verification
docker run --rm IMAGE python -c "
import cv2
from pdf2image import convert_from_path
from PIL import Image
import magic
import sqlite3
print('All dependencies OK')
"
```

---

## 15. Production Readiness Checklist

### Container
- [ ] 🐳 All system dependencies installed (OpenCV, Pillow, pdf2image, libmagic)
- [ ] 🐳 Multi-stage build implemented
- [ ] 🐳 Resource limits configured (CPU: 2-4 cores, Memory: 4-8GB)
- [ ] 🐳 Non-root user configured
- [ ] 🐳 HEALTHCHECK instruction present
- [ ] 🐳 Comprehensive .dockerignore
- [ ] 🐳 Models pre-downloaded (optional)

### Network
- [ ] TLS 1.2+ with strong ciphers
- [ ] WebSocket upgrade headers configured
- [ ] Appropriate timeouts (300s+ for processing)
- [ ] Client body size limit (100MB+)
- [ ] Rate limiting enabled

### Storage
- [ ] Named volumes for persistence
- [ ] SQLite WAL mode enabled
- [ ] Backup strategy implemented and tested
- [ ] Retention policies configured
- [ ] Disk space monitoring enabled

### Security
- [ ] Secrets management system in use
- [ ] Image security scanning in CI/CD
- [ ] Log scrubbing implemented
- [ ] Non-root user enforced
- [ ] Minimal base image used

### Observability
- [ ] Prometheus metrics exported
- [ ] Grafana dashboards created
- [ ] Logs aggregated to central system
- [ ] Alerts configured with runbooks
- [ ] Distributed tracing enabled

### Deployment
- [ ] Rollback strategy documented and tested
- [ ] Database migration strategy defined
- [ ] Smoke tests automated
- [ ] Feature flags implemented (optional)

---

## 16. Estimated Effort & Image Size Impact

### Fix Now (Before Production)
- Multi-stage build implementation: **2-3 hours**
- System dependency installation: **1 hour**
- Non-root user configuration: **1 hour**
- Health checks implementation: **2 hours**
- Resource limits configuration: **1 hour**
- **Total**: **7-8 hours**

### Image Size Impact
- Base python:3.11-slim-bookworm: ~150MB
- OpenCV dependencies: ~50MB
- Pillow dependencies: ~30MB
- poppler-utils: ~20MB
- Fonts: ~15MB
- Other dependencies: ~10MB
- **Total runtime image**: ~275MB
- **With models pre-downloaded**: ~500-700MB

---

## 17. Production Verification Procedures

### Pre-Deployment
```bash
# Build and verify
docker build -t docling-interactive:test .

# Verify dependencies
docker run --rm docling-interactive:test python -c "import cv2, PIL, magic; print('OK')"

# Check resource usage under load
docker stats

# Verify health endpoint
docker run -d -p 8000:8000 docling-interactive:test
curl -k http://localhost:8000/health
```

### Post-Deployment
- [ ] Run smoke tests on critical workflows
- [ ] Verify document upload and processing
- [ ] Test WebSocket real-time updates
- [ ] Monitor error rates for 24 hours
- [ ] Verify autoscaling behavior under load

### Chaos Testing
- [ ] Kill container, verify recovery
- [ ] Fill disk space, verify alerts
- [ ] Disconnect Label Studio, verify graceful degradation
- [ ] Overload with documents, verify queue behavior

---

## 18. Architecture-Specific Notes

### Python/FastAPI/Uvicorn
- [ ] Configure Uvicorn workers (2-4 per core for CPU-bound workload)
- [ ] Set graceful shutdown timeout
- [ ] Enable access logs in production
- [ ] Use lifespan events for startup/shutdown tasks

### WebSocket Considerations
- [ ] Sticky sessions required for WebSocket connections
- [ ] Keep-alive/ping-pong configured
- [ ] Frontend reconnection logic implemented
- [ ] Connection timeout >= max processing time

### Frontend/Vite
- [ ] Production build optimized (`vite build`)
- [ ] Assets served from CDN or NGINX
- [ ] Gzip/Brotli compression enabled
- [ ] Cache headers configured for static assets

---

## Summary

This consolidated audit covers:
1. **Complete system dependency matrix** for Python-slim containers with OpenCV, Pillow, pdf2image, and Docling
2. **Production-ready Dockerfile template** with multi-stage build and security hardening
3. **Infrastructure requirements** for deployment, networking, storage, and observability
4. **Verification commands** to ensure all dependencies are working
5. **Actionable checklists** for production readiness

**Key AI-Coding Risks**:
- Missing native libraries cause runtime failures (not build failures)
- Resource limits not set → OOM kills during document processing
- WebSocket configuration missing → real-time updates fail
- No checkpoint retention → unbounded disk usage
- Missing health checks → traffic to unhealthy containers

**Priority**: Fix system dependencies and multi-stage build before first production deployment. All other infrastructure items can be addressed incrementally based on scale and operational requirements.
