# Testing Strategy Audit Prompt (Production-Ready, Regression-Proof)

## Role
Act as a Senior QA Architect and Test Engineering Lead. Perform a comprehensive Testing Strategy Audit on the provided codebase to ensure robust test coverage, reliable test infrastructure, and effective regression prevention.

## Primary Goal
Identify gaps in test coverage, flaky test patterns, missing test types, and testing anti-patterns that will lead to production regressions. Provide concrete improvements that make the test suite reliable and maintainable.

## Context
- This code was developed with AI assistance ("vibecoded") and may have inconsistent or superficial test coverage.
- I need you to find testing gaps, flaky patterns, and coverage holes before production deployment.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn
- Document Processing: Docling engine
- Data Validation: Pydantic v2
- Database: SQLite3
- Image Processing: OpenCV, Pillow, pdf2image
- External Integration: Label Studio SDK
- Real-time: WebSockets
- Frontend: React 19 + TypeScript 5.9
- Build: Vite 7
- State: Zustand
- Routing: React Router DOM 7
- E2E Testing: Playwright
- Backend Testing: pytest
- Linting: ESLint, Ruff, Black, MyPy

## Testing Targets
- Unit test coverage: >80% for core business logic
- Integration test coverage: Critical paths covered
- E2E test coverage: All user workflows
- Test execution time: <5 minutes for unit tests, <15 minutes for full suite
- Flaky test rate: <1%
- Test reliability: 100% deterministic on CI

## How to Provide Code
I will paste/upload the codebase files below. Analyze all test files, fixtures, configurations, and the code they test systematically.
If any critical context is missing (CI config, test database setup, fixture files), infer what you can from the code and explicitly list assumptions.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - Test framework configuration (pytest.ini, conftest.py, playwright.config.ts)
   - Test directory structure and naming conventions
   - Fixture patterns and shared test utilities
   - Mock/stub strategies for external dependencies
   - CI/CD test execution setup
   - Test database/state management approach
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation.

---

## 1) Test Coverage Gaps

### A) Missing Unit Tests for Core Logic
- Pipeline stage processors without unit tests
- Pydantic model validation logic untested
- Utility functions and helpers without coverage
- Edge cases for coordinate transformations
- **Stack-specific**: Docling integration points, checkpoint serialization, bbox calculations
- Suggested Fix: Add focused unit tests with clear arrange-act-assert structure.

### B) Missing Integration Tests
- API endpoints without request/response tests
- Database operations without transaction tests
- WebSocket message handling untested
- File upload/download flows missing tests
- **Stack-specific**: Label Studio API integration, checkpoint save/load cycles, pipeline stage transitions
- Suggested Fix: Add integration tests using TestClient (FastAPI) and real fixtures.

### C) Missing E2E Tests for Critical Paths
- User workflows without Playwright coverage
- Multi-step operations not tested end-to-end
- Error states and recovery flows untested
- **Stack-specific**: Document upload → processing → export flow, stage viewer interactions, bbox editing
- Suggested Fix: Add Playwright tests for complete user journeys.

### D) Missing Contract Tests
- Frontend/backend API contract not validated
- WebSocket message schema drift possible
- Pydantic models not validated against TypeScript interfaces
- **Stack-specific**: Pipeline stage data models, checkpoint format compatibility
- Suggested Fix: Add contract tests or schema validation tests.

---

## 2) Test Reliability Issues

### A) Flaky Test Patterns
- Tests depending on timing (sleep, setTimeout)
- Race conditions in async test code
- Order-dependent tests that fail in isolation
- Tests depending on external state
- **Stack-specific**: WebSocket connection timing, Playwright element waits, async pipeline processing
- Suggested Fix: Use proper async patterns, explicit waits, test isolation.

### B) Non-Deterministic Tests
- Random data generation without seeds
- Tests depending on current time/date
- File system order assumptions
- **Stack-specific**: Document processing order, checkpoint timestamps, image rendering
- Suggested Fix: Use fixed seeds, mock time, explicit ordering.

### C) Environment-Dependent Tests
- Tests that pass locally but fail in CI
- Hardcoded paths or system-specific assumptions
- Missing test environment setup
- **Stack-specific**: DPI settings, font availability, system library versions (OpenCV, Pillow)
- Suggested Fix: Use environment abstraction, Docker-based CI, explicit dependencies.

### D) Resource Leaks in Tests
- Database connections not cleaned up
- Temporary files not removed
- WebSocket connections left open
- **Stack-specific**: SQLite connections, checkpoint files, image processing buffers
- Suggested Fix: Use fixtures with proper teardown, context managers.

---

## 3) Test Architecture Problems

### A) Over-Mocking
- Mocking implementation details instead of interfaces
- Mocks that don't reflect real behavior
- Tests that pass with broken production code
- **Stack-specific**: Mocking Docling internals, SQLite behavior, image processing results
- Suggested Fix: Mock at boundaries, use realistic stubs, integration tests for critical paths.

