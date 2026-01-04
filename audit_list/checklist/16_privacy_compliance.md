---
## Metadata
**Priority Level:** P3 (Lower)
**Original Audit:** #14 Privacy & Compliance
**Last Updated:** 2025-12-26
**AI/Vibe-Coding Risk Level:** MEDIUM

---

# Privacy & Compliance Audit Prompt (GDPR/CCPA Ready)

## Role
Act as a Privacy Engineer and Data Protection Officer (DPO). Perform a comprehensive Privacy & Compliance Audit on the provided codebase to ensure readiness for GDPR, CCPA, and general data protection best practices.

## Primary Goal
Identify where AI-generated code may have introduced privacy vulnerabilities, missing consent mechanisms, inadequate data lifecycle management, or compliance gaps that could lead to regulatory penalties or data breaches.

## Context
- This code was developed with a focus on speed ("vibecoded") and may not have considered privacy-by-design principles.
- I need you to find data handling issues, consent gaps, and compliance risks before production deployment.

## Tech Stack
- Backend: Python 3.12 / FastAPI / Uvicorn
- Database: SQLite3 (state persistence)
- Document Processing: Docling (PDF/image processing, OCR)
- Image Processing: OpenCV, Pillow, pdf2image
- External Integration: Label Studio SDK
- Real-time: WebSockets
- Frontend: React 19 / TypeScript 5.9 / Zustand
- Infrastructure: Docker (Python 3.11-slim-bookworm)

## Compliance Targets
- GDPR (General Data Protection Regulation) - EU
- CCPA (California Consumer Privacy Act) - US
- SOC 2 Type II readiness (data handling controls)
- Industry best practices for document processing systems

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (data flows, third-party integrations, deployment model), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - Data categories processed (PII types: names, emails, document content, images)
   - Data flow paths (upload → processing → storage → export)
   - Third-party data sharing (Label Studio, external APIs)
   - Retention policies visible in code
   - Authentication/authorization model
   - Logging practices and what data is logged
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) PII Identification & Data Inventory

### A) Document Content as PII
- Identify where document content (text, images, OCR output) is stored, processed, or logged.
- Flag storage of extracted text that may contain PII (names, addresses, SSNs, financial data).
- **Stack-specific**: Check Docling OCR output, checkpoint JSON files, SQLite tables.
- Suggested Fix: Implement data classification, minimize storage, encrypt at rest.

### B) Metadata Leakage
- Find file metadata exposure (original filenames, user paths, timestamps).
- Flag PDF metadata preservation (author, creator, modification dates).
- **Stack-specific**: Check upload handlers, checkpoint schemas, API responses.
- Suggested Fix: Strip metadata on upload, sanitize filenames, use UUIDs.

### C) Derived PII
- Identify derived data that could re-identify individuals (document fingerprints, reading patterns).
- Flag ML model outputs that encode personal information.
- **Stack-specific**: Check Docling model outputs, layout predictions, table structures.
- Suggested Fix: Document data lineage, apply purpose limitation.

### D) Data Inventory Gaps
- Missing documentation of what PII is collected, where it's stored, and how long it's retained.
- **Stack-specific**: Check for data flow documentation, schema comments, retention policies.
- Suggested Fix: Create data inventory spreadsheet, map all PII flows.

---

## 2) Consent & Lawful Basis

### A) Missing Consent Mechanisms
- Find data collection points without explicit consent capture.
- Flag implicit consent assumptions (e.g., "by uploading, you agree").
- **Stack-specific**: Check upload endpoints, document processing triggers.
- Suggested Fix: Implement consent capture, store consent records with timestamps.

### B) Purpose Limitation Violations
- Identify data used for purposes beyond original collection intent.
- Flag feature creep in data processing (analytics, ML training, sharing).
- **Stack-specific**: Check if document content is used beyond immediate processing.
- Suggested Fix: Document purposes, implement purpose-bound access controls.

