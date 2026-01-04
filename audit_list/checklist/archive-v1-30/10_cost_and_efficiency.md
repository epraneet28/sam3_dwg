# Cost & Efficiency Audit Prompt (Production-Ready, Resource Optimization)

## Role
Act as a Senior Cloud Economist and Backend Optimization Specialist. Perform a deep-dive Cost & Efficiency Audit on the provided codebase to identify wasteful resource consumption, unnecessary operations, and opportunities for optimization.

## Primary Goal
Identify where AI-generated logic introduces inefficiencies, redundant operations, and resource waste that will compound costs at scale, and provide concrete fixes that reduce operational overhead.

## Context
- This code was developed with a focus on speed ("vibecoded") and may contain inefficient patterns that work fine in development but become costly in production.
- I need you to find cost drivers, wasteful patterns, and optimization opportunities before scaling to production workloads.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn
- Document Processing: Docling engine
- Database: SQLite3 (state persistence)
- Image Processing: OpenCV, Pillow, pdf2image
- External Integration: Label Studio SDK
- Real-time: WebSockets
- Frontend: React 19 + TypeScript 5.9 + Vite 7
- State Management: Zustand
- Infrastructure: Docker (Python 3.11-slim-bookworm)

## Efficiency Targets
- Reduce redundant I/O operations by 50%+
- Minimize checkpoint file sizes without data loss
- Optimize WebSocket message frequency (batch where possible)
- Reduce image re-rendering to only when necessary
- Minimize unnecessary API calls and database queries

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (storage paths, caching config, message frequency settings), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - Storage patterns (local filesystem, temp files, checkpoint directories)
   - Caching strategy (in-memory, disk, none)
   - Image processing pipeline (DPI settings, format conversions)
   - WebSocket message patterns (frequency, payload sizes)
   - Logging verbosity and destinations
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) Database & Query Inefficiencies

### A) Redundant Queries
- Look for repeated identical queries within the same request lifecycle.
- Flag queries that fetch the same data multiple times without caching.
- Common hotspots: Document status checks, checkpoint metadata reads, user permission lookups.
- Suggested Fix: Request-scoped caching, query result memoization, batch fetches.

### B) Unbatched Operations
- Find loops that execute individual INSERT/UPDATE statements.
- Flag patterns like `for item in items: db.insert(item)` instead of batch inserts.
- Suggested Fix: Use `executemany()`, bulk insert patterns, transaction batching.

### C) Unnecessary Data Retrieval
- Identify SELECT * patterns when only specific columns are needed.
- Flag queries that retrieve full records for existence checks.
- Suggested Fix: Column projection, EXISTS queries, COUNT instead of full fetch.

### D) SQLite-Specific Inefficiencies
- Missing PRAGMA optimizations (synchronous, cache_size, temp_store).
- Transaction overhead from auto-commit mode.
- Lack of prepared statement reuse.
- Suggested Fix: Configure PRAGMAs, explicit transactions, statement caching.

---

## 2) Image Processing Waste

### A) Redundant Image Re-rendering
- Look for page images being regenerated on every request.
- Flag missing caching of rendered images.
- Identify DPI conversions happening multiple times for the same source.
- Suggested Fix: Cache rendered images with content hashes, lazy rendering.

### B) Unnecessary Format Conversions
- Find patterns converting PNG→JPEG→PNG or similar round-trips.
- Flag base64 encoding/decoding happening in loops.
- Look for image quality loss through repeated compression.
- Suggested Fix: Preserve original format, convert once at boundaries.

### C) Memory-Inefficient Image Operations
- Loading full images when only thumbnails are needed.
- Processing all pages when only specific pages are requested.
- Missing image streaming (loading entire image into memory).
- Suggested Fix: Thumbnail generation, lazy loading, streaming reads.

### D) OpenCV/Pillow Overhead
- Unnecessary color space conversions.
- Loading images at full resolution for dimension checks.
- Missing image metadata caching (dimensions, format).
- Suggested Fix: Read metadata without loading pixels, cache dimensions.

