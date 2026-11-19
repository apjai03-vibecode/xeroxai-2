"""Telemetry and observability module for XeroxAI 2.0.

Provides Sentry distributed tracing integration with local ring-buffer span storage
for live counter cockpit monitoring and zero-cloud fallback capability.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Generator, Optional
import sentry_sdk

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory telemetry buffer for local counter dashboard monitoring
RECENT_SPANS: list[dict[str, Any]] = []
MAX_BUFFER_SIZE = 50


def init_telemetry() -> None:
    """Initializes the Sentry SDK with performance and distributed tracing.

    If SENTRY_DSN is not configured, initializes Sentry in local tracing mode
    so spans continue to function in-memory without network transmission.
    """
    try:
        if settings.SENTRY_DSN:
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                traces_sample_rate=settings.TRACES_SAMPLE_RATE,
                send_default_pii=False,
                _experiments={
                    "enable_metrics": True,
                },
            )
            logger.info("Sentry tracing initialized with configured DSN.")
        else:
            # Initializing without DSN allows start_span to function as a local tracer
            sentry_sdk.init(
                dsn=None,
                traces_sample_rate=1.0,
                send_default_pii=False,
            )
            logger.info("Sentry initialized in local in-memory tracing mode.")
    except Exception as exc:
        logger.warning("Failed to initialize Sentry telemetry: %s", exc)


@contextmanager
def trace_span(
    op: str,
    description: str,
    tags: Optional[dict[str, str]] = None,
    data: Optional[dict[str, Any]] = None,
) -> Generator[Any, None, None]:
    """Context manager wrapping pipeline steps in a distributed trace span.

    Args:
        op: Operation category name (e.g., 'image.processing', 'smartdoc.enhancement').
        description: Human-readable task description.
        tags: Optional key-value tags to attach to the span.
        data: Optional contextual metadata parameters.

    Yields:
        The active Sentry span object.

    Raises:
        Exception: Re-raises any exception raised within the managed block
            after capturing it to Sentry and logging error status.
    """
    start_time = time.perf_counter()
    status = "ok"
    error_msg: Optional[str] = None
    span_tags = tags or {}
    span_data = data or {}

    with sentry_sdk.start_span(op=op, name=description) as span:
        for k, v in span_tags.items():
            span.set_tag(k, v)
        for k, v in span_data.items():
            span.set_data(k, v)

        try:
            yield span
        except Exception as exc:
            status = "error"
            error_msg = str(exc)
            span.set_tag("status", "error")
            span.set_data("error", error_msg)
            sentry_sdk.capture_exception(exc)
            logger.error("Span '%s' (%s) failed: %s", op, description, exc)
            raise
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            span.set_data("duration_ms", duration_ms)
            span.set_tag("status", status)

            # Record into local telemetry buffer for operator dashboard
            record: dict[str, Any] = {
                "op": op,
                "description": description,
                "duration_ms": duration_ms,
                "status": status,
                "tags": span_tags,
                "data": {k: str(v) for k, v in span_data.items()},
                "timestamp": time.time(),
                "error": error_msg,
            }
            RECENT_SPANS.append(record)
            if len(RECENT_SPANS) > MAX_BUFFER_SIZE:
                RECENT_SPANS.pop(0)


def get_recent_telemetry() -> list[dict[str, Any]]:
    """Returns the most recent 20 executed spans in reverse chronological order.

    Returns:
        List of span records formatted for counter dashboard visualization.
    """
    return list(reversed(RECENT_SPANS[-20:]))
