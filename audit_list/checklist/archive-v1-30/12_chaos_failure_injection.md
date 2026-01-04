# Chaos / Failure Injection Audit Prompt (Production-Ready, Resilience Testing)

## Role
Act as a Senior Chaos Engineer and Site Reliability Engineer (SRE). Perform a comprehensive Chaos / Failure Injection Audit on the provided codebase to identify how the system behaves under adverse conditions and ensure graceful degradation.

## Primary Goal
Identify failure modes, missing error handling, and resilience gaps that will cause cascading failures, data corruption, or poor user experience when dependencies fail or behave unexpectedly.

## Context
- This code was developed with a focus on speed ("vibecoded") and happy-path scenarios.
- Production environments experience failures: network issues, dependency outages, resource exhaustion, and partial failures.
- I need you to find where the system will break badly vs. degrade gracefully.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn
- Document Processing: Docling (ML models, OCR, layout detection)
- Database: SQLite3 (file-based, single-writer)
- Image Processing: OpenCV, Pillow, pdf2image
- External Integration: Label Studio SDK
- Real-time: WebSockets
- Frontend: React 19 + TypeScript 5.9 + Zustand

## Failure Scenarios to Test
The audit should cover how the system handles:
- Label Studio server unavailable (connection refused, timeouts, 5xx errors)
- Docling model loading failures (missing models, CUDA errors, OOM)
- Corrupt or malformed PDF files
- SQLite database locked or corrupted
- File system failures (disk full, permission denied)
- WebSocket connection drops during processing
- Memory exhaustion during large document processing
- Partial checkpoint corruption

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (error handling patterns, retry logic, fallback mechanisms), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - Error handling patterns (try/except scope, exception types caught)
   - Retry mechanisms (if any exist)
   - Timeout configurations for external calls
   - Fallback/degradation strategies
   - Health check implementations
   - Circuit breaker patterns (if any)
2) If you cannot infer any of the above, mark as "Needs Confirmation" and provide best-practice recommendations.

## Audit Requirements
Scan the files and generate a report identifying how the system handles (or fails to handle) the failure scenarios below.
Include "Suspicious Patterns" when something looks risky but requires confirmation.

---

## 1) External Dependency Failures

### A) Label Studio Unavailability
- Identify all Label Studio SDK calls and their error handling.
- Check for: connection timeouts, retry logic, graceful fallback when Label Studio is down.
- Common failures: Connection refused, 5xx responses, authentication failures, rate limiting.
- Suggested Fix: Circuit breaker pattern, cached responses, user notification of degraded mode.

### B) Docling Model Loading Failures
- Identify model initialization code and error handling.
- Check for: Missing model files, CUDA/GPU errors, insufficient memory, version mismatches.
- Common failures: Model download failures, corrupted model files, incompatible hardware.
- Suggested Fix: Model availability checks at startup, CPU fallback, clear error messages to user.

### C) pdf2image / Poppler Failures
- Identify PDF rendering calls and their error handling.
- Check for: Missing poppler binaries, corrupted PDFs, password-protected PDFs.
- Common failures: Subprocess errors, timeout on large PDFs, missing system dependencies.
- Suggested Fix: Pre-validation, timeouts, fallback rendering strategies.

---

## 2) Database Failures (SQLite-Specific)

### A) Database Lock Contention
- Identify concurrent write patterns and transaction handling.
- Check for: Long-running transactions, missing WAL mode, concurrent access patterns.
- Common failures: "database is locked" errors, write timeouts, corrupted writes.
- Suggested Fix: WAL mode, connection pooling, transaction scoping, retry with backoff.

### B) Database Corruption Handling
- Identify database initialization and integrity checks.
- Check for: Schema validation, corruption detection, backup/recovery mechanisms.
- Common failures: Silent corruption, missing tables, schema drift.
- Suggested Fix: Integrity checks on startup, schema versioning, automated backups.

### C) Disk Space Exhaustion
- Identify disk write operations without space checks.
- Check for: Checkpoint files, uploaded documents, temporary files, database growth.
- Common failures: Silent failures, corrupted partial writes, crash loops.
- Suggested Fix: Disk space monitoring, cleanup policies, graceful rejection of new uploads.

---

## 3) File System Failures