---

## 3) Checkpoint & Storage Bloat

### A) Checkpoint File Size Growth
- Storing redundant data across checkpoint stages.
- Embedding base64 images in JSON checkpoints.
- Missing compression for large text fields.
- Storing full document state when deltas would suffice.
- Suggested Fix: Delta-based checkpoints, external image references, compression.

### B) Orphaned File Cleanup
- Temporary files not deleted after processing.
- Old checkpoints never pruned.
- Uploaded files retained after processing completion.
- Suggested Fix: Cleanup hooks, TTL-based pruning, background cleanup jobs.

### C) Inefficient Serialization
- Using verbose JSON when binary formats would be smaller.
- Pretty-printing JSON in production (whitespace overhead).
- Redundant nested structures with repeated data.
- Suggested Fix: Compact JSON, consider MessagePack for large payloads.

### D) Disk I/O Overhead
- Writing checkpoints synchronously on every change.
- Missing write batching or debouncing.
- Reading entire checkpoint files for small updates.
- Suggested Fix: Debounced writes, partial updates, memory-mapped files.

---

## 4) WebSocket Message Inefficiency

### A) High-Frequency Updates
- Sending updates on every minor state change.
- Per-keystroke or per-pixel updates instead of debounced.
- Polling patterns over WebSocket (redundant with push).
- Suggested Fix: Debounce/throttle updates, batch multiple changes.

### B) Oversized Payloads
- Sending full document state when only changed fields are needed.
- Embedding large data (images, full text) in WebSocket messages.
- Lack of payload compression.
- Suggested Fix: Delta updates, external references, message compression.

### C) Unnecessary Broadcasts
- Broadcasting to all clients when only specific clients need updates.
- Sending updates for unchanged data.
- Missing client subscription filtering.
- Suggested Fix: Topic-based routing, change detection, client filters.

### D) Connection Overhead
- Creating new connections for each operation.
- Missing connection pooling or multiplexing.
- Excessive ping/pong frequency.
- Suggested Fix: Persistent connections, reduced heartbeat frequency.

---

## 5) API & Network Waste

### A) Unnecessary API Calls
- Fetching data that's already available locally.
- Polling for updates when WebSocket push is available.
- Redundant Label Studio API calls for unchanged data.
- Suggested Fix: Local caching, push notifications, request deduplication.

### B) Oversized Responses
- API endpoints returning more data than needed.
- Missing response filtering or projection.
- Lack of compression (gzip) for large responses.
- Suggested Fix: Field selection, pagination, response compression.

### C) Chatty Protocols
- Multiple sequential requests that could be batched.
- Round-trips for data that could be prefetched.
- Missing HTTP/2 or request pipelining opportunities.
- Suggested Fix: Batch endpoints, prefetch patterns, HTTP/2 multiplexing.

### D) Retry Waste
- Retrying failed requests without backoff.
- Retrying non-idempotent operations.
- Aggressive retry policies consuming resources.
- Suggested Fix: Exponential backoff, idempotency keys, retry budgets.

---

## 6) Logging & Observability Overhead

### A) Excessive Logging Volume
- DEBUG-level logging enabled in production.
- Logging entire request/response bodies.
- Per-iteration logging in loops.
- Suggested Fix: Production log levels, sampling, structured logging.

### B) Log Storage Costs
- Unbounded log retention.
- Logging to slow storage (network drives).
- Lack of log rotation and compression.
- Suggested Fix: Log rotation, retention policies, async logging.

### C) Metric Cardinality Explosion
- High-cardinality labels (user IDs, document IDs) in metrics.
- Metrics generated for every request detail.
- Missing metric aggregation.
- Suggested Fix: Bounded cardinality, histogram aggregation, sampling.

### D) Tracing Overhead
- Tracing every request at full detail.
- Span storage for low-value operations.
- Missing sampling strategies.
- Suggested Fix: Head/tail sampling, trace pruning, priority-based retention.

---

## 7) Compute & CPU Waste

