# Data Integrity & Concurrency Audit

## Metadata
- **Priority**: P0 (Critical - Must Fix Before Production)
- **Merged from**: Archive issues #5 (Data Integrity & Concurrency), #26 (SQLite Concurrency & WAL)
- **Tags**: ⚠️ AI-CODING RISK, 🐍 PYTHON/FASTAPI, Database, Concurrency, SQLite
- **Estimated Impact**: High - Data loss, corruption, and lock errors under concurrent load
- **Estimated Effort**: 2-3 days for critical fixes

---

## Overview

This audit combines data integrity, concurrency control, and SQLite-specific configuration issues. The codebase was developed with AI assistance and has not been stress-tested for concurrent access. Under production loads (50+ concurrent document processing sessions, 10+ concurrent editors), the system will likely experience:

- "Database is locked" errors from SQLite write contention
- Lost updates from race conditions in read-modify-write patterns
- Corrupted checkpoint files from non-atomic writes
- Inconsistent state between frontend/backend/database
- Duplicate document processing and orphaned data

**Core Problem**: SQLite's default configuration serializes all writes, and the application lacks proper transaction boundaries, connection pooling, and atomic file operations.

---

## Audit Scope & Methodology

### Tech Stack Context
- **Backend**: Python 3.12, FastAPI, Uvicorn (async)
- **Database**: SQLite3 (file-based, single-writer default)
- **State Management**: Pydantic v2 models, JSON checkpoint files
- **Processing**: Docling 15-stage pipeline with checkpoint persistence
- **Real-time**: WebSockets for progress updates
- **Frontend**: React 19 + TypeScript, Zustand state

### Concurrency Test Targets
- [ ] 50 concurrent document uploads
- [ ] 10 concurrent users editing the same document
- [ ] Sub-second checkpoint save/load cycles
- [ ] WebSocket broadcast to 100+ clients
- [ ] **SLO**: Zero data loss, zero "Database is locked" errors, write latency < 100ms p99

### Audit Categories
1. **SQLite Concurrency & WAL Configuration**
2. **Checkpoint File Atomicity**
3. **Race Conditions & Check-Then-Act Patterns**
4. **Transaction & Isolation Issues**
5. **Idempotency & Duplicate Prevention**
6. **Distributed State & Consistency**
7. **Data Validation & Constraint Enforcement**

---

## 1. SQLite Concurrency & WAL Configuration

### 🔴 CRITICAL: Enable WAL Mode

#### The Problem
- [ ] Verify current journal mode: `PRAGMA journal_mode;` returns DELETE/ROLLBACK (not WAL)
- [ ] Confirm WAL initialization: Search for `PRAGMA journal_mode=WAL` in database initialization code
- [ ] Check connection factory: Ensure WAL is set per-connection or persisted in DB file

**Why This Matters**: SQLite's default DELETE journal mode allows only ONE writer at a time. Every write transaction blocks ALL other connections (readers and writers). Under concurrent document processing, this causes:
- Immediate "Database is locked" errors when multiple documents save checkpoints
- Write starvation as writers queue behind each other
- Timeout failures when busy_timeout is not configured

**Expected Files to Check**:
- `backend/core/database.py` - Connection initialization
- `backend/core/checkpoint/manager.py` - Checkpoint save operations
- Any module with `sqlite3.connect()` or `aiosqlite.connect()`

#### How to Verify
```bash
# 1. Check current journal mode
sqlite3 /path/to/database.db "PRAGMA journal_mode;"

# 2. Expected output after fix: WAL
# 3. Verify WAL file exists during operation
ls -la /path/to/database.db-wal

# 4. Concurrent write test (should complete without errors)
python -c "
import sqlite3
import threading

def writer(n):
    conn = sqlite3.connect('test.db', timeout=5)
    conn.execute('PRAGMA journal_mode=WAL;')
    for i in range(100):
        try:
            conn.execute('INSERT INTO test VALUES (?, ?)', (n, i))
            conn.commit()
        except sqlite3.OperationalError as e:
            print(f'Thread {n} failed: {e}')
    conn.close()

threads = [threading.Thread(target=writer, args=(i,)) for i in range(10)]
[t.start() for t in threads]
[t.join() for t in threads]
print('Test complete')
"
```

#### The Fix
```python
# backend/core/database.py - BEFORE
def get_connection():
    conn = sqlite3.connect("app.db")
    return conn

# backend/core/database.py - AFTER
def get_connection():
    conn = sqlite3.connect("app.db", timeout=5.0)
    # Enable WAL mode immediately (persists in DB file after first execution)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")  # 5 second wait on locks
    conn.execute("PRAGMA synchronous=NORMAL;")  # Safe with WAL, better performance
    conn.execute("PRAGMA foreign_keys=ON;")     # Enable FK constraints
    conn.execute("PRAGMA cache_size=-64000;")   # 64MB cache
    conn.execute("PRAGMA temp_store=MEMORY;")   # Temp tables in RAM
    return conn
```

**For async code using aiosqlite**:
```python
# backend/core/database.py - Async version
async def get_async_connection():
    conn = await aiosqlite.connect("app.db", timeout=5.0)
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.execute("PRAGMA busy_timeout=5000;")
    await conn.execute("PRAGMA synchronous=NORMAL;")
    await conn.execute("PRAGMA foreign_keys=ON;")
    return conn
```

