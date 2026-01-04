# WebSocket Reliability & State Synchronization Audit

**Priority:** P1 (Critical for Production)
**Merged from:** #22 (WebSocket Reliability), #30 (WebSocket State Sync)
**Tech Stack:** FastAPI + Uvicorn WebSockets, React 19 + TypeScript 5.9 + Zustand
**Use Case:** Document processing pipeline with real-time progress updates

---

## Overview

This consolidated audit covers both **connection-level reliability** (transport, heartbeat, reconnection) and **application-level state synchronization** (Zustand integration, race conditions, consistency). Both dimensions must be robust for production deployment.

### Critical Reliability Targets
- Connection recovery: < 5 seconds automatic reconnection
- Message delivery: No silent message loss during brief disconnections
- Heartbeat interval: 30 seconds with 10-second timeout
- State consistency: No data loss or state tearing during disconnects
- Graceful degradation: UI remains functional during WebSocket outage

---

## Section 1: Connection & Transport Reliability

> 🐍 PYTHON/FASTAPI - Backend WebSocket implementation patterns
> ⚛️ REACT/TS - Frontend connection lifecycle management
> ⚠️ AI-CODING RISK - Patterns often incomplete in rapid development

### 1.1 Connection Lifecycle Management

#### [ ] Missing Connection State Machine
**Location:** Frontend WebSocket hooks, backend connection managers
**Risk:** Cannot distinguish between intentional close and error close; improper cleanup

- [ ] Check WebSocket handlers have explicit state tracking (CONNECTING, OPEN, CLOSING, CLOSED)
- [ ] Verify distinction between intentional close vs error close (close codes)
- [ ] Ensure state machine has transitions and callbacks for each state
- [ ] Common hotspots:
  - `frontend/src/utils/websocket.ts` - Connection state enum
  - `backend/websocket/manager.py` - Connection lifecycle tracking

**⚠️ AI-CODING RISK:** State machines often reduced to simple boolean flags

**Expected Pattern:**
```typescript
// ⚛️ REACT/TS
enum ConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
  FAILED = 'failed'
}
```

---

#### [ ] Improper Connection Cleanup
**Location:** React useEffect cleanup, component unmount handlers

- [ ] Find WebSocket connections not properly closed on component unmount
- [ ] Check for missing cleanup in useEffect return functions
- [ ] Verify no zombie connections after route change or page navigation
- [ ] Ensure finally blocks execute in async handlers
- [ ] Validate AbortController usage for pending operations

**⚠️ AI-CODING RISK:** Cleanup functions often forgotten in rapid prototyping

**Expected Pattern:**
```typescript
// ⚛️ REACT/TS
useEffect(() => {
  const ws = new WebSocket(url);

  return () => {
    ws.close(1000, 'Component unmounting');
  };
}, [url]);
```

---

#### [ ] Missing Connection Validation
**Location:** `backend/websocket/handlers.py`, WebSocket upgrade endpoints

- [ ] Check WebSocket upgrades validate authentication before accepting
- [ ] Verify session tokens/API keys checked on connection
- [ ] Ensure origin validation (CORS equivalent for WebSocket)
- [ ] Validate no anonymous WebSocket connections without auth

**🐍 PYTHON/FASTAPI Pattern:**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Validate before accepting!
    token = websocket.query_params.get("token")
    if not await validate_token(token):
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
```

---

#### [ ] Concurrent Connection Handling
**Location:** `backend/websocket/manager.py`, connection tracking structures

- [ ] Verify limits on connections per user/session/IP
- [ ] Check for unbounded connection acceptance (resource exhaustion risk)
- [ ] Ensure connection tracking data structures exist
- [ ] Validate clear error messages when connection limit reached

**🐍 PYTHON/FASTAPI - Expected Pattern:**
```python
class ConnectionManager:
    def __init__(self, max_per_client: int = 3):
        self.connections: dict[str, list[WebSocket]] = {}
        self.max_per_client = max_per_client

    async def connect(self, client_id: str, websocket: WebSocket):
        if len(self.connections.get(client_id, [])) >= self.max_per_client:
            await websocket.close(code=4003, reason="Too many connections")
            return False
