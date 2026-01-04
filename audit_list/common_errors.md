# Common Errors Log

> Running log of actual errors discovered during AI-assisted development ("Vibe Coding")

**Numbering Convention:** Sections are labeled A, B, C, etc. Entries within each section use section-scoped numbers (A.1, A.2, B.1, B.2, etc.). This allows adding entries to a section without renumbering the entire document.

**Note (2026-01-03):** Adapted for SAM3 project. Removed document-processing-specific sections (PDF coordinates, Docling library errors, TypeScript patterns). Error handling and FastAPI patterns extracted to CLAUDE.md § Common Pitfalls.

---

## B. Configuration & Hardcoded Values Errors

### B.1 Frontend Options Not Passed to Backend
**File:** API call sites in frontend (e.g., fetch/axios calls), corresponding backend endpoint handlers
**Issue:** User selects options in UI (model type, processing flags, thresholds) but backend ignores them - uses hardcoded defaults instead
**Fix:** Audit the full data path: (1) UI state captures user selection, (2) API call includes parameter in request body/query, (3) Backend endpoint extracts and uses parameter, (4) Processing function receives and applies parameter
**Pattern:** UI and backend are developed separately; UI adds configurable option but API call isn't updated to pass it, or backend endpoint ignores the parameter and uses hardcoded value. Feature appears to work (backend runs with defaults) so bug goes unnoticed until user wonders why their selection has no effect. Watch for: dropdown/checkbox that "does nothing", fetch calls with incomplete request bodies, backend functions with default parameter values that are never overridden, config options that work in direct API testing but not through UI.

### B.2 Stale Hardcoded Counts and Name Mappings
**File:** Any file with hardcoded limits, counts, or name mappings (e.g., lookup tables, limit checks, ID-to-name maps)
**Issue:** Feature works for some items but fails for others - hardcoded values don't match current system state
**Fix:** Update all hardcoded values to match current configuration; consider centralizing such values in a single source of truth
**Pattern:** When adding/removing items from a system (stages, features, endpoints, etc.), hardcoded references scattered across the codebase become stale. Watch for: numeric limits (`> N`), lookup maps, ID references, and props not passed through component layers.

### B.3 Duplicated Mappings with Naming Convention Mismatches
**File:** Any file with copy-pasted lookup tables or ID mappings (e.g., `STAGE_CHECKPOINT_MAP` in Stage.tsx, Sidebar.tsx, ReadingOrder.tsx)
**Issue:** Feature works for some items but silently fails for others - some entries match while others use wrong naming convention
**Fix:** Centralize the mapping in a single file (e.g., types/index.ts) and import everywhere; verify convention matches the target system (file names vs route IDs)
**Pattern:** When the same mapping exists in multiple files, each copy may use different naming conventions. In this codebase: **route/API IDs use hyphens** (`layout-raw`), **checkpoint file names use underscores** (`layout_raw_done`). Items with single-word names (like `ocr`) work everywhere, masking the bug for multi-word items. Watch for: duplicated `Record<>` or `Map` definitions, mixed hyphen/underscore usage, tests passing for simple cases but failing for complex ones.

### B.4 Stale Enum Lookups After Refactoring
**File:** Any file that uses enum values for dictionary lookups or pattern matching after the enum was refactored
**Issue:** Feature silently fails or returns 404/400 - code looks up old enum values but new values are being stored
**Fix:** Update all lookup sites to check for new enum values first, with old values as fallbacks for backward compatibility
**Pattern:** When an enum is refactored to add new values (while keeping old values for backward compatibility), lookup code may still reference only the old values:
```python
# Old code (before refactoring) - only knows about LAYOUT_DETECTION_*
checkpoint = (
    state.checkpoints.get(ProcessingStage.LAYOUT_DETECTION_MODIFIED) or
    state.checkpoints.get(ProcessingStage.LAYOUT_DETECTION_DONE)
)

# ❌ Problem: Pipeline now saves LAYOUT_RAW_DONE, but lookup still uses old names
# No compile error because old enum values still exist for backward compatibility!

# ✅ Fixed: Check new names first, fallback to old for backward compatibility
checkpoint = (
    state.checkpoints.get(ProcessingStage.LAYOUT_RAW_MODIFIED) or
    state.checkpoints.get(ProcessingStage.LAYOUT_RAW_DONE) or
    state.checkpoints.get(ProcessingStage.LAYOUT_DETECTION_MODIFIED) or
    state.checkpoints.get(ProcessingStage.LAYOUT_DETECTION_DONE)
)
```
This is especially insidious because:
- Old enum values exist (for backward compatibility), so no import/compile errors
- Feature "works" for old data, fails only for new data
- Error message is misleading ("not found" when item exists under different key)

