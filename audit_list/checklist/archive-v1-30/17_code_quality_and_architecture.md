# Code Quality & Architecture Audit Prompt (Production-Ready, Maintainable)

## Role
Act as a Senior Software Architect and Tech Lead. Perform a deep-dive Code Quality & Architecture Audit on the provided codebase to identify maintainability risks, architectural violations, and tech debt that will compound over time.

## Primary Goal
Identify where AI-generated code has introduced structural issues, violated separation of concerns, created coupling, or accumulated tech debt that will slow development and increase defect rates.

## Context
- This code was developed with a focus on speed ("vibecoded") and may have inconsistent patterns.
- I need you to find architectural violations, code smells, and maintainability risks before the codebase grows further.

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
- Styling: Tailwind CSS 4
- State Management: Zustand
- Routing: React Router DOM 7
- Testing: Playwright, pytest

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (project structure, dependency graph, config files), infer what you can and explicitly list assumptions.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - Module/package structure and boundaries
   - Layering strategy (API -> Service -> Repository pattern, etc.)
   - Error handling patterns in use
   - State management approach (frontend and backend)
   - Type system usage (Pydantic models, TypeScript interfaces)
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation.

---

## 1) Module Boundaries & Separation of Concerns

### A) Leaky Abstractions
- Business logic bleeding into API route handlers
- Database queries directly in route handlers instead of repository/service layer
- Frontend components containing business logic instead of hooks/services
- **Stack-specific**: Pipeline stage logic mixed with FastAPI endpoints, Docling internals exposed to API layer

### B) Circular Dependencies
- Modules importing each other, creating dependency cycles
- Frontend components with circular imports
- **Stack-specific**: Checkpoint models importing from stage processors, stage processors importing from API

### C) God Modules / Files
- Files exceeding 500 lines with multiple responsibilities
- Classes/modules with too many methods or doing too many things
- **Stack-specific**: Single file handling all 15 pipeline stages, monolithic checkpoint manager

### D) Missing Domain Boundaries
- No clear separation between document processing, API, and storage domains
- Shared mutable state across boundaries
- **Stack-specific**: Docling types leaking into API responses, Label Studio types mixed with internal models

---

## 2) Layering & Dependency Direction

### A) Inverted Dependencies
- Lower layers depending on higher layers (e.g., utility depending on API)
- Domain/business logic depending on infrastructure
- **Stack-specific**: Pydantic models importing from FastAPI, checkpoint utilities importing from WebSocket handlers

### B) Missing Abstraction Layers
- Direct database access without repository abstraction
- External service calls without adapter pattern
- **Stack-specific**: SQLite3 calls scattered through codebase, Label Studio SDK calls without abstraction

### C) Improper Coupling
- Tight coupling between unrelated modules
- Hard-coded dependencies instead of dependency injection
- **Stack-specific**: Stage processors directly instantiating Docling models, frontend directly constructing API request shapes

### D) Shared Mutable State
- Global variables or singletons with mutable state
- Module-level state that persists between requests
- **Stack-specific**: Global document cache, shared WebSocket connection manager state

---

## 3) Error Handling Patterns

### A) Inconsistent Error Handling
- Mixed exception types (custom vs built-in vs third-party)
- Inconsistent error response shapes in API
- Silent failures (catching and ignoring exceptions)
- **Stack-specific**: Docling exceptions not translated to API errors, checkpoint validation failures not surfaced

### B) Missing Error Boundaries
- No centralized error handling middleware
- React components without error boundaries
- Unhandled promise rejections in frontend
- **Stack-specific**: Pipeline stage failures not properly propagated, WebSocket errors not handled in Zustand

### C) Improper Exception Usage
- Using exceptions for control flow
- Overly broad exception catching (bare `except:` or `except Exception:`)
- Not re-raising or wrapping exceptions with context
- **Stack-specific**: Catching all Docling exceptions without distinguishing recoverable vs fatal

### D) Missing Validation
- Input validation gaps at API boundaries
- Missing schema validation for checkpoint files
- Frontend not validating API responses
- **Stack-specific**: Pydantic models missing validators, TypeScript interfaces not enforcing runtime checks

---

## 4) Tech Debt Hotspots

### A) Code Duplication
- Copy-pasted logic across files
- Similar but slightly different implementations
- Missing shared utilities for common operations
- **Stack-specific**: Duplicate bbox transformation logic, repeated checkpoint save/load patterns

### B) Dead Code
- Unused imports, functions, classes, or modules
- Commented-out code left in production
- Feature flags or conditionals that are always true/false
- **Stack-specific**: Unused stage processor methods, deprecated export formats still in code

### C) TODO/FIXME/HACK Comments
- Unresolved technical debt markers
- Workarounds that were never properly fixed
- **Stack-specific**: "TODO: handle multi-page" comments, "HACK: workaround Docling bug" without tracking

### D) Inconsistent Patterns
- Multiple ways to do the same thing
- Naming convention violations
- Code style inconsistencies
- **Stack-specific**: Mixed async/sync patterns in FastAPI, inconsistent coordinate system usage

---

## 5) Type Safety & Schema Evolution

### A) Type Drift Between Frontend/Backend
- Pydantic models not matching TypeScript interfaces
- Enum values out of sync
- Optional vs required field mismatches
- **Stack-specific**: Pipeline stage status enums, checkpoint schema versions, WebSocket message types

### B) Missing Type Annotations
- Python functions without type hints
- `Any` type overuse
- TypeScript `any` or `unknown` without narrowing
- **Stack-specific**: Docling return types not properly typed, checkpoint data loosely typed

