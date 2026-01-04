# Load Test Readiness Audit Prompt (Production-Ready, High-Concurrency)

## Role
Act as a Senior Performance Engineer and Load Testing Specialist. Perform a comprehensive Load Test Readiness Audit on the provided codebase to ensure meaningful, reliable load testing outcomes.

## Primary Goal
Identify gaps in test infrastructure, data preparation, environment parity, and success criteria that would invalidate load test results or cause false positives/negatives. Ensure the system is properly instrumented and configured before running high-concurrency tests.

## Context
- This is a document processing pipeline built with Python/FastAPI, Docling, SQLite, and React 19/TypeScript.
- The codebase was developed with AI assistance ("vibecoded") and requires validation before production deployment.
- Load testing must cover the full document lifecycle: upload, multi-stage processing, real-time updates, and export.

## Tech Stack
- **Backend**: Python 3.12 + FastAPI + Uvicorn + Pydantic v2
- **Processing**: Docling (document AI), OpenCV, Pillow, pdf2image
- **Database**: SQLite3 with file-based checkpoints
- **Real-time**: WebSockets for progress updates
- **Frontend**: React 19 + TypeScript 5.9 + Vite 7 + Zustand
- **Integration**: Label Studio SDK for annotation workflows

## Load Test Targets
- **Concurrent Users**: 50-200 simultaneous document sessions
- **Document Upload Rate**: 10-50 uploads/minute
- **Processing Throughput**: 5-20 documents completing pipeline/minute
- **WebSocket Connections**: 100-500 concurrent connections
- **Duration**: 15-30 minute sustained load
- **SLO Guidance**: p95 upload < 2s, p95 stage transition < 5s, WebSocket latency < 100ms, error rate < 1%

---

## Audit Requirements
Scan the codebase and infrastructure configuration to assess load test readiness across all dimensions below.

---

## 1) Test Data Preparation

### A) Realistic Document Corpus
- Verify test PDFs represent real-world complexity:
  - Page counts: 1-page, 10-page, 50-page, 100+ page documents
  - Content types: text-heavy, image-heavy, tables, mixed layouts
  - File sizes: 100KB, 1MB, 10MB, 50MB+
  - Quality: clean scans, noisy scans, rotated pages, multi-column
- Flag if test data is synthetic/trivial (single page, simple text only).
- **Stack-specific**: Include documents with complex tables (for TableFormer), formulas (LaTeX extraction), and code blocks.

### B) Data Volume & Cardinality
- Ensure sufficient volume to stress:
  - SQLite write contention (hundreds of concurrent document records)
  - Checkpoint storage growth (thousands of JSON files)
  - File system I/O (concurrent PDF reads, image generation)
- Flag if tests use < 50 unique documents or reuse the same document.
- **Stack-specific**: Pre-generate checkpoint data for mid-pipeline testing (e.g., start at stage 8 instead of stage 1).

### C) Test Data Isolation
- Verify test data does not pollute production or staging databases.
- Check for proper cleanup scripts/fixtures after test runs.
- Flag shared file storage paths without namespace isolation.
- **Stack-specific**: Ensure `checkpoints/`, `uploads/`, and SQLite DB have test-specific paths.

### D) Seed Data & State Setup
- Verify ability to pre-populate system state for specific scenarios:
  - Documents at various pipeline stages
  - Pre-existing Label Studio projects and annotations
  - Partially processed checkpoints for resume testing
- Flag if all tests must start from empty state.

---

## 2) User Journey Coverage

### A) Critical Path Mapping
Verify load tests cover all critical user journeys:

| Journey | Description | Endpoints/Flows |
|---------|-------------|-----------------|
| Upload Flow | PDF upload → validation → initial processing | POST /upload, WebSocket progress |
| Stage Navigation | View/edit each of 15 pipeline stages | GET /stages/{id}, PUT /stages/{id} |
| Real-time Updates | WebSocket progress during processing | ws://host/ws |
| Export Flow | Generate final outputs (MD, JSON, HTML) | GET /export/{format} |
| Concurrent Editing | Multiple users editing same document | PUT with optimistic locking |
| Recovery Flow | Resume from checkpoint after failure | GET /checkpoints, POST /resume |

