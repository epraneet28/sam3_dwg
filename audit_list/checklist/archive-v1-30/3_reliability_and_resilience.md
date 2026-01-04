# Reliability & Resilience Audit Prompt

## Role
Act as a **Senior Site Reliability Engineer (SRE)** with 15+ years of experience building fault-tolerant distributed systems. You specialize in document processing pipelines, async Python services, and production-grade React applications. Your expertise includes resilience patterns (circuit breakers, retries, bulkheads), graceful degradation, and chaos engineering.

## Primary Goal
Conduct a ruthless reliability and resilience audit of the Docling-Interactive codebase. Identify every timeout missing, every retry absent, every error path unhandled, every resource leak possible, and every cascading failure scenario lurking in the code. This is NOT about features - it's about whether this system can survive production traffic, partial failures, and degraded conditions.

## Context
This is a 15-stage interactive document processing pipeline built with FastAPI backend and React frontend. The system was "vibecoded" - developed rapidly with AI assistance focusing on feature delivery and happy-path functionality. While the core functionality works, it likely lacks:

- Timeout protection on long-running document processing operations
- Retry logic with exponential backoff for transient failures
- Circuit breakers to prevent cascading failures from slow dependencies
- Graceful degradation when external services (Label Studio, OCR, VLM) fail
- Proper resource cleanup and memory management for large documents
- Checkpoint corruption detection and recovery mechanisms
- WebSocket reconnection logic and state synchronization
- Database write lock handling and connection pooling
- Health checks that actually validate critical dependencies
- Startup/shutdown sequences that ensure clean state transitions

## Tech Stack

### Backend
- **Runtime**: Python 3.12
- **Framework**: FastAPI + Uvicorn (ASGI server)
- **Document Processing**: Docling (can be slow, CPU/memory intensive)
- **Validation**: Pydantic v2
- **Database**: SQLite3 (write lock contention possible)
- **Image Processing**: OpenCV, Pillow, pdf2image (memory intensive)
- **External Services**: Label Studio SDK
- **Real-time**: WebSockets for progress updates
- **Async**: asyncio-based concurrent processing

### Frontend
- **Framework**: React 19 + TypeScript 5.9
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 4
- **State Management**: Zustand
- **Routing**: React Router DOM 7
- **Testing**: Playwright
- **API Communication**: fetch API + WebSocket

### Infrastructure
- **Container**: Docker (Python 3.11-slim-bookworm base)
- **API**: REST + WebSocket
- **File Storage**: Local filesystem for checkpoints and uploads
- **Deployment**: Uvicorn workers (potential for multi-worker issues)

---

## Detailed Audit Requirements

### 1. Timeout Handling

**Scope**: Every I/O operation must have explicit timeout protection.

#### 1.1 HTTP Client Timeouts
- **FastAPI routes**: Check all endpoints for request timeouts
- **External API calls**: Label Studio SDK, VLM services, any external HTTP calls
- **Requirements**:
  - Connection timeout (max 5s for establishing connection)
  - Read timeout (appropriate for operation - 30s for document processing, 120s for VLM inference)
  - Total timeout (end-to-end SLA enforcement)
  - Timeout values configurable via environment variables

#### 1.2 Database Operation Timeouts
- **SQLite queries**: Every SELECT, INSERT, UPDATE, DELETE
- **Write lock timeout**: SQLite default is infinite - must be bounded
- **Transaction timeout**: Long-running transactions should timeout
- **Requirements**:
  - Query timeout (5-10s max)
  - Write lock timeout (2s max before retry)
  - Connection timeout (3s max)

#### 1.3 Document Processing Timeouts
- **Docling pipeline stages**: Each of 15 stages must have timeout
- **OCR operations**: Can hang on corrupted PDFs
- **Layout detection**: ML model inference can be slow
- **Table extraction**: TableFormer can timeout on complex tables
- **VLM inference**: Picture description can take 30-60s
- **Requirements**:
  - Per-stage timeout (configurable, default 60s)
  - Total pipeline timeout (configurable, default 10 minutes)
  - Graceful cancellation (cleanup partial results)

#### 1.4 File I/O Timeouts
- **PDF loading**: Large PDFs can block on read
- **Image processing**: OpenCV/Pillow operations can hang
- **Checkpoint save/load**: Filesystem I/O can be slow
- **Requirements**:
  - File read timeout (30s max)
  - Image operation timeout (15s per image)
  - Checkpoint I/O timeout (5s max)

