# Reliability & Resilience Audit (Consolidated)

**Priority**: P1 (Critical)
**Merged From**: Archive v1-30 #3 (Reliability & Resilience), #12 (Chaos/Failure Injection)
**Focus**: Production readiness, fault tolerance, graceful degradation, chaos testing

---

## Role & Objective

Act as a **Senior Site Reliability Engineer (SRE)** with 15+ years experience building fault-tolerant distributed systems and conducting chaos engineering. Perform a ruthless reliability audit of the Docling-Interactive codebase to identify every timeout missing, retry absent, error path unhandled, resource leak possible, and cascading failure scenario lurking in the code.

**⚠️ AI-CODING RISK**: Vibecoded systems typically lack resilience patterns, focus on happy paths, and have brittle error handling.

**🐍 PYTHON/FASTAPI**: Async I/O requires explicit timeouts, SQLite has write lock contention, and resource cleanup must use context managers.

---

## Context

This 15-stage interactive document processing pipeline was developed rapidly with AI assistance ("vibecoded"), focusing on feature delivery and happy-path functionality. The system likely lacks:

- Timeout protection on long-running operations
- Retry logic with exponential backoff
- Circuit breakers to prevent cascading failures
- Graceful degradation when dependencies fail
- Proper resource cleanup and memory management
- Checkpoint corruption detection and recovery
- WebSocket reconnection logic and state sync
- Database write lock handling
- Health checks validating critical dependencies
- Clean startup/shutdown sequences

---

## Tech Stack

### Backend
- **Runtime**: Python 3.12
- **Framework**: FastAPI + Uvicorn (ASGI)
- **Document Processing**: Docling (CPU/memory intensive, can be slow)
- **Validation**: Pydantic v2
- **Database**: SQLite3 (single-writer, write lock contention)
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
- **Communication**: fetch API + WebSocket

### Infrastructure
- **Container**: Docker (Python 3.11-slim-bookworm)
- **API**: REST + WebSocket
- **Storage**: Local filesystem (checkpoints, uploads)
- **Deployment**: Uvicorn workers (multi-worker concurrency issues)

---

## Audit Checklist

### 1. Timeout Handling

⚠️ **Every I/O operation must have explicit timeout protection**

#### 1.1 HTTP Client Timeouts
- [ ] Check all FastAPI route handlers for request timeouts
- [ ] Verify Label Studio SDK calls have timeouts configured
- [ ] Check VLM service calls have timeouts
- [ ] Verify all external HTTP calls specify timeouts
- [ ] Ensure timeout values are environment-configurable

**Requirements**:
- Connection timeout: max 5s for establishing connection
- Read timeout: 30s for document processing, 120s for VLM inference
- Total timeout: End-to-end SLA enforcement
- All timeouts configurable via environment variables

#### 1.2 Database Operation Timeouts
- [ ] Check SQLite SELECT queries have timeouts
- [ ] Check INSERT/UPDATE/DELETE operations have timeouts
- [ ] Verify write lock timeout is bounded (not infinite)
- [ ] Check transaction timeouts exist
- [ ] Verify connection timeout is set

**Requirements**:
- Query timeout: 5-10s max
- Write lock timeout: 2s max before retry
- Connection timeout: 3s max

#### 1.3 Document Processing Timeouts
- [ ] Check each of 15 pipeline stages has timeout
- [ ] Verify OCR operations have timeout (can hang on corrupted PDFs)
- [ ] Check layout detection ML inference has timeout
- [ ] Verify TableFormer operations have timeout
- [ ] Check VLM picture description has timeout (30-60s typical)
- [ ] Verify graceful cancellation cleans up partial results

**Requirements**:
- Per-stage timeout: configurable, default 60s
- Total pipeline timeout: configurable, default 10 minutes
- Graceful cancellation with cleanup

#### 1.4 File I/O Timeouts
- [ ] Check PDF loading has timeout (large PDFs can block)
- [ ] Verify image processing operations have timeouts
- [ ] Check checkpoint save/load has timeout
- [ ] Verify temp file operations have timeouts

**Requirements**:
- File read timeout: 30s max
- Image operation timeout: 15s per image
- Checkpoint I/O timeout: 5s max

#### 1.5 WebSocket Timeouts
- [ ] Check WebSocket connection establishment timeout
- [ ] Verify message delivery doesn't wait forever
- [ ] Check heartbeat/ping-pong mechanism exists
- [ ] Verify dead connection detection

