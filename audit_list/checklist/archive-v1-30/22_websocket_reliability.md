# WebSocket Reliability Audit Prompt (Production-Ready, Real-Time Systems)

## Role
Act as a Senior Backend Engineer specializing in real-time systems and WebSocket infrastructure. Perform a deep-dive WebSocket Reliability Audit on the provided codebase to ensure robust, production-grade real-time communication.

## Primary Goal
Identify fragile WebSocket patterns, missing resilience mechanisms, and state synchronization issues that will cause connection drops, message loss, or degraded user experience under production conditions.

## Context
- This code was developed with a focus on speed ("vibecoded") and may have incomplete WebSocket handling.
- I need you to find reliability gaps, race conditions, and missing error handling before deploying to production.
- Real-time features are critical to user experience—document processing progress must be reliable.

## Tech Stack
- Backend: Python 3.12 + FastAPI + Uvicorn (ASGI WebSocket support)
- Frontend: React 19 + TypeScript 5.9 + Zustand (state management)
- Protocol: WebSocket over HTTP/1.1 upgrade
- Use case: Document processing progress updates, stage completion notifications, error state handling

## Reliability Targets
- Connection recovery: < 5 seconds automatic reconnection
- Message delivery: No silent message loss during brief disconnections
- Heartbeat interval: 30 seconds with 10-second timeout
- Max concurrent connections per client: Configurable limit (default: 3)
- Graceful degradation: UI remains functional during WebSocket outage

## How to Provide Code
I will paste/upload the codebase files below. Analyze all provided files systematically.
If any critical context is missing (WebSocket endpoint paths, message schemas, state management patterns), infer what you can from the code and explicitly list assumptions. If you cannot infer, state "Needs Confirmation" and tell me exactly which file/setting is needed.

## Environment & Assumptions (you must do this first)
1) Infer and list:
   - WebSocket endpoint structure (single vs multiple endpoints)
   - Message format (JSON schema, binary, or mixed)
   - Authentication mechanism for WebSocket connections
   - State management approach (Zustand stores, React context)
   - Deployment model (single instance vs load-balanced)
   - Reverse proxy configuration (NGINX WebSocket timeouts, sticky sessions)
2) If you cannot infer any of the above, provide best-practice defaults and mark as "Needs Confirmation".

## Audit Requirements
Scan the files and generate a report identifying high-confidence instances of the risks below.
Also include "Suspicious Patterns" when something looks risky but requires confirmation (call out exactly what to verify).

---

## 1) Connection Lifecycle Management

### A) Missing Connection State Machine
- Look for WebSocket handlers without explicit state tracking (CONNECTING, OPEN, CLOSING, CLOSED).
- Flag handlers that don't distinguish between intentional close and error close.
- Common hotspots: WebSocket endpoint handlers, React hooks managing connection state.
- Suggested Fix: Implement explicit state machine with transitions and callbacks for each state.

### B) Improper Connection Cleanup
- Find WebSocket connections not properly closed on component unmount or route change.
- Flag missing cleanup in useEffect return functions, missing finally blocks in async handlers.
- Look for zombie connections that remain after user navigates away.
- Suggested Fix: Proper cleanup with close() in useEffect cleanup, AbortController for pending operations.

### C) Missing Connection Validation
- Find WebSocket upgrades without authentication/authorization checks.
- Flag connections accepted before validating session tokens or API keys.
- Look for missing origin validation (CORS equivalent for WebSocket).
- Suggested Fix: Validate auth before accepting upgrade, implement origin whitelist.

### D) Concurrent Connection Handling
- Find missing limits on connections per user/session/IP.
- Flag unbounded connection acceptance that could lead to resource exhaustion.
- Look for missing connection tracking data structures.
- Suggested Fix: Track active connections per client, enforce limits, provide clear error on limit reached.

---

## 2) Reconnection Strategy

### A) Missing Automatic Reconnection
- Look for frontend WebSocket code without reconnection logic after disconnect.
- Flag connections that require manual page refresh to restore.
- Common hotspots: WebSocket hooks, connection managers, Zustand stores.
- Suggested Fix: Implement automatic reconnection with configurable max attempts.

### B) No Exponential Backoff
- Find reconnection logic with fixed delays or immediate retry.
- Flag patterns that will hammer the server after an outage (thundering herd).
- Look for missing jitter in retry delays.
- Suggested Fix: Exponential backoff starting at 1s, max 30s, with ±20% jitter.

```typescript
// Example: Proper reconnection with exponential backoff
const getReconnectDelay = (attempt: number): number => {
  const baseDelay = 1000;
  const maxDelay = 30000;
  const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  const jitter = delay * 0.2 * (Math.random() - 0.5);
  return delay + jitter;
};
```

