"""
Description: Reserved registry names for the internal interfaces whose CSUs are not yet designed.
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

#: INT-IF-02, Synthetic Data Handoff (SCG -> ADP); SRS SCG.7 / ADP.3.
SYNTHETIC_DATA_HANDOFF = "saag.int-if-02.synthetic-data-handoff"

#: INT-IF-03, Field Records Handoff (FRD -> ADP); SRS FRD.4 / ADP.2.
FIELD_RECORDS_HANDOFF = "saag.int-if-03.field-records-handoff"

#: INT-IF-04, Analytical Evaluation Data Handoff (ADP -> CSM-02); SRS ADP.4 /
#: CSM-02.2.
ANALYTICAL_DATA_HANDOFF = "saag.int-if-04.analytical-data-handoff"

#: INT-IF-05, Core System Model Access, read-only (CSM -> VAE); SRS
#: CSM-01.27-28 / VAE-02.3, VAE-03.10.
CORE_SYSTEM_MODEL_ACCESS = "saag.int-if-05.core-system-model-access"

# Why names without protocols
# --------------------------
# What SDD §2.3 left open for these four interfaces, and what CDR-24 to CDR-28
# ask, is the communication method and protocol. That is answered here and in
# SDD §2.3.1: the in-process component registry, under the names above, with the
# provider advertising a `saag.contract.version` service property.
#
# The call interfaces themselves are a different question, and answering it now
# would mean inventing payloads the design has deliberately deferred: the
# Analytical Evaluation Data format is still open (CDR-12), as is what the
# synthetic data simulates (CDR-11), and the CSUs on both ends of INT-IF-02 to
# INT-IF-05 are scheduled for Increments 4 to 6. Each name therefore gains its
# `@Specification`-decorated protocol in the increment that builds its provider,
# beside the one INT-IF-01 already has in `specs.model_setup_data`.
