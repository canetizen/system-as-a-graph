"""
Description: Small outbound port for time, so sessions and job timing stay testable.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class ClockPort(Protocol):
    """Supplies the current time.

    Token expiry, job start/finish times, and accessibility snapshots all need
    a clock a test can pin.
    """

    def now(self) -> datetime:
        """Return the current time."""
        ...
