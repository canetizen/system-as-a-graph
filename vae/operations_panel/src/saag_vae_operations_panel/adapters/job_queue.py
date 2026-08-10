"""
Description: Runs Model Setup Data production outside the request that started it.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from saag_contracts.specs.tasks import JobQueue
from saag_contracts.types.identifiers import system_version

from saag_vae_operations_panel.model.production_job import ProductionJobRequest

#: Name this CSU publishes its production operation under. Recorded in queued
#: work, so it must stay stable across releases even if the code behind it moves.
PRODUCTION_TASK_NAME = "vae01.produce_model_setup_data"


class DeferringJobQueue:
    """Hands a production process to the host's background application.

    Implements the panel's own port over the CSCI-wide deferral service, so the
    panel's use cases keep speaking in their own terms while the queue technology
    stays entirely outside this CSU (SDD §2.5). Whether the operation is deferred
    to a worker or run inline is the host's decision, not the panel's.
    """

    def __init__(self, queue: JobQueue) -> None:
        """Bind the adapter to the deferral service.

        Args:
            queue: The host's deferral service.
        """
        self._queue = queue

    def enqueue(self, request: ProductionJobRequest) -> None:
        """Request execution of one production process.

        The request is flattened into serializable arguments because a deferred
        operation is stored before it runs, and reassembled by ``task_arguments``
        on the other side.

        Args:
            request: What to produce, and which job row to update.
        """
        self._queue.defer(
            PRODUCTION_TASK_NAME,
            job_id=request.job_id,
            project=request.system_version.project.name,
            platform=request.system_version.platform.name,
            system_version=request.system_version.version,
            started_by=request.started_by,
        )


def to_request(
    job_id: str, project: str, platform: str, system_version_number: str, started_by: str
) -> ProductionJobRequest:
    """Rebuild a production request from the arguments a queued task carries.

    Args:
        job_id: Job row to update.
        project: Project to produce for.
        platform: Platform to produce for.
        system_version_number: System version to produce for.
        started_by: Operator who started the process.

    Returns:
        The request the panel's workflow executes.
    """
    return ProductionJobRequest(
        job_id=job_id,
        system_version=system_version(project, platform, system_version_number),
        started_by=started_by,
    )
