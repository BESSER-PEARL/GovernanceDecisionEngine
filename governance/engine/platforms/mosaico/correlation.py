"""Correlates an AISP ``evaluate-collaboration`` request with the eventual
``Decision`` produced by the engine's FSM.

The AISP request/response cycle is synchronous (see docs/aisp-interface.md),
but the engine processes events asynchronously on its own session event loop
(``agent.receive_event`` only enqueues the event). ``decide_bodybuilder``
resolves the future registered here once a terminal ``Decision`` exists for
the collaboration, letting the AISP executor thread block on it without
coupling to BAF's internals any further than reading ``collab._is_decided``.
"""

import threading
from concurrent.futures import Future

_pending: dict[int, Future] = {}
_lock = threading.Lock()


def register(collaboration_id: int) -> Future:
    """Register a collaboration as awaiting a decision, returning its future."""
    future: Future = Future()
    with _lock:
        _pending[collaboration_id] = future
    return future


def resolve_if_pending(collaboration_id: int, decision) -> None:
    """Resolve the pending future for this collaboration, if any is registered."""
    with _lock:
        future = _pending.pop(collaboration_id, None)
    if future is not None and not future.done():
        future.set_result(decision)


def cancel(collaboration_id: int) -> None:
    """Drop a pending registration, e.g. after a timeout."""
    with _lock:
        _pending.pop(collaboration_id, None)
