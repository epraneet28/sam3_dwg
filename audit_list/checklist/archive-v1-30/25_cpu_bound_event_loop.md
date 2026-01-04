# CPU-Bound Event Loop Audit Prompt (Python/FastAPI Async-Safety)

## Role
Act as a Senior Python Backend Engineer and Async Concurrency Expert. Perform a deep-dive CPU-Bound Event Loop Audit on the provided FastAPI codebase to identify blocking operations that will freeze the async event loop.

## Primary Goal
Identify where CPU-intensive operations (Docling, OpenCV, Pillow, PDF parsing) are blocking the async event loop, causing request starvation, WebSocket heartbeat failures, and cascading timeouts. Provide concrete fixes using `run_in_executor`, `anyio.to_thread.run_sync`, or process pools.

## Context
- This is a document processing pipeline using FastAPI with heavy CPU-bound workloads.
- AI-generated code often calls CPU-intensive libraries directly in async handlers without offloading.
- A single blocking call can freeze ALL concurrent requests, WebSocket connections, and health checks.

## Tech Stack
- **Backend**: Python 3.12 + FastAPI + Uvicorn (async ASGI)
- **Document Processing**: Docling (ML-based document understanding)
- **Image Processing**: OpenCV, Pillow, pdf2image
- **Database**: SQLite3 (with potential async issues)
- **Real-time**: WebSockets for progress updates
- **State**: Checkpoint files (JSON serialization)

## Critical Understanding: Python's Event Loop

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

## Load Test Target
- 50 concurrent document uploads
- 10 WebSocket connections for progress monitoring
- Background processing of 5 documents simultaneously
- SLO: WebSocket heartbeat response < 100ms, API response < 500ms during processing

## Audit Requirements

Scan all files systematically for CPU-blocking patterns. Focus on these critical areas:

---

## 1) Direct CPU-Bound Library Calls in Async Context

### A) Docling Processing Without Offloading
- Look for direct calls to Docling pipeline, document conversion, or ML inference in async handlers.
- Common patterns:
  ```python
  # BLOCKING - Freezes event loop
  @app.post("/process")
  async def process_document(file: UploadFile):
      doc = DocumentConverter().convert(file)  # CPU-bound!
      return doc
  ```
- **Failure Mode**: Single document processing (30-60+ seconds) blocks ALL other requests.
- **Suggested Fix**: Offload to thread pool or process pool.

### B) OpenCV/Pillow Image Operations
- Flag any `cv2.*`, `PIL.Image.*`, or `pdf2image.convert_from_*` in async functions.
- Common hotspots:
  - Image resizing/rotation
  - Color space conversion
  - PDF to image rendering
  - Bounding box drawing
- **Failure Mode**: Image operations (100ms-5s per page) cause request queuing.
- **Suggested Fix**: Wrap in `asyncio.to_thread()` or `run_in_executor()`.

### C) PDF Parsing Operations
- Look for `PyPDF2`, `pdfplumber`, `fitz` (PyMuPDF), `pdf2image` calls.
- These are CPU-intensive for large/complex PDFs.
- **Failure Mode**: 50-page PDF parsing blocks event loop for 5-30 seconds.

### D) JSON Serialization of Large Objects
- `json.dumps()` / `json.loads()` on checkpoint files or large document structures.
- Pydantic `.model_dump()` / `.model_validate()` on complex nested models.
- **Failure Mode**: Serializing 10MB+ checkpoints blocks for 100-500ms.

---

## 2) Synchronous File I/O in Async Context

### A) Blocking File Operations
- Look for standard `open()`, `read()`, `write()` without `aiofiles`.
- Flag patterns like:
  ```python
  async def save_checkpoint(data):
      with open("checkpoint.json", "w") as f:
          json.dump(data, f)  # BLOCKING!
  ```
- **Failure Mode**: Disk I/O (especially on network mounts) blocks event loop.
- **Suggested Fix**: Use `aiofiles` or offload to thread.

### B) Temporary File Handling
- `tempfile.NamedTemporaryFile`, `shutil.copy`, `os.path` operations.
- Often used in document upload handling.

### C) Checkpoint Read/Write Operations
- All checkpoint save/load operations should be async or offloaded.
- Large checkpoint files (multi-page documents) are particularly risky.

---

## 3) Database Operations That Block