### C) Consent Record Management
- Missing audit trail of consent given/withdrawn.
- No mechanism to update consent preferences.
- **Stack-specific**: Check for consent tables, preference storage, withdrawal handlers.
- Suggested Fix: Create consent ledger with immutable records.

### D) Third-Party Consent Propagation
- Consent not propagated to third-party integrations.
- **Stack-specific**: Check Label Studio data sharing, external API calls.
- Suggested Fix: Implement consent checks before third-party data transfer.

---

## 3) Data Subject Rights (GDPR Articles 15-22)

### A) Right to Access (Art. 15)
- Missing endpoint for users to download their data.
- Incomplete data export (missing some data categories).
- **Stack-specific**: Check for export endpoints, data compilation logic.
- Suggested Fix: Implement comprehensive data export endpoint.

### B) Right to Rectification (Art. 16)
- No mechanism to correct inaccurate data.
- Corrections not propagated to derived data.
- **Stack-specific**: Check for edit endpoints, checkpoint update propagation.
- Suggested Fix: Implement data correction with cascade updates.

### C) Right to Erasure (Art. 17)
- Missing delete functionality for user data.
- Soft delete instead of hard delete.
- Data persisting in backups, logs, caches.
- **Stack-specific**: Check checkpoint deletion, SQLite record removal, file cleanup.
- Suggested Fix: Implement hard delete with cascade, backup exclusion policies.

### D) Right to Data Portability (Art. 20)
- Data export not in machine-readable format.
- Missing standardized export formats (JSON, CSV).
- **Stack-specific**: Check export formats, API response structures.
- Suggested Fix: Implement JSON/CSV export with standard schemas.

### E) Right to Object (Art. 21)
- No mechanism to opt-out of specific processing.
- **Stack-specific**: Check for processing preferences, opt-out flags.
- Suggested Fix: Implement granular processing controls.

---

## 4) Data Retention & Lifecycle

### A) Unbounded Retention
- Data stored indefinitely without cleanup.
- Missing retention policies in code or documentation.
- **Stack-specific**: Check checkpoint retention, SQLite record age, uploaded file cleanup.
- Suggested Fix: Implement TTL-based cleanup, retention policy enforcement.

### B) Orphaned Data
- Data remaining after parent record deletion.
- Dangling references to deleted users/documents.
- **Stack-specific**: Check foreign key relationships, checkpoint orphans, file system orphans.
- Suggested Fix: Implement cascade deletes, orphan cleanup jobs.

### C) Backup Retention
- Backups retained longer than source data.
- No backup purge aligned with data deletion.
- **Stack-specific**: Check backup scripts, SQLite backup policies.
- Suggested Fix: Align backup retention with data retention policies.

### D) Log Retention
- Logs containing PII retained indefinitely.
- No log rotation or purging.
- **Stack-specific**: Check logging configuration, log file management.
- Suggested Fix: Implement log rotation with PII redaction.

---

## 5) Data Security & Encryption

### A) Encryption at Rest
- Sensitive data stored unencrypted.
- Weak encryption algorithms or key management.
- **Stack-specific**: Check SQLite encryption, checkpoint file encryption, uploaded file storage.
- Suggested Fix: Implement AES-256 encryption, use secure key management.

### B) Encryption in Transit
- Missing HTTPS enforcement.
- Insecure WebSocket connections.
- **Stack-specific**: Check API endpoints, WebSocket configuration.
- Suggested Fix: Enforce TLS 1.3, implement WSS.

### C) Access Control Gaps
- Missing authentication on sensitive endpoints.
- Overly permissive authorization.
- **Stack-specific**: Check endpoint decorators, middleware, session management.
- Suggested Fix: Implement RBAC, principle of least privilege.

### D) Secrets in Code
- Hardcoded API keys, passwords, tokens.
- Secrets in version control.
- **Stack-specific**: Check for Label Studio API keys, database credentials.
- Suggested Fix: Use environment variables, secrets manager.

