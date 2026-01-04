# WebSocket State Sync Audit Prompt (Production-Ready, Real-Time State Consistency)

## Role
Act as a Senior Frontend Architect and Real-Time Systems Engineer. Perform a deep-dive WebSocket State Sync Audit on the provided codebase to ensure reliable, consistent state synchronization between the FastAPI backend and React/Zustand frontend.

## Primary Goal
Identify where AI-generated patterns for real-time state management will cause state tearing, race conditions, stale data, and poor user experience under realistic usage scenarios.

## Context
- This code was developed with a focus on speed ("vibecoded") and real-time features may have subtle synchronization bugs.
- WebSocket state sync issues are notoriously hard to reproduce but catastrophic in production.
- I need you to find race conditions, state conflicts, and resilience gaps before users encounter them.

## Tech Stack
- Backend: Python 3.12 + FastAPI + WebSockets (native or Starlette)
- Frontend: React 19 + TypeScript 5.9 + Zustand
- State Management: Zustand stores for document processing state
- Real-Time Features: Pipeline stage progress, document status updates, error notifications
- Use Case: Interactive document processing with human-in-the-loop editing

## Test Scenarios
- User editing document while receiving WebSocket updates
- Rapid stage transitions (100ms between updates)
- WebSocket disconnect during active editing session
- Reconnection after 30+ second outage
- Multiple browser tabs with same document
- Network latency simulation (500ms+ round trip)

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (WebSocket handler code, Zustand store definitions, message schemas), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - WebSocket implementation (native FastAPI WebSocket, python-socketio, etc.)
   - Message format (JSON schema, message types, versioning)
   - Zustand store structure (slices, selectors, actions)
   - Optimistic update patterns (if any)
   - Reconnection strategy (automatic, manual, exponential backoff)
   - State persistence strategy (localStorage, sessionStorage, none)
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) State Tearing & Race Conditions

### A) Optimistic Update Conflicts
- Look for patterns where local state is updated before server confirmation, then overwritten by WebSocket message.
- Common hotspots: Form submissions, drag-and-drop reordering, inline editing, bbox adjustments.
- Failure Mode: User makes edit → sees change → WebSocket overwrites with stale data → user loses work.
- Suggested Fix: Implement version vectors, last-write-wins with timestamps, or conflict resolution UI.

### B) Concurrent Update Races
- Find patterns where multiple state updates can arrive out of order.
- Look for: Missing sequence numbers, no message ordering guarantees, updates processed without queueing.
- Failure Mode: Stage 5 completion arrives before Stage 4 → UI shows inconsistent state.
- Suggested Fix: Sequence numbers per entity, message queuing with ordering, idempotent state transitions.

### C) Partial State Updates
- Identify WebSocket handlers that update nested state without proper merging.
- Look for: Direct assignment to nested objects, shallow spread operators on deep structures.
- Failure Mode: Update to `document.stages[5].status` clobbers `document.stages[5].elements` array.
- Suggested Fix: Immer-style immutable updates, deep merge utilities, or Zustand's `set` with proper merge.

### D) Zustand Selector Stale Closures
- Find useEffect/useCallback with Zustand selectors that don't update when store changes.
- Look for: Missing dependencies, stale closures capturing old state, subscriptions not re-running.
- Failure Mode: WebSocket handler uses stale state from initial render → incorrect updates applied.
- Suggested Fix: Use `useStore.getState()` in handlers, or `subscribe` with proper cleanup.

---

## 2) Disconnect & Reconnection Resilience

### A) Missing Disconnect Detection
- Look for WebSocket connections without heartbeat/ping-pong or `onclose` handlers.
- Failure Mode: Server crashes → client shows stale data indefinitely → user thinks app is working.
- Suggested Fix: Implement heartbeat (30s interval), detect missed pongs, show "Connection Lost" UI.

### B) Stale Data Indicator Missing
- Find disconnect handlers that don't update UI to indicate data may be stale.
- Look for: State that remains "fresh" after disconnect, missing "last synced" timestamps.
- Failure Mode: User continues editing stale document → reconnect overwrites all changes.
- Suggested Fix: Add `connectionStatus` to store, show "Stale" badge, disable editing when disconnected.

### C) Reconnection Without State Sync
- Identify reconnection logic that doesn't fetch current state from server.
- Look for: Reconnect handlers that just resubscribe without fetching missed updates.
- Failure Mode: 5-minute disconnect → reconnect → miss all intermediate updates → state drift.
- Suggested Fix: On reconnect, fetch full state or request updates since last known sequence number.

### D) Reconnection Stampede
- Find reconnection without exponential backoff or jitter.
- Look for: Immediate retry, fixed interval retry, no maximum retry limit.
- Failure Mode: Server recovers → 1000 clients reconnect simultaneously → server crashes again.
- Suggested Fix: Exponential backoff (1s, 2s, 4s, 8s...) with jitter (±20%), max backoff cap (60s).

