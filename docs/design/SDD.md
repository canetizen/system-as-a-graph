# Software Design Description (SDD)
## System as a Graph (SaaG) Digital System Model
### Prepared in accordance with MIL-STD-498 (Data Item Description DI-IPSC-81435)

---

## 1. Scope

### 1.1 Identification

This document is the Software Design Description (SDD) for the **System as a Graph (SaaG) Digital System Model** CSCI, prepared in the format defined by MIL-STD-498, Data Item Description DI-IPSC-81435. It describes the design that satisfies the requirements stated in `../requirements/SRS.md`.

### 1.2 System Overview

SaaG is a static digital system model built using an architectural digital twin approach: it represents the structural and relational architecture of the target system as a node-relationship graph, without executing the target system's software. Software units, middleware and communication services, processor/console units, topics, and messages are modeled as nodes; dependency, publishing, and consuming relationships between them are modeled as relationships. Behavioral analysis is achieved by overlaying Analytical Evaluation Data — derived from field records or a scenario generator — onto this structural graph, rather than by running the components themselves.

### 1.3 Document Overview

This SDD specifies the CSCI-wide design decisions (Section 3), the CSCI's architectural decomposition into Computer Software Components (CSCs) and its concept of execution (Section 4), the detailed design of each CSC down to Computer Software Unit (CSU) level (Section 5), and the traceability of every SRS requirement to the design element that satisfies it (Section 6). Interface characteristics and database designs are specified in companion documents — the Interface Design Description (IDD) and Database Design Description (DBDD) — and are only referenced here, not duplicated.

---

## 2. Referenced Documents

- MIL-STD-498, *Software Development and Documentation*, Data Item Description DI-IPSC-81435 (Software Design Description).
- `../requirements/SRS.md` — Software Requirements Specification for the SaaG CSCI (parent requirements document for this SDD).
- `IDD.md` — Interface Design Description for the SaaG CSCI.
- `DBDD.md` — Database Design Description for the SaaG CSCI.

---

## 3. CSCI-Wide Design Decisions

1. **Static digital twin, no execution**: The CSCI never executes the target system's actual software units; it constructs and analyzes a node-relationship representation of the system's architecture (SRS 1.2).
2. **Separable structural and behavioral layers**: The structural graph (Core System Model, built from Model Setup Data) and the behavioral overlay (Analytical Evaluation Data) are constructed independently and bound together without either altering the other, so they remain separable at all times (SRS 3.2.5.13).
3. **Concurrency-safe shared model access**: Multiple user sessions, and multiple concurrent production-pipeline/analysis/simulation operations, read and write the same Core System Model without compromising model integrity or result consistency (SRS 3.2.5.18–19).
4. **Non-destructive experimentation**: Structural "what-if" changes (adding/removing nodes or relationships, altering attributes) are performed only on a working model derived from the Core System Model, never on the Core System Model itself (SRS 3.2.6.17).
5. **Common validation-and-error-recording pattern**: Every data-acquisition path in the CSCI (configuration data, source repository files, field records, synthetic data, Model Setup Data) performs format/integrity/mandatory-field checks and records failures with a consistent set of attributes (source, reason, time), rather than each CSC inventing its own error model.

---

## 4. CSCI Architectural Design

### 4.1 CSCI Components

The SaaG CSCI is decomposed into 6 Computer Software Components (CSCs), mapped 1:1 onto the capability areas already defined in the SRS:

| CSC | Abbreviation | SRS Reference | CSUs | SDD Reference |
|---|---|---|---|---|
| Model Setup Data Generation | MSD | §3.2.1 | 5 | §5.1 |
| Scenario Generator | SCG | §3.2.2 | 3 | §5.2 |
| Field Records Database | FRD | §3.2.3 | 2 | §5.3 |
| Analytical Data Preparation | ADP | §3.2.4 | 3 | §5.4 |
| Node-Relationship Based Core System Model | CSM | §3.2.5 | 6 | §5.5 |
| Design Verification, Analysis and Evaluation | VAE | §3.2.6 | 12 | §5.6 |