### A) Redundant Computations
- Recalculating derived data on every access.
- Missing memoization for expensive operations.
- Repeated regex compilation.
- Suggested Fix: Caching, memoization, compile-once patterns.

### B) Inefficient Algorithms
- O(n²) patterns where O(n) or O(n log n) is possible.
- Linear searches in large collections.
- String concatenation in loops.
- Suggested Fix: Appropriate data structures, indexing, StringBuilder patterns.

### C) Frontend Re-computation
- Expensive calculations in render loops.
- Missing useMemo/useCallback for derived data.
- Recomputing on every state change.
- Suggested Fix: Memoization, selectors, computed state.

### D) Unnecessary Parsing
- Parsing JSON/XML repeatedly for the same document.
- Missing parsed data caching.
- Parsing entire documents when partial access suffices.
- Suggested Fix: Parse once and cache, lazy parsing, streaming parsers.

---

## 8) Docling-Specific Inefficiencies

### A) Model Loading Overhead
- Loading models on every request instead of at startup.
- Not sharing model instances across requests.
- Loading unused model components.
- Suggested Fix: Model singleton, lazy loading, component selection.

### B) Pipeline Redundancy
- Running all stages when only specific stages are needed.
- Not caching intermediate pipeline results.
- Re-processing unchanged pages.
- Suggested Fix: Stage caching, incremental processing, change detection.

### C) Coordinate Transformation Waste
- Repeated coordinate conversions between systems.
- Missing transformation matrix caching.
- Converting all bboxes when only visible ones are needed.
- Suggested Fix: Lazy conversion, cached matrices, viewport culling.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: HIGH | MEDIUM | LOW | OPTIMIZATION]

Location: FileName : Line Number(s)
Waste Category: Database | Image | Storage | WebSocket | API | Logging | Compute | Docling

The Problem:
- 2-4 sentences explaining the inefficiency and its cost at scale.
- Be specific about waste type: redundant I/O, wasted CPU, excessive storage, bandwidth waste, etc.

Cost Impact:
- Provide a realistic estimate of resource waste.
- Examples: "100 redundant queries/request", "5MB checkpoint bloat/document", "10 unnecessary renders/page view"
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (profiling, query logging, storage audit, network capture, metric analysis).

The Fix:
- Provide the optimized code snippet.
- Show before/after if useful.
- If fix requires config changes, show the config and where it belongs.

Savings Estimate:
- Quantify expected improvement.
- Examples: "Reduces queries by 80%", "Cuts checkpoint size by 60%", "Eliminates 90% of re-renders"
```

## Severity Classification
- **HIGH**: Significant resource waste that compounds at scale (storage, bandwidth, compute).
- **MEDIUM**: Noticeable inefficiency that affects performance or costs.
- **LOW**: Minor optimization opportunity with incremental benefit.
- **OPTIMIZATION**: Nice-to-have improvement, not urgent.

---

## Efficiency Score Rubric (Resource Optimization 1-10)

Rate overall efficiency based on severity/quantity and systemic waste:
- **9-10**: Highly optimized; minimal waste identified.
- **7-8**: Some inefficiencies but generally well-optimized.
- **5-6**: Multiple areas of waste; needs optimization before scale.
- **3-4**: Significant inefficiencies; will be costly at scale.
- **<3**: Wasteful patterns throughout; major refactoring needed.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 optimizations list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Quick Wins (low effort, high impact)
2) Optimization Backlog (medium effort, good returns)
3) Future Consideration (when scaling requires it)

## Also include:
- Estimated cost savings after implementing Quick Wins
- Metrics to track for ongoing efficiency monitoring:
  - Query count per request
  - Checkpoint file sizes
  - WebSocket message frequency
  - Image render cache hit rate
  - API call deduplication rate
  - Storage growth rate
- Recommended profiling approach:
  - Python: cProfile, memory_profiler, py-spy
  - SQLite: EXPLAIN QUERY PLAN, query logging
  - Network: Chrome DevTools, WebSocket frame inspector
  - Storage: `du -sh`, checkpoint size tracking
