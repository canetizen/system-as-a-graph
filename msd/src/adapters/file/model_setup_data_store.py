"""
Description: Writes and reads Model Setup Data documents on disk (INT-IF-01 carrier).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from msd.src.model.model_setup_data import document_file_name

#: Environment variable naming the directory documents are written to. Mounted
#: as a volume so produced files outlive the container and CSM-01 can read them.
OUTPUT_DIR_ENV_VAR = "MSD_OUTPUT_DIR"

_DEFAULT_OUTPUT_DIR = Path("/var/lib/saag/msd")


def output_dir(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Resolve the directory documents are written to.

    Args:
        explicit: Explicit directory; defaults to ``$MSD_OUTPUT_DIR`` and then
            to the packaged default.

    Returns:
        The resolved directory; not created here.
    """
    return Path(explicit or os.getenv(OUTPUT_DIR_ENV_VAR) or _DEFAULT_OUTPUT_DIR)


class FileModelSetupDataStore:
    """Stores Model Setup Data documents as JSON files.

    The file is the interface CSM-01 consumes (INT-IF-01); the metadata row
    kept elsewhere only points at it.
    """

    def __init__(self, directory: Path) -> None:
        """Initialize the store.

        Args:
            directory: Directory documents are written to; created on demand.
        """
        self._directory = directory

    def write(self, platform: str, document: dict) -> Path:
        """Write a document.

        A same-day rerun for the same platform overwrites its predecessor,
        because the file name is dated per UXD §4 and the newest production run
        for a platform is the one an operator means.

        Args:
            platform: Platform the document was produced for.
            document: The serialized document.

        Returns:
            Path of the written file.

        Raises:
            OSError: If the directory cannot be created or the file written.
            KeyError: If the document carries no production timestamp.
        """
        produced_at = datetime.fromisoformat(document["provenance"]["produced_at"])
        self._directory.mkdir(parents=True, exist_ok=True)

        path = self._directory / document_file_name(platform, produced_at)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, ensure_ascii=False)

        return path

    def read(self, path: Path) -> dict | None:
        """Read a document back.

        Args:
            path: File to read.

        Returns:
            The document, or None when the file is absent.

        Raises:
            json.JSONDecodeError: If the file is not valid JSON.
        """
        if not path.is_file():
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