- Flag if any critical journey is missing from load test scenarios.
- **Stack-specific**: Ensure TableCellMatchingEditor, ReadingOrderEditor, and BboxEditor interactions are covered.

### B) User Behavior Modeling
- Verify think times between actions (realistic pauses, not machine-gun requests).
- Check for proper session simulation (cookies, WebSocket lifecycle).
- Flag if all requests are stateless/independent (unrealistic).
- **Stack-specific**: Model the edit-save-continue cycle for stage editors.

### C) Error Path Coverage
- Include scenarios that trigger errors:
  - Invalid PDF uploads (corrupt, password-protected, non-PDF)
  - Mid-processing failures (Docling model errors, OOM)
  - WebSocket disconnection during processing
  - Concurrent edit conflicts
- Flag if load tests only cover happy paths.

### D) Mixed Workload Simulation
- Verify tests include realistic workload mix:
  - 60% passive viewers (GET requests, WebSocket listeners)
  - 30% active editors (stage modifications)
  - 10% heavy operations (uploads, full pipeline runs)
- Flag if tests assume uniform user behavior.

---

## 3) Ramp Strategy & Load Profiles

### A) Ramp-Up Configuration
- Verify gradual ramp-up to target load (not instant spike):
  - Recommended: 10% of target per minute
  - Allow system to warm up (JIT, connection pools, caches)
- Flag instant-start load tests that miss warm-up issues.
- **Stack-specific**: Docling model loading on first request can cause cold-start latency.

### B) Load Profile Variety
Ensure tests cover multiple profiles:

| Profile | Purpose | Configuration |
|---------|---------|---------------|
| Baseline | Establish normal performance | 10% target load, 5 min |
| Ramp | Find saturation point | 0→100% over 10 min |
| Sustained | Test stability | 80% target, 30 min |
| Spike | Test elasticity | 50%→150%→50% rapid |
| Soak | Find memory leaks | 50% target, 2+ hours |

- Flag if only single load profile is defined.
- **Stack-specific**: Include checkpoint file accumulation in soak tests.

### C) Cooldown & Recovery
- Verify tests include cooldown period to observe:
  - Connection draining
  - Background task completion
  - Memory release
- Flag tests that stop abruptly without recovery observation.

---

## 4) Pass/Fail Criteria & SLOs

### A) Quantitative Success Criteria
Verify explicit, measurable pass/fail thresholds:

| Metric | Target | Failure Threshold |
|--------|--------|-------------------|
| p50 Latency (API) | < 200ms | > 500ms |
| p95 Latency (API) | < 1s | > 3s |
| p99 Latency (API) | < 3s | > 10s |
| Error Rate | < 0.5% | > 1% |
| WebSocket Latency | < 50ms | > 200ms |
| Upload Success Rate | > 99% | < 95% |
| Pipeline Completion | > 95% | < 90% |
| Memory Growth | Stable | > 50% increase |

- Flag if pass/fail is subjective ("looks fast enough").
- **Stack-specific**: Include Docling processing time per page as a metric.

### B) Business SLO Alignment
- Verify load test criteria align with actual business requirements:
  - User expectations (how long will users wait?)
  - Contract/SLA commitments
  - Competitive benchmarks
- Flag if criteria are arbitrary or copied from templates.

### C) Regression Detection
- Define acceptable variance from baseline:
  - p95 latency regression > 20% = fail
  - Throughput regression > 15% = fail
- Flag if no historical baseline exists for comparison.

### D) Resource Utilization Limits
- Define acceptable resource consumption:
  - CPU utilization < 80% sustained
  - Memory < 85% of allocation
  - Disk I/O < 70% capacity
  - SQLite lock contention < 5% of requests
- Flag if resource limits are undefined.

---

## 5) Environment Parity

### A) Infrastructure Matching
Verify test environment matches production:

| Component | Production | Test | Parity Check |
|-----------|------------|------|--------------|
| CPU cores | X | Y | Y >= 50% of X |
| Memory | X GB | Y GB | Y >= 50% of X |
| Disk IOPS | X | Y | Similar class |
| Network | X Gbps | Y Gbps | Y >= X |
| SQLite version | X | Y | X == Y |
| Python version | 3.12 | ? | Exact match |
| Docling version | X | ? | Exact match |