### C) Schema Evolution Risks
- No versioning for checkpoint format
- Breaking changes in API contracts
- Missing migrations for schema changes
- **Stack-specific**: Checkpoint format changes breaking old documents, API response shape changes

### D) Unsafe Type Assertions
- TypeScript `as` casts without validation
- Python `cast()` without runtime checks
- Missing runtime validation for external data
- **Stack-specific**: Casting Label Studio responses, assuming Docling output shapes

---

## 6) Frontend-Specific Quality

### A) Component Architecture
- Components too large (>300 lines)
- Missing separation between presentation and logic
- Props drilling instead of proper state management
- **Stack-specific**: StageViewer monolith, BboxEditor mixing rendering and event handling

### B) State Management Issues
- Zustand store too large or with too many responsibilities
- Derived state not memoized
- Stale closures in callbacks
- **Stack-specific**: Document state, pipeline state, and UI state mixed in single store

### C) Hook Hygiene
- Custom hooks with side effects
- Missing cleanup in useEffect
- Dependencies array issues (missing deps or unnecessary deps)
- **Stack-specific**: WebSocket connection hooks, document polling hooks

### D) Performance Anti-patterns
- Inline object/function creation in render
- Missing React.memo on expensive components
- Unnecessary re-renders from context
- **Stack-specific**: Bbox rendering causing re-renders, page image re-loading

---

## 7) Backend-Specific Quality

### A) FastAPI Patterns
- Route handlers doing too much
- Missing dependency injection
- Improper use of background tasks
- **Stack-specific**: Stage processing in route handlers, missing lifespan management

### B) Pydantic Usage
- Models with validation logic in wrong layer
- Missing model reuse (duplicate schemas)
- Improper Config/model_config usage
- **Stack-specific**: Checkpoint models, API request/response models, stage data models

### C) Async Patterns
- Blocking calls in async functions
- Missing `await` on coroutines
- Improper async context manager usage
- **Stack-specific**: Synchronous Docling calls blocking event loop, file I/O without run_in_executor

### D) Resource Management
- Missing context managers for resources
- Database connections not properly managed
- File handles not closed
- **Stack-specific**: Checkpoint file handling, SQLite connection lifecycle, temporary image files

---

## 8) Pipeline-Specific Architecture (Stack-Specific)

### A) Stage Isolation
- Stages with hidden dependencies on each other
- Shared state between stages without explicit passing
- Stages modifying input data instead of returning new data
- **Stack-specific**: Stage N assuming Stage N-1 output shape, global document state mutation

### B) Checkpoint Integrity
- Checkpoint format not self-describing
- Missing checksums or validation
- No atomic write guarantees
- **Stack-specific**: Partial checkpoint writes, schema version not stored, no rollback capability

### C) Coordinate System Consistency
- Mixed coordinate systems (PDF vs pixel vs normalized)
- Transformation logic duplicated
- Missing origin documentation
- **Stack-specific**: Docling coordinates vs display coordinates vs Label Studio coordinates

### D) Export Format Coupling
- Export logic tightly coupled to internal representation
- Format-specific code scattered through codebase
- Missing format abstraction
- **Stack-specific**: Markdown export knowing internal structure, JSON export duplicating logic

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | LOW]

Location: FileName : Line Number(s)
Risk Category: Boundaries | Layering | Errors | Debt | Types | Frontend | Backend | Pipeline

The Problem:
- 2-4 sentences explaining the architectural violation or quality issue.
- Be specific about impact: maintainability, testability, defect risk, developer velocity.

Technical Debt Impact:
- Estimate effort to fix: Trivial (<1hr) | Small (1-4hr) | Medium (1-2 days) | Large (1 week+)
- Estimate impact if unfixed: Low | Medium | High | Critical
- Confidence: High | Medium | Low

Code Smell Indicators:
- List specific violations (e.g., "500+ lines", "3 levels of nesting", "5 responsibilities")

The Fix:
- Provide the refactored approach or code snippet.
- Show the target structure/pattern.
- If refactor is large, show the strategy not full implementation.

Trade-off Consideration:
- Note complexity, risk of refactor, and any breaking changes.
- If acceptable short-term, mark as LOW with refactor trigger.
```

## Severity Classification
- **CRITICAL**: Fundamental architecture issue blocking development or causing cascading problems.
- **HIGH**: Significant maintainability or testability issue; will compound quickly.
- **MEDIUM**: Code smell that increases cognitive load and defect risk.
- **LOW**: Minor inconsistency or style issue; fix opportunistically.

---

## Architecture Health Score Rubric (1-10)

Rate overall architectural health based on severity/quantity and systemic risks:
- **9-10**: Clean architecture; minor improvements only.
- **7-8**: Good structure with 1-2 areas needing attention.
- **5-6**: Noticeable tech debt; refactoring needed before major features.
- **3-4**: Significant architectural issues; development velocity impacted.
- **<3**: Fundamental restructuring required; high defect risk.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (blocking development or high defect risk)
2) Fix Soon (before next major feature)
3) Fix Opportunistically (during related work)
4) Document/Accept (known limitations with clear rationale)

## Also include:
- Estimated effort for all Fix Now items (range is fine)
- Metrics to track architecture health:
  - Module size distribution (files >300 lines)
  - Cyclomatic complexity per module
  - Import depth / dependency graph analysis
  - Type coverage percentage
  - Test coverage per module
  - Duplication percentage
- Recommended tooling:
  - Python: `ruff`, `mypy --strict`, `radon` (complexity), `vulture` (dead code)
  - TypeScript: `eslint`, `tsc --strict`, `madge` (circular deps)
  - Both: `sonarqube` or `codeclimate` for continuous tracking