### A) SQLite Synchronous Calls
- SQLite's `sqlite3` module is entirely synchronous.
- Any `cursor.execute()`, `connection.commit()` in async context blocks.
- **Suggested Fix**: Use `aiosqlite` or wrap in `run_in_executor()`.

### B) Long-Running Queries
- Complex queries, table scans, or bulk inserts.
- Transaction locks held during processing.

### C) Connection Per Request Anti-Pattern
- Creating new SQLite connections in each request (slow due to file locking).

---

## 4) Synchronous External API Calls

### A) Label Studio SDK Calls
- The Label Studio SDK uses `requests` (synchronous HTTP).
- Any call to Label Studio API blocks the event loop.
- Common operations: project creation, task import, annotation export.
- **Suggested Fix**: Use `httpx.AsyncClient` or offload SDK calls.

### B) HTTP Requests Without Async Client
- Look for `requests.get/post` instead of `httpx` async client.
- Flag any `urllib` usage.

---

## 5) WebSocket Impact Analysis

### A) Heartbeat Starvation
- If event loop is blocked, WebSocket ping/pong fails.
- Client disconnects after missed heartbeats (typically 30-60s timeout).
- **Failure Mode**: Progress updates stop, client shows "disconnected".

### B) Message Backpressure
- Blocked event loop prevents sending queued WebSocket messages.
- Messages pile up, causing memory growth and delayed updates.

### C) Concurrent Connection Handling
- All WebSocket connections share the same event loop.
- One blocked request affects all WebSocket clients.

---

## 6) Pipeline Stage Processing

### A) Stage Executor Blocking
- Each of 15 pipeline stages likely has CPU-intensive processing.
- Audit each stage executor for blocking calls.
- Priority stages (highest CPU impact):
  1. OCR stage (Docling OCR engine)
  2. Layout Raw (ML model inference)
  3. Table Structure (TableFormer model)
  4. Image rendering for viewer

### B) Sequential Stage Processing
- If stages run sequentially in async context, total blocking time compounds.
- 15 stages × 2s each = 30s of event loop blocking.

### C) Checkpoint Operations Between Stages
- Save/load operations between each stage add blocking time.

---

## 7) Startup and Shutdown Blocking

### A) Model Loading at Startup
- Docling model loading is CPU/memory intensive (can take 30-60s).
- If done in async startup hook, delays server readiness.
- Health checks may timeout during model loading.

### B) Graceful Shutdown Blocking
- Pending document processing may block shutdown.
- Checkpoint saving during shutdown should be handled carefully.

---

## Correct Patterns Reference

### Pattern 1: Using `asyncio.to_thread()` (Python 3.9+)
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

### Pattern 2: Using `run_in_executor()` with Custom Pool
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# For I/O-bound blocking (file ops, sync HTTP)
io_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="io")

# For CPU-bound work (bypass GIL for true parallelism)
cpu_executor = ProcessPoolExecutor(max_workers=4)

async def process_image(image_path: str):
    loop = asyncio.get_event_loop()
    # Use process pool for CPU-bound OpenCV work
    result = await loop.run_in_executor(
        cpu_executor,
        cv2_process_image,  # must be picklable
        image_path
    )
    return result
```

### Pattern 3: Using `anyio.to_thread.run_sync()` (FastAPI preferred)
```python
import anyio

async def save_checkpoint(data: dict, path: str):
    await anyio.to_thread.run_sync(
        lambda: json.dump(data, open(path, "w"))
    )
```

### Pattern 4: Background Tasks for Fire-and-Forget
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

### Pattern 5: Dedicated Worker Process (Production)
```python
# For heavy workloads, use a task queue
# Celery, ARQ, or simple multiprocessing.Queue
from arq import create_pool

async def enqueue_processing(doc_id: str):
    redis = await create_pool(RedisSettings())
    await redis.enqueue_job('process_document', doc_id)
```

---

## Anti-Patterns to Flag

### Anti-Pattern 1: Direct Sync Call in Async Handler
```python
# BAD - Blocks event loop
@app.post("/process")
async def process(file: UploadFile):
    result = heavy_cpu_function(file)  # BLOCKING!
    return result
```

### Anti-Pattern 2: Sync-in-Async Wrapper Without Offloading
```python
# BAD - Still blocking, just hidden
async def process_async(data):
    return sync_heavy_function(data)  # No await, still blocking!
