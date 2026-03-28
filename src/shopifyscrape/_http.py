"""HTTP transport layer for shopifyscrape using requests."""

from __future__ import annotations

import logging
import random
import time

import requests

from shopifyscrape.exceptions import RateLimitError, RequestError

logger = logging.getLogger('shopifyscrape.http')

DEFAULT_HEADERS: dict[str, str] = {
    'Accept': 'application/json',
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/136.0.0.0 Safari/537.36'
    ),
}


class HTTPClient:
    """HTTP client with retry logic and optional proxy.

    Uses ``requests.Session`` for connection pooling.
    No explicit ``.close()`` required — the session is cleaned up on garbage collection.

    Args:
        proxy: Optional proxy URL (e.g. ``'http://user:pass@host:port'``).
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts on transient failures.
    """

    RETRYABLE_STATUS_CODES: tuple[int, ...] = (429, 430, 500, 502, 503, 504)

    def __init__(
        self,
        proxy: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self._proxy = proxy
        self._timeout = timeout
        self._max_retries = max_retries
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        if self._proxy:
            session.proxies = {'http': self._proxy, 'https': self._proxy}
        return session

    @staticmethod
    def _backoff_delay(attempt: int) -> float:
        """Exponential backoff with jitter."""
        base = min(2 ** attempt, 30)
        jitter = random.uniform(0, base * 0.5)
        return base + jitter

    def get(self, url: str) -> requests.Response:
        """Send a GET request with retry logic.

        Args:
            url: Full URL to GET.

        Returns:
            Response object.

        Raises:
            RateLimitError: On HTTP 429/430 after all retries.
            RequestError: On other HTTP errors after all retries.
        """
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = self._session.get(url, timeout=self._timeout)

                if response.status_code == 200:
                    return response

                if response.status_code in (429, 430):
                    last_error = RateLimitError()
                    if attempt < self._max_retries:
                        delay = self._backoff_delay(attempt)
                        logger.warning(
                            'Rate limited (attempt %d/%d), retrying in %.1fs',
                            attempt + 1, self._max_retries + 1, delay,
                        )
                        time.sleep(delay)
                        continue
                    raise last_error

                if response.status_code in self.RETRYABLE_STATUS_CODES:
                    last_error = RequestError(response.status_code)
                    if attempt < self._max_retries:
                        delay = self._backoff_delay(attempt)
                        logger.warning(
                            'HTTP %d (attempt %d/%d), retrying in %.1fs',
                            response.status_code, attempt + 1,
                            self._max_retries + 1, delay,
                        )
                        time.sleep(delay)
                        continue

                raise RequestError(response.status_code, response.text[:200])

            except (requests.ConnectionError, requests.Timeout) as exc:
                last_error = exc
                if attempt < self._max_retries:
                    delay = self._backoff_delay(attempt)
                    logger.warning(
                        'Request failed (attempt %d/%d): %s, retrying in %.1fs',
                        attempt + 1, self._max_retries + 1, exc, delay,
                    )
                    time.sleep(delay)
                    continue

        raise RequestError(0, f'Request failed after {self._max_retries + 1} attempts: {last_error}')
