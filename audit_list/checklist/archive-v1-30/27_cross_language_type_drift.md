# Cross-Language Type Drift Audit Prompt (Python/Pydantic ↔ TypeScript)

## Role
Act as a Senior Full-Stack Architect specializing in type safety and API contracts. Perform a deep-dive Cross-Language Type Drift Audit to identify mismatches between Python/Pydantic backend models and TypeScript frontend interfaces that will cause runtime errors, silent data corruption, or broken UI behavior.

## Primary Goal
Identify where Python backend types and TypeScript frontend types have drifted apart due to AI-generated code, manual updates, or serialization assumptions—and provide concrete fixes to ensure end-to-end type safety.

## Context
- This code was developed with AI assistance ("vibecoded") and likely has implicit assumptions about how types serialize/deserialize across the Python ↔ TypeScript boundary.
- Backend and frontend were often modified independently without updating the counterpart types.
- Runtime type mismatches cause silent failures, corrupted data, and difficult-to-debug production issues.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Pydantic v2
- Frontend: React 19 + TypeScript 5.9
- State Management: Zustand
- Communication: REST API + WebSockets
- Build Tool: Vite 7

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically, focusing on:
1. All Pydantic models (look for `BaseModel` subclasses)
2. All TypeScript interfaces/types (look for `interface`, `type` declarations)
3. API endpoint responses and request bodies
4. WebSocket message handlers (both send and receive)
5. Zustand store state shapes

If any critical context is missing (API route definitions, WebSocket message schemas, shared constants), infer what you can from the code and explicitly list assumptions.

## Environment & Assumptions (you must do this first)
1) Inventory and map:
   - All Pydantic models and their locations
   - All TypeScript interfaces/types and their locations
   - API endpoints that return/accept these models
   - WebSocket message types on both sides
   - Shared enums, constants, and status values
2) Identify which types are "paired" (should match between backend/frontend)
3) Note any code generation tools in use (openapi-typescript, etc.)

---

## 1) Schema Parity Issues

### A) Missing Fields (Backend → Frontend)
- Backend Pydantic model has fields that TypeScript interface lacks.
- Common hotspots: New fields added to backend during feature development but never synced to frontend.
- Failure Mode: Frontend silently ignores data; features don't work; data is lost on round-trip.
- Suggested Fix: Add missing fields to TypeScript interfaces; consider code generation from OpenAPI spec.

### B) Missing Fields (Frontend → Backend)
- TypeScript interface has fields that Pydantic model doesn't expect.
- Common hotspots: Frontend adds "local-only" fields that accidentally get sent to API.
- Failure Mode: Pydantic validation fails (422 Unprocessable Entity) or fields silently dropped.
- Suggested Fix: Align models or explicitly mark fields as client-only with `Omit<>` utility types.

### C) Type Mismatches (Same Field, Different Type)
- Field exists in both but with incompatible types (e.g., `string` vs `number`, `string[]` vs `string`).
- Common hotspots: IDs (string vs number), arrays vs single values, nested objects vs flattened.
- Failure Mode: Runtime type errors, NaN values, undefined behavior in comparisons.
- Suggested Fix: Audit and align types; add runtime validation on frontend for critical fields.

### D) Nullability Mismatches
- Python `Optional[T]` vs TypeScript `T | null` vs `T | undefined` vs `T?`.
- Pydantic v2 serializes `None` as `null` in JSON, but TypeScript optional (`?`) means "possibly undefined".
- Failure Mode: `undefined` sent to backend fails validation; `null` causes frontend `Cannot read property of null`.
- Suggested Fix: Be explicit about nullability; use `T | null` not `T?` for API types; handle both in frontend.

### E) Default Value Assumptions
- Pydantic model has `Field(default=...)` but TypeScript assumes required.
- Or TypeScript has default but Pydantic expects the field.
- Failure Mode: Missing required field errors; unexpected default values in database.
- Suggested Fix: Document defaults in both places; consider making all API fields explicit.