### E) Message Queue During Disconnect
- Check if user actions during disconnect are queued for replay on reconnect.
- Look for: Actions lost during disconnect, no local queue, no conflict resolution.
- Failure Mode: User makes edits while disconnected → reconnect → edits lost.
- Suggested Fix: Queue actions locally, replay on reconnect with conflict detection, or disable editing.

---

## 3) Message Processing & Ordering

### A) Missing Message Type Validation
- Find WebSocket message handlers without type/schema validation.
- Look for: Direct property access without type guards, `as` type assertions without validation.
- Failure Mode: Malformed message → runtime error → entire WebSocket handler crashes.
- Suggested Fix: Zod/Yup validation on message ingress, discriminated unions for message types.

### B) Unhandled Message Types
- Identify switch/if-else chains for message types without default/exhaustive handling.
- Look for: Missing `default` case, no exhaustive type checking, silent drops of unknown messages.
- Failure Mode: New message type added → old client silently ignores → state diverges.
- Suggested Fix: Exhaustive type checking, log unknown message types, version negotiation.

### C) Blocking Message Processing
- Find synchronous heavy operations in WebSocket message handlers.
- Look for: Large array transformations, deep object cloning, DOM manipulation in handlers.
- Failure Mode: Heavy processing blocks UI → messages queue up → UI freezes → user frustrated.
- Suggested Fix: Process in microtasks, use `requestIdleCallback`, batch updates with `unstable_batchedUpdates`.

### D) Message Ordering Assumptions
- Identify code that assumes messages arrive in order.
- Look for: State machines without out-of-order handling, increment-only logic, missing sequence gaps.
- Failure Mode: Network reordering → Stage 7 processed before Stage 6 → invalid state transition.
- Suggested Fix: Buffer out-of-order messages, request retransmission for gaps, or design for unordered updates.

---

## 4) State Consistency & Synchronization

### A) Multiple Sources of Truth
- Find state duplicated between Zustand, component state, and refs.
- Look for: `useState` mirroring Zustand, refs holding copies of store data, derived state stored.
- Failure Mode: WebSocket updates Zustand → local state not updated → UI shows stale data.
- Suggested Fix: Single source of truth in Zustand, derive all other state, remove duplicate state.

### B) Derived State Not Updating
- Identify derived/computed values that don't recalculate on WebSocket updates.
- Look for: Memoized values with missing dependencies, cached computations without invalidation.
- Failure Mode: Document status changes → derived "canEdit" doesn't update → edit button state wrong.
- Suggested Fix: Use Zustand selectors with proper equality checks, or computed stores.

### C) Cross-Tab State Drift
- Find applications without cross-tab state synchronization.
- Look for: Each tab having independent WebSocket connection and state, no BroadcastChannel usage.
- Failure Mode: User edits in Tab A → Tab B shows old state → user confused.
- Suggested Fix: BroadcastChannel API for state sync, SharedWorker for single WebSocket, or accept drift with clear UX.

### D) Undo/Redo Stack Corruption
- Check if undo/redo stacks are invalidated by WebSocket updates.
- Look for: Undo that reverts to state that's now inconsistent with server, no undo stack clearing on sync.
- Failure Mode: User undos → reverts to pre-WebSocket state → submits → server rejects as conflict.
- Suggested Fix: Clear undo stack on WebSocket updates, or implement operational transformation.

---

## 5) Backend WebSocket Patterns (FastAPI)

### A) Missing Connection Lifecycle Management
- Find WebSocket endpoints without proper try/finally cleanup.
- Look for: Connections not removed from manager on disconnect, missing `WebSocketDisconnect` handling.
- Failure Mode: Connections accumulate → memory leak → server OOM.
- Suggested Fix: Connection manager with proper add/remove, context manager pattern, periodic cleanup.

### B) Broadcast Without Filtering
- Identify broadcast patterns that send all updates to all clients.
- Look for: Global broadcast lists, no room/topic filtering, no per-document subscription.
- Failure Mode: 100 documents processing → each client gets 100x updates → bandwidth waste.
- Suggested Fix: Room-based subscriptions (per document), topic filtering, or selective broadcast.

### C) Missing Rate Limiting
- Find WebSocket message handlers without rate limiting.
- Look for: No throttling on client messages, no maximum message size, no frequency limits.
- Failure Mode: Malicious client floods messages → server CPU saturated → all clients affected.
- Suggested Fix: Per-connection rate limiting, message size limits, slow consumer detection.

### D) Synchronous Database in WebSocket Handler
- Identify blocking database calls in async WebSocket handlers.
- Look for: SQLite writes without `run_in_executor`, synchronous ORM calls.
- Failure Mode: DB write blocks event loop → all WebSocket connections stall → missed heartbeats.
- Suggested Fix: Use `run_in_executor` for SQLite, or async database driver.

### E) Missing Message Acknowledgment
- Find fire-and-forget message patterns without delivery confirmation.
- Look for: `send_json` without waiting for client ACK, no message receipts.
- Failure Mode: Network drops message → server thinks delivered → client misses critical update.
- Suggested Fix: Application-level ACKs for critical messages, or accept eventual consistency.

