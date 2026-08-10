"""
Description: Small infrastructure the panel's adapters share.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """Returns the current UTC time.

    The panel's own, rather than borrowed from another CSU: a clock is four lines
    and sharing one would make this CSU's wheel depend on that CSU's (SDD §2.5).
    """

    def now(self) -> datetime:
        """Return the current time, timezone-aware in UTC."""
        return datetime.now(tz=UTC)
