# Production Audit Checklists

> Comprehensive audit guides adapted from docling-interactive project.

**Note**: These checklists were created for a full-stack document processing application (FastAPI + React + SQLite + WebSockets). Many sections require adaptation for SAM3's API-only, GPU-focused architecture.

---

## Quick Start

**Immediate Value (Use As-Is)**:
- [01_security_threat_model.md](checklist/01_security_threat_model.md) - File upload security, image validation
- [05_reliability_resilience.md](checklist/05_reliability_resilience.md) - Timeouts, retries, error handling
- [07_dependency_supply_chain.md](checklist/07_dependency_supply_chain.md) - CVE scanning, lockfile hygiene
- [11_configuration_secrets.md](checklist/11_configuration_secrets.md) - Environment variables, secrets management

**High Value (Needs Adaptation)**:
- [04_performance_event_loop.md](checklist/04_performance_event_loop.md) ⚠️ **CRITICAL** - Replace "Docling" → "SAM3", add GPU-specific sections
- [09_observability_incident.md](checklist/09_observability_incident.md) - Add GPU metrics, remove WebSocket/SQLite sections
- [12_code_quality_architecture.md](checklist/12_code_quality_architecture.md) - AI hallucination verification patterns

**Not Applicable (Skip or Archive)**:
- [02_data_integrity_concurrency.md](checklist/02_data_integrity_concurrency.md) - SQLite patterns (SAM3 is stateless)
- [03_checkpoint_state_management.md](checklist/03_checkpoint_state_management.md) - Document pipeline checkpoints
- [06_websocket_reliability_state.md](checklist/06_websocket_reliability_state.md) - WebSocket patterns (no WebSocket in SAM3)
- [08_api_contract_type_safety.md](checklist/08_api_contract_type_safety.md) - Pydantic/TypeScript parity (no frontend)
- [15_ux_accessibility.md](checklist/15_ux_accessibility.md) - Frontend UX (no frontend)

---

## SAM3-Specific Adaptations Needed

### Performance Checklist (04)
**Current**: CPU-bound operations, async event loop blocking
**Need to Add**:
- GPU synchronization blocking patterns
- CUDA memory allocation in async endpoints
- Model loading time optimization
- Batch size tuning for GPU memory limits
- `torch.inference_mode()` usage verification

### Security Checklist (01)
**Current**: File upload, SQL injection, XSS
**Need to Add**:
- Adversarial image attacks on SAM3
- GPU resource exhaustion DoS
- Prompt injection via text prompts
- Base64 payload bomb detection
- Model weight file integrity validation

### Observability Checklist (09)
**Current**: Multi-stage pipeline metrics, WebSocket tracing
**Need to Add**:
- GPU utilization metrics (NVIDIA SMI integration)
- Inference latency percentiles by image size
- Model confidence score distribution
- Failed inference root cause analysis
- Cold start vs warm inference timing

---

## Missing Checklists for SAM3

The following production concerns are **not covered** by existing checklists:

1. **ML Model Security & Integrity**
   - Model weight tampering detection
   - Model version validation
   - Inference reproducibility verification

2. **Computer Vision Pipeline Validation**
   - Image preprocessing correctness
   - Bounding box coordinate validation
   - Zone overlap resolution
   - Confidence threshold tuning methodology

3. **GPU Resource Management**
   - Memory leak detection
   - Multi-model loading strategies
   - Graceful degradation to CPU/MockModel
   - Batch processing queue management

4. **Prompt Engineering Quality**
   - Prompt effectiveness regression testing
   - Exemplar image curation standards
   - Zero-shot vs few-shot accuracy comparison

---

## Usage Patterns

### For New Features
1. Check relevant checklist **before** implementation
2. Use checklist sections as acceptance criteria
3. Adapt terminology (document → drawing, Docling → SAM3)

### For Production Readiness
1. Start with "Immediate Value" checklists
2. Adapt "High Value" checklists for SAM3
3. Create missing checklists as needed
4. Run verification audits before launch

### For Code Reviews
1. Reference checklist sections in PR comments
2. Use finding templates from checklists
3. Track audit findings in issues

---

## Checklist Status

| # | Checklist | Relevance | Status | Notes |
|---|-----------|-----------|--------|-------|
| 01 | Security Threat Model | ✅ HIGH | Ready | Add ML security sections |
| 02 | Data Integrity & Concurrency | ❌ LOW | Skip | SQLite-specific |
| 03 | Checkpoint State Management | ❌ LOW | Skip | Pipeline-specific |
| 04 | Performance & Event Loop | ⚠️ **CRITICAL** | Needs Adaptation | Add GPU sections |
| 05 | Reliability & Resilience | ✅ MEDIUM | Ready | Generic patterns apply |
| 06 | WebSocket Reliability | ❌ LOW | Skip | No WebSocket |
| 07 | Dependency & Supply Chain | ✅ HIGH | Ready | CVE scanning applies |
| 08 | API Contract & Type Safety | ⚠️ MEDIUM | Partial | Remove frontend sections |
| 09 | Observability & Incident | ✅ HIGH | Needs Adaptation | Add GPU metrics |
| 10 | Infrastructure & Deployment | ✅ MEDIUM | Ready | Docker/GPU deployment |
| 11 | Configuration & Secrets | ✅ HIGH | Ready | Universal patterns |
| 12 | Code Quality & Architecture | ✅ MEDIUM | Needs Adaptation | Remove React sections |
| 13 | Testing Strategy | ⚠️ MEDIUM | Needs Adaptation | Add ML testing patterns |
| 14 | CI/CD Pipeline | ✅ MEDIUM | Ready | Generic pipeline patterns |
| 15 | UX & Accessibility | ❌ LOW | Skip | No frontend |
| 16 | Privacy & Compliance | ⚠️ LOW | Partial | Only if handling user docs |
| 17 | Logging & Data Exposure | ✅ MEDIUM | Ready | Log sanitization applies |
| 18 | Backup, Restore & DR | ❌ LOW | Skip | Stateless service |
| 19 | Cost & Efficiency | ⚠️ MEDIUM | Needs Adaptation | Focus on GPU costs |
| 20 | Documentation & Runbooks | ✅ HIGH | Ready | Universal patterns |

**Legend**: ✅ Use as-is | ⚠️ Needs adaptation | ❌ Not applicable

---

## Contributing

When adapting checklists or creating new ones:
1. Keep the severity classification system (CRITICAL/HIGH/MEDIUM/LOW)
2. Include concrete code examples (✅ GOOD vs ❌ BAD)
3. Provide verification commands where possible
4. Reference CLAUDE.md guidelines for consistency

---

## Related Documentation

- [../CLAUDE.md](../CLAUDE.md) - SAM3 project preferences and guidelines
- [common_errors.md](common_errors.md) - Running log of actual bugs (Python/FastAPI focus)
- [../ai_guides/](../ai_guides/) - AI coding guidelines and structure patterns
