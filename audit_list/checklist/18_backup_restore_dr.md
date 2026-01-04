---
## Metadata
**Priority Level:** P3 (Lower)
**Original Audit:** #16 Backup/Restore & DR
**Last Updated:** 2025-12-26
**AI/Vibe-Coding Risk Level:** LOW

---

# Backup/Restore & Disaster Recovery Audit Prompt (Production-Ready)

## Role
Act as a Senior Infrastructure Engineer and Disaster Recovery Specialist. Perform a comprehensive Backup/Restore & DR Audit on the provided codebase to ensure business continuity and data protection.

## Primary Goal
Identify gaps in backup strategies, restore procedures, and disaster recovery planning that could lead to data loss or extended downtime, and provide concrete fixes to ensure recoverability.

## Context
- This code was developed with a focus on features ("vibecoded") and backup/DR may have been an afterthought.
- I need you to find all data persistence points and ensure they have proper backup and recovery mechanisms.
- The system processes sensitive documents that users expect to be recoverable.

## Tech Stack
- Backend: Python 3.12 / FastAPI / Uvicorn
- Database: SQLite3 (state persistence)
- File Storage: Local filesystem (checkpoints, uploaded PDFs, extracted images)
- Document Processing: Docling pipeline with 15-stage checkpointing
- External Integration: Label Studio (annotation data)
- Real-time: WebSockets for progress updates

## Recovery Objectives (Use if not provided)
- **RPO (Recovery Point Objective)**: Maximum 1 hour of data loss acceptable
- **RTO (Recovery Time Objective)**: Service restored within 4 hours
- **Data Criticality**: User-uploaded documents and processing checkpoints are high-value

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (storage paths, backup scripts, deployment model), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - All data persistence locations (DB files, checkpoint directories, upload paths)
   - Current backup mechanisms (if any exist)
   - Data retention policies (if defined)
   - Deployment model (single server, containers, cloud storage)
   - External service dependencies requiring backup consideration
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) Backup Existence & Coverage

### A) Database Backup Strategy
- Verify SQLite database has backup mechanism in place.
- Check for WAL mode handling during backups (WAL checkpoint before backup).
- Flag if database is only on local disk with no offsite copy.
- Suggested Fix: Implement scheduled backups with sqlite3 `.backup` command or file copy after WAL checkpoint.

### B) Checkpoint File Backup
- Identify all checkpoint storage locations.
- Verify checkpoints are included in backup scope.
- Check for checkpoint file naming that supports point-in-time recovery.
- Flag orphaned checkpoints without corresponding document records.
- Suggested Fix: Include checkpoint directories in backup, implement retention policy.

### C) Uploaded Document Backup
- Verify original uploaded PDFs are preserved (not just processed outputs).
- Check if upload directory is included in backup scope.
- Flag if processed files are stored but originals are deleted.
- Suggested Fix: Maintain original uploads with backup, implement tiered storage.

### D) Configuration & Secrets Backup
- Verify environment configuration can be reconstructed.
- Check for secrets management (API keys, Label Studio credentials).
- Flag hardcoded configurations that would be lost.
- Suggested Fix: Document all required configuration, use secrets manager, backup env templates.

### E) Label Studio Data Backup
- Identify Label Studio project data and annotations.
- Check if there's a strategy for backing up external service data.
- Flag reliance on external service without local backup.
- Suggested Fix: Implement Label Studio export automation, store annotation backups locally.

---

## 2) Restore Procedures & Testing

### A) Documented Restore Procedure
- Check for restore documentation or runbooks.
- Verify restore steps are actionable (not just "restore from backup").
- Flag if restore has never been tested.
- Suggested Fix: Create step-by-step restore runbook, schedule quarterly restore tests.

### B) SQLite Restore Validation
- Check for database integrity verification after restore.
- Look for `PRAGMA integrity_check` usage.
- Flag if restored database is used without validation.
- Suggested Fix: Add integrity check to restore procedure, verify foreign key consistency.

