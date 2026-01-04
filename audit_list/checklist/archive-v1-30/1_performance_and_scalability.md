# Performance & Scalability Audit Prompt (Production-Ready, High-Concurrency)

## Role
Act as a Senior Site Reliability Engineer (SRE) and Performance Architect. Perform a deep-dive Performance & Scalability Audit on the provided codebase to prepare for a high-concurrency load test.

## Primary Goal
Identify where AI-generated logic, shortcuts, and architectural gaps will fail under stress, and provide concrete fixes that make the system load test ready.

## Context
- This code was developed with a focus on speed ("vibecoded") and has not yet been stress-tested.
- I need you to find bottlenecks, failure modes, and reliability gaps before running a high-concurrency load test.

## Tech Stack (adjust if different)
- Backend: Node.js / Express
- Frontend: React
- Database: ORM/raw may vary (infer from code)
- Optional: Redis, queues, WebSockets (infer from code)

## Load Test Target
- 1,000 concurrent users
- 100 req/sec sustained
- Duration: 5 minutes
- SLO guidance (use if not provided): p95 latency < 500ms for core endpoints, error rate < 1%

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (DB type, ORM, deployment model, pool settings, env/config, migrations), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - DB type (Postgres/MySQL/MongoDB/etc), ORM/query library (Prisma/Sequelize/Knex/etc)
   - Session strategy (in-memory vs Redis vs DB)
   - Caching layer and TTL usage
   - Deployment model (single VM, container, serverless) if visible
   - Node version, reverse proxy usage (NGINX/ALB), and any CDN hints
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) Database & Data Bottlenecks

### A) N+1 Patterns
- Look for DB calls inside `.map()`, forEach, loops, or repeated per-item fetches.
- Common hotspots: Express route handlers, services, React useEffect hooks calling per-item endpoints.
- Suggested Fix: Batch queries with JOINs or IN clauses; prefetch; DataLoader batching where appropriate.

### B) Unbounded Data Fetches
- Find GET endpoints that return arrays without `limit/offset/cursor` pagination.
- Flag queries that could return 10,000+ records in one request.
- Suggested Fix: Implement pagination defaults (e.g., limit=50) and enforce maximums.

### C) Indexing Gaps & Query Shape Risks
- Identify WHERE / ORDER BY / JOIN patterns that likely need indexes.
- Flag patterns like `WHERE col=? AND col2=? ORDER BY col3` when no composite index is apparent.
- Suggested Fix: Propose indexes and recommend EXPLAIN analysis.

### D) Connection Pool Exhaustion
- Find DB clients created per-request, missing pooling, or pool misconfiguration.
- Look for pool size too small, long transactions, and "pool wait" conditions.
- Suggested Fix: Use a singleton pooled client, tune pool size, reduce transaction scope.

---

## 2) Resource & Memory Leaks

### A) Zombie Connections / Handles
- DB clients, Redis connections, file streams, WebSockets opened without close/destroy/finally.
- Flag missing `try/finally` cleanup in async operations.
- Suggested Fix: Ensure cleanup via try/finally, lifecycle hooks, and pooling.

### B) Global State Growth / Cache Leaks
- Global arrays/objects/Maps used as caches without TTL/max size.
- Sessions stored in memory in production.
- Suggested Fix: LRU with max size, Redis with TTL, eviction policies.

### C) Log Flooding & Excessive Logging Cost
- `console.log/error` in hot paths, loops, or per-request verbose dumps.
- Suggested Fix: Structured logging (pino/winston), levels, sampling, disable debug in prod.

### D) Large Payload & Buffering Risks
- Buffering whole files in memory, large JSON bodies, huge responses without streaming/backpressure.
- Suggested Fix: Stream upload/downloads, enforce body size limits, paginate responses.

---

## 3) Asynchronous & Network Fragility

### A) Missing Timeouts (Mandatory)
- Every fetch/axios/external API call must have a hard timeout.
- Flag missing AbortController, axios timeout, DB statement timeouts if applicable.
- Suggested Fix: Add timeouts and align with SLA (e.g., 5-30s).

### B) Retry Storms & Unbounded Retries
- Retrying without jitter/backoff or retrying non-idempotent requests.
- Suggested Fix: Exponential backoff with jitter, retry budgets, idempotency keys.

### C) Race Conditions / Check-Then-Act
- Patterns like if (exists) create, cache stampedes, duplicate inserts under concurrency.
- Suggested Fix: DB unique constraints, atomic upserts, distributed locks, SWR caching.

