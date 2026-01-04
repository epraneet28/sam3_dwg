# 08: API Contract & Cross-Language Type Safety

**Priority**: P1 (Critical)
**Merged From**: #6 (API Contract & Validation), #27 (Cross-Language Type Drift)
**Status**: Active
**Last Updated**: 2025-12-26

---

## Overview

This audit ensures robust, type-safe communication between Python/FastAPI backend and React/TypeScript frontend. Focus areas:
- Pydantic v2 validation patterns and field constraints
- Cross-language type drift (Python ↔ TypeScript)
- API contract consistency and documentation
- WebSocket message schemas
- Serialization correctness (datetime, enums, nested objects)

**Tech Stack Context**:
- Backend: Python 3.12 + FastAPI + Pydantic v2 + Uvicorn
- Frontend: React 19 + TypeScript 5.9 + Zustand
- Communication: REST API + WebSockets
- Database: SQLite3
- External: Label Studio SDK

---

## Section 1: API Contract Standards

### 1.1 Request Validation

⚠️ **AI-CODING RISK**: AI-generated endpoints may use permissive types (`dict`, `Any`) instead of strict Pydantic models, allowing invalid data through.

**Audit Items**:

- [ ] 🐍 **Pydantic Model Usage**: All endpoints use typed Pydantic models (no `dict`, `Any`, raw JSON)
  - Check: `@app.post()` handlers accept Pydantic models, not `dict` params
  - Location: `backend/api/endpoints/*.py`

- [ ] 🐍 **Field Constraints**: All Pydantic fields have appropriate validators
  - Strings: `min_length`, `max_length`, `pattern` where applicable
  - Numbers: `ge`, `le`, `gt`, `lt` for ranges
  - Lists: `min_items`, `max_items` to prevent unbounded collections
  - Check: `Field(...)` usage in `backend/api/models/*.py`

- [ ] 🐍 **File Upload Validation**: Upload endpoints validate type, size, and sanitize filenames
  - MIME type validation (not just extension)
  - File size limits (prevent DoS via large payloads)
  - Path traversal protection in filename handling
  - Location: `backend/api/endpoints/upload.py`

- [ ] 🐍 **Query Parameter Validation**: Query params use `Query()` with constraints
  - Pagination: `limit` has max value (e.g., `Query(le=100)`)
  - Optional params have explicit defaults
  - Location: All endpoints with query parameters

### 1.2 Response Models

⚠️ **AI-CODING RISK**: Inconsistent response shapes and missing `response_model` declarations break frontend expectations.

**Audit Items**:

- [ ] 🐍 **Response Model Declarations**: All routes declare `response_model`
  - Check: `@app.get("/...", response_model=...)` everywhere
  - No raw `dict` returns without schema
  - Location: `backend/api/endpoints/*.py`

- [ ] 🐍 **Field Naming Consistency**: Use snake_case consistently (not mixed with camelCase)
  - Pydantic serialization uses `by_alias=True` if using camelCase aliases
  - Location: `backend/api/models/*.py`

- [ ] 🐍 **Response Model Security**: Don't expose internal fields
  - Use `response_model_exclude_unset` or `response_model_exclude_none` appropriately
  - Separate models for create/read/update if needed (no password fields in responses)
  - Check: Model inheritance or explicit exclude lists

- [ ] 🐍 **Pagination Standards**: Consistent pagination response shape
  - Standardized wrapper: `{ items: T[], total: int, page: int, page_size: int }`
  - All paginated endpoints use same model
  - Location: `backend/api/models/*.py` for pagination model

- [ ] 🐍 **Response Envelope Consistency**: Decide on envelope strategy and apply everywhere
  - Either: Unwrapped `T` OR wrapped `{ data: T, metadata: {...} }`
  - Document decision in API standards
  - Check: No mixing of both patterns

### 1.3 Error Handling

⚠️ **AI-CODING RISK**: Inconsistent error formats and exposed stack traces leak sensitive information.

**Audit Items**:

- [ ] 🐍 **Standard Error Response Model**: Define and use consistent error schema
  - Structure: `{ error: { code: str, message: str, details: Optional[dict] } }`
  - Follows RFC 7807 or similar standard
  - Location: `backend/api/models/*.py` or `backend/core/errors.py`

