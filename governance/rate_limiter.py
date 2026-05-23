"""
governance/rate_limiter.py - Token and request rate limiting for API governance
"""

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional
from config import GOVERNANCE_CONFIG


@dataclass
class RateLimitResult:
    allowed: bool
    reason: str = ""
    retry_after_seconds: float = 0.0
    current_rpm: int = 0
    limit_rpm: int = 0


class RateLimiter:
    """
    Sliding window rate limiter that tracks:
    - Requests per minute (RPM)
    - Estimated tokens per minute (TPM)

    Used to prevent API abuse and control costs.
    """

    def __init__(self):
        self.config = GOVERNANCE_CONFIG
        self.max_rpm = self.config.get("rate_limit_requests_per_minute", 20)
        self.max_tpm = self.config.get("rate_limit_tokens_per_minute", 100000)

        # Sliding window queues: store timestamps
        self._request_window: deque = deque()
        self._token_window: deque = deque()

        # Tracking
        self.total_requests = 0
        self.total_tokens_estimated = 0
        self.blocked_requests = 0

    def _clean_window(self, window: deque, window_seconds: int = 60) -> None:
        """Remove entries older than window_seconds from the deque."""
        cutoff = time.time() - window_seconds
        while window and window[0] < cutoff:
            window.popleft()

    def check_request(self, estimated_tokens: int = 1000) -> RateLimitResult:
        """
        Check if a new request is allowed under current rate limits.

        Args:
            estimated_tokens: Estimated token count for this request

        Returns:
            RateLimitResult with allowed flag and details
        """
        now = time.time()

        # Clean old entries
        self._clean_window(self._request_window)
        self._clean_window(self._token_window)

        current_rpm = len(self._request_window)
        current_tpm = sum(1 for _ in self._token_window)  # Each entry = 1 token unit

        # Check RPM limit
        if current_rpm >= self.max_rpm:
            oldest = self._request_window[0] if self._request_window else now
            retry_after = max(0.0, 60.0 - (now - oldest))
            self.blocked_requests += 1
            return RateLimitResult(
                allowed=False,
                reason=f"Rate limit exceeded: {current_rpm}/{self.max_rpm} requests/min",
                retry_after_seconds=round(retry_after, 1),
                current_rpm=current_rpm,
                limit_rpm=self.max_rpm,
            )

        # Check TPM limit (rough estimate)
        current_tpm_estimated = self.total_tokens_estimated - self._count_old_tokens(now)
        if current_tpm_estimated + estimated_tokens > self.max_tpm:
            self.blocked_requests += 1
            return RateLimitResult(
                allowed=False,
                reason=f"Token rate limit exceeded: ~{current_tpm_estimated:,}/{self.max_tpm:,} tokens/min",
                retry_after_seconds=30.0,
                current_rpm=current_rpm,
                limit_rpm=self.max_rpm,
            )

        return RateLimitResult(
            allowed=True,
            reason="Request allowed",
            current_rpm=current_rpm,
            limit_rpm=self.max_rpm,
        )

    def record_request(self, tokens_used: int = 1000) -> None:
        """
        Record a completed request for rate tracking.

        Args:
            tokens_used: Actual tokens consumed by the request
        """
        now = time.time()
        self._request_window.append(now)
        # Track token usage as N entries (simplified)
        for _ in range(min(tokens_used // 100, 1000)):  # Each unit = 100 tokens
            self._token_window.append(now)

        self.total_requests += 1
        self.total_tokens_estimated += tokens_used

    def _count_old_tokens(self, now: float) -> int:
        """Count tokens from more than 60 seconds ago (already expired)."""
        cutoff = now - 60
        old_count = sum(1 for t in self._token_window if t < cutoff)
        return old_count * 100  # Each entry = 100 tokens

    def wait_if_needed(self, estimated_tokens: int = 1000) -> bool:
        """
        Block and wait until a request is allowed (max 65 seconds).

        Returns:
            True if request eventually allowed, False if timeout
        """
        for _ in range(130):  # Try every 0.5s for up to 65s
            result = self.check_request(estimated_tokens)
            if result.allowed:
                return True
            time.sleep(0.5)
        return False

    def get_stats(self) -> dict:
        """Return current rate limiting statistics."""
        self._clean_window(self._request_window)
        return {
            "current_rpm": len(self._request_window),
            "max_rpm": self.max_rpm,
            "total_requests_session": self.total_requests,
            "total_tokens_estimated": self.total_tokens_estimated,
            "blocked_requests": self.blocked_requests,
            "utilization_pct": round((len(self._request_window) / self.max_rpm) * 100, 1),
        }
