# Testing Strategy & Load Test Readiness Audit

**Priority**: P2 (Medium-High)
**Source**: Consolidated from #18 (Testing Strategy) + #11 (Load Test Readiness)
**Status**: Not Started

---

## Overview

This audit consolidates comprehensive testing strategy assessment and load test readiness evaluation for the Docling Interactive document processing pipeline. The system requires robust testing at all levels (unit, integration, E2E) and validation that it can handle production load scenarios.

**Scope**:
- Unit/Integration/E2E test coverage and quality
- Test reliability, architecture, and infrastructure
- Load test readiness: data preparation, environment parity, success criteria
- Performance baseline establishment and regression detection

---

## 1. Unit/Integration/E2E Testing Strategy

### 1.1 Test Coverage Assessment

#### [ ] ⚠️ AI-CODING RISK - Pipeline Stage Processor Unit Tests
- **Risk**: Pipeline stage processors developed with AI assistance may lack comprehensive unit tests
- **Check**: Verify each of the 15 pipeline stages has dedicated unit tests covering:
  - Input validation and edge cases
  - Transformation logic correctness
  - Error handling and recovery
  - Coordinate preservation across transformations
- **Stack-specific**: Docling integration points, checkpoint serialization, bbox calculations
- **Target**: >80% coverage for core business logic, >90% for pipeline stages

#### [ ] 🐍 PYTHON/FASTAPI - Pydantic Model Validation Testing
- **Risk**: Complex data validation logic in Pydantic models may be untested
- **Check**: Validate that all Pydantic models have tests for:
  - Valid data acceptance
  - Invalid data rejection with proper error messages
  - Custom validators and transformers
  - Serialization/deserialization round-trips
- **Stack-specific**: Pipeline stage data models, checkpoint format compatibility
- **Target**: 95% coverage for checkpoint handling and data models

#### [ ] 🐍 PYTHON/FASTAPI - API Endpoint Integration Tests
- **Risk**: Endpoints may work in isolation but fail in realistic scenarios
- **Check**: Verify integration tests using FastAPI TestClient for:
  - All document lifecycle endpoints (upload, stages, export)
  - WebSocket message handling end-to-end
  - File upload/download flows with real file objects
  - Database transaction isolation and rollback
  - Background task execution
- **Stack-specific**: Label Studio API integration, checkpoint save/load cycles, pipeline stage transitions
- **Target**: 85% coverage for API endpoints

#### [ ] ⚛️ REACT/TS - Critical Path E2E Tests
- **Risk**: Multi-step user workflows may break due to component integration issues
- **Check**: Verify Playwright tests cover complete user journeys:
  - Document upload → processing → export flow
  - Stage viewer interactions (all 15 stages)
  - Bbox editing with coordinate accuracy validation
  - Reading order editor drag-and-drop
  - Table cell matching assignment flows
  - Error states and recovery (corrupt PDF, processing failure)
- **Stack-specific**: BboxEditor, TableCellMatchingEditor, ReadingOrderEditor
- **Target**: All critical user workflows covered

#### [ ] ⚠️ AI-CODING RISK - Frontend/Backend Contract Tests
- **Risk**: TypeScript interfaces and Pydantic models may drift out of sync
- **Check**: Validate API contract consistency:
  - Pydantic models match TypeScript interfaces
  - WebSocket message schemas validated on both ends
  - Pipeline stage data format compatibility
  - No breaking changes without versioning
- **Stack-specific**: 15 stage data structures, checkpoint format
- **Suggested Fix**: Add contract validation tests or schema comparison

#### [ ] 🐍 PYTHON/FASTAPI - Missing Test Utilities
- **Risk**: Duplicated test setup code, brittle test data creation
- **Check**: Verify existence of test utility library:
  - Document fixture factory (sample PDFs with various characteristics)
  - Checkpoint builder (valid states for each of 15 stages)
  - Bbox assertion helpers (coordinate comparison with tolerance)
  - Mock Docling output generators
- **Suggested Fix**: Create `tests/fixtures/` with domain-specific helpers

---

### 1.2 Test Reliability & Anti-Patterns

#### [ ] ⚠️ AI-CODING RISK - Flaky Test Patterns
- **Risk**: AI-generated tests may include timing assumptions or race conditions
- **Check**: Scan for flaky patterns:
  - `time.sleep()` or `setTimeout()` instead of condition waits
  - Tests that fail intermittently in CI
  - Order-dependent tests (fixture state leakage)
  - Uncontrolled async timing in WebSocket tests
- **Stack-specific**: WebSocket connection timing, Playwright element waits, async pipeline processing
- **Suggested Fix**: Use `pytest-asyncio` properly, Playwright auto-wait, explicit conditions

#### [ ] 🐍 PYTHON/FASTAPI - Non-Deterministic Test Data
- **Risk**: Random data generation causes unpredictable test failures
- **Check**: Verify test determinism:
  - Random generators use fixed seeds
  - Time/date dependencies are mocked
  - File system ordering is explicit
  - Document processing order is controlled
- **Stack-specific**: Checkpoint timestamps, image rendering, document processing order
- **Suggested Fix**: Use `faker.seed()`, `freezegun` for time, explicit sorting