### 4.2 Concept of Execution

1. **MSD** acquires and validates data from the configuration management database, source code repository, package repository, and network topology source, and assembles it into a Model Setup Data file.
2. **CSM** ingests the Model Setup Data file and constructs the Core System Model (nodes and relationships).
3. In parallel, **SCG** produces synthetic data from user-defined scenarios, and **FRD** stores System Field Records uploaded from the field.
4. **ADP** consumes either the System Field Records (from FRD) or the synthetic data (from SCG) — never both for the same run — and produces Analytical Evaluation Data.
5. **CSM** binds the Analytical Evaluation Data to the relevant nodes and relationships of the Core System Model, preserving which upstream source (field or synthetic) produced it.
6. **VAE** is the sole component through which users and automation clients (CLI/build tools) interact with the model: it drives the MSD/CSM/ADP production processes, performs read-only verification and analysis against the bound model (or a derived working model), and reports findings, reports, and installation-suitability decisions.

### 4.3 Interface Design

Interface characteristics for all external interfaces (configuration management DB, source code repository, package repository, network topology source, field-data recording mechanism, LDAP directory service, CLI/build automation) and internal interfaces (MSD→CSM, SCG→ADP, FRD→ADP, ADP→CSM, CSM→VAE) are specified in `IDD.md` §3.3 and §3.4 respectively. This SDD does not restate them.

---

## 5. CSCI Detailed Design

### 5.1 MSD — Model Setup Data Generation

#### 5.1.1 CSC-wide design decisions
All external data acquisition is funneled through a common validation and error-recording path (mandatory-field checks, missing-data status, access/authorization/integrity error handling) before a single Model Setup Data file is assembled (SRS 3.2.1.1).

#### 5.1.2 CSC architectural design
MSD is composed of 5 CSUs: Data Source Connector & Configuration Manager, Configuration Data Acquisition, Software Unit Version Inventory Manager, Source Repository Ingestion, and Data Validation & Model Setup Data Assembler. Data flows left to right through this list, converging on the assembled Model Setup Data file passed to CSM.

#### 5.1.3 CSU detailed design

**5.1.3.1 Data Source Connector & Configuration Manager**
Purpose: manage controlled, traceable access to the four external data sources (configuration management database, source code repository, package repository, network topology data source), including user-definable per-source configuration (source type, name, access method, connection address, credentials) and the two supported methods of network topology acquisition (automatic or manual entry). Traces to SRS 3.2.1.2–4. Interface characteristics: see IDD. Data: see DBDD.

**5.1.3.2 Configuration Data Acquisition**
Purpose: retrieve current project, platform, and system version information from the configuration management database; mark the effective version; mark the acquisition process with an error status on deficiency, access error, or format incompatibility. Traces to SRS 3.2.1.5–9, 12.

**5.1.3.3 Software Unit Version Inventory Manager**
Purpose: record and update the Software Unit Version Inventory (software unit name/version per project, platform, version), including insertion of a candidate software unit version alongside the other defined versions. Traces to SRS 3.2.1.10–11. Data: see DBDD.

**5.1.3.4 Source Repository Ingestion**
Purpose: transfer source code, installation scripts, and configuration files for the software units in scope from the source code repository; record file name, path, package/version, and update timestamp per file; report missing-data status for mandatory files that cannot be obtained; report access/authorization/integrity errors. Traces to SRS 3.2.1.13–16.

**5.1.3.5 Data Validation & Model Setup Data Assembler**
Purpose: perform a mandatory-field-presence check across all received/manually-entered source data; record error reason, source name/type, project/platform association, and error time for each failure; assemble the data that passes verification into the Model Setup Data file handed off to CSM. Traces to SRS 3.2.1.17–19.

---

### 5.2 SCG — Scenario Generator

#### 5.2.1 CSC-wide design decisions
Synthetic data generation is fully decoupled from field data collection; scenario inputs and the data they produced are recorded together so any synthetic data set is traceable back to the exact inputs that generated it (SRS 3.2.2.6).