```

---

### 1.2 Reconnection Strategy

#### [ ] Missing Automatic Reconnection
**Location:** Frontend WebSocket hooks, connection manager utilities

- [ ] Check for reconnection logic after unexpected disconnect
- [ ] Verify connections don't require manual page refresh
- [ ] Ensure reconnection attempts are configurable
- [ ] Common hotspots: `useWebSocket` hook, Zustand WebSocket middleware

**⚠️ AI-CODING RISK:** Reconnection logic often omitted entirely

---

#### [ ] No Exponential Backoff
**Location:** Reconnection timing logic

- [ ] Find reconnection with fixed delays or immediate retry
- [ ] Check for missing jitter in retry delays (thundering herd risk)
- [ ] Verify maximum backoff cap exists (typically 30s)
- [ ] Ensure backoff resets after successful connection

**⚛️ REACT/TS - Expected Pattern:**
```typescript
const getReconnectDelay = (attempt: number): number => {
  const baseDelay = 1000;
  const maxDelay = 30000;
  const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  const jitter = delay * 0.2 * (Math.random() - 0.5);
  return delay + jitter;
};
```

---

#### [ ] Missing Reconnection State Sync
**Location:** Reconnection handlers, state reconciliation logic

- [ ] Verify reconnection requests missed updates after reconnecting
- [ ] Check for "last received message ID" or timestamp tracking
- [ ] Ensure state doesn't become stale after reconnection
- [ ] Validate delta/full refresh mechanism exists

**Key Questions:**
- Does the client track `lastMessageId` or `lastSyncTimestamp`?
- On reconnect, does the client request state since last known point?

---

#### [ ] No Reconnection Feedback to User
**Location:** UI components, Zustand connection state

- [ ] Check for "reconnecting..." or "connection lost" UI indicators
- [ ] Verify not just spinner without connection state context
- [ ] Ensure user knows difference between loading and reconnecting
- [ ] Validate toast/notification on connection state changes

---

### 1.3 Message Queue & Delivery Guarantees

#### [ ] Message Loss During Disconnection
**Location:** WebSocket send logic, message queuing utilities

- [ ] Find `send()` calls without checking `readyState`
- [ ] Check for fire-and-forget patterns for important messages
- [ ] Verify message acknowledgment system exists
- [ ] Ensure messages queue during disconnect and retry on reconnect

**⚛️ REACT/TS - Expected Pattern:**
```typescript
const send = useCallback((message: any) => {
  if (wsRef.current?.readyState === WebSocket.OPEN) {
    wsRef.current.send(JSON.stringify(message));
  } else {
    messageQueue.current.push(message);
  }
}, []);
```

---

#### [ ] No Message Ordering Guarantees
**Location:** Message handlers, state update logic

- [ ] Check for sequence number tracking in messages
- [ ] Verify handlers don't assume ordered delivery
- [ ] Ensure out-of-order detection exists
- [ ] Validate gap detection and retransmission requests

**⚠️ AI-CODING RISK:** Message ordering rarely considered in initial implementation

---

#### [ ] Missing Message Deduplication
**Location:** Message handlers, message ID tracking

- [ ] Find handlers that process same message multiple times on retry
- [ ] Check for unique message IDs in message schema
- [ ] Verify deduplication tracking with TTL
- [ ] Ensure non-idempotent operations are protected

---

#### [ ] Unbounded Message Queues
**Location:** Client-side message buffering, queue implementation

- [ ] Find in-memory queues without size limits
- [ ] Check for OOM risk during extended outages
- [ ] Verify queue eviction policies exist (FIFO, priority-based)
- [ ] Ensure graceful handling when queue is full

**🐍 PYTHON/FASTAPI - Expected Pattern:**
```python
from collections import deque

class BoundedMessageQueue:
    def __init__(self, maxlen: int = 1000):
        self._queue: deque[Any] = deque(maxlen=maxlen)
        self._dropped_count = 0

    def enqueue(self, message: Any) -> bool:
        if len(self._queue) >= self._queue.maxlen:
            self._dropped_count += 1
            return False
        self._queue.append(message)
        return True
```

---

### 1.4 Heartbeat & Keep-Alive Implementation

#### [ ] Missing Heartbeat Mechanism
**Location:** Backend WebSocket handlers, frontend ping/pong logic

- [ ] Check for ping/pong or application-level heartbeat
- [ ] Verify not relying solely on TCP keep-alive
- [ ] Ensure dead connection detection exists
- [ ] Validate 30s interval, 10s timeout pattern

**🐍 PYTHON/FASTAPI - Expected Pattern:**
```python
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
            await websocket.send_json({"type": "ping", "ts": current_time})