- [ ] 🐍 **HTTP Status Codes**: Correct status codes for all responses
  - 200: Success (GET, PUT, PATCH)
  - 201: Created (POST)
  - 204: No Content (DELETE)
  - 400: Client error (malformed request)
  - 401: Unauthorized
  - 403: Forbidden
  - 404: Not Found
  - 422: Validation Error (Pydantic)
  - 500: Server error
  - Check: `status_code=...` in route decorators and `HTTPException` raises

- [ ] 🐍 **Global Exception Handlers**: Register handlers for all error types
  - `ValidationError` (Pydantic) → 422 with field details
  - `HTTPException` → appropriate status code
  - `Exception` → 500 with sanitized message
  - Location: `backend/main.py` or middleware

- [ ] 🐍 **Error Message Security**: No sensitive data in error responses
  - No stack traces in production
  - No database connection strings, file paths, or secrets
  - Generic messages for 500 errors
  - Check: Exception handler sanitization logic

### 1.4 WebSocket Contracts

⚠️ **AI-CODING RISK**: Untyped WebSocket messages cause silent failures when schema changes.

**Audit Items**:

- [ ] 🐍 **WebSocket Message Schemas**: Define Pydantic models for all message types
  - Discriminated unions with `type` field: `{ type: "event_name", payload: {...} }`
  - Separate models for client→server vs server→client
  - Location: `backend/api/models/*.py` or `backend/websocket/*.py`

- [ ] 🐍 **Message Validation**: Validate all incoming WebSocket messages
  - Parse with Pydantic before processing
  - Send structured error messages on validation failure
  - Location: `backend/websocket/handlers.py`

- [ ] 🐍 **Message Versioning**: Include version field for forward compatibility
  - Field: `message_version: str = "1.0"`
  - Document version changes
  - Handle multiple versions if breaking changes occur

- [ ] 📄 **WebSocket Protocol Documentation**: Document connection lifecycle
  - Connection/authentication flow
  - All message types with examples
  - Error message formats
  - Location: `docs/` or OpenAPI extensions

### 1.5 OpenAPI Documentation

⚠️ **AI-CODING RISK**: Missing documentation makes API hard to consume and prevents code generation.

**Audit Items**:

- [ ] 🐍 **Endpoint Descriptions**: All routes have docstrings and metadata
  - `summary`, `description`, `tags` in route decorators
  - Docstrings explain purpose and behavior
  - Location: `backend/api/endpoints/*.py`

- [ ] 🐍 **Example Values**: Models include `json_schema_extra` with examples
  - Request examples showing valid payloads
  - Response examples for success and error cases
  - Location: `backend/api/models/*.py`

- [ ] 🐍 **Response Documentation**: Document all possible response codes
  - `responses={...}` parameter with error models
  - 4xx and 5xx cases documented
  - Check: Route decorator completeness

- [ ] 🐍 **Schema Naming**: Clear, non-generic Pydantic model names
  - Use explicit `model_config = ConfigDict(title="...")` if needed
  - No auto-generated names like `Model1`, `Model2`
  - Location: `backend/api/models/*.py`

### 1.6 API Versioning

⚠️ **AI-CODING RISK**: Breaking changes without versioning break production clients.

**Audit Items**:

- [ ] 🐍 **Versioning Strategy**: Implement URL-based or header-based versioning
  - URL: `/api/v1/...` vs `/api/v2/...`
  - OR Header: `API-Version: 1.0`
  - Document strategy and apply consistently

- [ ] 🐍 **Deprecation Warnings**: Use `deprecated=True` in route decorators
  - Document sunset timeline
  - Include `Sunset` header in responses
  - Location: Any endpoints being phased out

- [ ] 🐍 **Backwards Compatibility**: Additive changes only within same version
  - New fields should be optional
  - Use union types for transitions: `Field[Union[OldType, NewType]]`
  - Required field additions require version bump

### 1.7 Idempotency

⚠️ **AI-CODING RISK**: Non-idempotent operations cause duplicate data under retries.

**Audit Items**:

- [ ] 🐍 **Idempotency Key Support**: POST/PUT endpoints accept `Idempotency-Key` header
  - Store key → response mapping (Redis or database)
  - Return cached response for duplicate keys
  - Location: Middleware or decorator in critical endpoints

- [ ] 🐍 **Database Constraints**: Unique constraints prevent duplicates
  - Document IDs, filenames, or business keys have DB-level uniqueness
  - Handle `IntegrityError` gracefully
  - Location: Database schema and model validators