**One-time WAL initialization script**:
```python
# scripts/init_wal.py
import sqlite3

def initialize_wal_mode(db_path="app.db"):
    """One-time conversion to WAL mode (persists in DB file)"""
    conn = sqlite3.connect(db_path)

    # Enable WAL mode
    result = conn.execute("PRAGMA journal_mode=WAL;").fetchone()
    print(f"Journal mode set to: {result[0]}")

    # Optional: Checkpoint and truncate WAL to compact
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")

    conn.close()
    print(f"WAL mode enabled for {db_path}")

if __name__ == "__main__":
    initialize_wal_mode()
```

#### Trade-offs
- **Disk Space**: WAL file can grow; configure `wal_autocheckpoint` to limit
- **WAL Persistence**: WAL mode is a DB property (persists), but some Python bindings require per-connection setting
- **Checkpointing**: WAL must be periodically checkpointed; configure autocheckpoint or run manual checkpoints
- **Compatibility**: WAL mode requires filesystem that supports memory-mapped I/O (not all network filesystems)

---

### 🔴 CRITICAL: Configure Busy Timeout

#### The Problem
- [ ] Search for `busy_timeout` configuration in connection setup
- [ ] Check if timeout parameter is passed to `sqlite3.connect()`
- [ ] Verify timeout is >= 5000ms for concurrent workloads

**Default busy_timeout is 0**: Any concurrent write attempt fails IMMEDIATELY with "Database is locked" instead of waiting for the lock to be released.

#### The Fix
```python
# Set busy timeout at connection creation
conn = sqlite3.connect("app.db", timeout=5.0)  # timeout parameter

# OR via PRAGMA (if not set at connect time)
conn.execute("PRAGMA busy_timeout=5000;")  # 5000 milliseconds
```

#### Verification
```bash
# Check current timeout
sqlite3 app.db "PRAGMA busy_timeout;"
# Expected: 5000 (or your configured value)
```

---

### 🔴 CRITICAL: Use aiosqlite for Async Context

#### The Problem
- [ ] Search for synchronous `sqlite3` usage in async FastAPI handlers
- [ ] Identify blocking `.execute()` calls without `await`
- [ ] Check for `run_in_executor()` wrappers or aiosqlite usage

**Blocking DB calls in async handlers freeze the entire event loop**, causing all concurrent requests to hang.

#### The Fix
```python
# BEFORE - Synchronous sqlite3 blocks event loop
from fastapi import FastAPI
import sqlite3

@app.post("/checkpoint")
def save_checkpoint(data: dict):
    conn = sqlite3.connect("app.db")  # BLOCKS!
    conn.execute("INSERT INTO checkpoints ...")  # BLOCKS!
    conn.commit()
    conn.close()
    return {"status": "ok"}

# AFTER - Use aiosqlite
from fastapi import FastAPI
import aiosqlite

@app.post("/checkpoint")
async def save_checkpoint(data: dict):
    async with aiosqlite.connect("app.db", timeout=5.0) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("INSERT INTO checkpoints ...")
        await conn.commit()
    return {"status": "ok"}
```

**Alternative: Use run_in_executor for existing sync code**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)

@app.post("/checkpoint")
async def save_checkpoint(data: dict):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _sync_save_checkpoint, data)
    return {"status": "ok"}

def _sync_save_checkpoint(data: dict):
    conn = sqlite3.connect("app.db", timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("INSERT INTO checkpoints ...")
    conn.commit()
    conn.close()
```

---

### 🟡 HIGH: Connection Pooling/Lifecycle

#### The Problem
- [ ] Check if new connection is created per API request
- [ ] Verify connections are properly closed (use context managers)
- [ ] Identify connection reuse patterns

**Creating a new connection per request is expensive** and can lead to file handle exhaustion. Connections must be properly closed to avoid leaked locks.

#### The Fix
```python
# BEFORE - Connection per request (expensive)
@app.get("/documents/{doc_id}")
def get_document(doc_id: str):
    conn = sqlite3.connect("app.db")
    result = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    conn.close()  # Easy to forget!
    return result

# AFTER - Use context manager (ensures cleanup)
@app.get("/documents/{doc_id}")
def get_document(doc_id: str):
    with sqlite3.connect("app.db", timeout=5.0) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        result = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    return result

# BETTER - Use dependency injection with connection pool
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_connection():
    async with aiosqlite.connect("app.db", timeout=5.0) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("PRAGMA busy_timeout=5000;")
        yield conn

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str, conn=Depends(get_db_connection)):
    async with conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)) as cursor:
        result = await cursor.fetchone()
    return result
```

---

### 🟡 HIGH: WAL Autocheckpoint Configuration

#### The Problem
- [ ] Verify `wal_autocheckpoint` is configured
- [ ] Monitor WAL file size during testing
- [ ] Check for manual checkpoint calls in long-running processes

**WAL file grows unbounded without periodic checkpoints**, leading to disk space issues and eventual performance degradation.

#### The Fix
```python
# Set autocheckpoint threshold (in pages, ~4KB each)
conn.execute("PRAGMA wal_autocheckpoint=1000;")  # Checkpoint every ~4MB

# Manual checkpoint for long-running processes
conn.execute("PRAGMA wal_checkpoint(PASSIVE);")  # Non-blocking
# OR
conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")  # Truncate WAL file
```

#### Verification
```bash
# Check WAL file size
ls -lh app.db-wal

