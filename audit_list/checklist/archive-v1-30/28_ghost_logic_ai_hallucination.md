# "Ghost Logic" & AI Hallucination Audit Prompt (Vibe Code Verification)

## Role
Act as a Senior Code Auditor specializing in AI-assisted development. Perform a comprehensive "Ghost Logic" & AI Hallucination Audit to identify code that was incorrectly generated, uses non-existent APIs, or contains unrequested features that slipped in during AI-assisted development.

## Primary Goal
Identify where AI-generated code makes incorrect assumptions about libraries, uses deprecated/non-existent APIs, or includes "phantom" features that were never requested. Ensure the codebase only contains intentional, functional code.

## Context
- This codebase was developed with AI assistance ("vibecoded") and may contain hallucinated library methods, incorrect API usage, or features that were never requested.
- AI models can confidently generate code using APIs that don't exist in the installed versions or have been deprecated.
- "Ghost logic" refers to code blocks that appear functional but serve no actual purpose or are disconnected from the rest of the application.

## Tech Stack
- **Backend**: Python 3.12 + FastAPI + Uvicorn
- **Document Processing**: Docling (document AI engine)
- **Data Validation**: Pydantic v2
- **Database**: SQLite3
- **Image Processing**: OpenCV, Pillow, pdf2image
- **External Integration**: Label Studio SDK
- **Real-time**: WebSockets (native FastAPI)
- **Frontend**: React 19 + TypeScript 5.9
- **Build**: Vite 7
- **Styling**: Tailwind CSS 4
- **State**: Zustand
- **Routing**: React Router DOM 7
- **Testing**: Playwright, pytest

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
For each file, cross-reference imported modules against their actual installed versions and documented APIs.

## Environment & Assumptions (you must do this first)
1) Extract and list:
   - All imported packages and their versions from requirements.txt / package.json
   - Any custom modules that may reference external libraries
   - Environment configuration files that may affect behavior
2) For each major library (Docling, FastAPI, Pydantic, React, Zustand), note the specific version and any breaking changes between versions.
3) If version cannot be determined, mark as "Needs Version Verification" and list what to check.

---

## Audit Requirements

Scan the files and generate a report identifying instances of the risks below.
Include "Suspicious Patterns" when something looks like it could be hallucinated but requires confirmation.

---

## 1) Import & API Hallucinations

### A) Non-Existent Library Methods
- Look for method calls that don't exist in the installed library version.
- Common hotspots:
  - Docling: `DocumentConverter`, `ConversionResult`, pipeline methods
  - FastAPI: Middleware patterns, dependency injection, WebSocket handlers
  - Pydantic v2: Model validators, field configurations, serialization methods
  - React 19: New hooks, component patterns, concurrent features
- Verification: Cross-reference each import with official documentation for that version.
- Suggested Fix: Replace with actual API, or implement wrapper if functionality is needed.

### B) Deprecated API Usage
- Identify calls to deprecated methods that may work now but will break.
- Common hotspots:
  - Pydantic v1 → v2 migration patterns (e.g., `@validator` vs `@field_validator`)
  - React class components or legacy lifecycle methods
  - FastAPI deprecated parameters or patterns
- Suggested Fix: Update to current API, add deprecation warnings for tracking.

### C) Version-Specific API Mismatches
- Code written for a different library version than what's installed.
- Example: Using React 19 features when React 18 is installed, or Pydantic v2 syntax with v1.
- Verification: Compare `package.json` / `requirements.txt` versions against code usage.
- Suggested Fix: Either upgrade library or rewrite to match installed version.

### D) Phantom Import Statements
- Imports that are never used in the file.
- Imports of modules that don't exist in the project or dependencies.
- Suggested Fix: Remove unused imports, verify module paths.

---

## 2) Docling-Specific Hallucinations

### A) Non-Existent Docling Pipeline Methods
- Check all Docling API calls against the actual Docling documentation.
- Common hallucinations:
  - `doc.get_elements()` vs actual element access patterns
  - Pipeline stage names that don't exist
  - Conversion options that aren't supported
  - Model configuration parameters that don't exist
- Verification: Import Docling in REPL and check `dir()` on objects.
- Suggested Fix: Use actual Docling API from documentation.

