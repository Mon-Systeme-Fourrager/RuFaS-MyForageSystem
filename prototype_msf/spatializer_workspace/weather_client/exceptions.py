"""
exceptions.py — Open-Meteo client, MSFourrager

Exception hierarchy for Open-Meteo failures.

All exceptions derive from :class:`WeatherError`, so a caller that does not
care about the distinction can catch that one type.

Open-Meteo reports failures as HTTP 400 with a JSON body of the shape
``{"error": true, "reason": "<message>"}`` (confirmed live 2026-09-11). The
``reason`` is the only place the actual problem is described, so it is
extracted onto :attr:`WeatherError.reason` rather than left buried in the
raw body.
"""

from typing import Optional


class WeatherError(Exception):
    """
    Base class for every Open-Meteo client failure.

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
    reason
        The API's own ``reason`` field, when the body carried one.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.status_code: Optional[int] = status_code
        self.response_text: Optional[str] = response_text
        self.reason: Optional[str] = reason

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code is not None:
            parts.append(f"(HTTP {self.status_code})")
        if self.reason:
            parts.append(f"reason: {self.reason}")
        elif self.response_text:
            parts.append(f"body: {self.response_text}")
        return " ".join(parts)


class WeatherHTTPError(WeatherError):
    """
    The API answered with a non-2xx status.

    Open-Meteo uses HTTP 400 for every caller-side problem — an out-of-range
    coordinate and an unknown variable name both land here, distinguished
    only by :attr:`WeatherError.reason`.
    """


class WeatherTimeoutError(WeatherError):
    """
    The request did not complete within the configured timeout.

    Transport-level, so ``status_code``, ``response_text`` and ``reason``
    are all ``None``.
    """


class WeatherValidationError(WeatherError):
    """
    Client-side validation failure — the request was never sent.

    Raised for arguments this client can reject without a round trip:
    out-of-range latitude or longitude, a non-positive forecast window, or a
    window beyond what the API serves. Also raised when a response parses as
    JSON but lacks the structure the caller asked for.
    """
