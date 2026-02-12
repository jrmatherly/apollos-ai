"""Brute force protection for local login.

Provides progressive delays and temporary account lockout after repeated
failed login attempts.  State is held in-memory (resets on server restart,
which is acceptable for this use case).

Usage::

    from python.helpers.login_protection import login_protection

    if login_protection.check_locked(username):
        # return 429 with Retry-After header
        ...

    # on failure
    delay = login_protection.record_failure(username)
    await asyncio.sleep(delay)

    # on success
    login_protection.record_success(username)
"""

import time


class LoginProtection:
    """In-memory progressive delay + account lockout for local login."""

    MAX_ATTEMPTS: int = 5
    LOCKOUT_DURATION: int = 300  # seconds (5 minutes)
    PROGRESSIVE_DELAYS: list[float] = [0, 1, 2, 4, 8]

    def __init__(self) -> None:
        self._attempts: dict[str, list[float]] = {}

    def check_locked(self, username: str) -> bool:
        """Return True if the account is currently locked out."""
        attempts = self._attempts.get(username, [])
        if len(attempts) < self.MAX_ATTEMPTS:
            return False
        last_attempt = attempts[-1]
        if time.monotonic() - last_attempt > self.LOCKOUT_DURATION:
            # Lockout expired — clear history
            self._attempts.pop(username, None)
            return False
        return True

    def record_failure(self, username: str) -> float:
        """Record a failed login attempt.

        Returns the number of seconds the caller should delay before
        responding (progressive backoff).
        """
        now = time.monotonic()
        attempts = self._attempts.setdefault(username, [])

        # Prune attempts older than the lockout window
        cutoff = now - self.LOCKOUT_DURATION
        self._attempts[username] = [t for t in attempts if t > cutoff]
        attempts = self._attempts[username]

        attempts.append(now)
        idx = min(len(attempts) - 1, len(self.PROGRESSIVE_DELAYS) - 1)
        return self.PROGRESSIVE_DELAYS[idx]

    def record_success(self, username: str) -> None:
        """Clear attempt history on successful login."""
        self._attempts.pop(username, None)

    def lockout_remaining(self, username: str) -> float:
        """Return seconds remaining in lockout, or 0 if not locked."""
        attempts = self._attempts.get(username, [])
        if len(attempts) < self.MAX_ATTEMPTS:
            return 0
        elapsed = time.monotonic() - attempts[-1]
        remaining = self.LOCKOUT_DURATION - elapsed
        return max(0, remaining)


# Module-level singleton
login_protection = LoginProtection()
