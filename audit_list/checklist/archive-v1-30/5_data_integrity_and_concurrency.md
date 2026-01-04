# Data Integrity & Concurrency Audit Prompt (Production-Ready, High-Concurrency)

## Role
Act as a Senior Database Engineer and Distributed Systems Architect. Perform a deep-dive Data Integrity & Concurrency Audit on the provided codebase to identify race conditions, data corruption risks, and consistency gaps before production deployment.

## Primary Goal
Identify where AI-generated logic, shortcuts, and architectural gaps will cause data corruption, lost updates, or inconsistent state under concurrent access, and provide concrete fixes that ensure data integrity.

## Context
- This code was developed with a focus on speed ("vibecoded") and has not yet been stress-tested for concurrent access.
- I need you to find race conditions, atomicity violations, and consistency gaps before running concurrent workloads.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn (async)
- Database: SQLite3 (single-writer limitation, WAL mode considerations)
- State: Pydantic v2 models, JSON checkpoint files
- Processing: Docling pipeline with 15 stages, OpenCV/Pillow image processing
- Integration: Label Studio SDK, WebSockets for real-time updates
- Frontend: React 19 + TypeScript, Zustand state management

## Concurrency Test Target
- 50 concurrent document processing sessions
- 10 concurrent users editing the same document
- Rapid checkpoint save/load cycles (sub-second intervals)
- WebSocket broadcast to 100+ connected clients
- SLO: Zero data loss, zero orphaned state, zero duplicate entries

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (DB schema, connection setup, transaction boundaries, lock patterns), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - SQLite connection mode (WAL vs DELETE journal, busy_timeout setting)
   - Connection pooling strategy (per-request vs singleton vs pool)
   - Transaction isolation level and explicit transaction usage
   - File locking strategy for checkpoints (atomic writes, temp files)
   - Async patterns (asyncio locks, threading considerations)
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) SQLite Concurrency Issues

### A) Write Contention & Lock Timeouts
- Look for multiple concurrent writes without proper busy_timeout configuration.
- Flag missing WAL mode configuration (journal_mode=WAL).
- Identify long-running transactions that block other writers.
- Suggested Fix: Enable WAL mode, set appropriate busy_timeout (5000ms+), minimize transaction scope.

### B) Connection Handling
- Find connection creation per-request without proper pooling.
- Flag connections opened without context managers (no auto-close).
- Identify shared connections across async tasks without thread safety.
- Suggested Fix: Use connection pool (aiosqlite for async), proper context managers, thread-local connections if needed.

### C) Read-Your-Writes Consistency
- Identify patterns where a write is followed by a read that might not see the update.
- Flag missing explicit commits before reads that depend on prior writes.
- Suggested Fix: Explicit commit boundaries, use RETURNING clause where supported.

### D) Schema/Migration Safety
- Find ALTER TABLE or schema changes without proper locking.
- Flag missing transaction wrappers around DDL operations.
- Suggested Fix: Wrap DDL in transactions, use migration tools with locking.

---

## 2) Checkpoint File Atomicity

### A) Non-Atomic File Writes
- Look for direct file writes that could leave partial/corrupted files on crash.
- Pattern: `open(file, 'w').write(data)` without atomic rename pattern.
- Flag missing write-to-temp-then-rename patterns.
- Suggested Fix: Write to `.tmp` file, then `os.rename()` (atomic on POSIX), use `fsync()` for durability.

### B) Checkpoint Race Conditions
- Identify concurrent reads/writes to the same checkpoint file.
- Flag missing file locks (fcntl.flock, portalocker, or equivalent).
- Look for TOCTOU (time-of-check-time-of-use) patterns in checkpoint loading.
- Suggested Fix: File locking, atomic operations, version fields for conflict detection.

### C) Checkpoint Corruption Detection
- Find missing validation after checkpoint load (schema validation, checksums).
- Flag blind trust of checkpoint file contents without Pydantic validation.
- Suggested Fix: Validate with Pydantic models, add checksum/hash verification, keep backup of previous checkpoint.

### D) Orphaned Checkpoint Cleanup
- Identify checkpoint creation without cleanup on document deletion.
- Flag missing cleanup of `.tmp` files on crash recovery.
- Suggested Fix: Cleanup routines on startup, orphan detection, temp file age limits.

---

## 3) Race Conditions & Check-Then-Act Patterns