---

## 2) Enum & Constant Drift

### A) Enum Value Mismatches
- Python `Enum` values don't match TypeScript string literals or `enum` declarations.
- Common issue: Python uses `UPPER_CASE`, TypeScript uses `camelCase` or different strings entirely.
- Failure Mode: Backend rejects frontend values; switch/case statements fall through to default.
- Suggested Fix: Use identical string values; consider a shared constants file or code generation.

### B) Missing Enum Values
- New enum value added to backend (e.g., new pipeline stage) but not to frontend.
- Failure Mode: TypeScript exhaustiveness check fails at compile time (good) or unknown value at runtime (bad).
- Suggested Fix: Add all enum values; use `satisfies` or exhaustiveness helpers in TypeScript.

### C) Enum Serialization Format
- Python `Enum` serialized as `.value` vs `.name` vs custom.
- Pydantic v2 default is `.value`, but some code may use `.name`.
- Failure Mode: Frontend receives unexpected format; comparisons fail.
- Suggested Fix: Explicit serialization in Pydantic (`use_enum_values=True` or custom serializer); match in TypeScript.

### D) Status/State Constants
- String constants for status values (e.g., "pending", "processing", "completed") not synchronized.
- Failure Mode: UI shows wrong states; conditional logic breaks.
- Suggested Fix: Single source of truth; generate TypeScript from Python or vice versa.

---

## 3) Date/Time Serialization

### A) ISO Format Assumptions
- Python `datetime` serialized in one ISO format, TypeScript expects another.
- Common issues: Timezone awareness (naive vs aware), microseconds vs milliseconds, `Z` suffix vs `+00:00`.
- Failure Mode: Date parsing fails; times shown incorrectly; sorting broken.
- Suggested Fix: Use consistent ISO 8601 format; always use UTC with `Z` suffix; parse with robust library (date-fns, dayjs).

### B) Timezone Handling
- Backend uses UTC, frontend displays in local time, but conversion is wrong or missing.
- Python `datetime` without timezone info (naive) gets serialized ambiguously.
- Failure Mode: Times off by hours; DST causes intermittent bugs.
- Suggested Fix: Always use timezone-aware datetimes; store/transmit UTC; convert for display only.

### C) Date-Only vs DateTime
- Python `date` vs `datetime`, TypeScript treats both as string but handles differently.
- Failure Mode: Time components appear as midnight; date comparisons fail.
- Suggested Fix: Use consistent types; if date-only, serialize as `YYYY-MM-DD` string.

### D) Duration/Timedelta Serialization
- Python `timedelta` doesn't have a standard JSON representation.
- Failure Mode: Frontend receives `null` or throws; calculation logic breaks.
- Suggested Fix: Serialize as ISO 8601 duration (`P1DT2H`), seconds integer, or structured object.

---

## 4) Nested Object & Collection Types

### A) Nested Model Drift
- Nested Pydantic models drift from nested TypeScript interfaces.
- Common hotspots: Deep structures like `Document.pages[].elements[].bbox`.
- Failure Mode: Deeply nested null/undefined errors; partial data corruption.
- Suggested Fix: Audit nested types recursively; consider flattening or using IDs with separate lookups.

### B) Array Type Mismatches
- `List[T]` vs `T[]` with different element types.
- Array of IDs vs array of full objects.
- Failure Mode: `.map()` fails; property access on wrong type.
- Suggested Fix: Be explicit about array element types; use generics consistently.

### C) Dict/Object Typing
- Python `Dict[str, Any]` vs TypeScript `Record<string, unknown>` vs `{ [key: string]: T }`.
- Common issue: Python uses string keys, but TypeScript might expect specific literal keys.
- Failure Mode: Type narrowing fails; index access returns unexpected types.
- Suggested Fix: Use specific types where possible; avoid `Any`/`unknown` in public APIs.

