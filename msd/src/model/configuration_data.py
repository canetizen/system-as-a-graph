"""
Description: Project, platform, and system version data acquired from the CM database (SRS MSD.9-13).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.types.identifiers import PlatformRef, ProjectRef, SystemVersionRef


@dataclass(frozen=True)
class Project:
    """A project as reported by a configuration management database.

    Attributes:
        ref: Identity of the project.
        source_name: Configured source that reported it.
    """

    ref: ProjectRef
    source_name: str


@dataclass(frozen=True)
class Platform:
    """A platform belonging to a project.

    Attributes:
        ref: Identity of the platform.
        source_name: Configured source that reported it.
    """

    ref: PlatformRef
    source_name: str


@dataclass(frozen=True)
class SystemVersion:
    """A system version belonging to a platform.

    Attributes:
        ref: Identity of the system version.
        is_effective: Whether this is the currently effective version
            (SRS MSD.13). At most one version per platform carries the mark.
        source_name: Configured source that reported it.
    """

    ref: SystemVersionRef
    is_effective: bool
    source_name: str


@dataclass
class ConfigurationDataSet:
    """Everything one acquisition run retrieved from the CM databases.

    Attributes:
        projects: Projects retrieved (SRS MSD.10).
        platforms: Platforms retrieved for the selected project (SRS MSD.11).
        versions: System versions retrieved for the selected platform
            (SRS MSD.12).
    """

    projects: list[Project] = field(default_factory=list)
    platforms: list[Platform] = field(default_factory=list)
    versions: list[SystemVersion] = field(default_factory=list)

    @property
    def effective_version(self) -> SystemVersion | None:
        """The version marked as currently effective, if any (SRS MSD.13).

        Returns:
            The effective version, or None when no source marked one.
        """
        for version in self.versions:
            if version.is_effective:
                return version
        return None
