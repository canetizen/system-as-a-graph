"""
Description: The project/platform/system-version an operator is working on (SRS VAE-01.4).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.types.identifiers import SystemVersionRef


@dataclass(frozen=True)
class WorkingScope:
    """One operator's current selection.

    Attributes:
        username: Operator the selection belongs to; selections are per user,
            since two operators may work on different platforms at once.
        system_version: The selected project/platform/system version.
        selected_is_effective: Whether the selected version is the one the
            configuration management database marks as currently effective.
            Kept alongside the selection because VAE-01.4 requires the
            effective version to be shown *distinctly* from the selected one —
            an operator may deliberately work on an older version.
        selected_model_setup_data_run_id: Which produced Model Setup Data file
            the operator picked (VAE-01.5); empty when none is picked yet.
    """

    username: str
    system_version: SystemVersionRef
    selected_is_effective: bool = False
    selected_model_setup_data_run_id: str = ""
