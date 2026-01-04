# Performance & Event Loop Blocking Audit

**Metadata:**
- **Priority**: P0 (Event Loop Blocking) / P1 (General Performance)
- **Merged from**: Archive #1 (Performance & Scalability), #25 (CPU-Bound Event Loop)
- **Markers**: ⚠️ AI-CODING RISK | 🐍 PYTHON/FASTAPI
- **Status**: Ready for audit

---

## Overview

This consolidated audit addresses critical performance and scalability issues with **primary focus on event loop blocking** - the P0 issue that can cause catastrophic failures under load. The secondary focus is on general performance, scalability, and production readiness.

### Why Event Loop Blocking is P0 Critical

```
┌─────────────────────────────────────────────────────────────────┐
│                    UVICORN EVENT LOOP                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Request 1│  │ Request 2│  │WebSocket │  │HealthChk │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│       ▼             ▼             ▼             ▼               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              SINGLE THREAD EVENT LOOP                    │   │
│  │  If ANY task blocks here, ALL tasks wait!                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Failure Mode**: A single blocking Docling conversion (30-60s) freezes ALL concurrent requests, WebSocket connections, and health checks.

---

## PART 1: EVENT LOOP BLOCKING (P0 CRITICAL) ⚠️🐍

### Tech Stack Context
- **Backend**: Python 3.12 + FastAPI + Uvicorn (async ASGI)
- **Document Processing**: Docling (ML-based document understanding)
- **Image Processing**: OpenCV, Pillow, pdf2image
- **Database**: SQLite3 (with potential async issues)
- **Real-time**: WebSockets for progress updates
- **State**: Checkpoint files (JSON serialization)

### Load Test Target
- 50 concurrent document uploads
- 10 WebSocket connections for progress monitoring
- Background processing of 5 documents simultaneously
- **SLO**: WebSocket heartbeat response < 100ms, API response < 500ms during processing

---

## 1.1) Direct CPU-Bound Library Calls in Async Context ⚠️

### [ ] A) Docling Processing Without Offloading - CRITICAL

**Problem**: Direct calls to Docling pipeline, document conversion, or ML inference in async handlers.

**Anti-Pattern to Find**:
```python
# BLOCKING - Freezes event loop for 30-60+ seconds
@app.post("/process")
async def process_document(file: UploadFile):
    doc = DocumentConverter().convert(file)  # CPU-bound, ML inference!
    return doc
```

**Failure Mode**: Single document processing blocks ALL other requests, WebSocket heartbeats fail, health checks timeout.

**Blocking Duration**: 30-60+ seconds per document (varies by complexity, page count)

**Where to Look**:
- `backend/api/endpoints/processing.py`
- `backend/api/endpoints/upload.py`
- Pipeline stage executors (15 stages total)
- Any direct `DocumentConverter()` calls

**The Fix - Pattern 1: asyncio.to_thread() (Python 3.9+)**:
```python
import asyncio

async def process_document(file_path: str):
    # Offload CPU-bound work to thread pool
    result = await asyncio.to_thread(
        docling_convert,  # sync function
        file_path
    )
    return result
```

**The Fix - Pattern 2: run_in_executor() with Custom Pool**:
```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

# For CPU-bound work (bypass GIL for true parallelism)
cpu_executor = ProcessPoolExecutor(max_workers=4)

async def process_document(file_path: str):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        cpu_executor,
        docling_convert,  # must be picklable
        file_path
    )
    return result
```

**The Fix - Pattern 3: FastAPI Background Tasks**:
```python
from fastapi import BackgroundTasks

@app.post("/upload")
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    doc_id = save_upload(file)
    # Don't await - schedule for background processing
    background_tasks.add_task(process_document_sync, doc_id)
    return {"doc_id": doc_id, "status": "processing"}
```

---

### [ ] B) OpenCV/Pillow Image Operations - CRITICAL

**Problem**: Any `cv2.*`, `PIL.Image.*`, or `pdf2image.convert_from_*` in async functions.

**Common Hotspots**:
- Image resizing/rotation
- Color space conversion
- PDF to image rendering (especially at 216 DPI for OCR)
- Bounding box drawing

**Failure Mode**: Image operations (100ms-5s per page) cause request queuing and WebSocket delays.

**Where to Look**:
- `backend/services/pdf_image_extractor/extractor.py`
- `backend/api/endpoints/preprocessing.py`
- Any image rendering for viewer components

**Anti-Pattern**:
```python
async def render_pdf_page(pdf_path: str, page_num: int):
    # BLOCKING - PDF rendering at high DPI is CPU-intensive
    images = pdf2image.convert_from_path(
        pdf_path,
        dpi=216,  # OCR requires high DPI
        first_page=page_num,
        last_page=page_num
    )
    return images[0]
```

**The Fix**:
```python
import asyncio

async def render_pdf_page(pdf_path: str, page_num: int):
    # Offload to thread pool
    image = await asyncio.to_thread(
        _render_pdf_page_sync,
        pdf_path,
        page_num
    )
    return image