### C) Checkpoint Restore Consistency
- Verify checkpoint restore maintains processing state consistency.
- Check for orphaned references (checkpoints pointing to deleted documents).
- Flag if partial restores could create inconsistent state.
- Suggested Fix: Implement consistency validation after restore, document dependencies.

### D) Application State Recovery
- Check if in-memory state (active WebSocket connections, processing queues) can be recovered.
- Verify application can cold-start from restored data.
- Flag if application requires manual intervention after restore.
- Suggested Fix: Implement startup recovery logic, document manual steps if needed.

### E) Restore Time Estimation
- Check if restore time has been measured.
- Verify RTO can be met with current restore procedure.
- Flag if large data volumes could exceed RTO.
- Suggested Fix: Measure and document restore times, optimize if needed.

---

## 3) RPO/RTO Definition & Monitoring

### A) Data Loss Window Analysis
- Identify how much data could be lost between backups.
- Check backup frequency against RPO requirements.
- Flag if backup gaps exceed acceptable data loss.
- Suggested Fix: Increase backup frequency, implement continuous replication for critical data.

### B) Recovery Time Components
- Break down RTO into: detection time, decision time, restore time, validation time.
- Identify bottlenecks in recovery process.
- Flag if any component could exceed RTO budget.
- Suggested Fix: Automate detection and restore triggers, parallelize recovery steps.

### C) Backup Success Monitoring
- Check for backup job monitoring and alerting.
- Verify backup failures are detected promptly.
- Flag silent backup failures.
- Suggested Fix: Implement backup monitoring, alert on failures, track backup age.

### D) Storage Capacity Planning
- Check if backup storage is monitored for capacity.
- Verify retention policy won't exhaust storage.
- Flag unbounded backup retention.
- Suggested Fix: Implement retention policy, monitor storage usage, alert on thresholds.

---

## 4) Disaster Recovery Planning

### A) Disaster Scenarios Documented
- Check for documented disaster scenarios (disk failure, data corruption, ransomware, etc.).
- Verify each scenario has a response plan.
- Flag undocumented likely disaster scenarios.
- Suggested Fix: Document top 5 disaster scenarios with response procedures.

### B) Data Corruption Detection
- Check for mechanisms to detect data corruption.
- Look for checksums on checkpoint files.
- Flag if corruption could go undetected.
- Suggested Fix: Implement checksums, periodic integrity verification, corruption alerts.

### C) Point-in-Time Recovery Capability
- Check if system can restore to a specific point in time.
- Verify checkpoint timestamps are preserved.
- Flag if only latest state is recoverable.
- Suggested Fix: Implement versioned backups, maintain backup history.

### D) Geographic Redundancy
- Check for offsite backup copies.
- Verify backups survive site-level disasters.
- Flag single-site backup storage.
- Suggested Fix: Implement offsite replication, cloud backup, or cross-region storage.

### E) Failover Procedures
- Check if there's a documented failover process.
- Verify failover has been tested.
- Flag if failover is manual without clear ownership.
- Suggested Fix: Document failover procedure, assign ownership, schedule drills.

---

## 5) Data Integrity & Consistency

### A) Atomic Write Operations
- Check if checkpoint writes are atomic (write-then-rename pattern).
- Look for partial write scenarios during crash.
- Flag non-atomic file operations on critical data.
- Suggested Fix: Implement write-to-temp-then-rename, use fsync for durability.

### B) Cross-Component Consistency
- Verify database and file system state remain consistent.
- Check for transactions spanning DB and filesystem.
- Flag if crash could leave inconsistent state.
- Suggested Fix: Implement two-phase commit or compensating transactions.

### C) Backup Consistency Point
- Check if backups capture consistent state across all components.
- Verify backup doesn't capture mid-transaction state.
- Flag if backup could capture partial processing state.
- Suggested Fix: Implement backup coordination, use snapshots where available.