**Requirements**:
- Connection timeout: 10s
- Message timeout: 5s before dropping slow clients
- Ping interval: 30s, pong timeout: 10s

---

### 2. Retry Logic with Exponential Backoff

⚠️ **Transient failures must be retried intelligently**

#### 2.1 Retryable vs Non-Retryable Error Classification
- [ ] Verify errors are classified as retryable vs non-retryable
- [ ] Check network errors are retried
- [ ] Check 503 Service Unavailable is retried
- [ ] Check SQLite BUSY errors are retried
- [ ] Check temporary file locks are retried
- [ ] Verify 400/404/validation errors are NOT retried
- [ ] Check retry attempts are logged with context

**Retryable**: Network errors, 503, SQLite BUSY, temp file locks
**Non-retryable**: 400, 404, validation errors, corrupted data

#### 2.2 Exponential Backoff Configuration
- [ ] Verify retry logic uses exponential backoff
- [ ] Check jitter is added to prevent thundering herd
- [ ] Verify max delay cap exists
- [ ] Check max attempts limit exists
- [ ] Verify backoff multiplier is 2x (standard)

**Requirements**:
- Pattern: `delay = base_delay * (2 ^ attempt) + jitter`
- Initial delay: 100ms-1s
- Max delay: 30s-60s
- Max attempts: 3-5
- Jitter: +/-20% randomization

#### 2.3 Retry Scenarios
- [ ] Database writes retry on SQLite BUSY
- [ ] External API calls retry on transient failures
- [ ] File operations retry on temporary locks
- [ ] Checkpoint saves retry on filesystem contention
- [ ] Network requests retry on connection errors

---

### 3. Circuit Breaker Patterns

⚠️ **Prevent cascading failures from slow/failing dependencies**

#### 3.1 External Service Circuit Breakers
- [ ] Check Label Studio API has circuit breaker
- [ ] Check VLM inference services have circuit breaker
- [ ] Check OCR engine has circuit breaker (if external)
- [ ] Verify fail-fast response when circuit OPEN

**Requirements**:
- Failure threshold: 5 failures in 10s → OPEN
- Success threshold: 3 successes in HALF-OPEN → CLOSED
- Timeout: 30s in OPEN before attempting HALF-OPEN
- Fail-fast: Don't queue requests when OPEN

#### 3.2 Database Circuit Breaker
- [ ] Check SQLite write lock failures trigger circuit breaker
- [ ] Verify avalanche of retries is prevented
- [ ] Check fallback to read-only mode exists
- [ ] Verify recovery on successful writes

**Requirements**:
- Threshold: 10 lock failures in 5s → OPEN
- Recovery: 2 successful writes → CLOSED
- Fallback: Read-only mode or in-memory caching

#### 3.3 Graceful Degradation
- [ ] Label Studio unavailable → disable export feature
- [ ] VLM unavailable → skip picture descriptions
- [ ] OCR failing → use cached results or skip
- [ ] Verify clear user messaging (not just 500 errors)
- [ ] Check feature flags exist to disable degraded features
- [ ] Verify automatic recovery when circuit closes

---

### 4. Load Shedding and Graceful Degradation

⚠️ **System must degrade gracefully under overload**

#### 4.1 Request Queue Management
- [ ] Check max queue depth exists (e.g., 100 documents)
- [ ] Verify new uploads rejected when queue full
- [ ] Check priority queue exists (user requests > batch jobs)
- [ ] Verify 429 Too Many Requests returned when overloaded
- [ ] Check queue depth exposed in health check
- [ ] Verify queue limits are configurable

#### 4.2 Resource-Based Load Shedding
- [ ] Check CPU monitoring exists (> 90% for 30s)
- [ ] Check memory monitoring exists (> 85% for 30s)
- [ ] Check disk I/O saturation detection exists
- [ ] Check concurrent task limit exists
- [ ] Verify load shedding occurs before OOM killer
- [ ] Check graceful rejection (not crashes)

---

### 5. Startup and Shutdown Sequences

🐍 **Clean initialization and termination prevents corrupted state**

#### 5.1 Startup Sequence
- [ ] Configuration loaded and validated first
- [ ] Database initialized (schema check, migrations)
- [ ] Checkpoint directory validated (exists, writable)
- [ ] Docling models pre-loaded (if applicable)
- [ ] External services connected with retry
- [ ] Health check endpoint started FIRST
- [ ] API server started LAST
- [ ] Fail fast if critical dependencies unavailable
- [ ] Each initialization step logged
- [ ] Readiness probe returns 503 until fully initialized