#### 5.2.2 CSC architectural design
SCG is composed of 3 CSUs: Scenario Input Manager, Synthetic Data Generator, and Scenario Output Recorder.

#### 5.2.3 CSU detailed design

**5.2.3.1 Scenario Input Manager**
Purpose: capture and traceably record user-defined scenario inputs — scenario scope, scenario type, time interval, data density, and data types to be produced. Traces to SRS 3.2.2.3, 6.

**5.2.3.2 Synthetic Data Generator**
Purpose: serve as the data source for system-wide simulation processes; produce synthetic data structurally equivalent to the topic/message schema, field naming, and value-range constraints used by the actual software units. Traces to SRS 3.2.2.2, 4.

**5.2.3.3 Scenario Output Recorder**
Purpose: record produced synthetic data together with scenario name, production time, and project/platform/system-version association; prepare the data for transfer to ADP. Traces to SRS 3.2.2.5, 7.

---

### 5.3 FRD — Field Records Database

#### 5.3.1 CSC-wide design decisions
System Field Records are stored centrally and indexed for retrieval by project, platform, system version, record source, and upload time; upload-time validation prevents malformed records from entering the store (SRS 3.2.3.1). Storage hardware disk capacity is an environment/infrastructure requirement (SRS 3.2.3.6) whose sizing will be determined during the critical design phase; it is not modeled as a CSU.

#### 5.3.2 CSC architectural design
FRD is composed of 2 CSUs: Record Upload Manager and Record Catalog Manager.

#### 5.3.3 CSU detailed design

**5.3.3.1 Record Upload Manager**
Purpose: accept user uploads of telemetry and system data records into the database in a controlled, traceable manner, associated with project/platform/system-version; detect and report format incompatibility, integrity errors, or missing fields at upload time. Traces to SRS 3.2.3.2, 5.

**5.3.3.2 Record Catalog Manager**
Purpose: record each uploaded System Field Record with its source, upload time, and project/platform/version association; support listing, search, and selection of existing records by project, platform, system version, record source, or upload time. Traces to SRS 3.2.3.3–4. Data: see DBDD.

---

### 5.4 ADP — Analytical Data Preparation

#### 5.4.1 CSC-wide design decisions
Analytical Evaluation Data is produced from exactly one of two upstream sources — System Field Records (via FRD) or synthetic data (via SCG) — through parallel, independently-validated ingestion paths that converge on a single assembly step (SRS 3.2.4.1).

#### 5.4.2 CSC architectural design
ADP is composed of 3 CSUs: Field Record Ingestion, Scenario Data Ingestion, and Analytical Data Assembler.

#### 5.4.3 CSU detailed design

**5.4.3.1 Field Record Ingestion**
Purpose: obtain System Field Records from FRD for Analytical Evaluation Data production; detect and report format incompatibility or unreadable data. Traces to SRS 3.2.4.2, 5.

**5.4.3.2 Scenario Data Ingestion**
Purpose: obtain synthetic data from SCG for Analytical Evaluation Data production; detect and report format incompatibility, unreadable data, or missing fields. Traces to SRS 3.2.4.3, 6.

**5.4.3.3 Analytical Data Assembler**
Purpose: process and appropriately associate the ingested System Field Records or synthetic data, and produce the Analytical Evaluation Data transmitted to CSM. Traces to SRS 3.2.4.4. Data: see DBDD.

---

### 5.5 CSM — Node-Relationship Based Core System Model

#### 5.5.1 CSC-wide design decisions
The structural graph (Core System Model) and the behavioral overlay (Analytical Evaluation Data) are built and bound as separable layers (SRS 3.2.5.1, 13) and exposed under concurrency control to multiple simultaneous consumers, including isolated per-candidate evaluation models used by the production deployment pipeline (SRS 3.2.5.18–20).