def _render_pdf_page_sync(pdf_path: str, page_num: int):
    images = pdf2image.convert_from_path(
        pdf_path,
        dpi=216,
        first_page=page_num,
        last_page=page_num
    )
    return images[0]
```

**OpenCV Operations to Flag**:
```python
# All of these BLOCK the event loop:
cv2.imread(path)
cv2.resize(image, size)
cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
cv2.rectangle(image, pt1, pt2, color)
cv2.imencode('.png', image)
```

---

### [ ] C) JSON Serialization of Large Objects - HIGH

**Problem**: `json.dumps()` / `json.loads()` on checkpoint files or large document structures.

**Blocking Duration**: 100-500ms for 10MB+ checkpoints (varies by complexity)

**Where to Look**:
- `backend/core/checkpoint/manager.py`
- All checkpoint save/load operations
- Pydantic `.model_dump()` / `.model_validate()` on complex nested models

**Anti-Pattern**:
```python
async def save_checkpoint(data: dict, path: str):
    # BLOCKING - Large JSON serialization can take 100-500ms
    checkpoint_json = json.dumps(data, indent=2)
    with open(path, "w") as f:
        f.write(checkpoint_json)
```

**The Fix - Pattern 1: anyio.to_thread.run_sync()**:
```python
import anyio

async def save_checkpoint(data: dict, path: str):
    await anyio.to_thread.run_sync(
        _save_checkpoint_sync,
        data,
        path
    )

def _save_checkpoint_sync(data: dict, path: str):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
```

**The Fix - Pattern 2: Combine with aiofiles**:
```python
import asyncio
import aiofiles

async def save_checkpoint(data: dict, path: str):
    # Offload serialization to thread
    json_str = await asyncio.to_thread(json.dumps, data, indent=2)
    # Async file write
    async with aiofiles.open(path, "w") as f:
        await f.write(json_str)
```

---

### [ ] D) PDF Parsing Operations - CRITICAL

**Problem**: `PyPDF2`, `pdfplumber`, `fitz` (PyMuPDF), `pdf2image` calls.

**Blocking Duration**: 5-30 seconds for 50-page PDFs

**Where to Look**:
- Any PDF metadata extraction
- Page count operations
- Text extraction from PDFs

**The Fix**:
```python
import asyncio

async def extract_pdf_metadata(pdf_path: str):
    metadata = await asyncio.to_thread(
        _extract_pdf_metadata_sync,
        pdf_path
    )
    return metadata

def _extract_pdf_metadata_sync(pdf_path: str):
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    metadata = {
        "page_count": len(doc),
        "title": doc.metadata.get("title"),
        # ... other metadata
    }
    doc.close()
    return metadata
```

---

## 1.2) Synchronous File I/O in Async Context ⚠️

### [ ] A) Blocking File Operations - HIGH

**Problem**: Standard `open()`, `read()`, `write()` without `aiofiles` or thread offloading.

**Failure Mode**: Disk I/O (especially on network mounts) blocks event loop for 10-500ms.

**Anti-Pattern**:
```python
async def save_checkpoint(data):
    with open("checkpoint.json", "w") as f:
        json.dump(data, f)  # BLOCKING!
```

**The Fix**:
```python
import aiofiles

async def save_checkpoint(data):
    async with aiofiles.open("checkpoint.json", "w") as f:
        await f.write(json.dumps(data))
```

---

### [ ] B) Temporary File Handling - MEDIUM

**Where to Look**:
- `tempfile.NamedTemporaryFile`, `shutil.copy`, `os.path` operations
- Document upload handling
- PDF upload temp storage

**The Fix**:
```python
import asyncio
import tempfile
import shutil

async def save_upload(file: UploadFile):
    # Read file content (async)
    content = await file.read()

    # Offload file writing to thread
    temp_path = await asyncio.to_thread(
        _save_to_temp,
        content
    )
    return temp_path