### D) Union Type Serialization
- Python `Union[A, B]` or discriminated unions need matching TypeScript handling.
- Common issue: No discriminator field, TypeScript can't narrow the type.
- Failure Mode: Type guards fail; wrong component rendered.
- Suggested Fix: Use discriminated unions with explicit `type` field; add type guards in TypeScript.

---

## 5) WebSocket Message Types

### A) Message Type Mismatch
- WebSocket sends messages with type/event field, but frontend expects different structure.
- Failure Mode: Messages ignored; wrong handlers called; state corruption.
- Suggested Fix: Define shared message schema; use discriminated unions with `type` field.

### B) Payload Schema Drift
- Message payload structure drifts between backend and frontend.
- Common hotspots: Progress updates, error messages, state sync.
- Failure Mode: Frontend crashes on unexpected payload shape.
- Suggested Fix: Strict TypeScript types for all message payloads; runtime validation.

### C) Event Name Inconsistency
- Backend emits event `document_updated`, frontend listens for `documentUpdated`.
- Failure Mode: Events never received; silent feature breakage.
- Suggested Fix: Shared constants for event names; case-consistent naming convention.

### D) Bidirectional Message Types
- Client → Server and Server → Client messages have different schemas but same handling.
- Failure Mode: Client sends message backend can't parse; vice versa.
- Suggested Fix: Separate types for inbound/outbound messages; clear documentation.

---

## 6) API Response Shape Issues

### A) Response Wrapper Inconsistency
- Some endpoints return `{ data: T }`, others return `T` directly.
- Frontend has inconsistent unwrapping logic.
- Failure Mode: `data.data` bugs; undefined errors.
- Suggested Fix: Consistent response envelope; update all endpoints.

### B) Error Response Types
- Backend returns structured errors, frontend doesn't handle all error shapes.
- Common issue: Pydantic validation errors (422) have specific structure.
- Failure Mode: Error messages not shown; generic "Something went wrong".
- Suggested Fix: Type all error responses; consistent error envelope; proper error handling.

### C) Pagination Response Drift
- Backend pagination uses `limit/offset`, frontend expects `page/pageSize`.
- Or response has `total` but frontend expects `totalPages`.
- Failure Mode: Pagination controls broken; infinite scroll doesn't stop.
- Suggested Fix: Align pagination schemas; document pagination contract.

### D) Partial Response Issues
- Backend returns partial objects (e.g., list view), frontend type expects full object.
- Common issue: List endpoint returns summary, detail endpoint returns full model.
- Failure Mode: Accessing missing fields throws; "undefined is not an object".
- Suggested Fix: Separate types for summary vs full models; use `Pick<>` or `Omit<>`.

---

## 7) Pydantic v2 Specific Issues

### A) Model Config Changes
- Pydantic v2 changed config syntax; old `class Config` vs new `model_config`.
- `orm_mode` → `from_attributes`; `schema_extra` → `json_schema_extra`.
- Failure Mode: Config not applied; serialization behavior different than expected.
- Suggested Fix: Update to Pydantic v2 patterns; test serialization explicitly.

### B) Field Serialization Aliases
- `Field(alias=...)` or `serialization_alias` in Pydantic v2.
- TypeScript uses the alias, Python code uses the field name.
- Failure Mode: Deserialization fails; wrong field names in requests.
- Suggested Fix: Use `by_alias=True` consistently; match aliases in TypeScript.

### C) Computed Fields
- Pydantic v2 `@computed_field` not reflected in TypeScript.
- Failure Mode: Frontend expects field that's only computed on serialization.
- Suggested Fix: Add computed fields to TypeScript interfaces.

### D) Strict Mode Differences
- Pydantic v2 has stricter type coercion by default.
- Frontend sends `"123"`, backend expected `123` (or vice versa).
- Failure Mode: Validation errors on previously working requests.
- Suggested Fix: Explicit type coercion; use `BeforeValidator` for flexibility.