---

## 6) Error Handling & Recovery

### A) Uncaught Exceptions in WebSocket Handler
- Find message handlers that can throw without try/catch.
- Look for: JSON parsing without try/catch, property access on possibly-undefined, validation throws.
- Failure Mode: One bad message → exception → WebSocket connection closes → user loses all updates.
- Suggested Fix: Wrap entire handler in try/catch, log errors, continue processing other messages.

### B) Missing Error Propagation to UI
- Identify server-side errors that aren't communicated to client.
- Look for: Server-side exceptions logged but not sent, silent failures, missing error message types.
- Failure Mode: Server fails to process edit → no error sent → user thinks edit saved → data loss.
- Suggested Fix: Error message type, error state in Zustand, toast/notification for user-visible errors.

### C) Reconnection Loop Without User Intervention
- Find infinite reconnection attempts without circuit breaker.
- Look for: No max retry count, no "give up" state, no manual reconnect button.
- Failure Mode: Server down for hours → client keeps hammering → battery drain → no user feedback.
- Suggested Fix: Max retries before showing "Reconnect" button, clear error state, circuit breaker.

### D) Partial Message Handling
- Check if WebSocket handles partial/fragmented messages correctly.
- Look for: Assumptions about message completeness, no buffering for large messages.
- Failure Mode: Large message split across frames → parser fails → handler crashes.
- Suggested Fix: Use WebSocket library that handles framing, or implement message buffering.

---

## 7) Testing & Observability

### A) Missing Connection State Tests
- Check for tests that verify disconnect/reconnect behavior.
- Look for: Only happy-path tests, no simulated network failures, no timeout tests.
- Suggested Fix: Mock WebSocket with controllable disconnect, test stale indicator, test queue replay.

### B) Missing Race Condition Tests
- Find tests that verify behavior under concurrent updates.
- Look for: Sequential-only tests, no parallel message injection, no timing variations.
- Suggested Fix: Fuzz testing with random message ordering, concurrent update simulation.

### C) No Connection Metrics
- Identify missing observability for WebSocket health.
- Look for: No connection count tracking, no message rate metrics, no latency measurement.
- Suggested Fix: Track active connections, message rates, reconnection frequency, latency percentiles.

### D) Missing Client-Side Error Tracking
- Check if WebSocket errors are tracked in error monitoring.
- Look for: Console.error only, no Sentry/LogRocket integration, no error aggregation.
- Suggested Fix: Capture WebSocket errors in monitoring, include connection state context.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s)
Risk Category: State Tearing | Disconnect | Message Processing | Consistency | Backend WS | Error Handling | Testing

The Problem:
- 2-4 sentences explaining the failure mode and user impact.
- Be specific: "User loses unsaved edits", "UI freezes for 5s", "State shows Stage 7 before Stage 6".

User Experience Impact:
- Describe what the user sees when this fails.
- Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (simulate disconnect, inject out-of-order messages, race condition test, network throttling).

The Fix:
- Provide the optimized code snippet.
- Show before/after if useful.
- If fix requires infrastructure, show the required changes.

Trade-off Consideration:
- Note complexity, UX impact, and any risks (e.g., "Adds message queue complexity but prevents data loss").
- If acceptable with good UX, mark as MONITOR with what metric triggers refactor.
```

## Severity Classification
- **CRITICAL**: Will cause data loss, corruption, or completely broken UX (user loses edits, app appears frozen).
- **HIGH**: Significant UX degradation or intermittent data issues (state flicker, stale data shown).
- **MEDIUM**: Noticeable issues under specific conditions (edge cases, slow networks).
- **MONITOR**: Theoretical risk, acceptable with proper monitoring.

---

## Vibe Score Rubric (Real-Time State Sync Readiness 1-10)

Rate overall readiness based on severity/quantity and systemic risks:
- **9-10**: Robust real-time sync; handles disconnects gracefully; no data loss scenarios.
- **7-8**: Works well in ideal conditions; minor edge cases to address.
- **5-6**: Works for happy path; significant disconnect/conflict issues.
- **3-4**: Multiple data loss scenarios; will frustrate users.
- **<3**: Do not deploy; fundamental state sync issues.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (before production)
2) Fix Soon (next iteration)
3) Monitor (metrics + thresholds)

## Also include:
- Estimated complexity for Fix Now items (S/M/L/XL)
- Recommended testing approach:
  - Unit: Mock WebSocket, test message handlers in isolation
  - Integration: Playwright with WebSocket interception
  - Chaos: Network Link Conditioner / tc for latency simulation
  - Manual: Multi-tab testing, disconnect during edit scenarios
- Key metrics to add:
  - Connection state changes (connect/disconnect count)
  - Message processing latency (p50/p95)
  - Reconnection frequency and success rate
  - Out-of-order message count
  - Conflict resolution frequency
