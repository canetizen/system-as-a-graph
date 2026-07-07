# Software Test Description and Plan (STD)
## System as a Graph (SaaG) Digital System Model
### Prepared in accordance with MIL-STD-498 (Data Item Descriptions DI-IPSC-81438 and DI-IPSC-81439)

---

## 1. Scope

### 1.1 Identification

This document is the Software Test Description (STD) for the **System as a Graph (SaaG) Digital System Model** CSCI, prepared in the format defined by MIL-STD-498, Data Item Descriptions DI-IPSC-81439 (Software Test Description) and DI-IPSC-81438 (Software Test Plan). It plans and details the formal qualification testing that demonstrates the CSCI satisfies `../requirements/SRS.md`.

### 1.2 System Overview

SaaG is a static digital system model built using an architectural digital twin approach, decomposed in `../design/SDD.md` into 6 CSCs (MSD, SCG, FRD, ADP, CSM, VAE) and 31 CSUs. Its external and internal interfaces are specified in `../design/SDD.md` §4.3; its persistent data stores in `../design/SDD.md` §4.4.

### 1.3 Document Overview

Section 3 describes the test environment and the preparations common to all test cases. Section 4 identifies and details the 31 tests planned, one per CSU defined in `../design/SDD.md`, all executed as part of a single CSCI-level formal qualification test effort (no separate CSU/CSC-level formal test levels are planned — see §3's note). For each test case, Section 4 gives: requirements traceability, prerequisite conditions, test inputs, test procedure, expected results, and evaluation criteria — phrased at the level of behavior already stated in `../requirements/SRS.md`/`../design/SDD.md`, without inventing concrete sample values, UI steps, or tool commands not yet defined by those documents. Section 5 addresses test progression/scheduling. Section 6 traces every SRS requirement exercised by these tests to its Test ID.

---

## 2. Referenced Documents

- MIL-STD-498, *Software Development and Documentation*, Data Item Descriptions DI-IPSC-81438 (Software Test Plan) and DI-IPSC-81439 (Software Test Description).
- `../requirements/SRS.md` — Software Requirements Specification for the SaaG CSCI.
- `../design/SDD.md` — Software Design Description for the SaaG CSCI.

---

## 3. Software Test Environment and Preparations

**Test level note**: all 31 tests identified in Section 4 are formal qualification tests conducted at the CSCI level — i.e., against the assembled SaaG CSCI, not against isolated CSUs in a separate unit-test harness. They are organized one-per-CSU purely for traceability to `../design/SDD.md`'s decomposition, not because CSU is a distinct formal test level.

### 3.1 Software Items

The test environment requires a stand-in or harness for each external interface identified in `../design/SDD.md` §4.3, plus representative test data for each capability area:

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

### 3.4 Test Preparations

Common to all 31 test cases, unless a test case states otherwise:

- The test environment described in §3.1–3.2 above (stand-ins for all 7 external interfaces, representative Model Setup Data and scenario/field-record test data) is available and reachable.
- The SaaG CSCI build under test is installed and its 6 CSCs (MSD, SCG, FRD, ADP, CSM, VAE) are running.
- A dedicated test project/platform/system-version identity is selected so test data does not interfere with other data in the same environment.
- Test execution and results recording follow §3.3 above.

---

## 4. Test Identification and Descriptions

Each test's objective and SRS basis are carried directly from the corresponding CSU's purpose in `../design/SDD.md` §5. Test type is "requirements-based functional test" for all 31 unless noted otherwise; pass/fail criteria is conformance to the SRS paragraphs traced. The table under each CSC heading summarizes its tests; the detailed description that follows each table gives, per test case, prerequisite conditions, test inputs, test procedure, expected results, and evaluation criteria.

### 4.1 MSD — Model Setup Data Generation

| Test ID | Test Name | Objective | SRS Basis |
|---|---|---|---|
| TC-MSD-01 | Data Source Connector & Configuration Manager | Verify controlled, traceable access and configuration management for the 4 external data sources, including both network-topology acquisition methods. | 3.2.1.2–4 |
| TC-MSD-02 | Configuration Data Acquisition | Verify retrieval of project/platform/version data and effective-version marking from the configuration management database, and error-status marking on deficiency/access/format failure. | 3.2.1.5–9, 12 |
| TC-MSD-03 | Software Unit Version Inventory Manager | Verify recording and candidate-version update of the Software Unit Version Inventory. | 3.2.1.10–11 |
| TC-MSD-04 | Source Repository Ingestion | Verify file transfer, per-file recording, missing-data reporting, and access/integrity error reporting from the source code repository. | 3.2.1.13–16 |
| TC-MSD-05 | Data Validation & Model Setup Data Assembler | Verify mandatory-field validation, failure recording, and assembly of the Model Setup Data file from data that passes verification. | 3.2.1.17–19 |

#### TC-MSD-01 — Data Source Connector & Configuration Manager
- **Requirements Traceability**: SRS 3.2.1.2–4.
- **Prerequisite Conditions**: test stand-ins for the configuration management database, source code repository, package repository, and network topology data source are reachable; both automatic and manual network-topology acquisition paths are available.
- **Test Inputs**: per-source configuration information (source type, name, access method, connection address, connection credentials) for each of the 4 sources; a network topology instance available both automatically and for manual entry.
- **Test Procedure**: configure each of the 4 data sources; invoke acquisition via the automatic network-topology method, then via manual entry; confirm configuration is saved and reusable.
- **Expected Test Results**: MSD manages and persists per-source configuration; both network-topology acquisition methods succeed and produce equivalent topology data.
- **Evaluation Criteria**: pass if all 4 sources are accessed using their configured connection information and both topology-acquisition methods succeed; fail otherwise.

#### TC-MSD-02 — Configuration Data Acquisition
- **Requirements Traceability**: SRS 3.2.1.5–9, 12.
- **Prerequisite Conditions**: the test configuration management database contains at least one project with multiple platforms and system versions, one marked effective.
- **Test Inputs**: a project selection; a deficient/inaccessible/malformed configuration-database response (for the error path).
- **Test Procedure**: acquire project, platform, and version information for the selected project; confirm the effective version is marked; repeat acquisition against the deficient/inaccessible/malformed response.
- **Expected Test Results**: project/platform/version data is retrieved and the effective version is distinctly marked; the deficient/inaccessible/malformed case is marked with an error status rather than silently accepted.
- **Evaluation Criteria**: pass if effective-version marking is correct in the normal case and an error status is recorded in the fault case; fail otherwise.

#### TC-MSD-03 — Software Unit Version Inventory Manager
- **Requirements Traceability**: SRS 3.2.1.10–11.
- **Prerequisite Conditions**: a selected project/platform/system version with a defined set of software unit versions; a candidate software unit version available for evaluation.
- **Test Inputs**: the defined software unit versions; one candidate software unit version to be evaluated for installation.
- **Test Procedure**: record the Software Unit Version Inventory for the selected scope; update it by adding the candidate version alongside the existing versions.
- **Expected Test Results**: the inventory reflects the existing versions and, after update, the candidate version alongside them.
- **Evaluation Criteria**: pass if the inventory is complete and the candidate version coexists correctly with the other recorded versions; fail otherwise.

#### TC-MSD-04 — Source Repository Ingestion
- **Requirements Traceability**: SRS 3.2.1.13–16.
- **Prerequisite Conditions**: the Software Unit Version Inventory from TC-MSD-03 is available; the test source code repository contains files for the in-scope software units, including at least one mandatory file deliberately withheld and one file with an access/integrity fault.
- **Test Inputs**: the in-scope software unit set; the deliberately-withheld mandatory file case; the access/integrity-fault file case.
- **Test Procedure**: ingest source code, installation scripts, and configuration files for the in-scope units; confirm per-file name/path/package-version/timestamp are recorded; repeat with the withheld-file and fault-file cases.
- **Expected Test Results**: normal ingestion records all required per-file metadata; the withheld-file case is reported with a missing-data status; the fault case is reported and recorded as an error.
- **Evaluation Criteria**: pass if all three outcomes (normal, missing-data, error) are correctly detected and reported; fail otherwise.

#### TC-MSD-05 — Data Validation & Model Setup Data Assembler
- **Requirements Traceability**: SRS 3.2.1.17–19.
- **Prerequisite Conditions**: source data collected by TC-MSD-01–04 is available, including at least one record with a missing mandatory field.
- **Test Inputs**: the collected source data set, including the deliberately-incomplete record.
- **Test Procedure**: run the mandatory-field-presence check across all source data; confirm failure recording for the incomplete record; assemble the data that passes verification into a Model Setup Data file.
- **Expected Test Results**: the incomplete record is rejected and its failure is recorded with reason/source/association/time; a Model Setup Data file is produced containing only data that passed verification.
- **Evaluation Criteria**: pass if the incomplete record is excluded and recorded as a failure, and the assembled file contains only verified data; fail otherwise.

### 4.2 SCG — Scenario Generator

| Test ID | Test Name | Objective | SRS Basis |
|---|---|---|---|
| TC-SCG-01 | Scenario Input Manager | Verify capture and traceable recording of scenario scope/type/interval/density/data-type inputs. | 3.2.2.3, 6 |
| TC-SCG-02 | Synthetic Data Generator | Verify synthetic data production conforms to the topic/message schema, field naming, and value-range constraints of the real software units. | 3.2.2.2, 4 |
| TC-SCG-03 | Scenario Output Recorder | Verify recorded synthetic data output includes scenario name/production time/project-platform-version, and is prepared for transfer to ADP. | 3.2.2.5, 7 |

#### TC-SCG-01 — Scenario Input Manager
- **Requirements Traceability**: SRS 3.2.2.3, 6.
- **Prerequisite Conditions**: SCG is available and idle.
- **Test Inputs**: a scenario scope, scenario type, time interval, data density, and data types to be produced.
- **Test Procedure**: submit the scenario inputs; confirm they are recorded traceably before generation begins.
- **Expected Test Results**: the submitted inputs are captured completely and are retrievable/traceable after submission.
- **Evaluation Criteria**: pass if all 5 input categories are recorded and traceable; fail otherwise.

#### TC-SCG-02 — Synthetic Data Generator
- **Requirements Traceability**: SRS 3.2.2.2, 4.
- **Prerequisite Conditions**: scenario inputs from TC-SCG-01 are available; the topic/message schema, field naming, and value-range constraints of the real software units are known to the test.
- **Test Inputs**: the recorded scenario inputs.
- **Test Procedure**: generate synthetic data from the scenario inputs; compare its structure, field naming, and value ranges against the real software units' topic/message schema.
- **Expected Test Results**: generated data is structurally equivalent to the real schema, field naming, and value-range constraints.
- **Evaluation Criteria**: pass if no structural, naming, or range deviation is found; fail otherwise.

#### TC-SCG-03 — Scenario Output Recorder
- **Requirements Traceability**: SRS 3.2.2.5, 7.
- **Prerequisite Conditions**: synthetic data from TC-SCG-02 is available.
- **Test Inputs**: the generated synthetic data and its originating scenario.
- **Test Procedure**: record the produced data together with scenario name, production time, and project/platform/version; confirm it is prepared for transfer to ADP.
- **Expected Test Results**: the recorded output includes all required metadata and is retrievable by ADP.
- **Evaluation Criteria**: pass if all metadata fields are present and ADP can retrieve the prepared output; fail otherwise.

### 4.3 FRD — Field Records Database

| Test ID | Test Name | Objective | SRS Basis |
|---|---|---|---|
| TC-FRD-01 | Record Upload Manager | Verify controlled, traceable upload of telemetry/system records with project/platform/version association, and detection/reporting of upload-time errors. | 3.2.3.2, 5 |
| TC-FRD-02 | Record Catalog Manager | Verify recorded metadata (source, upload time, project/platform/version) and list/search/select behavior across those criteria. | 3.2.3.3–4 |

#### TC-FRD-01 — Record Upload Manager
- **Requirements Traceability**: SRS 3.2.3.2, 5.
- **Prerequisite Conditions**: representative valid and invalid (format-incompatible / integrity-broken / missing-field) System Field Records are available for upload.
- **Test Inputs**: a valid record and each invalid-record variant.
- **Test Procedure**: upload the valid record and confirm project/platform/version association is recorded; upload each invalid variant and confirm the corresponding error condition is detected and reported.
- **Expected Test Results**: the valid record is stored with correct association; each invalid variant is detected and reported without being silently accepted.
- **Evaluation Criteria**: pass if the valid case is stored correctly and every invalid variant is detected; fail otherwise.

#### TC-FRD-02 — Record Catalog Manager
- **Requirements Traceability**: SRS 3.2.3.3–4.
- **Prerequisite Conditions**: multiple System Field Records exist across different projects, platforms, system versions, sources, and upload times.
- **Test Inputs**: search/filter criteria covering project, platform, system version, record source, and upload time, individually and combined.
- **Test Procedure**: list all records; search/filter using each criterion and combinations of them; select a record from the results.
- **Expected Test Results**: listing, search, filter, and selection return correct and complete results for every criterion tested.
- **Evaluation Criteria**: pass if all criteria and combinations return correct results; fail otherwise.

### 4.4 ADP — Analytical Data Preparation

| Test ID | Test Name | Objective | SRS Basis |
|---|---|---|---|
| TC-ADP-01 | Field Record Ingestion | Verify retrieval of System Field Records from FRD and detection/reporting of format/unreadable-data errors. | 3.2.4.2, 5 |
| TC-ADP-02 | Scenario Data Ingestion | Verify retrieval of synthetic data from SCG and detection/reporting of format/unreadable/missing-field errors. | 3.2.4.3, 6 |
| TC-ADP-03 | Analytical Data Assembler | Verify processing/association of ingested data into Analytical Evaluation Data transmitted to CSM. | 3.2.4.4 |

#### TC-ADP-01 — Field Record Ingestion
- **Requirements Traceability**: SRS 3.2.4.2, 5.
- **Prerequisite Conditions**: FRD contains at least one valid and one format-incompatible/unreadable System Field Record.
- **Test Inputs**: the valid and invalid records.
- **Test Procedure**: retrieve the valid record from FRD for Analytical Evaluation Data production; retrieve the invalid record and confirm error detection/reporting.
- **Expected Test Results**: the valid record is ingested successfully; the invalid record's format/unreadable condition is detected and reported.
- **Evaluation Criteria**: pass if both outcomes are correct; fail otherwise.

#### TC-ADP-02 — Scenario Data Ingestion
- **Requirements Traceability**: SRS 3.2.4.3, 6.
- **Prerequisite Conditions**: SCG contains at least one valid synthetic data output and one variant with format incompatibility, unreadable data, or a missing field.
- **Test Inputs**: the valid and invalid synthetic data outputs.
- **Test Procedure**: retrieve the valid output from SCG for Analytical Evaluation Data production; retrieve the invalid variant and confirm error detection/reporting.
- **Expected Test Results**: the valid output is ingested successfully; the invalid variant's condition is detected and reported.
- **Evaluation Criteria**: pass if both outcomes are correct; fail otherwise.

#### TC-ADP-03 — Analytical Data Assembler
- **Requirements Traceability**: SRS 3.2.4.4.
- **Prerequisite Conditions**: ingested data from TC-ADP-01 or TC-ADP-02 is available.
- **Test Inputs**: the ingested System Field Records or synthetic data.
- **Test Procedure**: process and associate the ingested data; produce Analytical Evaluation Data and transmit it toward CSM.
- **Expected Test Results**: Analytical Evaluation Data is produced and made available to CSM.
- **Evaluation Criteria**: pass if CSM can retrieve correctly-associated Analytical Evaluation Data; fail otherwise.

### 4.5 CSM — Node-Relationship Based Core System Model

| Test ID | Test Name | Objective | SRS Basis |
|---|---|---|---|
| TC-CSM-01 | Model Construction Engine | Verify Model Setup Data ingestion, validation, conversion to a node-relationship Core System Model, error reporting, and model metadata recording. | 3.2.5.2–5, 9, 15 |
| TC-CSM-02 | Node-Relationship Schema Manager | Verify all required node/relationship types are representable, and CPU/OS/runtime attributes are queryable. | 3.2.5.6–8 |
| TC-CSM-03 | Analytical Data Binder | Verify Analytical Evaluation Data association/matching/provenance-preservation/separability, and unmatched-record reporting. | 3.2.5.10–14 |
| TC-CSM-04 | Model Access Provider | Verify VAE can access the Core System Model's nodes, relationships, and bound Analytical Evaluation Data. | 3.2.5.16–17 |
| TC-CSM-05 | Concurrency & Session Manager | Verify concurrent multi-session read/write and concurrent pipeline/analysis operations do not compromise integrity or result consistency. | 3.2.5.18–19 |
| TC-CSM-06 | Candidate Evaluation Model Builder | Verify creation of an isolated, process-specific Core System Model for a candidate software unit version. | 3.2.5.20 |

#### TC-CSM-01 — Model Construction Engine
- **Requirements Traceability**: SRS 3.2.5.2–5, 9, 15.
- **Prerequisite Conditions**: a Model Setup Data file from TC-MSD-05 is available, including a variant with a missing entity or invalid relationship.
- **Test Inputs**: the valid Model Setup Data file and the fault variant.
- **Test Procedure**: submit the valid file for Core System Model construction; confirm project/platform/version association, model metadata, and successful construction; submit the fault variant and confirm error detection/reporting.
- **Expected Test Results**: the valid file produces a correctly-associated Core System Model with recorded metadata; the fault variant is detected and reported without producing a silently-incomplete model.
- **Evaluation Criteria**: pass if both outcomes are correct; fail otherwise.

#### TC-CSM-02 — Node-Relationship Schema Manager
- **Requirements Traceability**: SRS 3.2.5.6–8.
- **Prerequisite Conditions**: a constructed Core System Model from TC-CSM-01 covering at least one instance of each of the 12 node types and each of the 6 relationship types in `../requirements/SRS.md` 3.2.5.6–7.
- **Test Inputs**: queries for each node type, each relationship type, and the CPU-allocation/OS-settings/runtime-environment attributes of software-unit nodes.
- **Test Procedure**: query the model for each node type and relationship type; query the software-unit attributes.
- **Expected Test Results**: every node type and relationship type is representable and retrievable; the 3 attribute categories are queryable on software-unit nodes.
- **Evaluation Criteria**: pass if all 12 node types, all 6 relationship types, and all 3 attribute categories are correctly represented and queryable; fail otherwise.

#### TC-CSM-03 — Analytical Data Binder
- **Requirements Traceability**: SRS 3.2.5.10–14.
- **Prerequisite Conditions**: a Core System Model from TC-CSM-01/02 and Analytical Evaluation Data from TC-ADP-03, including at least one record with no corresponding node/relationship.
- **Test Inputs**: the Analytical Evaluation Data set, including the unmatched record.
- **Test Procedure**: bind the data to the model; confirm project/platform/version/model association, correct node/relationship matching, and provenance preservation (field vs. synthetic); confirm the unmatched record is reported; confirm the Core System Model's own nodes/relationships are unchanged by the binding.
- **Expected Test Results**: matched records are bound correctly with provenance preserved; the unmatched record is reported; the Core System Model is unaltered and remains separable from the bound data.
- **Evaluation Criteria**: pass if matching, provenance, unmatched-reporting, and separability all hold; fail otherwise.

#### TC-CSM-04 — Model Access Provider
- **Requirements Traceability**: SRS 3.2.5.16–17.
- **Prerequisite Conditions**: a Core System Model with bound Analytical Evaluation Data from TC-CSM-03.
- **Test Inputs**: a VAE read request for nodes, relationships, and bound Analytical Evaluation Data.
- **Test Procedure**: request the model's nodes, relationships, and bound Analytical Evaluation Data from VAE.
- **Expected Test Results**: VAE receives complete, correct access to the requested elements.
- **Evaluation Criteria**: pass if VAE's view matches the underlying model and bound data exactly; fail otherwise.

#### TC-CSM-05 — Concurrency & Session Manager
- **Requirements Traceability**: SRS 3.2.5.18–19.
- **Prerequisite Conditions**: a Core System Model accessible to multiple concurrent user sessions and concurrent pipeline/analysis operations.
- **Test Inputs**: concurrent read/write requests from multiple sessions; concurrent production-pipeline and user analysis/simulation operations.
- **Test Procedure**: issue overlapping read/write requests from multiple sessions against the same model; issue a production-pipeline operation concurrently with a user analysis/simulation operation.
- **Expected Test Results**: model integrity and query-result consistency are preserved under concurrent access; the pipeline and user operations complete independently without interfering with one another.
- **Evaluation Criteria**: pass if no integrity violation, inconsistent result, or cross-operation interference is observed; fail otherwise.

#### TC-CSM-06 — Candidate Evaluation Model Builder
- **Requirements Traceability**: SRS 3.2.5.20.
- **Prerequisite Conditions**: a candidate software unit version from TC-MSD-03 and the other software units of the target system version.
- **Test Inputs**: the candidate version combined with the target system version's other units.
- **Test Procedure**: create a process-specific Core System Model combining the candidate with the other units; run concurrently with an unrelated evaluation to confirm isolation.
- **Expected Test Results**: a correctly-combined, isolated Core System Model is created without affecting other concurrent evaluations.
- **Evaluation Criteria**: pass if the model correctly reflects the candidate combination and remains isolated from concurrent evaluations; fail otherwise.

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

#### TC-VAE-01 — Session & Authentication Manager
- **Requirements Traceability**: SRS 3.2.6.1–4.
- **Prerequisite Conditions**: a test LDAP directory service with known valid and invalid credentials; a project/platform with multiple system versions, one marked effective.
- **Test Inputs**: valid credentials, invalid credentials, and a project/platform/version selection.
- **Test Procedure**: attempt access with invalid credentials, then valid credentials; select a project/platform/version and confirm the effective version is distinctly displayed.
- **Expected Test Results**: invalid credentials are rejected; valid credentials grant access within the user's authorizations; the effective version is distinctly displayed.
- **Evaluation Criteria**: pass if authentication, authorization scoping, and effective-version display are all correct; fail otherwise.

#### TC-VAE-02 — Model Setup Data Workflow Manager
- **Requirements Traceability**: SRS 3.2.6.5–9.
- **Prerequisite Conditions**: an authenticated session from TC-VAE-01; multiple Model Setup Data files for the selected scope; a data source in a deliberately inaccessible state.
- **Test Inputs**: a file selection; a production-start command; the inaccessible-data-source condition.
- **Test Procedure**: list and select a Model Setup Data file; start production and monitor status through in-progress/successful/failed; observe data-source accessibility display; trigger the inaccessible-source condition and observe error display.
- **Expected Test Results**: correct file listing/selection; accurate status monitoring; accurate accessibility display; correct error display for the inaccessible case.
- **Evaluation Criteria**: pass if all four behaviors are correct; fail otherwise.

#### TC-VAE-03 — Analytical Data Workflow Manager
- **Requirements Traceability**: SRS 3.2.6.10–14, 48.
- **Prerequisite Conditions**: an authenticated session; available System Field Records and Scenario Generator inputs.
- **Test Inputs**: a data-source selection (field records or synthetic); field-record selection or scenario inputs accordingly.
- **Test Procedure**: select each data-source option in turn; provide the corresponding selection/inputs; start and track production; confirm scenario metadata is recorded when synthetic data is used.
- **Expected Test Results**: both data-source paths function correctly; production is tracked with visible errors when they occur; scenario metadata is recorded correctly.
- **Evaluation Criteria**: pass if both paths and metadata recording are correct; fail otherwise.

#### TC-VAE-04 — Working Model Editor
- **Requirements Traceability**: SRS 3.2.6.17.
- **Prerequisite Conditions**: a Core System Model accessible via TC-CSM-04.
- **Test Inputs**: node/relationship additions, removals, and attribute updates on a derived working model.
- **Test Procedure**: derive a working model; add/remove nodes and relationships and update attributes; run a verification/analysis operation against the updated working model; confirm the original Core System Model is unchanged.
- **Expected Test Results**: structural changes succeed without breaking working-model integrity; analysis runs correctly against the updated working model; the underlying Core System Model is unaffected.
- **Evaluation Criteria**: pass if the working model updates correctly and the Core System Model remains unmodified; fail otherwise.

#### TC-VAE-05 — Structural & Dependency Analysis Engine
- **Requirements Traceability**: SRS 3.2.6.15–16, 18–19, 28–29.
- **Prerequisite Conditions**: a Core System Model including at least one circular dependency and one disconnected/missing/invalid/unmatched relationship, deliberately introduced for the test.
- **Test Inputs**: the model with and without the deliberately-introduced faults.
- **Test Procedure**: run structural/communication/runtime-environment relationship analysis with and without Analytical Evaluation Data; confirm binding-status display; run circular-dependency and disconnected/invalid-relationship detection against the faulted model.
- **Expected Test Results**: analysis runs correctly with and without Analytical Evaluation Data and without altering the Core System Model; the introduced circular dependency and relationship faults are detected.
- **Evaluation Criteria**: pass if all introduced faults are detected and the model is unaltered; fail otherwise.

#### TC-VAE-06 — Architectural Rule Verification Engine
- **Requirements Traceability**: SRS 3.2.6.20–27, 30, 42.
- **Prerequisite Conditions**: a Core System Model containing at least one deliberate violation of each rule category in SRS 3.2.6.20–27, 30 (once critical-design-phase rule definitions exist to violate).
- **Test Inputs**: the model with each deliberate violation.
- **Test Procedure**: run verification against QoS conformance, publisher/consumer matching, communication consistency, load balancing, core allocation, OS settings, memory allocation, resource contention, and architectural-rule-violating patterns; observe the conforming/non-conforming classification for each.
- **Expected Test Results**: each deliberately-introduced violation is detected and the model is classified non-conforming for that check; an unmodified model is classified conforming.
- **Evaluation Criteria**: pass if every introduced violation is detected and classification is correct in both the violating and non-violating cases; fail otherwise. **Note**: full execution depends on the QoS/load-balancing/core-allocation/OS-settings/memory-allocation/architectural rule sets that `../requirements/SRS.md` defers to the critical design phase.

#### TC-VAE-07 — Simulation Analysis Engine
- **Requirements Traceability**: SRS 3.2.6.31–36.
- **Prerequisite Conditions**: Analytical Evaluation Data produced from Scenario Generator synthetic data (TC-SCG-03), bound to a Core System Model (TC-CSM-03).
- **Test Inputs**: a scenario driving message flow, a node/relationship set to inactive, an increased topic/message density scenario, and a fault/load/communication-interruption/bandwidth-narrowing scenario.
- **Test Procedure**: run message-flow analysis; simulate a node/relationship becoming inactive and observe the evaluated effect; run traffic analysis under increased density and changed publish/consume behavior; run propagation analysis for the fault/load scenario and observe the reported path; observe the top-resource-usage/most-intensive-messaging summary.
- **Expected Test Results**: each analysis produces results consistent with the scenario's synthetic data, including a correct propagation path and correct summary indicators.
- **Evaluation Criteria**: pass if all 6 analysis behaviors (3.2.6.31–36) produce correct results for their respective scenarios; fail otherwise.

#### TC-VAE-08 — Field Data Analysis Engine
- **Requirements Traceability**: SRS 3.2.6.37–41.
- **Prerequisite Conditions**: Analytical Evaluation Data produced from System Field Records (TC-ADP-01, TC-CSM-03), including at least one deliberate architectural-drift condition (entity present in Model Setup Data but not observed at runtime, or vice versa, or incompatible).
- **Test Inputs**: the field-record-derived Analytical Evaluation Data, including the drift condition.
- **Test Procedure**: run analyses on operational/health status, resource usage, error/warning/restart/timeout information, message flow, communication latency/loss/success rate, and topic activity; compare Model Setup Data to observed runtime data for drift; analyze associated event records; observe the top-resource-usage/most-intensive-messaging summary.
- **Expected Test Results**: each analysis category (3.2.6.38) produces correct results; the introduced drift condition is correctly classified into one of the 3 drift categories (3.2.6.39); event and summary analyses are correct.
- **Evaluation Criteria**: pass if all analysis categories and the drift classification are correct; fail otherwise.

#### TC-VAE-09 — Model Visualization & Navigation UI
- **Requirements Traceability**: SRS 3.2.6.43.
- **Prerequisite Conditions**: a populated Core System Model spanning multiple types, projects, platforms, system versions, and software units.
- **Test Inputs**: search terms; filter criteria by type, project, platform, system version, and software unit; zoom/pan/selection actions.
- **Test Procedure**: search for entities/relationships; filter by each criterion individually and combined; perform zoom in, zoom out, pan, and selection with attribute display.
- **Expected Test Results**: search and filter return correct results for every criterion; visual operations behave correctly and attribute display is accurate on selection.
- **Evaluation Criteria**: pass if all search/filter/visual operations behave correctly; fail otherwise.

#### TC-VAE-10 — Findings & Reporting Manager
- **Requirements Traceability**: SRS 3.2.6.44–47, 49.
- **Prerequisite Conditions**: findings produced by TC-VAE-05/06/07/08, including at least two findings with a cause-and-effect relationship, and an operation deliberately interrupted by an error.
- **Test Inputs**: the finding set; sort/filter criteria (operation type, evaluation result, finding type, severity, project, platform, version, affected nodes); the interrupted-operation condition.
- **Test Procedure**: display each finding with its 7 required fields; confirm cause-and-effect linkage between the related findings; sort/filter findings by each criterion; confirm error cause/stage/time recording for the interrupted operation; generate a summary and a detailed report and confirm all 12 required report fields are present.
- **Expected Test Results**: findings, linkage, sort/filter, error recording, and report content are all complete and correct.
- **Evaluation Criteria**: pass if all finding fields, the cause-effect link, every sort/filter criterion, error recording, and all 12 report fields are correct; fail otherwise.

#### TC-VAE-11 — Automation Interface (CLI/Build Tools)
- **Requirements Traceability**: SRS 3.2.6.50.
- **Prerequisite Conditions**: a test automation client (CLI/build-tool stand-in) able to submit requests and poll status.
- **Test Inputs**: an analysis request submitted via the automation client, concurrently with an interactive-user-driven analysis.
- **Test Procedure**: submit an analysis request via the CLI/automation client; poll status from both the automation client and an interactive session; confirm the CLI-driven and interactive-driven analyses execute concurrently and independently.
- **Expected Test Results**: the automation client's request is accepted and its status is visible to both the client and interactive users; concurrent operations do not interfere with one another.
- **Evaluation Criteria**: pass if status visibility and operation independence both hold; fail otherwise.

#### TC-VAE-12 — Installation Suitability Evaluator
- **Requirements Traceability**: SRS 3.2.6.51–54.
- **Prerequisite Conditions**: at least 2 candidate software units (one with a critical-severity finding or blocking-rule violation, one without), each with a defined evaluation profile (rule identifier, evaluation heading, severity, weight, acceptance criterion, blocking status).
- **Test Inputs**: the 2 candidate software units and their evaluation profiles.
- **Test Procedure**: evaluate each candidate across the 4 evaluation headings (3.2.6.51); observe the conformance score/class computed per rule; submit both evaluations under independent operation identifiers within the same production-pipeline run.
- **Expected Test Results**: the non-critical/non-blocking candidate receives a score-based result; the critical/blocking candidate is forced to "non-conforming" regardless of its overall score, and the pipeline-blocking decision is transmitted to the automation client; both candidates' results (score, class, blocking findings, decision) and the aggregate result are reported in machine-processable format under independent operation identifiers.
- **Evaluation Criteria**: pass if the blocking override, per-candidate independence, and machine-processable aggregate reporting are all correct; fail otherwise.

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