**Order**:
1. Load configuration
2. Initialize database
3. Validate checkpoint directory
4. Pre-load models
5. Connect external services
6. Start health check endpoint
7. Start API server

#### 5.2 Shutdown Sequence
- [ ] Stop accepting new requests (return 503)
- [ ] Finish in-flight requests (with timeout)
- [ ] Save checkpoint state
- [ ] Close WebSocket connections gracefully
- [ ] Flush pending database writes
- [ ] Close database connections
- [ ] Cleanup temporary files
- [ ] SIGTERM handler exists (Kubernetes compatible)
- [ ] Shutdown timeout exists (30s before forceful kill)
- [ ] Shutdown progress logged

---

### 6. Health Checks and Readiness Probes

⚠️ **Accurate health reporting for load balancers and orchestrators**

#### 6.1 Liveness Probe
- [ ] `GET /health/live` endpoint exists
- [ ] Returns 200 if process running
- [ ] Ultra-lightweight (no dependencies)
- [ ] Sub-millisecond response time
- [ ] Never blocks

#### 6.2 Readiness Probe
- [ ] `GET /health/ready` endpoint exists
- [ ] Checks database is writable
- [ ] Checks checkpoint directory accessible
- [ ] Checks critical external services reachable (with timeout)
- [ ] Checks circuit breakers not all OPEN
- [ ] Checks processing queue not full
- [ ] Total timeout: 5s
- [ ] Returns 503 if not ready
- [ ] Includes detailed status in response body

---

### 7. Error Handling and Recovery

⚠️ **Comprehensive error handling with recovery strategies**

#### 7.1 Pipeline Stage Error Recovery
- [ ] Preprocessing failure → retry with different parameters
- [ ] OCR failure → fall back to basic text extraction
- [ ] Layout detection failure → use heuristic fallback
- [ ] Table extraction failure → skip or use simpler parser
- [ ] VLM failure → skip descriptions, continue pipeline
- [ ] Checkpoint created before each stage (rollback point)
- [ ] Explicit recovery strategy per stage documented
- [ ] Recovery attempts logged
- [ ] User notified of degraded output

#### 7.2 Checkpoint Corruption Handling
- [ ] Validate checkpoint on load (JSON schema)
- [ ] Atomic writes (temp file + rename)
- [ ] Checksum/hash validation exists
- [ ] Fallback to previous checkpoint works
- [ ] Corrupted checkpoints deleted (with backup)

**Scenarios**:
- Incomplete write (crash during save)
- Corrupted JSON (filesystem error)
- Schema version mismatch
- Missing checkpoint file

#### 7.3 Database Error Recovery
- [ ] SQLITE_BUSY → retry with backoff
- [ ] SQLITE_LOCKED → retry with backoff
- [ ] SQLITE_CORRUPT → fail loudly, log for recovery
- [ ] Disk full → return 507 Insufficient Storage
- [ ] WAL mode enabled (better concurrency)
- [ ] Busy timeout configured (5s)
- [ ] Connection pooling prevents leaks

---

### 8. Dependency Failure Handling

⚠️ **System must survive dependency failures**

#### 8.1 Label Studio Unavailable
- [ ] Service down → disable export feature
- [ ] Network partition → queue export requests
- [ ] Authentication failure → return 503 on export endpoints
- [ ] Circuit breaker protection exists
- [ ] User-facing error message clear
- [ ] Automatic retry on recovery

**Scenarios**: Service down, network partition, auth failure

#### 8.2 Docling Model Loading Failure
- [ ] Model file corrupted → fail startup
- [ ] Insufficient memory → fail startup with clear error
- [ ] Version mismatch → fail startup with version info
- [ ] Detailed error logged
- [ ] Health check reports not ready

**Critical dependency - must fail startup**

---

### 9. Concurrent Processing Safety

🐍 **Multi-worker and async safety**

#### 9.1 SQLite Write Lock Handling
- [ ] WAL mode enabled
- [ ] Busy timeout configured
- [ ] Retry logic on SQLITE_BUSY exists
- [ ] Short transactions (acquire, write, release)
- [ ] Long-running transactions avoided
- [ ] Deadlock prevention implemented

**Issues**: Multiple workers writing, long transactions, deadlocks

#### 9.2 Checkpoint File Concurrency
- [ ] File locking exists (fcntl on Linux)
- [ ] Atomic writes (temp + rename)
- [ ] Reader validation detects incomplete writes
- [ ] Multiple workers don't corrupt same checkpoint