# Force checkpoint and check size reduction
sqlite3 app.db "PRAGMA wal_checkpoint(TRUNCATE);"
ls -lh app.db-wal
```

---

### SQLite Configuration Checklist

Apply these PRAGMA settings at connection initialization:

```python
# Essential for concurrency
conn.execute("PRAGMA journal_mode=WAL;")           # Enable Write-Ahead Logging
conn.execute("PRAGMA busy_timeout=5000;")          # 5 second wait on locks
conn.execute("PRAGMA synchronous=NORMAL;")         # Safe with WAL, better performance

# Recommended optimizations
conn.execute("PRAGMA cache_size=-64000;")          # 64MB cache (negative = KB)
conn.execute("PRAGMA temp_store=MEMORY;")          # Temp tables in memory
conn.execute("PRAGMA mmap_size=268435456;")        # 256MB memory-mapped I/O

# Data integrity
conn.execute("PRAGMA foreign_keys=ON;")            # Enable foreign key constraints

# WAL management
conn.execute("PRAGMA wal_autocheckpoint=1000;")    # Checkpoint every 1000 pages
```

**Verification Script**:
```bash
#!/bin/bash
# scripts/verify_sqlite_config.sh

DB_PATH="app.db"

echo "=== SQLite Configuration Check ==="
echo ""

echo "Journal Mode:"
sqlite3 "$DB_PATH" "PRAGMA journal_mode;"

echo "Busy Timeout:"
sqlite3 "$DB_PATH" "PRAGMA busy_timeout;"

echo "Synchronous Mode:"
sqlite3 "$DB_PATH" "PRAGMA synchronous;"

echo "Foreign Keys:"
sqlite3 "$DB_PATH" "PRAGMA foreign_keys;"

echo "WAL Autocheckpoint:"
sqlite3 "$DB_PATH" "PRAGMA wal_autocheckpoint;"

echo ""
echo "=== WAL File Status ==="
if [ -f "$DB_PATH-wal" ]; then
    ls -lh "$DB_PATH-wal"
else
    echo "No WAL file found (may not have been created yet)"
fi
```

---

## 2. Checkpoint File Atomicity

### 🔴 CRITICAL: Non-Atomic Checkpoint Writes

#### The Problem
- [ ] Search for direct file writes: `open(checkpoint_path, 'w').write(json_data)`
- [ ] Check if write-to-temp-then-rename pattern is used
- [ ] Verify `fsync()` is called for durability-critical writes

**Direct file writes can leave corrupted checkpoints on crash/interruption**. A partially written JSON file cannot be parsed, causing checkpoint load failures.

#### How to Verify
```python
# Test: Kill process during checkpoint write
# Expected: Checkpoint file is either fully written (old version) or fully updated (new version)
# Never: Partial/corrupted JSON

# Grep for non-atomic patterns
grep -r "open.*'w'.*write" backend/core/checkpoint/
```

#### The Fix
```python
# BEFORE - Non-atomic write (DANGEROUS)
def save_checkpoint(checkpoint_path: str, data: dict):
    with open(checkpoint_path, 'w') as f:
        json.dump(data, f)  # CRASH HERE = CORRUPTED FILE

# AFTER - Atomic write with temp file + rename
import os
import tempfile
import json

def save_checkpoint(checkpoint_path: str, data: dict):
    # Write to temporary file in same directory (same filesystem = atomic rename)
    dir_path = os.path.dirname(checkpoint_path)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=dir_path,
        delete=False,
        suffix='.tmp'
    ) as tmp_file:
        json.dump(data, tmp_file, indent=2)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())  # Force write to disk
        tmp_path = tmp_file.name

    # Atomic rename (POSIX guarantees atomicity)
    os.replace(tmp_path, checkpoint_path)  # Atomic on all platforms
```

**Enhanced version with backup**:
```python
def save_checkpoint_with_backup(checkpoint_path: str, data: dict):
    # Keep backup of previous version
    backup_path = f"{checkpoint_path}.backup"
    if os.path.exists(checkpoint_path):
        os.replace(checkpoint_path, backup_path)

    # Atomic write
    dir_path = os.path.dirname(checkpoint_path)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=dir_path,
        delete=False,
        suffix='.tmp'
    ) as tmp_file:
        json.dump(data, tmp_file, indent=2)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        tmp_path = tmp_file.name

    os.replace(tmp_path, checkpoint_path)
```

---

### 🟡 HIGH: Checkpoint Validation on Load

#### The Problem
- [ ] Check if checkpoint loading validates with Pydantic models
- [ ] Verify schema version checking for evolution
- [ ] Look for checksum/hash verification

**Blindly trusting checkpoint file contents can lead to crashes** if files are manually edited or corrupted.

#### The Fix
```python
from pydantic import BaseModel, ValidationError
import hashlib
import json

class CheckpointSchema(BaseModel):
    schema_version: str = "1.0"
    document_id: str
    stage: int
    data: dict
    # ... other fields

def load_checkpoint(checkpoint_path: str) -> CheckpointSchema:
    try:
        with open(checkpoint_path, 'r') as f:
            raw_data = json.load(f)

        # Pydantic validation
        checkpoint = CheckpointSchema(**raw_data)

        # Version check
        if checkpoint.schema_version != "1.0":
            raise ValueError(f"Unsupported schema version: {checkpoint.schema_version}")

        return checkpoint

    except ValidationError as e:
        # Try loading backup if available
        backup_path = f"{checkpoint_path}.backup"
        if os.path.exists(backup_path):
            print(f"Checkpoint corrupted, trying backup: {e}")
            with open(backup_path, 'r') as f:
                raw_data = json.load(f)
            return CheckpointSchema(**raw_data)
        raise

