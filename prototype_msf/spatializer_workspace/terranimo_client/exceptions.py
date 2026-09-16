"""
exceptions.py — Terranimo API client, MSFourrager

Exception hierarchy for Terranimo REST API failures.

All exceptions derive from :class:`TerranimoError`, so a caller that does not
care about the distinction can catch that one type.

Every exception carries the HTTP status code and the raw response body when
one was available. The body matters: the Terranimo spec maps 400/401/403/500
onto the ``ProblemDetails`` schema, and the useful message is inside it — the
status line alone does not say what was wrong with a payload.
"""

from typing import Optional


class TerranimoError(Exception):
    """
    Base class for every Terranimo client failure.

    Parameters
    ----------
    message
        Human-readable description of what failed.
    status_code
        HTTP status code, when the failure came from a completed response.
        ``None`` for transport-level failures (timeout, connection refused).
    response_text
        Raw response body, verbatim and untruncated. ``None`` when no
        response was received or the body was empty.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.status_code: Optional[int] = status_code
        self.response_text: Optional[str] = response_text

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code is not None:
            parts.append(f"(HTTP {self.status_code})")
        if self.response_text:
            parts.append(f"body: {self.response_text}")
        return " ".join(parts)


class TerranimoAuthError(TerranimoError):
    """
    Authentication or authorization failure — HTTP 401 or 403.

    Raised when the Bearer token is missing, malformed, expired, or lacks
    access to the requested operation. The spec applies Bearer auth to all
    48 operations, so this can surface on any call including ``/ping``.
    """


class TerranimoValidationError(TerranimoError):
    """
    Request rejected by the API — HTTP 400.

    The payload reached Terranimo but failed its validation. The spec
    documents zero request examples, so the ``ProblemDetails`` body carried
    on this exception is usually the only description of what was wrong.
    """


class TerranimoServerError(TerranimoError):
    """
    Terranimo-side failure — HTTP 500 or above.

    Not caused by the caller's payload. Retrying may succeed; this client
    does not retry on its own.
    """


class TerranimoTimeoutError(TerranimoError):
    """
    The request did not complete within the configured timeout.

    Transport-level, so ``status_code`` and ``response_text`` are ``None``.
    The spec documents no response-time guarantee; see
    :data:`terranimo_client.config.DEFAULT_TIMEOUT_SECONDS`.
    """