### B) Under-Mocking
- Tests hitting real external services
- Slow tests due to real I/O
- Tests that fail due to network issues
- **Stack-specific**: Label Studio API calls, file system operations, image loading
- Suggested Fix: Mock external dependencies, use in-memory alternatives where appropriate.

### C) Test Duplication
- Same logic tested multiple times
- Copy-pasted test code without abstraction
- Missing shared fixtures and helpers
- **Stack-specific**: Repeated checkpoint creation, bbox test data, page fixtures
- Suggested Fix: Extract shared fixtures, use parameterized tests.

### D) Missing Test Utilities
- No factories for test data generation
- No builders for complex object setup
- No custom assertions for domain objects
- **Stack-specific**: Document fixture factory, checkpoint builder, bbox assertion helpers
- Suggested Fix: Create test utility library with domain-specific helpers.

---

## 4) Backend Testing (pytest)

### A) Fixture Issues
- Fixtures with wrong scope (function vs session)
- Missing async fixture support
- Fixture dependency chains too complex
- **Stack-specific**: Database fixtures, Docling model fixtures, checkpoint fixtures
- Suggested Fix: Use appropriate scopes, async fixtures, simplify dependencies.

### B) FastAPI Testing Gaps
- Missing TestClient usage
- Async endpoint testing issues
- Dependency injection not properly overridden
- **Stack-specific**: WebSocket testing, file upload testing, background task testing
- Suggested Fix: Use FastAPI TestClient, proper dependency overrides.

### C) Database Testing Issues
- Tests sharing database state
- Missing transaction rollback
- SQLite-specific behavior not handled
- **Stack-specific**: Checkpoint metadata, document status, concurrent access
- Suggested Fix: Use test database isolation, transaction rollback, WAL mode testing.

### D) Async Testing Problems
- Missing pytest-asyncio configuration
- Async tests not properly awaited
- Event loop issues in tests
- **Stack-specific**: Pipeline async processing, WebSocket handlers, background tasks
- Suggested Fix: Configure pytest-asyncio properly, use async fixtures.

---

## 5) Frontend Testing (Playwright)

### A) Selector Fragility
- Tests using implementation-detail selectors
- Selectors that break with styling changes
- Missing data-testid attributes
- **Stack-specific**: Bbox editor elements, stage viewer controls, document list items
- Suggested Fix: Use semantic selectors, add data-testid, role-based queries.

### B) Wait Strategy Issues
- Using fixed timeouts instead of conditions
- Missing proper element state waits
- Race conditions with async updates
- **Stack-specific**: Document processing status, stage transitions, WebSocket updates
- Suggested Fix: Use Playwright auto-wait, explicit conditions, retry patterns.

### C) Test Isolation Problems
- Tests depending on previous test state
- Shared authentication state issues
- Browser state leakage between tests
- **Stack-specific**: Document state, checkpoint state, stage progress
- Suggested Fix: Proper test isolation, fresh state per test, cleanup hooks.

### D) Visual Regression Gaps
- No screenshot comparison for UI components
- Missing responsive design testing
- Component style changes undetected
- **Stack-specific**: Bbox rendering, page overlays, stage viewer layouts
- Suggested Fix: Add visual regression tests, component screenshots.

---

## 6) Mocking & Stubbing Strategy

### A) Docling Mocking
- Missing Docling engine mocks for unit tests
- Real Docling processing in unit tests (too slow)
- Incomplete mock of Docling output structures
- Suggested Fix: Create comprehensive Docling mock fixtures with realistic outputs.

### B) Label Studio Mocking
- API calls not mocked in tests
- Missing error scenario mocks
- Integration tests hitting real Label Studio
- Suggested Fix: Mock Label Studio SDK, use recorded responses.

### C) File System Mocking
- Real file operations in unit tests
- Temporary files not cleaned up
- Path-dependent test failures
- **Stack-specific**: PDF files, checkpoint files, image files
- Suggested Fix: Use tmp_path fixture, in-memory alternatives, proper cleanup.

### D) WebSocket Mocking
- WebSocket connections not properly mocked
- Missing message sequence testing
- Reconnection logic untested
- Suggested Fix: Use WebSocket test utilities, mock connection lifecycle.

---

## 7) CI/CD Testing Integration

### A) Test Execution Issues
- Tests not running in CI
- Different behavior in CI vs local
- Missing test artifacts collection
- **Stack-specific**: Playwright screenshots, pytest reports, coverage reports
- Suggested Fix: Proper CI configuration, artifact collection, environment parity.

### B) Test Performance
- Test suite too slow for CI
- Missing parallel test execution
- No test sharding for large suites
- **Stack-specific**: Docling processing tests, Playwright tests, integration tests
- Suggested Fix: Parallelize tests, use markers for slow tests, shard in CI.