### A) Document State Transitions
- Look for if (status == X) then update(status = Y) patterns without locking.
- Flag pipeline stage transitions that could race (two workers processing same doc).
- Identify missing optimistic locking (version fields, ETags).
- Suggested Fix: Use DB-level locks or atomic compare-and-swap, add version/etag fields.

### B) Duplicate Document Processing
- Find patterns where the same document could be picked up by multiple workers.
- Flag missing "claimed by" markers or lease patterns.
- Suggested Fix: Atomic claim with unique constraint, use SELECT FOR UPDATE pattern (if supported), lease timeouts.

### C) Concurrent Edits / Lost Updates
- Identify endpoints that read-modify-write without conflict detection.
- Flag missing version checks on update operations.
- Look for frontend optimistic updates without backend validation.
- Suggested Fix: Optimistic concurrency with version fields, last-write-wins with explicit merge, real-time conflict notification via WebSocket.

### D) Cache/State Inconsistency
- Find in-memory caches (Zustand, Python globals) that can diverge from DB.
- Flag missing cache invalidation on data changes.
- Suggested Fix: Event-driven cache invalidation, short TTLs, WebSocket-based sync.

---

## 4) Transaction & Isolation Issues

### A) Missing Transaction Boundaries
- Look for multiple related DB operations without explicit transaction.
- Flag partial failure scenarios (first insert succeeds, second fails).
- Suggested Fix: Wrap related operations in explicit transactions, use context managers.

### B) Transaction Scope Violations
- Identify external API calls or file I/O inside transactions (blocks DB).
- Flag long-running transactions that hold locks.
- Suggested Fix: Move non-DB operations outside transactions, reduce transaction scope.

### C) Nested Transaction Handling
- Find savepoint usage or nested transaction patterns.
- Flag incorrect rollback behavior in nested contexts.
- Suggested Fix: Use savepoints correctly, avoid deep nesting, prefer flat transactions.

### D) Isolation Level Issues
- Identify read operations that might see phantom reads or non-repeatable reads.
- Flag assumptions about isolation that SQLite doesn't guarantee.
- Suggested Fix: Understand SQLite's isolation model, use explicit locking where needed.

---

## 5) Idempotency & Duplicate Prevention

### A) Non-Idempotent Operations
- Find POST/PUT handlers that create duplicates on retry.
- Flag missing idempotency keys for client-retryable operations.
- Suggested Fix: Add idempotency key support, use UPSERT patterns, unique constraints.

### B) Missing Unique Constraints
- Identify logical uniqueness (doc_id + page_num + element_id) without DB constraints.
- Flag application-level checks that can race.
- Suggested Fix: Add DB-level unique constraints, composite keys, use ON CONFLICT clauses.

### C) Event/Message Deduplication
- Find WebSocket message handlers that could duplicate on reconnect.
- Flag missing deduplication for async job queues or event processing.
- Suggested Fix: Message IDs with deduplication, at-least-once with idempotent handlers.

### D) Retry Safety
- Identify retry loops that could cause side effects on each retry.
- Flag non-idempotent operations in retry blocks.
- Suggested Fix: Make operations idempotent, use transaction rollback on retry, idempotency tokens.

---

## 6) Distributed State & Consistency

### A) Frontend/Backend State Divergence
- Find Zustand state that can get out of sync with backend.
- Flag missing state refresh after mutations.
- Identify stale data patterns in optimistic updates.
- Suggested Fix: Server-authoritative state, WebSocket-based sync, periodic polling fallback.

### B) Label Studio Sync Issues
- Identify race conditions in Label Studio project creation/annotation sync.
- Flag missing conflict handling when Label Studio and local state diverge.
- Suggested Fix: Define source of truth, handle sync conflicts explicitly, queue-based sync.

### C) WebSocket State Broadcast
- Find broadcast patterns that could miss clients (no guaranteed delivery).
- Flag missing sequence numbers or catch-up mechanisms.
- Suggested Fix: Message sequence IDs, missed message buffer, client state reconciliation on reconnect.

### D) Multi-Tab/Session Conflicts
- Identify scenarios where multiple browser tabs could conflict.
- Flag missing session-level locking or warning mechanisms.
- Suggested Fix: Tab detection via BroadcastChannel, session locks, conflict warnings.

---

## 7) Data Validation & Constraint Enforcement