---

## 6) Audit Logging & Accountability

### A) Missing Audit Trail
- No logging of data access, modifications, deletions.
- Missing "who did what when" records.
- **Stack-specific**: Check for audit log tables, access logging middleware.
- Suggested Fix: Implement comprehensive audit logging.

### B) Insufficient Log Detail
- Logs missing user identity, action type, affected data.
- No correlation IDs for request tracking.
- **Stack-specific**: Check logging patterns, log structure.
- Suggested Fix: Structured logging with user context.

### C) Audit Log Tampering
- Logs stored in mutable format.
- No integrity protection for audit records.
- **Stack-specific**: Check log storage, append-only guarantees.
- Suggested Fix: Implement append-only audit log, consider blockchain-style hashing.

### D) Missing Breach Detection
- No monitoring for suspicious access patterns.
- No alerting on anomalous data access.
- **Stack-specific**: Check for monitoring, alerting configuration.
- Suggested Fix: Implement access anomaly detection.

---

## 7) Third-Party & Cross-Border Transfers

### A) Data Processor Agreements
- Missing DPAs with third-party services.
- Unclear data processing relationships.
- **Stack-specific**: Check Label Studio integration, external API usage.
- Suggested Fix: Document all processors, obtain DPAs.

### B) Cross-Border Transfer Mechanisms
- Data transferred outside EU without adequate safeguards.
- Missing Standard Contractual Clauses (SCCs).
- **Stack-specific**: Check deployment locations, third-party service locations.
- Suggested Fix: Implement SCCs, data localization options.

### C) Sub-Processor Management
- No visibility into sub-processor chain.
- Missing sub-processor notifications.
- **Stack-specific**: Check Label Studio's sub-processors, cloud provider dependencies.
- Suggested Fix: Maintain sub-processor registry, notification process.

---

## 8) Privacy by Design (Stack-Specific)

### A) Document Processing Privacy
- OCR extracting more data than necessary.
- Full document content stored when only metadata needed.
- **Stack-specific**: Check Docling processing options, data minimization.
- Suggested Fix: Implement selective extraction, redaction options.

### B) Checkpoint Data Minimization
- Checkpoints containing full document content.
- Sensitive data in intermediate processing states.
- **Stack-specific**: Check checkpoint schemas, data fields stored.
- Suggested Fix: Minimize checkpoint content, encrypt sensitive fields.

### C) Frontend Data Exposure
- Sensitive data sent to browser unnecessarily.
- PII visible in browser dev tools, local storage.
- **Stack-specific**: Check API responses, Zustand state, React component props.
- Suggested Fix: Implement data projection, minimize frontend state.

### D) WebSocket Privacy
- PII transmitted over WebSocket without necessity.
- Message history containing sensitive data.
- **Stack-specific**: Check WebSocket message schemas, broadcast patterns.
- Suggested Fix: Minimize WebSocket payloads, avoid PII in real-time updates.

---

## 9) CCPA-Specific Requirements

### A) "Do Not Sell" Compliance
- Missing opt-out mechanism for data sale.
- No tracking of sale preferences.
- Suggested Fix: Implement "Do Not Sell My Personal Information" functionality.

### B) Consumer Request Handling
- No 45-day response tracking for consumer requests.
- Missing verification process for requesters.
- Suggested Fix: Implement request tracking, identity verification.

### C) Financial Incentive Disclosure
- Missing disclosure of data collection incentives.
- No opt-in for incentive programs.
- Suggested Fix: Document and disclose any incentives.

### D) Minor Privacy Protections
- No age verification.
- Missing parental consent for minors.
- Suggested Fix: Implement age gate if applicable.

---

## 10) Vibe Code Privacy Anti-Patterns