```

### Anti-Pattern 3: await on Sync Function
```python
# BAD - await doesn't make sync code async
async def handler():
    result = await sync_function()  # TypeError or still blocking
```

### Anti-Pattern 4: Blocking in Middleware
```python
# BAD - Affects EVERY request
@app.middleware("http")
async def log_middleware(request, call_next):
    sync_write_to_file(request.url)  # Blocks all requests!
    return await call_next(request)
```

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s)
Risk Category: Event Loop Blocking | File I/O | Database | External API | WebSocket

The Problem:
- 2-4 sentences explaining why this blocks the event loop.
- Be specific about the blocking duration and affected operations.
- Example: "Docling conversion takes 30-60s per document. During this time, all API requests queue, WebSocket heartbeats fail, and health checks timeout."

Blocking Duration Estimate:
- Estimated blocking time per operation.
- Impact on concurrent requests.
- Confidence: High | Medium | Low

How to Verify:
- Add timing instrumentation: `time.perf_counter()` around suspected code.
- Check event loop lag: `asyncio.get_event_loop().time()` before/after.
- Use `py-spy` or `yappi` profiler during load test.
- Monitor WebSocket disconnection rate during processing.

The Fix:
- Provide the corrected async-safe code.
- Show which executor/offloading pattern to use.
- Include any required imports and pool configuration.

Trade-off Consideration:
- Thread pool: GIL limits true parallelism, but simple to implement.
- Process pool: True parallelism, but serialization overhead and complexity.
- Task queue: Most scalable, but adds infrastructure dependency.
```

## Severity Classification

- **CRITICAL**: Blocks event loop >5 seconds. Will cause WebSocket disconnects, health check failures, request timeouts. Immediate fix required.
- **HIGH**: Blocks event loop 1-5 seconds. Noticeable request queuing and latency spikes.
- **MEDIUM**: Blocks event loop 100ms-1s. Degrades p99 latency but unlikely to cause failures.
- **MONITOR**: Blocks <100ms. Acceptable for now but should be tracked.

---

## Vibe Score Rubric (Async Safety 1-10)

Rate overall async safety based on blocking patterns found:

- **9-10**: All CPU-bound work properly offloaded; ready for concurrent load.
- **7-8**: Minor blocking issues; most heavy operations handled correctly.
- **5-6**: Several blocking patterns; concurrent requests will queue significantly.
- **3-4**: Major blocking in request handlers; WebSocket stability at risk.
- **<3**: Synchronous architecture in async framework; complete refactor needed.

---

## Summary Sections (Mandatory)

### Blocking Hotspots Summary
List all identified blocking operations with estimated duration:
| Location | Operation | Est. Block Time | Fix Complexity |
|----------|-----------|-----------------|----------------|

### Executor Strategy Recommendation
Based on workload analysis, recommend:
1. Thread pool sizing (for I/O-bound operations)
2. Process pool sizing (for CPU-bound operations)
3. Whether a task queue is warranted

### Fix Now (Before Load Test)
- Items that will cause immediate failures under concurrent load.

### Fix Soon (Next Iteration)
- Items that degrade performance but won't cause outages.

### Monitor (Add Instrumentation)
- Add these metrics to track event loop health:
  - `asyncio` event loop lag (time between scheduled and actual execution)
  - Request queue depth
  - WebSocket ping/pong latency
  - Processing time per pipeline stage

---

## Verification Commands

```bash
# Profile event loop blocking with py-spy
py-spy record -o profile.svg -- python -m uvicorn app:app

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

## Stack-Specific Focus Areas

### Docling Integration Points
- `DocumentConverter` initialization and conversion
- `PdfPipelineOptions` processing
- Model inference calls (Layout, OCR, Table)

### OpenCV Operations
- `cv2.imread`, `cv2.resize`, `cv2.cvtColor`
- Contour detection, bounding box operations
- Image encoding/decoding

### Pillow Operations
- `Image.open`, `Image.save`
- Format conversion
- Thumbnail generation

### pdf2image Operations
- `convert_from_path`, `convert_from_bytes`
- High DPI rendering (especially 216+ DPI for OCR)

### Checkpoint Operations
- JSON serialization of document state
- Multi-page checkpoint files (can be 10MB+)
- Frequent saves between pipeline stages