#### 1.5 WebSocket Timeouts
- **Connection establishment**: Must timeout quickly
- **Message delivery**: Don't wait forever for client ACK
- **Heartbeat/ping-pong**: Detect dead connections
- **Requirements**:
  - Connection timeout (10s)
  - Message timeout (5s before dropping slow clients)
  - Ping interval (30s) and pong timeout (10s)

### 2. Retry Logic with Exponential Backoff

**Scope**: Transient failures must be retried intelligently.

#### 2.1 Retryable vs Non-Retryable Errors
- **Classify errors**:
  - Retryable: Network errors, 503 Service Unavailable, SQLite BUSY, temporary file locks
  - Non-retryable: 400 Bad Request, 404 Not Found, validation errors, corrupted data
- **Requirements**:
  - Explicit classification in code
  - Different handling paths
  - Log retry attempts with context

#### 2.2 Exponential Backoff Configuration
- **Pattern**: delay = base_delay * (2 ^ attempt) + jitter
- **Requirements**:
  - Initial delay: 100ms-1s (depends on operation)
  - Max delay: 30s-60s
  - Max attempts: 3-5 (depends on operation)
  - Jitter: +/-20% randomization to avoid thundering herd
  - Backoff multiplier: 2x (standard exponential)

#### 2.3 Retry Scenarios to Check
- **Database writes**: SQLite BUSY errors
- **External API calls**: Label Studio, VLM services
- **File operations**: Temporary lock conflicts
- **Checkpoint saves**: Filesystem contention
- **Network requests**: Connection errors, timeouts

### 3. Circuit Breaker Patterns

**Scope**: Prevent cascading failures from slow/failing dependencies.

#### 3.1 External Service Circuit Breakers
- **Services to protect**:
  - Label Studio API
  - VLM inference services
  - OCR engine (if external)
  - Any external HTTP APIs