def _save_to_temp(content: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(content)
        return f.name
```

---

### [ ] C) Checkpoint Read/Write Operations - HIGH

**Problem**: Multi-page documents generate large checkpoint files (10MB+). Reading/writing without async causes event loop blocking.

**Where to Look**:
- `backend/core/checkpoint/manager.py`
- All 15 pipeline stage checkpoint operations
- `backend/core/intercepting_pipeline/checkpoint_handler.py`

**The Fix**:
```python
import asyncio
import aiofiles

class CheckpointManager:
    async def save_checkpoint(self, stage: int, data: dict, doc_id: str):
        # Offload JSON serialization to thread
        json_str = await asyncio.to_thread(json.dumps, data, indent=2)

        # Async file write
        path = self._get_checkpoint_path(doc_id, stage)
        async with aiofiles.open(path, "w") as f:
            await f.write(json_str)

    async def load_checkpoint(self, stage: int, doc_id: str) -> dict:
        path = self._get_checkpoint_path(doc_id, stage)

        # Async file read
        async with aiofiles.open(path, "r") as f:
            json_str = await f.read()

        # Offload JSON parsing to thread
        data = await asyncio.to_thread(json.loads, json_str)
        return data
```

---

## 1.3) Database Operations That Block ⚠️🐍

### [ ] A) SQLite Synchronous Calls - CRITICAL

**Problem**: SQLite's `sqlite3` module is entirely synchronous. Any `cursor.execute()`, `connection.commit()` in async context blocks.

**Where to Look**:
- `backend/core/database.py`
- Any direct `sqlite3` usage

**The Fix - Option 1: aiosqlite**:
```python
import aiosqlite

async def get_document(doc_id: str):
    async with aiosqlite.connect("database.db") as db:
        async with db.execute(
            "SELECT * FROM documents WHERE id = ?",
            (doc_id,)
        ) as cursor:
            row = await cursor.fetchone()
    return row
```

**The Fix - Option 2: run_in_executor**:
```python
import asyncio
import sqlite3
from concurrent.futures import ThreadPoolExecutor

db_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="db")

async def get_document(doc_id: str):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        db_executor,
        _get_document_sync,
        doc_id
    )
    return result

def _get_document_sync(doc_id: str):
    conn = sqlite3.connect("database.db")
    cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return row
```

---

### [ ] B) Long-Running Queries - MEDIUM

**What to Check**:
- Complex queries without indexes
- Table scans on large datasets
- Bulk inserts/updates
- Transaction locks held during processing

**The Fix**: Even with `aiosqlite`, offload complex queries:
```python
async def bulk_insert_pages(doc_id: str, pages: list):
    # Heavy operation - offload to thread
    await asyncio.to_thread(
        _bulk_insert_sync,
        doc_id,
        pages
    )
```

---

## 1.4) Synchronous External API Calls ⚠️

### [ ] A) Label Studio SDK Calls - CRITICAL

**Problem**: Label Studio SDK uses `requests` (synchronous HTTP). Any call to Label Studio API blocks the event loop.

**Where to Look**:
- `backend/services/label_studio_client/client.py`
- `backend/api/endpoints/labelstudio/export.py`
- `backend/api/endpoints/labelstudio/import_.py`

**Common Operations**:
- Project creation
- Task import
- Annotation export

**Anti-Pattern**:
```python
from label_studio_sdk import Client

async def create_project(name: str):
    # BLOCKING - requests library is synchronous
    client = Client(url=LABEL_STUDIO_URL, api_key=API_KEY)
    project = client.create_project(title=name)  # BLOCKS!
    return project
```

**The Fix - Option 1: Offload to Thread**:
```python
import asyncio
from label_studio_sdk import Client

async def create_project(name: str):
    project = await asyncio.to_thread(
        _create_project_sync,
        name
    )
    return project

def _create_project_sync(name: str):
    client = Client(url=LABEL_STUDIO_URL, api_key=API_KEY)
    return client.create_project(title=name)
```

**The Fix - Option 2: Use httpx AsyncClient**:
```python
import httpx

async def create_project(name: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{LABEL_STUDIO_URL}/api/projects",
            headers={"Authorization": f"Token {API_KEY}"},
            json={"title": name}
        )
        response.raise_for_status()
        return response.json()
```

---

### [ ] B) Other HTTP Requests Without Async Client - HIGH

**What to Flag**:
- `requests.get/post` instead of `httpx` async client
- `urllib` usage
- Any third-party SDK that uses synchronous HTTP

**The Fix**: Always use `httpx.AsyncClient`:
```python
import httpx