### A) Schema Drift
- Find Pydantic models that don't match DB schema or checkpoint format.
- Flag missing schema version fields for evolution.
- Suggested Fix: Schema version in checkpoints, migration routines, strict validation.

### B) Referential Integrity
- Identify foreign key relationships without DB-level enforcement (SQLite FK disabled by default).
- Flag orphan creation patterns (child created before parent committed).
- Suggested Fix: Enable `PRAGMA foreign_keys = ON`, validate relationships in application.

### C) Boundary Validation
- Find missing bounds checking (page numbers, element indices, coordinates).
- Flag assumptions about array lengths or valid ranges.
- Suggested Fix: Pydantic validators with min/max, DB CHECK constraints, defensive coding.

### D) Type Coercion Issues
- Identify implicit type conversions that could lose data (float->int, truncation).
- Flag JSON serialization of types that don't round-trip cleanly.
- Suggested Fix: Explicit type handling, custom JSON encoders, validation on deserialization.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s)
Risk Category: SQLite | Checkpoint | Race Condition | Transaction | Idempotency | Distributed State | Validation

The Problem:
- 2-4 sentences explaining the data integrity risk.
- Be specific about failure mode: lost update, duplicate entry, corrupted checkpoint, orphaned state, inconsistent read, etc.

Concurrency Scenario:
- Describe the specific race or concurrent access pattern that triggers the issue.
- Example: "User A and User B both read element version 1, both submit edits, User A's edit is silently overwritten."

Impact:
- Quantify the risk (data loss, duplicate records, corrupted state, user confusion).
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (concurrent test script, DB constraint check, log analysis, chaos testing).

The Fix:
- Provide the corrected code snippet.
- Show before/after if useful.
- If fix requires schema changes or config, specify exactly what.

Trade-off Consideration:
- Note complexity, performance impact, and any risks.
- If acceptable at small scale, mark as MONITOR with what threshold triggers the fix.
```

## Severity Classification
- **CRITICAL**: Will cause data loss or corruption under concurrent access (lost updates, duplicate records, corrupted checkpoints).
- **HIGH**: Likely to cause inconsistent state or user-visible data issues (stale reads, race conditions with visible impact).
- **MEDIUM**: Could cause data issues under specific timing (edge case races, minor inconsistencies).
- **MONITOR**: Theoretical risk; watch for symptoms and revisit at scale.

---

## Integrity Score Rubric (Production Readiness 1-10)

Rate overall data integrity readiness based on severity/quantity and systemic risks:
- **9-10**: Strong data integrity guarantees; minor theoretical risks only.
- **7-8**: Generally safe; 1-2 races to fix before high concurrency.
- **5-6**: Significant integrity gaps; concurrent testing will expose issues.
- **3-4**: Multiple critical issues; data loss likely under concurrency.
- **<3**: Do not deploy; fundamental integrity issues.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (before concurrent access)
2) Fix Soon (before production scale)
3) Monitor (metrics + thresholds)

## Also include:
- Estimated time to implement all Fix Now items (range is fine)
- Testing strategy to verify fixes:
  - Concurrent write tests with `asyncio.gather()` or `threading`
  - Chaos testing (kill process during write, corrupt checkpoint)
  - Load test with conflict detection assertions
  - Recommended test approach:
    - `pytest-asyncio` for concurrent DB tests
    - Property-based testing with Hypothesis for edge cases
    - Playwright tests simulating multi-tab editing

---

## SQLite-Specific Checklist

Verify these SQLite best practices are followed:

```
[ ] WAL mode enabled (PRAGMA journal_mode=WAL)
[ ] Busy timeout configured (PRAGMA busy_timeout=5000)
[ ] Foreign keys enabled (PRAGMA foreign_keys=ON)
[ ] Synchronous mode appropriate (PRAGMA synchronous=NORMAL for WAL)
[ ] Connection properly closed (context managers)
[ ] Single writer pattern respected (or queue writes)
[ ] Transactions used for multi-statement operations
[ ] Prepared statements used (avoid SQL injection)
```

## Checkpoint File Checklist

Verify these file operation best practices are followed:

```
[ ] Atomic write pattern (write temp + rename)
[ ] fsync() called for durability-critical writes
[ ] Pydantic validation on load
[ ] Checksum or version for corruption detection
[ ] Backup of previous version before overwrite
[ ] Temp file cleanup on startup
[ ] Exclusive lock during write
[ ] Shared lock during read (if needed)
```
