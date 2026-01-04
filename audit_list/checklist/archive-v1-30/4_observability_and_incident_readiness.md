# Observability & Incident Readiness Audit Prompt (Production-Ready)

## Role
Act as a Senior Site Reliability Engineer (SRE) and Observability Architect. Perform a comprehensive Observability & Incident Readiness Audit on the provided codebase to ensure production visibility, debuggability, and rapid incident response capability.

## Primary Goal
Identify gaps in logging, metrics, tracing, health checks, and alerting that would prevent effective incident detection, diagnosis, and resolution. Provide concrete implementations that make the system production-observable.

## Context
- This code was developed with a focus on speed ("vibecoded") and likely lacks comprehensive observability.
- I need you to find visibility gaps, missing instrumentation, and incident response weaknesses before production deployment.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn
- Document Processing: Docling engine
- Data Validation: Pydantic v2
- Database: SQLite3
- Image Processing: OpenCV, Pillow, pdf2image
- External Integration: Label Studio SDK
- Real-time: WebSockets
- Frontend: React 19 + TypeScript 5.9 + Vite 7
- State Management: Zustand
- Infrastructure: Docker (Python 3.11-slim-bookworm)

## Observability Goals
- Mean Time to Detect (MTTD): < 2 minutes for critical issues
- Mean Time to Diagnose (MTTD): < 10 minutes with available telemetry
- Request traceability: End-to-end correlation from frontend to backend
- Pipeline visibility: Stage-by-stage progress and failure tracking

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (logging config, metrics endpoints, health checks, deployment model), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - Current logging approach (stdlib logging, loguru, structlog, print statements)
   - Log format (structured JSON vs unstructured text)
   - Metrics collection (Prometheus, StatsD, custom, none)
   - Tracing implementation (OpenTelemetry, Jaeger, none)
   - Health check endpoints (FastAPI /health, custom, none)
   - Error tracking (Sentry, Rollbar, custom, none)
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) Structured Logging Audit

### A) Log Format & Structure
- Find print() statements, unstructured logging, inconsistent log formats.
- Look for missing context: request IDs, user IDs, document IDs, stage names.
- Flag logs that would be impossible to parse or aggregate.
- Suggested Fix: Structured JSON logging with consistent fields (timestamp, level, message, context).

### B) Log Levels & Verbosity
- Find DEBUG logs in hot paths that would flood production.
- Look for ERROR/WARNING misuse (errors logged as warnings, vice versa).
- Flag missing log level configuration per environment.
- Suggested Fix: Environment-based log level config, appropriate level usage.

### C) Request/Correlation ID Propagation
- Find requests without correlation IDs.
- Look for broken ID propagation across async boundaries, WebSocket connections.
- Flag missing correlation in background tasks, pipeline stages.
- Suggested Fix: Middleware for ID generation, context propagation, consistent inclusion.

### D) Sensitive Data in Logs
- Find PII, credentials, tokens, file contents in log statements.
- Look for full exception traces exposing internal paths.
- Flag document content or OCR text being logged.
- Suggested Fix: Log redaction, structured field policies, sensitive data filters.

### E) Log Rotation & Retention
- Find unbounded log files, missing rotation config.
- Look for logs written to container filesystem without volume.
- Flag missing log aggregation/shipping configuration.
- Suggested Fix: Rotation config, log shipping to aggregator (ELK, Loki, CloudWatch).

---

## 2) Metrics & Golden Signals Audit

### A) Four Golden Signals Coverage
- **Latency**: Find missing request duration metrics per endpoint.
- **Traffic**: Find missing request count/rate metrics.
- **Errors**: Find missing error rate metrics by type/endpoint.
- **Saturation**: Find missing resource utilization metrics (CPU, memory, connections).
- Suggested Fix: Prometheus histogram/counter for each signal.

### B) Pipeline Stage Metrics
- Find missing stage duration metrics for each of 15 pipeline stages.
- Look for missing stage success/failure counters.
- Flag missing queue depth metrics for processing backlog.
- Suggested Fix: Stage-level histograms and counters.

### C) Database Metrics
- Find missing SQLite query duration metrics.
- Look for missing connection pool metrics (if applicable).
- Flag missing checkpoint read/write metrics.
- Suggested Fix: Query timing instrumentation, checkpoint operation metrics.

