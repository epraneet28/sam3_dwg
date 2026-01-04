# Checkpoint & State Integrity Audit Prompt (15-Stage Pipeline Focus)

## Role
Act as a Senior Data Engineer and Distributed Systems Architect specializing in state management and data integrity. Perform a deep-dive Checkpoint & State Integrity Audit on the provided codebase to ensure data durability, consistency, and recoverability across all 15 pipeline stages.

## Primary Goal
Identify where AI-generated checkpoint logic, state serialization shortcuts, and integrity gaps will cause data loss, corruption, or inconsistency, and provide concrete fixes that make the system production-ready.

## Context
- This is a 15-stage document processing pipeline with checkpoint saves at each stage.
- Checkpoints are JSON-based state serialization files storing pipeline state.
- The system must support:
  - Resume from any stage after interruption
  - Concurrent document processing
  - Manual stage edits persisted correctly
  - Cross-stage data consistency
- This code was developed with AI assistance ("vibecoded") and checkpoint integrity has not been stress-tested.

## Tech Stack
- **Backend**: Python 3.12 + FastAPI + Uvicorn
- **State Persistence**: SQLite3 (metadata) + JSON files (checkpoints)
- **Data Validation**: Pydantic v2
- **Document Processing**: Docling engine
- **Image Processing**: OpenCV, Pillow, pdf2image
- **Real-time Updates**: WebSockets
- **Frontend State**: Zustand (React 19)
- **Infrastructure**: Docker (python-slim)

## Pipeline Stages (15 total)
1. Upload, 2. Preprocessing, 3. OCR, 4. Layout Raw, 5. Cell Assignment, 6. Table Structure Raw, 7. Table Cell Matching, 8. Page Assembly, 9. Reading Order, 10. Caption/Footnote, 11. Merge Prediction, 12. Code/Formula, 13. Picture Classification, 14. Picture Description, 15. Export

## Integrity Requirements
- Zero data loss on crash/restart
- Atomic checkpoint writes (no partial/corrupt files)
- Schema version compatibility (forward/backward)
- Cross-stage consistency validation
- Orphaned file cleanup
- Concurrent access safety (SQLite + file system)

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (checkpoint directory structure, schema definitions, SQLite schema, Pydantic models), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - Checkpoint file structure (directory layout, naming convention)
   - Schema versioning strategy (if any)
   - Write patterns (direct write vs atomic rename)
   - SQLite usage patterns (connection management, transactions)
   - Pydantic model hierarchy for checkpoint data
   - Error recovery mechanisms
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) Schema Versioning & Migration

### A) Missing Schema Version Field
- Look for checkpoint JSON structures without a `schema_version` or `version` field.
- Flag Pydantic models that lack version tracking.
- **Failure Mode**: After code updates, old checkpoints become unreadable or silently lose data.
- Suggested Fix: Add `schema_version: str` to all checkpoint models; implement version-aware deserialization.

### B) No Migration Strategy
- Identify checkpoint loading code without version checks or migration logic.
- Flag hard assumptions about field presence/types.
- **Failure Mode**: Pipeline crashes on old checkpoints after schema evolution.
- Suggested Fix: Implement versioned loaders with migration functions; use `Optional` fields with defaults.

### C) Breaking Schema Changes
- Look for field renames, type changes, or removed fields without migration.
- Flag Pydantic models with `Field(...)` requirements that changed between versions.
- **Failure Mode**: `ValidationError` on checkpoint load after updates.
- Suggested Fix: Maintain backward-compatible aliases; provide explicit migration scripts.

### D) Enum/Literal Type Drift
- Check for Enum or Literal types in checkpoint models that may have added/removed values.
- **Failure Mode**: Old checkpoints with deprecated enum values fail validation.
- Suggested Fix: Use permissive parsing with fallback; validate enums explicitly with graceful degradation.

---

## 2) Atomic Write Patterns

