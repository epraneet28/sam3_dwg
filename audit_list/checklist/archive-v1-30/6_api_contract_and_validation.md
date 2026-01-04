# API Contract & Validation Audit Prompt (Production-Ready)

## Role
Act as a Senior API Architect and Backend Engineer. Perform a comprehensive API Contract & Validation Audit on the provided codebase to ensure robust, consistent, and well-documented API interfaces.

## Primary Goal
Identify where AI-generated API code lacks proper validation, has inconsistent contracts, or missing documentation, and provide concrete fixes that make the API production-ready and maintainable.

## Context
- This code was developed with a focus on speed ("vibecoded") and may have inconsistent API patterns.
- I need you to find validation gaps, contract inconsistencies, and documentation issues before production deployment.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn
- Validation: Pydantic v2
- Database: SQLite3
- Real-time: WebSockets
- External: Label Studio SDK integration
- Frontend: React 19 + TypeScript 5.9
- State: Zustand
- Testing: Playwright (E2E), pytest (backend)

## Audit Targets
- All FastAPI route handlers and their request/response models
- Pydantic model definitions and validation rules
- WebSocket message schemas and handlers
- Error response formats and HTTP status codes
- OpenAPI/Swagger documentation completeness
- Frontend TypeScript types and API client code

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (route structure, middleware, error handlers), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - API versioning strategy (path-based, header-based, none)
   - Authentication/authorization middleware
   - Error handling middleware and patterns
   - Request/response logging approach
   - API documentation generation (FastAPI auto-docs)
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) Request Validation Gaps

### A) Missing or Incomplete Pydantic Models
- Endpoints accepting `dict` or `Any` instead of typed Pydantic models.
- Models with overly permissive types (`str` where `EmailStr`, `HttpUrl`, etc. apply).
- Missing field validators for business logic constraints.
- Suggested Fix: Define strict Pydantic models with appropriate field types and validators.

### B) Insufficient Field Constraints
- Missing `min_length`, `max_length`, `ge`, `le`, `pattern` constraints.
- String fields without length limits (potential DoS via large payloads).
- Numeric fields without range validation.
- List fields without `min_items`, `max_items` constraints.
- Suggested Fix: Add appropriate Field constraints matching business requirements.

### C) File Upload Validation Gaps
- Missing file type validation (MIME type, magic bytes).
- Missing file size limits on upload endpoints.
- Path traversal vulnerabilities in filename handling.
- Suggested Fix: Validate file type, size, and sanitize filenames.

### D) Query Parameter Validation
- Missing type coercion for query parameters.
- Unbounded pagination parameters (offset/limit without max).
- Missing default values for optional parameters.
- Suggested Fix: Use Pydantic models or FastAPI Query() with constraints.

---

## 2) Response Contract Issues

### A) Inconsistent Response Models
- Endpoints returning raw dicts instead of Pydantic response models.
- Missing `response_model` declarations on route handlers.
- Inconsistent field naming (camelCase vs snake_case mixing).
- Suggested Fix: Define and apply response models to all endpoints.

### B) Missing Response Model Configurations
- Response models exposing internal fields (IDs, timestamps, internal state).
- Missing `response_model_exclude_unset` or `response_model_exclude_none`.
- Overly broad models returning more data than needed.
- Suggested Fix: Use model inheritance or `response_model_include/exclude`.

### C) Pagination Response Standards
- Inconsistent pagination response shapes across endpoints.
- Missing total count, page info, or navigation links.
- Different pagination strategies (offset vs cursor) without documentation.
- Suggested Fix: Standardize pagination response wrapper model.

### D) Envelope Consistency
- Some endpoints wrapped in `{data: ...}`, others returning raw data.
- Inconsistent metadata fields (timestamp, request_id, version).
- Suggested Fix: Establish and enforce consistent response envelope.

---

## 3) Error Handling & Status Codes

### A) Inconsistent Error Response Shapes
- Different error formats across endpoints.
- Missing structured error details (code, message, field errors).
- Validation errors not following RFC 7807 or consistent schema.
- Suggested Fix: Define standard error response model and use consistently.

### B) Incorrect HTTP Status Codes
- Using 200 for errors or 500 for client errors.
- Missing 201 for resource creation, 204 for no content.
- Using 400 generically instead of specific 4xx codes.
- Suggested Fix: Map error types to appropriate status codes.

### C) Exception Handler Gaps
- Unhandled exceptions leaking stack traces to clients.
- Missing global exception handlers for common error types.
- Inconsistent handling of Pydantic ValidationError.
- Suggested Fix: Register exception handlers for all error categories.

### D) Error Message Security
- Error messages exposing internal paths, database details, or secrets.
- Stack traces visible in production responses.
- Suggested Fix: Sanitize error messages, use generic messages in production.

---

## 4) WebSocket Contract Issues

### A) Missing Message Schemas
- WebSocket messages sent/received as untyped JSON.
- No validation of incoming WebSocket messages.
- Inconsistent message type/action field naming.
- Suggested Fix: Define Pydantic models for all WebSocket message types.