#### 5.5.2 CSC architectural design
CSM is composed of 6 CSUs: Model Construction Engine, Node-Relationship Schema Manager, Analytical Data Binder, Model Access Provider, Concurrency & Session Manager, and Candidate Evaluation Model Builder.

#### 5.5.3 CSU detailed design

**5.5.3.1 Model Construction Engine**
Purpose: accept the Model Setup Data produced by MSD; perform format/schema/integrity/mandatory-field checks; convert validated data into a node-relationship Core System Model associated with project/platform/system version; report missing-entity and invalid-relationship errors; record the Model Setup Data file used, creation time, and model status. Traces to SRS 3.2.5.2–5, 9, 15.

**5.5.3.2 Node-Relationship Schema Manager**
Purpose: define and maintain the node types (System, Software Segment, CSCI, CSC, CSU, Role, Topic, Message, Operator Console/Processor Units, Network components, Middleware Services, Communication Technology services) and relationship types (runs-on, uses-middleware/communication-service, publishes, consumes, depends-on, assigned-to-role); expose CPU allocation, OS settings, and runtime environment configuration as queryable node attributes. Traces to SRS 3.2.5.6–8. Data: see DBDD.

**5.5.3.3 Analytical Data Binder**
Purpose: accept Analytical Evaluation Data from ADP; associate it with the relevant project/platform/system version/model; match record, telemetry, and synthetic data to the corresponding nodes and relationships; preserve provenance (field vs. synthetic); keep the binding separable from the Core System Model; report unmatched node/relationship records. Traces to SRS 3.2.5.10–14.

**5.5.3.4 Model Access Provider**
Purpose: make the Core System Model, and the Analytical Evaluation Data bound to it, available for read access by VAE. Traces to SRS 3.2.5.16–17.

**5.5.3.5 Concurrency & Session Manager**
Purpose: handle concurrent read/write operations from multiple user sessions on the same Core System Model without compromising integrity or query-result consistency; execute production-pipeline operations and user analysis/simulation operations concurrently and independently of one another. Traces to SRS 3.2.5.18–19.

**5.5.3.6 Candidate Evaluation Model Builder**
Purpose: create a new, process-specific Core System Model combining a candidate software unit version under evaluation with the other software units of the target system version, isolated from other concurrent evaluations. Traces to SRS 3.2.5.20.

---

### 5.6 VAE — Design Verification, Analysis and Evaluation

#### 5.6.1 CSC-wide design decisions
All verification and analysis operations are read-only against the Core System Model (SRS 3.2.6.15, 18); structural experimentation happens only on a derived working model (§5.6.3.4). Analysis is organized by the kind of check being performed — rule-based static verification, scenario-driven simulation analysis, and field-record-driven observational analysis — with shared findings, reporting, and access-control infrastructure common to all of them.

#### 5.6.2 CSC architectural design
VAE is composed of 12 CSUs: Session & Authentication Manager, Model Setup Data Workflow Manager, Analytical Data Workflow Manager, Working Model Editor, Structural & Dependency Analysis Engine, Architectural Rule Verification Engine, Simulation Analysis Engine, Field Data Analysis Engine, Model Visualization & Navigation UI, Findings & Reporting Manager, Automation Interface (CLI/Build Tools), and Installation Suitability Evaluator.

#### 5.6.3 CSU detailed design

**5.6.3.1 Session & Authentication Manager**
Purpose: authenticate users against a defined LDAP directory service and restrict access to their authorizations; let the user select the working project/platform/system version and see the currently effective version; mediate VAE's interaction with MSD, SCG, ADP, and CSM. Traces to SRS 3.2.6.1–4.

**5.6.3.2 Model Setup Data Workflow Manager**
Purpose: list Model Setup Data files for the selected project/platform/version and let the user pick one; start and monitor the Model Setup Data production process (in progress/successful/failed); continuously display data-source accessibility status; display missing-data/access/authorization/format/integrity errors from MSD. Traces to SRS 3.2.6.5–9.