### A) Direct File Writes (Non-Atomic)
- Look for `open(path, 'w')` followed by `json.dump()` or `write()` without rename pattern.
- Flag checkpoint saves that don't use write-then-rename (atomic pattern).
- **Failure Mode**: Power loss or crash during write = corrupt/truncated checkpoint.
- Suggested Fix: Write to temp file, then `os.replace()` (atomic on POSIX).

```python
# BAD - Non-atomic
with open(checkpoint_path, 'w') as f:
    json.dump(data, f)

# GOOD - Atomic
temp_path = checkpoint_path + '.tmp'
with open(temp_path, 'w') as f:
    json.dump(data, f)
    f.flush()
    os.fsync(f.fileno())
os.replace(temp_path, checkpoint_path)
```

### B) Missing fsync/Flush
- Look for file writes without `f.flush()` and `os.fsync(f.fileno())`.
- **Failure Mode**: Data in OS buffer not persisted on crash.
- Suggested Fix: Explicit flush + fsync before rename.

### C) Directory Sync (Optional Hardening)
- For maximum durability, check if parent directory fd is fsync'd after rename.
- **Note**: Usually not needed for SQLite + JSON hybrid, but flag if critical data.

### D) Partial Update Patterns
- Look for code that modifies checkpoint incrementally (read-modify-write).
- Flag patterns where failure between read and write leaves inconsistent state.
- Suggested Fix: Always write complete checkpoint; use journaling for incremental updates.

---

## 3) Corruption Detection & Recovery

### A) No Checksum/Hash Validation
- Look for checkpoint loads without integrity verification.
- Flag missing SHA-256/CRC32 checksums in checkpoint structure or sidecar files.
- **Failure Mode**: Silent data corruption goes undetected.
- Suggested Fix: Add `checksum` field; validate on load; reject corrupted checkpoints.

```python
import hashlib

def compute_checksum(data: dict) -> str:
    content = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(content).hexdigest()

def save_checkpoint(path: str, data: dict):
    data['_checksum'] = compute_checksum({k: v for k, v in data.items() if k != '_checksum'})
    # ... atomic write ...

def load_checkpoint(path: str) -> dict:
    data = json.load(...)
    stored = data.pop('_checksum', None)
    computed = compute_checksum(data)
    if stored and stored != computed:
        raise CorruptedCheckpointError(f"Checksum mismatch: {path}")
    return data
```

### B) No Backup/Previous Version Retention
- Look for checkpoint saves that overwrite without keeping previous version.
- **Failure Mode**: Corrupt save with no recovery option.
- Suggested Fix: Keep N previous versions (e.g., `.bak`, `.prev`); implement rotation.

### C) JSON Parsing Without Error Handling
- Flag `json.load()` without try/except for `JSONDecodeError`.
- **Failure Mode**: Crash on truncated/corrupt checkpoint.
- Suggested Fix: Graceful handling with fallback to backup.

### D) Pydantic Validation Failures
- Check for checkpoint load without handling `ValidationError`.
- **Failure Mode**: Single malformed field crashes entire load.
- Suggested Fix: Implement staged validation with partial recovery.

---

## 4) Orphaned Checkpoint Cleanup

### A) No Cleanup on Document Deletion
- Look for document deletion code that doesn't remove checkpoint files.
- Flag SQL DELETE without corresponding file cleanup.
- **Failure Mode**: Disk fills with orphaned checkpoint directories.
- Suggested Fix: Transactional cleanup - delete files then DB record (or vice versa with cleanup job).

### B) Orphaned Temp Files
- Look for `.tmp` files that may remain after failed writes.
- Flag missing cleanup of temporary files on startup or shutdown.
- Suggested Fix: Implement startup cleanup of stale `.tmp` files older than threshold.

### C) Orphaned Stage Checkpoints
- After pipeline completion/export, check if intermediate stage checkpoints are cleaned.
- Flag accumulation of all 15 stage checkpoints when only final state needed.
- Suggested Fix: Configurable retention policy; cleanup job for completed documents.