#### [ ] 🐍 PYTHON/FASTAPI - Resource Leaks in Tests
- **Risk**: Tests may leave resources open, causing failures in subsequent tests
- **Check**: Verify proper cleanup:
  - SQLite connections closed (use fixtures with teardown)
  - Temporary files removed (`tmp_path` fixture)
  - WebSocket connections closed
  - Image processing buffers released
- **Stack-specific**: Checkpoint files, PDF file handles, OpenCV/Pillow resources
- **Suggested Fix**: Use `pytest` fixtures with `yield` and cleanup code

#### [ ] ⚛️ REACT/TS - Playwright Selector Fragility
- **Risk**: Tests break with styling changes or component refactoring
- **Check**: Verify robust selector strategy:
  - Use `data-testid` attributes for critical elements
  - Prefer role-based queries (`getByRole`)
  - Avoid CSS class selectors or implementation details
  - Document elements have stable identifiers
- **Stack-specific**: Bbox editor elements, stage viewer controls, document list items
- **Suggested Fix**: Add `data-testid` to all interactive components

#### [ ] ⚛️ REACT/TS - Playwright Wait Strategy Issues
- **Risk**: Fixed timeouts cause flaky tests or slow test execution
- **Check**: Verify proper wait patterns:
  - Use Playwright auto-wait instead of `page.waitForTimeout()`
  - Explicit conditions for async state changes
  - Retry logic for eventually-consistent operations
- **Stack-specific**: Document processing status, stage transitions, WebSocket updates
- **Suggested Fix**: Use `page.waitForSelector()`, `page.waitForResponse()`, custom expect conditions

---

### 1.3 Test Architecture & Infrastructure

#### [ ] 🐍 PYTHON/FASTAPI - Over-Mocking vs Under-Mocking Balance
- **Risk**: Tests may mock too much (brittle) or too little (slow/flaky)
- **Check**: Verify appropriate mocking strategy:
  - External services mocked (Label Studio API, file system I/O)
  - Internal boundaries use real implementations
  - Integration tests use minimal mocking
  - Mock behavior matches real service responses
- **Stack-specific**: Docling internals should NOT be heavily mocked; Label Studio API should be
- **Suggested Fix**: Mock at service boundaries, use realistic response fixtures

#### [ ] 🐍 PYTHON/FASTAPI - Fixture Scope and Dependencies
- **Risk**: Incorrect fixture scope causes slow tests or state pollution
- **Check**: Verify fixture design:
  - `session` scope for expensive setup (Docling model loading)
  - `function` scope for test isolation (database state)
  - Async fixtures for async code (`@pytest_asyncio.fixture`)
  - No complex fixture dependency chains
- **Stack-specific**: Database fixtures, Docling model fixtures, checkpoint fixtures
- **Suggested Fix**: Review `conftest.py`, optimize scopes, use `tmp_path`

#### [ ] 🐍 PYTHON/FASTAPI - Database Test Isolation
- **Risk**: Tests share database state, causing order-dependent failures
- **Check**: Verify database test strategy:
  - Each test gets clean database state
  - Transactions rolled back after tests
  - SQLite WAL mode handled correctly
  - Concurrent access tested separately
- **Stack-specific**: Checkpoint metadata, document status records
- **Suggested Fix**: Use test database with transaction rollback or in-memory SQLite

#### [ ] 🐍 PYTHON/FASTAPI - Async Test Configuration
- **Risk**: Async tests may not be properly configured, causing event loop errors
- **Check**: Verify pytest-asyncio setup:
  - `pytest.ini` has `asyncio_mode = auto`
  - Async fixtures use `@pytest_asyncio.fixture`
  - All async functions properly awaited
  - Event loop cleanup between tests
- **Stack-specific**: Pipeline async processing, WebSocket handlers, background tasks
- **Suggested Fix**: Configure pytest-asyncio properly, add to `requirements.txt`

---

### 1.4 CI/CD Testing Integration

#### [ ] ⚠️ AI-CODING RISK - Test Execution in CI
- **Risk**: Tests may pass locally but fail in CI due to environment differences
- **Check**: Verify CI test configuration:
  - All test suites run in CI (unit, integration, E2E)
  - Test artifacts collected (screenshots, reports, coverage)
  - Environment parity with local development
  - Proper dependency installation
- **Stack-specific**: Playwright screenshots, pytest HTML reports, coverage XML
- **Suggested Fix**: Add GitHub Actions workflow with test jobs

#### [ ] 🐍 PYTHON/FASTAPI - Test Performance & Parallelization
- **Risk**: Slow test suite delays feedback and reduces developer productivity
- **Check**: Verify test performance optimization:
  - Unit tests complete in <5 minutes
  - Full suite (including E2E) in <15 minutes
  - Parallel test execution configured (`pytest-xdist`)
  - Slow tests marked and optionally skipped
- **Stack-specific**: Docling processing tests, Playwright tests, integration tests
- **Suggested Fix**: Use `pytest -n auto`, mark slow tests with `@pytest.mark.slow`