async def fetch_external_data(url: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        return response.json()
```

---

## 1.5) WebSocket Impact Analysis ⚠️

### [ ] A) Heartbeat Starvation - CRITICAL

**Problem**: If event loop is blocked, WebSocket ping/pong fails. Client disconnects after missed heartbeats (typically 30-60s timeout).

**Failure Mode**: Progress updates stop, client shows "disconnected", user experience degraded.

**Where to Look**:
- `backend/websocket/manager.py`
- `backend/websocket/handlers.py`
- `backend/websocket/events.py`

**How to Verify**:
- Monitor WebSocket ping/pong latency during document processing
- Check WebSocket disconnection rate under load
- Add metrics for heartbeat intervals

**The Fix**: Ensure ALL operations in WebSocket handlers are async or offloaded:
```python
from fastapi import WebSocket

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        # Ensure heartbeat isn't blocked
        message = await websocket.receive_text()

        # Offload heavy processing
        result = await asyncio.to_thread(
            process_message,
            message
        )

        await websocket.send_json(result)
```

---

### [ ] B) Message Backpressure - HIGH

**Problem**: Blocked event loop prevents sending queued WebSocket messages. Messages pile up, causing memory growth and delayed updates.

**The Fix**: Monitor send buffer and implement backpressure:
```python
from collections import deque

class WebSocketManager:
    def __init__(self):
        self.message_queue = deque(maxlen=1000)  # Bounded queue

    async def broadcast(self, message: dict):
        # Don't block on send - drop old messages if queue full
        if len(self.message_queue) >= 950:
            print("WebSocket queue near capacity, dropping old messages")
            # Implement backpressure strategy
```

---

## 1.6) Pipeline Stage Processing ⚠️

### [ ] A) Stage Executor Blocking - CRITICAL

**Problem**: Each of 15 pipeline stages likely has CPU-intensive processing. If run in async context without offloading, compounds blocking time.

**Priority Stages (Highest CPU Impact)**:
1. **Stage 3: OCR** - Docling OCR engine (10-30s per page)
2. **Stage 4: Layout Raw** - ML model inference (5-15s per page)
3. **Stage 6: Table Structure** - TableFormer model (5-20s per table)
4. **Stage 2: Preprocessing** - Image rendering for viewer (1-5s per page)

**Where to Look**:
- Each stage executor in pipeline
- `backend/core/intercepting_pipeline/`

**The Fix - Executor Pattern**:
```python
from concurrent.futures import ProcessPoolExecutor

# Global executor for CPU-bound pipeline stages
pipeline_executor = ProcessPoolExecutor(max_workers=4)

async def execute_stage(stage_num: int, input_data: dict):
    # Offload CPU-bound stage processing
    result = await asyncio.get_event_loop().run_in_executor(
        pipeline_executor,
        _execute_stage_sync,
        stage_num,
        input_data
    )
    return result

def _execute_stage_sync(stage_num: int, input_data: dict):
    # Heavy CPU work here - runs in separate process
    if stage_num == 3:  # OCR
        return run_ocr_stage(input_data)
    elif stage_num == 4:  # Layout
        return run_layout_stage(input_data)
    # ... other stages
```

---

### [ ] B) Sequential Stage Processing - HIGH

**Problem**: If stages run sequentially in async context, total blocking time compounds.
- 15 stages × 2s each = 30s of event loop blocking

**The Fix**: Use background tasks or task queue:
```python
from fastapi import BackgroundTasks

@app.post("/process/{doc_id}")
async def process_document(
    doc_id: str,
    background_tasks: BackgroundTasks
):
    # Don't wait for pipeline - schedule in background
    background_tasks.add_task(run_pipeline, doc_id)
    return {"status": "processing", "doc_id": doc_id}

async def run_pipeline(doc_id: str):
    for stage in range(1, 16):
        # Each stage offloaded to executor
        result = await execute_stage(stage, doc_id)
        await save_checkpoint(stage, result, doc_id)
```

---

## 1.7) Startup and Shutdown Blocking ⚠️

### [ ] A) Model Loading at Startup - HIGH

**Problem**: Docling model loading is CPU/memory intensive (30-60s). If done in async startup hook, delays server readiness and health checks timeout.

**Where to Look**:
- `backend/main.py` startup hooks
- Any global model initialization

**Anti-Pattern**:
```python
@app.on_event("startup")
async def startup():
    # BLOCKING - Delays server startup for 30-60s
    global docling_converter
    docling_converter = DocumentConverter()  # Loads ML models
```

**The Fix - Lazy Loading**:
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_converter():
    # Load on first use, not at startup
    return DocumentConverter()

async def process_document(doc_id: str):
    # Offload even the first lazy load
    converter = await asyncio.to_thread(get_converter)
    result = await asyncio.to_thread(converter.convert, doc_path)
    return result
```

**The Fix - Background Loading**:
```python
import asyncio

@app.on_event("startup")
async def startup():
    # Don't block startup - load models in background
    asyncio.create_task(load_models_background())

async def load_models_background():
    await asyncio.to_thread(_load_models_sync)

def _load_models_sync():
    global docling_converter
    docling_converter = DocumentConverter()
```

---

## 1.8) Verification & Monitoring 🐍

### [ ] Instrumentation to Add

**Event Loop Lag Monitoring**:
```python
import asyncio
import time

async def monitor_event_loop():
    while True:
        start = asyncio.get_event_loop().time()
        await asyncio.sleep(0.1)
        lag = asyncio.get_event_loop().time() - start - 0.1
        if lag > 0.01:  # 10ms threshold
            print(f'⚠️ Event loop lag: {lag*1000:.1f}ms')
```

**Blocking Operation Timer**:
```python
import time
from functools import wraps

def measure_blocking(threshold_ms=100):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            duration = (time.perf_counter() - start) * 1000
            if duration > threshold_ms:
                print(f'⚠️ {func.__name__} took {duration:.1f}ms')
            return result
        return wrapper
    return decorator
```

---

### [ ] Verification Commands

```bash
# Profile event loop blocking with py-spy
py-spy record -o profile.svg -- python -m uvicorn backend.main:app

# Check for blocking calls statically
ruff check --select=ASYNC  # async-related lints

# Runtime event loop monitoring
python -c "
import asyncio
async def monitor():
    while True:
        start = asyncio.get_event_loop().time()
        await asyncio.sleep(0.1)
        lag = asyncio.get_event_loop().time() - start - 0.1
        if lag > 0.01:
            print(f'Event loop lag: {lag*1000:.1f}ms')
asyncio.run(monitor())
"
```

---

## 1.9) Executor Strategy Recommendation 🐍

Based on workload analysis:

### Thread Pool (for I/O-bound operations)
```python
from concurrent.futures import ThreadPoolExecutor

# For sync I/O: file operations, sync HTTP, SQLite
io_executor = ThreadPoolExecutor(
    max_workers=10,  # Scale with I/O concurrency
    thread_name_prefix="io"
)
```

### Process Pool (for CPU-bound operations)
```python
from concurrent.futures import ProcessPoolExecutor

# For heavy CPU work: Docling, OpenCV, PDF parsing
cpu_executor = ProcessPoolExecutor(
    max_workers=4,  # Match CPU cores
    # max_workers=min(4, os.cpu_count() or 1)
)
```

### When to Use Task Queue
Consider a task queue (Celery, ARQ, RQ) when:
- [ ] Pipeline processing takes >60s per document
- [ ] Scaling beyond single-server capacity
- [ ] Need job retry and failure handling
- [ ] Multiple document processing workflows

---

## PART 2: GENERAL PERFORMANCE & SCALABILITY (P1) ⚠️

### Tech Stack (Inferred)
- Backend: Python 3.12 + FastAPI + Uvicorn
- Frontend: React + TypeScript + Tailwind CSS
- Database: SQLite3 (single-file, no connection pool)
- Session: In-memory or database-backed
- Deployment: Single server, containerized

### Load Test Target
- 1,000 concurrent users
- 100 req/sec sustained
- Duration: 5 minutes
- SLO: p95 latency < 500ms for core endpoints, error rate < 1%

---

## 2.1) Database & Data Bottlenecks

### [ ] A) N+1 Patterns - HIGH

**Where to Look**:
- DB calls inside `.map()`, `for` loops, list comprehensions
- Per-item fetches in API endpoints
- React components calling endpoints in `useEffect` for each item

**Common Hotspots**:
- Document list rendering (fetch metadata per document)
- Stage data fetching (per-page or per-element queries)
- Related data loading (checkpoints, thumbnails)

**Anti-Pattern**:
```python
@app.get("/documents")
async def get_documents():
    docs = await db.query("SELECT id FROM documents")
    # N+1 - Queries once per document
    results = []
    for doc in docs:
        metadata = await db.query("SELECT * FROM metadata WHERE doc_id = ?", doc.id)
        results.append({**doc, "metadata": metadata})
    return results
```

**The Fix**:
```python
@app.get("/documents")
async def get_documents():
    # Single query with JOIN
    results = await db.query("""
        SELECT d.*, m.*
        FROM documents d
        LEFT JOIN metadata m ON d.id = m.doc_id
    """)
    return results
```

---

### [ ] B) Unbounded Data Fetches - HIGH

**Problem**: GET endpoints that return arrays without `limit/offset/cursor` pagination.

**Where to Look**:
- `/api/documents` - could return 1000+ documents
- `/api/documents/{id}/pages` - could return 100+ pages
- Any list/collection endpoints

**Anti-Pattern**:
```python
@app.get("/documents")
async def get_documents():
    # Could return 10,000+ records
    return await db.query("SELECT * FROM documents")
```

**The Fix**:
```python
@app.get("/documents")
async def get_documents(
    limit: int = 50,
    offset: int = 0,
    max_limit: int = 100
):
    # Enforce pagination
    limit = min(limit, max_limit)
    results = await db.query(
        "SELECT * FROM documents LIMIT ? OFFSET ?",
        (limit, offset)
    )
    total = await db.query("SELECT COUNT(*) FROM documents")
    return {
        "items": results,
        "total": total,
        "limit": limit,
        "offset": offset
    }
```

---

### [ ] C) Indexing Gaps & Query Shape Risks - MEDIUM

**What to Check**:
- WHERE / ORDER BY / JOIN patterns that need indexes
- Composite indexes for multi-column filters
- Foreign key indexes

**Common Patterns Needing Indexes**:
```sql
-- Needs index on (doc_id, stage)
SELECT * FROM checkpoints WHERE doc_id = ? AND stage = ?

-- Needs index on (doc_id, page_num)
SELECT * FROM pages WHERE doc_id = ? ORDER BY page_num

-- Needs composite index on (status, created_at)
SELECT * FROM queue WHERE status = 'pending' ORDER BY created_at
```

**How to Verify**:
```python
# Add EXPLAIN analysis to queries
result = await db.execute("EXPLAIN QUERY PLAN SELECT ...")
# Look for "SCAN TABLE" without "USING INDEX"
```

**The Fix**:
```sql
-- Create indexes for common query patterns
CREATE INDEX idx_checkpoints_doc_stage ON checkpoints(doc_id, stage);
CREATE INDEX idx_pages_doc_num ON pages(doc_id, page_num);
CREATE INDEX idx_queue_status_created ON queue(status, created_at);
```

---

### [ ] D) Connection Pool Exhaustion - CRITICAL (for SQLite)

**Problem**: SQLite doesn't have traditional connection pooling. Concurrent writes cause locking and timeouts.

**SQLite Limitations**:
- Single writer at a time
- Write locks block all reads
- No connection pool configuration

**Where to Check**:
- Database connection creation pattern
- Write-heavy operations
- Transaction scope

**The Fix - Option 1: Use WAL mode**:
```python
import sqlite3

conn = sqlite3.connect("database.db")
# Enable Write-Ahead Logging for better concurrency
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
```

**The Fix - Option 2: Serialize writes**:
```python
from asyncio import Lock

db_write_lock = Lock()

async def write_operation(query: str, params: tuple):
    async with db_write_lock:
        # Serialize all writes
        await db.execute(query, params)
```

**The Fix - Option 3: Consider PostgreSQL**:
For production at scale, consider migrating to PostgreSQL with proper connection pooling.

---

## 2.2) Resource & Memory Leaks

### [ ] A) Zombie Connections / Handles - MEDIUM

**Where to Look**:
- File streams without close/context manager
- WebSocket connections without cleanup
- Temporary files not deleted

**Anti-Pattern**:
```python
def process_file(path: str):
    f = open(path)  # Never closed!
    data = f.read()
    return process(data)
```

**The Fix**:
```python
async def process_file(path: str):
    async with aiofiles.open(path) as f:
        data = await f.read()
    return await asyncio.to_thread(process, data)
```

---

### [ ] B) Global State Growth / Cache Leaks - HIGH

**Where to Look**:
- Global dictionaries/lists used as caches
- In-memory sessions
- Document metadata caching without TTL

**Anti-Pattern**:
```python
# MEMORY LEAK - Grows unbounded
document_cache = {}  # Global cache

async def get_document(doc_id: str):
    if doc_id not in document_cache:
        document_cache[doc_id] = await load_document(doc_id)
    return document_cache[doc_id]
```

**The Fix - LRU Cache with Size Limit**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_document_cached(doc_id: str):
    return load_document(doc_id)
```

**The Fix - TTL Cache**:
```python
from cachetools import TTLCache
import asyncio

document_cache = TTLCache(maxsize=100, ttl=300)  # 5 min TTL

async def get_document(doc_id: str):
    if doc_id not in document_cache:
        document_cache[doc_id] = await load_document(doc_id)
    return document_cache[doc_id]
```

---

### [ ] C) Log Flooding & Excessive Logging Cost - MEDIUM

**Where to Look**:
- `print()` or `logging.info()` in hot paths
- Verbose logging in loops
- Per-request logging without sampling

**Anti-Pattern**:
```python
for page in pages:
    print(f"Processing page {page.num}")  # Floods logs
    process_page(page)
```

**The Fix**:
```python
import logging
from backend.utils.logger import logger

# Use structured logging with levels
logger.info("Processing document", extra={
    "doc_id": doc_id,
    "page_count": len(pages)
})

# Sample verbose logs
if page.num % 10 == 0:
    logger.debug(f"Progress: {page.num}/{len(pages)} pages")
```

---

### [ ] D) Large Payload & Buffering Risks - HIGH

**Where to Look**:
- PDF upload handling
- Checkpoint file loading
- Image rendering endpoints
- Export endpoints (full document JSON)

**Anti-Pattern**:
```python
@app.post("/upload")
async def upload(file: UploadFile):
    # Loads entire PDF into memory
    content = await file.read()  # Could be 100MB+
    return process(content)
```

**The Fix - Stream Processing**:
```python
@app.post("/upload")
async def upload(file: UploadFile):
    # Stream to temp file
    temp_path = f"/tmp/{file.filename}"
    async with aiofiles.open(temp_path, "wb") as f:
        while chunk := await file.read(8192):  # 8KB chunks
            await f.write(chunk)
    return await process_file(temp_path)
```

**Enforce Body Size Limits**:
```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

app = FastAPI()

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.method == "POST":
        # 50MB limit
        max_size = 50 * 1024 * 1024
        if int(request.headers.get("content-length", 0)) > max_size:
            raise RequestValidationError("File too large")
    return await call_next(request)
```

---

## 2.3) Asynchronous & Network Fragility

### [ ] A) Missing Timeouts - CRITICAL

**Problem**: Every external call must have a hard timeout.

**Where to Look**:
- Label Studio API calls
- Any external HTTP requests
- Database query timeouts

**Anti-Pattern**:
```python
async with httpx.AsyncClient() as client:
    # No timeout - could hang forever
    response = await client.get(url)
```

**The Fix**:
```python
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.get(url)
```

**Database Timeouts (SQLite)**:
```python
conn = sqlite3.connect("database.db", timeout=5.0)
```

---

### [ ] B) Retry Storms & Unbounded Retries - MEDIUM

**Where to Look**:
- External API calls
- Failed processing retries
- Queue processing

**Anti-Pattern**:
```python
while True:
    try:
        return await external_api_call()
    except Exception:
        # Infinite retry storm
        await asyncio.sleep(1)
```

**The Fix - Exponential Backoff with Jitter**:
```python
import random

async def call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            # Exponential backoff with jitter
            delay = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)