### C) Missing Reconnection State Sync
- Find reconnection logic that doesn't request missed updates after reconnecting.
- Flag patterns where client state becomes stale after reconnection.
- Look for missing "last received message ID" or timestamp tracking.
- Suggested Fix: Track last received message ID, request delta on reconnect.

### D) No Reconnection Feedback to User
- Find silent reconnection attempts without UI indication.
- Flag missing "reconnecting..." or "connection lost" indicators.
- Look for spinner-only feedback without connection state context.
- Suggested Fix: Display connection state in UI, show reconnection progress.

---

## 3) Message Queue & Delivery Guarantees

### A) Message Loss During Disconnection
- Look for send() calls without checking connection readyState.
- Flag fire-and-forget patterns for important messages.
- Find missing message acknowledgment system.
- Suggested Fix: Queue messages during disconnect, retry on reconnect, implement ack/nack.

### B) No Message Ordering Guarantees
- Find message handlers that assume order but don't verify sequence numbers.
- Flag patterns where out-of-order messages could corrupt state.
- Look for missing sequence tracking in message schemas.
- Suggested Fix: Add sequence numbers to messages, detect gaps, request retransmission.

### C) Missing Message Deduplication
- Find handlers that process the same message multiple times on retry.
- Flag non-idempotent message handlers without deduplication.
- Look for missing message IDs for deduplication.
- Suggested Fix: Add unique message IDs, track processed IDs with TTL.

### D) Unbounded Message Queues
- Find in-memory queues without size limits that grow during disconnection.
- Flag patterns that could cause OOM during extended outages.
- Look for missing queue eviction policies.
- Suggested Fix: Implement max queue size, evict oldest messages or fail gracefully.

```python
# Example: Bounded message queue with eviction
from collections import deque
from typing import Any

class BoundedMessageQueue:
    def __init__(self, maxlen: int = 1000):
        self._queue: deque[Any] = deque(maxlen=maxlen)
        self._dropped_count = 0

    def enqueue(self, message: Any) -> bool:
        if len(self._queue) >= self._queue.maxlen:
            self._dropped_count += 1
            return False  # Queue full, message dropped
        self._queue.append(message)
        return True

    def drain(self) -> list[Any]:
        messages = list(self._queue)
        self._queue.clear()
        return messages
```

---

## 4) Heartbeat & Keep-Alive Implementation

### A) Missing Heartbeat Mechanism
- Look for WebSocket connections without ping/pong or application-level heartbeat.
- Flag connections that rely solely on TCP keep-alive (insufficient for WebSocket).
- Find missing dead connection detection.
- Suggested Fix: Implement ping/pong at application level, 30s interval, 10s timeout.

### B) Improper Heartbeat Timing
- Find heartbeat intervals longer than typical proxy timeouts (60s).
- Flag heartbeat without configurable intervals.
- Look for missing heartbeat response timeout handling.
- Suggested Fix: Heartbeat interval < proxy timeout (typically 30s), with response timeout.

### C) Missing Server-Side Dead Connection Cleanup
- Find server code that doesn't detect dead clients (clients that stopped responding).
- Flag unbounded connection maps that grow with dead connections.
- Look for missing periodic connection health checks.
- Suggested Fix: Track last pong time, close connections exceeding timeout.

```python
# Example: FastAPI WebSocket heartbeat with timeout
import asyncio
from fastapi import WebSocket, WebSocketDisconnect

async def websocket_with_heartbeat(websocket: WebSocket):
    await websocket.accept()
    last_pong = asyncio.get_event_loop().time()

    async def heartbeat_sender():
        nonlocal last_pong
        while True:
            await asyncio.sleep(30)
            current_time = asyncio.get_event_loop().time()
            if current_time - last_pong > 40:  # 30s + 10s grace
                await websocket.close(code=1000, reason="Heartbeat timeout")
                return
            try:
                await websocket.send_json({"type": "ping", "ts": current_time})
            except:
                return

    heartbeat_task = asyncio.create_task(heartbeat_sender())
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "pong":
                last_pong = asyncio.get_event_loop().time()
            else:
                # Handle other messages
                pass
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
```

### D) Frontend Heartbeat Response Missing
- Find frontend code that receives pings but doesn't send pongs.
- Flag missing heartbeat response handlers.
- Look for heartbeat handling only on one side (client or server).
- Suggested Fix: Implement bidirectional heartbeat, respond to pings immediately.

---

## 5) Error Handling & Recovery

### A) Silent Error Swallowing
- Look for try/catch blocks around WebSocket operations that don't log or report errors.
- Flag empty catch blocks or generic error handling.
- Find missing error event handlers on WebSocket objects.
- Suggested Fix: Log all WebSocket errors with context, report to monitoring.