#### [ ] ⚠️ AI-CODING RISK - Coverage Thresholds & Quality Gates
- **Risk**: Coverage may regress without enforcement
- **Check**: Verify quality gates in CI:
  - Coverage threshold enforced (e.g., fail if <80%)
  - Type checking with MyPy in strict mode
  - Linting with Ruff/Black (no warnings allowed)
  - ESLint rules enforced for frontend
- **Suggested Fix**: Add `--cov-fail-under=80` to pytest, CI step for mypy/ruff

#### [ ] 🐍 PYTHON/FASTAPI - Flaky Test Detection & Tracking
- **Risk**: Flaky tests erode confidence in CI
- **Check**: Verify flaky test management:
  - Tests run multiple times to detect flakiness
  - Flaky tests tracked and prioritized for fixing
  - Quarantine mechanism for known flaky tests
- **Suggested Fix**: Use pytest-rerunfailures, track flaky rate <1%

---

### 1.5 Testing Best Practices & Guidelines

#### [ ] ⚠️ AI-CODING RISK - Hard Assertions Only
- **Risk**: Soft assertions that warn but don't fail hide real issues
- **Check**: Verify all tests use hard assertions:
  - `assert` statements that fail tests on violation
  - No `try/except` that swallows failures
  - No early `return` that silently passes
  - Clear failure messages for all assertions
- **Suggested Fix**: Review test code for assertion strength

#### [ ] 🐍 PYTHON/FASTAPI - Test Naming & Organization
- **Risk**: Poorly organized tests are hard to maintain and understand
- **Check**: Verify test structure:
  - Tests organized by module/feature
  - Clear naming convention (`test_<functionality>_<scenario>`)
  - AAA pattern (Arrange, Act, Assert) followed
  - Test docstrings for complex scenarios
- **Suggested Fix**: Create `tests/unit/`, `tests/integration/`, `tests/e2e/`

#### [ ] 🐍 PYTHON/FASTAPI - Test Markers for Selective Execution
- **Risk**: Cannot run subset of tests for faster feedback
- **Check**: Verify pytest markers configured:
  - `@pytest.mark.slow` for tests >5s
  - `@pytest.mark.integration` for tests requiring external services
  - `@pytest.mark.e2e` for end-to-end tests
  - `@pytest.mark.wip` for work-in-progress tests
- **Suggested Fix**: Add markers to `pytest.ini`, document in test README

---

## 2. Load Test Readiness

### 2.1 Test Data Preparation

#### [ ] ⚠️ AI-CODING RISK - Realistic Document Corpus
- **Risk**: Testing with trivial documents won't reveal real-world performance issues
- **Check**: Verify test document diversity:
  - Page counts: 1-page, 10-page, 50-page, 100+ page documents
  - Content types: text-heavy, image-heavy, tables, mixed layouts, formulas, code blocks
  - File sizes: 100KB, 1MB, 10MB, 50MB+
  - Quality: clean scans, noisy scans, rotated pages, multi-column layouts
- **Stack-specific**: Complex tables for TableFormer, LaTeX formulas, code blocks
- **Blocker if**: Only synthetic/single-page documents available
- **Remediation**: Collect or generate 50+ representative PDFs covering all document types

#### [ ] 🐍 PYTHON/FASTAPI - Data Volume & Cardinality
- **Risk**: Insufficient test data volume won't stress system limits
- **Check**: Verify data volume adequacy:
  - Minimum 50-100 unique documents for load tests
  - Pre-generated checkpoints for mid-pipeline testing (start at stage 8, not stage 1)
  - Sufficient volume to stress SQLite write contention
  - File system I/O capacity tested (hundreds of concurrent reads)
- **Stack-specific**: Thousands of checkpoint JSON files, concurrent PDF reads, image generation
- **Blocker if**: <50 unique documents or only same document reused
- **Remediation**: Generate checkpoint fixtures for all 15 stages, create 100+ document library

#### [ ] 🐍 PYTHON/FASTAPI - Test Data Isolation
- **Risk**: Load tests may pollute production/staging data
- **Check**: Verify test environment isolation:
  - Test-specific paths for `checkpoints/`, `uploads/`, SQLite DB
  - Cleanup scripts after test runs
  - No shared storage with production
  - Environment variables distinguish test from prod
- **Blocker if**: Tests use production paths or database
- **Remediation**: Create `test_` prefixed directories, add cleanup scripts, verify isolation

#### [ ] 🐍 PYTHON/FASTAPI - Seed Data & State Setup
- **Risk**: Cannot test resume/recovery scenarios without pre-populated state
- **Check**: Verify state setup capabilities:
  - Ability to pre-populate documents at various pipeline stages
  - Pre-existing Label Studio projects and annotations
  - Partially processed checkpoints for resume testing
  - Mix of new uploads and in-progress documents
- **Recommendation**: Create seed data scripts for realistic scenarios
- **Remediation**: Build test data generator for each pipeline stage (15 total)

---

### 2.2 User Journey Coverage

#### [ ] ⚠️ AI-CODING RISK - Critical Path Mapping
- **Risk**: Load tests may miss critical user flows
- **Check**: Verify all critical journeys are covered:

