"""
Description: Accessibility status of the configured data sources (SRS VAE-01.7).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Accessibility(str, Enum):
    """Whether a configured data source answered its last probe."""

    REACHABLE = "reachable"
    UNREACHABLE = "unreachable"


@dataclass(frozen=True)
class SourceStatus:
    """One configured source's accessibility at one moment.

    Attributes:
        source_type: Type of the configured source.
        source_name: Name of the configured source.
        accessibility: Whether it answered.
        checked_at: When the probe ran.
        detail: Why it was unreachable; empty when reachable.
    """

    source_type: str
    source_name: str
    accessibility: Accessibility
    checked_at: datetime
    detail: str = ""

    @property
    def is_reachable(self) -> bool:
        """Whether the source answered its last probe."""
        return self.accessibility is Accessibility.REACHABLE


@dataclass
class SourceStatusSnapshot:
    """The accessibility of every configured source at one moment.

    VAE-01.7 asks for the status to be displayed *continuously and traceably*,
    so each snapshot is recorded rather than only shown: an operator can see
    not just that a source is down now, but that it was down when a production
    run failed.

    Attributes:
        checked_at: When the snapshot was taken.
        statuses: One entry per configured source.
    """

    checked_at: datetime
    statuses: list[SourceStatus] = field(default_factory=list)

    @property
    def all_reachable(self) -> bool:
        """Whether every configured source answered."""
        return all(status.is_reachable for status in self.statuses)

    @property
    def unreachable(self) -> list[SourceStatus]:
        """The sources that did not answer."""
        return [status for status in self.statuses if not status.is_reachable]