### D) WebSocket Metrics
- Find missing connection count metrics.
- Look for missing message rate metrics (sent/received).
- Flag missing connection duration, error rate metrics.
- Suggested Fix: WebSocket-specific gauges and counters.

### E) External Dependency Metrics
- Find missing Label Studio API call metrics (latency, errors).
- Look for missing Docling model load/inference metrics.
- Flag missing image processing metrics (OpenCV/Pillow operations).
- Suggested Fix: Dependency-specific timing and error metrics.

### F) Frontend Metrics
- Find missing Core Web Vitals collection.
- Look for missing error rate tracking in React.
- Flag missing user timing metrics for key interactions.
- Suggested Fix: RUM collection, error boundary metrics, performance API usage.

---

## 3) Distributed Tracing Audit

### A) Trace Context Propagation
- Find missing trace context in HTTP requests.
- Look for broken context across WebSocket messages.
- Flag missing context in background/async operations.
- Suggested Fix: OpenTelemetry auto-instrumentation, manual context propagation.

### B) Span Coverage
- Find untraced database operations.
- Look for untraced external API calls (Label Studio).
- Flag untraced pipeline stage transitions.
- Suggested Fix: Span creation for all significant operations.

### C) Span Attributes
- Find spans missing critical attributes (document_id, stage_name, page_number).
- Look for generic span names that don't identify the operation.
- Flag missing error details in span status.
- Suggested Fix: Rich span attributes, descriptive naming, error recording.

### D) Trace Sampling
- Find missing sampling configuration.
- Look for all-or-nothing sampling (no tail-based sampling).
- Flag missing high-value trace preservation (errors, slow requests).
- Suggested Fix: Head-based + tail-based sampling strategy.

---

## 4) Health Checks & Readiness Audit

### A) Liveness Probe
- Find missing /health or /livez endpoint.
- Look for liveness checks that do too much (should be minimal).
- Flag checks that could false-positive during transient issues.
- Suggested Fix: Simple liveness endpoint that confirms process is running.

### B) Readiness Probe
- Find missing /ready or /readyz endpoint.
- Look for readiness checks that don't verify dependencies.
- Flag missing checks for: SQLite connectivity, Docling model loaded, Label Studio reachable.
- Suggested Fix: Comprehensive readiness that checks all critical dependencies.

### C) Startup Probe
- Find missing startup health check.
- Look for long model loading without startup indication.
- Flag race conditions where traffic arrives before ready.
- Suggested Fix: Startup probe with appropriate timeout for model loading.

### D) Dependency Health Checks
- Find missing Label Studio connectivity check.
- Look for missing checkpoint directory write check.
- Flag missing image processing library validation.
- Suggested Fix: Per-dependency health status in readiness response.

---

## 5) Alerting Readiness Audit

### A) Alert Definitions
- Find missing alert rules for critical conditions.
- Look for alert thresholds that are undefined or arbitrary.
- Flag missing alerts for: high error rate, high latency, service down.
- Suggested Fix: Prometheus alerting rules or equivalent for key conditions.

### B) Alert Actionability
- Find alerts that don't include diagnostic context.
- Look for alerts without runbook links.
- Flag alerts that would wake someone up but provide no next steps.
- Suggested Fix: Alert annotations with context, links, severity.

### C) Alert Fatigue Prevention
- Find alerts that would fire frequently under normal conditions.
- Look for missing alert grouping/deduplication.
- Flag missing alert silencing for maintenance windows.
- Suggested Fix: Proper thresholds, grouping, inhibition rules.

### D) Pipeline-Specific Alerts
- Find missing alerts for: stage failures, document stuck in processing, checkpoint corruption.
- Look for missing alerts for Label Studio sync failures.
- Flag missing alerts for WebSocket connection storms.
- Suggested Fix: Domain-specific alert rules for document processing.

---

## 6) Incident Response Readiness Audit

### A) Runbook Availability
- Find missing operational runbooks for common issues.
- Look for undocumented failure modes.
- Flag missing recovery procedures for: stuck documents, corrupt checkpoints, Label Studio down.
- Suggested Fix: Runbook for each alertable condition.