| Journey | Description | Endpoints/Flows | Covered? |
|---------|-------------|-----------------|----------|
| Upload Flow | PDF upload → validation → processing | POST /upload, WebSocket progress | [ ] |
| Stage Navigation | View/edit each of 15 pipeline stages | GET /stages/{id}, PUT /stages/{id} | [ ] |
| Real-time Updates | WebSocket progress during processing | ws://host/ws | [ ] |
| Export Flow | Generate final outputs (MD, JSON, HTML) | GET /export/{format} | [ ] |
| Concurrent Editing | Multiple users editing same document | PUT with optimistic locking | [ ] |
| Recovery Flow | Resume from checkpoint after failure | GET /checkpoints, POST /resume | [ ] |

- **Stack-specific**: TableCellMatchingEditor, ReadingOrderEditor, BboxEditor interactions
- **Blocker if**: Upload or Stage Navigation flows not covered
- **Remediation**: Create load test scripts for each journey (6 total)

#### [ ] 🐍 PYTHON/FASTAPI - User Behavior Modeling
- **Risk**: Unrealistic request patterns won't simulate real load
- **Check**: Verify realistic user simulation:
  - Think times between actions (1-5s, not instant)
  - Session simulation (cookies, WebSocket lifecycle)
  - Stateful interactions (edit-save-continue cycle)
  - Mixed user types (viewers, editors, uploaders)
- **Stack-specific**: Stage editor edit-save-continue pattern
- **Warning if**: All requests are stateless/independent
- **Remediation**: Add think times to Locust/k6 scripts, model session behavior

#### [ ] 🐍 PYTHON/FASTAPI - Error Path Coverage
- **Risk**: Only testing happy paths misses failure handling under load
- **Check**: Verify error scenarios included:
  - Invalid PDF uploads (corrupt, password-protected, non-PDF)
  - Mid-processing failures (Docling model errors, OOM)
  - WebSocket disconnection during processing
  - Concurrent edit conflicts
  - Network timeouts and retries
- **Warning if**: Only success scenarios tested
- **Remediation**: Add 10-15% error injection to load scripts

#### [ ] ⚠️ AI-CODING RISK - Mixed Workload Simulation
- **Risk**: Uniform load doesn't match real usage patterns
- **Check**: Verify workload distribution:
  - 60% passive viewers (GET requests, WebSocket listeners)
  - 30% active editors (stage modifications)
  - 10% heavy operations (uploads, full pipeline runs)
- **Recommendation**: Model realistic workload mix
- **Remediation**: Configure Locust task weights to match distribution

---

### 2.3 Ramp Strategy & Load Profiles

#### [ ] 🐍 PYTHON/FASTAPI - Ramp-Up Configuration
- **Risk**: Instant load spike misses warm-up issues
- **Check**: Verify gradual ramp-up:
  - 10% of target load per minute (recommended)
  - System warm-up time (JIT compilation, connection pools, caches)
  - Docling model loading on first request handled
- **Stack-specific**: Docling model cold-start latency can be significant
- **Warning if**: Instant start without warm-up
- **Remediation**: Configure 10-minute ramp-up in load test tool

#### [ ] 🐍 PYTHON/FASTAPI - Load Profile Variety
- **Risk**: Single load profile misses different failure modes
- **Check**: Verify multiple test profiles defined:

| Profile | Purpose | Configuration | Implemented? |
|---------|---------|---------------|--------------|
| Baseline | Establish normal performance | 10% target load, 5 min | [ ] |
| Ramp | Find saturation point | 0→100% over 10 min | [ ] |
| Sustained | Test stability | 80% target, 30 min | [ ] |
| Spike | Test elasticity | 50%→150%→50% rapid | [ ] |
| Soak | Find memory leaks | 50% target, 2+ hours | [ ] |

- **Stack-specific**: Checkpoint file accumulation in soak tests
- **Warning if**: Only single profile defined
- **Remediation**: Create 5 load profile configurations

#### [ ] 🐍 PYTHON/FASTAPI - Cooldown & Recovery Observation
- **Risk**: Abrupt test stop misses recovery issues
- **Check**: Verify cooldown period included:
  - Connection draining observed
  - Background task completion tracked
  - Memory release verified
  - Resource cleanup confirmed
- **Recommendation**: 5-10 minute cooldown after load
- **Remediation**: Add cooldown period to test scripts, monitor during

---

### 2.4 Pass/Fail Criteria & SLOs

#### [ ] ⚠️ AI-CODING RISK - Quantitative Success Criteria
- **Risk**: Subjective pass/fail leads to inconclusive results
- **Check**: Verify explicit, measurable thresholds defined:

| Metric | Target | Failure Threshold | Defined? |
|--------|--------|-------------------|----------|
| p50 API Latency | < 200ms | > 500ms | [ ] |
| p95 API Latency | < 1s | > 3s | [ ] |
| p99 API Latency | < 3s | > 10s | [ ] |
| Error Rate | < 0.5% | > 1% | [ ] |
| WebSocket Latency | < 50ms | > 200ms | [ ] |
| Upload Success Rate | > 99% | < 95% | [ ] |
| Pipeline Completion | > 95% | < 90% | [ ] |
| Memory Growth | Stable | > 50% increase | [ ] |
| Docling Processing (per page) | < 500ms | > 2s | [ ] |

