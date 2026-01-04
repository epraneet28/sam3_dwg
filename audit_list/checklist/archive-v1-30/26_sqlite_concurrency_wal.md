# SQLite Concurrency & WAL Audit Prompt (Production-Ready, High-Concurrency)

## Role
Act as a Senior Database Engineer and Concurrency Specialist with deep expertise in SQLite internals. Perform a comprehensive SQLite Concurrency & WAL Audit on the provided codebase to identify and resolve write-locking issues before production deployment.

## Primary Goal
Identify where SQLite's default locking behavior, missing WAL configuration, and naive connection patterns will cause "Database is locked" errors, write starvation, and request timeouts under concurrent document processing loads.

## Context
- This code was developed with AI assistance ("vibecoded") and likely uses SQLite with default settings that fail under concurrency.
- SQLite's default journal mode (DELETE/ROLLBACK) allows only one writer at a time, blocking all other connections.
- The application processes documents concurrently, requiring careful SQLite configuration to avoid deadlocks.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn (async)
- Database: SQLite3 (file-based persistence)
- ORM/Driver: sqlite3 stdlib or aiosqlite
- Processing: Docling document pipeline with checkpoint writes
- Real-time: WebSocket connections for progress updates
- Frontend: React 19 + TypeScript

## Concurrency Target
- 10-50 concurrent document uploads
- Multiple simultaneous checkpoint writes per document
- Real-time status updates during processing
- SLO: No "Database is locked" errors, write latency < 100ms p99

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
Focus especially on:
- Database initialization and connection creation
- Any file with `sqlite`, `db`, `connection`, or `cursor` in the name
- Checkpoint save/load operations
- Document status update endpoints
- Background task workers

---

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - SQLite journal mode currently in use (WAL vs DELETE/ROLLBACK)
   - Connection pooling strategy (per-request, singleton, pool)
   - Async driver usage (sqlite3 vs aiosqlite)
   - Transaction isolation level and autocommit settings
   - Busy timeout configuration
   - File locking mode (normal vs exclusive)
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

---

## Audit Requirements

Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) Journal Mode & WAL Configuration