---

### 10. Resource Cleanup and Leak Prevention

🐍 **No resource leaks under load**

#### 10.1 File Handle Leaks
- [ ] Context managers used for all file I/O
- [ ] Explicit cleanup in finally blocks
- [ ] Temp file auto-deletion
- [ ] File handle limit monitoring

**Sources**: PDF files, images, temp files

#### 10.2 Memory Leaks
- [ ] Cache eviction policies exist
- [ ] WebSocket connections cleaned up
- [ ] Circular references avoided
- [ ] In-memory queues bounded
- [ ] Memory profiling in tests

**Sources**: Cached documents, WebSocket connections, growing queues

#### 10.3 Database Connection Leaks
- [ ] Connection pooling with max size
- [ ] Context managers for transactions
- [ ] Connection timeout set
- [ ] Leak detection in health check

---

## Chaos & Failure Injection Testing

**⚠️ CRITICAL SECTION**: Production failures are inevitable. Test them before users encounter them.

### 11. External Dependency Failure Scenarios

#### 11.1 Label Studio Unavailability
- [ ] Test: Stop Label Studio container during document export
- [ ] Test: Inject 5xx responses with proxy during project creation
- [ ] Test: Add network latency (100ms-2s) to Label Studio calls
- [ ] Test: Revoke API credentials mid-session
- [ ] Test: Rate limiting from Label Studio
- [ ] Verify: Connection refused handled gracefully
- [ ] Verify: Timeouts configured and working
- [ ] Verify: Circuit breaker opens after failures
- [ ] Verify: User notified of degraded mode
- [ ] Verify: Automatic retry on recovery

**Common Failures**: Connection refused, 5xx responses, auth failures, rate limiting

**How to Verify**:
```bash
# Stop Label Studio during operation
docker-compose stop label-studio
# Trigger document export and observe behavior

# Inject latency with toxiproxy
toxiproxy-cli toxic add -t latency -a latency=2000 label-studio

# Inject errors
toxiproxy-cli toxic add -t http -a status=503 label-studio
```

#### 11.2 Docling Model Loading Failures
- [ ] Test: Remove model files after startup
- [ ] Test: Simulate CUDA OOM errors
- [ ] Test: Inject model loading timeouts
- [ ] Test: Corrupt model cache
- [ ] Test: Missing model files at startup
- [ ] Test: Version mismatch scenarios
- [ ] Verify: CPU fallback works when GPU unavailable
- [ ] Verify: Clear error messages to user
- [ ] Verify: Health check reports not ready
- [ ] Verify: Startup fails gracefully on missing models

**Common Failures**: Missing files, CUDA errors, insufficient memory, corrupted cache

**How to Verify**:
```bash
# Remove model files
rm -rf ~/.cache/docling/models/*
# Restart and observe error handling

# Simulate OOM
# Set memory limit in docker-compose and trigger processing
```

#### 11.3 pdf2image / Poppler Failures
- [ ] Test: Missing poppler binaries
- [ ] Test: Corrupted PDF files
- [ ] Test: Password-protected PDFs
- [ ] Test: Timeout on large PDFs (100+ pages)
- [ ] Test: Subprocess errors
- [ ] Verify: Pre-validation catches corrupt PDFs
- [ ] Verify: Timeouts prevent hanging
- [ ] Verify: Fallback rendering strategies work
- [ ] Verify: Clear error messages for unsupported PDFs

**Common Failures**: Missing dependencies, corrupted PDFs, subprocess timeouts

**How to Verify**:
```bash
# Upload corrupted PDF
# Upload password-protected PDF
# Upload extremely large PDF (1000+ pages)
# Remove poppler from PATH and test
```

---

### 12. Database Failure Scenarios (SQLite-Specific)

#### 12.1 Database Lock Contention
- [ ] Test: Concurrent write load from multiple workers
- [ ] Test: Long-running transaction blocking writes
- [ ] Test: Kill process during write operation
- [ ] Test: Simulate deadlock scenarios
- [ ] Verify: WAL mode enabled
- [ ] Verify: Retry with backoff on SQLITE_BUSY
- [ ] Verify: Transaction scoping is short
- [ ] Verify: "database is locked" errors handled

**Common Failures**: "database is locked", write timeouts, corrupted writes

**How to Verify**:
```bash
# Concurrent write stress test
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/upload &
done
wait

# Kill during write
curl -X POST http://localhost:8000/api/checkpoint &
killall -9 python3
# Check for corruption on restart
```