- Flag significant discrepancies that would invalidate results.
- **Stack-specific**: Ensure NVIDIA GPU availability matches if using GPU-accelerated models.

### B) Configuration Parity
- Verify test environment uses production-equivalent config:
  - Uvicorn worker count
  - SQLite connection settings
  - File upload limits
  - WebSocket connection limits
  - Docling model settings (batch sizes, timeouts)
- Flag if test uses debug/development settings.

### C) External Dependency Simulation
- Verify external services are properly simulated or isolated:
  - Label Studio API (mock vs. real instance)
  - Any cloud storage integrations
- Flag if tests depend on shared external services that could cause interference.
- **Stack-specific**: Label Studio mock should simulate realistic response times.

### D) Network Conditions
- Verify tests can simulate realistic network conditions:
  - Latency injection (50-200ms for remote users)
  - Bandwidth limits (especially for large PDF uploads)
  - Packet loss (1-2% for poor connections)
- Flag if tests assume perfect local network.

---

## 6) Instrumentation & Observability

### A) Metrics Collection
Verify comprehensive metrics are captured during tests:

**Backend Metrics:**
- Request latency (p50, p95, p99) per endpoint
- Request rate and error rate
- SQLite query time and lock contention
- Checkpoint read/write latency
- WebSocket message latency
- Docling processing time per stage
- Memory usage (heap, RSS)
- CPU utilization per worker
- File descriptor count
- Active connection count

**Frontend Metrics:**
- Time to First Byte (TTFB)
- Largest Contentful Paint (LCP)
- First Input Delay (FID)
- JavaScript heap size
- WebSocket reconnection count

- Flag if any critical metric is missing.

### B) Tracing Setup
- Verify distributed tracing is configured:
  - Request correlation IDs
  - Span coverage for DB, external calls, processing stages
  - Trace sampling rate appropriate for load
- Flag if traces will be incomplete or overwhelming.
- **Stack-specific**: Ensure 15-stage pipeline has per-stage spans.

### C) Log Aggregation
- Verify logs are:
  - Structured (JSON format)
  - Include request IDs
  - Aggregated to searchable store
  - Not set to DEBUG level during load tests
- Flag if log volume will cause I/O bottleneck.

### D) Real-time Dashboards
- Verify dashboards are prepared showing:
  - Live request rate and latency
  - Error rate trends
  - Resource utilization
  - Queue depths (if applicable)
  - WebSocket connection count
- Flag if dashboards must be built during the test.

---

## 7) Test Tool Configuration

### A) Load Generator Selection
Recommend appropriate tools for this stack:

| Tool | Use Case | Stack Fit |
|------|----------|-----------|
| Locust | Python-native, WebSocket support | Excellent |
| k6 | JavaScript, good metrics | Good |
| Artillery | YAML config, WebSocket | Good |
| Gatling | JVM-based, enterprise | Medium |
| autocannon | Node.js, HTTP only | Limited |

- Flag if selected tool cannot:
  - Maintain WebSocket connections
  - Upload binary files (PDFs)
  - Handle cookie/session state