- **Requirements**:
  - Failure threshold: 5 failures in 10s -> OPEN
  - Success threshold: 3 successes in HALF-OPEN -> CLOSED
  - Timeout: 30s in OPEN before attempting HALF-OPEN
  - Fail-fast response when OPEN (don't queue requests)

#### 3.2 Database Circuit Breaker
- **SQLite protection**:
  - Detect repeated write lock failures
  - Prevent avalanche of retries
- **Requirements**:
  - Threshold: 10 lock failures in 5s -> OPEN
  - Recovery: 2 successful writes -> CLOSED
  - Fallback: Read-only mode or in-memory caching

#### 3.3 Graceful Degradation with Circuit Breakers
- **Fallback strategies**:
  - Label Studio unavailable -> disable export feature
  - VLM unavailable -> skip picture descriptions
  - OCR failing -> use cached results or skip
- **Requirements**:
  - Clear user messaging (not just 500 errors)
  - Feature flags to disable degraded features
  - Automatic recovery when circuit closes

### 4. Load Shedding and Graceful Degradation

**Scope**: System must degrade gracefully under overload.

#### 4.1 Request Queue Management
- **Pipeline processing queue**:
  - Max queue depth (e.g., 100 documents)
  - Reject new uploads when queue full
  - Priority queue (user-facing requests > batch jobs)
- **Requirements**:
  - 429 Too Many Requests when overloaded
  - Queue depth exposed in health check
  - Configurable queue limits

#### 4.2 Resource-Based Load Shedding
- **Triggers**:
  - CPU > 90% for 30s
  - Memory > 85% for 30s
  - Disk I/O saturated
  - Too many concurrent document processing tasks
- **Requirements**:
  - Monitor system resources
  - Shed load before OOM killer strikes
  - Graceful rejection (not crashes)

### 5. Startup and Shutdown Sequences

**Scope**: Clean initialization and termination.

#### 5.1 Startup Sequence
- **Order of operations**:
  1. Load configuration (with validation)
  2. Initialize database (check schema, run migrations)
  3. Validate checkpoint directory exists and is writable
  4. Pre-load Docling models (if applicable)
  5. Connect to external services (with retry)
  6. Start health check endpoint FIRST
  7. Start API server LAST
- **Requirements**:
  - Fail fast if critical dependencies unavailable
  - Log each initialization step
  - Readiness probe returns 503 until fully initialized

#### 5.2 Shutdown Sequence
- **Graceful shutdown**:
  1. Stop accepting new requests (return 503)
  2. Finish in-flight requests (with timeout)
  3. Save checkpoint state
  4. Close WebSocket connections gracefully
  5. Flush pending database writes
  6. Close database connections
  7. Cleanup temporary files
  8. Exit
- **Requirements**:
  - SIGTERM handler (Kubernetes compatibility)
  - Shutdown timeout (30s before forceful kill)
  - Log shutdown progress

### 6. Health Checks and Readiness Probes

**Scope**: Accurate health reporting for load balancers and orchestrators.

#### 6.1 Liveness Probe
- **Purpose**: Is the process alive?
- **Endpoint**: `GET /health/live`
- **Response**: 200 if process running
- **Requirements**:
  - Ultra-lightweight (no dependencies)
  - Sub-millisecond response time
  - Never blocks

#### 6.2 Readiness Probe
- **Purpose**: Can the service handle requests?
- **Endpoint**: `GET /health/ready`
- **Checks**:
  - Database writable
  - Checkpoint directory accessible
  - Critical external services reachable (with timeout)
  - Circuit breakers not all OPEN
  - Processing queue not full
- **Requirements**:
  - Timeout: 5s total
  - Return 503 if not ready
  - Include detailed status in response body

### 7. Error Handling and Recovery

**Scope**: Comprehensive error handling with recovery strategies.

#### 7.1 Pipeline Stage Error Recovery
- **Per-stage failures**:
  - Preprocessing failure: Retry with different parameters
  - OCR failure: Fall back to basic text extraction
  - Layout detection failure: Use heuristic fallback
  - Table extraction failure: Skip table or use simpler parser
  - VLM failure: Skip descriptions, continue pipeline
- **Requirements**:
  - Checkpoint before each stage (rollback point)
  - Explicit recovery strategy per stage
  - Log recovery attempts
  - User notification of degraded output

#### 7.2 Checkpoint Corruption Handling
- **Scenarios**:
  - Incomplete write (crash during save)
  - Corrupted JSON (filesystem error)
  - Schema version mismatch
  - Missing checkpoint file
- **Requirements**:
  - Validate checkpoint on load (JSON schema)
  - Atomic writes (temp file + rename)
  - Checksum/hash validation
  - Fallback to previous checkpoint
  - Delete corrupted checkpoints (with backup)

#### 7.3 Database Error Recovery
- **SQLite-specific**:
  - SQLITE_BUSY: Retry with backoff
  - SQLITE_LOCKED: Retry with backoff
  - SQLITE_CORRUPT: Fail loudly, log for recovery
  - Disk full: Return 507 Insufficient Storage
- **Requirements**:
  - WAL mode enabled (better concurrency)
  - Busy timeout configured (5s)
  - Retry logic for lock conflicts
  - Connection pooling (prevent leaks)

### 8. Dependency Failure Handling

**Scope**: System must survive dependency failures.

#### 8.1 Label Studio Unavailable
- **Scenarios**:
  - Service down
  - Network partition
  - Authentication failure
- **Handling**:
  - Disable export feature
  - Queue export requests for later
  - Return 503 on export endpoints
- **Requirements**:
  - Circuit breaker protection
  - User-facing error message
  - Automatic retry on recovery

#### 8.2 Docling Model Loading Failure
- **Scenarios**:
  - Model file corrupted
  - Insufficient memory
  - Incompatible version
- **Handling**:
  - Fail startup (critical dependency)
  - Log detailed error
  - Health check reports not ready

### 9. Concurrent Processing Safety

**Scope**: Multi-worker and async safety.

#### 9.1 SQLite Write Lock Handling
- **Issues**:
  - Multiple workers writing concurrently
  - Long-running transactions blocking writes
  - Deadlocks
- **Requirements**:
  - WAL mode enabled
  - Busy timeout configured
  - Retry logic on SQLITE_BUSY
  - Short transactions (acquire lock, write, release)

#### 9.2 Checkpoint File Concurrency
- **Issues**:
  - Multiple workers writing same checkpoint
  - Reader reading during write
  - Incomplete writes
- **Requirements**:
  - File locking (fcntl on Linux)
  - Atomic writes (temp + rename)
  - Reader validation (detect incomplete)

### 10. Resource Cleanup and Leak Prevention

**Scope**: No resource leaks under load.

#### 10.1 File Handle Leaks
- **Sources**:
  - PDF files not closed
  - Images not disposed
  - Temp files not deleted
- **Requirements**:
  - Context managers for all file I/O
  - Explicit cleanup in finally blocks
  - Temp file auto-deletion
  - File handle limit monitoring

#### 10.2 Memory Leaks
- **Sources**:
  - Large documents cached indefinitely
  - WebSocket connections not cleaned up
  - Circular references
  - Growing in-memory queues
- **Requirements**:
  - Cache eviction policies
  - Connection cleanup
  - Weak references where appropriate
  - Memory profiling in tests

#### 10.3 Database Connection Leaks
- **Sources**:
  - Connections not closed
  - Transactions not committed
  - Connection pool exhaustion
- **Requirements**:
  - Connection pooling with max size
  - Context managers for transactions
  - Connection timeout
  - Leak detection in health check

---

## Output Format

Provide findings in this exact format:

### Finding #X: [Concise Title]

**Location**: `path/to/file.py:line_number` or `component/function_name`

**Risk Category**: [Timeout | Retry | Circuit Breaker | Load Shedding | Startup/Shutdown | Health Check | Error Handling | Dependency Failure | Concurrency | Resource Leak]

**Severity**: [CRITICAL | HIGH | MEDIUM | MONITOR]

**The Problem**:
[2-3 sentences describing the exact issue in the code]

**Reliability Impact**:
[Concrete failure scenario and consequences]
- Under what conditions does this fail?
- What is the user impact?
- What is the cascade risk?

**How to Verify**:
```bash
# Specific commands to reproduce the issue
```

**The Fix**:
```python
# Exact code changes needed
```

**Trade-off Consideration**:
[Any performance, complexity, or operational costs of the fix]

---

## Severity Level Definitions

- **CRITICAL**: Causes data loss, crashes, or cascading failures. Production blocker.
- **HIGH**: Causes request failures, timeouts, or service degradation under load.
- **MEDIUM**: Causes poor user experience, inefficiency, or edge case failures.
- **MONITOR**: Not immediately harmful but creates tech debt or future risk.

---

## Reliability Score Rubric

After completing the audit, assign a reliability score from 1-10:

- **1-2**: System will fail in production within hours. Critical gaps everywhere.
- **3-4**: System will fail under moderate load. Many missing resilience patterns.
- **5-6**: System works under light load but has significant gaps. Some patterns present.
- **7-8**: System is mostly resilient with minor gaps. Production-ready with fixes.
- **9-10**: System is battle-tested with comprehensive resilience. Excellent coverage.

**Scoring Criteria**:
- Timeout coverage (are all I/O operations bounded?)
- Retry logic (are transient failures handled?)
- Circuit breakers (are cascading failures prevented?)
- Error handling (are error paths as robust as happy paths?)
- Resource cleanup (are leaks prevented?)
- Graceful degradation (does the system degrade or crash?)
- Observability (can failures be diagnosed?)

---

## Final Section: Summary & Action Plan

### Overall Reliability Score: X/10

**Summary**:
[2-3 paragraph executive summary of the codebase's resilience posture]

### Fix Now (Critical/High - Block Production)
1. [Issue #X]: [Title] - [One-line impact]
2. [Issue #Y]: [Title] - [One-line impact]

### Fix Soon (Medium - Production Risks)
1. [Issue #X]: [Title] - [One-line impact]
2. [Issue #Y]: [Title] - [One-line impact]

### Monitor (Low - Technical Debt)
1. [Issue #X]: [Title] - [One-line impact]
2. [Issue #Y]: [Title] - [One-line impact]

### Testing Strategy for Fixes
- Chaos testing: [Specific scenarios to inject failures]
- Load testing: [Specific load patterns to validate]
- Integration tests: [Specific dependency failure tests]
- Observability: [Metrics and alerts to add]

---

## Instructions for the Auditor

1. **Be ruthless**: This is production-readiness assessment, not a code review. Focus ONLY on reliability/resilience.
2. **Read the entire codebase**: Check backend (Python/FastAPI), frontend (React/TS), configs, Docker setup.
3. **Think about failure modes**: What happens if Label Studio is down? What happens if a 500MB PDF is uploaded? What happens if SQLite is locked?
4. **Check every I/O operation**: Network calls, disk I/O, database queries, subprocess calls - all need timeouts.
5. **Verify error paths**: Look at try-except blocks - are they specific? Do they recover? Or just log-and-continue?
6. **Consider cascading failures**: If one component fails, does it take down the whole system?
7. **Look for resource leaks**: Files, connections, memory - are they always cleaned up?
8. **Check observability**: Can failures be diagnosed from logs/metrics?
9. **Prioritize by risk**: Focus on CRITICAL/HIGH severity first. MONITOR issues are nice-to-fix.

**Deliverable**: Comprehensive reliability audit report with prioritized findings and remediation roadmap.
