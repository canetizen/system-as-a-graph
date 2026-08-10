"""
Description: Project/platform/system-version identifiers shared by every SaaG data store.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectRef:
    """Reference to a project defined in the configuration management database.

    Attributes:
        name: Project name; unique within the configuration management database.

    Raises:
        ValueError: If the name is empty or blank.
    """

    name: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Project name must not be empty")

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class PlatformRef:
    """Reference to a platform belonging to a project.

    Attributes:
        project: Owning project.
        name: Platform name; unique within the owning project.

    Raises:
        ValueError: If the name is empty or blank.
    """

    project: ProjectRef
    name: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Platform name must not be empty")

    def __str__(self) -> str:
        return f"{self.project}/{self.name}"


@dataclass(frozen=True)
class SystemVersionRef:
    """Reference to a system version belonging to a platform.

    Attributes:
        platform: Owning platform.
        version: System version number as recorded by the configuration
            management database (kept as text; no ordering is implied here).

    Raises:
        ValueError: If the version is empty or blank.
    """

    platform: PlatformRef
    version: str

    def __post_init__(self) -> None:
        if not self.version or not self.version.strip():
            raise ValueError("System version must not be empty")

    @property
    def project(self) -> ProjectRef:
        """Project this system version ultimately belongs to."""
        return self.platform.project

    def __str__(self) -> str:
        return f"{self.platform}@{self.version}"


def system_version(project: str, platform: str, version: str) -> SystemVersionRef:
    """Build a fully-qualified system version reference from plain strings.

    Convenience for adapters and API layers that receive the three parts
    separately; the domain never constructs the chain by hand.

    Args:
        project: Project name.
        platform: Platform name.
        version: System version number.

    Returns:
        The corresponding SystemVersionRef.

    Raises:
        ValueError: If any part is empty or blank.
    """
    return SystemVersionRef(PlatformRef(ProjectRef(project), platform), version)