---

## Section 2: Cross-Language Type Safety (Pydantic ↔ TypeScript)

### 2.1 Schema Parity

⚠️ **AI-CODING RISK**: Independent backend/frontend changes cause type drift and runtime errors.

**Audit Items**:

- [ ] 🐍⚛️ **Field Completeness (Backend → Frontend)**: TypeScript interfaces have all Pydantic fields
  - Inventory: Map every Pydantic model to its TypeScript counterpart
  - Check: No missing fields in frontend that backend sends
  - Locations: `backend/api/models/*.py` ↔ `frontend/src/types/*.ts`

- [ ] 🐍⚛️ **Field Completeness (Frontend → Backend)**: No extra fields in TypeScript sent to API
  - Client-only fields should use `Omit<BaseType, 'clientField'>` for API calls
  - Check: No 422 validation errors from unexpected fields
  - Locations: `frontend/src/types/*.ts` and API call sites

- [ ] 🐍⚛️ **Type Alignment**: Same field, same type on both sides
  - IDs: Consistent `string` vs `number`
  - Arrays: `T[]` vs `T` single value
  - Nested objects: Match structure exactly
  - Check: Compare field-by-field for all paired types

- [ ] 🐍⚛️ **Nullability Consistency**: `Optional[T]` maps to `T | null` (not `T?`)
  - Pydantic: `Optional[str]` → JSON `null` allowed
  - TypeScript: `field: string | null` (explicit null)
  - NOT: `field?: string` (means undefined)
  - Rationale: `undefined` sent to backend fails validation

- [ ] 🐍⚛️ **Default Values**: Pydantic defaults match TypeScript expectations
  - Document all default values in both places
  - Required fields in Pydantic must be required in TypeScript (no `?`)
  - Check: `Field(default=...)` vs TypeScript optional (`?`)

### 2.2 Enum & Constant Synchronization

⚠️ **AI-CODING RISK**: Enum value mismatches cause switch/case fallthrough and wrong states.

**Audit Items**:

- [ ] 🐍⚛️ **Enum Value Parity**: Python enum values match TypeScript exactly
  - Use identical string values (case-sensitive)
  - Example: Python `Status.PENDING = "pending"` ↔ TypeScript `"pending"`
  - Avoid: Python `UPPER_CASE` vs TypeScript `camelCase` mismatches
  - Locations: `backend/api/models/*.py` ↔ `frontend/src/types/*.ts`

- [ ] 🐍⚛️ **Enum Completeness**: All enum values exist on both sides
  - New pipeline stages, statuses, or types added to both
  - TypeScript exhaustiveness checks: `satisfies` or switch/case default throws
  - Check: Compare all enum declarations

- [ ] 🐍⚛️ **Enum Serialization Format**: Pydantic uses `use_enum_values=True` or explicit serializer
  - Pydantic v2 default serializes enum `.value` (good for strings)
  - Ensure `.name` is not used unless TypeScript expects it
  - Location: `model_config = ConfigDict(use_enum_values=True)`

- [ ] 🐍⚛️ **Status Constants**: Shared status/state strings match exactly
  - Example: `"pending"`, `"processing"`, `"completed"`, `"error"`
  - Single source of truth (generate TypeScript from Python or vice versa)
  - Check: Search for hardcoded status strings on both sides

### 2.3 Date/Time Serialization

⚠️ **AI-CODING RISK**: Datetime serialization mismatches cause off-by-hours bugs and parsing failures.

**Audit Items**:

- [ ] 🐍⚛️ **ISO 8601 Consistency**: All datetimes serialize as ISO 8601 with UTC and `Z` suffix
  - Format: `2025-12-26T14:30:00.000Z`
  - Pydantic v2: Use `AwareDatetime` or custom serializer
  - TypeScript: Parse with `new Date(isoString)` or date-fns
  - Check: Sample API responses for datetime format

- [ ] 🐍⚛️ **Timezone Awareness**: All Python `datetime` objects are timezone-aware (UTC)
  - Use `datetime.now(timezone.utc)` not `datetime.now()`
  - Pydantic validator ensures timezone info exists
  - Frontend converts to local time only for display
  - Location: All datetime fields in models