- **Blocker if**: No quantitative criteria defined
- **Remediation**: Define all thresholds based on business requirements, document in test plan

#### [ ] 🐍 PYTHON/FASTAPI - Business SLO Alignment
- **Risk**: Arbitrary test criteria don't reflect real requirements
- **Check**: Verify criteria align with:
  - User expectations (acceptable wait times)
  - Contract/SLA commitments
  - Competitive benchmarks
  - Historical baseline data
- **Warning if**: Criteria copied from templates without validation
- **Remediation**: Review with stakeholders, validate against user research

#### [ ] 🐍 PYTHON/FASTAPI - Regression Detection Baseline
- **Risk**: Cannot detect performance regressions without baseline
- **Check**: Verify regression detection setup:
  - Historical baseline performance recorded
  - Acceptable variance defined (e.g., p95 latency ±20%)
  - Automated comparison to baseline
  - Trend tracking over time
- **Blocker if**: No baseline exists
- **Remediation**: Run single-user baseline test, document results, automate comparison

#### [ ] 🐍 PYTHON/FASTAPI - Resource Utilization Limits
- **Risk**: System may fail due to resource exhaustion before hitting throughput limits
- **Check**: Verify resource limits defined:
  - CPU utilization < 80% sustained
  - Memory < 85% of allocation
  - Disk I/O < 70% capacity
  - SQLite lock contention < 5% of requests
  - File descriptor usage < 80% limit
- **Recommendation**: Monitor resource utilization during tests
- **Remediation**: Define acceptable resource consumption, add monitoring

---

### 2.5 Environment Parity

#### [ ] ⚠️ AI-CODING RISK - Infrastructure Matching
- **Risk**: Test environment differences invalidate load test results
- **Check**: Verify production/test parity:

| Component | Production | Test | Parity Check | Match? |
|-----------|------------|------|--------------|--------|
| CPU cores | X | Y | Y >= 50% of X | [ ] |
| Memory | X GB | Y GB | Y >= 50% of X | [ ] |
| Disk IOPS | X | Y | Similar class | [ ] |
| Network | X Gbps | Y Gbps | Y >= X | [ ] |
| SQLite version | X | Y | X == Y | [ ] |
| Python version | 3.12 | ? | Exact match | [ ] |
| Docling version | X | ? | Exact match | [ ] |
| GPU (if used) | Model X | Model Y | Match or N/A | [ ] |

- **Blocker if**: <50% CPU/memory or different Python/Docling versions
- **Remediation**: Document all differences, scale test results accordingly or match environment

#### [ ] 🐍 PYTHON/FASTAPI - Configuration Parity
- **Risk**: Debug settings in test environment don't match production
- **Check**: Verify configuration matches:
  - Uvicorn worker count (production-like)
  - SQLite connection settings (WAL mode, timeout, pragmas)
  - File upload limits and timeouts
  - WebSocket connection limits
  - Docling model settings (batch sizes, timeouts, GPU usage)
  - Logging level (INFO, not DEBUG)
- **Blocker if**: Using development/debug configuration
- **Remediation**: Copy production config to test environment, verify with diff

#### [ ] 🐍 PYTHON/FASTAPI - External Dependency Simulation
- **Risk**: Real external services cause test interference or rate limiting
- **Check**: Verify external service handling:
  - Label Studio API properly mocked or isolated test instance
  - Cloud storage (if any) uses test buckets
  - Mock response times match production latency
  - No shared services between test and production
- **Warning if**: Tests depend on shared external services
- **Remediation**: Use mocked Label Studio with realistic response times, isolate all external dependencies

#### [ ] ⚛️ REACT/TS - Network Conditions Simulation
- **Risk**: Perfect local network doesn't match user experience
- **Check**: Verify network realism:
  - Latency injection (50-200ms for remote users)
  - Bandwidth limits (upload speed for large PDFs)
  - Packet loss simulation (1-2% for poor connections)
  - CDN simulation for frontend assets
- **Recommendation**: Add network throttling to test scenarios
- **Remediation**: Use load test tool's network throttling features

---

### 2.6 Instrumentation & Observability

#### [ ] 🐍 PYTHON/FASTAPI - Backend Metrics Collection
- **Risk**: Cannot diagnose performance issues without metrics
- **Check**: Verify comprehensive metrics captured:
  - Request latency (p50, p95, p99) per endpoint
  - Request rate and error rate
  - SQLite query time and lock contention
  - Checkpoint read/write latency
  - WebSocket message latency
  - Docling processing time per stage (15 stages)
  - Memory usage (heap, RSS)
  - CPU utilization per worker
  - File descriptor count
  - Active connection count
- **Blocker if**: Missing latency percentiles or error rate
- **Remediation**: Add Prometheus instrumentation or use built-in FastAPI middleware

#### [ ] ⚛️ REACT/TS - Frontend Metrics Collection
- **Risk**: Frontend performance issues invisible during backend load tests
- **Check**: Verify frontend metrics:
  - Time to First Byte (TTFB)
  - Largest Contentful Paint (LCP)
  - First Input Delay (FID)
  - JavaScript heap size
  - WebSocket reconnection count
  - Component render times