```

---

#### [ ] Improper Heartbeat Timing
**Location:** Heartbeat interval configuration

- [ ] Check heartbeat interval is less than proxy timeout (typically 60s)
- [ ] Verify heartbeat interval is configurable
- [ ] Ensure response timeout handling exists
- [ ] Validate intervals don't conflict with processing delays

**Common Issue:** 60s+ heartbeat interval causes proxy timeouts

---

#### [ ] Missing Server-Side Dead Connection Cleanup
**Location:** `backend/websocket/manager.py`, connection health checks

- [ ] Find server code detecting dead clients (no pong response)
- [ ] Check for periodic connection health checks
- [ ] Verify unbounded connection maps have cleanup
- [ ] Ensure last-pong timestamp tracking exists

---

#### [ ] Frontend Heartbeat Response Missing
**Location:** Frontend message handlers, ping/pong response logic

- [ ] Check frontend responds to ping messages with pong
- [ ] Verify heartbeat handling is bidirectional
- [ ] Ensure immediate pong response (no queueing delays)
- [ ] Validate heartbeat response includes timestamp/correlation ID

**⚛️ REACT/TS - Expected Pattern:**
```typescript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'ping') {
    ws.send(JSON.stringify({ type: 'pong', ts: data.ts }));
    return;
  }

  // Handle other messages
};
```

---

### 1.5 Error Handling & Recovery

#### [ ] Silent Error Swallowing
**Location:** WebSocket operation try/catch blocks

- [ ] Find try/catch blocks that don't log WebSocket errors
- [ ] Check for empty catch blocks or generic error handling
- [ ] Verify error event handlers exist on WebSocket objects
- [ ] Ensure errors propagate to monitoring (Sentry, etc.)

**⚠️ AI-CODING RISK:** Empty catch blocks extremely common

---

#### [ ] Missing Close Code Handling
**Location:** WebSocket close event handlers

- [ ] Check close handlers examine close codes (1000, 1001, 1006, 1011, etc.)
- [ ] Verify different retry logic per close code
- [ ] Ensure custom close codes documented (4xxx range)
- [ ] Validate UI feedback varies by close reason

**⚛️ REACT/TS - Expected Pattern:**
```typescript
websocket.onclose = (event) => {
  switch (event.code) {
    case 1000: // Normal closure
      console.log("Connection closed normally");
      break;
    case 1001: // Going away
      scheduleReconnect();
      break;
    case 1006: // Abnormal closure
      console.error("Connection lost unexpectedly");
      scheduleReconnect();
      break;
    case 1011: // Internal server error
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

---

#### [ ] Missing Graceful Degradation
**Location:** UI components, fallback mechanisms

- [ ] Check UI doesn't freeze when WebSocket unavailable
- [ ] Verify fallback mechanisms exist (polling, manual refresh)
- [ ] Ensure "stale data" indicators show during outage
- [ ] Validate core functionality works without WebSocket

**Key Questions:**
- Can user view document without live updates?
- Is there a polling fallback for critical updates?
- Does UI clearly indicate "offline" vs "loading" state?

---

#### [ ] Unhandled Promise Rejections in WebSocket Context
**Location:** Async WebSocket operations, message handlers

- [ ] Find async WebSocket operations without error handling
- [ ] Check for fire-and-forget async calls in message handlers
- [ ] Verify try/catch in all async message processing
- [ ] Ensure unhandled rejections are logged

---

### 1.6 Security Considerations

#### [ ] Missing WebSocket Authentication
**Location:** WebSocket upgrade handlers, authentication middleware

- [ ] Check WebSocket endpoints validate tokens on connection
- [ ] Verify not just HTTP upgrade auth, but also in-message validation
- [ ] Ensure session re-validation for long-lived connections
- [ ] Validate token expiry handling (4001 close code)

---

#### [ ] Missing Message Validation
**Location:** Backend message handlers, schema validation

- [ ] Find handlers that trust incoming message structure
- [ ] Check for schema validation (Pydantic on backend, Zod on frontend)
- [ ] Verify no direct object spreading from untrusted messages
- [ ] Ensure type guards exist before property access

**🐍 PYTHON/FASTAPI - Expected Pattern:**
```python
from pydantic import BaseModel

class WebSocketMessage(BaseModel):
    type: str
    payload: dict

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    while True:
        data = await websocket.receive_json()
        try:
            message = WebSocketMessage(**data)  # Pydantic validation
        except ValidationError as e:
            await websocket.send_json({"type": "error", "message": "Invalid message format"})
            continue
```

---

#### [ ] Missing Rate Limiting for Messages
**Location:** Backend message handlers, rate limiting middleware

- [ ] Check for per-connection message rate limits
- [ ] Verify protection against message flooding
- [ ] Ensure CPU-intensive operations have throttling
- [ ] Validate message size limits exist

---

#### [ ] Sensitive Data in WebSocket Messages
**Location:** Message payloads, logging statements

- [ ] Find messages containing tokens, passwords, or PII
- [ ] Check debug logs don't output full WebSocket messages
- [ ] Verify redaction in error messages
- [ ] Ensure separate channel for sensitive auth operations

---

## Section 2: State Synchronization

> ⚛️ REACT/TS - Zustand state management patterns
> 🐍 PYTHON/FASTAPI - Backend state broadcast logic
> ⚠️ AI-CODING RISK - Race conditions and state tearing extremely common

### 2.1 State Tearing & Race Conditions

#### [ ] Optimistic Update Conflicts
**Location:** Form submissions, inline editing, drag-and-drop handlers

- [ ] Find patterns where local state updates before server confirmation
- [ ] Check for WebSocket messages overwriting optimistic updates
- [ ] Verify conflict resolution mechanism exists
- [ ] Ensure version vectors or timestamps prevent data loss

**Common Failure Mode:**
1. User edits element label
2. UI updates immediately (optimistic)
3. WebSocket sends stale data from server
4. UI overwrites user's edit
5. User loses work

**⚠️ AI-CODING RISK:** Optimistic updates without rollback extremely common

**Expected Pattern:**
```typescript
// ⚛️ REACT/TS - Zustand store with version tracking
interface StageState {
  version: number;  // Server-provided version
  lastEditTimestamp?: number;  // Client-side edit tracking
  data: any;
}

const handleWebSocketUpdate = (update: any) => {
  const currentState = useStore.getState();

  // Don't overwrite recent local edits
  if (currentState.lastEditTimestamp &&
      Date.now() - currentState.lastEditTimestamp < 5000) {
    console.warn('Skipping stale update during active editing');
    return;
  }

  // Apply update only if version is newer
  if (update.version > currentState.version) {
    useStore.setState({ data: update.data, version: update.version });
  }
};
```

---

#### [ ] Concurrent Update Races
**Location:** Message handlers, state update logic

- [ ] Check for sequence numbers in message schema
- [ ] Verify handlers detect out-of-order messages
- [ ] Ensure message queuing with ordering exists
- [ ] Validate idempotent state transitions

**Common Failure Mode:**
- Stage 5 completion arrives before Stage 4 completion
- UI shows inconsistent state (Stage 5 done, Stage 4 pending)

**Expected Pattern:**
```typescript
// ⚛️ REACT/TS - Sequence number tracking
interface Message {
  sequenceNum: number;
  type: string;
  payload: any;
}

let expectedSequenceNum = 0;
const messageBuffer: Message[] = [];

const handleMessage = (msg: Message) => {
  if (msg.sequenceNum === expectedSequenceNum) {
    processMessage(msg);
    expectedSequenceNum++;

    // Process buffered messages
    while (messageBuffer[0]?.sequenceNum === expectedSequenceNum) {
      processMessage(messageBuffer.shift()!);
      expectedSequenceNum++;
    }
  } else if (msg.sequenceNum > expectedSequenceNum) {
    // Buffer out-of-order message
    messageBuffer.push(msg);
    messageBuffer.sort((a, b) => a.sequenceNum - b.sequenceNum);
  }
  // Ignore duplicate/old messages
};
```

---

#### [ ] Partial State Updates
**Location:** WebSocket handlers updating Zustand state

- [ ] Find updates to nested state without proper merging
- [ ] Check for shallow spread on deep structures
- [ ] Verify no direct assignment clobbering sibling properties
- [ ] Ensure immer or deep merge utilities used

**Common Failure Mode:**
```typescript
// ❌ BAD: Clobbers other properties
set({ stages: { ...state.stages, [5]: newStage5Data } });
// This overwrites state.stages[4], state.stages[6], etc.

// ✅ GOOD: Preserves sibling properties
set((state) => ({
  stages: state.stages.map((stage, idx) =>
    idx === 5 ? newStage5Data : stage
  )
}));
```

---

#### [ ] Zustand Selector Stale Closures
**Location:** useEffect/useCallback with Zustand selectors

- [ ] Find useEffect with Zustand selectors missing dependencies
- [ ] Check for stale closures capturing old state
- [ ] Verify subscriptions re-run on store changes
- [ ] Ensure `useStore.getState()` used in handlers instead of closures

**⚠️ AI-CODING RISK:** Stale closure bugs extremely subtle

**Expected Pattern:**
```typescript
// ❌ BAD: Stale closure
const documentId = useStore((state) => state.documentId);

useEffect(() => {
  ws.onmessage = (event) => {
    // documentId is stale! Captured from initial render
    console.log('Processing for doc:', documentId);
  };
}, []); // Missing documentId dependency

// ✅ GOOD: Use getState() for current value
useEffect(() => {
  ws.onmessage = (event) => {
    const currentDocId = useStore.getState().documentId;
    console.log('Processing for doc:', currentDocId);
  };
}, []); // No stale closure
```

---

### 2.2 Disconnect & Reconnection Resilience

#### [ ] Missing Disconnect Detection
**Location:** WebSocket onclose handlers, heartbeat monitoring

- [ ] Check for disconnect detection beyond onclose event
- [ ] Verify heartbeat timeout triggers disconnect state
- [ ] Ensure UI updates immediately on disconnect
- [ ] Validate no stale data shown indefinitely

**Expected Pattern:**
```typescript
// ⚛️ REACT/TS
const connectionStatus = useStore((state) => state.connectionStatus);

useEffect(() => {
  if (connectionStatus === 'disconnected') {
    // Show "Connection Lost" banner
    // Mark all data as potentially stale
    // Disable editing/submission
  }
}, [connectionStatus]);
```

---

#### [ ] Stale Data Indicator Missing
**Location:** UI components, data freshness tracking

- [ ] Find disconnect handlers that don't mark data as stale
- [ ] Check for missing "last synced" timestamps
- [ ] Verify stale indicators visible to user
- [ ] Ensure editing disabled when data is stale

**Key UI Elements:**
- [ ] "Last synced: X seconds ago" timestamp
- [ ] Yellow/red border around stale data
- [ ] "Offline" badge in header
- [ ] Disabled edit buttons with tooltip

---

#### [ ] Reconnection Without State Sync
**Location:** Reconnection handlers, state reconciliation logic

- [ ] Check reconnection fetches current state from server
- [ ] Verify delta updates requested (not just resubscribe)
- [ ] Ensure full state refresh available as fallback
- [ ] Validate no state drift after long disconnects

**Expected Pattern:**
```typescript
// ⚛️ REACT/TS
const onReconnect = async () => {
  const lastSyncTimestamp = useStore.getState().lastSyncTimestamp;

  // Request updates since last known state
  ws.send(JSON.stringify({
    type: 'sync_request',
    since: lastSyncTimestamp
  }));

  // Or fetch full state as fallback
  if (Date.now() - lastSyncTimestamp > 60000) {
    await fetchFullState();
  }
};
```

---

#### [ ] Reconnection Stampede
**Location:** Reconnection timing logic, backoff implementation

- [ ] Find reconnection without exponential backoff
- [ ] Check for missing jitter (±20% randomization)
- [ ] Verify maximum backoff cap exists (60s)
- [ ] Ensure no immediate retry on server error

**Already covered in Section 1.2, but critical for state sync**

---

#### [ ] Message Queue During Disconnect
**Location:** Client-side action buffering, conflict resolution

- [ ] Check if user actions during disconnect are queued
- [ ] Verify actions don't get lost on reconnect
- [ ] Ensure conflict resolution exists for queued actions
- [ ] Validate editing disabled vs queued (choose one strategy)

**Two Strategies:**
1. **Disable editing** during disconnect (simpler, prevents conflicts)
2. **Queue actions** and replay on reconnect (complex, better UX)

**If using queuing:**
```typescript
// ⚛️ REACT/TS
const actionQueue = useRef<Action[]>([]);

const onReconnect = async () => {
  // Fetch current state first
  await fetchFullState();

  // Replay queued actions with conflict detection
  for (const action of actionQueue.current) {
    const conflict = detectConflict(action);
    if (conflict) {
      await showConflictResolutionUI(action, conflict);
    } else {
      await executeAction(action);
    }
  }

  actionQueue.current = [];
};
```

---

### 2.3 Message Processing & Ordering

#### [ ] Missing Message Type Validation
**Location:** WebSocket message handlers, type guards

- [ ] Find handlers without type/schema validation
- [ ] Check for direct property access without type guards
- [ ] Verify `as` type assertions have validation
- [ ] Ensure malformed messages don't crash handler

**⚛️ REACT/TS - Expected Pattern:**
```typescript
import { z } from 'zod';

const MessageSchema = z.discriminatedUnion('type', [
  z.object({ type: z.literal('stage_update'), payload: z.object({...}) }),
  z.object({ type: z.literal('error'), message: z.string() }),
  z.object({ type: z.literal('ping'), ts: z.number() }),
]);

ws.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    const message = MessageSchema.parse(data);  // Throws if invalid

    // message is now type-safe
    switch (message.type) {
      case 'stage_update': ...
      case 'error': ...
      case 'ping': ...
    }
  } catch (e) {
    console.error('Invalid message:', e);
  }
};
```

---

#### [ ] Unhandled Message Types
**Location:** Message type switch/if-else chains

- [ ] Check for missing default case in switch statements
- [ ] Verify exhaustive type checking (TypeScript exhaustiveness)
- [ ] Ensure unknown message types are logged
- [ ] Validate version negotiation for new message types

**Expected Pattern:**
```typescript
// ⚛️ REACT/TS
const handleMessage = (message: Message) => {
  switch (message.type) {
    case 'stage_update':
      handleStageUpdate(message.payload);
      break;
    case 'error':
      handleError(message.message);
      break;
    case 'ping':
      handlePing(message.ts);
      break;
    default:
      // Log unknown types for debugging
      console.warn('Unknown message type:', (message as any).type);
      // Optional: Send to analytics for version tracking
  }
};
```

---

#### [ ] Blocking Message Processing
**Location:** WebSocket message handlers, heavy computations

- [ ] Find synchronous heavy operations in message handlers
- [ ] Check for large array transformations blocking UI
- [ ] Verify deep object cloning uses async patterns
- [ ] Ensure DOM manipulation doesn't block message queue

**⚠️ AI-CODING RISK:** Synchronous processing in handlers extremely common

**Expected Pattern:**
```typescript
// ⚛️ REACT/TS
ws.onmessage = async (event) => {
  const data = JSON.parse(event.data);

  // Defer heavy processing
  requestIdleCallback(() => {
    processHeavyUpdate(data);
  });

  // Or use microtask
  await Promise.resolve();
  processMediumUpdate(data);
};
```

---

#### [ ] Message Ordering Assumptions
**Location:** State machines, increment-only logic

- [ ] Check for state machines without out-of-order handling
- [ ] Verify increment-only logic handles gaps
- [ ] Ensure sequence gap detection exists
- [ ] Validate buffering or retransmission for gaps

**Already covered in Section 2.1, but critical for processing**

---

### 2.4 State Consistency & Synchronization

#### [ ] Multiple Sources of Truth
**Location:** Component state, Zustand stores, refs

- [ ] Find state duplicated between Zustand and useState
- [ ] Check for refs holding copies of store data
- [ ] Verify derived state is not stored separately
- [ ] Ensure single source of truth principle

**Common Anti-Pattern:**
```typescript
// ❌ BAD: Multiple sources of truth
const [localDocStatus, setLocalDocStatus] = useState('idle');
const storeDocStatus = useStore((state) => state.documentStatus);

useEffect(() => {
  // WebSocket updates store, but local state not updated!
  ws.onmessage = (event) => {
    if (event.data.type === 'status_update') {
      useStore.setState({ documentStatus: event.data.status });
      // Forgot to update localDocStatus!
    }
  };
}, []);

// ✅ GOOD: Single source of truth
const docStatus = useStore((state) => state.documentStatus);
// Derive everything from store
```

---

#### [ ] Derived State Not Updating
**Location:** Memoized values, computed stores

- [ ] Find memoized values with missing dependencies
- [ ] Check for cached computations without invalidation
- [ ] Verify Zustand selectors have proper equality checks
- [ ] Ensure computed stores recalculate on WebSocket updates

**Expected Pattern:**
```typescript
// ⚛️ REACT/TS
const canEdit = useStore((state) => {
  // Selector recomputes when documentStatus changes
  return state.documentStatus === 'idle' &&
         state.connectionStatus === 'connected';
}, shallow);  // Use shallow equality for objects
```

---

#### [ ] Cross-Tab State Drift
**Location:** Multi-tab support, BroadcastChannel usage

- [ ] Find applications without cross-tab synchronization
- [ ] Check if each tab has independent WebSocket connection
- [ ] Verify no BroadcastChannel or SharedWorker usage
- [ ] Ensure UX acknowledges multi-tab limitations (if accepting drift)

**Two Strategies:**
1. **Accept drift** with clear UX ("Changes in other tabs not reflected")
2. **Sync via BroadcastChannel** for shared state

**If syncing:**
```typescript
// ⚛️ REACT/TS
const channel = new BroadcastChannel('docling-state');

// Send local updates to other tabs
const updateStore = (update: any) => {
  useStore.setState(update);
  channel.postMessage({ type: 'store_update', update });
};

// Receive updates from other tabs
channel.onmessage = (event) => {
  if (event.data.type === 'store_update') {
    useStore.setState(event.data.update);
  }
};
```

---

#### [ ] Undo/Redo Stack Corruption
**Location:** Undo/redo implementation, history management

- [ ] Check if undo/redo stack invalidated by WebSocket updates
- [ ] Verify undo doesn't revert to pre-WebSocket state
- [ ] Ensure undo stack cleared or merged on server updates
- [ ] Validate no conflicts when undoing after sync

**Expected Pattern:**
```typescript
// ⚛️ REACT/TS
const handleWebSocketUpdate = (update: any) => {
  useStore.setState(update);

  // Clear undo stack on server update
  useStore.setState({ undoStack: [], redoStack: [] });

  // Or: Merge server update into undo stack
  // (requires operational transformation)
};
```

---

### 2.5 Backend WebSocket Patterns

#### [ ] Missing Connection Lifecycle Management
**Location:** `backend/websocket/manager.py`, connection tracking

- [ ] Find WebSocket endpoints without try/finally cleanup
- [ ] Check for connections not removed from manager on disconnect
- [ ] Verify WebSocketDisconnect exception handling exists
- [ ] Ensure periodic cleanup of stale connections

**🐍 PYTHON/FASTAPI - Expected Pattern:**
```python
@app.websocket("/ws/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: str):
    await websocket.accept()
    await connection_manager.connect(document_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(document_id, data)
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {document_id}")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
    finally:
        await connection_manager.disconnect(document_id, websocket)
```

---

#### [ ] Broadcast Without Filtering
**Location:** Broadcast/notification logic

- [ ] Find global broadcast lists (all updates to all clients)
- [ ] Check for missing room/topic filtering
- [ ] Verify per-document subscription exists
- [ ] Ensure bandwidth not wasted on irrelevant updates

**Expected Pattern:**
```python
# 🐍 PYTHON/FASTAPI
class ConnectionManager:
    def __init__(self):
        # Group connections by document ID
        self.connections: dict[str, set[WebSocket]] = {}

    async def broadcast_to_document(self, document_id: str, message: dict):
        if document_id in self.connections:
            for websocket in self.connections[document_id]:
                try:
                    await websocket.send_json(message)
                except:
                    # Handle stale connections
                    pass
```

---

#### [ ] Missing Rate Limiting
**Location:** Message handler entry points

- [ ] Find WebSocket message handlers without rate limiting
- [ ] Check for no throttling on client messages
- [ ] Verify message size limits exist
- [ ] Ensure slow consumer detection exists

**🐍 PYTHON/FASTAPI - Expected Pattern:**
```python
from collections import defaultdict
from time import time

class RateLimiter:
    def __init__(self, max_per_minute: int = 60):
        self.max_per_minute = max_per_minute
        self.requests: defaultdict[str, list[float]] = defaultdict(list)

    def check(self, client_id: str) -> bool:
        now = time()
        # Remove old timestamps
        self.requests[client_id] = [
            ts for ts in self.requests[client_id]
            if now - ts < 60
        ]

        if len(self.requests[client_id]) >= self.max_per_minute:
            return False

        self.requests[client_id].append(now)
        return True
```

---

#### [ ] Synchronous Database in WebSocket Handler
**Location:** Database operations in async WebSocket handlers

- [ ] Find blocking database calls in async handlers
- [ ] Check for SQLite writes without `run_in_executor`
- [ ] Verify synchronous ORM calls wrapped properly
- [ ] Ensure event loop not blocked by I/O

**🐍 PYTHON/FASTAPI - Expected Pattern:**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    while True:
        data = await websocket.receive_json()

        # ❌ BAD: Blocks event loop
        # db.execute("UPDATE documents SET ...")

        # ✅ GOOD: Run in executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: db.execute("UPDATE ..."))
```

---

#### [ ] Missing Message Acknowledgment
**Location:** Critical message send operations

- [ ] Find fire-and-forget send patterns for critical messages
- [ ] Check for missing delivery confirmation
- [ ] Verify no application-level ACKs for important updates
- [ ] Ensure acceptable to lose messages or implement ACKs

**Two Strategies:**
1. **Accept loss** for non-critical updates (progress, status)
2. **Implement ACKs** for critical updates (stage completion, errors)

---

### 2.6 Error Handling & Recovery

#### [ ] Uncaught Exceptions in WebSocket Handler
**Location:** Message handler try/catch coverage

- [ ] Find message handlers that can throw without try/catch
- [ ] Check for JSON parsing without error handling
- [ ] Verify property access on undefined wrapped in try/catch
- [ ] Ensure one bad message doesn't close entire connection

**🐍 PYTHON/FASTAPI - Expected Pattern:**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    while True:
        try:
            data = await websocket.receive_json()
            message = WebSocketMessage(**data)  # Pydantic validation
            await handle_message(message)
        except ValidationError as e:
            await websocket.send_json({"type": "error", "message": str(e)})
            continue  # Don't close connection
        except Exception as e:
            logger.exception("Message handler error")
            await websocket.send_json({"type": "error", "message": "Internal error"})
```

---

#### [ ] Missing Error Propagation to UI
**Location:** Server error to client error message flow

- [ ] Find server errors not communicated to client
- [ ] Check for silent failures without user notification
- [ ] Verify error message type exists in schema
- [ ] Ensure Zustand has error state for UI display

**Expected Flow:**
1. Server error occurs during processing
2. Server sends `{ type: 'error', message: '...' }` to client
3. Client updates Zustand error state
4. UI shows toast/notification to user

---

#### [ ] Reconnection Loop Without User Intervention
**Location:** Reconnection max attempts, circuit breaker

- [ ] Find infinite reconnection attempts without limit
- [ ] Check for no "give up" state after max retries
- [ ] Verify manual reconnect button exists
- [ ] Ensure clear error state shown to user

**Expected Pattern:**
```typescript
// ⚛️ REACT/TS
const MAX_RECONNECT_ATTEMPTS = 10;
let reconnectAttempts = 0;

const attemptReconnect = () => {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    useStore.setState({
      connectionStatus: 'failed',
      errorMessage: 'Could not reconnect. Click to retry manually.'
    });
    return;
  }

  reconnectAttempts++;
  const delay = getReconnectDelay(reconnectAttempts);
  setTimeout(() => connect(), delay);
};
```

---

#### [ ] Partial Message Handling
**Location:** Message fragmentation handling

- [ ] Check if WebSocket handles fragmented messages
- [ ] Verify large messages buffered correctly
- [ ] Ensure WebSocket library handles framing
- [ ] Validate no assumptions about message completeness

**Note:** Most WebSocket libraries (browser, Starlette) handle framing automatically, but verify for large messages (>1MB)

---

### 2.7 Testing & Observability

#### [ ] Missing Connection State Tests
**Location:** Test suites for WebSocket functionality

- [ ] Check for tests verifying disconnect/reconnect behavior
- [ ] Verify simulated network failures in tests
- [ ] Ensure timeout scenarios tested
- [ ] Validate stale indicator tests exist

**Expected Tests:**
```typescript
// ⚛️ REACT/TS - Example with Jest + React Testing Library
test('shows stale indicator on disconnect', () => {
  const { getByText } = render(<App />);

  // Simulate disconnect
  act(() => {
    mockWebSocket.triggerClose();
  });

  expect(getByText(/connection lost/i)).toBeInTheDocument();
  expect(getByText(/stale/i)).toBeInTheDocument();
});
```

---

#### [ ] Missing Race Condition Tests
**Location:** Concurrent update test scenarios

- [ ] Find tests for concurrent state updates
- [ ] Check for out-of-order message injection tests
- [ ] Verify timing variation tests exist
- [ ] Ensure fuzz testing for message ordering

**Expected Tests:**
```typescript
test('handles out-of-order messages correctly', () => {
  const messages = [
    { sequenceNum: 1, type: 'update', payload: 'A' },
    { sequenceNum: 3, type: 'update', payload: 'C' },
    { sequenceNum: 2, type: 'update', payload: 'B' },
  ];

  messages.forEach(msg => handleMessage(msg));

  // Should process in order: A, B, C
  expect(getProcessedOrder()).toEqual(['A', 'B', 'C']);
});
```

---

#### [ ] No Connection Metrics
**Location:** Monitoring/observability infrastructure

- [ ] Check for connection count tracking
- [ ] Verify message rate metrics exist
- [ ] Ensure reconnection frequency tracked
- [ ] Validate latency percentiles measured

**Expected Metrics:**
- `websocket_connections_active` (gauge)
- `websocket_messages_received_total` (counter)
- `websocket_reconnections_total` (counter)
- `websocket_message_latency_seconds` (histogram)

---

#### [ ] Missing Client-Side Error Tracking
**Location:** Error monitoring integration (Sentry, LogRocket)

- [ ] Find WebSocket errors not captured in monitoring
- [ ] Check for missing connection state context in errors
- [ ] Verify error aggregation exists
- [ ] Ensure WebSocket errors tagged/categorized

**Expected Pattern:**
```typescript
// ⚛️ REACT/TS
import * as Sentry from '@sentry/react';

ws.onerror = (event) => {
  Sentry.captureException(new Error('WebSocket error'), {
    tags: {
      component: 'websocket',
      connectionState: useStore.getState().connectionStatus
    },
    extra: {
      url: ws.url,
      readyState: ws.readyState
    }
  });
};
```

---

## Summary Checklist

### Connection Reliability (Section 1)
- [ ] Connection state machine implemented
- [ ] Proper cleanup on unmount/navigation
- [ ] Authentication validation on connect
- [ ] Concurrent connection limits enforced
- [ ] Automatic reconnection with exponential backoff
- [ ] State sync on reconnect (delta or full refresh)
- [ ] User feedback during reconnection
- [ ] Message queuing during disconnect
- [ ] Message ordering and deduplication
- [ ] Heartbeat implementation (30s ping/pong)
- [ ] Close code handling with different retry logic
- [ ] Graceful degradation (UI works without WebSocket)
- [ ] WebSocket authentication and authorization
- [ ] Message schema validation (Pydantic/Zod)
- [ ] Rate limiting for incoming messages

### State Synchronization (Section 2)
- [ ] Optimistic update conflict resolution
- [ ] Sequence numbers for message ordering
- [ ] Partial state update protection (immer/deep merge)
- [ ] Stale closure prevention (getState() in handlers)
- [ ] Disconnect detection with UI indicators
- [ ] Stale data indicators and editing locks
- [ ] State reconciliation on reconnect
- [ ] Message type validation with type guards
- [ ] Exhaustive message type handling
- [ ] Non-blocking message processing
- [ ] Single source of truth (no duplicate state)
- [ ] Derived state recalculates on updates
- [ ] Cross-tab state strategy (accept drift or sync)
- [ ] Undo/redo stack invalidation on sync
- [ ] Backend connection lifecycle management
- [ ] Room-based broadcast filtering
- [ ] Backend rate limiting
- [ ] Async database operations (run_in_executor)
- [ ] Error propagation to UI
- [ ] Reconnection circuit breaker (max attempts)
- [ ] Tests for disconnect/reconnect scenarios
- [ ] Tests for race conditions
- [ ] Connection metrics and monitoring
- [ ] Client-side error tracking (Sentry)

---

## Priority Fix Recommendations

### Fix Now (P0 - Before Production)
1. **Implement heartbeat mechanism** (Section 1.4)
   - 30s ping/pong with 10s timeout
   - Prevents zombie connections and proxy timeouts
2. **Add exponential backoff for reconnection** (Section 1.2)
   - Prevents thundering herd on server recovery
3. **Validate messages on both ends** (Section 1.6, 2.3)
   - Pydantic on backend, Zod on frontend
   - Prevents crashes from malformed messages
4. **State reconciliation on reconnect** (Section 2.2)
   - Fetch full state or delta on reconnect
   - Prevents state drift after outages
5. **Close code handling** (Section 1.5)
   - Different retry logic per close code
   - Proper auth expiry handling (4001)

### Fix Soon (P1 - Next Iteration)
1. **Message ordering with sequence numbers** (Section 2.1)
   - Prevents state corruption from reordering
2. **Connection state machine** (Section 1.1)
   - Clear state transitions and error handling
3. **Message queue during disconnect** (Section 1.3)
   - Prevents message loss during brief outages
4. **Stale data indicators** (Section 2.2)
   - Clear UX when data is not fresh
5. **Backend connection filtering** (Section 2.5)
   - Room-based subscriptions to reduce bandwidth

### Monitor (P2 - Watch Metrics)
1. **Cross-tab state sync** (Section 2.4)
   - BroadcastChannel if multi-tab issues reported
2. **Optimistic update conflicts** (Section 2.1)
   - Version vectors if user reports lost edits
3. **Message deduplication** (Section 1.3)
   - If metrics show duplicate processing
4. **Undo/redo stack handling** (Section 2.4)
   - If undo feature exists and conflicts reported

---

## Testing Recommendations

### Unit Tests
- Mock WebSocket with controllable states
- Test message handlers in isolation
- Verify state updates for each message type
- Test reconnection backoff calculations

### Integration Tests
- Playwright with WebSocket interception
- Simulate network disconnect during editing
- Test multi-tab scenarios (if applicable)
- Verify end-to-end message flow

### Chaos Testing
- Network Link Conditioner for latency simulation
- `tc` (traffic control) for packet loss
- Server restart during active connections
- Message flood testing (rate limiting)

### Manual Testing
- Open multiple browser tabs
- Disconnect WiFi during active editing
- Leave connection idle for 2+ minutes
- Rapid successive edits (race conditions)

---

## Key Metrics to Track

### Backend (Prometheus/CloudWatch)
- `websocket_connections_active` - Active connection count
- `websocket_connections_total` - Total connections (lifetime)
- `websocket_disconnects_total` - Disconnect count by close code
- `websocket_messages_received_total` - Messages received
- `websocket_messages_sent_total` - Messages sent
- `websocket_broadcast_duration_seconds` - Broadcast latency
- `websocket_heartbeat_failures_total` - Missed pongs

### Frontend (Analytics/Sentry)
- Connection state changes (connect/disconnect count)
- Reconnection attempts and success rate
- Message processing latency (p50/p95/p99)
- Out-of-order message count
- State reconciliation count
- WebSocket error rate by type

### Alerting Thresholds
- Reconnection rate > 10/min per client
- Heartbeat failure rate > 5%
- Message queue depth > 100
- Average message latency > 1s
- Connection error rate > 10%

---

## Next Steps

1. **Audit Execution:**
   - Use this checklist to review `backend/websocket/` and `frontend/src/utils/websocket.ts`
   - Document findings for each [ ] checkbox item
   - Prioritize fixes based on severity (P0/P1/P2)

2. **Implementation:**
   - Start with "Fix Now" items (heartbeat, backoff, validation)
   - Add tests for each fix before marking complete
   - Update metrics/monitoring infrastructure

3. **Validation:**
   - Run chaos testing suite
   - Manual testing with network throttling
   - Load testing with multiple concurrent connections
   - Monitor metrics for 24-48 hours before production deploy

4. **Documentation:**
   - Document WebSocket message schema
   - Document close codes and retry logic
   - Document monitoring and alerting setup
   - Create runbook for WebSocket issues