Watch for: enum refactorings that add new values while keeping old ones, dictionary lookups using enum keys, any feature that "stopped working" after a refactoring but has no error at compile time.
**Fixed in:** `backend/api/endpoints/labelstudio/export.py` - Added `LAYOUT_RAW_MODIFIED` and `LAYOUT_RAW_DONE` lookups before legacy fallbacks (lines 78-79)

---

## C. Error Handling Anti-Patterns

### C.1 Silent Exception Swallowing
**File:** Any file with try/except blocks, error handlers, or async operations
**Issue:** Feature silently fails or returns incomplete data - exceptions are caught and suppressed without logging or re-raising
**Fix:** Always log caught exceptions; re-raise or return explicit error states; use `except Exception as e` with `logger.error(f"...: {e}")` at minimum
**Pattern:** Bare `except:` or `except Exception: pass` blocks hide failures, making debugging impossible. Common in: data parsing (returns `None` or `{}`), API calls (returns default instead of error), async handlers (swallows errors silently), fallback logic (masks root cause). Watch for: empty except blocks, catch-all handlers without logging, functions that "never fail" but return suspicious defaults, try/except around optional features that should still report issues.

### C.2 Exception Logged Without Stack Trace
**File:** Any file with try/except blocks that log exceptions
**Issue:** Exceptions are logged but debugging is impossible - only the exception message is captured, not the stack trace
**Fix:** Add `exc_info=True` to logging calls: `_log.warning(f"Operation failed: {e}", exc_info=True)`
**Pattern:** Developers log the exception message but forget `exc_info=True`, losing the stack trace that shows WHERE the error occurred:
```python
# ❌ Useless for debugging - only shows "Connection refused"
except Exception as e:
    _log.warning(f"Operation failed: {e}")

# ✅ Full stack trace - shows the exact line and call chain
except Exception as e:
    _log.warning(f"Operation failed: {e}", exc_info=True)
```
This is especially problematic when:
- The exception could originate from multiple code paths (ML models, file I/O, network)
- The feature is "optional" so the code continues after catching (enrichment, classification)
- Errors happen intermittently in production but can't be reproduced locally

Watch for: `_log.warning/error(f"... {e}")` without `exc_info=True`, except blocks that log and continue, "optional" feature handlers that catch broadly.
**Fixed in:** `backend/core/intercepting_pipeline/stage_executor/enrichment_stage_runners.py` - Added `exc_info=True` to enrichment failure warnings (lines 89, 172, 254)

### C.3 WARNING Level for Expected Conditions
**File:** Any file with logging in conditional paths (file existence checks, optional feature detection, fallback logic)
**Issue:** Log files flooded with warnings for normal operation - real errors get buried in noise
**Fix:** Use DEBUG for expected conditions; reserve WARNING for unexpected-but-recoverable situations
**Pattern:** Developers use WARNING for "didn't find what we looked for" even when not finding it is a normal, expected case:
```python
# ❌ Generates 100+ warnings per pipeline run for expected behavior
if not path.exists():
    _log.warning(f"Checkpoint not found: {path}")
    return None  # Fallback to default - this is EXPECTED

# ✅ DEBUG for expected conditions
if not path.exists():
    _log.debug(f"Checkpoint not found: {path} (expected for optional stages)")
    return None
```
Log level guidelines:
- **DEBUG**: Expected conditions, "file not found" when file is optional, fallback paths
- **INFO**: Successful operations, state changes
- **WARNING**: Unexpected but recoverable situations (e.g., retry succeeded after failure)
- **ERROR**: Failures that affect functionality

Watch for: WARNING logs that appear 10+ times per operation, "not found" warnings for optional resources, fallback logic that logs warnings before returning defaults.
**Fixed in:** `backend/core/intercepting_pipeline/checkpoint_handler/handler.py` - Changed `_log.warning()` to `_log.debug()` for optional checkpoint file checks

---

## D. Import & Module Structure Errors

### D.1 Circular Import via Eager `__init__.py` Exports
**File:** `__init__.py` files that eagerly re-export from submodules crossing package boundaries
**Issue:** `ImportError: cannot import name 'X' from partially initialized module`
**Fix:** Use lazy imports (import inside functions) with comment: `# Import here to avoid circular imports`
**Pattern:** Cycles span multiple `__init__.py` files. Watch for: eager `from .submodule import *`, cross-package imports at module level, errors only when importing from package level.
**Fixed in:** `backend/services/reading_order/import_.py` - moved `CheckpointIO` import inside function

### D.2 Layer Violation: Core Depending on Services
**File:** Core modules (`backend/core/*`) importing from service modules (`backend/services/*`)
**Issue:** Fragile import order; services should depend on core, not vice versa
**Fix:** Move shared utilities to core layer; services re-exports from core for backward compatibility
**Pattern:** Proper layering: `models` → `core` → `services` → `api`. Watch for: `from backend.services.X` in `backend/core/` files.
**Fixed:** Moved bbox validation from `services/coordinates/validation.py` → `core/checkpoint/validation.py`