**5.6.3.3 Analytical Data Workflow Manager**
Purpose: let the user choose the Analytical Evaluation Data source (System Field Records or SCG synthetic data), select field records or specify scenario inputs accordingly, start/track synthetic- and Analytical-Evaluation-Data production and view errors, and record the scenario name/inputs/production time/project-platform-version association used. Traces to SRS 3.2.6.10–14, 48.

**5.6.3.4 Working Model Editor**
Purpose: derive a working model from the Core System Model and let the user add/remove nodes and relationships and update attributes without breaking structural integrity, enabling verification/analysis on the updated working model. Traces to SRS 3.2.6.17.

**5.6.3.5 Structural & Dependency Analysis Engine**
Purpose: start the Core System Model creation process and monitor its result; display Analytical Evaluation Data binding/matching status; analyze structural dependencies, communication connections, and runtime-environment relationships (with or without Analytical Evaluation Data); detect circular dependencies and disconnected/missing/invalid/unmatched structural relationships. Traces to SRS 3.2.6.15–16, 18–19, 28–29.

**5.6.3.6 Architectural Rule Verification Engine**
Purpose: statically verify the Core System Model against design rules — topic QoS conformance (durability, reliability, lifespan, transport priority), publisher/consumer matching, external-to-middleware communication consistency, software-unit load-balancing distribution, processor core allocation conformance, OS-settings conformance, runtime-environment memory allocation conformance, resource-contention/bottleneck detection, and architectural-rule-violating design patterns; classify each result as conforming/non-conforming. Traces to SRS 3.2.6.20–27, 30, 42.

**5.6.3.7 Simulation Analysis Engine**
Purpose: analyze Analytical Evaluation Data produced from SCG synthetic data — message flow direction/count/volume/frequency, the effect of a node/relationship becoming inactive, design-time traffic analysis under increased topic/message density or changed publish/consume behavior, propagation of fault/load/communication-interruption/bandwidth-narrowing conditions to dependent nodes (with affected path), and the highest-resource-usage/most-intensive-messaging entities. Traces to SRS 3.2.6.31–36.

**5.6.3.8 Field Data Analysis Engine**
Purpose: analyze Analytical Evaluation Data produced from System Field Records — operational/health status; processor/memory/storage/network usage; error/warning/restart/timeout information; message flow/volume/frequency; communication latency/message loss/successful-transmission rates; topic publish/consume activity; comparison of Model Setup Data vs. observed runtime entities/relationships (architectural drift: present-but-not-observed, observed-but-not-present, incompatible); event-record analysis; and highest-resource-usage/most-intensive-messaging entities. Traces to SRS 3.2.6.37–41.

**5.6.3.9 Model Visualization & Navigation UI**
Purpose: let the user search the node-relationship structure, filter by type/project/platform/system-version/software-unit, and perform zoom/pan/selection/attribute-display operations. Traces to SRS 3.2.6.43.

**5.6.3.10 Findings & Reporting Manager**
Purpose: present each finding with identifier, type, description, affected entity/relationship, related rule/acceptance criterion, supporting evidence, and severity (informational/low/medium/high/critical); record cause-and-effect relationships between findings from the same operation; support sort/filter of findings by operation type, result, finding type, severity, project, platform, version, or affected nodes; record error cause/interruption stage/error time for interrupted operations; generate exportable summary/detailed reports containing project/platform/version, model used, Analytical Evaluation Data used and its source, operation identifier/type/start/end time, evaluation result, findings, affected nodes/relationships, severity levels, and additional finding information. Traces to SRS 3.2.6.44–47, 49.

**5.6.3.11 Automation Interface (CLI/Build Tools)**
Purpose: accept analysis requests from Build Automation Tools and a Command Line Interface; present ongoing-operation status to both interactive users and automation clients (e.g., Jenkins); ensure requested analysis operations run concurrently and independently of one another. Traces to SRS 3.2.6.50.

