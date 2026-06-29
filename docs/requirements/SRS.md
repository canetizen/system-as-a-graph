# Software Requirements Specification
## System-as-a-Graph (SaG)

A graph-based static digital-twin framework for the pre-deployment modelling, validation, analysis, and failure-impact evaluation of distributed publish–subscribe systems.

---

| Field | Value |
|---|---|
| Document | Software Requirements Specification (SRS) |
| Product | System-as-a-Graph (SaG) |
| Version | 0.1 (Baseline Draft) |
| Date | 2026-06-29 |
| Status | Draft — for review |
| Standard | Structured per ISO/IEC/IEEE 29148:2018 |
| Derived from | *System-as-a-Graph: Dağıtık Sistemler için Çizge Tabanlı Sayısal Sistem Modeli* (system-level requirements) |
| Implements upon | Software-as-a-Graph (`saag/`) framework |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [External Interface Requirements](#3-external-interface-requirements)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional (Quality) Requirements](#5-non-functional-quality-requirements)
6. [Verification](#6-verification)
7. [Requirements Traceability](#7-requirements-traceability)
8. [Appendix A — Glossary](#8-appendix-a--glossary)
9. [Appendix B — Open Decisions](#9-appendix-b--open-decisions)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the software requirements for **System-as-a-Graph (SaG)**, an open-source framework that models the structural and relational architecture of a distributed publish–subscribe system as a graph, and evaluates that architecture statically — without executing the target system. It refines the supplied system-level requirements into verifiable software requirements and traces each one back to its source.

The intended audience is the SaG development team, reviewers and maintainers of the open-source project, and integrators connecting SaG to a CI/CD deployment pipeline.

### 1.2 Scope

SaG ingests the structure of a deployed or planned distributed system from authoritative configuration sources, constructs a typed graph (the **Core System Model**), overlays analytical evaluation data derived either from field telemetry or from synthetic scenarios, and provides design-time validation, static analysis, what-if analysis, failure-impact simulation, architectural-drift detection, and an automatable deployment-suitability gate.

**In scope.** The five subsystems defined by the system-level requirements: Model Setup Data Generation (MKV), Scenario Generator (SUR), Analytical Data Preparation (AVH), the Core System Model (CSM), and Design Validation, Analysis and Evaluation (DAD).

**Out of scope (baseline).** Learned criticality prediction (GNN-based `Q(v)` scoring) and prescriptive architectural remediation are **not** part of this baseline, because the system-level requirements do not call for them. They are treated as a research-layer extension (see §2.6 and Appendix B, Decision A). The framework will neither modify nor monitor the running target system; it produces analyses, findings, and gate decisions only.

### 1.3 Relationship to Software-as-a-Graph

SaG is built on the existing **Software-as-a-Graph** SDK (`saag/`), which already provides the graph domain model, structural analysis, failure-impact simulation, anti-pattern detection, QoS conformance checks, and a verified separation between the structural model and simulation outputs (the *independence guarantee*). SaG reuses this analytical core unchanged and adds the data-ingestion, multi-tenancy, persistence, access-control, and orchestration envelope required for production and CI/CD use (see §2.1, §2.5).

### 1.4 Document Conventions

- Requirement statements use **shall** (mandatory), **should** (recommended), and **may** (optional).
- Software requirement identifiers: `SRS-<SUBSYSTEM>-NNN` (functional), `SRS-EXT-NNN` (external interface), `SRS-NFR-NNN` (quality).
- Each requirement cites its originating system-level requirement as `→ §s.i`, referencing the section and item of the source document (e.g. `→ §5.16`).
- Verification method tags: `[T]` Test, `[A]` Analysis, `[I]` Inspection, `[D]` Demonstration.

### 1.5 References

1. System-level requirements: *System-as-a-Graph: Dağıtık Sistemler için Çizge Tabanlı Sayısal Sistem Modeli.*
2. ISO/IEC/IEEE 29148:2018 — Systems and software engineering — Requirements engineering.
3. Software-as-a-Graph framework architecture (`ARCHITECTURE.md`, `docs/graph-model.md`, `docs/structural-analysis.md`, `docs/antipatterns.md`).

---

## 2. Overall Description

### 2.1 Product Perspective

SaG is a layered system. A reusable **analytical core** (the `saag/` SDK, hexagonal/ports-and-adapters architecture) performs graph modelling, structural analysis, simulation, and validation against an in-memory or graph-database repository. Around this core, SaG adds:

- an **ingestion layer** (MKV) that builds Model Setup Data from external authoritative sources;
- a **scenario/analytical-data layer** (SUR, AVH) that produces Analytical Evaluation Data from synthetic or field inputs;
- a **persistence and identity layer** that keys every artifact by *(project, platform, version)* and stores field records;
- a **presentation and orchestration layer** (interactive UI, CLI, and CI/CD automation entry point).

The core domain logic has no dependency on infrastructure, presentation, or ingestion concerns; these are accessed through defined ports.

### 2.2 Product Functions (Summary)

| Subsystem | Turkish source name | Function |
|---|---|---|
| **MKV** | Model Kurulum Verisi Üretimi | Acquire and validate structural model-setup data from authoritative sources. |
| **SUR** | Senaryo Üreteci | Generate synthetic, schema-faithful scenario data without field records. |
| **AVH** | Analitik Veri Hazırlama | Prepare Analytical Evaluation Data from field telemetry or synthetic data. |
| **CSM** | Çizge Tabanlı Çekirdek Sistem Modeli | Build the typed graph model and overlay analytical data without altering structure. |
| **DAD** | Tasarım Doğrulama, Analiz ve Değerlendirme | Validate, analyse, simulate, detect drift, report findings, and gate deployment. |

### 2.3 User Classes

- **System architect / analyst** — performs interactive validation, analysis, what-if studies, and simulation through the UI.
- **CI/CD automation client** (e.g. Jenkins, build tooling) — invokes deployment-suitability evaluation via CLI/API and consumes machine-readable results.
- **Administrator** — configures data-source connections and access control.

### 2.4 Operating Environment

SaG runs as a server-side application with a graph-database backend (Neo4j or an in-memory repository for testing), a relational/document store for field records and run history, a REST API, and a web user interface. It integrates with a configuration-management database, source-code and package repositories, a network-topology data source, an LDAP directory, and a CI/CD automation server.

### 2.5 Design and Implementation Constraints

- **C-1 Independence guarantee.** Structural analysis and any criticality computation shall operate only on the structural model; they shall not consume analytical (runtime or simulated) data. Analytical data is overlaid for simulation, drift detection, and field analysis only. *(This constraint is normative; see SRS-NFR-001/002.)*
- **C-2 No target execution.** SaG shall derive the dynamic dimension of the model from field records or scenario-generated data, never by executing the target system.
- **C-3 Non-destructive overlay.** Binding Analytical Evaluation Data shall not modify the structural entities or relationships of the Core System Model.
- **C-4 Core reuse.** The framework shall reuse the existing `saag/` analytical core (analysis, simulation, validation, anti-pattern detection) without forking it; new ingestion, persistence, and orchestration code shall sit outside the analytical core and invoke it through its use-case interfaces.
- **C-5 Open-source.** SaG shall be distributable under a recognised open-source licence, with all third-party dependencies licence-compatible.

### 2.6 Assumptions and Dependencies

- **A-1.** Authoritative external sources (configuration-management database, source/package repositories, network-topology source) are reachable and expose the metadata required for model construction.
- **A-2.** Field telemetry, where used, is collected by an external mechanism and made available to SaG; SaG does not instrument the target system.
- **A-3 (load-bearing — see Appendix B, Decision A).** Learned prediction (`Q(v)` via GNN) and prescriptive remediation are **out of scope** for this baseline, consistent with the system-level requirements. If they are later brought into product scope, they enter as an additive, clearly-bounded advisory capability that must preserve C-1.
- **A-4.** The MIL-STD-498 entity hierarchy (System, Software Segment, CSCI, CSC, CSU) and supporting entities (Role, Console/Processor, Network, Middleware/Communication services) are representable as first-class modelled entities, extending the prior five-type vocabulary (Application, Broker, Topic, Node, Library). The mapping strategy is a design decision (Appendix B, Decision C).

---

## 3. External Interface Requirements

### 3.1 Data Source Interfaces

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-EXT-001 | SaG shall connect to a configuration-management database to retrieve project, platform, version, and software-unit inventory information. | → §1.2, §1.6–§1.10 | [T] |
| SRS-EXT-002 | SaG shall connect to source-code repositories to retrieve source and configuration files for in-scope software units, capturing file name, path, commit id, branch, package/version, and update timestamp per file. | → §1.2, §1.12–§1.13 | [T] |
| SRS-EXT-003 | SaG shall connect to a package repository to retrieve package and version metadata for in-scope software units. | → §1.2 | [T] |
| SRS-EXT-004 | SaG shall obtain network-topology data either automatically from an external source or via manual user entry of topology parameters. | → §1.2, §1.3 | [T] |
| SRS-EXT-005 | SaG shall store, per data source, the source type, source name, access method, connection address, and required credentials as user-defined settings that are entered once and reused. | → §1.4 | [T] |

### 3.2 Field Records Database Interface

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-EXT-010 | SaG shall provide a Field Records Database that centrally stores telemetry and system data records ingested from the distributed field environment. | → §3.8 | [T] |
| SRS-EXT-011 | SaG shall allow a user to upload field telemetry and data records into the Field Records Database in a controlled, traceable manner, associating each upload with project, platform, and version. | → §3.10 | [T] |

### 3.3 Authentication Interface

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-EXT-020 | SaG shall authenticate user credentials against a configured LDAP directory service and grant access only to successfully authenticated users, within their authorised scope. | → §5.51 | [T] |

### 3.4 Automation / CI Interface

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-EXT-030 | SaG shall accept analysis and evaluation requests from a Build Automation Tool and a Command Line Interface in addition to the user interface. | → §5.52 | [T] |
| SRS-EXT-031 | SaG shall report the status of in-progress operations to both interactive users and automation clients. | → §5.52 | [T] |
| SRS-EXT-032 | SaG shall expose a single deployment-pipeline entry point that accepts a deployment-suitability request and returns a machine-readable result to the automation client. | → §5.53, §5.57 | [T] |

### 3.5 User Interface

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-EXT-040 | SaG shall provide an interactive interface for graph exploration supporting entity/relationship search, filtering by type/project/platform/version/software-unit, and zoom, pan, and selection. | → §5.46 | [D] |
| SRS-EXT-041 | SaG shall continuously display the reachability status of all configured data sources. | → §5.6 | [D] |

---

## 4. Functional Requirements

### 4.1 SaG-MKV — Model Setup Data Generation

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-MKV-001 | The MKV component shall produce Model Setup Data in a controlled, traceable, verifiable form suitable for transfer to the model-construction process. | → §1.1 | [A] |
| SRS-MKV-002 | MKV shall associate every data-acquisition operation with a project, platform, and version number. | → §1.5 | [T] |
| SRS-MKV-003 | MKV shall retrieve available projects, the platforms of a selected project, and the versions of a selected project/platform from the configuration-management database. | → §1.6–§1.8 | [T] |
| SRS-MKV-004 | MKV shall mark the currently effective (in-force) version among the retrieved versions. | → §1.9 | [T] |
| SRS-MKV-005 | MKV shall record, for the selected project/platform/version, the names and versions of the software units targeted for the environment as a *Software Unit Version Inventory*, in a traceable form. | → §1.10, §1.19 | [T] |
| SRS-MKV-006 | MKV shall retrieve, from the source-code repository, the source and configuration files of the software units in the Software Unit Version Inventory and import them. | → §1.12 | [T] |
| SRS-MKV-007 | MKV shall perform required-field/entity presence validation over all acquired source data and over manually entered network-topology parameters, as required for model construction. | → §1.16 | [T] |
| SRS-MKV-008 | MKV shall persist validated source data as a *Model Setup Data* file, ready for transfer to the model-construction process. | → §1.18 | [T] |
| SRS-MKV-009 | MKV shall mark the data-acquisition process as failed and record the reason, source name, source type, associated project/platform, and timestamp when missing data, access/connection/authorisation errors, or format incompatibility is detected. | → §1.11, §1.14–§1.15, §1.17 | [T] |

### 4.2 SaG-SUR — Scenario Generator

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-SUR-001 | The SUR component shall generate synthetic data from user-defined scenario inputs without requiring field records. | → §2.1 | [T] |
| SRS-SUR-002 | SUR shall serve as the data source for all simulation operations across the system. | → §2.2 | [A] |
| SRS-SUR-003 | SUR shall allow the user to specify scenario scope, scenario type, time range, data density, and the types of data to be generated. | → §2.3 | [T] |
| SRS-SUR-004 | SUR shall generate synthetic data that conforms to the same schema, field naming, and value-range constraints as field records. | → §2.4 | [T] |
| SRS-SUR-005 | SUR shall record generated synthetic data with scenario name, generation time, and associated project, platform, and version, and shall record the user inputs used in generation. | → §2.5–§2.6 | [T] |
| SRS-SUR-006 | SUR shall make generated synthetic data available to the Analytical Data Preparation component. | → §2.7 | [T] |

### 4.3 SaG-AVH — Analytical Data Preparation

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-AVH-001 | The AVH component shall prepare Analytical Evaluation Data in a controlled, traceable, verifiable form transferable to the Core System Model. | → §3.1 | [A] |
| SRS-AVH-002 | AVH shall ingest telemetry and system records as *System Field Records*, either directly or from the Field Records Database. | → §3.2, §3.9 | [T] |
| SRS-AVH-003 | AVH shall ingest synthetic data produced by the Scenario Generator. | → §3.3 | [T] |
| SRS-AVH-004 | AVH shall produce Analytical Evaluation Data from either System Field Records or Scenario-Generator synthetic data. | → §3.4–§3.5 | [T] |
| SRS-AVH-005 | AVH shall detect and record format incompatibility, unreadable data, and (for synthetic input) missing fields, reporting the condition. | → §3.6–§3.7 | [T] |

### 4.4 SaG-CSM — Core System Model

#### 4.4.1 Model Construction

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-CSM-001 | The CSM component shall construct a typed graph representation of the distributed system from Model Setup Data, associated with project, platform, and version. | → §4.1–§4.2, §4.5 | [T] |
| SRS-CSM-002 | CSM shall validate the format, schema, integrity, and required fields of Model Setup Data before construction, and shall convert only data that passes validation. | → §4.3–§4.4 | [T] |
| SRS-CSM-003 | CSM shall represent at least the following entity types as graph nodes: System, Software Segment, CSCI, CSC, CSU, Role, Operator Console and Processor Units, Network components, Middleware Services, Communication Services, Topic, Message. | → §4.6 | [I] |
| SRS-CSM-004 | CSM shall represent at least the following relationship types as graph edges: runs-on (Console/Processor), uses (Middleware/Communication service), publishes, subscribes/consumes, depends-on (library or software unit), and role assignment of a software unit. | → §4.7 | [I] |
| SRS-CSM-005 | CSM shall report and record missing entities and invalid-relationship errors detected during construction, and shall report structural records in Analytical Evaluation Data that have no counterpart in the model. | → §4.8, §4.13 | [T] |
| SRS-CSM-006 | CSM shall record, per constructed model, the Model Setup Data file used, construction time, project, platform, version, and model status. | → §4.14 | [T] |

#### 4.4.2 Analytical Overlay (Independence-Preserving)

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-CSM-010 | CSM shall bind Analytical Evaluation Data to the model **without modifying** structural entities or relationships, keeping structural data and analytical data separately manageable. | → §4.12 | [T] |
| SRS-CSM-011 | CSM shall preserve and expose whether the Analytical Evaluation Data originated from System Field Records or from Scenario-Generator synthetic data, including the associated scenario information. | → §4.10.11, §4.11 | [T] |
| SRS-CSM-012 | CSM shall associate Analytical Evaluation Data with project, platform, version, and the Core System Model, and shall map record/telemetry/synthetic values to the relevant entities and relationships. | → §4.9–§4.10, §4.10.1–§4.10.2 | [T] |
| SRS-CSM-013 | CSM shall make the following queryable over the graph, sourced from Analytical Evaluation Data: operating/health status; CPU/memory/storage/network usage; error, warning, restart, and timeout information; message flow direction, count, volume, and frequency; communication latency, message loss, and successful-delivery rate; topic publish/consume activity; event records; and synthetically generated fault/load/latency/communication conditions. | → §4.10.3–§4.10.10 | [T] |

#### 4.4.3 Model Service and Concurrency

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-CSM-020 | CSM shall make the model available to the DAD component, providing access to entities, relationships, and their associated Analytical Evaluation Data. | → §4.15 | [T] |
| SRS-CSM-021 | CSM shall serve concurrent read/write operations from multiple user sessions on the same model without compromising model integrity or query-result consistency. | → §4.16 | [T] |
| SRS-CSM-022 | CSM shall construct a process-specific model for a candidate software-unit version combined with the other software-unit versions of the target platform version. | → §4.17 | [T] |
| SRS-CSM-023 | CSM shall execute concurrent analysis and simulation operations — including those of the production deployment pipeline — independently, without operations affecting one another. | → §4.18 | [T] |

### 4.5 SaG-DAD — Design Validation, Analysis and Evaluation

#### 4.5.1 Orchestration and Workflow Control

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-DAD-001 | DAD shall interact with the MKV, SUR, AVH, and CSM components. | → §5.2 | [A] |
| SRS-DAD-002 | DAD shall let the user select the working project, platform, and version, distinctly indicating the effective platform version. | → §5.3 | [D] |
| SRS-DAD-003 | DAD shall list the Model Setup Data files for the selected project/platform/version and let the user choose one. | → §5.4 | [D] |
| SRS-DAD-004 | DAD shall let the user start the Model Setup Data production process and monitor its status as in-progress, succeeded, or failed, and shall display detected errors. | → §5.5, §5.7 | [D] |
| SRS-DAD-005 | DAD shall let the user start Core System Model construction from selected Model Setup Data and monitor the result as succeeded, failed, or incomplete-model. | → §5.8 | [D] |
| SRS-DAD-006 | DAD shall let the user select the analytical-data source as either System Field Records or Scenario-Generator synthetic data; select field records when the former is chosen; and specify scenario inputs when the latter is chosen. | → §5.9–§5.11 | [D] |
| SRS-DAD-007 | DAD shall let the user start and monitor synthetic-data generation and Analytical Evaluation Data preparation, displaying errors that occur. | → §5.12–§5.13 | [D] |

#### 4.5.2 Structure-Only Validation and Analysis

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-DAD-010 | DAD shall perform validation and analysis without modifying the structural entities and relationships of the Core System Model. | → §5.14 | [T] |
| SRS-DAD-011 | DAD shall be able to perform analyses on the Core System Model **without** using Analytical Evaluation Data. | → §5.15 | [T] |
| SRS-DAD-012 | DAD shall verify topic QoS conformance and detect non-conformance for at least Durability, Reliability, Lifespan, and Transport Priority. | → §5.16 | [T] |
| SRS-DAD-013 | DAD shall analyse structural dependencies, communication links, and runtime-environment relationships on the model. | → §5.17 | [T] |
| SRS-DAD-014 | DAD shall verify publisher–consumer matching and detect: topics with no publisher, topics with no consumer, and topics sharing a name but differing in content definition. | → §5.18 | [T] |
| SRS-DAD-015 | DAD shall verify the consistency of source, destination, message, and direction for non-middleware communications over the configured communication services. | → §5.19 | [T] |
| SRS-DAD-016 | DAD shall analyse the distribution of software units across Operator Consoles and Processor Units against the configured load-balancing rules. | → §5.20 | [T] |
| SRS-DAD-017 | DAD shall detect cyclic dependencies among distributed-system software units. | → §5.21 | [T] |
| SRS-DAD-018 | DAD shall detect broken, missing, invalid, or unmatched structural relationships in the model. | → §5.22 | [T] |
| SRS-DAD-019 | DAD shall detect design patterns that violate the configured architectural rules (anti-patterns). | → §5.23 | [T] |

#### 4.5.3 What-If Analysis

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-DAD-020 | DAD shall let the user add/remove entities, add/remove relationships, and update entity attributes on a working copy of the model **without breaking its structural integrity**, and shall let the user run validation and analysis on the updated model. | → §5.24 | [D] |

#### 4.5.4 Simulation (Synthetic Analytical Data)

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-DAD-030 | DAD shall perform analyses using Analytical Evaluation Data derived from synthetic data, including message flow direction/count/volume/frequency and fault/load/communication conditions. | → §5.25–§5.26, §5.31 | [T] |
| SRS-DAD-031 | DAD shall simulate, on the model, at least: an entity becoming disabled, increased message density, and changed publish/consume behaviour, and shall evaluate their effects. | → §5.27 | [T] |
| SRS-DAD-032 | DAD shall perform design-time traffic analysis and evaluate the effects of simulated load conditions on entities and relationships. | → §5.28 | [T] |
| SRS-DAD-033 | DAD shall determine the propagation of simulated fault, load, communication-interruption, or bandwidth-narrowing conditions to dependent entities, identifying directly and indirectly affected entities and relationships and the propagation path the effect follows. | → §5.29 | [T] |
| SRS-DAD-034 | DAD shall identify the entities with the highest resource usage or heaviest messaging from simulation results and present them as summary indicators. | → §5.30 | [D] |

#### 4.5.5 Field-Data Analysis and Architectural Drift

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-DAD-040 | DAD shall perform analyses using Analytical Evaluation Data derived from System Field Records, covering at least: operating/health status; CPU/memory/storage/network usage; errors/warnings/restarts/timeouts/unreachability; message flow direction/count/volume/frequency; communication latency, message loss, and successful-delivery rate; and topic publish/consume activity. | → §5.32, §5.34–§5.37, §5.41 | [T] |
| SRS-DAD-041 | DAD shall detect topics used at runtime that are absent from the Model Setup Data. | → §5.33 | [T] |
| SRS-DAD-042 | DAD shall compare structural entities/relationships in the Model Setup Data with runtime entities/relationships observed in field-derived Analytical Evaluation Data and detect: entities/relationships present in the model but not observed at runtime; entities/relationships observed at runtime but absent from the model; and entities/relationships that are inconsistent between the two (architectural drift). | → §5.38 | [T] |
| SRS-DAD-043 | DAD shall evaluate the effect of observed communication latency on the model and identify the entities with the highest resource usage or heaviest messaging, presenting them as summary indicators. | → §5.39–§5.40 | [D] |

#### 4.5.6 Findings, Results, and Reporting

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-DAD-050 | DAD shall classify each validation/analysis result as "conformant" or "non-conformant" against the relevant rule or acceptance criterion. | → §5.43 | [T] |
| SRS-DAD-051 | DAD shall present each finding with at least: finding id, finding type, description, affected entity/relationship, related rule or acceptance criterion, supporting data/evidence, and a severity level of informational, low, medium, high, or critical. | → §5.44 | [I] |
| SRS-DAD-052 | DAD shall record and display the cause-and-effect relationships among related findings produced within one operation. | → §5.45 | [D] |
| SRS-DAD-053 | DAD shall let the user sort and filter findings by operation type, evaluation result, finding type, severity, project, platform, version, and affected entity. | → §5.47 | [D] |
| SRS-DAD-054 | DAD shall record the error reason, the stage at which an operation was interrupted, and the time, for any validation/analysis/simulation error, and display these to the user. | → §5.48 | [T] |
| SRS-DAD-055 | DAD shall store previous and current results separately by operation id, prevent overwriting of prior results, and allow results to be searched and viewed by operation id, operation type, project, platform, version, or operation time. | → §5.49 | [T] |
| SRS-DAD-056 | DAD shall record, for each simulation operation, the scenario name, scenario inputs, data-generation time, and associated project/platform/version. | → §5.42 | [T] |
| SRS-DAD-057 | DAD shall generate summary and detailed system reports in an exportable file format, containing at least: project, platform, and version; the Core System Model used; the Analytical Evaluation Data and its source; operation id and type; operation start/end times; evaluation result; detected findings; affected entities/relationships; severity levels; and supplementary information. | → §5.50 | [T] |

#### 4.5.7 Deployment-Suitability Gate (CI/CD)

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-DAD-060 | DAD shall act as the single entry point for a deployment-suitability evaluation initiated by the pipeline automation client, orchestrating Model Setup Data production, Core System Model construction, and evaluation, and returning the result to the client. | → §5.53 | [T] |
| SRS-DAD-061 | DAD shall evaluate a software unit's suitability for the target environment under at least: structural/architectural conformance; interface/topic/communication conformance; dependency/integration conformance; and resource/performance adequacy. | → §5.54 | [T] |
| SRS-DAD-062 | DAD shall define each check rule with a rule id, evaluation heading, severity, weight, acceptance criterion, and blocking flag, and shall classify and score rule results by the configured scoring method. | → §5.55 | [T] |
| SRS-DAD-063 | DAD shall set the deployment result to "non-conformant" — independent of the overall conformance score — when a critical-severity finding or a violation of a rule marked blocking is detected, and shall send the automation client a decision that halts the pipeline. | → §5.56 | [T] |
| SRS-DAD-064 | DAD shall run deployment-suitability evaluations for one or more software units under independent operation ids, and shall provide the automation client, per unit, with the conformance score, score class, blocking findings, and deployment decision, plus a machine-readable batch result. | → §5.57 | [T] |

---

## 5. Non-Functional (Quality) Requirements

### 5.1 Independence and Separability

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-NFR-001 | The structural model and the Analytical Evaluation Data shall be stored and managed as separately addressable artifacts, such that structural analysis output is identical whether or not analytical data is attached. | → §4.12, §5.15 | [T] |
| SRS-NFR-002 | No structural-analysis or criticality computation shall consume runtime or simulated analytical data as input; analytical data shall flow only into simulation, drift detection, field analysis, and reporting. *(Enforced by static import-separation tests; see §6.)* | → §4.12, §5.14–§5.15 | [T][A] |

### 5.2 Determinism, Traceability, and Auditability

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-NFR-010 | Every artifact (Model Setup Data, Core System Model, Analytical Evaluation Data, finding, result, and report) shall be associated with a project, platform, and version, and shall be retrievable by these keys. | → pervasive (§1.5, §2.5, §3.10, §4.5, §5.3, §5.49) | [T] |
| SRS-NFR-011 | Given the same Model Setup Data and the same analytical inputs and parameters, analysis and validation shall produce identical results. | → §5.49 (result integrity) | [T] |
| SRS-NFR-012 | All data-acquisition, generation, and evaluation operations shall be traceable, recording their inputs, source, and timestamps. | → §1.1, §2.6, §5.42, §5.49 | [T] |

### 5.3 Concurrency and Isolation

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-NFR-020 | The system shall execute concurrent interactive and automation-initiated operations independently and without mutual interference. | → §4.16, §4.18, §5.52 | [T] |

### 5.4 Security

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-NFR-030 | The system shall enforce LDAP-based authentication and grant access only within an authenticated user's authorised scope. | → §5.51 | [T] |
| SRS-NFR-031 | Stored data-source credentials shall be protected and shall not be exposed in logs, reports, or exported artifacts. | → §1.4 (derived) | [T] |

### 5.5 Performance and Scalability

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-NFR-040 | The system shall complete a full model-construction-and-evaluation pass for representative system scales within a configurable time budget, and shall scale to the largest supported configuration without loss of correctness. | → derived (operational use, §5.52–§5.57) | [T] |

### 5.6 Portability and Licensing

| ID | Requirement | Source | V |
|---|---|---|---|
| SRS-NFR-050 | The system shall be released under an open-source licence, with all dependencies licence-compatible, and shall run on the supported deployment environments without proprietary lock-in to a single graph-database vendor. | → §1.3 (scope), C-5 | [I] |

---

## 6. Verification

Each requirement carries a verification-method tag: **Test [T]**, **Analysis [A]**, **Inspection [I]**, or **Demonstration [D]**.

- **Independence (SRS-NFR-001/002)** is verified both by behavioural tests (structural output invariant to analytical attachment) and by static import-separation analysis that fails the build if the analysis/prediction code path imports simulation or analytical-data symbols. This reuses the existing executable independence checks of the `saag/` core.
- **Functional requirements** are verified primarily by automated tests against seeded models, including a representative reference system exercising QoS conformance, pub/sub matching, cyclic-dependency detection, anti-pattern detection, drift detection, and the deployment-suitability gate (including blocking-rule behaviour).
- **Interface and orchestration requirements** are verified by demonstration against the configured external sources and the CI automation client.
- A requirement is considered satisfied only when its associated verification activity passes and is traced in the requirements-traceability record.

---

## 7. Requirements Traceability

Coverage of the system-level requirements by this SRS. Section references are to the source document.

| System requirement group | Source items | Covering SRS requirements |
|---|---|---|
| MKV — Model Setup Data Generation | §1.1–§1.19 | SRS-MKV-001…009; SRS-EXT-001…005 |
| SUR — Scenario Generator | §2.1–§2.7 | SRS-SUR-001…006 |
| AVH — Analytical Data Preparation | §3.1–§3.10 | SRS-AVH-001…005; SRS-EXT-010…011 |
| CSM — Core System Model | §4.1–§4.18 (incl. §4.10.1–§4.10.11) | SRS-CSM-001…006, 010…013, 020…023; SRS-NFR-001 |
| DAD — workflow & data-source control | §5.1–§5.13 | SRS-DAD-001…007; SRS-EXT-040…041 |
| DAD — structure-only validation/analysis | §5.14–§5.23 | SRS-DAD-010…019 |
| DAD — what-if | §5.24 | SRS-DAD-020 |
| DAD — simulation (synthetic) | §5.25–§5.31 | SRS-DAD-030…034 |
| DAD — field analysis & drift | §5.32–§5.41 | SRS-DAD-040…043 |
| DAD — findings, results, reporting | §5.42–§5.50 | SRS-DAD-050…057 |
| DAD — deployment-suitability gate | §5.53–§5.57 | SRS-DAD-060…064 |
| DAD — access & automation interfaces | §5.51–§5.52 | SRS-EXT-020, 030…032; SRS-NFR-020, 030 |
| Cross-cutting — project/platform/version identity | pervasive | SRS-NFR-010…012 |
| Cross-cutting — independence guarantee | §4.12, §5.14–§5.15 | SRS-NFR-001…002; SRS-CSM-010; SRS-DAD-010…011 |

Unmapped source items: none at the requirement level. Items the source defers to "critical design" (rule sets, QoS rule details, load-balancing rules, anti-pattern rule catalogue, report file format, scoring method) are captured here as configurable inputs and are intentionally left to design, consistent with the source.

---

## 8. Appendix A — Glossary

| Term | Meaning |
|---|---|
| **SaG** | System-as-a-Graph — the framework specified by this document. |
| **Model Setup Data** | Validated structural data acquired from authoritative sources, used to build the Core System Model. |
| **Analytical Evaluation Data** | Dynamic-dimension data (from field records or synthetic scenarios) overlaid on the model for simulation, drift, and field analysis. |
| **Core System Model (CSM)** | The typed graph representation of the distributed system. |
| **Independence guarantee** | The property that structural analysis and analytical/runtime data are kept disjoint; analytical data never feeds structural analysis. |
| **Architectural drift** | Divergence between the designed structure (Model Setup Data) and the structure observed at runtime (field records). |
| **CSCI / CSC / CSU** | Computer Software Configuration Item / Component / Unit (MIL-STD-498 software decomposition). |
| **QoS** | Quality of Service — topic delivery attributes (Durability, Reliability, Lifespan, Transport Priority). |
| **Blocking rule** | A check rule whose violation forces a non-conformant deployment decision regardless of the overall score. |
| **Deployment-suitability gate** | The orchestrated, automatable evaluation that decides whether a software-unit version may proceed in the deployment pipeline. |

---

## 9. Appendix B — Open Decisions

These design decisions are deliberately left open by this baseline SRS; each is recorded so the document can be revised once resolved.

- **Decision A — Learned prediction/prescription scope.** This baseline excludes GNN-based `Q(v)` prediction and prescriptive remediation, matching the system-level requirements. If these are brought into product scope, they enter as an additive advisory capability (new requirement group) that must preserve SRS-NFR-001/002. *Affects:* §1.2, §2.6 (A-3).
- **Decision B — Field-data overlay boundary.** Field-derived analytical data is permitted for simulation, drift, and field analysis only. The implementation must guarantee it never reaches the structural-analysis path. *Affects:* SRS-NFR-002, SRS-DAD-040…043.
- **Decision C — Node-taxonomy realisation.** The extended entity types (System/Segment/CSCI/CSC/CSU/Role/Console/Network/Middleware/Communication) may be realised as first-class nodes or as container/attribute structures over the existing five-type analytical core. SRS-CSM-003/004 state *what* must be represented; the *how* is a design decision. *Affects:* SRS-CSM-003, SRS-CSM-004.
- **Decision D — Scenario Generator vs. topology generator.** SUR generates an analytical/runtime overlay on an ingested structure; it is distinct from the research topology generator, which synthesises structure and labels. They are kept as separate components. *Affects:* §4.2, A-4.

---

*End of document.*