### A) Missing WAL Mode Initialization
- Look for database initialization WITHOUT `PRAGMA journal_mode=WAL;`
- Default journal mode (DELETE) serializes ALL writes, causing severe bottlenecks.
- Common mistake: Assuming WAL is default (it's not).
- Suggested Fix: Execute `PRAGMA journal_mode=WAL;` immediately after opening connection.

### B) WAL Checkpoint Configuration
- Missing `PRAGMA wal_autocheckpoint` tuning.
- WAL file growing unbounded without periodic checkpoints.
- Suggested Fix: Configure appropriate autocheckpoint threshold (e.g., 1000 pages).

### C) WAL Mode Persistence Issues
- WAL mode must be set per-connection in many SQLite bindings.
- Check if WAL is set once at startup vs every connection.
- Suggested Fix: Set WAL mode in connection factory/pool initialization.

### D) Synchronous Mode Misconfiguration
- `PRAGMA synchronous=OFF` for performance (data loss risk).
- `PRAGMA synchronous=FULL` causing unnecessary latency.
- Suggested Fix: Use `PRAGMA synchronous=NORMAL` with WAL mode (safe and fast).

---

## 2) Connection Management Anti-Patterns

### A) Connection Per Request Without Pooling
- Creating new sqlite3.connect() for every API request.
- Connection overhead + potential file handle exhaustion.
- Suggested Fix: Use connection pooling or singleton with proper thread safety.

### B) Blocking sqlite3 in Async Context
- Using synchronous `sqlite3` module directly in async FastAPI handlers.
- Blocks the event loop, freezing all concurrent requests.
- Suggested Fix: Use `aiosqlite` or `run_in_executor()` wrapper.

### C) Missing Connection Cleanup
- Connections opened without `finally` block or context manager.
- Leaked connections holding locks indefinitely.
- Suggested Fix: Always use `with connection:` or `async with connection:`.

### D) Thread-Unsafe Connection Sharing
- Single connection shared across threads without synchronization.
- SQLite connections are NOT thread-safe by default.
- Suggested Fix: Use `check_same_thread=False` with proper locking, or one connection per thread.

---

## 3) Write Contention & Locking Issues

### A) Missing Busy Timeout
- Default busy timeout is 0 (immediate failure on lock).
- Any concurrent write attempt fails instantly with "Database is locked".
- Suggested Fix: Set `PRAGMA busy_timeout=5000;` (5 seconds) or use `connection.execute("PRAGMA busy_timeout=5000")`.

### B) Long-Running Transactions
- Transactions held open during slow operations (file I/O, API calls).
- Write locks held for seconds, blocking all other writers.
- Suggested Fix: Minimize transaction scope; do heavy work outside transaction.

### C) Implicit Transaction Mismanagement
- Python sqlite3 starts implicit transactions that aren't committed.
- Accumulating uncommitted writes holding locks.
- Suggested Fix: Use explicit `connection.commit()` or `isolation_level=None` for autocommit reads.

### D) Write-Ahead Log Contention
- Even with WAL, only ONE writer at a time is allowed.
- Multiple concurrent checkpoint saves competing for write lock.
- Suggested Fix: Serialize writes through a queue or use optimistic concurrency with retries.

### E) Reader Blocking Writer (Rare but Possible)
- Long-running read transactions can block WAL checkpoints.
- WAL file grows unbounded, eventually causing issues.
- Suggested Fix: Keep read transactions short; use `BEGIN IMMEDIATE` for writes.

---

## 4) Checkpoint & State Persistence Issues

### A) Non-Atomic Checkpoint Writes
- Writing checkpoint JSON directly to target file.
- Crash during write = corrupted checkpoint.
- Suggested Fix: Write to temp file, then atomic rename (`os.replace()`).

### B) Checkpoint Metadata in SQLite Without Batching
- Individual INSERT/UPDATE per checkpoint field.
- N writes for N fields = N lock acquisitions.
- Suggested Fix: Batch all checkpoint updates in single transaction.

### C) File-Based Checkpoints Bypassing SQLite
- JSON files written directly to filesystem alongside SQLite.
- No coordination between file writes and DB state.
- Suggested Fix: Either all-SQLite or all-file with proper fsync ordering.

### D) Concurrent Checkpoint Access
- Multiple workers reading/writing same checkpoint simultaneously.
- Race conditions on checkpoint state.
- Suggested Fix: Use DB-level locking or file locking (fcntl/msvcrt).

---

## 5) Async/Await Integration Issues

### A) Synchronous DB Calls in Async Handlers
- `sqlite3.connect()` and `.execute()` are blocking calls.
- Single slow query blocks entire event loop.
- Suggested Fix: Use `aiosqlite` or wrap in `asyncio.to_thread()`.

### B) aiosqlite Connection Lifecycle
- Creating new aiosqlite connection per query (expensive).
- Not awaiting connection close properly.
- Suggested Fix: Use connection pool or long-lived connection with proper cleanup.

### C) Mixed Sync/Async Database Access
- Some code paths using sqlite3, others using aiosqlite.
- Inconsistent locking behavior and potential deadlocks.
- Suggested Fix: Standardize on one approach throughout codebase.

### D) Background Tasks Competing with Request Handlers
- BackgroundTasks or asyncio.create_task() writing to same DB.
- No coordination of write ordering.
- Suggested Fix: Use write queue or ensure serialized access.

---

## 6) Concurrent Document Processing Patterns

### A) Parallel Pipeline Stages Writing Status
- Multiple documents being processed, each updating status.
- All competing for single write lock.
- Suggested Fix: Batch status updates or use write-through queue.

### B) Progress Updates During Long Processing
- Frequent status updates (every second) during document processing.
- High write contention for progress tracking.
- Suggested Fix: Throttle updates, use in-memory cache with periodic flush.

### C) Upload + Processing Race Condition
- Document upload starts processing before upload transaction commits.
- Processing reads stale/missing data.
- Suggested Fix: Ensure upload transaction commits before spawning processor.

### D) Checkpoint Save Storms
- All pipeline stages saving checkpoints simultaneously.
- Serialized writes causing cascading delays.
- Suggested Fix: Stagger checkpoint saves or use single checkpoint transaction.

---

## 7) Error Handling & Recovery

### A) Swallowed "Database is locked" Errors
- Catching OperationalError without retry logic.
- Silent failures leaving data inconsistent.
- Suggested Fix: Implement retry with exponential backoff for lock errors.

### B) Transaction Rollback on Exception
- Exceptions leaving transactions uncommitted.
- Locks held until connection timeout/close.
- Suggested Fix: Use context managers; explicit rollback in except blocks.

### C) Corrupted WAL Recovery
- No handling for WAL file corruption scenarios.
- Application fails to start after crash.
- Suggested Fix: Implement WAL integrity check on startup.

### D) Connection State After Error
- Reusing connection after error without reset.
- Connection in undefined state causing subsequent failures.
- Suggested Fix: Create fresh connection after unrecoverable errors.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s)
Risk Category: WAL Config | Connection | Write Contention | Async | Checkpoint | Error Handling

