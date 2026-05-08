"""Pipeline tracker — collects agent step events during a query run.

Each agent calls `tracker.emit(step_name, detail)` as it starts.
The API server reads these events to stream progress to the frontend.
Uses a simple thread-local queue so concurrent requests don't mix events.
"""
import threading
import time

_local = threading.local()


def _get_queue():
    if not hasattr(_local, "queue"):
        _local.queue = []
    return _local.queue


def start_run():
    """Clear the queue at the start of a new query."""
    _local.queue = []
    _local.start_time = time.perf_counter()


def emit(step: str, detail: str = ""):
    """Record an agent step event."""
    elapsed = round((time.perf_counter() - getattr(_local, "start_time", time.perf_counter())) * 1000)
    _get_queue().append({
        "step": step,
        "detail": detail,
        "elapsed_ms": elapsed,
    })


def get_steps() -> list[dict]:
    return list(_get_queue())