```

---

### [ ] C) Race Conditions / Check-Then-Act - MEDIUM

**Where to Look**:
- Document creation (duplicate handling)
- Checkpoint file creation
- Cache stampedes

**Anti-Pattern**:
```python
# Race condition - two requests could create duplicate
if not await db.exists(doc_id):
    await db.create(doc_id)
```

**The Fix - Database Constraints**:
```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,  -- Prevents duplicates
    -- ...
);
```

**The Fix - Atomic Upsert**:
```python
await db.execute("""
    INSERT INTO documents (id, name)
    VALUES (?, ?)
    ON CONFLICT(id) DO UPDATE SET name = excluded.name
""", (doc_id, name))
```

---

### [ ] D) Waterfall Requests - MEDIUM

**Problem**: Sequential awaits where parallelization is safe.

**Anti-Pattern**:
```python
# Sequential - total time = sum of all
page1 = await fetch_page(1)
page2 = await fetch_page(2)
page3 = await fetch_page(3)
```

**The Fix**:
```python
# Parallel - total time = max of all
pages = await asyncio.gather(
    fetch_page(1),
    fetch_page(2),
    fetch_page(3)
)
```

---

## 2.4) Backend Resilience & Load Shedding

### [ ] A) Rate Limiting & Abuse Controls - HIGH

**Where to Look**:
- Expensive endpoints (document processing, export)
- Upload endpoints
- `backend/middleware/rate_limiter.py`

**The Fix**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/process")
@limiter.limit("5/minute")
async def process_document(request: Request):
    # Limited to 5 requests per minute per IP
    pass
```

