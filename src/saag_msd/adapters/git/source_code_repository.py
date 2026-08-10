"""
Description: Source code repository adapter cloning software unit trees with git (EXT-IF-02).
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

from __future__ import annotations

import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from saag_contracts.errors.acquisition import AcquisitionFailure, AcquisitionStatus

from saag_msd.model.data_source import DataSourceConfiguration
from saag_msd.model.source_files import FileClassifier, SourceFileRecord
from saag_msd.model.version_inventory import SoftwareUnitVersion

#: Default location of a unit's repository under the configured address.
_DEFAULT_PATH_TEMPLATE = "{unit}.git"

#: Seconds a git invocation may take before it is abandoned.
_DEFAULT_TIMEOUT = 300

#: Substrings git prints when the transport refused the credential rather than
#: merely failing. Git has no exit code for this, so the message is the only
#: signal available.
_AUTHORIZATION_MARKERS = (
    "authentication failed",
    "invalid username or password",
    "access denied",
    "403 forbidden",
    "permission denied",
)


class GitSourceCodeRepository:
    """Clones software unit trees over git.

    One adapter serves every git host — Gitea, Bitbucket, GitLab — because they
    differ in deployment, not in protocol. Moving to a different server is a
    change of connection address and credential, nothing more.

    Only the requested tag is fetched (``--depth 1 --branch``), and ``.git`` is
    removed afterwards: MSD wants the files at a version, not a working clone,
    and leaving history behind would quietly multiply the workspace.
    """

    def __init__(
        self,
        configuration: DataSourceConfiguration,
        workspace: Path,
        classifier: FileClassifier,
        credential: str | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            configuration: The repository server this instance serves.
            workspace: Directory transferred files are cloned into.
            classifier: Assigns a kind to each transferred file.
            credential: Resolved token or password, injected into the URL for
                the duration of a call. None clones anonymously.
        """
        self._configuration = configuration
        self._workspace = workspace
        self._classifier = classifier
        self._credential = credential
        self._parameters: dict[str, Any] = dict(configuration.parameters or {})

    @property
    def source_name(self) -> str:
        """Name of the configured repository this instance serves."""
        return self._configuration.name

    def holds(self, unit: SoftwareUnitVersion) -> bool:
        """Whether this server carries the unit at the requested tag.

        Answers with ``git ls-remote``, and reports False rather than raising
        when the answer is no — the router needs a miss to be quiet.
        """
        try:
            result = self._git("ls-remote", "--tags", self._url(unit), unit.version)
        except AcquisitionFailure:
            return False
        return bool(result.strip())

    def check_access(self) -> None:
        """Verify the server answers at all.

        Asks over HTTP rather than with ``git ls-remote``, because the
        configured address is the server or the account under it — not one
        repository — and ls-remote can only speak to a repository. Git over
        HTTP is HTTP, so this reaches the same endpoint the clone will.

        Raises:
            AcquisitionFailure: AUTHORIZATION_ERROR when the server refuses the
                credential, ACCESS_ERROR when it cannot be reached at all.
        """
        address = self._configuration.connection_address.rstrip("/")
        parsed = urllib.parse.urlsplit(address)
        if parsed.scheme not in {"http", "https"}:
            # A local or ssh remote has no endpoint to poll; ask git instead.
            self._git("ls-remote", "--exit-code", "--heads", self._base_url(), timeout=30)
            return

        request = urllib.request.Request(self._authenticated(address), method="GET")
        try:
            with urllib.request.urlopen(request, timeout=30):
                return
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403}:
                raise AcquisitionFailure(
                    AcquisitionStatus.AUTHORIZATION_ERROR,
                    f"'{self.source_name}' refused the credential",
                    detail=f"HTTP {exc.code}",
                ) from exc
            # Any other status means the server answered, which is what
            # accessibility asks about; what lives at that path is the clone's
            # problem, not the probe's.
            return
        except (urllib.error.URLError, TimeoutError) as exc:
            raise AcquisitionFailure(
                AcquisitionStatus.ACCESS_ERROR,
                f"'{self.source_name}' is not reachable",
                detail=str(getattr(exc, "reason", exc)),
            ) from exc

    def transfer(self, unit: SoftwareUnitVersion) -> list[SourceFileRecord]:
        """Clone a unit at its tag and record the transferred files (SRS MSD.17-18).

        Args:
            unit: Software unit version to transfer.

        Returns:
            One record per transferred file.

        Raises:
            AcquisitionFailure: On access, authorization, or integrity errors.
        """
        destination = self.local_tree(unit)
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        self._git(
            "clone",
            "--depth",
            "1",
            "--branch",
            unit.version,
            self._url(unit),
            str(destination),
        )

        git_directory = destination / ".git"
        if git_directory.is_dir():
            shutil.rmtree(git_directory)

        return [
            self._record(unit, path, destination)
            for path in sorted(destination.rglob("*"))
            if path.is_file()
        ]

    def local_tree(self, unit: SoftwareUnitVersion) -> Path:
        """Return the workspace root this unit is cloned into."""
        return self._workspace / self.source_name / unit.versioned_name

    def _record(
        self, unit: SoftwareUnitVersion, path: Path, root: Path
    ) -> SourceFileRecord:
        relative = path.relative_to(root).as_posix()
        return SourceFileRecord(
            file_name=path.name,
            file_path=relative,
            package=unit.unit_name,
            version=unit.version,
            updated_at=datetime.fromtimestamp(path.stat().st_mtime, tz=UTC),
            source_name=self.source_name,
            kind=self._classifier.classify(relative),
            local_path=str(path),
        )

    def _base_url(self) -> str:
        return self._authenticated(self._configuration.connection_address.rstrip("/"))

    def _url(self, unit: SoftwareUnitVersion) -> str:
        template = str(self._parameters.get("path_template", _DEFAULT_PATH_TEMPLATE))
        path = template.format(unit=unit.unit_name, version=unit.version)
        base = self._configuration.connection_address.rstrip("/")
        return self._authenticated(f"{base}/{path.lstrip('/')}")

    def _authenticated(self, url: str) -> str:
        """Put the credential in the URL, escaped, for transports that take one.

        The token never reaches the stored configuration — it is resolved per
        call — and a scheme that carries no credentials (a local path, ``file:``)
        is left alone.
        """
        credential = self._configuration.credential
        if not self._credential or credential is None:
            return url

        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in {"http", "https"}:
            return url

        user = urllib.parse.quote(credential.username or "git", safe="")
        secret = urllib.parse.quote(self._credential, safe="")
        return urllib.parse.urlunsplit(
            parsed._replace(netloc=f"{user}:{secret}@{parsed.netloc}")
        )

    def _git(self, *arguments: str, timeout: int | None = None) -> str:
        try:
            completed = subprocess.run(
                ["git", *arguments],
                capture_output=True,
                text=True,
                timeout=timeout or int(self._parameters.get("timeout_seconds", _DEFAULT_TIMEOUT)),
                check=False,
            )
        except FileNotFoundError as exc:
            raise AcquisitionFailure(
                AcquisitionStatus.ACCESS_ERROR,
                "The git client is not available in this environment",
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise AcquisitionFailure(
                AcquisitionStatus.ACCESS_ERROR,
                f"'{self.source_name}' did not answer before the timeout",
            ) from exc

        if completed.returncode != 0:
            raise AcquisitionFailure(
                self._classify(completed.stderr),
                f"'{self.source_name}' refused the request",
                detail=_redact(completed.stderr.strip()),
            )

        return completed.stdout

    def _classify(self, stderr: str) -> AcquisitionStatus:
        lowered = stderr.lower()
        if any(marker in lowered for marker in _AUTHORIZATION_MARKERS):
            return AcquisitionStatus.AUTHORIZATION_ERROR
        return AcquisitionStatus.ACCESS_ERROR


def _redact(message: str) -> str:
    """Strip any credential git echoed back inside a URL."""
    return " ".join(
        part.split("@", 1)[-1] if "://" in part and "@" in part else part
        for part in message.split(" ")
    )