### C) Missing Quality Gates
- No coverage thresholds enforced
- No type checking in CI
- No linting enforcement
- **Stack-specific**: MyPy strict mode, Ruff/Black formatting, ESLint rules
- Suggested Fix: Add coverage gates, type checking, linting as CI steps.

### D) Test Reporting Gaps
- No test result tracking over time
- Missing flaky test detection
- No coverage trend analysis
- Suggested Fix: Add test reporting, flaky test tracking, coverage badges.

---

## 8) Load & Performance Testing

### A) Missing Load Tests
- No load testing setup
- Performance regressions undetected
- Scalability issues discovered in production
- **Stack-specific**: Concurrent document processing, WebSocket connections, API throughput
- Suggested Fix: Add load test suite using locust or k6.

### B) Missing Benchmark Tests
- No performance baseline
- Algorithm performance not tracked
- Memory usage not monitored
- **Stack-specific**: Checkpoint save/load times, image processing speed, pipeline stage timing
- Suggested Fix: Add benchmark tests with pytest-benchmark.

### C) Missing Stress Tests
- System limits not tested
- Resource exhaustion scenarios missing
- Recovery behavior untested
- **Stack-specific**: Large PDF processing, many concurrent uploads, SQLite write contention
- Suggested Fix: Add stress test scenarios with resource monitoring.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | LOW]

Location: FileName : Line Number(s) (or "Missing" if test doesn't exist)
Risk Category: Coverage | Reliability | Architecture | Backend | Frontend | Mocking | CI/CD | Performance

The Problem:
- 2-4 sentences explaining why this testing gap leads to production risk.
- Be specific about failure mode: undetected regression, flaky CI, slow feedback, production bug.

Impact Assessment:
- Provide realistic estimate of risk (e.g., "50% of regressions in this module will reach production", "CI fails 10% of runs due to flakiness")
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (run test isolation, check coverage report, measure flaky rate, review CI logs).

The Fix:
- Provide the test code or configuration to add.
- Show example test case if applicable.
- If fix requires info/config, show the config change and where it belongs.

Effort Estimate:
- Time to implement: Quick (<1hr) | Medium (1-4hr) | Large (>4hr)
- Dependencies: None | Requires fixture setup | Requires infrastructure
```

## Severity Classification
- **CRITICAL**: Core functionality untested, will ship bugs to production.
- **HIGH**: Significant coverage gaps or reliability issues causing CI problems.
- **MEDIUM**: Missing test types or suboptimal patterns reducing confidence.
- **LOW**: Nice-to-have improvements, polish, or minor gaps.

---

## Test Suite Health Score Rubric (1-10)

Rate overall test suite health based on coverage, reliability, and maintainability:
- **9-10**: Comprehensive coverage, fast & reliable, well-maintained. Ship with confidence.
- **7-8**: Good coverage for critical paths, some gaps. Minor reliability issues.
- **5-6**: Significant gaps in coverage or reliability. Regressions likely.
- **3-4**: Major testing debt. Production bugs frequent. CI unreliable.
- **<3**: Minimal testing. No confidence in changes. Do not ship.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 5 testing improvements list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)

### 1) Fix Now (before production)
- Critical coverage gaps
- Flaky tests blocking CI
- Missing integration tests for core flows

### 2) Fix Soon (next sprint)
- Medium priority coverage improvements
- Test architecture improvements
- Performance testing setup

### 3) Continuous Improvement (ongoing)
- Coverage threshold increases
- Flaky test reduction
- Test execution optimization

## Also include:

### Test Infrastructure Recommendations:
- pytest configuration (pytest.ini, conftest.py)
- Playwright configuration (playwright.config.ts)
- Coverage configuration (.coveragerc)
- CI test job configuration

### Fixtures to Create:
- Document fixtures (sample PDFs, expected outputs)
- Checkpoint fixtures (valid states for each stage)
- Mock fixtures (Docling, Label Studio, file system)
- Database fixtures (clean state, populated state)

### Test Commands to Add:
```bash
# Unit tests only (fast feedback)
pytest tests/unit -v --cov=backend --cov-report=term-missing

# Integration tests
pytest tests/integration -v --cov=backend

# E2E tests
npx playwright test --project=chromium

# Full suite with coverage
pytest --cov=backend --cov-report=html && npx playwright test

# Performance tests
pytest tests/performance --benchmark-only
```

### Recommended Test Markers:
```python
# pytest markers for selective execution
@pytest.mark.slow  # Tests taking >5s
@pytest.mark.integration  # Requires database/external services
@pytest.mark.e2e  # End-to-end tests
@pytest.mark.flaky  # Known flaky tests to fix
@pytest.mark.wip  # Work in progress tests
```

### Coverage Targets by Module:
| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| Pipeline stages | ? | 90% | P0 |
| Checkpoint handling | ? | 95% | P0 |
| API endpoints | ? | 85% | P1 |
| WebSocket handlers | ? | 80% | P1 |
| Utility functions | ? | 90% | P2 |
| Frontend components | ? | 70% | P2 |