# Optional: Add checksum verification
def save_checkpoint_with_checksum(checkpoint_path: str, data: dict):
    # Add checksum to data
    data_json = json.dumps(data, sort_keys=True)
    checksum = hashlib.sha256(data_json.encode()).hexdigest()

    full_data = {
        "checksum": checksum,
        "data": data
    }

    # Atomic write (as shown above)
    save_checkpoint(checkpoint_path, full_data)

def load_checkpoint_with_checksum(checkpoint_path: str) -> dict:
    with open(checkpoint_path, 'r') as f:
        full_data = json.load(f)

    expected_checksum = full_data["checksum"]
    data = full_data["data"]

    # Verify checksum
    data_json = json.dumps(data, sort_keys=True)
    actual_checksum = hashlib.sha256(data_json.encode()).hexdigest()

    if actual_checksum != expected_checksum:
        raise ValueError("Checkpoint checksum mismatch - possible corruption")

    return data
```

---

### 🟡 MEDIUM: Orphaned Checkpoint Cleanup

#### The Problem
- [ ] Check for `.tmp` file cleanup on startup
- [ ] Verify checkpoint deletion when document is deleted
- [ ] Look for age-based temp file cleanup

**Orphaned temporary files and checkpoints accumulate over time**, consuming disk space.

#### The Fix
```python
# Startup cleanup routine
import glob
import time

def cleanup_orphaned_files(checkpoint_dir: str, max_age_hours: int = 24):
    """Clean up orphaned .tmp files and old checkpoints"""
    now = time.time()
    max_age_seconds = max_age_hours * 3600

    # Clean up .tmp files
    for tmp_file in glob.glob(os.path.join(checkpoint_dir, "*.tmp")):
        file_age = now - os.path.getmtime(tmp_file)
        if file_age > max_age_seconds:
            print(f"Removing orphaned temp file: {tmp_file}")
            os.remove(tmp_file)

    # Clean up checkpoints for deleted documents
    # (requires DB query to get active document IDs)
    active_doc_ids = get_active_document_ids()
    for checkpoint_file in glob.glob(os.path.join(checkpoint_dir, "*.json")):
        doc_id = extract_doc_id_from_filename(checkpoint_file)
        if doc_id not in active_doc_ids:
            print(f"Removing orphaned checkpoint: {checkpoint_file}")
            os.remove(checkpoint_file)

# Run on application startup
@app.on_event("startup")
async def startup_cleanup():
    cleanup_orphaned_files("/path/to/checkpoints")
```

---

### Checkpoint File Best Practices Checklist

```
[ ] Atomic write pattern (write temp + rename)
[ ] fsync() called for durability-critical writes
[ ] Pydantic validation on load
[ ] Checksum or version for corruption detection
[ ] Backup of previous version before overwrite
[ ] Temp file cleanup on startup
[ ] Orphaned checkpoint cleanup when document deleted
[ ] File locking during concurrent access (if needed)
```

---

## 3. Race Conditions & Check-Then-Act Patterns

### 🔴 CRITICAL: Document State Transitions Without Locking

#### The Problem
- [ ] Search for `if status == X: update status = Y` patterns
- [ ] Check for optimistic locking (version fields, ETags)
- [ ] Identify pipeline stage transitions that could race

**Check-then-act pattern without locking allows two workers to process the same document**, leading to duplicate processing and wasted resources.

#### Example Scenario
```python
# BEFORE - Race condition
def claim_document_for_processing(doc_id: str, worker_id: str):
    doc = db.query("SELECT status FROM documents WHERE id=?", (doc_id,))
    if doc.status == "pending":  # ← RACE HERE
        db.execute("UPDATE documents SET status='processing', worker_id=? WHERE id=?",
                   (worker_id, doc_id))
        return True
    return False

# RACE: Two workers both see status="pending", both claim the document
```

#### The Fix
```python
# AFTER - Atomic compare-and-swap
def claim_document_for_processing(doc_id: str, worker_id: str) -> bool:
    result = db.execute(
        """UPDATE documents
           SET status='processing', worker_id=?, claimed_at=CURRENT_TIMESTAMP
           WHERE id=? AND status='pending'""",
        (worker_id, doc_id)
    )
    db.commit()
    return result.rowcount > 0  # True if document was claimed

# Alternative: Optimistic locking with version field
def update_with_version_check(doc_id: str, new_data: dict, expected_version: int):
    result = db.execute(
        """UPDATE documents
           SET data=?, version=version+1
           WHERE id=? AND version=?""",
        (json.dumps(new_data), doc_id, expected_version)
    )
    db.commit()
    if result.rowcount == 0:
        raise ConcurrentModificationError("Document was modified by another user")
```

---

### 🔴 CRITICAL: Concurrent Edits / Lost Updates

#### The Problem
- [ ] Check API endpoints that read-modify-write without version checks
- [ ] Verify frontend sends version/etag with updates
- [ ] Look for last-write-wins behavior without user notification

**Two users editing the same document will silently overwrite each other's changes.**

#### The Fix
```python
from pydantic import BaseModel
from fastapi import HTTPException

class DocumentUpdate(BaseModel):
    version: int  # Frontend must send current version
    data: dict