---

## 8) AI-Generated Code Patterns (Vibe Code Issues)

### A) Hallucinated Types
- AI generated TypeScript interface that doesn't match any backend model.
- Or backend model that doesn't match any frontend usage.
- Failure Mode: Types give false confidence; runtime errors despite "type safety".
- Suggested Fix: Trace every type to its source of truth; delete orphan types.

### B) Copy-Paste Drift
- AI copied a similar type and modified it, but not all fields were updated.
- Failure Mode: Wrong field names/types slip through.
- Suggested Fix: Code review focusing on type definitions; integration tests.

### C) Assumed Serialization
- AI assumed `datetime` serializes as timestamp vs ISO string.
- Or assumed enum serializes as number vs string.
- Failure Mode: Silent data corruption; wrong values stored.
- Suggested Fix: Explicit serialization tests; end-to-end type checking.

### D) Incomplete Type Updates
- AI added a new feature but only updated one side (backend or frontend).
- Failure Mode: New feature broken; frontend shows undefined for new fields.
- Suggested Fix: Checklist for type changes: backend model → API response → TypeScript interface → component props.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | LOW]

Location:
- Backend: FileName:LineNumber (Pydantic model/field)
- Frontend: FileName:LineNumber (TypeScript type/interface)

Drift Category: Schema Parity | Enum | DateTime | Nested | WebSocket | API Response | Pydantic v2 | Vibe Code

The Problem:
- 2-4 sentences explaining the type mismatch and its consequences.
- Be specific about failure mode: validation error, silent data loss, runtime crash, broken UI, etc.

Evidence:
- Show the mismatched code snippets from both sides.
- Highlight the specific difference (field name, type, nullability, etc.).

Impact:
- Which API endpoints/WebSocket messages are affected.
- Which UI components/pages will break.
- Confidence: High | Medium | Low

The Fix:

Backend (if change needed):
```python
# Before
# After
```

Frontend (if change needed):
```typescript
// Before
// After
```

Verification:
- How to test the fix works (integration test, type check, runtime validation).

Trade-off Consideration:
- Breaking change? Need migration?
- Which side should be source of truth?
```

## Severity Classification
- **CRITICAL**: Will cause runtime crashes, data corruption, or security issues. Must fix before deployment.
- **HIGH**: Will cause visible bugs, broken features, or API errors (422/500).
- **MEDIUM**: May cause edge case bugs; inconsistent behavior; confusing UX.
- **LOW**: Type documentation mismatch; no runtime impact but maintenance burden.

---

## Type Safety Score Rubric (1-10)

Rate overall type safety based on severity/quantity of drift:
- **9-10**: Excellent type parity; minor documentation issues only.
- **7-8**: Good alignment; 1-2 medium issues to address.
- **5-6**: Significant drift; multiple fields/types out of sync.
- **3-4**: Major mismatches; features likely broken.
- **<3**: Types are decorative; no actual type safety.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- Types requiring immediate sync (highest risk)
- Recommended source of truth strategy

## Final Section: Summary & Action Plan (Mandatory)

### 1) Fix Now (Critical/High - blocks release)
- List specific type fixes with file locations.

### 2) Fix Soon (Medium - next sprint)
- List secondary type alignment tasks.

### 3) Process Improvements
- Code generation from OpenAPI spec
- Shared schema definitions
- CI checks for type drift

### 4) Recommended Tooling
- `openapi-typescript` - Generate TypeScript from FastAPI OpenAPI schema
- `pydantic-to-typescript` - Direct Pydantic → TypeScript conversion
- `zod` - Runtime validation on frontend matching Pydantic
- Type comparison scripts for CI

### 5) Testing Recommendations
- Integration tests that validate full request/response cycle
- Snapshot tests for API response shapes
- Contract tests between backend and frontend