- **Recommendation**: Use Real User Monitoring (RUM) during load tests
- **Remediation**: Add performance monitoring SDK (e.g., web-vitals library)

#### [ ] 🐍 PYTHON/FASTAPI - Distributed Tracing Setup
- **Risk**: Cannot trace requests through multi-stage pipeline
- **Check**: Verify tracing configured:
  - Request correlation IDs propagated
  - Span coverage for DB queries, external calls, processing stages
  - All 15 pipeline stages have dedicated spans
  - Trace sampling rate appropriate for load (1-10%)
- **Recommendation**: Use OpenTelemetry or similar
- **Remediation**: Add tracing instrumentation to FastAPI app, configure exporter

#### [ ] 🐍 PYTHON/FASTAPI - Log Aggregation
- **Risk**: Logs lost or create I/O bottleneck during load test
- **Check**: Verify logging setup:
  - Structured logging (JSON format)
  - Request IDs included in all log entries
  - Logs aggregated to searchable store (ELK, Loki, etc.)
  - Log level set to INFO or WARN (not DEBUG)
  - Asynchronous logging to prevent blocking
- **Warning if**: DEBUG logging enabled or logs not aggregated
- **Remediation**: Configure structured logging, set level to INFO, use log aggregation

#### [ ] 🐍 PYTHON/FASTAPI - Real-time Dashboards
- **Risk**: Cannot observe test progress or diagnose issues during run
- **Check**: Verify dashboards prepared before test:
  - Live request rate and latency graphs
  - Error rate trends and breakdown
  - Resource utilization (CPU, memory, disk)
  - Queue depths (if applicable)
  - WebSocket connection count
  - Per-stage processing times
- **Blocker if**: Dashboards don't exist
- **Remediation**: Create Grafana dashboards or equivalent before load test

---

### 2.7 Load Test Tool Configuration

#### [ ] 🐍 PYTHON/FASTAPI - Load Generator Selection
- **Risk**: Wrong tool choice limits test capabilities
- **Check**: Verify tool matches requirements:

| Tool | Use Case | Stack Fit | Selected? |
|------|----------|-----------|-----------|
| Locust | Python-native, WebSocket support | Excellent | [ ] |
| k6 | JavaScript, good metrics | Good | [ ] |
| Artillery | YAML config, WebSocket | Good | [ ] |
| Gatling | JVM-based, enterprise | Medium | [ ] |

- **Required capabilities**:
  - WebSocket connection support
  - Binary file upload (PDFs)
  - Cookie/session state handling
  - Distributed load generation
- **Blocker if**: Tool cannot handle WebSockets or file uploads
- **Remediation**: Select Locust (recommended for Python stack) or k6