### B) Protocol Documentation Gaps
- Missing documentation of WebSocket message flow.
- Undocumented connection lifecycle (connect, auth, disconnect).
- Missing error message formats for WebSocket errors.
- Suggested Fix: Document WebSocket protocol in OpenAPI extensions or separate docs.

### C) Message Versioning
- No version field in WebSocket messages.
- Breaking changes not signaled to clients.
- Suggested Fix: Add message version/type fields for forward compatibility.

---

## 5) OpenAPI/Documentation Completeness

### A) Missing Endpoint Documentation
- Routes without docstrings or operation descriptions.
- Missing `summary`, `description`, `tags` in route decorators.
- Undocumented query parameters or path parameters.
- Suggested Fix: Add comprehensive docstrings and FastAPI metadata.

### B) Example Values Missing
- Request/response models without `json_schema_extra` examples.
- No example values for complex nested objects.
- Missing examples for error responses.
- Suggested Fix: Add example values to Pydantic models and route definitions.

### C) Response Documentation Gaps
- Missing `responses` parameter documenting error cases.
- 4xx/5xx responses not documented in OpenAPI spec.
- Missing response descriptions.
- Suggested Fix: Document all possible response codes with models.

### D) Schema Naming Issues
- Auto-generated schema names that are unclear.
- Duplicate schema definitions with different names.
- Suggested Fix: Use explicit `title` in Pydantic models.

---

## 6) Type Safety & Frontend Sync

### A) TypeScript Type Drift
- Frontend TypeScript types not matching backend Pydantic models.
- Manual type definitions instead of generated from OpenAPI.
- Missing null/undefined handling matching Python Optional.
- Suggested Fix: Generate TypeScript types from OpenAPI spec.

### B) API Client Inconsistencies
- Inconsistent error handling in API client code.
- Missing type assertions on API responses.
- Hardcoded URLs instead of centralized API configuration.
- Suggested Fix: Use typed API client generated from OpenAPI.

### C) Enum Synchronization
- Backend string enums not matching frontend constants.
- Inconsistent enum value casing or naming.
- Suggested Fix: Generate shared enum definitions or use string literals.

---

## 7) API Versioning & Evolution

### A) No Versioning Strategy
- API changes breaking existing clients.
- No deprecation warnings or sunset headers.
- Missing version prefix in routes.
- Suggested Fix: Implement versioning strategy (URL path or header).

### B) Breaking Change Risks
- Field removals or renames without deprecation period.
- Type changes that break existing clients.
- Suggested Fix: Use additive changes, deprecation headers, version bumps.

### C) Backwards Compatibility Issues
- Required fields added to request models.
- Response field types changed.
- Suggested Fix: Make new fields optional, use union types for transitions.

---

## 8) Idempotency & Request Handling

### A) Missing Idempotency Keys
- POST/PUT endpoints without idempotency support.
- Retry-unsafe operations that can cause duplicates.
- Suggested Fix: Accept and honor `Idempotency-Key` header.

### B) Request Deduplication Gaps
- Same request processed multiple times under concurrent requests.
- Missing unique constraints or duplicate checks.
- Suggested Fix: Implement idempotency middleware or database constraints.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | LOW]

Location: FileName : Line Number(s)
Risk Category: Validation | Response | Error | WebSocket | Documentation | TypeSafety | Versioning | Idempotency

The Problem:
- 2-4 sentences explaining the contract violation or validation gap.
- Be specific about the risk: data corruption, security exposure, client breakage, debugging difficulty, etc.

Contract Impact:
- Describe the impact on API consumers and system reliability.
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (send malformed request, check OpenAPI spec, compare with TypeScript types, etc.).

The Fix:
- Provide the corrected code snippet.
- Show before/after if useful.
- Include Pydantic model definitions where applicable.

Trade-off Consideration:
- Note validation overhead, backwards compatibility, or migration complexity.
- If acceptable at current scale, mark as LOW with what threshold triggers fix.
```

## Severity Classification
- **CRITICAL**: Security vulnerability, data corruption risk, or breaking production clients.
- **HIGH**: Significant contract violations that cause client errors or confusion.
- **MEDIUM**: Inconsistencies that complicate debugging or maintenance.
- **LOW**: Documentation gaps or minor standardization issues.

---

## Contract Quality Score Rubric (1-10)

Rate overall API contract quality based on issues found:
- **9-10**: Production-ready APIs with comprehensive validation and documentation.
- **7-8**: Solid contracts with minor gaps; safe for production with monitoring.
- **5-6**: Notable inconsistencies; needs cleanup before scaling team/usage.
- **3-4**: Significant validation/contract issues; high risk of client problems.
- **<3**: Fundamental contract problems; not suitable for external consumption.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (security/breaking issues)
2) Fix Soon (contract standardization)
3) Improve Later (documentation/polish)

## Also include:
- Estimated effort to implement all Fix Now items
- Tooling recommendations:
  - OpenAPI spec validation: `openapi-spec-validator`
  - TypeScript generation: `openapi-typescript` or `openapi-generator`
  - Contract testing: `schemathesis` for property-based API testing
  - Pydantic best practices: `pydantic` v2 strict mode, custom validators
- Recommended workflow:
  - Generate OpenAPI spec -> Validate spec -> Generate TypeScript types -> Run contract tests