### D) Directory Structure Orphans
- Look for document directories without corresponding SQLite records.
- Flag inconsistency between DB state and filesystem state.
- Suggested Fix: Reconciliation job that syncs DB and filesystem.

---

## 5) Cross-Stage Consistency Validation

### A) Missing Stage Dependency Validation
- Each stage should validate required data from previous stages exists.
- Flag stages that assume previous stage data without verification.
- **Failure Mode**: Stage 7 runs with missing Stage 6 data = silent data loss.
- Suggested Fix: Explicit stage prerequisites check; fail fast with clear errors.

### B) Element ID Consistency
- Bounding boxes, elements, and cells should have stable IDs across stages.
- Flag ID generation that could produce duplicates or gaps.
- **Failure Mode**: Element references break after manual edits.
- Suggested Fix: UUID-based IDs; ID stability validation between stages.

### C) Coordinate System Drift
- Check that coordinate systems (PDF coords vs image coords) are consistent.
- Flag transformations without clear coordinate space tracking.
- **Failure Mode**: Bounding boxes misaligned after stage processing.
- Suggested Fix: Explicit coordinate system field; validation on stage transitions.

### D) Page Count Consistency
- Total pages should be consistent across all stage checkpoints.
- Flag stages that could silently drop or add pages.
- Suggested Fix: Page count validation; explicit page exclusion tracking.

### E) Referential Integrity
- Elements referencing other elements (captions→figures, cells→tables) must be valid.
- Flag references to non-existent element IDs.
- Suggested Fix: Reference validation on checkpoint save; broken reference detection.

---

## 6) SQLite Concurrency & State Sync

### A) SQLite Write Lock Conflicts
- Look for long-running SQLite transactions that block concurrent operations.
- Flag missing WAL mode configuration.
- **Failure Mode**: "Database is locked" errors during concurrent document processing.
- Suggested Fix: Enable WAL mode; minimize transaction scope; use connection pooling.

```python
# On database initialization
connection.execute("PRAGMA journal_mode=WAL;")
connection.execute("PRAGMA busy_timeout=5000;")
```

### B) DB-File State Inconsistency
- Look for code that updates SQLite and filesystem separately.
- Flag non-transactional updates across DB and checkpoints.
- **Failure Mode**: DB says "completed" but checkpoint file missing.
- Suggested Fix: Update checkpoint file first, then DB; implement consistency checks.

### C) Connection Lifecycle Issues
- Check for SQLite connections opened but not closed properly.
- Flag missing connection cleanup in error paths.
- Suggested Fix: Use context managers; connection pool with proper cleanup.

### D) Race Conditions in Status Updates
- Look for check-then-update patterns without locking.
- Flag concurrent stage transitions without synchronization.
- Suggested Fix: Atomic status updates; optimistic locking with version field.

---

## 7) Frontend State Synchronization (Zustand + WebSocket)

### A) Stale State After Checkpoint Save
- Frontend Zustand state may not reflect latest checkpoint after backend save.
- Flag missing WebSocket notifications on checkpoint updates.
- **Failure Mode**: UI shows old data after backend processing.
- Suggested Fix: WebSocket broadcast on checkpoint save; optimistic UI updates with reconciliation.

### B) Conflicting Edits
- Manual UI edits may conflict with background processing updates.
- Flag missing conflict detection/resolution strategy.
- **Failure Mode**: User edits silently overwritten by backend.
- Suggested Fix: Version-based conflict detection; last-write-wins with notification or merge UI.

### C) Zustand Persistence Integrity
- If Zustand persists to localStorage/sessionStorage, check for corruption handling.
- Flag missing validation on hydration.
- Suggested Fix: Validate persisted state; clear on validation failure.

---

## 8) Pydantic Model Integrity