### D) Waterfall Requests
- Sequential awaits where parallelization is safe.
- Suggested Fix: Promise.all/Promise.allSettled where appropriate.

### E) Event Loop Blocking (Node-specific)
- Synchronous crypto/fs, heavy parsing, CPU-bound loops on request path, large JSON.stringify/parse.
- Suggested Fix: Move CPU work off-request, worker threads/queues, streaming, incremental parsing.

---

## 4) Backend Resilience & Load Shedding (SRE-focus)

### A) Rate Limiting & Abuse Controls
- Missing rate limits on expensive endpoints, missing auth checks, missing request size limits.
- Suggested Fix: Rate limiting, request body size caps, compression strategy.

### B) Circuit Breakers & Dependency Isolation
- External dependencies without breakers/bulkheads.
- Suggested Fix: Circuit breaker (possum or equivalent), separate pools, graceful degradation.

### C) Backpressure & Streaming
- Missing backpressure with streams or large responses.
- Suggested Fix: Proper streaming and bounded buffers.

### D) Error Handling & Observability Gaps
- Missing centralized error middleware, unhandled promise rejections, lack of correlation IDs.
- Suggested Fix: Standard error handling, request IDs, structured logs, metrics, tracing.

---

## 5) Front-End Performance "Jank" Triggers (React)

### A) Re-render Hell
- High-frequency state updates (scroll/resize/typing/mousemove) causing large subtree re-renders.
- Missing React.memo/useMemo/useCallback, and no debounce/throttle where needed.
- Suggested Fix: Memoize, throttle/debounce, component splits.

### B) Large List Rendering Without Virtualization
- Rendering large tables/lists without windowing.
- Suggested Fix: React-window/react-virtualized, pagination/infinite scroll.

### C) Data Fetch Loops / Hydration Storms
- useEffect dependencies mistake causing repeated fetches, aggressive polling, low staleTime.
- Suggested Fix: Stabilize dependencies, React Query/SWR config, dedupe requests.

### D) Large Payload Injection
- Fetching entire API payloads in state when only a subset is used.
- Suggested Fix: project/normalize data, selectors, avoid megabyte state blobs.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s)
Risk Category: Database | Memory | Async | Runtime | Resilience | Frontend

The Problem:
- 2-4 sentences explaining why it fails under the specified load.
- Be specific about failure mode: timeout, pool exhaustion, OOM, event loop stall, cascading retries, LI jank, etc.

Performance Impact:
- Provide a realistic estimate (example: "Pool wait spikes -> p95 2s+", "Heap grows 200MB over 5 min", "Blocks event loop 15ms per request").
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (EXPLAIN plan, metric to add, flamegraph, tracing span, heap snapshot, load-test assertion).

The Fix:
- Provide the optimized code snippet.
- Show before/after if useful.
- If fix requires info/config, show the config change and where it belongs.

Trade-off Consideration:
- Note complexity, cost, and any risks (e.g., "Adds Redis dependency but prevents stampede").
- If acceptable at small scale, mark as MONITOR with what threshold triggers refactor.
```

## Severity Classification
- **CRITICAL**: Will very likely fail the load test (timeouts, pool exhaustion, OOM, event loop stalls, cascading retries).
- **HIGH**: Likely to degrade performance significantly or cause partial failures.
- **MEDIUM**: Noticeable UX/perf degradation but not immediate outage.
- **MONITOR**: Acceptable for now; watch metrics and revisit at thresholds.

---

## Vibe Score Rubric (Production Readiness 1-10)

Rate overall readiness based on severity/quantity and systemic risks:
- **9-10**: Ready for 1K+ concurrency; minor issues only.
- **7-8**: Needs 1-2 critical fixes before load testing.
- **5-6**: Significant refactoring needed; load test only after fixes.
- **3-4**: Multiple critical issues; will fail under load.
- **<3**: Do not deploy; fundamental architecture issues.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (before load test)
2) Fix Soon (next iteration)
3) Monitor (metrics + thresholds)

## Also include:
- Estimated time to implement all Fix Now items (range is fine)
- Infrastructure to add before running the load test:
  - Metrics: p95/p99 latency per endpoint, error rate, DB pool wait, DB query time, Redis ops, Node event loop lag, heap usage/gc.
  - Tracing: request path spans for DB/external calls
  - Logging: structured logs with request/correlation IDs
  - Recommended test command:
    - `npx autocannon` flags -> run baseline load test -> compare deltas -> iterate