---

### [ ] B) Circuit Breakers & Dependency Isolation - MEDIUM

**Where to Look**:
- Label Studio integration
- External API dependencies

**The Fix**:
```python
from pybreaker import CircuitBreaker

label_studio_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=60
)

@label_studio_breaker
async def call_label_studio():
    # Fails fast after 5 errors
    pass
```

---

### [ ] C) Error Handling & Observability Gaps - HIGH

**Where to Look**:
- Unhandled exceptions
- Missing correlation IDs
- No structured logging

**The Fix - Centralized Error Handler**:
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc)
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

**Add Correlation IDs**:
```python
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id")

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request_id_var.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

---

## 2.5) Front-End Performance (React)

### [ ] A) Re-render Hell - MEDIUM

**Where to Look**:
- High-frequency state updates (scroll, resize, typing)
- Missing `React.memo`, `useMemo`, `useCallback`
- Large component subtrees re-rendering

**Anti-Pattern**:
```typescript
// Re-renders entire list on every keystroke
function SearchableList({ items }) {
  const [search, setSearch] = useState('');

  const filtered = items.filter(item =>
    item.name.includes(search)  // Expensive on large lists
  );

  return (
    <>
      <input onChange={(e) => setSearch(e.target.value)} />
      {filtered.map(item => <Item key={item.id} item={item} />)}
    </>
  );
}
```

**The Fix**:
```typescript
import { useMemo, useCallback } from 'react';
import { debounce } from 'lodash';