### B) Debug Endpoints
- Find missing admin/debug endpoints for inspection.
- Look for missing ability to query system state.
- Flag missing endpoints for: active documents, stage progress, connection status.
- Suggested Fix: Admin endpoints for operational visibility.

### C) Log Query Patterns
- Find missing documentation for common log queries.
- Look for logs that don't support efficient filtering.
- Flag missing examples for tracing request flow.
- Suggested Fix: Documented log query patterns for common investigations.

### D) Incident Metadata
- Find missing build version/commit SHA exposure.
- Look for missing deployment timestamp tracking.
- Flag missing configuration dump endpoint.
- Suggested Fix: /version and /config endpoints for incident context.

---

## 7) Frontend Observability Audit

### A) Error Tracking
- Find missing global error handler.
- Look for swallowed errors in catch blocks.
- Flag missing error reporting to backend/service.
- Suggested Fix: Error boundary with reporting, global error handler.

### B) Performance Monitoring
- Find missing performance timing for key user flows.
- Look for missing slow render detection.
- Flag missing network request timing.
- Suggested Fix: Performance marks/measures, React profiler integration.

### C) User Session Context
- Find missing session ID for correlating frontend/backend.
- Look for missing user action tracking for reproduction.
- Flag missing breadcrumb trail for error context.
- Suggested Fix: Session correlation, action logging, breadcrumbs.

### D) WebSocket Observability
- Find missing connection state logging.
- Look for missing reconnection attempt tracking.
- Flag missing message delivery confirmation.
- Suggested Fix: WebSocket lifecycle logging, reconnection metrics.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s)
Risk Category: Logging | Metrics | Tracing | Health | Alerting | Incident Response | Frontend

The Problem:
- 2-4 sentences explaining why this gap impacts incident detection/resolution.
- Be specific about the impact: delayed detection, impossible diagnosis, unclear root cause, extended MTTR.

Observability Impact:
- Provide realistic impact estimate (example: "Cannot trace request across pipeline stages", "No visibility into document processing latency", "Alert fatigue from false positives").
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (simulate failure and attempt diagnosis, check log aggregator, review metrics dashboard).

The Fix:
- Provide the implementation code snippet.
- Show before/after if useful.
- If fix requires config/infrastructure, show the config and where it belongs.

Trade-off Consideration:
- Note complexity, cost, and any risks (e.g., "Adds OpenTelemetry dependency but enables end-to-end tracing").
- If acceptable at small scale, mark as MONITOR with what threshold triggers implementation.
```

## Severity Classification
- **CRITICAL**: Complete blind spot for production issues (no error logging, no health checks, no key metrics).
- **HIGH**: Significant gap that extends incident detection or resolution time.
- **MEDIUM**: Missing observability that complicates debugging but doesn't prevent it.
- **MONITOR**: Nice-to-have observability; implement when scaling.

---

## Observability Maturity Score Rubric (1-10)

Rate overall observability maturity:
- **9-10**: Production-ready; comprehensive logging, metrics, tracing, health checks, and alerting.
- **7-8**: Good foundation; 1-2 gaps in coverage that need addressing.
- **5-6**: Basic observability; can detect issues but slow to diagnose.
- **3-4**: Minimal observability; relies on user reports to find issues.
- **<3**: Flying blind; no systematic observability.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest impact on MTTD/MTTR first)

## Final Section: Summary & Action Plan (Mandatory)
1) Implement Now (before production)
2) Implement Soon (first iteration)
3) Monitor (add when scaling)

## Also include:
- Estimated time to implement all "Implement Now" items (range is fine)
- Recommended observability stack:
  - Logging: structlog/loguru -> JSON -> Loki/ELK/CloudWatch
  - Metrics: Prometheus + Grafana
  - Tracing: OpenTelemetry -> Jaeger/Tempo
  - Alerting: Prometheus Alertmanager / PagerDuty integration
  - Frontend: Sentry / custom error reporting
- Minimum viable dashboards:
  - Request latency/error rate (RED metrics)
  - Pipeline stage progress and failures
  - WebSocket connection health
  - System resources (CPU, memory, disk)
- Sample alerting rules for:
  - Error rate > 5% for 5 minutes
  - p95 latency > 2s for 5 minutes
  - Pipeline stage failure rate > 1%
  - Health check failures
  - WebSocket connection count spike/drop