### A) Checkpoint Read/Write Failures
- Identify checkpoint save/load operations and error handling.
- Check for: Atomic writes (temp file + rename), partial write handling, permission errors.
- Common failures: Corrupted checkpoints, missing checkpoint files, permission denied.
- Suggested Fix: Atomic writes, checksums, backup copies, validation on load.

### B) Upload Directory Failures
- Identify file upload handling and storage operations.
- Check for: Directory creation, file write permissions, temp file cleanup.
- Common failures: Directory not found, permission denied, disk full.
- Suggested Fix: Directory pre-creation, permission checks, cleanup on failure.

### C) Temporary File Cleanup
- Identify temporary file creation and cleanup patterns.
- Check for: Orphaned temp files, cleanup in finally blocks, process crash handling.
- Common failures: Disk space exhaustion from orphaned files, cleanup race conditions.
- Suggested Fix: Temp directory isolation, periodic cleanup, process-level cleanup hooks.

---

## 4) Network & WebSocket Failures

### A) WebSocket Connection Drops
- Identify WebSocket lifecycle management and reconnection logic.
- Check for: Heartbeat/ping-pong, reconnection with backoff, state sync after reconnect.
- Common failures: Silent disconnection, lost progress updates, duplicate messages.
- Suggested Fix: Heartbeat mechanism, automatic reconnection, message acknowledgment.

### B) WebSocket Message Delivery Failures
- Identify message sending patterns and error handling.
- Check for: Send failures, message queuing during disconnect, message ordering.
- Common failures: Lost messages, out-of-order delivery, client state divergence.
- Suggested Fix: Message acknowledgment, idempotent message handling, state reconciliation.

### C) HTTP Request Timeouts
- Identify all HTTP calls and their timeout configurations.
- Check for: Missing timeouts, appropriate timeout values, timeout handling.
- Common failures: Hanging requests, resource exhaustion, cascading timeouts.
- Suggested Fix: Explicit timeouts on all external calls, timeout budgets, circuit breakers.

---

## 5) Processing Pipeline Failures

### A) Mid-Pipeline Failures
- Identify error handling at each pipeline stage.
- Check for: Stage isolation, checkpoint recovery, partial progress preservation.
- Common failures: Lost work on failure, inconsistent state, stuck documents.
- Suggested Fix: Per-stage checkpointing, atomic stage transitions, recovery mechanisms.

### B) Memory Exhaustion During Processing
- Identify memory-intensive operations (large PDFs, image processing, ML inference).
- Check for: Memory limits, streaming patterns, cleanup after processing.
- Common failures: OOM kills, process crashes, incomplete processing.
- Suggested Fix: Memory-aware processing, chunking, resource limits, graceful rejection.

### C) CPU-Bound Blocking
- Identify synchronous CPU-intensive operations on the event loop.
- Check for: Blocking calls without run_in_executor, long-running computations.
- Common failures: Event loop starvation, timeout on health checks, WebSocket disconnects.
- Suggested Fix: Offload to thread pool, async patterns, progress updates.

---

## 6) Input Validation & Malformed Data

### A) Corrupt PDF Handling
- Identify PDF parsing and validation code.
- Check for: PDF structure validation, error handling on parse failures, resource cleanup.
- Common failures: Crash on malformed PDFs, hung processing, resource leaks.
- Suggested Fix: Pre-validation, try/except with cleanup, user-friendly error messages.

### B) Checkpoint Schema Mismatches
- Identify checkpoint loading and schema validation.
- Check for: Version checks, missing field handling, type validation.
- Common failures: KeyError/TypeError on load, silent data corruption, crash on old checkpoints.
- Suggested Fix: Schema versioning, migration logic, validation with clear errors.

### C) Malicious Input Handling
- Identify input sanitization patterns.
- Check for: Path traversal prevention, file type validation (magic bytes), size limits.
- Common failures: Security vulnerabilities, resource exhaustion attacks, data corruption.
- Suggested Fix: Strict validation, sandbox processing, resource limits.

---

## 7) Partial Failure & Degraded Operation

### A) Graceful Degradation Patterns
- Identify what features can operate when dependencies are unavailable.
- Check for: Feature flags, fallback modes, user notifications of degraded state.
- Common failures: All-or-nothing operation, unclear error states, user confusion.
- Suggested Fix: Define degradation levels, implement fallbacks, clear status indicators.