### A) Logging PII
- `console.log` / `logger.info` with document content, user data.
- Error messages containing extracted text.
- **Stack-specific**: Check logging statements in document handlers, OCR processors.
- Suggested Fix: Implement PII redaction in logs, structured logging with field filtering.

### B) Debug Data Exposure
- Debug endpoints returning raw data.
- Verbose error responses with internal data.
- **Stack-specific**: Check debug routes, exception handlers, error responses.
- Suggested Fix: Disable debug endpoints in production, sanitize errors.

### C) Implicit Data Collection
- Features collecting data without clear purpose.
- Analytics or telemetry without disclosure.
- **Stack-specific**: Check for hidden analytics, usage tracking.
- Suggested Fix: Document all data collection, provide transparency.

### D) Copy-Paste Privacy Debt
- AI-generated code copying patterns without privacy consideration.
- Boilerplate that stores more data than needed.
- **Stack-specific**: Check for unnecessary data fields, over-broad queries.
- Suggested Fix: Review all data storage against purpose, minimize.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | LOW]

Location: FileName : Line Number(s)
Risk Category: PII Handling | Consent | Subject Rights | Retention | Security | Audit | Third-Party | Privacy-by-Design

The Problem:
- 2-4 sentences explaining the privacy/compliance risk.
- Be specific about regulatory violation: GDPR article, CCPA requirement, or best practice gap.

Compliance Impact:
- Potential penalty exposure (GDPR: up to 4% global revenue, CCPA: $7,500 per intentional violation).
- Reputational risk assessment.
- Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (data flow trace, log review, request test, config check).

The Fix:
- Provide the recommended code/config change.
- Show before/after if useful.
- If fix requires architectural change, outline the approach.

Trade-off Consideration:
- Note UX impact, implementation complexity, and operational overhead.
- If acceptable for MVP, mark as LOW with clear remediation timeline.
```

## Severity Classification
- **CRITICAL**: Direct GDPR/CCPA violation with high penalty risk (missing deletion, consent, or access rights).
- **HIGH**: Significant compliance gap or data exposure risk.
- **MEDIUM**: Best practice violation, indirect compliance risk.
- **LOW**: Minor issue, documentation gap, or technical debt.

---

## Compliance Score Rubric (GDPR/CCPA Readiness 1-10)

Rate overall compliance readiness:
- **9-10**: Production-ready; comprehensive privacy controls in place.
- **7-8**: Minor gaps; needs 1-2 fixes before processing real PII.
- **5-6**: Significant gaps; should not process real PII until addressed.
- **3-4**: Major compliance failures; high regulatory risk.
- **<3**: Do not deploy; fundamental privacy architecture missing.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest regulatory risk first)

## Final Section: Summary & Action Plan (Mandatory)

1) **Fix Now** (before processing any real PII)
   - Blocking issues for compliance

2) **Fix Before Production** (next iteration)
   - Important controls needed for production

3) **Implement for Maturity** (ongoing)
   - Best practices and enhanced controls

## Also Include:
- Estimated time to implement all Fix Now items (range is fine)
- Privacy infrastructure to add:
  - Data inventory documentation
  - Consent management system
  - Subject rights request workflow
  - Audit logging framework
  - Data retention automation
  - Privacy impact assessment template
- Recommended privacy tools:
  - Data discovery/classification tools
  - PII detection in logs
  - Consent management platforms
  - Privacy-preserving analytics

## Document Processing Specific Checklist

For this document processing pipeline, specifically verify:

- [ ] Uploaded documents are encrypted at rest
- [ ] OCR text is not logged in plaintext
- [ ] Checkpoints can be fully deleted
- [ ] Document content is not exposed in error messages
- [ ] Label Studio integration has proper data agreements
- [ ] WebSocket messages don't broadcast document content
- [ ] Frontend doesn't cache sensitive document data
- [ ] Export formats include only necessary data
- [ ] Temporary files are securely deleted
- [ ] Document metadata is stripped on upload
