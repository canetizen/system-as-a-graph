"""
Description: Published test support for exercising the operations panel.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from saag_vae_operations_panel.model.production_job import ProductionJobRequest
from saag_vae_operations_panel.ports.repositories import JobQueuePort


class InlineProductionQueue(JobQueuePort):
    """Runs a production process before ``enqueue`` returns.

    What the panel's own tests use, and what a consumer exercising the panel
    without the host's background application needs. The in-progress state still
    exists in the job record; it is simply never observed from outside, because
    the work is already finished by the time the caller can look.
    """

    def __init__(self, runner) -> None:
        """Bind the queue to a resolver for the workflow that executes the job.

        Args:
            runner: Returns the workflow. Resolved late because the workflow and
                its queue are each other's collaborators and neither can be built
                first.
        """
        self._runner = runner

    def enqueue(self, request: ProductionJobRequest) -> None:
        """Run the production process now."""
        self._runner().run(request)