### B) Health Check Accuracy
- Identify health check endpoints and what they verify.
- Check for: Dependency health checks, readiness vs. liveness, timeout handling.
- Common failures: False healthy status, missing critical dependency checks.
- Suggested Fix: Deep health checks, dependency status inclusion, fast failure detection.

### C) Error Propagation & User Feedback
- Identify error handling and user-facing error messages.
- Check for: Error classification, user-friendly messages, actionable guidance.
- Common failures: Generic "Internal Server Error", technical stack traces, no recovery guidance.
- Suggested Fix: Error categorization, user-friendly messages, retry/recovery suggestions.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s)
Failure Category: External Dependency | Database | File System | Network | Pipeline | Input Validation | Degradation

The Problem:
- 2-4 sentences explaining the failure mode and its impact.
- Be specific about consequences: data loss, user impact, recovery difficulty, cascading effects.

Failure Scenario:
- Describe the specific failure condition that triggers this issue.
- Example: "When Label Studio returns 503 during project creation..."
- Include Likelihood: High | Medium | Low (based on common production scenarios)

Current Behavior:
- What happens now when this failure occurs?
- Does it crash? Hang? Return misleading errors? Corrupt data?

Impact Assessment:
- User Impact: None | Minor | Significant | Critical
- Data Risk: None | Recoverable | Potential Loss | Corruption
- Recovery: Automatic | Manual Intervention | Complex Recovery | Data Loss

How to Verify:
- Concrete chaos testing step (kill process, inject latency, corrupt file, etc.)
- Example: "docker-compose stop label-studio && trigger document upload"

The Fix:
- Provide the resilience pattern to implement.
- Show code snippet for error handling/fallback.
- Include configuration changes if needed.

Trade-off Consideration:
- Note complexity, performance impact, and any false positive risks.
- If acceptable at small scale, mark as MONITOR with trigger conditions.
```

## Severity Classification
- **CRITICAL**: Causes data loss, corruption, or complete system unavailability.
- **HIGH**: Causes significant user-facing failures or requires manual intervention to recover.
- **MEDIUM**: Causes degraded experience but system remains functional.
- **MONITOR**: Edge case or unlikely scenario; watch for production occurrences.

---

## Chaos Testing Recommendations

### Recommended Chaos Tests for This Stack

1) **Label Studio Failure Injection**
   - Stop Label Studio container during active operations
   - Inject 5xx responses with a proxy
   - Add network latency (100ms-2s) to Label Studio calls
   - Revoke API credentials mid-session

2) **SQLite Stress Testing**
   - Concurrent write load testing
   - Kill process during write operations
   - Corrupt database file partially
   - Fill disk during write operations

3) **Docling Model Failures**
   - Remove model files after startup
   - Simulate CUDA OOM errors
   - Inject model loading timeouts
   - Corrupt model cache

4) **File System Chaos**
   - Fill disk to capacity
   - Remove checkpoint directory during processing
   - Change permissions on upload directory
   - Corrupt checkpoint files partially

5) **WebSocket Disruption**
   - Kill connections during progress updates
   - Inject message delays and reordering
   - Flood with invalid messages
   - Simulate client reconnection storms

6) **Processing Pipeline Failures**
   - Kill process at each pipeline stage
   - Inject OOM at specific stages
   - Corrupt intermediate stage data
   - Timeout specific processing steps

---

## Vibe Score Rubric (Resilience Readiness 1-10)

Rate overall resilience based on failure handling quality:
- **9-10**: Graceful degradation, clear error handling, automatic recovery.
- **7-8**: Good error handling, minor gaps in edge cases.
- **5-6**: Basic error handling, some failure modes cause issues.
- **3-4**: Poor error handling, many failure modes unhandled.
- **<3**: Critical failures likely; no resilience patterns implemented.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 resilience improvements (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (critical failure modes)
2) Fix Soon (high-impact improvements)
3) Monitor (edge cases, chaos test regularly)

## Also include:
- Estimated time to implement all Fix Now items (range is fine)
- Chaos testing infrastructure recommendations:
  - Tools: toxiproxy, chaos-mesh, custom scripts
  - Test environment setup
  - Failure injection patterns for this stack
  - Monitoring to add before chaos testing:
    - Error rate by type
    - Recovery time metrics
    - Dependency health status
    - User-facing error frequency