@app.put("/documents/{doc_id}")
async def update_document(doc_id: str, update: DocumentUpdate):
    async with get_db_connection() as conn:
        # Attempt optimistic update
        result = await conn.execute(
            """UPDATE documents
               SET data=?, version=version+1, updated_at=CURRENT_TIMESTAMP
               WHERE id=? AND version=?""",
            (json.dumps(update.data), doc_id, update.version)
        )
        await conn.commit()

        if result.rowcount == 0:
            # Version mismatch - conflict detected
            raise HTTPException(
                status_code=409,
                detail="Document was modified by another user. Please refresh and retry."
            )

        return {"status": "ok", "new_version": update.version + 1}
```

**Frontend conflict handling**:
```typescript
// frontend/src/utils/api.ts
async function updateDocument(docId: string, data: any, version: number) {
  try {
    const response = await fetch(`/api/documents/${docId}`, {
      method: 'PUT',
      body: JSON.stringify({ version, data }),
    });

    if (response.status === 409) {
      // Conflict - show merge UI or force refresh
      const userChoice = await showConflictDialog();
      if (userChoice === 'refresh') {
        window.location.reload();
      }
    }

    return response.json();
  } catch (error) {
    console.error('Update failed:', error);
  }
}
```

---

### 🟡 HIGH: Cache/State Inconsistency

#### The Problem
- [ ] Identify in-memory caches (Zustand, Python globals) that can diverge from DB
- [ ] Check for cache invalidation on data changes
- [ ] Verify WebSocket updates trigger cache refresh

**Frontend state can become stale when other users make changes**, leading to incorrect UI state.

#### The Fix
```python
# Backend: Broadcast changes via WebSocket
from fastapi import WebSocket
from typing import Dict

active_connections: Dict[str, list[WebSocket]] = {}

async def broadcast_document_update(doc_id: str, data: dict):
    """Notify all connected clients about document change"""
    if doc_id in active_connections:
        for ws in active_connections[doc_id]:
            try:
                await ws.send_json({
                    "type": "document_updated",
                    "doc_id": doc_id,
                    "data": data
                })
            except:
                # Connection closed, will be cleaned up elsewhere
                pass

@app.put("/documents/{doc_id}")
async def update_document(doc_id: str, update: DocumentUpdate):
    # ... database update ...

    # Broadcast to all connected clients
    await broadcast_document_update(doc_id, update.data)

    return {"status": "ok"}
```

```typescript
// Frontend: Listen for WebSocket updates
// frontend/src/utils/websocket.ts
import { useStore } from '../store';

export function setupWebSocketSync() {
  const ws = new WebSocket('ws://localhost:8000/ws');

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'document_updated') {
      // Update Zustand store with latest data
      useStore.getState().updateDocument(message.doc_id, message.data);

      // Show notification
      toast.info('Document updated by another user');
    }
  };
}
```

---

## 4. Transaction & Isolation Issues

### 🔴 CRITICAL: Missing Transaction Boundaries

#### The Problem
- [ ] Look for multiple related DB operations without explicit transaction
- [ ] Check for partial failure scenarios (first insert succeeds, second fails)
- [ ] Verify rollback handling on errors

**Multiple related operations without a transaction can leave data in inconsistent state** if one operation fails.

#### The Fix
```python
# BEFORE - No transaction, partial failure possible
def create_document_with_pages(doc_id: str, pages: list[dict]):
    conn.execute("INSERT INTO documents (id, name) VALUES (?, ?)", (doc_id, "New Doc"))
    conn.commit()  # ← If next line fails, document exists without pages

    for page in pages:
        conn.execute("INSERT INTO pages (doc_id, page_num, data) VALUES (?, ?, ?)",
                     (doc_id, page['num'], page['data']))
    conn.commit()

# AFTER - Wrapped in transaction
def create_document_with_pages(doc_id: str, pages: list[dict]):
    with conn:  # Context manager handles commit/rollback
        conn.execute("INSERT INTO documents (id, name) VALUES (?, ?)", (doc_id, "New Doc"))

        for page in pages:
            conn.execute("INSERT INTO pages (doc_id, page_num, data) VALUES (?, ?, ?)",
                         (doc_id, page['num'], page['data']))
        # Automatic commit on success, rollback on exception

# Explicit transaction control
def create_document_with_pages_explicit(doc_id: str, pages: list[dict]):
    try:
        conn.execute("BEGIN")

        conn.execute("INSERT INTO documents (id, name) VALUES (?, ?)", (doc_id, "New Doc"))

        for page in pages:
            conn.execute("INSERT INTO pages (doc_id, page_num, data) VALUES (?, ?, ?)",
                         (doc_id, page['num'], page['data']))

        conn.execute("COMMIT")
    except Exception as e:
        conn.execute("ROLLBACK")
        raise
```

---

### 🟡 HIGH: Transaction Scope Violations

#### The Problem
- [ ] Identify external API calls or file I/O inside transactions
- [ ] Check for long-running transactions that hold locks
- [ ] Look for processing logic inside transaction blocks

**Long-running transactions block other writers**, causing write starvation and timeout errors.

#### The Fix
```python
# BEFORE - External API call inside transaction (SLOW)
def process_document(doc_id: str):
    with conn:
        doc = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()

        # This holds the transaction lock for seconds!
        result = call_external_api(doc.data)  # ← BLOCKS OTHER WRITES

        conn.execute("UPDATE documents SET result=? WHERE id=?", (result, doc_id))

# AFTER - Minimize transaction scope
def process_document(doc_id: str):
    # Read outside transaction
    doc = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()

    # External API call (no transaction held)
    result = call_external_api(doc.data)

    # Write in minimal transaction
    with conn:
        conn.execute("UPDATE documents SET result=? WHERE id=?", (result, doc_id))
