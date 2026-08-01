"""
Description: Network topology adapter reading the deployment's Ansible tree (EXT-IF-04).
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from msd.src.model.data_source import DataSourceConfiguration
from msd.src.model.network_topology import (
    Machine,
    NetworkComponent,
    NetworkTopology,
    TopologyAcquisitionMethod,
)
from shared.errors.acquisition import AcquisitionFailure, AcquisitionStatus
from shared.types.identifiers import PlatformRef

#: Where things sit in an ordinary Ansible tree. Every one of these is
#: overridable per source, because the deployment's real layout is its own.
_DEFAULTS: dict[str, Any] = {
    "inventory": "inventory.yml",
    "host_vars_dir": "host_vars",
    "group_vars_dir": "group_vars",
    #: Variable holding a host's network components, as a list of mappings.
    "network_components_key": "network_components",
    #: Keys inside each of those mappings.
    "component_name_key": "name",
    "component_type_key": "type",
    #: Host variables copied onto the machine node. Empty means "all of them".
    "machine_attribute_keys": [],
}


class AnsibleNetworkTopologySource:
    """Reads machines and network components out of an Ansible tree.

    The tree is a directory on a mounted filesystem, which is what the real
    source is too — so unlike the other adapters this one has no stand-in
    version. Only the data differs between a demo tree and the deployment's own.

    Two kinds of node come out of it. Hosts in the inventory become operator
    console / processor units, carrying their variables as attributes; they
    merge by name with the units the deployment descriptor already names.
    Network components declared in host or group variables become network
    component nodes.

    Which files and which variables to read are configuration: the deployment's
    layout is not fixed here, so when it settles, only the source's parameters
    change.
    """

    def __init__(self, configuration: DataSourceConfiguration) -> None:
        """Initialize the adapter.

        Args:
            configuration: The topology source this instance serves; its
                ``connection_address`` is the tree's root directory.
        """
        self._configuration = configuration
        self._settings = {**_DEFAULTS, **(configuration.parameters or {})}
        self._root = Path(configuration.connection_address)

    @property
    def source_name(self) -> str:
        """Name of the configured source this instance serves."""
        return self._configuration.name

    def fetch(self, platform: PlatformRef) -> NetworkTopology:
        """Read the tree and report what it describes.

        The platform selects the inventory group to read: an Ansible tree
        usually describes every platform at once, and a group per platform is
        how they are told apart. A tree with no such group yields an empty
        topology rather than everything it happens to contain.

        Args:
            platform: Platform to read topology for.

        Returns:
            The machines and network components found.

        Raises:
            AcquisitionFailure: ACCESS_ERROR when the tree or its inventory is
                not there, FORMAT_INCOMPATIBLE when a file is not valid YAML.
        """
        if not self._root.is_dir():
            raise AcquisitionFailure(
                AcquisitionStatus.ACCESS_ERROR,
                f"Ansible tree for '{self.source_name}' is not reachable",
                detail=str(self._root),
            )

        inventory = self._read(self._root / str(self._settings["inventory"]))
        hosts = self._hosts_of(inventory, platform.name)

        machines: list[Machine] = []
        components: dict[str, NetworkComponent] = {}

        group_variables = self._group_variables(platform.name)
        self._collect_components(group_variables, components)

        for host, inline_variables in hosts.items():
            variables = {**group_variables, **inline_variables, **self._host_variables(host)}
            machines.append(Machine(name=host, attributes=self._machine_attributes(variables)))
            self._collect_components(variables, components)

        return NetworkTopology(
            method=TopologyAcquisitionMethod.AUTOMATIC,
            source_name=self.source_name,
            components=list(components.values()),
            machines=machines,
        )

    def _hosts_of(self, inventory: Any, platform: str) -> dict[str, dict[str, Any]]:
        """Return the hosts of the group named after the platform.

        Handles both inventory shapes Ansible accepts — a top-level group and a
        group nested under ``all.children`` — because either is ordinary.
        """
        if not isinstance(inventory, dict):
            return {}

        candidates = [inventory.get(platform)]
        nested = inventory.get("all", {})
        if isinstance(nested, dict):
            children = nested.get("children", {})
            if isinstance(children, dict):
                candidates.append(children.get(platform))

        for group in candidates:
            if isinstance(group, dict) and isinstance(group.get("hosts"), dict):
                return {
                    name: variables if isinstance(variables, dict) else {}
                    for name, variables in group["hosts"].items()
                }

        return {}

    def _group_variables(self, platform: str) -> dict[str, Any]:
        directory = self._root / str(self._settings["group_vars_dir"])
        return self._variables_for(directory, platform)

    def _host_variables(self, host: str) -> dict[str, Any]:
        directory = self._root / str(self._settings["host_vars_dir"])
        return self._variables_for(directory, host)

    def _variables_for(self, directory: Path, name: str) -> dict[str, Any]:
        for candidate in (f"{name}.yml", f"{name}.yaml", name):
            path = directory / candidate
            if path.is_file():
                content = self._read(path)
                return content if isinstance(content, dict) else {}
            if path.is_dir():
                merged: dict[str, Any] = {}
                for nested in sorted(path.glob("*.y*ml")):
                    content = self._read(nested)
                    if isinstance(content, dict):
                        merged.update(content)
                return merged
        return {}

    def _collect_components(
        self, variables: dict[str, Any], into: dict[str, NetworkComponent]
    ) -> None:
        declared = variables.get(str(self._settings["network_components_key"]), [])
        if not isinstance(declared, list):
            return

        name_key = str(self._settings["component_name_key"])
        type_key = str(self._settings["component_type_key"])

        for entry in declared:
            if not isinstance(entry, dict):
                continue
            name = entry.get(name_key)
            if not name:
                continue
            into.setdefault(
                str(name),
                NetworkComponent(
                    name=str(name),
                    component_type=str(entry.get(type_key, "")),
                    attributes={
                        key: str(value)
                        for key, value in entry.items()
                        if key not in {name_key, type_key}
                    },
                ),
            )

    def _machine_attributes(self, variables: dict[str, Any]) -> dict[str, str]:
        wanted = self._settings["machine_attribute_keys"]
        components_key = str(self._settings["network_components_key"])

        if wanted:
            selected = {key: variables[key] for key in wanted if key in variables}
        else:
            selected = {
                key: value
                for key, value in variables.items()
                if key != components_key and not isinstance(value, (list, dict))
            }

        return {key: str(value) for key, value in selected.items()}

    def _read(self, path: Path) -> Any:
        try:
            with path.open("r", encoding="utf-8") as handle:
                return yaml.safe_load(handle)
        except FileNotFoundError as exc:
            raise AcquisitionFailure(
                AcquisitionStatus.ACCESS_ERROR,
                f"'{self.source_name}' has no {path.name} in its Ansible tree",
                detail=str(path),
            ) from exc
        except yaml.YAMLError as exc:
            raise AcquisitionFailure(
                AcquisitionStatus.FORMAT_INCOMPATIBLE,
                f"'{path.name}' in the Ansible tree is not valid YAML",
                detail=str(exc),
            ) from exc
