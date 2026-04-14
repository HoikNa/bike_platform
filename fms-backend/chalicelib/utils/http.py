"""HTTP helpers for Chalice handlers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from chalice import Response


def json_response(*, data: Any, status_code: int = 200, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a consistent JSON response shape.

    The frontend can rely on this shape:
        {"status": 200, "data": [...], "meta": {...}}
    """

    payload: Dict[str, Any] = {"status": status_code, "data": data}
    if meta is not None:
        payload["meta"] = meta
    return payload


def error_response(message: str, status_code: int) -> Response:
    """Return consistent JSON error response with Chalice Response."""

    return Response(
        body={"error": message, "status": status_code},
        status_code=status_code,
        headers={"Content-Type": "application/json"},
    )