#### 12.2 Database Corruption Handling
- [ ] Test: Partially corrupt database file
- [ ] Test: Schema version mismatch
- [ ] Test: Missing tables
- [ ] Test: Integrity check on startup
- [ ] Verify: Corruption detected and reported
- [ ] Verify: Schema validation at startup
- [ ] Verify: Automated backups exist
- [ ] Verify: Recovery mechanisms work

**Common Failures**: Silent corruption, missing tables, schema drift

**How to Verify**:
```bash
# Corrupt database
dd if=/dev/urandom of=database.db bs=1024 count=10 seek=100 conv=notrunc

# Check integrity
sqlite3 database.db "PRAGMA integrity_check;"
```

#### 12.3 Disk Space Exhaustion
- [ ] Test: Fill disk to capacity during checkpoint save
- [ ] Test: Fill disk during document upload
- [ ] Test: Fill disk during database write
- [ ] Verify: Disk space monitoring exists
- [ ] Verify: Graceful rejection of new uploads
- [ ] Verify: Cleanup policies for old files
- [ ] Verify: Partial writes don't corrupt state

**Common Failures**: Silent failures, corrupted writes, crash loops

**How to Verify**:
```bash
# Fill disk
dd if=/dev/zero of=/tmp/fillup bs=1M count=10000

# Trigger operations and observe behavior
# Verify cleanup happens automatically
```

---

### 13. File System Failure Scenarios

#### 13.1 Checkpoint Read/Write Failures
- [ ] Test: Remove checkpoint directory during processing
- [ ] Test: Change permissions on checkpoint directory
- [ ] Test: Corrupt checkpoint file partially
- [ ] Test: Kill process during checkpoint write
- [ ] Test: Fill disk during checkpoint save
- [ ] Verify: Atomic writes (temp file + rename)
- [ ] Verify: Checksums detect corruption
- [ ] Verify: Backup copies maintained
- [ ] Verify: Validation on load catches corruption

**Common Failures**: Corrupted checkpoints, permission denied, partial writes

**How to Verify**:
```bash
# Remove checkpoint directory mid-processing
rm -rf checkpoints/ &
# Start processing

# Corrupt checkpoint
truncate -s 50% checkpoints/doc123/stage_5.json

# Permission test
chmod 000 checkpoints/
# Trigger checkpoint save
```

#### 13.2 Upload Directory Failures
- [ ] Test: Upload directory doesn't exist
- [ ] Test: Permission denied on upload directory
- [ ] Test: Disk full during upload
- [ ] Verify: Directory pre-creation at startup
- [ ] Verify: Permission checks before upload
- [ ] Verify: Cleanup on upload failure
- [ ] Verify: Clear error messages to user

**Common Failures**: Directory not found, permission denied, disk full

**How to Verify**:
```bash
# Remove upload directory
rmdir uploads/

# Change permissions
chmod 555 uploads/

# Fill disk and upload large file
```

#### 13.3 Temporary File Cleanup
- [ ] Test: Process crash leaves orphaned temp files
- [ ] Test: Cleanup race conditions
- [ ] Test: Periodic cleanup removes old temp files
- [ ] Verify: Temp directory isolation
- [ ] Verify: Process-level cleanup hooks
- [ ] Verify: No disk space exhaustion from orphans

**Common Failures**: Disk exhaustion from orphaned files, cleanup races

**How to Verify**:
```bash
# Kill process repeatedly
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/process &
  sleep 2
  killall -9 python3
done

# Check for orphaned files
ls -lh /tmp/ | grep -i temp
```

---

### 14. Network & WebSocket Failure Scenarios

#### 14.1 WebSocket Connection Drops
- [ ] Test: Kill WebSocket connection during processing
- [ ] Test: Network partition mid-processing
- [ ] Test: Client reconnection storms (100+ simultaneous)
- [ ] Test: Silent disconnection (no FIN/RST)
- [ ] Verify: Heartbeat/ping-pong mechanism works
- [ ] Verify: Automatic reconnection with backoff
- [ ] Verify: State sync after reconnect
- [ ] Verify: Progress updates resume correctly

**Common Failures**: Silent disconnection, lost updates, duplicate messages

**How to Verify**:
```bash
# Kill WebSocket connection
# Use browser dev tools to close connection mid-processing

# Network partition with iptables
iptables -A INPUT -p tcp --dport 8000 -j DROP
# Wait 30s, then restore
iptables -D INPUT -p tcp --dport 8000 -j DROP
```