#### [ ] 🐍 PYTHON/FASTAPI - Load Test Script Quality
- **Risk**: Poor scripts produce unrealistic or invalid results
- **Check**: Verify script robustness:
  - Proper error handling (don't stop on first error)
  - Response validation (status codes, body structure)
  - Think time variation (not fixed delays)
  - Data parameterization (different PDFs per user)
  - Checkpoint creation validation (not just HTTP 200)
- **Warning if**: Hardcoded values or no response validation
- **Remediation**: Add response assertions, parameterize test data, vary timing

#### [ ] 🐍 PYTHON/FASTAPI - Load Generator Resource Limits
- **Risk**: Load generator itself becomes bottleneck
- **Check**: Verify generator capacity:
  - File descriptor limits raised (ulimit -n)
  - Network connection limits adequate
  - CPU sufficient for target WebSocket count
  - Multiple generators for distributed load (if >10K RPS)
- **Warning if**: Single machine generating >10K RPS or >1000 WebSocket connections
- **Remediation**: Use distributed Locust deployment or multiple k6 instances

---

### 2.8 Pre-Test Validation

#### [ ] 🐍 PYTHON/FASTAPI - Smoke Test Checklist
- **Risk**: Load test fails immediately due to basic issues
- **Check**: Complete smoke test before load test:
  - [ ] Single user can complete full document lifecycle
  - [ ] All 15 pipeline stages execute successfully
  - [ ] WebSocket connections establish and receive updates
  - [ ] Checkpoints are created and readable
  - [ ] Export generates valid output files
  - [ ] Metrics appear in monitoring dashboards
- **Blocker if**: Any smoke test item fails
- **Remediation**: Fix all issues before proceeding to load test

#### [ ] 🐍 PYTHON/FASTAPI - Baseline Establishment
- **Risk**: Cannot detect regressions without baseline
- **Check**: Complete baseline before load test:
  - [ ] Run single-user baseline to establish expected latencies
  - [ ] Document baseline metrics (p50, p95, p99 for all endpoints)
  - [ ] Verify zero errors under minimal load
  - [ ] Confirm resource utilization at idle and light load
  - [ ] Record checkpoint for comparison
- **Blocker if**: No baseline exists
- **Remediation**: Run 1-hour single-user test, document all metrics

#### [ ] 🐍 PYTHON/FASTAPI - Capacity Estimation
- **Risk**: Target load exceeds theoretical capacity
- **Check**: Verify capacity estimates:
  - Single-request latency × target throughput < available capacity
  - Memory per connection × target connections < available memory
  - Disk I/O per document × target processing rate < IOPS limit
  - SQLite write throughput adequate for checkpoint creation rate
- **Warning if**: Estimates suggest >80% capacity utilization
- **Remediation**: Adjust targets or scale infrastructure

---

## 3. Action Plan & Recommendations

### 3.1 Priority 0: Blockers (Must Fix Before Load Testing)

#### [ ] Establish baseline performance metrics
- **Effort**: 4-8 hours
- **Action**: Run single-user tests for all 15 pipeline stages, document p50/p95/p99 latencies

#### [ ] Create realistic document corpus
- **Effort**: 8-16 hours
- **Action**: Collect/generate 50-100 PDFs covering all complexity types (tables, formulas, code, images)

#### [ ] Define quantitative pass/fail criteria
- **Effort**: 2-4 hours
- **Action**: Document SLOs for all metrics in table format, get stakeholder approval

#### [ ] Verify environment parity
- **Effort**: 4-8 hours
- **Action**: Compare production vs test infrastructure, document differences, adjust or scale results

#### [ ] Configure metrics and dashboards
- **Effort**: 8-16 hours
- **Action**: Add Prometheus instrumentation, create Grafana dashboards for real-time monitoring

---

### 3.2 Priority 1: High-Impact Testing Improvements

#### [ ] Add unit tests for all 15 pipeline stages
- **Effort**: 20-40 hours
- **Target**: >90% coverage for pipeline processors
- **Action**: Create test suite with fixtures for each stage, cover edge cases

#### [ ] Implement API integration tests
- **Effort**: 16-24 hours
- **Target**: 85% coverage for endpoints
- **Action**: Use FastAPI TestClient, cover upload/stages/export flows, WebSocket handlers

#### [ ] Create E2E tests for critical paths
- **Effort**: 16-24 hours
- **Action**: Playwright tests for document upload→processing→export, all stage editors

#### [ ] Build test utility library
- **Effort**: 8-16 hours
- **Action**: Create document factory, checkpoint builder, bbox helpers, mock Docling outputs

#### [ ] Configure load test tool with realistic scenarios
- **Effort**: 8-16 hours
- **Action**: Implement 6 user journeys in Locust, add think times, error handling, validation

---

### 3.3 Priority 2: Quality & Reliability Improvements

#### [ ] Fix flaky test patterns
- **Effort**: 8-16 hours
- **Action**: Scan for sleep/setTimeout, add proper async waits, use fixtures for isolation

#### [ ] Add contract tests for API schemas
- **Effort**: 4-8 hours
- **Action**: Validate Pydantic models match TypeScript interfaces, WebSocket message schemas

#### [ ] Implement test markers and selective execution
- **Effort**: 2-4 hours
- **Action**: Add pytest markers (slow, integration, e2e), configure pytest.ini

#### [ ] Add visual regression tests
- **Effort**: 8-16 hours
- **Action**: Playwright screenshot comparison for bbox rendering, overlays, stage layouts

#### [ ] Create all 5 load profiles
- **Effort**: 4-8 hours
- **Action**: Configure baseline, ramp, sustained, spike, soak test scenarios

---

### 3.4 Test Infrastructure Setup

#### [ ] pytest Configuration
```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (>5s)
    integration: marks tests requiring database/external services
    e2e: marks end-to-end tests
    flaky: marks known flaky tests to fix
    wip: marks work in progress tests
addopts =
    -v
    --strict-markers
    --cov=backend
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
```

#### [ ] Playwright Configuration
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

#### [ ] Coverage Configuration
```ini
# .coveragerc
[run]
source = backend
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*

[report]
precision = 2
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

---

### 3.5 Recommended Test Commands

```bash
# Unit tests only (fast feedback)
pytest tests/unit -v --cov=backend --cov-report=term-missing

# Integration tests
pytest tests/integration -v --cov=backend --cov-append

# E2E tests
npx playwright test --project=chromium

# Full test suite with coverage
pytest --cov=backend --cov-report=html && npx playwright test

# Performance/benchmark tests
pytest tests/performance --benchmark-only

# Run only fast tests (skip slow)
pytest -m "not slow" -v

# Run only integration tests
pytest -m integration -v

# Parallel execution
pytest -n auto --cov=backend

# Type checking
mypy backend --strict

# Linting
ruff check backend
black --check backend
```

---

### 3.6 Load Test Execution Plan

**Phase 1: Smoke Test (1 hour)**
- Single user, all 6 critical journeys
- Verify instrumentation and metrics collection
- Confirm zero errors on happy paths

**Phase 2: Baseline (2 hours)**
- 10% of target load (5-10 concurrent users)
- Establish performance baseline for all endpoints
- Document p50/p95/p99 latencies

**Phase 3: Ramp Test (3 hours)**
- Gradual increase 0→100% over 10 minutes
- Find saturation point and bottlenecks
- Identify resource limits (CPU, memory, SQLite)

**Phase 4: Sustained Load (4 hours)**
- 80% of target load
- 30-minute duration
- Verify stability, no memory leaks, checkpoint accumulation

**Phase 5: Stress Test (2 hours)**
- 120% of target load
- Identify failure modes and recovery behavior
- Test error handling under extreme load

**Total estimated time**: 12 hours of active testing + preparation

---

### 3.7 Sample Locust Configuration

```python
# locustfile.py
from locust import HttpUser, task, between
import random

class DocumentProcessingUser(HttpUser):
    wait_time = between(1, 5)  # Think time between requests

    def on_start(self):
        """Setup WebSocket connection on user start"""
        # Establish WebSocket connection
        # self.ws = create_connection(f"ws://{self.host}/ws")
        pass

    @task(6)  # 60% of requests
    def view_stage(self):
        """Passive viewer: GET stage data"""
        stage_id = random.randint(1, 15)
        with self.client.get(
            f"/api/stages/{stage_id}",
            catch_response=True,
            name="/api/stages/[id]"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Stage view failed: {response.text}")

    @task(3)  # 30% of requests
    def edit_stage(self):
        """Active editor: PUT stage modification"""
        stage_id = random.randint(5, 10)
        payload = {
            "elements": [
                {"id": 1, "label": "text", "bbox": [0, 0, 100, 100]}
            ]
        }
        with self.client.put(
            f"/api/stages/{stage_id}",
            json=payload,
            catch_response=True,
            name="/api/stages/[id]"
        ) as response:
            if response.status_code not in [200, 202]:
                response.failure(f"Stage edit failed: {response.text}")

    @task(1)  # 10% of requests
    def upload_document(self):
        """Heavy operation: POST PDF upload"""
        pdf_path = f"test_data/sample_{random.randint(1, 50)}.pdf"
        try:
            with open(pdf_path, "rb") as f:
                with self.client.post(
                    "/api/upload",
                    files={"file": f},
                    catch_response=True,
                    name="/api/upload"
                ) as response:
                    if response.status_code != 201:
                        response.failure(f"Upload failed: {response.text}")
                    else:
                        # Validate checkpoint creation
                        data = response.json()
                        if "checkpoint_id" not in data:
                            response.failure("No checkpoint ID in response")
        except FileNotFoundError:
            pass  # Skip if test file missing
```

---

### 3.8 Key Metrics to Monitor

#### Backend Metrics (Prometheus format)
```
http_request_duration_seconds{endpoint="/api/stages/{id}",method="GET"}  # p50, p95, p99
http_requests_total{endpoint="/api/upload",status="2xx"}  # Success rate
websocket_message_latency_seconds  # Real-time update latency
docling_stage_processing_seconds{stage="1-15"}  # Per-stage processing time
sqlite_query_duration_seconds{operation="insert|select|update"}  # DB performance
checkpoint_write_duration_seconds  # Checkpoint save time
process_resident_memory_bytes  # Memory usage
python_gc_collections_total  # GC pressure
uvicorn_active_connections  # Connection count
```

#### Frontend Metrics (Web Vitals)
```
time_to_first_byte_ms  # Server response time
largest_contentful_paint_ms  # Page load performance
first_input_delay_ms  # Interactivity
cumulative_layout_shift  # Visual stability
websocket_reconnections_total  # Connection stability
```

---

### 3.9 Coverage Targets by Module

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| Pipeline stages (15 total) | ? | 90% | P0 |
| Checkpoint handling | ? | 95% | P0 |
| API endpoints | ? | 85% | P1 |
| WebSocket handlers | ? | 80% | P1 |
| Pydantic models | ? | 95% | P1 |
| Utility functions | ? | 90% | P2 |
| Frontend components | ? | 70% | P2 |
| E2E critical paths | ? | 100% | P1 |

---

## 4. Success Criteria

### Load Test Readiness Score: TBD/10

**Score when ready for load testing**:
- **9-10**: All blockers addressed, comprehensive instrumentation, realistic test data
- **7-8**: Minor gaps documented, can proceed with caveats
- **<7**: Not ready for load testing

### Test Suite Health Score: TBD/10

**Score when unit/integration/E2E tests complete**:
- **9-10**: Comprehensive coverage, fast & reliable, well-maintained
- **7-8**: Good coverage for critical paths, some gaps
- **<7**: Significant testing debt, production risk

### Final Checklist Before Production

- [ ] All P0 blockers resolved
- [ ] Unit test coverage >80% overall, >90% for pipeline stages
- [ ] Integration test coverage >85% for API endpoints
- [ ] E2E tests cover all 6 critical user journeys
- [ ] Load test baseline established and documented
- [ ] All 5 load profiles executed successfully
- [ ] Performance meets SLO targets (p95 <3s, error rate <1%)
- [ ] No memory leaks in 2-hour soak test
- [ ] Flaky test rate <1%
- [ ] CI/CD pipeline includes all test suites
- [ ] Monitoring dashboards operational
- [ ] Incident response plan documented

---

**Notes**:
- Estimated total effort for comprehensive testing: 80-160 hours
- Recommended to tackle in sprints: P0 blockers → P1 improvements → P2 quality
- Load testing should occur after unit/integration tests reach 80%+ coverage
- Regular regression testing required after initial setup