**5.6.3.12 Installation Suitability Evaluator**
Purpose: evaluate a software unit's suitability for target-environment installation across structural/architectural conformance, interface/topic/communication conformance, dependency/integration conformance, and resource/performance sufficiency; score conformance per control rule (rule identifier, evaluation heading, severity, weight, acceptance criterion, blocking status); force a "non-conforming" installation result whenever a critical-severity finding or a blocking-rule violation occurs, regardless of overall score, and transmit the pipeline-blocking decision to the automation client; run installation evaluations for one or more software units under independent operation identifiers, reporting a separate score/class/blocking-findings/decision per unit plus an aggregate result, in machine-processable format. Traces to SRS 3.2.6.51–54.

---

## 6. Requirements Traceability

| SRS Paragraph(s) | Design Element |
|---|---|
| 3.2.1.1 | §5.1 MSD (CSC-wide) |
| 3.2.1.2–4 | §5.1.3.1 Data Source Connector & Configuration Manager |
| 3.2.1.5–9, 12 | §5.1.3.2 Configuration Data Acquisition |
| 3.2.1.10–11 | §5.1.3.3 Software Unit Version Inventory Manager |
| 3.2.1.13–16 | §5.1.3.4 Source Repository Ingestion |
| 3.2.1.17–19 | §5.1.3.5 Data Validation & Model Setup Data Assembler |
| 3.2.2.1 | §5.2 SCG (CSC-wide) |
| 3.2.2.3, 6 | §5.2.3.1 Scenario Input Manager |
| 3.2.2.2, 4 | §5.2.3.2 Synthetic Data Generator |
| 3.2.2.5, 7 | §5.2.3.3 Scenario Output Recorder |
| 3.2.3.1 | §5.3 FRD (CSC-wide) |
| 3.2.3.6 | §5.3.1 FRD (environment/infrastructure note) |
| 3.2.3.2, 5 | §5.3.3.1 Record Upload Manager |
| 3.2.3.3–4 | §5.3.3.2 Record Catalog Manager |
| 3.2.4.1 | §5.4 ADP (CSC-wide) |
| 3.2.4.2, 5 | §5.4.3.1 Field Record Ingestion |
| 3.2.4.3, 6 | §5.4.3.2 Scenario Data Ingestion |
| 3.2.4.4 | §5.4.3.3 Analytical Data Assembler |
| 3.2.5.1 | §5.5 CSM (CSC-wide) |
| 3.2.5.2–5, 9, 15 | §5.5.3.1 Model Construction Engine |
| 3.2.5.6–8 | §5.5.3.2 Node-Relationship Schema Manager |
| 3.2.5.10–14 | §5.5.3.3 Analytical Data Binder |
| 3.2.5.16–17 | §5.5.3.4 Model Access Provider |
| 3.2.5.18–19 | §5.5.3.5 Concurrency & Session Manager |
| 3.2.5.20 | §5.5.3.6 Candidate Evaluation Model Builder |
| 3.2.6.1–4 | §5.6.3.1 Session & Authentication Manager |
| 3.2.6.5–9 | §5.6.3.2 Model Setup Data Workflow Manager |
| 3.2.6.10–14, 48 | §5.6.3.3 Analytical Data Workflow Manager |
| 3.2.6.17 | §5.6.3.4 Working Model Editor |
| 3.2.6.15–16, 18–19, 28–29 | §5.6.3.5 Structural & Dependency Analysis Engine |
| 3.2.6.20–27, 30, 42 | §5.6.3.6 Architectural Rule Verification Engine |
| 3.2.6.31–36 | §5.6.3.7 Simulation Analysis Engine |
| 3.2.6.37–41 | §5.6.3.8 Field Data Analysis Engine |
| 3.2.6.43 | §5.6.3.9 Model Visualization & Navigation UI |
| 3.2.6.44–47, 49 | §5.6.3.10 Findings & Reporting Manager |
| 3.2.6.50 | §5.6.3.11 Automation Interface (CLI/Build Tools) |
| 3.2.6.51–54 | §5.6.3.12 Installation Suitability Evaluator |

---

## 7. Notes

None.
