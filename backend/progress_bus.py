import asyncio
from typing import Dict, Any, List

# List of queues for connected SSE clients
_listeners: List[asyncio.Queue[Dict[str, Any]]] = []


def register_listener() -> asyncio.Queue:  # Queue[Dict[str, Any]]
    """Return a new queue and add it to the listener list."""
    q: asyncio.Queue = asyncio.Queue()
    _listeners.append(q)  # type: ignore[arg-type]
    return q


def remove_listener(q: asyncio.Queue):
    try:
        _listeners.remove(q)  # type: ignore[arg-type]
    except ValueError:
        pass


def push(event: Dict[str, Any]):
    """Push an event to all listening queues without blocking."""
    for q in list(_listeners):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            # uncommon; skip if queue can't accept more msgs
            pass