### B) Incorrect Docling Data Structures
- Assuming Docling returns data in a format it doesn't.
- Common issues:
  - Accessing `.text` on objects that use `.content`
  - Assuming bounding box format (x,y,w,h vs x1,y1,x2,y2)
  - Incorrect page/element hierarchy assumptions
- Suggested Fix: Print actual Docling output, update code to match.

### C) Fabricated Docling Configuration Options
- Pipeline options, model settings, or feature flags that don't exist.
- Example: `DocumentConverter(enable_table_detection=True)` when the actual API differs.
- Suggested Fix: Review Docling source code or docs for actual configuration.

---

## 3) FastAPI & Pydantic Hallucinations

### A) Non-Existent FastAPI Patterns
- Middleware that uses incorrect signatures.
- Dependency injection patterns that don't work.
- WebSocket handlers with wrong lifecycle management.
- Response model configurations that don't exist.
- Suggested Fix: Follow FastAPI official documentation patterns.

### B) Pydantic v2 Confusion
- Mixing Pydantic v1 and v2 syntax:
  - `@validator` (v1) vs `@field_validator` (v2)
  - `Config` class (v1) vs `model_config` (v2)
  - `.dict()` (v1) vs `.model_dump()` (v2)
  - `parse_obj()` (v1) vs `model_validate()` (v2)
  - `schema()` (v1) vs `model_json_schema()` (v2)
- Field definitions:
  - `Optional[str] = None` vs `str | None = None`
  - `Field(...)` parameter names that changed
- Suggested Fix: Consistently use Pydantic v2 patterns throughout.

### C) SQLite/Database Hallucinations
- Using ORM methods on raw SQLite connections.
- Async patterns on synchronous SQLite operations.
- Connection pooling patterns that don't apply to SQLite.
- Suggested Fix: Use appropriate SQLite3 patterns, consider aiosqlite if async needed.

---

## 4) React & TypeScript Hallucinations

### A) Non-Existent React 19 Features
- Using hooks or patterns that don't exist in React 19.
- Common hallucinations:
  - Made-up hooks like `useAsyncState`, `useServerData`
  - Incorrect Suspense/concurrent mode patterns
  - Non-existent component lifecycle methods
- Suggested Fix: Verify against React 19 documentation.

### B) Zustand Misuse
- Incorrect store creation patterns.
- Non-existent selector optimization methods.
- Middleware that doesn't exist.
- Common issues:
  - `useStore.getState().property` in render (causes no re-render)
  - Non-existent persistence options
- Suggested Fix: Follow Zustand v4/v5 patterns correctly.

### C) TypeScript Type Hallucinations
- Types that reference non-existent properties.
- Generic constraints that don't match actual library types.
- Utility types used incorrectly.
- Interface definitions that don't match runtime behavior.
- Suggested Fix: Ensure types match actual data structures.

### D) React Router DOM v7 Patterns
- Using patterns from v5/v6 that changed in v7.
- Non-existent loader/action patterns.
- Incorrect route configuration.
- Suggested Fix: Verify against React Router v7 documentation.

---

## 5) Dead Code & Unrequested Features

### A) Orphaned Functions & Components
- Functions defined but never called.
- React components defined but never rendered.
- API endpoints that aren't used by any client code.
- Event handlers attached to nothing.
- Suggested Fix: Remove or document why kept for future use.

### B) Incomplete Feature Implementations
- Feature flags or conditional logic for features that don't exist.
- Half-implemented workflows (e.g., file upload without processing).
- Commented "TODO" blocks with substantial code.
- Suggested Fix: Complete, remove, or document as intentional stub.

### C) Speculative Abstractions
- Overly generic code solving problems that don't exist.
- Factory patterns, strategy patterns, or plugins for single implementations.
- Configuration options that are never used.
- Suggested Fix: Simplify to actual requirements, remove unused flexibility.

### D) Copy-Paste Artifacts
- Duplicate code blocks with slight variations.
- Error messages or comments referencing wrong features.
- Variable names that don't match their purpose.
- Suggested Fix: Consolidate, correct naming, or remove duplicates.

---

## 6) Integration Point Hallucinations

### A) Label Studio SDK Misuse
- Using Label Studio SDK methods that don't exist.
- Incorrect annotation format assumptions.
- Authentication patterns that don't work.
- Project configuration options that aren't supported.
- Suggested Fix: Verify against Label Studio SDK version installed.