### D.3 Barrel Export Bypass
**File:** New files importing from modules that use barrel exports (`utils/`, `types/`, `components/ui/`, etc.)
**Issue:** Import works initially but breaks if internal file is renamed/moved; inconsistent with codebase patterns
**Fix:** Import from the barrel export (directory index), not the internal file directly
**Pattern:** When creating new files, developers guess import paths instead of checking sibling files. Direct imports bypass the public API:
```typescript
// ❌ Direct import - fragile, breaks if websocket.ts is renamed
import { wsManager } from '../../utils/wsManager';

// ✅ Barrel import - stable, follows codebase pattern
import { wsManager } from '../../utils';
```
Watch for: imports with extra path segments (`utils/specificFile` vs `utils/`), new files with different import patterns than siblings, imports that reference non-existent files (file was renamed but import guessed old name).
**Prevention:** Before adding imports in new files, check how sibling files in the same directory import the same modules. Use the shortest path that works (barrel export).
**Fixed in:** `frontend/src/pages/hooks/useBatchRunner.ts` - Changed `../../utils/wsManager` to `../../utils`

---

## G. FastAPI Parameter Errors

### G.1 Optional Wrapper on FastAPI Injectable Types
**File:** Any FastAPI endpoint with `Request`, `WebSocket`, `Response`, `BackgroundTasks`, or `SecurityScopes` parameters
**Issue:** `FastAPIError: Invalid args for response field!` at module import time - endpoint registration fails before server starts
**Fix:** Remove the `Optional` wrapper; these types must be required parameters that FastAPI injects automatically
**Pattern:** FastAPI has special injectable types that it recognizes and auto-injects. When wrapped in `Optional[Type] = None`, FastAPI's parameter analyzer tries to treat them as Pydantic body fields, which fails:
```python
# ❌ Breaks - FastAPI can't create a Pydantic field from Request
async def endpoint(request: Optional[Request] = None):
    ...

# ✅ Works - FastAPI recognizes and injects automatically
async def endpoint(request: Request):
    ...
```
Affected types: `Request`, `WebSocket`, `Response`, `HTTPConnection`, `BackgroundTasks`, `SecurityScopes`

Watch for: endpoints that need to be called both via HTTP and internally (batch executors, testing); the misleading error says "response field" but the problem is in parameters; error occurs at import time, not runtime.

**Prevention:** If you need both HTTP and internal calls, separate business logic from the endpoint handler:
```python
# Business logic (can be called internally)
async def _process_data(doc_id: str, options: Options):
    ...

# HTTP endpoint (thin wrapper with injectable types)
@router.post("/{doc_id}/process")
async def process_endpoint(doc_id: str, request: Request, options: Options = None):
    check_rate_limit(request)
    return await _process_data(doc_id, options)
```
**Fixed in:** `backend/api/endpoints/pipeline_stages/stage_2_preprocessing.py`, `stage_3_ocr.py` - Removed `http_request: Optional[Request] = None` parameter, aligned with pattern used in stages 4-14

### G.2 Positional Argument Mismatch When Calling Functions Internally
**File:** Any file that calls endpoint handlers or functions with multiple optional parameters internally (batch executors, tests, internal utilities)
**Issue:** Code compiles and runs without error, but wrong parameter receives the value - causes silent misbehavior instead of clear error
**Fix:** Use explicit keyword arguments when calling functions with multiple optional parameters: `handler(doc_id, request=options)` not `handler(doc_id, options)`
**Pattern:** When calling functions internally that were designed for external API use, parameter ordering assumptions break:
```python
# Function signature has multiple optional params
async def run_stage(doc_id: str, http_request: Request = None, request: StageRunRequest = None):
    ...

# ❌ Silent bug - options goes to http_request, not request!
await handler(doc_id, options)

# ✅ Explicit keyword argument - options goes to correct parameter
await handler(doc_id, request=options)
```
This is especially dangerous when:
- Internal code calls HTTP endpoint handlers (batch execution, testing)
- Functions have similar-sounding parameter names (`request` vs `http_request`)
- All parameters have defaults, so missing arguments don't raise errors
- The wrong parameter receives a value it can technically accept (both are Optional)

Watch for: batch executors calling individual handlers, test utilities calling API functions, any internal call to functions with 2+ optional parameters, silent failures where "options have no effect".

**Prevention:**
1. Always use keyword arguments when calling functions with multiple optional parameters
2. Add comment explaining parameter routing: `# Use keyword arg to target 'request' param, not 'http_request'`
3. Consider separate internal functions from HTTP handlers (thin wrapper pattern from G.1)

**Fixed in:** `backend/api/endpoints/run_remaining.py` line 256 - Changed `await handler(doc_id, options)` to `await handler(doc_id, request=options)` in batch executor