### B) Missing Close Code Handling
- Find WebSocket close handlers that don't check close codes.
- Flag handlers that treat all closes the same (normal vs error vs going-away).
- Look for missing handling of specific close codes (1000, 1001, 1006, 1011).
- Suggested Fix: Handle close codes appropriately, different retry logic per code.

```typescript
// Example: Close code handling
websocket.onclose = (event) => {
  switch (event.code) {
    case 1000: // Normal closure
      console.log("Connection closed normally");
      break;
    case 1001: // Going away (server shutdown, page navigation)
      console.log("Server going away, will reconnect");
      scheduleReconnect();
      break;
    case 1006: // Abnormal closure (no close frame received)
      console.error("Connection lost unexpectedly");
      scheduleReconnect();
      break;
    case 1011: // Internal server error
      console.error("Server error, backing off");
      scheduleReconnect({ backoffMultiplier: 2 });
      break;
    case 4001: // Custom: Auth expired
      handleAuthExpired();
      break;
    default:
      console.warn(`Unknown close code: ${event.code}`);
      scheduleReconnect();
  }
};
```

### C) Missing Graceful Degradation
- Find UI that freezes or crashes when WebSocket is unavailable.
- Flag features that have no fallback when real-time updates fail.
- Look for missing "stale data" indicators when connection is lost.
- Suggested Fix: Implement polling fallback, show stale indicators, maintain functionality.

### D) Unhandled Promise Rejections in WebSocket Context
- Find async WebSocket operations without proper error handling.
- Flag fire-and-forget async calls in message handlers.
- Look for missing try/catch in async message processing.
- Suggested Fix: Wrap all async operations in try/catch, propagate errors appropriately.

---

## 6) State Synchronization (Zustand/React Specific)

### A) State Tearing Between WebSocket and UI
- Look for race conditions where UI updates conflict with incoming WebSocket updates.
- Flag optimistic updates without rollback on WebSocket correction.
- Find missing locking or versioning for concurrent state updates.
- Suggested Fix: Use version numbers, implement optimistic update rollback, serialize updates.

### B) Stale Closure References
- Find WebSocket handlers referencing stale React state via closures.
- Flag useEffect WebSocket handlers without proper dependency tracking.
- Look for handlers that don't use refs for mutable values.
- Suggested Fix: Use refs for values that change, update handlers on dependency change.

```typescript
// Example: Avoiding stale closures with refs
const useWebSocket = (url: string, onMessage: (data: any) => void) => {
  const onMessageRef = useRef(onMessage);

  // Keep ref updated
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onmessage = (event) => {
      // Use ref to always get latest handler
      onMessageRef.current(JSON.parse(event.data));
    };

    return () => ws.close();
  }, [url]); // Only recreate on URL change
};
```

### C) Missing State Reconciliation on Reconnect
- Find reconnection logic that doesn't request full state refresh.
- Flag patterns where state diverges after reconnection.
- Look for missing "get current state" endpoint for reconciliation.
- Suggested Fix: Request full state on reconnect, merge with local state carefully.

### D) Zustand Store Updates Without Immutability
- Find WebSocket handlers that mutate Zustand state directly.
- Flag missing immer or manual spread for nested updates.
- Look for array mutations (push, splice) instead of spread/concat.
- Suggested Fix: Use immer or ensure immutable updates in all handlers.

---

## 7) Security Considerations

### A) Missing WebSocket Authentication
- Look for WebSocket endpoints that don't validate tokens on connection.
- Flag connections that only check auth on HTTP upgrade, not in messages.
- Find missing session validation for long-lived connections.
- Suggested Fix: Validate token on connect, re-validate periodically, validate in messages.

### B) Missing Message Validation
- Find WebSocket handlers that trust incoming message structure.
- Flag missing schema validation on received messages.
- Look for direct object spreading from untrusted messages.
- Suggested Fix: Validate all incoming messages against schema (Pydantic/Zod).

### C) Missing Rate Limiting for Messages
- Find handlers without rate limiting for incoming messages.
- Flag endpoints vulnerable to message flooding.
- Look for CPU-intensive operations triggered by single messages.
- Suggested Fix: Implement per-connection message rate limiting.

### D) Sensitive Data in WebSocket Messages
- Find messages containing tokens, passwords, or PII.
- Flag debug logs that output full WebSocket message contents.
- Look for missing redaction in error messages.
- Suggested Fix: Sanitize sensitive data, redact in logs, use separate auth channel.

---

## Output Format (Mandatory)

For each issue found, provide:

```
[SEVERITY: CRITICAL | HIGH | MEDIUM | MONITOR]

Location: FileName : Line Number(s)
Risk Category: Connection | Reconnection | Messaging | Heartbeat | State Sync | Security

The Problem:
- 2-4 sentences explaining why it fails under production conditions.
- Be specific about failure mode: connection drop, message loss, state desync, zombie connections, etc.

Reliability Impact:
- Provide a realistic estimate (example: "Connection lost every 2 min without heartbeat", "50% message loss during 10s disconnect", "State desync after 1 hour").
- Include Confidence: High | Medium | Low

How to Verify:
- A concrete verification step (network throttle test, intentional disconnect, load test, browser devtools, etc.).

The Fix:
- Provide the optimized code snippet.
- Show before/after if useful.
- If fix requires config changes, show the config and where it belongs.

Trade-off Consideration:
- Note complexity, latency impact, and any risks.
- If acceptable for MVP, mark as MONITOR with what triggers refactor.
```

## Severity Classification
- **CRITICAL**: Will cause connection failures, data loss, or security vulnerabilities in production.
- **HIGH**: Likely to cause degraded real-time experience or intermittent failures.
- **MEDIUM**: Suboptimal UX during edge cases but not immediate failure.
- **MONITOR**: Acceptable for now; watch metrics and revisit at scale.

---

## Reliability Score Rubric (Production Readiness 1-10)

Rate overall WebSocket reliability based on severity/quantity and systemic risks:
- **9-10**: Production-ready WebSocket implementation; handles all edge cases gracefully.
- **7-8**: Needs 1-2 fixes before production; most happy paths work.
- **5-6**: Significant gaps; will have user-visible issues under normal conditions.
- **3-4**: Multiple critical issues; will fail frequently.
- **<3**: Not production-ready; fundamental reliability mechanisms missing.

---

## Include:
- The score
- Brief justification (2-5 bullets)
- A prioritized Top 3 fixes list (highest impact first)

## Final Section: Summary & Action Plan (Mandatory)
1) Fix Now (before production deployment)
2) Fix Soon (next iteration)
3) Monitor (metrics + thresholds)

## Also include:
- Estimated time to implement all Fix Now items (range is fine)
- Monitoring to add before deploying:
  - Metrics: connection count, reconnection rate, message latency, heartbeat failures, error rates by close code
  - Logging: connection lifecycle events, message processing errors, state sync events
  - Alerting thresholds: reconnection rate > 10/min, heartbeat failure rate > 5%, message queue depth > 100

## Testing Recommendations:
- Network throttling tests (Chrome DevTools, toxiproxy)
- Intentional server restart during active connections
- Long-running connection stability test (24 hours)
- Concurrent connection stress test
- Mobile network simulation (intermittent connectivity)

---

## Stack-Specific Patterns to Check

### FastAPI/Starlette WebSocket
```python
# Check for these patterns:

# 1. Proper exception handling
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Process data
    except WebSocketDisconnect:
        # Clean disconnect
        pass
    except Exception as e:
        # Log error, cleanup
        logger.exception("WebSocket error")
    finally:
        # Always cleanup resources
        await cleanup_connection(websocket)

# 2. Connection manager pattern
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str, websocket: WebSocket):
        async with self._lock:
            if client_id in self.active_connections:
                # Handle existing connection
                pass
            self.active_connections[client_id] = websocket

    async def disconnect(self, client_id: str):
        async with self._lock:
            self.active_connections.pop(client_id, None)
```

### React/TypeScript WebSocket Hook
```typescript
// Check for these patterns:

// 1. Proper cleanup on unmount
useEffect(() => {
  const ws = new WebSocket(url);
  wsRef.current = ws;

  ws.onopen = () => setConnectionState('connected');
  ws.onclose = () => setConnectionState('disconnected');
  ws.onerror = (e) => console.error('WebSocket error', e);
  ws.onmessage = handleMessage;

  return () => {
    ws.close(1000, 'Component unmounting');
  };
}, [url]);

// 2. Safe send with queue
const send = useCallback((message: any) => {
  if (wsRef.current?.readyState === WebSocket.OPEN) {
    wsRef.current.send(JSON.stringify(message));
  } else {
    messageQueue.current.push(message);
  }
}, []);
```

### Zustand WebSocket Integration
```typescript
// Check for these patterns:

// 1. Proper store integration
interface WebSocketStore {
  connectionState: 'connecting' | 'connected' | 'disconnected';
  lastMessage: any | null;
  messageQueue: any[];

  // Actions
  setConnectionState: (state: ConnectionState) => void;
  handleMessage: (message: any) => void;
  queueMessage: (message: any) => void;
  flushQueue: () => any[];
}

// 2. Middleware for WebSocket sync
const websocketMiddleware = (config) => (set, get, api) =>
  config(
    (...args) => {
      const prevState = get();
      set(...args);
      const nextState = get();

      // Detect changes that need WebSocket sync
      if (prevState.documentId !== nextState.documentId) {
        websocket.send({ type: 'subscribe', documentId: nextState.documentId });
      }
    },
    get,
    api
  );
```