#### 14.2 WebSocket Message Delivery Failures
- [ ] Test: Send messages faster than client can consume
- [ ] Test: Client disconnects before message ACK
- [ ] Test: Out-of-order message delivery
- [ ] Verify: Message acknowledgment exists
- [ ] Verify: Idempotent message handling
- [ ] Verify: State reconciliation on reconnect
- [ ] Verify: Slow clients don't block server

**Common Failures**: Lost messages, out-of-order delivery, state divergence

**How to Verify**:
```bash
# Slow client simulation
# Inject network latency and check message buffering

# Disconnect before ACK
# Close connection immediately after sending message
```

#### 14.3 HTTP Request Timeouts
- [ ] Test: External API call takes > 60s
- [ ] Test: Hanging requests (no response)
- [ ] Test: Connection timeout during DNS resolution
- [ ] Verify: All external calls have explicit timeouts
- [ ] Verify: Timeout budgets prevent cascading delays
- [ ] Verify: Circuit breakers prevent timeout avalanche

**Common Failures**: Hanging requests, resource exhaustion, cascading timeouts

**How to Verify**:
```bash
# Inject latency with toxiproxy
toxiproxy-cli toxic add -t latency -a latency=120000 external-api

# Hanging connection
toxiproxy-cli toxic add -t timeout -a timeout=0 external-api
```

---

### 15. Processing Pipeline Failure Scenarios

#### 15.1 Mid-Pipeline Failures
- [ ] Test: Kill process at each of 15 pipeline stages
- [ ] Test: Inject exception at random stage
- [ ] Test: Corrupt intermediate stage data
- [ ] Test: Timeout specific processing steps
- [ ] Verify: Per-stage checkpointing works
- [ ] Verify: Pipeline can resume from any stage
- [ ] Verify: Atomic stage transitions
- [ ] Verify: Partial progress preserved

**Common Failures**: Lost work, inconsistent state, stuck documents

**How to Verify**:
```bash
# Kill at random stage
for stage in {1..15}; do
  # Start processing
  curl -X POST http://localhost:8000/api/process/doc123/stage/$stage &
  sleep 5
  killall -9 python3

  # Restart and verify recovery
done
```

#### 15.2 Memory Exhaustion During Processing
- [ ] Test: Upload 500MB PDF
- [ ] Test: Process 1000-page document
- [ ] Test: Concurrent processing of 10 large documents
- [ ] Test: ML model inference OOM
- [ ] Verify: Memory limits enforced
- [ ] Verify: Streaming patterns used for large files
- [ ] Verify: Cleanup after processing
- [ ] Verify: Graceful rejection when memory low

**Common Failures**: OOM kills, process crashes, incomplete processing

**How to Verify**:
```bash
# Set memory limit and test
docker run --memory="512m" app
# Upload large PDF and observe

# Concurrent large document processing
for i in {1..10}; do
  curl -X POST -F "file=@large.pdf" http://localhost:8000/api/upload &
done
```

#### 15.3 CPU-Bound Blocking
- [ ] Test: Synchronous CPU-intensive operation blocks event loop
- [ ] Test: Long ML inference blocks health checks
- [ ] Test: WebSocket disconnects during CPU-bound work
- [ ] Verify: CPU-intensive work uses run_in_executor
- [ ] Verify: Event loop not starved
- [ ] Verify: Progress updates during long operations
- [ ] Verify: Health checks remain responsive

**Common Failures**: Event loop starvation, timeouts, WebSocket disconnects

**How to Verify**:
```bash
# Monitor event loop lag
# Use asyncio debug mode

# Trigger CPU-intensive operation
# Monitor health check response times
watch -n 1 'curl -s -w "%{time_total}\n" http://localhost:8000/health/live'
```

---

### 16. Input Validation & Malformed Data

#### 16.1 Corrupt PDF Handling
- [ ] Test: Upload PDF with corrupted structure
- [ ] Test: Upload PDF with missing pages
- [ ] Test: Upload PDF with unsupported encoding
- [ ] Test: Upload zero-byte PDF
- [ ] Verify: PDF structure validation exists
- [ ] Verify: Error handling on parse failures
- [ ] Verify: Resource cleanup on failure
- [ ] Verify: User-friendly error messages

**Common Failures**: Crash on malformed PDFs, hung processing, resource leaks