The Problem:
- 2-4 sentences explaining why it causes "Database is locked" or write failures under concurrent load.
- Be specific about failure mode: lock timeout, write starvation, event loop block, data corruption, etc.

Concurrency Impact:
- Provide a realistic estimate (example: "10 concurrent uploads -> 40% requests fail with locked error", "Write latency spikes to 5s+ under load").
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (PRAGMA queries, connection tracing, load test with concurrent writes, SQLite `.timer on`).

The Fix:
- Provide the optimized code snippet.
- Show before/after if useful.
- If fix requires configuration, show exact PRAGMA statements and where they belong.

Trade-off Consideration:
- Note complexity, WAL file size implications, and any risks (e.g., "WAL requires more disk space but enables concurrent reads").
- If acceptable at small scale, mark as MONITOR with what threshold triggers refactor.
```

## Severity Classification
- **CRITICAL**: Will cause "Database is locked" errors under normal concurrent usage (10+ simultaneous operations).
- **HIGH**: Likely to cause intermittent lock errors or significant write latency under moderate load.
- **MEDIUM**: Performance degradation or potential race conditions under specific scenarios.
- **MONITOR**: Acceptable for current scale; watch metrics and revisit at thresholds.

---

## SQLite Configuration Checklist

Verify these PRAGMA settings are applied correctly:

```sql
-- Essential for concurrency
PRAGMA journal_mode=WAL;           -- Enable Write-Ahead Logging
PRAGMA busy_timeout=5000;          -- 5 second wait on locks
PRAGMA synchronous=NORMAL;         -- Safe with WAL, better performance

-- Recommended optimizations
PRAGMA cache_size=-64000;          -- 64MB cache (negative = KB)
PRAGMA temp_store=MEMORY;          -- Temp tables in memory
PRAGMA mmap_size=268435456;        -- 256MB memory-mapped I/O

-- WAL management
PRAGMA wal_autocheckpoint=1000;    -- Checkpoint every 1000 pages
PRAGMA wal_checkpoint(TRUNCATE);   -- Run on startup to reset WAL
```

---

## Vibe Score Rubric (SQLite Concurrency Readiness 1-10)

Rate overall SQLite concurrency readiness:
- **9-10**: WAL configured, proper connection handling, no blocking patterns. Ready for concurrent load.
- **7-8**: WAL configured but minor connection management issues. Low risk of lock errors.
- **5-6**: WAL missing or misconfigured. Will see intermittent "Database is locked" under moderate load.
- **3-4**: Synchronous sqlite3 in async context OR no busy timeout. High failure rate under concurrency.
- **<3**: Multiple critical issues. Will fail immediately with concurrent document processing.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)

1) Fix Now (before concurrent document processing)
2) Fix Soon (next iteration)
3) Monitor (metrics + thresholds)

## Also include:
- Estimated time to implement all Fix Now items (range is fine)
- Verification commands:
  ```bash
  # Check current journal mode
  sqlite3 your_database.db "PRAGMA journal_mode;"

  # Check busy timeout
  sqlite3 your_database.db "PRAGMA busy_timeout;"

  # Check WAL file size
  ls -la your_database.db-wal

  # Simulate concurrent writes (Python)
  python -c "
  import sqlite3, threading, time
  def writer(n):
      conn = sqlite3.connect('test.db', timeout=5)
      for i in range(100):
          try:
              conn.execute('INSERT INTO test VALUES (?)', (f'{n}-{i}',))
              conn.commit()
          except sqlite3.OperationalError as e:
              print(f'Thread {n}: {e}')
  threads = [threading.Thread(target=writer, args=(i,)) for i in range(10)]
  [t.start() for t in threads]
  [t.join() for t in threads]
  "
  ```
- Recommended monitoring:
  - SQLite lock wait time (custom instrumentation)
  - WAL file size over time
  - "Database is locked" error rate
  - Write transaction duration histogram