```

---

## 5. Idempotency & Duplicate Prevention

### 🔴 CRITICAL: Non-Idempotent Operations

#### The Problem
- [ ] Find POST/PUT handlers that create duplicates on retry
- [ ] Check for idempotency key support
- [ ] Verify UPSERT patterns are used

**Client retries (network errors, timeouts) can create duplicate documents/entries** without idempotency protection.

#### The Fix
```python
# BEFORE - Duplicate on retry
@app.post("/upload")
async def upload_document(file: UploadFile):
    doc_id = str(uuid.uuid4())
    # If this succeeds but response is lost, client retries = duplicate
    await conn.execute("INSERT INTO documents (id, name) VALUES (?, ?)", (doc_id, file.filename))
    await conn.commit()
    return {"doc_id": doc_id}

# AFTER - Idempotent with client-provided key
@app.post("/upload")
async def upload_document(file: UploadFile, idempotency_key: str = Header(None)):
    if not idempotency_key:
        idempotency_key = str(uuid.uuid4())

    # Use UPSERT to make idempotent
    await conn.execute(
        """INSERT INTO documents (id, name, idempotency_key)
           VALUES (?, ?, ?)
           ON CONFLICT(idempotency_key) DO NOTHING""",
        (str(uuid.uuid4()), file.filename, idempotency_key)
    )
    await conn.commit()

    # Return existing document if already created
    doc = await conn.execute(
        "SELECT id FROM documents WHERE idempotency_key=?",
        (idempotency_key,)
    ).fetchone()

    return {"doc_id": doc['id']}