### B) WebSocket Protocol Hallucinations
- Custom message types that aren't handled on both ends.
- Reconnection logic that doesn't match server implementation.
- Heartbeat/ping patterns that aren't implemented.
- Suggested Fix: Audit both client and server WebSocket handlers.

### C) File System Operation Hallucinations
- Assuming file paths that don't exist.
- Using OS-specific paths without cross-platform handling.
- File permission assumptions that fail in production.
- Suggested Fix: Use pathlib, verify paths exist, handle errors.

---

## 7) Configuration & Environment Hallucinations

### A) Non-Existent Environment Variables
- Code referencing env vars that aren't defined.
- Default values that mask missing configuration.
- Environment-specific logic for environments that don't exist.
- Suggested Fix: Document all required env vars, add startup validation.

### B) Phantom Dependencies
- Code importing packages not in requirements.txt / package.json.
- Optional imports that silently fail.
- Version constraints that don't match installed versions.
- Suggested Fix: Sync dependency files with actual imports.

### C) Build Configuration Hallucinations
- Vite configuration options that don't exist.
- TypeScript compiler options that aren't valid.
- Test configuration for non-existent test frameworks.
- Suggested Fix: Validate against tool documentation.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | LOW]

Location: FileName : Line Number(s)
Risk Category: Import Hallucination | API Misuse | Dead Code | Integration | Configuration

The Problem:
- 2-4 sentences explaining the hallucination or ghost logic.
- Identify what the code assumes vs what actually exists.
- Note confidence level in the finding.

Evidence:
- Show the problematic code.
- Reference the actual API documentation or library behavior.
- Confidence: High | Medium | Low

How to Verify:
- Concrete verification step (REPL test, documentation link, version check).

The Fix:
- Provide the corrected code snippet.
- Show before/after if useful.
- If removal is recommended, explain why.

Impact if Unfixed:
- Runtime error, silent failure, security issue, maintenance burden, etc.
```

## Severity Classification
- **CRITICAL**: Code will crash or produce incorrect results. Non-existent API calls.
- **HIGH**: Deprecated APIs that will break, security-relevant hallucinations.
- **MEDIUM**: Dead code, unused features, maintenance burden.
- **LOW**: Minor inconsistencies, style issues, unnecessary complexity.

---

## Hallucination Score Rubric (Code Authenticity 1-10)

Rate overall code authenticity based on hallucination density and severity:
- **9-10**: Minimal hallucinations; code matches actual APIs.
- **7-8**: Few issues; mostly correct API usage with some deprecated patterns.
- **5-6**: Moderate issues; several hallucinated methods or dead code blocks.
- **3-4**: Significant issues; many non-existent APIs or phantom features.
- **<3**: Severe; core functionality relies on hallucinated APIs.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 5 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)

### 1) Fix Immediately (Runtime Errors)
- Non-existent API calls that will crash
- Import errors waiting to happen
- Critical integration hallucinations

### 2) Fix Soon (Correctness Issues)
- Deprecated API usage
- Incorrect data structure assumptions
- Integration mismatches

### 3) Clean Up (Maintenance)
- Dead code removal
- Unused imports
- Speculative abstractions

### 4) Document (For Future Reference)
- Intentional stubs or placeholders
- Version-specific workarounds
- Known limitations

## Also include:

- **Library Version Verification Commands**:
  ```bash
  # Python
  pip show docling fastapi pydantic pillow opencv-python label-studio-sdk

  # Node
  npm ls react react-router-dom zustand
  ```

- **Quick API Verification Snippets**:
  ```python
  # Verify Docling API
  from docling.document_converter import DocumentConverter
  print(dir(DocumentConverter))

  # Verify Pydantic version
  import pydantic
  print(pydantic.VERSION)
  ```

- **Recommended Static Analysis**:
  - `vulture` - Find dead Python code
  - `pylint` - Unused imports and variables
  - `ts-prune` - Find dead TypeScript exports
  - `eslint-plugin-unused-imports` - Unused JS/TS imports

- **Manual Review Checklist**:
  - [ ] All Docling pipeline methods verified against docs
  - [ ] All Pydantic models use v2 syntax
  - [ ] All FastAPI routes have working handler
  - [ ] All React components are rendered somewhere
  - [ ] All TypeScript types match runtime structures
  - [ ] All environment variables are defined
  - [ ] All imports resolve to actual modules
