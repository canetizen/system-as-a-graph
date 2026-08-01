"""
Description: Package repository adapter looking artifacts up over REST (EXT-IF-03).
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from msd.src.model.data_source import DataSourceConfiguration
from msd.src.model.version_inventory import SoftwareUnitVersion
from shared.errors.acquisition import AcquisitionFailure, AcquisitionStatus

#: Where to look an artifact up, unless the source configures otherwise.
_DEFAULT_PATH_TEMPLATE = "/api/artifacts?name={unit}&version={version}"

#: Where the artifacts sit in the response body, and what their fields are
#: called. Overridden per source, because no two registries agree.
_DEFAULT_RESULTS_KEY = "artifacts"
_DEFAULT_FIELDS = {"path": "path", "checksum": "checksum"}

_DEFAULT_TIMEOUT = 30


class RestPackageRepository:
    """Confirms an artifact exists for a software unit version, over HTTP.

    Artifactory, Nexus, and a git host's package registry all expose "does this
    artifact exist, and where is it" as a JSON lookup; they only disagree on the
    URL and the field names. Both are configuration here, so the product on the
    other end can change without this adapter changing.

    Configured under the source's ``parameters``: ``path_template``,
    ``results_key``, and ``fields``.
    """

    def __init__(
        self, configuration: DataSourceConfiguration, credential: str | None = None
    ) -> None:
        """Initialize the adapter.

        Args:
            configuration: The registry this instance serves.
            credential: Resolved token, sent as a bearer credential. None calls
                anonymously.
        """
        self._configuration = configuration
        self._credential = credential
        self._parameters: dict[str, Any] = dict(configuration.parameters or {})

    @property
    def source_name(self) -> str:
        """Name of the configured registry this instance serves."""
        return self._configuration.name

    def find_artifact(self, unit: SoftwareUnitVersion) -> dict[str, str] | None:
        """Look up a unit version's package artifact (SRS MSD.4).

        Args:
            unit: Software unit version to look up.

        Returns:
            Artifact metadata, or None when the registry answers that it has no
            such artifact — an absence, not a failure.

        Raises:
            AcquisitionFailure: If the registry is unreachable, refuses the
                credential, or answers with something that is not JSON.
        """
        payload = self._get(self._url(unit))
        results = self._results(payload)
        if not results:
            return None

        fields = {**_DEFAULT_FIELDS, **self._parameters.get("fields", {})}
        artifact = results[0]
        found = {
            "name": unit.unit_name,
            "version": unit.version,
        }
        for target, source in fields.items():
            value = artifact.get(source)
            if value is not None:
                found[target] = str(value)
        return found

    def _url(self, unit: SoftwareUnitVersion) -> str:
        template = str(self._parameters.get("path_template", _DEFAULT_PATH_TEMPLATE))
        path = template.format(
            unit=urllib.parse.quote(unit.unit_name, safe=""),
            version=urllib.parse.quote(unit.version, safe=""),
        )
        return f"{self._configuration.connection_address.rstrip('/')}/{path.lstrip('/')}"

    def _results(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        key = str(self._parameters.get("results_key", _DEFAULT_RESULTS_KEY))
        if isinstance(payload, dict):
            found = payload.get(key, [])
            if isinstance(found, list):
                return [item for item in found if isinstance(item, dict)]

        raise AcquisitionFailure(
            AcquisitionStatus.FORMAT_INCOMPATIBLE,
            f"'{self.source_name}' answered in an unexpected shape",
            detail=f"expected a list, or an object carrying '{key}'",
        )

    def _get(self, url: str) -> Any:
        request = urllib.request.Request(url, method="GET")
        request.add_header("accept", "application/json")
        if self._credential:
            request.add_header("Authorization", f"Bearer {self._credential}")

        timeout = int(self._parameters.get("timeout_seconds", _DEFAULT_TIMEOUT))
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403}:
                raise AcquisitionFailure(
                    AcquisitionStatus.AUTHORIZATION_ERROR,
                    f"'{self.source_name}' refused the credential",
                    detail=f"HTTP {exc.code}",
                ) from exc
            if exc.code == 404:
                return {}
            raise AcquisitionFailure(
                AcquisitionStatus.ACCESS_ERROR,
                f"'{self.source_name}' answered with an error",
                detail=f"HTTP {exc.code}",
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise AcquisitionFailure(
                AcquisitionStatus.ACCESS_ERROR,
                f"'{self.source_name}' is not reachable",
                detail=str(getattr(exc, "reason", exc)),
            ) from exc

        try:
            return json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            raise AcquisitionFailure(
                AcquisitionStatus.FORMAT_INCOMPATIBLE,
                f"'{self.source_name}' did not answer with JSON",
                detail=str(exc),
            ) from exc