- [ ] 🐍⚛️ **Date-Only Handling**: Separate date vs datetime serialization
  - Date-only: Serialize as `YYYY-MM-DD` string
  - DateTime: ISO 8601 with time component
  - TypeScript: Parse appropriately (don't add midnight time to dates)
  - Check: Pydantic `date` vs `datetime` field types

- [ ] 🐍⚛️ **Duration/Timedelta**: Standardized serialization format
  - Options: ISO 8601 duration (`P1DT2H`), seconds integer, or `{ days, hours, minutes }`
  - Document choice and implement on both sides
  - Location: Any timedelta/duration fields

### 2.4 Nested Objects & Collections

⚠️ **AI-CODING RISK**: Deep structure drift causes null reference errors deep in object trees.

**Audit Items**:

- [ ] 🐍⚛️ **Nested Model Alignment**: Deeply nested structures match exactly
  - Example: `Document.pages[].elements[].bbox`
  - Check each level of nesting recursively
  - Locations: Complex models like `Document`, `Page`, `Element`

- [ ] 🐍⚛️ **Array Element Types**: `List[T]` matches `T[]` element type
  - Array of IDs: `List[str]` ↔ `string[]`
  - Array of objects: `List[Model]` ↔ `Interface[]`
  - Check: `.map()` usage in frontend for type assumptions

- [ ] 🐍⚛️ **Dict/Record Typing**: `Dict[str, T]` maps to `Record<string, T>`
  - Avoid `Dict[str, Any]` → use specific value types
  - TypeScript: Use `Record<>` or `{ [key: string]: T }` consistently
  - Check: Index access patterns in frontend

- [ ] 🐍⚛️ **Union Type Handling**: Discriminated unions with explicit `type` field
  - Pydantic: `Union[ModelA, ModelB]` with `type` discriminator
  - TypeScript: `type Shape = TypeA | TypeB` with type guards
  - Check: Use `Discriminator(...)` in Pydantic v2 where applicable

### 2.5 WebSocket Message Types

⚠️ **AI-CODING RISK**: WebSocket type drift causes silent message drops and state corruption.

**Audit Items**:

- [ ] 🐍⚛️ **Message Type Structure**: Backend sends/expects same structure as frontend
  - Discriminated union: `{ type: "event_name", payload: {...} }`
  - Both sides have all message types defined
  - Locations: `backend/websocket/*.py` ↔ `frontend/src/types/websocket.ts`

- [ ] 🐍⚛️ **Payload Schema Parity**: Message payloads match field-by-field
  - Progress updates: `{ current, total, message }` consistent
  - Error messages: `{ error, code, details }` consistent
  - Check: All WebSocket message handler types

- [ ] 🐍⚛️ **Event Name Consistency**: Identical event names (case-sensitive)
  - Backend: `"document_updated"` ↔ Frontend: `"document_updated"`
  - Use shared constants or code generation
  - Check: Event name string literals on both sides

- [ ] 🐍⚛️ **Bidirectional Messages**: Separate types for client→server vs server→client
  - Don't reuse same interface if directions differ
  - Clear naming: `ClientMessage`, `ServerMessage`
  - Location: WebSocket type definitions

### 2.6 API Response Shape

⚠️ **AI-CODING RISK**: Inconsistent response wrapping causes `data.data` bugs or undefined errors.

**Audit Items**:

- [ ] 🐍⚛️ **Response Wrapper Consistency**: All endpoints use same wrapping strategy
  - Either: Direct `T` OR envelope `{ data: T }`
  - Frontend unwrapping logic matches backend consistently
  - Check: API response handling in frontend utils

- [ ] 🐍⚛️ **Error Response Types**: TypeScript has types for all error shapes
  - Pydantic validation errors (422): `{ detail: [{loc, msg, type}] }`
  - Custom errors: Match backend error model
  - Frontend: Type-safe error extraction
  - Locations: Error handling in API client

- [ ] 🐍⚛️ **Pagination Response Alignment**: Frontend expects backend pagination format
  - Backend: `{ items, total, page, page_size }` or similar
  - Frontend: Same field names and types
  - Check: Pagination component prop types vs API response

- [ ] 🐍⚛️ **Partial vs Full Models**: Separate types for list vs detail endpoints
  - List endpoint: Summary model (subset of fields)
  - Detail endpoint: Full model (all fields)
  - TypeScript: Use `Pick<>` or `Omit<>` for summaries
  - Avoid: Using full type when only partial data returned

### 2.7 Pydantic v2 Specific Patterns

⚠️ **AI-CODING RISK**: Pydantic v1→v2 migration changes serialization behavior if not updated correctly.

**Audit Items**:

- [ ] 🐍 **Model Config Syntax**: Use Pydantic v2 `model_config = ConfigDict(...)`
  - NOT: `class Config` (v1 syntax)
  - Update: `orm_mode` → `from_attributes`
  - Update: `schema_extra` → `json_schema_extra`
  - Location: All Pydantic models in `backend/api/models/*.py`

- [ ] 🐍 **Field Serialization Aliases**: Consistent alias usage
  - `Field(serialization_alias="...")` for camelCase JSON output
  - Use `by_alias=True` when serializing
  - TypeScript: Use alias names in interfaces
  - Check: Model `.model_dump(by_alias=True)` calls

- [ ] 🐍⚛️ **Computed Fields**: TypeScript includes `@computed_field` properties
  - Pydantic v2: `@computed_field` decorator adds read-only fields
  - Frontend: Add these fields to TypeScript interfaces
  - Check: Search for `@computed_field` in backend

- [ ] 🐍 **Strict Mode Handling**: Explicit type coercion for compatibility
  - Pydantic v2 stricter: `"123"` won't auto-coerce to `123`
  - Use `BeforeValidator` or `field_serializer` for flexibility
  - Document coercion rules
  - Location: Models with numeric or bool fields from query params

**Pydantic v1 → v2 Migration Reference**:

| Pydantic v1 | Pydantic v2 | Notes |
|-------------|-------------|-------|
| `class Config:` | `model_config = ConfigDict(...)` | New syntax |
| `orm_mode = True` | `from_attributes=True` | ORM model support |
| `schema_extra = {...}` | `json_schema_extra={...}` | Schema metadata |
| `Field(alias="...")` | `Field(serialization_alias="...")` | Serialization alias |
| `@validator` | `@field_validator` | Field validation |
| `@root_validator` | `@model_validator` | Model-level validation |
| `.dict()` | `.model_dump()` | Serialization method |
| `.json()` | `.model_dump_json()` | JSON serialization |
| `parse_obj()` | `model_validate()` | Deserialization |

### 2.8 Code Generation & Automation

⚠️ **AI-CODING RISK**: Manual type maintenance causes drift; automation keeps types in sync.

**Audit Items**:

- [ ] 🐍⚛️ **OpenAPI Spec Generation**: FastAPI auto-generates OpenAPI schema
  - Endpoint: `/openapi.json` or `/docs`
  - Validate with `openapi-spec-validator`
  - Check: Schema includes all models and endpoints

- [ ] ⚛️ **TypeScript Type Generation**: Generate frontend types from OpenAPI spec
  - Tool: `openapi-typescript` or `openapi-generator`
  - Automate: Add to CI/CD or pre-commit hook
  - Location: Script in `package.json` or `scripts/`

- [ ] 🐍⚛️ **Type Drift Detection**: CI check fails on type mismatches
  - Compare generated types to committed types
  - Fail build if drift detected
  - Force explicit type updates with review

- [ ] 🐍⚛️ **Shared Constants**: Single source of truth for enums/constants
  - Option 1: Generate TypeScript from Python
  - Option 2: Generate Python from TypeScript
  - Option 3: JSON/YAML schema consumed by both
  - Check: No duplicate enum definitions

---

## Reference: Python ↔ TypeScript Type Mapping

| Python (Pydantic v2) | JSON | TypeScript | Notes |
|----------------------|------|------------|-------|
| `str` | `"string"` | `string` | Basic string |
| `int` | `42` | `number` | Integer |
| `float` | `3.14` | `number` | Float |
| `bool` | `true/false` | `boolean` | Boolean |
| `None` / `Optional[T]` | `null` | `T \| null` | Explicit null (NOT `T?`) |
| `List[T]` | `[...]` | `T[]` or `Array<T>` | Array |
| `Dict[str, T]` | `{...}` | `Record<string, T>` | Object/dict |
| `datetime` | `"2025-12-26T14:30:00Z"` | `string` (ISO 8601) | Parse with `Date()` |
| `date` | `"2025-12-26"` | `string` (YYYY-MM-DD) | Date-only |
| `Enum` (with `use_enum_values`) | `"value"` | `"value"` (literal) | String enum value |
| `Union[A, B]` (discriminated) | `{type: "..."}` | `A \| B` with type guard | Use discriminator |
| `Literal["a", "b"]` | `"a"` or `"b"` | `"a" \| "b"` | Literal types |
| `Any` | any | `unknown` or `any` | Avoid in public APIs |

---

## Severity Classification

- **CRITICAL**: Security vulnerability, data corruption, or production client breakage
- **HIGH**: Visible bugs, broken features, API errors (422/500)
- **MEDIUM**: Edge case bugs, inconsistent behavior, confusing UX
- **LOW**: Documentation gaps, minor standardization issues

---

## Common AI-Generated Anti-Patterns

1. **Hallucinated Types**: TypeScript interface doesn't match any backend model
   - Fix: Trace every type to source of truth; delete orphans

2. **Copy-Paste Drift**: AI copied similar type but didn't update all fields
   - Fix: Code review focus on type definitions; integration tests

3. **Assumed Serialization**: AI assumed datetime format without checking
   - Fix: Explicit serialization tests; end-to-end type checking

4. **Incomplete Updates**: New feature added to backend but not frontend types
   - Fix: Checklist for changes: backend model → API → TypeScript → component

5. **Permissive Validation**: `str` where `EmailStr`, `HttpUrl`, or regex pattern needed
   - Fix: Use specialized Pydantic types with validators

6. **Missing Response Models**: Routes return raw dicts without `response_model`
   - Fix: Define response models for all endpoints

---

## Testing Recommendations

### Backend Tests
- [ ] Pydantic model validation tests (valid/invalid cases)
- [ ] API endpoint integration tests (request/response round-trip)
- [ ] Serialization tests (datetime, enums, nested objects)
- [ ] OpenAPI spec validation: `openapi-spec-validator`

### Frontend Tests
- [ ] API client mock tests (type assertions on responses)
- [ ] WebSocket message handler tests (all message types)
- [ ] Snapshot tests for API response shapes
- [ ] Type checking: `tsc --noEmit` in CI

### Integration Tests
- [ ] End-to-end tests validating full request/response cycle
- [ ] Contract tests between backend and frontend
- [ ] Type drift detection in CI (compare generated vs committed types)

---

## Tooling Recommendations

### Code Generation
- `openapi-typescript` - Generate TypeScript from FastAPI OpenAPI schema
- `pydantic-to-typescript` - Direct Pydantic → TypeScript conversion (if not using OpenAPI)
- `datamodel-code-generator` - Generate Pydantic models from JSON Schema/OpenAPI

### Validation & Testing
- `openapi-spec-validator` - Validate OpenAPI schema correctness
- `schemathesis` - Property-based API testing from OpenAPI spec
- `zod` - Runtime validation on frontend matching Pydantic
- `pytest` + `httpx` - Backend API integration tests

### Runtime Type Safety
- `pydantic` v2 strict mode - Stricter type coercion
- `TypeGuard` (TypeScript) - Runtime type narrowing
- Custom Pydantic validators - Business logic validation

---

## Action Plan Template

### 1) Fix Now (Critical/High - blocks release)
- [ ] List specific type/validation fixes with file locations
- [ ] Estimated effort: ___ hours/days

### 2) Fix Soon (Medium - next sprint)
- [ ] Secondary alignment tasks
- [ ] Estimated effort: ___ hours/days

### 3) Process Improvements
- [ ] Set up OpenAPI → TypeScript generation in CI
- [ ] Add contract tests to test suite
- [ ] Create shared enum/constant definitions
- [ ] Document API versioning strategy

### 4) Ongoing Maintenance
- [ ] Regular type drift audits (monthly/quarterly)
- [ ] Review all API changes for type impacts
- [ ] Update documentation when contracts change

---

## Completion Criteria

✅ This audit is complete when:
1. All Pydantic models have proper validation and constraints
2. All API endpoints have response models and documentation
3. TypeScript types match backend models (verified by generation or manual audit)
4. Enums and constants synchronized across languages
5. Datetime serialization uses consistent ISO 8601 UTC format
6. WebSocket messages have typed schemas on both sides
7. Error responses have consistent shape and proper status codes
8. OpenAPI documentation complete and validated
9. Type generation automated in CI/CD pipeline
10. Integration tests validate request/response contracts

---

**Next Steps**: Begin with Section 1.1 (Request Validation) and work through systematically, checking off items as you verify them.