**How to Verify**:
```bash
# Create corrupted PDF
dd if=/dev/urandom of=corrupt.pdf bs=1024 count=100

# Zero-byte file
touch empty.pdf

# Upload and observe error handling
curl -X POST -F "file=@corrupt.pdf" http://localhost:8000/api/upload
```

#### 16.2 Checkpoint Schema Mismatches
- [ ] Test: Load checkpoint from older version
- [ ] Test: Load checkpoint with missing fields
- [ ] Test: Load checkpoint with wrong types
- [ ] Verify: Version checks on load
- [ ] Verify: Missing field handling
- [ ] Verify: Type validation
- [ ] Verify: Migration logic for old checkpoints

**Common Failures**: KeyError/TypeError on load, silent corruption, crashes

**How to Verify**:
```bash
# Modify checkpoint to old schema
# Remove required fields
# Change field types

# Attempt to load and observe validation
```

#### 16.3 Malicious Input Handling
- [ ] Test: Path traversal in file names (../../etc/passwd)
- [ ] Test: Extremely large files (>1GB)
- [ ] Test: Malformed JSON in API requests
- [ ] Test: SQL injection attempts (if any raw SQL)
- [ ] Verify: Path traversal prevention
- [ ] Verify: File type validation (magic bytes)
- [ ] Verify: Size limits enforced
- [ ] Verify: Input sanitization

**Common Failures**: Security vulnerabilities, resource exhaustion, data corruption

**How to Verify**:
```bash
# Path traversal
curl -X POST -F "file=@test.pdf;filename=../../etc/passwd" http://localhost:8000/api/upload

# Huge file
dd if=/dev/zero of=huge.pdf bs=1M count=2000
curl -X POST -F "file=@huge.pdf" http://localhost:8000/api/upload

# Malformed JSON
curl -X POST -H "Content-Type: application/json" -d '{broken json}' http://localhost:8000/api/endpoint
```

---

### 17. Partial Failure & Degraded Operation

#### 17.1 Graceful Degradation Patterns
- [ ] Test: All dependencies down simultaneously
- [ ] Test: Partial feature availability
- [ ] Test: Recovery when dependencies come back
- [ ] Verify: Feature flags exist
- [ ] Verify: Fallback modes implemented
- [ ] Verify: User notifications of degraded state
- [ ] Verify: Clear status indicators in UI

**Common Failures**: All-or-nothing operation, unclear errors, user confusion

**Features that should degrade gracefully**:
- Label Studio unavailable → disable export
- VLM unavailable → skip picture descriptions
- OCR failing → basic text extraction fallback
- Table detection failing → simpler parser

#### 17.2 Health Check Accuracy
- [ ] Test: Health check during dependency failure
- [ ] Test: Health check during overload
- [ ] Test: Health check timeout scenarios
- [ ] Verify: Dependency health included in checks
- [ ] Verify: Readiness vs liveness separated
- [ ] Verify: Fast failure detection (< 5s)
- [ ] Verify: No false healthy status

**Common Failures**: False healthy status, missing dependency checks

**How to Verify**:
```bash
# Stop dependency and check health
docker-compose stop label-studio
curl http://localhost:8000/health/ready
# Should return 503

# Load system and check health
ab -n 1000 -c 100 http://localhost:8000/api/upload
curl http://localhost:8000/health/ready
```

#### 17.3 Error Propagation & User Feedback
- [ ] Test: Various failure scenarios
- [ ] Verify: Errors classified (transient vs permanent)
- [ ] Verify: User-friendly messages (no stack traces)
- [ ] Verify: Actionable guidance provided
- [ ] Verify: Retry/recovery suggestions given

**Common Failures**: Generic "Internal Server Error", technical stack traces

**Good error messages include**:
- What went wrong (user terms)
- Why it happened (if known)
- What user can do (retry, contact support, try different file)
- Expected recovery time (if applicable)

---

## Chaos Testing Infrastructure

### Recommended Tools

#### Toxiproxy (Network Chaos)
- [ ] Install toxiproxy for network failure injection
- [ ] Configure proxies for external dependencies
- [ ] Create toxic profiles (latency, timeout, errors)

```bash
# Install
go install github.com/Shopify/toxiproxy/v2/cmd/toxiproxy-cli@latest

# Create proxy
toxiproxy-cli create label-studio -l localhost:8080 -u label-studio-host:8081

# Add latency
toxiproxy-cli toxic add -t latency -a latency=2000 label-studio

# Add errors
toxiproxy-cli toxic add -t http -a status=503 label-studio
```