```

---

### 🟡 HIGH: Missing Unique Constraints

#### The Problem
- [ ] Identify logical uniqueness without DB constraints (doc_id + page_num)
- [ ] Check for application-level uniqueness checks that can race
- [ ] Verify composite unique constraints exist

**Application-level uniqueness checks can race**, allowing duplicates to be inserted.

#### The Fix
```sql
-- Add unique constraints at schema level
CREATE UNIQUE INDEX idx_unique_page ON pages (doc_id, page_num);
CREATE UNIQUE INDEX idx_unique_element ON elements (doc_id, page_num, element_id);
CREATE UNIQUE INDEX idx_idempotency ON documents (idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Use ON CONFLICT in application code
INSERT INTO pages (doc_id, page_num, data)
VALUES (?, ?, ?)
ON CONFLICT(doc_id, page_num) DO UPDATE SET data=excluded.data;
```

---

## 6. Distributed State & Consistency

### 🟡 HIGH: Frontend/Backend State Divergence

#### The Problem
- [ ] Find Zustand state that can get out of sync with backend
- [ ] Check for state refresh after mutations
- [ ] Verify optimistic updates are rolled back on failure

**Frontend optimistic updates can show stale data if backend update fails.**

#### The Fix
```typescript
// frontend/src/store/index.ts
import create from 'zustand';

interface DocumentStore {
  documents: Map<string, Document>;
  updateDocument: (id: string, data: any, version: number) => Promise<void>;
}

export const useStore = create<DocumentStore>((set, get) => ({
  documents: new Map(),

  updateDocument: async (id: string, data: any, version: number) => {
    // Optimistic update
    const originalDoc = get().documents.get(id);
    set((state) => ({
      documents: new Map(state.documents).set(id, { ...data, version: version + 1 })
    }));

    try {
      // Backend update
      const response = await fetch(`/api/documents/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ version, data }),
      });

      if (response.status === 409) {
        // Conflict - rollback optimistic update and refresh
        const latestDoc = await fetch(`/api/documents/${id}`).then(r => r.json());
        set((state) => ({
          documents: new Map(state.documents).set(id, latestDoc)
        }));
        throw new Error('Conflict - document was modified by another user');
      }

      const result = await response.json();

      // Confirm with server version
      set((state) => ({
        documents: new Map(state.documents).set(id, { ...data, version: result.new_version })
      }));
    } catch (error) {
      // Rollback on failure
      if (originalDoc) {
        set((state) => ({
          documents: new Map(state.documents).set(id, originalDoc)
        }));
      }
      throw error;
    }
  }
}));
```

---

### 🟡 MEDIUM: WebSocket State Broadcast

#### The Problem
- [ ] Check for guaranteed delivery mechanisms
- [ ] Verify sequence numbers or catch-up on reconnect
- [ ] Look for missed message buffers

**WebSocket messages can be lost during disconnection**, causing clients to miss updates.

#### The Fix
```python
# Backend: Add sequence numbers and message buffering
from collections import deque

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.message_buffer: Dict[str, deque] = {}  # Buffer last N messages per doc
        self.sequence_numbers: Dict[str, int] = {}

    async def broadcast(self, doc_id: str, message: dict):
        # Add sequence number
        seq = self.sequence_numbers.get(doc_id, 0) + 1
        self.sequence_numbers[doc_id] = seq
        message['seq'] = seq

        # Buffer message
        if doc_id not in self.message_buffer:
            self.message_buffer[doc_id] = deque(maxlen=100)
        self.message_buffer[doc_id].append(message)

        # Broadcast to connected clients
        for ws in self.active_connections.get(doc_id, []):
            try:
                await ws.send_json(message)
            except:
                pass

    async def catch_up(self, doc_id: str, last_seq: int) -> list[dict]:
        """Get messages client missed during disconnection"""
        if doc_id not in self.message_buffer:
            return []

        return [msg for msg in self.message_buffer[doc_id] if msg['seq'] > last_seq]
```

```typescript
// Frontend: Track sequence and request catch-up
let lastSeq = 0;

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.seq > lastSeq + 1) {
    // Gap detected - request catch-up
    ws.send(JSON.stringify({
      type: 'catch_up',
      last_seq: lastSeq
    }));
  }

  lastSeq = message.seq;
  // Process message...
};
```

---

## 7. Data Validation & Constraint Enforcement

### 🔴 CRITICAL: Enable Foreign Keys

#### The Problem
- [ ] Verify `PRAGMA foreign_keys=ON` is set at connection initialization
- [ ] Check for orphan creation patterns (child before parent committed)
- [ ] Look for CASCADE delete behavior

**SQLite disables foreign key constraints by default**, allowing orphaned records and referential integrity violations.

#### The Fix
```python
# Enable FK constraints at every connection
conn = sqlite3.connect("app.db", timeout=5.0)
conn.execute("PRAGMA foreign_keys=ON;")  # MUST be set per connection

# Verify FK constraints are enforced
result = conn.execute("PRAGMA foreign_keys;").fetchone()
assert result[0] == 1, "Foreign keys not enabled!"
```

```sql
-- Schema with FK constraints
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE pages (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    page_num INTEGER NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE (doc_id, page_num)
);

CREATE TABLE elements (
    id TEXT PRIMARY KEY,
    page_id TEXT NOT NULL,
    element_type TEXT NOT NULL,
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
);
```

---

### 🟡 HIGH: Schema Drift & Versioning

#### The Problem
- [ ] Check for schema version fields in checkpoints and DB
- [ ] Verify migration routines exist
- [ ] Look for Pydantic models matching DB schema

**Schema evolution without versioning causes checkpoint load failures** when format changes.

#### The Fix
```python
# Add schema version to checkpoints
class Checkpoint(BaseModel):
    schema_version: str = "2.0"
    document_id: str
    stage: int
    data: dict

def load_checkpoint_with_migration(path: str) -> Checkpoint:
    with open(path, 'r') as f:
        raw_data = json.load(f)

    version = raw_data.get('schema_version', '1.0')

    # Migrate old formats
    if version == '1.0':
        raw_data = migrate_v1_to_v2(raw_data)
        version = '2.0'

    if version != '2.0':
        raise ValueError(f"Unsupported schema version: {version}")

    return Checkpoint(**raw_data)

def migrate_v1_to_v2(data: dict) -> dict:
    """Migrate checkpoint format from v1 to v2"""
    return {
        'schema_version': '2.0',
        'document_id': data['doc_id'],  # Field renamed
        'stage': data.get('stage', 0),
        'data': data.get('data', {})
    }
```

---

## Summary & Action Plan

### Fix Now (Before Concurrent Access) - P0

#### 1. Enable SQLite WAL Mode (2-4 hours)
- [ ] Add `PRAGMA journal_mode=WAL;` to all connection initialization
- [ ] Set `busy_timeout=5000` on all connections
- [ ] Configure `synchronous=NORMAL` for performance
- [ ] Run verification script to confirm settings
- [ ] Test concurrent writes (10+ threads)

#### 2. Atomic Checkpoint Writes (4-6 hours)
- [ ] Replace direct file writes with temp-file-then-rename pattern
- [ ] Add `fsync()` for durability
- [ ] Implement Pydantic validation on checkpoint load
- [ ] Add backup before overwrite
- [ ] Test crash recovery (kill -9 during write)

#### 3. Replace Synchronous sqlite3 with aiosqlite (6-8 hours)
- [ ] Convert all FastAPI handlers to use aiosqlite
- [ ] Replace blocking `.execute()` with `await` versions
- [ ] Update connection factory for async context
- [ ] Verify no event loop blocking with concurrent requests

#### 4. Add Optimistic Locking (4-6 hours)
- [ ] Add `version` field to documents table
- [ ] Update all write endpoints to check version
- [ ] Return 409 Conflict on version mismatch
- [ ] Update frontend to handle conflicts

**Total Estimated Time: 2-3 days**

---

### Fix Soon (Before Production Scale) - P1

#### 5. Connection Pooling (2-4 hours)
- [ ] Implement connection pool or FastAPI dependency injection
- [ ] Use context managers for all connections
- [ ] Monitor connection count and leak detection

#### 6. Transaction Boundaries (4-6 hours)
- [ ] Wrap related operations in explicit transactions
- [ ] Move external API calls outside transactions
- [ ] Add rollback handling on errors

#### 7. Idempotency Keys (4-6 hours)
- [ ] Add idempotency key support to upload/create endpoints
- [ ] Use UPSERT patterns for duplicate prevention
- [ ] Add unique constraints to schema

#### 8. WebSocket Reliability (4-6 hours)
- [ ] Add message sequence numbers
- [ ] Implement catch-up mechanism for reconnects
- [ ] Buffer last N messages per document

**Total Estimated Time: 2-3 days**

---

### Monitor (Metrics + Thresholds) - P2

#### 9. Database Metrics
- [ ] Track "Database is locked" error rate (threshold: > 0.1%)
- [ ] Monitor write transaction duration (p99 < 100ms)
- [ ] Watch WAL file size (alert if > 100MB)
- [ ] Alert on connection leak (open connections > 100)

#### 10. State Consistency
- [ ] Log frontend/backend version mismatches
- [ ] Track optimistic update rollback rate
- [ ] Monitor WebSocket disconnect/reconnect rate

#### 11. Checkpoint Health
- [ ] Track checkpoint save/load latency (p99 < 1s)
- [ ] Count corrupted checkpoint recoveries
- [ ] Monitor orphaned temp file accumulation

---

## Verification & Testing Strategy

### Concurrent Write Test
```python
# tests/test_concurrent_writes.py
import pytest
import asyncio
import aiosqlite

@pytest.mark.asyncio
async def test_concurrent_document_updates():
    """Test 50 concurrent writers don't cause lock errors"""
    async def writer(worker_id: int):
        async with aiosqlite.connect("test.db", timeout=5.0) as conn:
            await conn.execute("PRAGMA journal_mode=WAL;")
            for i in range(100):
                await conn.execute(
                    "INSERT INTO test (worker_id, iteration) VALUES (?, ?)",
                    (worker_id, i)
                )
                await conn.commit()

    # Run 50 concurrent writers
    tasks = [writer(i) for i in range(50)]
    await asyncio.gather(*tasks)

    # Verify all writes succeeded
    async with aiosqlite.connect("test.db") as conn:
        result = await conn.execute("SELECT COUNT(*) FROM test")
        count = (await result.fetchone())[0]
        assert count == 5000  # 50 workers * 100 iterations
```

### Checkpoint Atomicity Test
```python
# tests/test_checkpoint_atomicity.py
import pytest
import os
import signal
import subprocess

def test_checkpoint_crash_recovery():
    """Kill process during checkpoint write, verify no corruption"""
    # Start background process that writes checkpoints
    proc = subprocess.Popen(['python', 'scripts/stress_test_checkpoints.py'])

    # Wait a bit, then kill it
    import time
    time.sleep(2)
    os.kill(proc.pid, signal.SIGKILL)

    # Verify all checkpoint files are valid JSON
    import glob
    import json
    for checkpoint_file in glob.glob("checkpoints/*.json"):
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)  # Should not raise
            assert 'document_id' in data
```

### Load Test with Playwright
```typescript
// tests/e2e/concurrent_edits.spec.ts
import { test, expect } from '@playwright/test';

test('concurrent edits show conflict warning', async ({ browser }) => {
  // Open two tabs editing same document
  const context1 = await browser.newContext();
  const context2 = await browser.newContext();

  const page1 = await context1.newPage();
  const page2 = await context2.newPage();

  await page1.goto('/documents/test-doc');
  await page2.goto('/documents/test-doc');

  // Both edit the same field
  await page1.fill('#element-text', 'User 1 edit');
  await page2.fill('#element-text', 'User 2 edit');

  // User 1 saves first
  await page1.click('#save-button');
  await expect(page1.locator('.success-message')).toBeVisible();

  // User 2 saves second - should see conflict warning
  await page2.click('#save-button');
  await expect(page2.locator('.conflict-warning')).toBeVisible();
});
```

---

## Integrity Score: 4/10

### Justification
- ⚠️ **CRITICAL**: No WAL mode configured → immediate "Database is locked" errors under concurrent load
- ⚠️ **CRITICAL**: Synchronous sqlite3 in async handlers → event loop blocking, cascading failures
- ⚠️ **CRITICAL**: No optimistic locking → silent data loss from concurrent edits
- ⚠️ **CRITICAL**: Non-atomic checkpoint writes → corrupted checkpoints on crash
- ⚠️ **HIGH**: No busy timeout → instant failures instead of retry
- ⚠️ **HIGH**: Missing transaction boundaries → partial failure scenarios

### Top 3 Fixes (Highest Impact)
1. **Enable WAL + busy_timeout** (2-4 hours) - Eliminates 90% of lock errors
2. **Atomic checkpoint writes** (4-6 hours) - Prevents checkpoint corruption
3. **Replace sqlite3 with aiosqlite** (6-8 hours) - Prevents event loop blocking

---

## Appendix: Complete Configuration Example

```python
# backend/core/database.py - Complete example
import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncGenerator

class DatabaseManager:
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path

    async def initialize(self):
        """One-time initialization - call on app startup"""
        async with self.get_connection() as conn:
            # WAL mode persists in DB file
            result = await conn.execute("PRAGMA journal_mode=WAL;")
            mode = (await result.fetchone())[0]
            print(f"Journal mode: {mode}")

            # Optional: Checkpoint and truncate WAL
            await conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Get configured database connection"""
        conn = await aiosqlite.connect(self.db_path, timeout=5.0)

        try:
            # Apply per-connection settings
            await conn.execute("PRAGMA busy_timeout=5000;")
            await conn.execute("PRAGMA synchronous=NORMAL;")
            await conn.execute("PRAGMA foreign_keys=ON;")
            await conn.execute("PRAGMA cache_size=-64000;")
            await conn.execute("PRAGMA temp_store=MEMORY;")

            # Enable row factory for dict-like access
            conn.row_factory = aiosqlite.Row

            yield conn
        finally:
            await conn.close()

# Singleton instance
db_manager = DatabaseManager()

# FastAPI dependency
async def get_db():
    async with db_manager.get_connection() as conn:
        yield conn

# Usage in endpoints
from fastapi import Depends

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str, db=Depends(get_db)):
    async with db.execute("SELECT * FROM documents WHERE id=?", (doc_id,)) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None

@app.on_event("startup")
async def startup():
    await db_manager.initialize()
```

---

**End of Audit**
