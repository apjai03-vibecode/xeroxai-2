import time
from contextlib import contextmanager
from typing import Any, Optional
import sentry_sdk
from app.config import settings

# In-memory telemetry buffer for local counter dashboard monitoring
RECENT_SPANS: list[dict[str, Any]] = []
MAX_BUFFER_SIZE = 50

def init_telemetry():
    """Initializes Sentry SDK with performance and distributed tracing enabled."""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=settings.TRACES_SAMPLE_RATE,
            send_default_pii=False,
            _experiments={
                "enable_metrics": True,
            }
        )
    else:
        # Initializing without DSN allows start_span to function as a local no-op/tracer
        sentry_sdk.init(
            dsn=None,
            traces_sample_rate=1.0,
            send_default_pii=False,
        )

@contextmanager
def trace_span(op: str, description: str, tags: Optional[dict[str, str]] = None, data: Optional[dict[str, Any]] = None):
    """
    Context manager wrapping operations in a Sentry span and recording
    execution metrics for local counter telemetry.
    """
    start_time = time.perf_counter()
    status = "ok"
    error_msg = None
    tags = tags or {}
    data = data or {}
    
    with sentry_sdk.start_span(op=op, name=description) as span:
        for k, v in tags.items():
            span.set_tag(k, v)
        for k, v in data.items():
            span.set_data(k, v)
            
        try:
            yield span
        except Exception as exc:
            status = "error"
            error_msg = str(exc)
            span.set_tag("status", "error")
            span.set_data("error", error_msg)
            sentry_sdk.capture_exception(exc)
            raise
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            span.set_data("duration_ms", duration_ms)
            span.set_tag("status", status)
            
            # Record into local telemetry buffer for operator dashboard
            record = {
                "op": op,
                "description": description,
                "duration_ms": duration_ms,
                "status": status,
                "tags": tags,
                "data": {k: str(v) for k, v in data.items()},
                "timestamp": time.time(),
                "error": error_msg,
            }
            RECENT_SPANS.append(record)
            if len(RECENT_SPANS) > MAX_BUFFER_SIZE:
                RECENT_SPANS.pop(0)

def get_recent_telemetry() -> list[dict[str, Any]]:
    return list(reversed(RECENT_SPANS[-20:]))