#### Custom Chaos Scripts
- [ ] Create script to kill processes at random stages
- [ ] Create script to corrupt files randomly
- [ ] Create script to fill disk gradually
- [ ] Create script to inject database errors

```python
# Example: Random stage killer
import random, subprocess, time
stages = range(1, 16)
while True:
    stage = random.choice(stages)
    time.sleep(random.randint(5, 30))
    subprocess.run(['killall', '-9', 'python3'])
```

#### Docker Chaos
- [ ] Use docker-compose to stop/start services
- [ ] Set resource limits (memory, CPU)
- [ ] Inject network latency with tc/netem

```bash
# Memory limit
docker run --memory="512m" --memory-swap="512m" app

# CPU limit
docker run --cpus="1.5" app

# Network latency
tc qdisc add dev eth0 root netem delay 100ms 20ms
```

### Monitoring Before Chaos Testing

⚠️ **Add these metrics BEFORE running chaos tests**:

- [ ] Error rate by type (transient vs permanent)
- [ ] Recovery time metrics (time to recover from failure)
- [ ] Dependency health status (Label Studio, Docling models)
- [ ] User-facing error frequency
- [ ] Processing queue depth
- [ ] Resource utilization (CPU, memory, disk)
- [ ] Database lock contention rate
- [ ] WebSocket connection churn rate
- [ ] Checkpoint corruption detection rate

```python
# Example: Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

error_counter = Counter('app_errors_total', 'Total errors', ['error_type'])
recovery_time = Histogram('app_recovery_seconds', 'Recovery time')
dependency_health = Gauge('app_dependency_health', 'Dependency health', ['dependency'])
queue_depth = Gauge('app_queue_depth', 'Processing queue depth')
```

---

## Severity Level Definitions

- **CRITICAL**: Causes data loss, corruption, crashes, or cascading failures. Production blocker.
- **HIGH**: Causes request failures, timeouts, or service degradation under load.
- **MEDIUM**: Causes poor user experience, inefficiency, or edge case failures.
- **MONITOR**: Not immediately harmful but creates tech debt or future risk.

---

## Output Format for Findings

For each issue found, use this format:

```
### Finding #X: [Concise Title]

**Location**: `path/to/file.py:line_number` or `component/function_name`

**Risk Category**: [Timeout | Retry | Circuit Breaker | Load Shedding | Startup/Shutdown |
                   Health Check | Error Handling | Dependency Failure | Concurrency | Resource Leak]

**Severity**: [CRITICAL | HIGH | MEDIUM | MONITOR]

**The Problem**:
[2-3 sentences describing the exact issue in the code]

**Reliability Impact**:
[Concrete failure scenario and consequences]
- Under what conditions does this fail?
- What is the user impact?
- What is the cascade risk?

**Failure Scenario**:
- Specific condition that triggers this issue
- Example: "When Label Studio returns 503 during project creation..."
- Likelihood: High | Medium | Low

**Current Behavior**:
- What happens when this failure occurs?
- Does it crash? Hang? Return misleading errors? Corrupt data?

**Impact Assessment**:
- User Impact: None | Minor | Significant | Critical
- Data Risk: None | Recoverable | Potential Loss | Corruption
- Recovery: Automatic | Manual Intervention | Complex Recovery | Data Loss

**How to Verify**:
```bash
# Specific chaos testing commands to reproduce the issue
```

**The Fix**:
```python
# Exact code changes needed
```

**Trade-off Consideration**:
[Performance, complexity, or operational costs of the fix]
```

---

## Reliability Score Rubric (1-10)

After completing the audit, assign a reliability score:

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
- **Chaos testing**: [Specific scenarios to inject failures]
- **Load testing**: [Specific load patterns to validate]
- **Integration tests**: [Specific dependency failure tests]
- **Observability**: [Metrics and alerts to add]

### Chaos Testing Priorities
1. **Label Studio Failure Injection** (External dependency)
2. **SQLite Stress Testing** (Database concurrency)
3. **WebSocket Disruption** (Real-time communication)
4. **Processing Pipeline Failures** (Core functionality)
5. **File System Chaos** (Checkpoints and uploads)

### Estimated Implementation Time
- Fix Now items: [X-Y hours/days]
- Fix Soon items: [X-Y hours/days]
- Monitor items: [X-Y hours/days]
- Total: [X-Y hours/days]

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
10. **Test with chaos**: Use the chaos testing scenarios to validate assumptions.

**Deliverable**: Comprehensive reliability audit report with prioritized findings, chaos testing results, and remediation roadmap.
