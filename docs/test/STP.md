# Software Test Plan (STP)
## System as a Graph (SaaG) Digital System Model
### Prepared in accordance with MIL-STD-498 (Data Item Description DI-IPSC-81438)

---

## 1. Scope

### 1.1 Identification

This document is the Software Test Plan (STP) for the **System as a Graph (SaaG) Digital System Model** CSCI, prepared in the format defined by MIL-STD-498, Data Item Description DI-IPSC-81438. It plans the formal qualification testing that demonstrates the CSCI satisfies `../requirements/SRS.md`.

### 1.2 System Overview

SaaG is a static digital system model built using an architectural digital twin approach, decomposed in `../design/SDD.md` into 6 CSCs (MSD, SCG, FRD, ADP, CSM, VAE) and 31 CSUs. Its external and internal interfaces are specified in `../design/IDD.md`; its persistent data stores in `../design/DBDD.md`.

### 1.3 Document Overview

Section 3 describes the test environment. Section 4 identifies the 31 tests planned, one per CSU defined in `../design/SDD.md`, all executed as part of a single CSCI-level formal qualification test effort (no separate CSU/CSC-level formal test levels are planned — see §3's note). Section 5 addresses test progression/scheduling. Section 6 traces every SRS requirement exercised by these tests to its Test ID.

---

## 2. Referenced Documents

- MIL-STD-498, *Software Development and Documentation*, Data Item Description DI-IPSC-81438 (Software Test Plan).
- `../requirements/SRS.md` — Software Requirements Specification for the SaaG CSCI.
- `../design/SDD.md` — Software Design Description for the SaaG CSCI.
- `../design/IDD.md` — Interface Design Description for the SaaG CSCI.
- `../design/DBDD.md` — Database Design Description for the SaaG CSCI.

---

## 3. Software Test Environment

**Test level note**: all 31 tests identified in Section 4 are formal qualification tests conducted at the CSCI level — i.e., against the assembled SaaG CSCI, not against isolated CSUs in a separate unit-test harness. They are organized one-per-CSU purely for traceability to `../design/SDD.md`'s decomposition, not because CSU is a distinct formal test level.

### 3.1 Software Items

The test environment requires a stand-in or harness for each external interface identified in `../design/IDD.md` §3, plus representative test data for each capability area:

- A test/mock Configuration Management Database (EXT-IF-01)
- A test/mock Source Code Repository (EXT-IF-02)
- A test/mock Software Units Package Repository (EXT-IF-03)
- A test network topology data source, and a manual-entry test harness for the alternative acquisition method (EXT-IF-04)
- A representative set of valid and invalid System Field Records for upload testing (EXT-IF-05)
- A test LDAP directory service instance with known valid/invalid credentials (EXT-IF-06)
- A test automation client / CLI harness able to submit analysis requests and poll status (EXT-IF-07)
- Representative valid and invalid Model Setup Data files (for MSD/CSM testing)
- Representative scenario definitions and their expected synthetic data outputs (for SCG testing)
- The SaaG CSCI build under test

### 3.2 Hardware and Firmware Items

To be determined during the critical design phase, consistent with `../requirements/SRS.md` 3.2.3.6 (storage hardware capacity) and the concurrency/user-load parameters left open in `../requirements/SRS.md` 3.2.5.19.

### 3.3 Test Support Personnel and Organizations

Test execution and results recording is performed by a test team independent of the development of the CSU under test, per each test's objective in Section 4. Specific staffing levels and organizational assignments are outside the scope of this document.

---

## 4. Test Identification

Each test's objective and SRS basis are carried directly from the corresponding CSU's purpose in `../design/SDD.md` §5. Test type is "requirements-based functional test" for all 31 unless noted otherwise; pass/fail criteria is conformance to the SRS paragraphs traced.

### 4.1 MSD — Model Setup Data Generation

| Test ID | Test Name | Objective | SRS Basis |
|---|---|---|---|
| TC-MSD-01 | Data Source Connector & Configuration Manager | Verify controlled, traceable access and configuration management for the 4 external data sources, including both network-topology acquisition methods. | 3.2.1.2–4 |
| TC-MSD-02 | Configuration Data Acquisition | Verify retrieval of project/platform/version data and effective-version marking from the configuration management database, and error-status marking on deficiency/access/format failure. | 3.2.1.5–9, 12 |
| TC-MSD-03 | Software Unit Version Inventory Manager | Verify recording and candidate-version update of the Software Unit Version Inventory. | 3.2.1.10–11 |
| TC-MSD-04 | Source Repository Ingestion | Verify file transfer, per-file recording, missing-data reporting, and access/integrity error reporting from the source code repository. | 3.2.1.13–16 |
| TC-MSD-05 | Data Validation & Model Setup Data Assembler | Verify mandatory-field validation, failure recording, and assembly of the Model Setup Data file from data that passes verification. | 3.2.1.17–19 |

### 4.2 SCG — Scenario Generator

| Test ID | Test Name | Objective | SRS Basis |
|---|---|---|---|
| TC-SCG-01 | Scenario Input Manager | Verify capture and traceable recording of scenario scope/type/interval/density/data-type inputs. | 3.2.2.3, 6 |
| TC-SCG-02 | Synthetic Data Generator | Verify synthetic data production conforms to the topic/message schema, field naming, and value-range constraints of the real software units. | 3.2.2.2, 4 |
| TC-SCG-03 | Scenario Output Recorder | Verify recorded synthetic data output includes scenario name/production time/project-platform-version, and is prepared for transfer to ADP. | 3.2.2.5, 7 |

### 4.3 FRD — Field Records Database

| Test ID | Test Name | Objective | SRS Basis |
|---|---|---|---|
| TC-FRD-01 | Record Upload Manager | Verify controlled, traceable upload of telemetry/system records with project/platform/version association, and detection/reporting of upload-time errors. | 3.2.3.2, 5 |
| TC-FRD-02 | Record Catalog Manager | Verify recorded metadata (source, upload time, project/platform/version) and list/search/select behavior across those criteria. | 3.2.3.3–4 |

### 4.4 ADP — Analytical Data Preparation

| Test ID | Test Name | Objective | SRS Basis |
|---|---|---|---|
| TC-ADP-01 | Field Record Ingestion | Verify retrieval of System Field Records from FRD and detection/reporting of format/unreadable-data errors. | 3.2.4.2, 5 |
| TC-ADP-02 | Scenario Data Ingestion | Verify retrieval of synthetic data from SCG and detection/reporting of format/unreadable/missing-field errors. | 3.2.4.3, 6 |
| TC-ADP-03 | Analytical Data Assembler | Verify processing/association of ingested data into Analytical Evaluation Data transmitted to CSM. | 3.2.4.4 |

### 4.5 CSM — Node-Relationship Based Core System Model

| Test ID | Test Name | Objective | SRS Basis |
|---|---|---|---|
| TC-CSM-01 | Model Construction Engine | Verify Model Setup Data ingestion, validation, conversion to a node-relationship Core System Model, error reporting, and model metadata recording. | 3.2.5.2–5, 9, 15 |
| TC-CSM-02 | Node-Relationship Schema Manager | Verify all required node/relationship types are representable, and CPU/OS/runtime attributes are queryable. | 3.2.5.6–8 |
| TC-CSM-03 | Analytical Data Binder | Verify Analytical Evaluation Data association/matching/provenance-preservation/separability, and unmatched-record reporting. | 3.2.5.10–14 |
| TC-CSM-04 | Model Access Provider | Verify VAE can access the Core System Model's nodes, relationships, and bound Analytical Evaluation Data. | 3.2.5.16–17 |
| TC-CSM-05 | Concurrency & Session Manager | Verify concurrent multi-session read/write and concurrent pipeline/analysis operations do not compromise integrity or result consistency. | 3.2.5.18–19 |
| TC-CSM-06 | Candidate Evaluation Model Builder | Verify creation of an isolated, process-specific Core System Model for a candidate software unit version. | 3.2.5.20 |

### 4.6 VAE — Design Verification, Analysis and Evaluation

| Test ID | Test Name | Objective | SRS Basis |
|---|---|---|---|
| TC-VAE-01 | Session & Authentication Manager | Verify LDAP authentication/authorization enforcement and project/platform/version selection. | 3.2.6.1–4 |
| TC-VAE-02 | Model Setup Data Workflow Manager | Verify Model Setup Data file listing/selection, production start/monitor, data-source status display, and error display. | 3.2.6.5–9 |
| TC-VAE-03 | Analytical Data Workflow Manager | Verify Analytical Evaluation Data source selection, record/scenario input handling, production start/track, and scenario metadata recording. | 3.2.6.10–14, 48 |
| TC-VAE-04 | Working Model Editor | Verify non-destructive structural editing of a working model derived from the Core System Model. | 3.2.6.17 |
| TC-VAE-05 | Structural & Dependency Analysis Engine | Verify structural/communication/runtime-environment relationship analysis, binding-status display, and circular/disconnected-relationship detection. | 3.2.6.15–16, 18–19, 28–29 |
| TC-VAE-06 | Architectural Rule Verification Engine | Verify QoS, publisher/consumer, communication-consistency, load-balancing, core-allocation, OS-settings, memory-allocation, resource-contention, and architectural-rule-violation detection, and conforming/non-conforming classification. | 3.2.6.20–27, 30, 42 |
| TC-VAE-07 | Simulation Analysis Engine | Verify message-flow, inactive-node/relationship-impact, traffic, and fault/load-propagation analyses using Scenario Generator data. | 3.2.6.31–36 |
| TC-VAE-08 | Field Data Analysis Engine | Verify operational/health, resource-usage, error, message-flow, latency, drift, and event analyses using System Field Records data. | 3.2.6.37–41 |
| TC-VAE-09 | Model Visualization & Navigation UI | Verify search, filter, and zoom/pan/selection/attribute-display operations. | 3.2.6.43 |
| TC-VAE-10 | Findings & Reporting Manager | Verify finding presentation, cause-effect linkage, sort/filter, error recording, and exportable report generation. | 3.2.6.44–47, 49 |
| TC-VAE-11 | Automation Interface (CLI/Build Tools) | Verify analysis requests, status reporting, and concurrent/independent execution via CLI/build automation clients. | 3.2.6.50 |
| TC-VAE-12 | Installation Suitability Evaluator | Verify multi-heading suitability evaluation, rule scoring, blocking-decision logic, and independent per-unit/aggregate results. | 3.2.6.51–54 |

---

## 5. Test Schedule

Concrete calendar dates are outside the scope of this document and depend on the project's overall schedule. Test progression follows the CSCI's concept of execution (`../design/SDD.md` §4.2): MSD, SCG, and FRD tests (independent data producers) are executed first; ADP tests next (consumes SCG/FRD output); CSM tests next (consumes MSD/ADP output); VAE tests last (consumes CSM output and exercises all analysis capabilities).

---

## 6. Requirements Traceability

| SRS Paragraph(s) | Test ID |
|---|---|
| 3.2.1.1 | Demonstrated collectively by TC-MSD-01–05 (CSC-existence statement; no dedicated test) |
| 3.2.1.2–4 | TC-MSD-01 |
| 3.2.1.5–9, 12 | TC-MSD-02 |
| 3.2.1.10–11 | TC-MSD-03 |
| 3.2.1.13–16 | TC-MSD-04 |
| 3.2.1.17–19 | TC-MSD-05 |
| 3.2.2.1 | Demonstrated collectively by TC-SCG-01–03 (CSC-existence statement; no dedicated test) |
| 3.2.2.3, 6 | TC-SCG-01 |
| 3.2.2.2, 4 | TC-SCG-02 |
| 3.2.2.5, 7 | TC-SCG-03 |
| 3.2.3.1 | Demonstrated collectively by TC-FRD-01–02 (CSC-existence statement; no dedicated test) |
| 3.2.3.2, 5 | TC-FRD-01 |
| 3.2.3.3–4 | TC-FRD-02 |
| 3.2.3.6 | Non-functional (storage capacity) requirement; verification approach to be determined during the critical design phase, pending hardware sizing |
| 3.2.4.1 | Demonstrated collectively by TC-ADP-01–03 (CSC-existence statement; no dedicated test) |
| 3.2.4.2, 5 | TC-ADP-01 |
| 3.2.4.3, 6 | TC-ADP-02 |
| 3.2.4.4 | TC-ADP-03 |
| 3.2.5.1 | Demonstrated collectively by TC-CSM-01–06 (CSC-existence statement; no dedicated test) |
| 3.2.5.2–5, 9, 15 | TC-CSM-01 |
| 3.2.5.6–8 | TC-CSM-02 |
| 3.2.5.10–14 | TC-CSM-03 |
| 3.2.5.16–17 | TC-CSM-04 |
| 3.2.5.18–19 | TC-CSM-05 |
| 3.2.5.20 | TC-CSM-06 |
| 3.2.6.1–4 | TC-VAE-01 |
| 3.2.6.5–9 | TC-VAE-02 |
| 3.2.6.10–14, 48 | TC-VAE-03 |
| 3.2.6.17 | TC-VAE-04 |
| 3.2.6.15–16, 18–19, 28–29 | TC-VAE-05 |
| 3.2.6.20–27, 30, 42 | TC-VAE-06 |
| 3.2.6.31–36 | TC-VAE-07 |
| 3.2.6.37–41 | TC-VAE-08 |
| 3.2.6.43 | TC-VAE-09 |
| 3.2.6.44–47, 49 | TC-VAE-10 |
| 3.2.6.50 | TC-VAE-11 |
| 3.2.6.51–54 | TC-VAE-12 |

---

## 7. Notes

None.