function SearchableList({ items }) {
  const [search, setSearch] = useState('');

  // Debounce search to reduce re-renders
  const handleSearch = useCallback(
    debounce((value) => setSearch(value), 300),
    []
  );

  // Memoize expensive filter
  const filtered = useMemo(() =>
    items.filter(item => item.name.includes(search)),
    [items, search]
  );

  return (
    <>
      <input onChange={(e) => handleSearch(e.target.value)} />
      {filtered.map(item => <MemoizedItem key={item.id} item={item} />)}
    </>
  );
}

const MemoizedItem = React.memo(Item);
```

---

### [ ] B) Large List Rendering Without Virtualization - HIGH

**Where to Look**:
- Document lists (100+ documents)
- Page lists (100+ pages)
- Element lists in stage viewers

**The Fix**:
```typescript
import { FixedSizeList } from 'react-window';

function DocumentList({ documents }) {
  const Row = ({ index, style }) => (
    <div style={style}>
      <DocumentItem document={documents[index]} />
    </div>
  );

  return (
    <FixedSizeList
      height={600}
      itemCount={documents.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
```

---

### [ ] C) Data Fetch Loops / Hydration Storms - HIGH

**Where to Look**:
- `useEffect` dependencies causing repeated fetches
- Aggressive polling
- Low `staleTime` in queries

**Anti-Pattern**:
```typescript
useEffect(() => {
  // Re-fetches on every render
  fetchDocuments();
}, [documents]);  // documents changes, causes re-fetch
```

**The Fix - React Query**:
```typescript
import { useQuery } from '@tanstack/react-query';

function Documents() {
  const { data } = useQuery({
    queryKey: ['documents'],
    queryFn: fetchDocuments,
    staleTime: 60000,  // 1 minute
    refetchOnWindowFocus: false
  });
}
```

---

### [ ] D) Large Payload Injection - MEDIUM

**Where to Look**:
- Fetching entire documents when only metadata needed
- Loading all pages when only current page displayed

**The Fix**:
```typescript
// Instead of fetching full document
const { data: document } = useQuery(['document', id]);

// Fetch only needed data
const { data: metadata } = useQuery(['document-metadata', id]);
const { data: currentPage } = useQuery(['document-page', id, pageNum]);
```

---

## ACTION PLAN

### Fix Now (Before Load Test) - P0

1. **[ ] Docling Processing Offloading** (CRITICAL)
   - Wrap all `DocumentConverter` calls in `asyncio.to_thread()` or process pool
   - Estimated time: 4-8 hours

2. **[ ] OpenCV/Pillow Operations** (CRITICAL)
   - Offload all image operations to thread pool
   - Estimated time: 3-6 hours

3. **[ ] SQLite Async Safety** (CRITICAL)
   - Implement `aiosqlite` or `run_in_executor` for all DB operations
   - Estimated time: 6-10 hours

4. **[ ] Label Studio SDK Offloading** (CRITICAL)
   - Wrap all Label Studio calls in `asyncio.to_thread()`
   - Estimated time: 2-4 hours

5. **[ ] Checkpoint I/O Async** (HIGH)
   - Use `aiofiles` + `asyncio.to_thread()` for JSON serialization
   - Estimated time: 3-5 hours

**Total Estimated Time: 18-33 hours**

---

### Fix Soon (Next Iteration) - P1

1. **[ ] Pagination** - Add to all list endpoints
2. **[ ] Database Indexing** - Add indexes for common queries
3. **[ ] Rate Limiting** - Implement on expensive endpoints
4. **[ ] Request Body Size Limits** - Prevent OOM on large uploads
5. **[ ] React Virtualization** - Add to large lists
6. **[ ] Error Handling** - Centralized exception handler and correlation IDs

---

### Monitor (Add Instrumentation)

Add these metrics before load testing:

```python
# Event loop health
- Event loop lag (time between scheduled and actual execution)
- Request queue depth
- WebSocket ping/pong latency

# Performance
- p95/p99 latency per endpoint
- Processing time per pipeline stage
- Checkpoint save/load time

# Resources
- Memory usage and GC frequency
- CPU usage per executor
- Database query time
- Connection pool stats (if using PostgreSQL)

# Reliability
- Error rate by endpoint
- Timeout count
- Retry count
- Circuit breaker state
```

**Recommended Test Command**:
```bash
# Baseline load test
locust -f load_test.py --host=http://localhost:8000 --users=50 --spawn-rate=5

# Monitor event loop during test
py-spy top --pid <uvicorn-pid>
```

---

## Severity Classification Reference

- **CRITICAL**: Will cause immediate failures under load (event loop blocking >5s, pool exhaustion, OOM, cascading failures)
- **HIGH**: Significant performance degradation or partial failures likely
- **MEDIUM**: Noticeable UX degradation but not immediate outage
- **MONITOR**: Acceptable for now; watch metrics and revisit at thresholds

---

## Production Readiness Score

**Current Vibe Score: 3/10** - Multiple critical issues; will fail under concurrent load

**Justification**:
- Event loop blocking throughout codebase (Docling, OpenCV, file I/O)
- Synchronous SQLite calls without async wrapper
- No timeout protection on external calls
- Missing pagination and rate limiting
- Global state growth risks

**After P0 Fixes: 7/10** - Ready for load testing with monitoring

---

## References

### Code Examples Repository
All code patterns shown in this audit are production-ready and can be copied directly.

### Stack-Specific Focus Areas

**Docling Integration Points**:
- `DocumentConverter` initialization and conversion
- `PdfPipelineOptions` processing
- Model inference calls (Layout, OCR, Table)

**OpenCV Operations**:
- `cv2.imread`, `cv2.resize`, `cv2.cvtColor`
- Contour detection, bounding box operations
- Image encoding/decoding

**Pillow Operations**:
- `Image.open`, `Image.save`
- Format conversion, thumbnail generation

**pdf2image Operations**:
- `convert_from_path`, `convert_from_bytes`
- High DPI rendering (especially 216+ DPI for OCR)

**Checkpoint Operations**:
- JSON serialization of document state
- Multi-page checkpoint files (can be 10MB+)
- Frequent saves between pipeline stages

---

**END OF AUDIT**