### A) Optional Fields Without Defaults
- Look for `Optional[T]` fields without `= None` default.
- Flag fields that are Optional but required in JSON.
- **Failure Mode**: Old checkpoints missing field cause ValidationError.
- Suggested Fix: Always provide defaults for Optional fields.

### B) Model Inheritance Issues
- Check for Pydantic model inheritance that could break serialization.
- Flag discriminated unions without proper type field.
- **Failure Mode**: Polymorphic checkpoint data fails to deserialize correctly.
- Suggested Fix: Use discriminated unions with `Literal` type field.

### C) Custom Validators on Load
- Look for `@validator` or `@field_validator` that may reject valid historical data.
- Flag validators that enforce rules added after initial data creation.
- **Failure Mode**: Validator rejects old checkpoint data.
- Suggested Fix: Use `mode='before'` validators with lenient parsing; separate validation from parsing.

### D) Serialization Round-Trip Integrity
- Check that `model.model_dump()` -> JSON -> `Model.model_validate()` preserves all data.
- Flag custom `json_encoders` or `model_serializer` that lose information.
- Suggested Fix: Unit tests for serialization round-trips; explicit preservation tests.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s)
Risk Category: Schema | Atomicity | Corruption | Orphans | Consistency | Concurrency | Frontend | Pydantic

The Problem:
- 2-4 sentences explaining the data integrity risk.
- Be specific about failure mode: data loss, silent corruption, inconsistency, crash on load, orphaned files, etc.

Data Impact:
- Provide realistic impact estimate (example: "Checkpoint loss on 1 in 1000 saves", "Orphaned files grow 100MB/month", "Cross-stage inconsistency in 5% of complex documents").
- Include Confidence: High | Medium | Low

How to Verify:
- Concrete verification step (simulate crash during write, inject corrupt checkpoint, concurrent write test, orphan scan, round-trip test).

The Fix:
- Provide the optimized code snippet.
- Show before/after if useful.
- If fix requires config/infrastructure change, specify exactly where.

Trade-off Consideration:
- Note complexity, performance impact, and any risks (e.g., "Checksums add 5ms per save but catch 100% of corruption").
- If acceptable at current scale, mark as MONITOR with what threshold triggers refactor.
```

## Severity Classification
- **CRITICAL**: Will cause data loss, corruption, or unrecoverable state (non-atomic writes, no checksum, broken references).
- **HIGH**: Significant integrity risk under stress or edge cases (orphan accumulation, race conditions).
- **MEDIUM**: Data quality issues or recoverable inconsistencies (missing validation, stale frontend state).
- **MONITOR**: Minor risks acceptable at current scale; watch metrics.

---

## Integrity Score Rubric (Data Safety 1-10)

Rate overall checkpoint/state integrity based on severity/quantity and systemic risks:
- **9-10**: Production-ready; atomic writes, checksums, schema versioning, cleanup jobs all in place.
- **7-8**: Mostly safe; 1-2 critical fixes needed for production.
- **5-6**: Significant gaps; data loss possible under edge cases.
- **3-4**: Multiple critical issues; high risk of corruption or loss.
- **<3**: Do not use for production data; fundamental integrity issues.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (before production/user data)
2) Fix Soon (next iteration)
3) Monitor (metrics + thresholds)

## Also include:
- Estimated time to implement all Fix Now items (range is fine)
- Infrastructure/tooling to add:
  - Integrity Checks: Checksum validation on load, schema version tracking
  - Cleanup Jobs: Orphan detection, temp file cleanup, retention policy
  - Monitoring: Failed checkpoint loads, orphan file count, schema migration success rate
  - Testing: Corruption injection tests, crash recovery tests, concurrent write tests
  - Recommended test scenarios:
    - Kill process during checkpoint write → verify recovery
    - Inject corrupt JSON → verify graceful handling
    - Run concurrent document processing → verify no conflicts
    - Simulate schema migration → verify old checkpoints load