### B) Script Quality Checks
- Verify load test scripts include:
  - Proper error handling (don't stop on first error)
  - Response validation (check status codes, response bodies)
  - Think time variation (not fixed delays)
  - Data parameterization (different PDFs, user sessions)
- Flag hardcoded values that limit test realism.
- **Stack-specific**: Scripts should validate checkpoint creation, not just HTTP 200.

### C) Resource Limits on Load Generator
- Verify load generator machine(s) can handle target load:
  - File descriptor limits
  - Network connection limits
  - CPU for maintaining WebSocket connections
- Flag if single machine generates > 10K requests/sec.

---

## 8) Pre-Test Validation Checklist

### A) Smoke Test Requirements
Before full load test, verify:
- [ ] Single user can complete full document lifecycle
- [ ] All 15 pipeline stages execute successfully
- [ ] WebSocket connections establish and receive updates
- [ ] Checkpoints are created and readable
- [ ] Export generates valid output files
- [ ] Metrics appear in monitoring dashboards

### B) Baseline Establishment
- [ ] Run single-user baseline to establish expected latencies
- [ ] Document baseline metrics for regression comparison
- [ ] Verify no errors under minimal load
- [ ] Confirm resource utilization at idle and under light load

### C) Capacity Estimation
- Estimate expected capacity based on:
  - Single-request latency × target throughput
  - Memory per connection × target connections
  - Disk I/O per document × target processing rate
- Flag if estimates suggest target exceeds theoretical capacity.

---

## Output Format (Mandatory)

For each gap or issue found, provide:

```
[READINESS: BLOCKER | WARNING | RECOMMENDATION]

Category: Test Data | User Journeys | Load Profile | Pass/Fail Criteria | Environment | Instrumentation | Tooling | Pre-Test

The Gap:
- 2-4 sentences explaining what is missing or misconfigured.
- Why this matters for load test validity.

Impact if Not Addressed:
- What could go wrong during or after the load test.
- Examples: "False positive (test passes but prod fails)", "Inconclusive results", "Cannot diagnose failures"

Remediation:
- Concrete steps to address the gap.
- Include configuration examples, file changes, or tool recommendations.
- Provide time estimate for remediation.

Verification:
- How to confirm the gap has been addressed.
- Specific checklist item or validation step.
```

## Readiness Classification
- **BLOCKER**: Cannot run valid load test until addressed. Results would be meaningless or misleading.
- **WARNING**: Load test can proceed but results may be limited or require caveats.
- **RECOMMENDATION**: Best practice that improves test quality but not strictly required.

---

## Load Test Readiness Score Rubric (1-10)

Rate overall readiness to execute meaningful load tests:

- **9-10**: Fully prepared; can run load test today with confidence in results.
- **7-8**: Mostly ready; 1-2 gaps to address, test can proceed with documented caveats.
- **5-6**: Partially ready; significant gaps that may invalidate results.
- **3-4**: Not ready; multiple blockers that would produce misleading results.
- **<3**: Unprepared; fundamental infrastructure or tooling missing.

---

## Final Section: Load Test Readiness Summary (Mandatory)

### Readiness Score: X/10

### Justification (3-5 bullets)

### Blockers to Address Before Testing
1. [Highest priority blocker]
2. [Second priority]
3. [Third priority]

### Warnings to Document
1. [Caveat for test interpretation]
2. [Limitation of current setup]

### Recommended Test Execution Plan

**Phase 1: Smoke Test (1 hour)**
- Single user, all journeys, verify instrumentation

**Phase 2: Baseline (2 hours)**
- 10% load, establish performance baseline

**Phase 3: Ramp Test (3 hours)**
- Gradual increase to 100%, find saturation point

**Phase 4: Sustained Load (4 hours)**
- 80% target, 30-minute duration, verify stability

**Phase 5: Stress Test (2 hours)**
- 120% target, identify failure modes

### Estimated Preparation Time
- Blockers: X hours
- Warnings: Y hours
- Recommendations: Z hours (optional)

### Required Infrastructure
- Load generator: [Locust/k6/Artillery] on [specs]
- Monitoring: [Prometheus/Grafana/etc.] configured with dashboards
- Log aggregation: [ELK/Loki/etc.] with sufficient retention
- Test data: [X] documents of varying complexity
- Environment: [specs matching production or documented differences]

### Sample Locust Configuration for This Stack

```python
from locust import HttpUser, task, between
from locust_plugins.users.socketio import SocketIOUser

class DocumentProcessingUser(SocketIOUser):
    wait_time = between(1, 5)

    def on_start(self):
        # Establish WebSocket connection
        self.connect("ws://host/ws")

    @task(3)
    def view_stage(self):
        # GET stage data
        self.client.get("/api/stages/current")

    @task(1)
    def upload_document(self):
        # POST PDF upload
        with open("test_data/sample.pdf", "rb") as f:
            self.client.post("/api/upload", files={"file": f})

    @task(2)
    def edit_stage(self):
        # PUT stage modification
        self.client.put("/api/stages/5", json={"elements": [...]})
```

### Key Metrics to Monitor During Test
1. `http_request_duration_seconds` (p95, p99)
2. `websocket_message_latency_seconds`
3. `docling_stage_processing_seconds` (per stage)
4. `sqlite_query_duration_seconds`
5. `checkpoint_write_duration_seconds`
6. `process_resident_memory_bytes`
7. `python_gc_collections_total`
8. `uvicorn_active_connections`