### D) Foreign Key & Reference Integrity
- Check for dangling references in restored data.
- Verify foreign key constraints are enforced.
- Flag if SQLite foreign keys are disabled.
- Suggested Fix: Enable foreign key enforcement, validate references on restore.

---

## 6) Stack-Specific Considerations

### A) SQLite-Specific Backup
- Check for proper WAL checkpoint before backup.
- Verify both main database and WAL file are included.
- Flag if only .db file is backed up (missing WAL).
- Suggested Fix: Run `PRAGMA wal_checkpoint(TRUNCATE)` before backup, or use `.backup` command.

### B) Checkpoint Directory Structure
- Verify checkpoint directory structure is preserved in backup.
- Check for path dependencies in checkpoint files.
- Flag if absolute paths would break on restore to different location.
- Suggested Fix: Use relative paths in checkpoints, document path requirements.

### C) Document Processing State Recovery
- Check if interrupted processing can resume after restore.
- Verify pipeline stage state is recoverable.
- Flag if processing must restart from beginning after restore.
- Suggested Fix: Ensure checkpoint granularity supports mid-processing recovery.

### D) Label Studio Sync State
- Check if Label Studio project state is tracked.
- Verify annotation imports can be replayed.
- Flag if Label Studio and local state could diverge after restore.
- Suggested Fix: Track sync state, implement reconciliation procedure.

### E) Uploaded File Metadata
- Check if file metadata (upload time, original name, user) is preserved.
- Verify metadata is included in backup.
- Flag if only file content is backed up without metadata.
- Suggested Fix: Store metadata in database, include in backup scope.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s) OR Configuration/Process Gap

Risk Category: Backup Coverage | Restore Procedure | RPO/RTO | DR Planning | Data Integrity | Stack-Specific

The Problem:
- 2-4 sentences explaining the risk and potential data loss scenario.
- Be specific about failure mode: complete data loss, partial corruption, extended downtime, inconsistent state, etc.

Business Impact:
- Describe impact in business terms (data loss hours, downtime duration, recovery effort).
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (test restore, check backup age, verify integrity, simulate failure).

The Fix:
- Provide the implementation or procedure.
- Show scripts, configurations, or documentation needed.
- If fix requires infrastructure, describe requirements.

Trade-off Consideration:
- Note complexity, cost, and operational overhead.
- If acceptable at current scale, mark as MONITOR with triggers for implementation.
```

## Severity Classification
- **CRITICAL**: No backup exists for critical data, or restore procedure is untested and likely to fail.
- **HIGH**: Backup gaps exceed RPO, or RTO cannot be met with current procedures.
- **MEDIUM**: Backup exists but has gaps, or restore procedure needs documentation.
- **MONITOR**: Basic backup exists; improvements needed as data volume grows.

---

## Vibe Score Rubric (DR Readiness 1-10)

Rate overall readiness based on backup coverage and recovery capability:
- **9-10**: Comprehensive backups, tested restores, documented procedures, meets RPO/RTO.
- **7-8**: Backups exist for critical data, restore tested once, basic documentation.
- **5-6**: Some backups exist, restore untested, gaps in coverage or documentation.
- **3-4**: Ad-hoc backups only, no tested restore, significant data at risk.
- **<3**: No systematic backup, no restore procedure, data loss likely on any failure.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (immediate data protection)
2) Fix Soon (within next sprint)
3) Monitor (ongoing operational items)

## Also include:
- Estimated time to implement all Fix Now items (range is fine)
- Infrastructure/tooling needed:
  - Backup automation (cron, systemd timers, or backup service)
  - Monitoring for backup success/failure
  - Offsite storage solution
  - Restore testing environment
- Recommended verification steps:
  - Schedule first restore test
  - Document and assign DR ownership
  - Create backup monitoring dashboard
